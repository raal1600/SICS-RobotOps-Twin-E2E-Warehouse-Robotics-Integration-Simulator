"""Durable deterministic world. A synthetic effect and its journal commit atomically."""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import numpy as np

from robotops.calibration.contracts import CalibrationArtifact
from robotops.calibration.errors import CalibrationError
from robotops.calibration.geometry import Array
from robotops.calibration.lifecycle import CalibrationStore, CameraState
from robotops.calibration.optics import CameraModelReport
from robotops.cell import calibration_execution
from robotops.cell.calibration_motion import controller_frames
from robotops.cell.hkm_execution import final_machine, receipt_metadata, validate_execution
from robotops.config import Settings
from robotops.domain.models import (
    CellMode,
    CellState,
    CommandReceipt,
    CommandStatus,
    Fault,
    Pose,
    RobotCommand,
    RobotEvent,
    WorldObject,
    WorldState,
    new_id,
    utc_now,
)
from robotops.robotics.catalogue import fixture_source_pose, initial_tool_state, load_catalogue
from robotops.robotics.models import RobotState
from robotops.workflow.store import Conflict, Store, digest, metadata


class CommunicationTimeout(TimeoutError):
    """No response proves neither effect nor absence of effect."""


class SyntheticRuntime:
    def __init__(self, path: Path, settings: Settings | None = None):
        self.settings = settings or Settings()
        # Reuse transaction/immutable-record primitives, never business tables or decisions.
        self.db = Store(path)
        with self.db.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS runtime_world (id INTEGER PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS controller_journal (
                    id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, command TEXT NOT NULL,
                    receipt TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS robot_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT, command_id TEXT, body TEXT NOT NULL);
            """)
        with self.db.transaction() as db:
            if not db.execute("SELECT 1 FROM runtime_world WHERE id=1").fetchone():
                db.execute(
                    "INSERT OR REPLACE INTO meta VALUES ('execution_settings',?)",
                    (self.settings.model_dump_json(),),
                )
                self._reset(db)
            else:
                saved = db.execute(
                    "SELECT value FROM meta WHERE key='execution_settings'"
                ).fetchone()
                if saved:
                    self.settings = Settings.model_validate_json(saved[0])
                    if settings is not None:
                        self.settings = self.settings.model_copy(
                            update={"visual_frame_seconds": settings.visual_frame_seconds}
                        )
                else:
                    # Historical worlds keep their own fixture and wire format. Reading them
                    # does not migrate their durable records or command hashes.
                    world = self._world(db)
                    if world.schema_version != "1.0":
                        raise ValueError("VERSIONED_WORLD_MISSING_EXECUTION_SETTINGS")
                    self.settings = (
                        settings if settings is not None and not settings.is_hkm else Settings()
                    ).model_copy(
                        update={
                            "products": tuple(obj.product for obj in world.objects),
                            "locations": world.locations,
                        }
                    )

    def reset(self, scene_epoch: str | None = None) -> WorldState:
        with self.db.transaction() as db:
            epoch = scene_epoch or new_id()
            previous = db.execute(
                "SELECT body FROM records WHERE kind='WorldState' AND id=?", (epoch,)
            ).fetchone()
            if previous:
                return WorldState.model_validate_json(previous[0])
            if any(
                CommandReceipt.model_validate_json(row[0]).status
                in {CommandStatus.RUNNING, CommandStatus.STATUS_UNKNOWN}
                for row in db.execute("SELECT receipt FROM controller_journal")
            ):
                raise Conflict("SCENE_RESET_BLOCKED_UNCERTAIN_COMMAND")
            # Restocking objects does not reinstall a removed board or change the
            # reported physical tool/gantry. Calibration remains tied to that cell.
            previous_machine = (
                self._world(db).calibration_machine if self.settings.is_measured else None
            )
            world = self._reset(db, epoch)
            if previous_machine is not None:
                world = world.model_copy(update={"calibration_machine": previous_machine})
                self._write_world(db, world)
            self.db._record(db, epoch, world)
            event = RobotEvent(
                **metadata(world),
                event_id=new_id(),
                component="fixture",
                event_type="SCENE_RESET",
                reason="EXPLICIT_FIXTURE_RESTOCK",
                scene_epoch=epoch,
                step=0,
            )
            db.execute(
                "INSERT INTO robot_events(command_id,body) VALUES (NULL,?)",
                (event.model_dump_json(),),
            )
            return world

    def _reset(self, db: sqlite3.Connection, scene_epoch: str | None = None) -> WorldState:
        now = utc_now()
        epoch = scene_epoch or new_id()
        common = dict(
            run_id=self.db.run_id, correlation_id=epoch, causation_id=epoch, timestamp=now
        )
        cell = CellState(**common)
        source = self.settings.locations[0]
        extensions = {}
        if self.settings.is_measured:
            extensions = dict(
                schema_version="3.0",
                calibration_machine=calibration_execution.initial_machine(
                    self.settings.calibration_command_mode or "flange"
                ),
            )
        elif self.settings.is_hkm:
            catalogue = load_catalogue()
            tools = initial_tool_state()
            extensions = dict(
                schema_version="2.0",
                robot_profile_version=catalogue.profile_version,
                product_catalog_version=catalogue.product_catalog_version,
                tool_spec_version=catalogue.tool_catalog_version,
                frame_tree_version=catalogue.frame_tree_version,
                robot_state=RobotState(
                    tcp_pose=catalogue.layout.home_tcp_pose, active_tool_id=tools.active_tool_id
                ),
                tool_state=tools,
            )
        world = WorldState(
            **common,
            **extensions,
            scene_epoch=epoch,
            step=0,
            cell=cell,
            locations=self.settings.locations,
            objects=tuple(
                WorldObject(
                    product=p,
                    location_id=self.settings.source_for(p.product_id),
                    pose=fixture_source_pose(p.sku)
                    if self.settings.is_hkm
                    else source.pose.model_copy(
                        update={
                            "position": (
                                source.pose.position[0],
                                source.pose.position[1]
                                + (index - (len(self.settings.products) - 1) / 2) * 0.18,
                                source.pose.position[2],
                            )
                        }
                    ),
                )
                for index, p in enumerate(self.settings.products)
            ),
        )
        self._write_world(db, world)
        return world

    @staticmethod
    def _world(db: sqlite3.Connection) -> WorldState:
        row = db.execute("SELECT body FROM runtime_world WHERE id=1").fetchone()
        if row is None:
            raise RuntimeError("WORLD_NOT_INITIALIZED")
        return WorldState.model_validate_json(row[0])

    @staticmethod
    def _write_world(db: sqlite3.Connection, world: WorldState) -> None:
        db.execute("INSERT OR REPLACE INTO runtime_world VALUES (1,?)", (world.model_dump_json(),))

    def world(self) -> WorldState:
        with self.db.connect() as db:
            return self._world(db)

    def set_cell(self, mode: CellMode, reason: str) -> CellState:
        with self.db.transaction() as db:
            world = self._world(db)
            cell = world.cell.model_copy(
                update={
                    "mode": mode,
                    "reason": reason,
                    "generation": world.cell.generation + 1,
                    "timestamp": utc_now(),
                }
            )
            self._write_world(db, world.model_copy(update={"cell": cell, "timestamp": utc_now()}))
            event = RobotEvent(
                **metadata(world),
                event_id=new_id(),
                component="cell",
                event_type="CELL_STATE",
                state_before=world.cell.mode,
                state_after=mode,
                reason=reason,
                scene_epoch=world.scene_epoch,
                step=world.step,
            )
            db.execute(
                "INSERT INTO robot_events(command_id,body) VALUES (NULL,?)",
                (event.model_dump_json(),),
            )
            return cell

    def journal(self, command_id: str) -> CommandReceipt | None:
        return self.recorded_journal(command_id)

    def recorded_journal(self, command_id: str) -> CommandReceipt | None:
        """Presentation reads persisted receipts without completing pending checkpoints."""
        with self.db.connect() as db:
            row = db.execute(
                "SELECT receipt FROM controller_journal WHERE id=?", (command_id,)
            ).fetchone()
            return CommandReceipt.model_validate_json(row[0]) if row else None

    @staticmethod
    def _event(
        db: sqlite3.Connection, command: RobotCommand, world: WorldState, kind: str, reason: str
    ) -> None:
        previous = db.execute(
            "SELECT body FROM robot_events WHERE command_id=? ORDER BY sequence DESC LIMIT 1",
            (command.command_id,),
        ).fetchone()
        cause = (
            RobotEvent.model_validate_json(previous[0]).event_id if previous else command.command_id
        )
        event = RobotEvent(
            **metadata(command, cause),
            event_id=new_id(),
            component="runtime",
            event_type=kind,
            reason=reason,
            order_id=command.order_id,
            job_id=command.job_id,
            command_id=command.command_id,
            scene_epoch=world.scene_epoch,
            step=world.step,
        )
        db.execute(
            "INSERT INTO robot_events(command_id,body) VALUES (?,?)",
            (command.command_id, event.model_dump_json()),
        )

    def events(self, command_id: str | None = None) -> list[RobotEvent]:
        with self.db.connect() as db:
            return [
                RobotEvent.model_validate_json(r[0])
                for r in db.execute(
                    "SELECT body FROM robot_events WHERE (? IS NULL OR command_id=?) ORDER BY sequence",
                    (command_id, command_id),
                )
            ]

    @staticmethod
    def rejection_reason(
        world: WorldState, command: RobotCommand, fault: Fault | None
    ) -> str | None:
        objects = {obj.product.product_id: obj for obj in world.objects}
        locations = {loc.location_id: loc for loc in world.locations}
        if command.scene_epoch != world.scene_epoch:
            return "SCENE_EPOCH_MISMATCH"
        elif world.cell.mode != CellMode.READY:
            return "CELL_NOT_READY"
        elif command.cell_generation != world.cell.generation:
            return "CELL_GENERATION_MISMATCH"
        elif command.product_id not in objects or command.destination_id not in locations:
            return "UNKNOWN_PRODUCT_OR_DESTINATION"
        elif objects[command.product_id].location_id != command.source_id:
            return "SOURCE_PRECONDITION_FAILED"
        elif world.schema_version != command.schema_version:
            return "RUNTIME_PROFILE_VERSION_MISMATCH"
        elif world.schema_version == "2.0":
            try:
                validate_execution(world, command)
            except (ValueError, StopIteration) as exc:
                return str(exc) or "RUNTIME_PRECONDITION_FAILED"
        elif world.schema_version == "3.0":
            try:
                if command.target_pose != locations[command.destination_id].pose:
                    return "TARGET_POSE_MISMATCH"
                calibration_execution.validate_execution(world, command)
            except (ValueError, StopIteration) as exc:
                return str(exc) or "RUNTIME_PRECONDITION_FAILED"
        elif command.target_pose != locations[command.destination_id].pose:
            return "TARGET_POSE_MISMATCH"
        if fault == Fault.MISSED_PICK and command.schema_version != "3.0":
            return "MISSED_PICK_REQUIRES_MEASURED_CELL"
        if fault == Fault.DROP_ACK_BEFORE_EFFECT:
            return "PROVEN_NOT_STARTED"
        elif fault == Fault.ROBOT_COMMAND_FAILURE:
            return "SIMULATED_COMMAND_FAILURE"
        return None

    def _motion_events(
        self,
        db: sqlite3.Connection,
        command: RobotCommand,
        world: WorldState,
        physical_tool: Array | None = None,
        *,
        grip_established: bool = True,
    ) -> Pose | None:
        if command.calibrated_plan is not None:
            if world.calibration_machine is None or physical_tool is None:
                raise CalibrationError("MEASURED_MACHINE_REQUIRED")
            result = None
            last_phase = None
            for frame in controller_frames(
                world, command, physical_tool, grip_established=grip_established
            ):
                result = frame.object_pose
                reported_world = world.model_copy(
                    update={
                        "calibration_machine": frame.machine,
                        "objects": tuple(
                            obj.model_copy(
                                update={"pose": frame.object_pose, "attached": frame.attached}
                            )
                            if obj.product.product_id == command.product_id
                            else obj
                            for obj in world.objects
                        ),
                    }
                )
                self._write_world(db, reported_world)
                db.execute(
                    "INSERT INTO calibration_machine_reports(capture_id,body) VALUES (?,?)",
                    (
                        f"command:{command.command_id}:{frame.index}",
                        frame.machine.model_dump_json(),
                    ),
                )
                db.execute(
                    "INSERT INTO calibration_motion_frames VALUES (?,?,?)",
                    (command.command_id, frame.index, frame.model_dump_json()),
                )
                if frame.machine.motion_phase != last_phase:
                    self._event(
                        db,
                        command,
                        reported_world,
                        frame.machine.motion_phase,
                        f"SYNTHETIC_GANTRY_REPORTED;SIM_TIME_S={frame.sim_time_s:.9f}",
                    )
                last_phase = frame.machine.motion_phase
            return result
        if command.trajectory is None:
            return None
        for point in command.trajectory.waypoints:
            self._event(db, command, world, point.phase, f"SIM_TIME_S={point.sim_time_s:.9f}")
        return None

    def _execute(
        self,
        db: sqlite3.Connection,
        command: RobotCommand,
        fault: Fault | None,
        gate_rejection: str | None = None,
    ) -> CommandReceipt:
        world = self._world(db)
        original_world = world
        hashed = digest(command)
        existing = db.execute(
            "SELECT payload_hash,receipt FROM controller_journal WHERE id=?", (command.command_id,)
        ).fetchone()
        if existing:
            if existing[0] != hashed:
                raise Conflict("COMMAND_ID_PAYLOAD_CONFLICT")
            self._event(db, command, world, "DUPLICATE_SUPPRESSED", "ORIGINAL_JOURNAL_RETURNED")
            return CommandReceipt.model_validate_json(existing[1])
        self._event(db, command, world, "COMMAND_CREATED", "DURABLE_INTENT")
        self._event(db, command, world, "COMMAND_DISPATCHED", "DELIVERY")
        if fault is not None:
            self._event(db, command, world, "FAULT_INJECTED", fault.value)
        objects = {obj.product.product_id: obj for obj in world.objects}
        reason = "PICK_APPLIED"
        status = CommandStatus.SUCCEEDED
        count = 0
        missed_transfer = False
        if fault in {Fault.CELL_FAULT, Fault.LOGICAL_ESTOP}:
            mode = CellMode.FAULTED if fault == Fault.CELL_FAULT else CellMode.ESTOP_LOGICAL
            world = world.model_copy(
                update={
                    "cell": world.cell.model_copy(
                        update={
                            "mode": mode,
                            "generation": world.cell.generation + 1,
                            "reason": fault.value,
                        }
                    )
                }
            )
        reason = gate_rejection or self.rejection_reason(world, command, fault) or "PICK_APPLIED"
        physical_tool = None
        if reason == "PICK_APPLIED" and command.schema_version == "3.0":
            row = db.execute("SELECT value FROM meta WHERE key='synthetic_sensor_truth'").fetchone()
            if row is None:
                reason = "SYNTHETIC_PHYSICAL_TOOL_UNKNOWN"
            else:
                try:
                    physical_tool = np.asarray(json.loads(row[0])["tool"], dtype=np.float64)
                    calibration_execution.validate_execution(world, command, physical_tool)
                except (ValueError, KeyError) as error:
                    reason = str(error)
        if reason == "SIMULATED_COMMAND_FAILURE":
            status = CommandStatus.FAILED
        if reason != "PICK_APPLIED":
            if status != CommandStatus.FAILED:
                status = CommandStatus.REJECTED
        else:
            self._event(db, command, world, "COMMAND_ACCEPTED", "PRECONDITIONS_PASSED")
            self._event(db, command, world, "COMMAND_RUNNING", "SIMULATED_PICK")
            missed_transfer = fault == Fault.MISSED_PICK
            measured_final_pose = self._motion_events(
                db, command, world, physical_tool, grip_established=not missed_transfer
            )
            moved = (
                objects[command.product_id]
                if missed_transfer
                else objects[command.product_id].model_copy(
                    update={
                        "location_id": command.destination_id,
                        "pose": measured_final_pose
                        if measured_final_pose is not None
                        else command.target_pose,
                        "attached": False,
                    }
                )
            )
            world = world.model_copy(
                update={
                    "step": world.step + 1,
                    "timestamp": utc_now(),
                    "objects": tuple(
                        moved if obj.product.product_id == command.product_id else obj
                        for obj in world.objects
                    ),
                }
            )
            if command.schema_version == "2.0":
                robot, tools = final_machine(original_world, command)
                world = world.model_copy(update={"robot_state": robot, "tool_state": tools})
            elif command.schema_version == "3.0":
                world = world.model_copy(
                    update={
                        "calibration_machine": calibration_execution.final_machine(
                            original_world, command
                        )
                    }
                )
            if missed_transfer:
                status, reason = CommandStatus.FAILED, "GRASP_NOT_ESTABLISHED"
                self._event(db, command, world, "PICK_ATTEMPT_NO_TRANSFER", reason)
            else:
                self._event(db, command, world, "PICK_EFFECT", "ATTACH_TRANSFER_DETACH")
                count = 1
        self._write_world(db, world)
        receipt = CommandReceipt(
            **metadata(command, command.command_id),
            **(
                calibration_execution.receipt_metadata(
                    original_world,
                    command,
                    effect=count == 1,
                    motion_without_transfer=missed_transfer,
                )
                if command.schema_version == "3.0"
                else receipt_metadata(original_world, command, effect=count == 1)
            ),
            command_id=command.command_id,
            job_id=command.job_id,
            scene_epoch=command.scene_epoch,
            status=status,
            reason=reason,
            effect_count=count,
            payload_hash=hashed,
        )
        db.execute(
            "INSERT INTO controller_journal VALUES (?,?,?,?)",
            (command.command_id, hashed, command.model_dump_json(), receipt.model_dump_json()),
        )
        self._event(db, command, world, "COMMAND_" + status.value, reason)
        return receipt

    def apply(self, command: RobotCommand, fault: Fault | None = None) -> CommandReceipt:
        # Parse even Python callers: no model_construct/model_copy bypass at the boundary.
        command = RobotCommand.model_validate_json(command.model_dump_json())
        with self.calibration_gate(command) as rejection, self.db.transaction() as db:
            receipt = self._execute(db, command, fault, gate_rejection=rejection)
        if fault in {Fault.DROP_ACK_AFTER_EFFECT, Fault.DROP_ACK_BEFORE_EFFECT}:
            raise CommunicationTimeout("ACKNOWLEDGEMENT_LOST")
        return receipt

    def bind_calibration_store(self, path: Path) -> None:
        """Application composition binds a same-run store; not an HTTP file-path input."""
        if path.resolve().parent != self.db.path.resolve().parent:
            raise CalibrationError("CALIBRATION_STORE_MUST_BELONG_TO_SAME_RUN")
        with self.db.transaction() as db:
            prior = db.execute(
                "SELECT value FROM meta WHERE key='calibration_workflow_name'"
            ).fetchone()
            if prior and prior[0] != path.name:
                raise CalibrationError("CALIBRATION_STORE_BINDING_IMMUTABLE")
            db.execute(
                "INSERT OR IGNORE INTO meta VALUES ('calibration_workflow_name',?)", (path.name,)
            )

    @contextmanager
    def calibration_gate(self, command: RobotCommand) -> Iterator[str | None]:
        """Pin applicable approval across the physical transaction; never reinterpret a command.

        An existing command always reconciles its original journal, even if calibration
        subsequently changed. A new physical effect requires the exact bound artifact.
        """
        if command.schema_version != "3.0" or self.recorded_journal(command.command_id) is not None:
            yield None
            return
        with self.db.readonly_connect() as db:
            row = db.execute(
                "SELECT value FROM meta WHERE key='calibration_workflow_name'"
            ).fetchone()
        if row is None or Path(row[0]).name != row[0]:
            yield "CALIBRATION_STORE_NOT_BOUND"
            return
        path = self.db.path.with_name(row[0])
        if not path.is_file():
            yield "CALIBRATION_STORE_UNAVAILABLE"
            return
        workflow = Store(path)
        with workflow.transaction() as authority:
            reason = None
            intent = command.calibrated_plan
            if intent is None:
                reason = "MEASURED_COMMAND_REQUIRED"
            else:
                try:
                    recorded = authority.execute(
                        "SELECT body FROM records WHERE kind='RobotCommand' AND id=?",
                        (command.command_id,),
                    ).fetchone()
                    if recorded is None or RobotCommand.model_validate_json(recorded[0]) != command:
                        raise CalibrationError("COMMAND_NOT_BOUND_TO_SAVED_AUTHORITY")
                    for binding in (intent.observed_object.binding, *intent.supporting_bindings):
                        row = authority.execute(
                            "SELECT body FROM calibration_cameras WHERE id=?", (binding.camera_id,)
                        ).fetchone()
                        if row is None:
                            raise CalibrationError("APPROVED_CALIBRATION_REQUIRED")
                        state = CameraState.model_validate_json(row[0])
                        if state.active_validity != "VERIFIED":
                            raise CalibrationError("ACTIVE_CALIBRATION_SUSPECT")
                        if state.active_artifact_id != binding.artifact_id:
                            raise CalibrationError("PREPARED_COMMAND_CALIBRATION_CHANGED")
                        if state.camera_model_report_id is None:
                            raise CalibrationError("CAMERA_MODEL_VERIFICATION_REQUIRED")
                        optical = CalibrationStore._record(
                            authority,
                            "camera-model-report",
                            state.camera_model_report_id,
                            CameraModelReport,
                        )
                        if (
                            not optical.passed
                            or optical.camera_configuration_fingerprint
                            != state.camera.fingerprint()
                        ):
                            raise CalibrationError("CAMERA_MODEL_NOT_VERIFIED")
                        artifact = CalibrationStore._record(
                            authority, "artifact", binding.artifact_id, CalibrationArtifact
                        )
                        if (
                            artifact.camera_model_report_id != optical.report_id
                            or artifact.camera_model_report_fingerprint != optical.fingerprint()
                        ):
                            raise CalibrationError("APPROVED_OPTICAL_REPORT_BINDING_CHANGED")
                        if (
                            artifact.fingerprint() != binding.artifact_fingerprint
                            or state.camera.fingerprint()
                            != binding.camera_configuration_fingerprint
                            or artifact.candidate.camera.fingerprint() != state.camera.fingerprint()
                            or artifact.candidate.limits_fingerprint != state.limits.fingerprint()
                            or artifact.candidate.board.fingerprint() != state.board.fingerprint()
                        ):
                            raise CalibrationError("COMMAND_CALIBRATION_CONFIGURATION_MISMATCH")
                except (CalibrationError, ValueError, LookupError) as error:
                    reason = str(error)
            yield reason

    def capture(self, path: Path) -> Path:
        # Headless diagnostic artifact; never presented as a Blender screenshot.
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.world().model_dump(mode="json"), indent=2), encoding="utf-8"
        )
        return path
