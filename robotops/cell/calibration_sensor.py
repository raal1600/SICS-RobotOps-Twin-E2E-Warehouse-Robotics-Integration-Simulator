"""Synthetic hardware adapter. This is the permitted private-world/sensor boundary."""

import hashlib
import json
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from scipy.spatial.transform import Rotation

from robotops.blender.visualization import VisualScene
from robotops.calibration.artifacts import SensorArtifacts
from robotops.calibration.configuration import charuco_board, default_board, framed
from robotops.calibration.contracts import Board, Camera, Capture, Limits, ReferenceBatch, Transform
from robotops.calibration.errors import CalibrationError
from robotops.calibration.faults import FaultRecord, sensor_output
from robotops.calibration.geometry import Array, from_xyzw
from robotops.calibration.presentation import CapturePresentation
from robotops.calibration.runtime_contracts import CalibrationMachine, SensorSnapshot
from robotops.calibration.synthetic import PhysicalBox, SyntheticSensorWorld
from robotops.calibration.tcp import (
    ToolMeasurements,
    ToolProbe,
    ToolVerification,
    verify_measurements,
)
from robotops.cell.calibration_execution import CUBE_SIDE_M, WORKSPACE_MAX, WORKSPACE_MIN
from robotops.cell.runtime import SyntheticRuntime
from robotops.domain.models import CellMode, WorldState, utc_now
from robotops.workflow.store import Conflict


class ControllerSensor(SyntheticSensorWorld):
    """Calibrate and observe the actual local runtime using synthetic sensor arrays.

    Image acquisition is journaled with the controller-reported flange pose. Retrying
    a capture ID returns its original images; it neither moves nor recaptures a scene.
    """

    def __init__(self, runtime: SyntheticRuntime, artifacts: SensorArtifacts):
        super().__init__(runtime.settings.seed, artifacts)
        self.runtime = runtime
        with runtime.db.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS calibration_captures (
                    id TEXT PRIMARY KEY, input_hash TEXT NOT NULL, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS calibration_machine_reports (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT, capture_id TEXT UNIQUE NOT NULL,
                    body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS calibration_capture_scenes (
                    capture_id TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS calibration_motion_frames (
                    command_id TEXT NOT NULL, sample_index INTEGER NOT NULL, body TEXT NOT NULL,
                    PRIMARY KEY(command_id,sample_index));
                CREATE TABLE IF NOT EXISTS calibration_tool_measurements (
                    id TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS calibration_reference_batches (
                    id TEXT PRIMARY KEY, input_hash TEXT NOT NULL, body TEXT NOT NULL);
            """)
            physical_tool = np.eye(4)
            physical_tool[2, 3] = 0.18
            truth = {
                "cameras": {key: matrix.tolist() for key, matrix in self._physical_cameras.items()},
                "mount": self._physical_mount.tolist(),
                "tool": physical_tool.tolist(),
            }
            db.execute(
                "INSERT OR IGNORE INTO meta VALUES ('synthetic_sensor_truth',?)",
                (json.dumps(truth),),
            )
            db.execute(
                "INSERT OR IGNORE INTO meta VALUES ('synthetic_reported_board',?)",
                (self.board.model_dump_json(),),
            )
            db.execute(
                "INSERT OR IGNORE INTO meta VALUES ('synthetic_reported_cameras',?)",
                (
                    json.dumps(
                        {
                            key: camera.model_dump(mode="json")
                            for key, camera in self.cameras.items()
                        }
                    ),
                ),
            )
        self._load_physics()

    def _load_physics(self) -> None:
        with self.runtime.db.readonly_connect() as db:
            db.execute("BEGIN")
            row = db.execute("SELECT value FROM meta WHERE key='synthetic_sensor_truth'").fetchone()
            rows = db.execute(
                "SELECT value FROM meta WHERE key LIKE 'sensor-output-fault:%'"
            ).fetchall()
            reported = db.execute(
                "SELECT value FROM meta WHERE key='synthetic_reported_cameras'"
            ).fetchone()
            board = db.execute(
                "SELECT value FROM meta WHERE key='synthetic_reported_board'"
            ).fetchone()
            printing = db.execute(
                "SELECT value FROM meta WHERE key='synthetic_board_print_fault'"
            ).fetchone()
        if row is None:
            raise CalibrationError("SYNTHETIC_SENSOR_WORLD_MISSING")
        truth = json.loads(row[0])
        self._physical_cameras = {key: np.array(matrix) for key, matrix in truth["cameras"].items()}
        self._physical_mount = np.array(truth["mount"])
        self._physical_tool = np.array(truth["tool"])
        self._board_print_fault = FaultRecord.model_validate_json(printing[0]) if printing else None
        marker_ids = (
            tuple(range(17, 34))
            if self._board_print_fault
            and self._board_print_fault.definition.kind == "board_marker_ids"
            else ()
        )
        if marker_ids != self._printing_marker_ids:
            self._printing_marker_ids = marker_ids
            self._texture = charuco_board(self._physical_board, marker_ids).generateImage(
                (1400, 1000), marginSize=0
            )
        if board:
            self.board = Board.model_validate_json(board[0])
        if reported:
            self.cameras = {
                key: Camera.model_validate(value) for key, value in json.loads(reported[0]).items()
            }
        self._output_faults = {
            fault.camera_id: fault
            for row in rows
            for fault in [FaultRecord.model_validate_json(row[0])]
        }

    def refresh_configuration(self) -> None:
        self._load_physics()

    def sensor_output(
        self, camera: Camera, rgb: NDArray[np.uint8], depth: NDArray[np.float32], capture_id: str
    ) -> tuple[NDArray[np.uint8], NDArray[np.float32]]:
        return sensor_output(
            self._output_faults.get(camera.camera_id), camera, rgb, depth, capture_id
        )

    def sensor_fault_ids(self, camera_id: str) -> tuple[str, ...]:
        fault = self._output_faults.get(camera_id)
        return ((fault.fault_id,) if fault is not None else ()) + (
            (self._board_print_fault.fault_id,) if self._board_print_fault else ()
        )

    def apply_fault(self, fault: FaultRecord) -> None:
        """A durable fixture mutation; no fitted/approved values are accessed here."""
        if fault.camera_id not in self.cameras:
            raise CalibrationError("UNKNOWN_SYNTHETIC_CAMERA")
        with self.runtime.db.transaction() as db:
            key = f"applied-fault:{fault.fault_id}"
            previous = db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
            if previous:
                if previous[0] != fault.fingerprint():
                    raise Conflict("FAULT_IDEMPOTENCY_CONFLICT")
                return
            world = self.runtime._world(db)
            if world.cell.mode != CellMode.READY or world.calibration_machine is None:
                raise CalibrationError("CELL_NOT_READY")
            machine = world.calibration_machine
            if fault.definition.affected == "sensor":
                db.execute(
                    "INSERT INTO meta VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (f"sensor-output-fault:{fault.camera_id}", fault.model_dump_json()),
                )
            elif fault.definition.affected == "configuration":
                declared = self._factory_models[fault.camera_id].model_dump(mode="json")
                kind = fault.definition.kind
                if kind != "restore_model":
                    declared["configuration_revision"] = fault.fault_id
                if kind == "model_focal":
                    declared["rgb"]["k"][0][0] *= 1.1
                    declared["rgb"]["k"][1][1] *= 1.1
                elif kind == "model_profile":
                    declared["profile_id"] = "unsupported-profile"
                elif kind == "model_crop":
                    declared["rgb"]["crop_xy"] = [32, 32]
                elif kind == "model_resize":
                    declared["depth"]["resize_xy"] = [0.5, 0.5]
                elif kind == "model_distortion":
                    declared["rgb"].update(
                        distortion_model="fisheye", coefficients=[0.0, 0.0, 0.0, 0.0]
                    )
                configured = Camera.model_validate(declared)
                models = json.loads(
                    db.execute(
                        "SELECT value FROM meta WHERE key='synthetic_reported_cameras'"
                    ).fetchone()[0]
                )
                models[fault.camera_id] = configured.model_dump(mode="json")
                db.execute(
                    "UPDATE meta SET value=? WHERE key='synthetic_reported_cameras'",
                    (json.dumps(models),),
                )
            elif fault.definition.affected == "board":
                declared_board = Board.model_validate_json(
                    db.execute(
                        "SELECT value FROM meta WHERE key='synthetic_reported_board'"
                    ).fetchone()[0]
                )
                if fault.definition.kind in {"board_marker_ids", "restore_board_print"}:
                    db.execute(
                        "INSERT OR REPLACE INTO meta VALUES ('synthetic_board_print_fault',?)",
                        (fault.model_dump_json(),),
                    )
                elif fault.definition.kind == "board_remount":
                    truth = json.loads(
                        db.execute(
                            "SELECT value FROM meta WHERE key='synthetic_sensor_truth'"
                        ).fetchone()[0]
                    )
                    mount = np.array(truth["mount"])
                    change = np.eye(4)
                    change[:3, :3] = Rotation.from_rotvec([0.02, 0, 0]).as_matrix()
                    change[:3, 3] = [0.008, 0, 0]
                    truth["mount"] = (change @ mount).tolist()
                    db.execute(
                        "UPDATE meta SET value=? WHERE key='synthetic_sensor_truth'",
                        (json.dumps(truth),),
                    )
                    declared_board = declared_board.model_copy(
                        update={"mounting_id": fault.fault_id}
                    )
                else:
                    specification = default_board().model_dump(mode="json")
                    specification["mounting_id"] = declared_board.mounting_id
                    if fault.definition.kind == "board_dimensions":
                        for key in ("square_length_m", "marker_length_m"):
                            specification[key] *= 1.08
                        specification["measured_dimensions_m"] = [
                            value * 1.08 for value in specification["measured_dimensions_m"]
                        ]
                        specification["corners_m"] = [
                            [value * 1.08 for value in point]
                            for point in specification["corners_m"]
                        ]
                    declared_board = Board.model_validate(specification)
                db.execute(
                    "UPDATE meta SET value=? WHERE key='synthetic_reported_board'",
                    (declared_board.model_dump_json(),),
                )
                world = world.model_copy(
                    update={
                        "calibration_machine": machine.model_copy(
                            update={
                                "board_mounted": True,
                                "tool_verification_id": None,
                                "motion_phase": "BOARD_CHECK_REQUIRED",
                            }
                        )
                    }
                )
            else:
                truth = json.loads(
                    db.execute(
                        "SELECT value FROM meta WHERE key='synthetic_sensor_truth'"
                    ).fetchone()[0]
                )
                physical = np.eye(4)
                physical[2, 3] = 0.18
                if fault.definition.kind == "tool_translation":
                    physical[2, 3] += 0.015
                elif fault.definition.kind == "tool_rotation":
                    physical[:3, :3] = Rotation.from_rotvec([0.04, 0, 0]).as_matrix()
                truth["tool"] = physical.tolist()
                db.execute(
                    "UPDATE meta SET value=? WHERE key='synthetic_sensor_truth'",
                    (json.dumps(truth),),
                )
                world = world.model_copy(
                    update={
                        "calibration_machine": machine.model_copy(
                            update={
                                "tool_verification_id": None,
                                "motion_phase": "TOOL_CHECK_REQUIRED",
                            }
                        )
                    }
                )
            db.execute("INSERT INTO meta VALUES (?,?)", (key, fault.fingerprint()))
            self.runtime._write_world(
                db,
                world.model_copy(
                    update={
                        "cell": world.cell.model_copy(
                            update={"generation": world.cell.generation + 1}
                        ),
                        "timestamp": utc_now(),
                    }
                ),
            )
        self._load_physics()

    def presentation_reference(self) -> tuple[dict[str, Array], Array]:
        """Read-only physical layout for the 3D world, never an estimator/planner input."""
        self._load_physics()
        return {
            key: value.copy() for key, value in self._physical_cameras.items()
        }, self._physical_mount.copy()

    def presentation_snapshot(self, world: WorldState) -> VisualScene:
        from robotops.calibration.visualization import cell_geometry

        physical_cameras, mount = self.presentation_reference()
        objects, cameras = cell_geometry(
            world,
            self._physical_board,
            physical_cameras,
            mount,
            self._factory_models,
            self._printing_marker_ids,
        )
        return VisualScene(
            schema_version="3.0",
            robot_profile_version="synthetic_calibration_gantry_v1",
            source="SAVED_START_SCENE",
            scene_epoch=world.scene_epoch,
            timestamp=world.timestamp,
            cell_mode=world.cell.mode,
            objects=objects,
            cameras=cameras,
        )

    def evidence_snapshot(self) -> dict[str, object]:
        """Allowlisted telemetry and explicitly labelled saved instructor presentation."""
        with self.runtime.db.readonly_connect() as db:
            db.execute("BEGIN")
            commands = [
                {
                    "command_id": row[0],
                    "payload_hash": row[1],
                    "command": json.loads(row[2]),
                    "receipt": json.loads(row[3]),
                }
                for row in db.execute(
                    "SELECT id,payload_hash,command,receipt FROM controller_journal ORDER BY id"
                )
            ]
            frames = [
                json.loads(row[0])
                for row in db.execute(
                    "SELECT body FROM calibration_motion_frames ORDER BY command_id,sample_index"
                )
            ]
            reports = [
                json.loads(row[0])
                for row in db.execute(
                    "SELECT body FROM calibration_machine_reports ORDER BY sequence"
                )
            ]
            scenes = [
                json.loads(row[0])
                for row in db.execute(
                    "SELECT body FROM calibration_capture_scenes ORDER BY capture_id"
                )
            ]
            events = [
                json.loads(row[0])
                for row in db.execute("SELECT body FROM robot_events ORDER BY sequence")
            ]
        snapshot = {
            "scope": "Read-only controller journal, reported samples and labelled instructor presentation geometry; not estimator inputs",
            "commands": commands,
            "motion_frames": frames,
            "capture_machine_reports": reports,
            "capture_presentations": scenes,
            "events": events,
        }
        canonical = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
        return {**snapshot, "sha256": hashlib.sha256(canonical.encode()).hexdigest()}

    def capture_presentation(self, capture_id: str) -> CapturePresentation:
        with self.runtime.db.readonly_connect() as db:
            row = db.execute(
                "SELECT body FROM calibration_capture_scenes WHERE capture_id=?", (capture_id,)
            ).fetchone()
        if row is None:
            raise CalibrationError(
                "SAVED_CAPTURE_SCENE_UNAVAILABLE",
                "This capture has no saved robot/board presentation. Current geometry is not substituted for historical evidence.",
            )
        return CapturePresentation.model_validate_json(row[0])

    def reference_batch(
        self, camera_id: str, dataset_id: str, partition: Literal["validation", "routine"]
    ) -> ReferenceBatch:
        """Journal a frozen synthetic fixture acquisition; retries return the original bytes/times.

        One transaction freezes physical state while all surveyed fixtures are rendered.
        Restarts cannot silently turn an existing validation dataset into new measurements.
        The journal contains observations and independent survey coordinates, never X or Y.
        """
        identity = f"{camera_id}:{dataset_id}"
        with self.runtime.db.transaction() as db:
            self._load_physics()
            if camera_id not in self.cameras:
                raise CalibrationError("UNKNOWN_SYNTHETIC_CAMERA")
            request = json.dumps(
                [
                    camera_id,
                    dataset_id,
                    partition,
                    self.cameras[camera_id].fingerprint(),
                    self.board.fingerprint(),
                ]
            )
            digest = hashlib.sha256(request.encode()).hexdigest()
            prior = db.execute(
                "SELECT input_hash,body FROM calibration_reference_batches WHERE id=?", (identity,)
            ).fetchone()
            if prior:
                if prior[0] != digest:
                    raise Conflict("REFERENCE_CAPTURE_IDEMPOTENCY_CONFLICT")
                return ReferenceBatch.model_validate_json(prior[1])
            world = self.runtime._world(db)
            machine = world.calibration_machine
            if machine is None or world.cell.mode != CellMode.READY or not machine.settled:
                raise CalibrationError("SETTLED_MEASURED_CELL_REQUIRED")
            timestamp = utc_now().timestamp()
            batch = super().reference_batch(camera_id, dataset_id, partition)
            batch = batch.model_copy(
                update={
                    "captures": tuple(
                        item.model_copy(
                            update={
                                "capture": item.capture.model_copy(
                                    update={
                                        "t_b_f": machine.flange,
                                        "rgb_timestamp_s": timestamp,
                                        "depth_timestamp_s": timestamp,
                                        "robot_timestamp_s": timestamp,
                                    }
                                )
                            }
                        )
                        for item in batch.captures
                    )
                }
            )
            db.execute(
                "INSERT INTO calibration_reference_batches VALUES (?,?,?)",
                (
                    identity,
                    digest,
                    batch.model_dump_json(),
                ),
            )
            return batch

    def move_camera(
        self,
        camera_id: str,
        request_id: str,
        translation_m: tuple[float, float, float],
        rotation_rad: tuple[float, float, float],
    ) -> None:
        """Idempotent isolated physical fault. Never changes an estimated transform."""
        if camera_id not in self.cameras:
            raise CalibrationError("UNKNOWN_SYNTHETIC_CAMERA")
        if (
            not np.isfinite([translation_m, rotation_rad]).all()
            or np.linalg.norm(translation_m) > 0.15
            or np.linalg.norm(rotation_rad) > 0.25
        ):
            raise CalibrationError("SIMULATED_MOVEMENT_OUT_OF_BOUNDS")
        key = f"camera-movement:{request_id}"
        payload = json.dumps([camera_id, translation_m, rotation_rad])
        with self.runtime.db.transaction() as db:
            prior = db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
            if prior:
                if prior[0] != payload:
                    raise Conflict("FAULT_IDEMPOTENCY_CONFLICT")
                return
            world = self.runtime._world(db)
            if world.cell.mode != CellMode.READY:
                raise CalibrationError("CELL_NOT_READY")
            truth = json.loads(
                db.execute("SELECT value FROM meta WHERE key='synthetic_sensor_truth'").fetchone()[
                    0
                ]
            )
            physical = np.array(truth["cameras"][camera_id])
            physical[:3, 3] += translation_m
            physical[:3, :3] = Rotation.from_rotvec(rotation_rad).as_matrix() @ physical[:3, :3]
            truth["cameras"][camera_id] = physical.tolist()
            db.execute(
                "UPDATE meta SET value=? WHERE key='synthetic_sensor_truth'", (json.dumps(truth),)
            )
            db.execute("INSERT INTO meta VALUES (?,?)", (key, payload))
            self.runtime._write_world(
                db,
                world.model_copy(
                    update={
                        "cell": world.cell.model_copy(
                            update={"generation": world.cell.generation + 1}
                        ),
                        "timestamp": utc_now(),
                    }
                ),
            )
        self._load_physics()

    def mount_board(self, request_id: str) -> None:
        """Reinstall the unchanged keyed simulation fixture; not a changed mounting."""
        with self.runtime.db.transaction() as db:
            key = f"mount-board:{request_id}"
            if db.execute("SELECT 1 FROM meta WHERE key=?", (key,)).fetchone():
                return
            world = self.runtime._world(db)
            if world.cell.mode != CellMode.READY or world.calibration_machine is None:
                raise CalibrationError("CELL_NOT_READY")
            machine = world.calibration_machine.model_copy(
                update={
                    "board_mounted": True,
                    "tool_verification_id": None,
                    "motion_phase": "BOARD_INSTALLED",
                }
            )
            self.runtime._write_world(
                db,
                world.model_copy(update={"calibration_machine": machine, "timestamp": utc_now()}),
            )
            db.execute("INSERT INTO meta VALUES (?,?)", (key, "unchanged-keyed-fixture"))

    def planned_poses(self, partition: str, count: int = 18) -> tuple[Transform, ...]:
        # Raise the board clear of the new cell's supporting bench. This is a fixed
        # geometry constraint, not a response to a candidate or validation residual.
        poses = []
        for pose in super().planned_poses(partition, count):
            matrix = np.array(pose.matrix)
            matrix[2, 3] += 0.10
            poses.append(framed(matrix, "f", "b"))
        return tuple(poses)

    def acquire(
        self,
        camera_id: str,
        flange: Transform,
        dataset_id: str,
        index: int,
        partition: Literal["fit", "validation", "routine"],
        limits: Limits,
        *,
        settled: bool = True,
        timestamp_skew_s: float = 0,
    ) -> Capture:
        self._load_physics()
        identity = f"{dataset_id}-{camera_id}-{index:03d}"
        request = json.dumps(
            [
                camera_id,
                flange.model_dump(mode="json"),
                dataset_id,
                index,
                partition,
                limits.fingerprint(),
                self.cameras[camera_id].fingerprint(),
                settled,
                float(timestamp_skew_s),
            ],
            sort_keys=True,
        )
        digest = hashlib.sha256(request.encode()).hexdigest()
        with self.runtime.db.transaction() as db:
            previous = db.execute(
                "SELECT input_hash,body FROM calibration_captures WHERE id=?", (identity,)
            ).fetchone()
            if previous:
                if previous[0] != digest:
                    raise Conflict("CAPTURE_IDEMPOTENCY_CONFLICT")
                saved = Capture.model_validate_json(previous[1])
                if saved.board_fingerprint != self.board.fingerprint():
                    raise Conflict("CAPTURE_BOARD_CONFIGURATION_CHANGED")
                return saved
            world = self.runtime._world(db)
            machine = world.calibration_machine
            if machine is None or not machine.board_mounted:
                raise CalibrationError("CALIBRATION_BOARD_REQUIRED")
            if world.cell.mode != CellMode.READY:
                raise CalibrationError("CELL_NOT_READY")
            position = np.asarray(flange.matrix)[:3, 3]
            if (position < WORKSPACE_MIN).any() or (position > WORKSPACE_MAX).any():
                raise CalibrationError("CALIBRATION_POSE_OUTSIDE_WORKSPACE")
            # Physical collision check, not an estimation input. Use the real board
            # corners so remounting cannot invalidate a hardcoded upright envelope.
            width, height = self._physical_board.measured_dimensions_m
            corners = np.array(
                [[0, 0, 0, 1], [width, 0, 0, 1], [width, height, 0, 1], [0, height, 0, 1]]
            )
            physical_corners = (np.asarray(flange.matrix) @ self._physical_mount @ corners.T).T
            if float(physical_corners[:, 2].min()) - 0.005 <= 0.31:
                raise CalibrationError("CALIBRATION_BOARD_BENCH_CLEARANCE")
            captured = super().acquire(
                camera_id,
                flange,
                dataset_id,
                index,
                partition,
                limits,
                settled=settled,
                timestamp_skew_s=timestamp_skew_s,
            )
            # Persist the reported pose used by estimation. Noise is an explicit sensor
            # property; the renderer used the physical commanded pose above.
            reported = CalibrationMachine.model_validate(
                {
                    **machine.model_dump(),
                    "flange": captured.t_b_f,
                    "tcp": framed(
                        np.asarray(captured.t_b_f.matrix) @ np.asarray(machine.tool.t_f_tcp.matrix),
                        "tcp",
                        "b",
                    ),
                    "settled": settled,
                    "motion_phase": "CALIBRATION_CAPTURE",
                }
            )
            self.runtime._write_world(
                db,
                world.model_copy(update={"calibration_machine": reported, "timestamp": utc_now()}),
            )
            db.execute(
                "INSERT INTO calibration_captures VALUES (?,?,?)",
                (identity, digest, captured.model_dump_json()),
            )
            db.execute(
                "INSERT INTO calibration_machine_reports(capture_id,body) VALUES (?,?)",
                (identity, reported.model_dump_json()),
            )
            saved_scene = CapturePresentation(
                capture_id=identity,
                camera_id=camera_id,
                capture_fingerprint=captured.fingerprint(),
                scene=self.presentation_snapshot(
                    world.model_copy(update={"calibration_machine": reported})
                ),
            )
            db.execute(
                "INSERT INTO calibration_capture_scenes VALUES (?,?)",
                (identity, saved_scene.model_dump_json()),
            )
            return captured

    def measure_tool(self, verification_id: str) -> ToolMeasurements:
        """Independent synthetic metrology fixture: pivot contacts plus indexed axis probes."""
        with self.runtime.db.readonly_connect() as db:
            prior = db.execute(
                "SELECT body FROM calibration_tool_measurements WHERE id=?", (verification_id,)
            ).fetchone()
        if prior:
            return ToolMeasurements.model_validate_json(prior[0])
        self._load_physics()
        world = self.runtime.world()
        machine = world.calibration_machine
        if machine is None or world.cell.mode != CellMode.READY:
            raise CalibrationError("MEASURED_CELL_NOT_READY")
        # Physical tool geometry is owned by the simulator. This check supplies only
        # reported flange poses and independent probe measurements to the solver.
        physical_tool = self._physical_tool
        pivot = np.array([0, 0, 0.65])
        poses = []
        for angles in (
            (0, 0, 0),
            (0.3, 0, 0),
            (-0.3, 0, 0),
            (0, 0.3, 0),
            (0, -0.3, 0),
            (0.2, 0.2, 0.2),
        ):
            matrix = np.eye(4)
            matrix[:3, :3] = Rotation.from_euler("xyz", angles).as_matrix()
            matrix[:3, 3] = pivot - matrix[:3, :3] @ physical_tool[:3, 3]
            poses.append(framed(matrix, "f", "b"))
        probes = []
        for point in ((0, 0, 0), (0.08, 0, 0), (0, 0.08, 0), (0, 0, 0.08)):
            actual = physical_tool @ np.array([*point, 1])
            probes.append(
                ToolProbe(tcp_reference_point_m=point, measured_flange_point_m=tuple(actual[:3]))
            )
        measurements = ToolMeasurements(
            measurement_id=verification_id,
            tool=machine.tool,
            pivot_flange_poses=tuple(poses),
            probes=tuple(probes),
            machine_fingerprint=machine.fingerprint(),
            scene_epoch=world.scene_epoch,
            cell_generation=world.cell.generation,
            captured_at_utc=utc_now().isoformat(),
        )
        with self.runtime.db.transaction() as db:
            current = self.runtime._world(db)
            prior = db.execute(
                "SELECT body FROM calibration_tool_measurements WHERE id=?", (verification_id,)
            ).fetchone()
            if prior:
                return ToolMeasurements.model_validate_json(prior[0])
            self._tool_context(current, measurements)
            db.execute(
                "INSERT INTO calibration_tool_measurements VALUES (?,?)",
                (verification_id, measurements.model_dump_json()),
            )
        return measurements

    @staticmethod
    def _tool_context(world: WorldState, measurements: ToolMeasurements) -> None:
        if (
            world.calibration_machine is None
            or world.calibration_machine.fingerprint() != measurements.machine_fingerprint
            or world.scene_epoch != measurements.scene_epoch
            or world.cell.generation != measurements.cell_generation
            or world.cell.mode != CellMode.READY
        ):
            raise Conflict("CELL_CHANGED_DURING_TOOL_VERIFICATION")

    def apply_tool_check(self, measurements: ToolMeasurements, report: ToolVerification) -> None:
        """Idempotent local interlock update, after the application saved the complete check.

        A crash before this update leaves the tool blocked. A retry may complete the
        original update only while the measured cell context is still unchanged.
        Replaying a completed check never restores authorization after a later change.
        """
        if verify_measurements(measurements) != report:
            raise CalibrationError("TOOL_REPORT_RECOMPUTATION_MISMATCH")
        with self.runtime.db.transaction() as db:
            key = f"tool-check-applied:{measurements.measurement_id}"
            if db.execute("SELECT 1 FROM meta WHERE key=?", (key,)).fetchone():
                return
            row = db.execute(
                "SELECT body FROM calibration_tool_measurements WHERE id=?",
                (measurements.measurement_id,),
            ).fetchone()
            if row is None or ToolMeasurements.model_validate_json(row[0]) != measurements:
                raise CalibrationError("TOOL_MEASUREMENTS_NOT_JOURNALED")
            current = self.runtime._world(db)
            self._tool_context(current, measurements)
            machine = current.calibration_machine
            if machine is None:
                raise CalibrationError("MEASURED_CELL_REQUIRED")
            changed = CalibrationMachine.model_validate(
                {
                    **machine.model_dump(),
                    "board_mounted": False,
                    "tool_verification_id": report.verification_id if report.passed else None,
                    "settled": True,
                    "motion_phase": "TOOL_CHECK_COMPLETE" if report.passed else "TOOL_CHECK_FAILED",
                }
            )
            self.runtime._write_world(
                db,
                current.model_copy(update={"calibration_machine": changed, "timestamp": utc_now()}),
            )
            db.execute("INSERT INTO meta VALUES (?,?)", (key, report.fingerprint()))

    def fresh(self, camera_ids: tuple[str, ...], capture_prefix: str) -> SensorSnapshot:
        self._load_physics()
        world = self.runtime.world()
        machine = world.calibration_machine
        if machine is None:
            raise CalibrationError("MEASURED_CELL_REQUIRED")
        fixtures = []
        for location, color in zip(world.locations, ((40, 200, 70), (40, 200, 200)), strict=True):
            matrix = np.eye(4)
            matrix[:3, 3] = [*location.pose.position[:2], 0.155]
            fixtures.append(PhysicalBox(matrix, (0.16, 0.16, 0.31), color))
        objects = (
            *fixtures,
            *(
                PhysicalBox(
                    from_xyzw(obj.pose.position, obj.pose.quaternion_xyzw),
                    (CUBE_SIDE_M,) * 3,
                    (225, 40, 35),
                )
                for obj in world.objects
            ),
        )
        timestamp = utc_now().timestamp()
        captures = tuple(
            self.capture_objects(
                camera_id, objects, machine.flange, f"{capture_prefix}-{camera_id}", timestamp
            )
            for camera_id in camera_ids
        )
        return SensorSnapshot(
            scene_epoch=world.scene_epoch,
            step=world.step,
            cell_generation=world.cell.generation,
            machine=machine,
            captures=captures,
        )
