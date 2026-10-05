import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
from math import dist
from pathlib import Path
from typing import Any

from robotops.blender.visualization import MotionRecording
from robotops.cell.hkm_execution import final_machine, receipt_metadata
from robotops.cell.runtime import CommunicationTimeout, SyntheticRuntime
from robotops.config import Settings
from robotops.domain.models import (
    CellMode,
    CommandReceipt,
    CommandStatus,
    Fault,
    RobotCommand,
    WorldState,
    new_id,
    utc_now,
)
from robotops.workflow.store import digest, metadata

SCRIPT = Path(__file__).resolve().parents[2] / "blender" / "scripts" / "runtime.py"


def executable() -> str:
    configured = os.environ.get("BLENDER_EXECUTABLE") or shutil.which("blender")
    if configured:
        return configured
    windows = Path("C:/Program Files/Blender Foundation/Blender 5.2/blender.exe")
    if windows.exists():
        return str(windows)
    raise FileNotFoundError(
        "Blender 5.2.1 LTS required. Set BLENDER_EXECUTABLE; no silent fallback."
    )


class BlenderRuntime(SyntheticRuntime):
    def __init__(self, path: Path, settings: Settings | None = None):
        self.executable = executable()
        self._import_lock = threading.Lock()
        self.artifacts = path.parent / "blender-artifacts"
        self.artifacts.mkdir(parents=True, exist_ok=True)
        super().__init__(path, settings)

    def _exchange(
        self, operation: str, world: WorldState, command: RobotCommand | None = None
    ) -> Path:
        directory = self.artifacts / new_id()
        directory.mkdir()
        request = {
            "schema_version": world.schema_version,
            "operation": operation,
            "world": world.model_dump(mode="json"),
            "command": command.model_dump(mode="json") if command else None,
            "visual_frame_seconds": self.settings.visual_frame_seconds,
        }
        if world.schema_version == "2.0":
            request["durable_payload_hash"] = digest(command) if command else None
        (directory / "request.json").write_text(json.dumps(request), encoding="utf-8")
        return directory

    def _invoke(self, directory: Path, *, record_existing: bool = False) -> None:
        args = [
            self.executable,
            "--background",
            "--factory-startup",
            "--disable-autoexec",
            "--python-exit-code",
            "2",
            "--python",
            str(SCRIPT),
            "--",
            str(directory.resolve()),
        ]
        if record_existing:
            args.append("--record-existing")
        # On Windows hybrid CPUs, a background process can be assigned only
        # efficiency cores while the browser is active. Use Blender's scoped
        # QoS option; leave process deadlines, render settings and OS policy alone.
        if sys.platform == "win32":
            args[args.index("--python") : args.index("--python")] = ["--qos", "high"]
        try:
            process = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=self.settings.runtime_timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            output = "\n".join(
                value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value
                for value in (exc.stdout, exc.stderr)
                if value
            )
            (directory / ("replay.log" if record_existing else "runtime.log")).write_text(
                output + "\n" + str(exc), encoding="utf-8"
            )
            raise CommunicationTimeout("BLENDER_PROCESS_TIMEOUT") from exc
        (directory / ("replay.log" if record_existing else "runtime.log")).write_text(
            process.stdout + process.stderr, encoding="utf-8"
        )
        if process.returncode:
            raise CommunicationTimeout("BLENDER_PROCESS_FAILED:" + str(process.returncode))

    def _complete(self, command: RobotCommand, directory: Path) -> CommandReceipt | None:
        response_path = directory / "response.json"
        if not response_path.exists():
            return None
        try:
            response = json.loads(response_path.read_text(encoding="utf-8"))
            world = WorldState.model_validate(response["world"])
            if (
                response["command_id"] != command.command_id
                or response["effect_count"] != 1
                or world.scene_epoch != command.scene_epoch
                or response["scene_sha256"]
                != hashlib.sha256((directory / "scene.blend").read_bytes()).hexdigest()
            ):
                return None
            request = json.loads((directory / "request.json").read_text(encoding="utf-8"))
            original_world = WorldState.model_validate(request["world"])
            if command.schema_version == "2.0":
                if (
                    response.get("schema_version") != "2.0"
                    or response.get("durable_payload_hash") != digest(command)
                    or request.get("durable_payload_hash") != digest(command)
                    or RobotCommand.model_validate(request["command"]) != command
                    or response.get("runtime_profile_version") != "hkm_inspired_v1"
                    or world.schema_version != "2.0"
                    or self.rejection_reason(original_world, command, None) is not None
                ):
                    return None
                robot, tools = final_machine(original_world, command)
                expected_objects = tuple(
                    obj.model_copy(
                        update={
                            "location_id": command.destination_id,
                            "pose": command.target_pose,
                            "attached": False,
                        }
                    )
                    if obj.product.product_id == command.product_id
                    else obj
                    for obj in original_world.objects
                )
                expected = original_world.model_copy(
                    update={
                        "objects": expected_objects,
                        "step": original_world.step + 1,
                        "timestamp": world.timestamp,
                        "robot_state": robot,
                        "tool_state": tools,
                    }
                )
                normalized_objects = []
                for actual, intended in zip(world.objects, expected.objects, strict=True):
                    if (
                        dist(actual.pose.position, intended.pose.position) > 1e-6
                        or min(
                            dist(actual.pose.quaternion_xyzw, intended.pose.quaternion_xyzw),
                            dist(
                                actual.pose.quaternion_xyzw,
                                tuple(-v for v in intended.pose.quaternion_xyzw),
                            ),
                        )
                        > 1e-6
                        or actual.pose.model_copy(
                            update={
                                "position": intended.pose.position,
                                "quaternion_xyzw": intended.pose.quaternion_xyzw,
                            }
                        )
                        != intended.pose
                    ):
                        return None
                    normalized_objects.append(actual.model_copy(update={"pose": intended.pose}))
                if world.model_copy(update={"objects": tuple(normalized_objects)}) != expected:
                    return None
            with self.db.transaction() as db:
                row = db.execute(
                    "SELECT receipt,payload_hash,command FROM controller_journal WHERE id=?",
                    (command.command_id,),
                ).fetchone()
                if row is None:
                    return None
                original = CommandReceipt.model_validate_json(row[0])
                if row[1] != digest(command) or RobotCommand.model_validate_json(row[2]) != command:
                    return None
                if original.status == CommandStatus.SUCCEEDED:
                    return original
                current = self._world(db)
                if current.scene_epoch != world.scene_epoch or world.step != current.step + 1:
                    return None
                if (
                    command.schema_version == "2.0"
                    and current.model_copy(
                        update={"cell": original_world.cell, "timestamp": original_world.timestamp}
                    )
                    != original_world
                ):
                    # The request is an exchange artifact, not authoritative state.
                    # Bind its entire starting world to the durable controller row;
                    # only asynchronous logical cell updates are allowed in flight.
                    return None
                cell = current.cell
                if cell.mode == CellMode.BUSY and cell.generation == command.cell_generation:
                    cell = cell.model_copy(
                        update={"mode": CellMode.READY, "reason": "BLENDER_COMMAND_FINISHED"}
                    )
                world = world.model_copy(update={"cell": cell})
                self._write_world(db, world)
                receipt = original.model_copy(
                    update={
                        **receipt_metadata(original_world, command, effect=True),
                        "status": CommandStatus.SUCCEEDED,
                        "effect_count": 1,
                        "reason": "BLENDER_PICK_APPLIED",
                        "timestamp": utc_now(),
                    }
                )
                receipt = CommandReceipt.model_validate_json(receipt.model_dump_json())
                db.execute(
                    "UPDATE controller_journal SET receipt=? WHERE id=?",
                    (receipt.model_dump_json(), command.command_id),
                )
                self._motion_events(db, command, world)
                self._event(db, command, world, "PICK_EFFECT", "BLENDER_ATTACH_TRANSFER_DETACH")
                self._event(db, command, world, "COMMAND_SUCCEEDED", "BLENDER_CHECKPOINT_COMMITTED")
                db.execute(
                    "INSERT OR REPLACE INTO meta VALUES ('latest_artifact',?)",
                    (str(directory / "capture.png"),),
                )
                return receipt
        except (ValueError, KeyError, OSError):
            return None

    def journal(self, command_id: str) -> CommandReceipt | None:
        receipt = super().journal(command_id)
        if receipt and receipt.status in {CommandStatus.RUNNING, CommandStatus.STATUS_UNKNOWN}:
            with self.db.connect() as db:
                row = db.execute(
                    "SELECT command FROM controller_journal WHERE id=?", (command_id,)
                ).fetchone()
                exchange = db.execute(
                    "SELECT value FROM meta WHERE key=?", ("exchange:" + command_id,)
                ).fetchone()
            if row and exchange:
                completed = self._complete(
                    RobotCommand.model_validate_json(row[0]), Path(exchange[0])
                )
                if completed:
                    return completed
            return receipt.model_copy(
                update={
                    "status": CommandStatus.STATUS_UNKNOWN,
                    "reason": "BLENDER_CHECKPOINT_UNCERTAIN",
                }
            )
        return receipt

    def apply(self, command: RobotCommand, fault: Fault | None = None) -> CommandReceipt:
        command = RobotCommand.model_validate_json(command.model_dump_json())
        with self.db.transaction() as db:
            world = self._world(db)
            existing = db.execute(
                "SELECT 1 FROM controller_journal WHERE id=?", (command.command_id,)
            ).fetchone()
            unresolved = any(
                CommandReceipt.model_validate_json(row[0]).status
                in {CommandStatus.RUNNING, CommandStatus.STATUS_UNKNOWN}
                for row in db.execute("SELECT receipt FROM controller_journal")
            )
            if unresolved and not existing and world.cell.mode == CellMode.READY:
                world = world.model_copy(
                    update={
                        "cell": world.cell.model_copy(
                            update={"mode": CellMode.BUSY, "reason": "UNKNOWN_COMMAND_QUARANTINE"}
                        )
                    }
                )
                self._write_world(db, world)
            if (
                existing
                or self.rejection_reason(world, command, fault) is not None
                or fault in {Fault.CELL_FAULT, Fault.LOGICAL_ESTOP}
            ):
                receipt = self._execute(db, command, fault)
                directory = None
            else:
                directory = self._exchange("pick", world, command)
                receipt = CommandReceipt(
                    **metadata(command, command.command_id),
                    **receipt_metadata(world, command),
                    command_id=command.command_id,
                    job_id=command.job_id,
                    scene_epoch=command.scene_epoch,
                    status=CommandStatus.RUNNING,
                    reason="BLENDER_INTENT_DURABLE",
                    effect_count=0,
                    payload_hash=digest(command),
                )
                db.execute(
                    "INSERT INTO controller_journal VALUES (?,?,?,?)",
                    (
                        command.command_id,
                        digest(command),
                        command.model_dump_json(),
                        receipt.model_dump_json(),
                    ),
                )
                db.execute(
                    "INSERT INTO meta VALUES (?,?)",
                    ("exchange:" + command.command_id, str(directory)),
                )
                self._event(db, command, world, "COMMAND_CREATED", "DURABLE_BLENDER_INTENT")
                self._event(db, command, world, "COMMAND_DISPATCHED", "BOUNDED_PROCESS")
                self._event(db, command, world, "COMMAND_ACCEPTED", "PRECONDITIONS_PASSED")
                self._event(db, command, world, "COMMAND_RUNNING", "BLENDER_PROCESS")
                if fault:
                    self._event(db, command, world, "FAULT_INJECTED", fault.value)
                self._write_world(
                    db,
                    world.model_copy(
                        update={
                            "cell": world.cell.model_copy(
                                update={"mode": CellMode.BUSY, "reason": "BLENDER_RUNNING"}
                            )
                        }
                    ),
                )
        if directory:
            self._invoke(directory)
            completed = self._complete(command, directory)
            if completed is None:
                raise CommunicationTimeout("BLENDER_REPLY_OR_CHECKPOINT_INVALID")
            receipt = completed
        if fault in {Fault.DROP_ACK_AFTER_EFFECT, Fault.DROP_ACK_BEFORE_EFFECT}:
            raise CommunicationTimeout("ACKNOWLEDGEMENT_LOST")
        return receipt

    def reset(self, scene_epoch: str | None = None) -> WorldState:
        world = super().reset(scene_epoch=scene_epoch)
        directory = self._exchange("reset", world)
        self._invoke(directory)
        return world

    def capture(self, path: Path) -> Path:
        directory = self._exchange("capture", self.world())
        self._invoke(directory)
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(directory / "capture.png", path)
        return path

    def manifest(self) -> dict[str, Any]:
        version = subprocess.run(
            [self.executable, "--version"], capture_output=True, text=True, check=True
        )
        root = SCRIPT.parents[2]
        # Entry-point identity alone does not identify the bounded v2 runtime.
        # Hash every checked-in runtime helper and its declarative fixture data.
        closure_files = (
            "blender/scripts/runtime.py",
            "blender/scripts/hkm_runtime.py",
            "blender/scripts/hkm_scene.py",
            "robotops/hkm_geometry.py",
            "robotops/scene_geometry.py",
            "robotops/presentation_io.py",
            "robotops/robotics/catalogue_data.py",
            "robotops/robotics/catalogue-v1.json",
        )
        closure = {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in closure_files
        }
        return {
            "adapter": "blender-batch-1",
            "blender": version.stdout.splitlines()[0],
            "script_sha256": hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
            "runtime_files_sha256": closure,
            "runtime_closure_sha256": hashlib.sha256(
                json.dumps(closure, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            "gpu_required": False,
            "cpu_qos": "high" if sys.platform == "win32" else "os_default",
        }

    def latest_artifact(self) -> Path | None:
        with self.db.connect() as db:
            row = db.execute("SELECT value FROM meta WHERE key='latest_artifact'").fetchone()
        if row is None:
            return None
        path = Path(row[0]).resolve()
        if not path.is_relative_to(self.artifacts.resolve()):
            raise ValueError("ARTIFACT_OUTSIDE_RUNTIME")
        return path if path.is_file() else None

    def command_artifact(self, command_id: str, name: str) -> Path | None:
        """Only fixed artifact names under the original durable command exchange."""
        if name not in {"motion.json", "scene.blend", "response.json", "capture.png"}:
            raise ValueError("INVALID_ARTIFACT_NAME")
        with self.db.connect() as db:
            row = db.execute(
                "SELECT value FROM meta WHERE key=?", ("exchange:" + command_id,)
            ).fetchone()
        if row is None:
            return None
        path = (Path(row[0]) / name).resolve()
        if not path.is_relative_to(self.artifacts.resolve()):
            raise ValueError("ARTIFACT_OUTSIDE_RUNTIME")
        return path if path.is_file() else None

    def motion(self, command: RobotCommand) -> MotionRecording | None:
        path = self.command_artifact(command.command_id, "motion.json")
        if path is None:
            return None
        if path.stat().st_size > (32_000_000 if command.schema_version == "2.0" else 2_000_000):
            raise ValueError("RECORDING_TOO_LARGE")
        recording = MotionRecording.model_validate_json(path.read_bytes())
        if recording.schema_version != command.schema_version:
            raise ValueError("RECORDING_SCHEMA_MISMATCH")
        if (
            recording.command_id,
            recording.job_id,
            recording.scene_epoch,
            recording.product_id,
        ) != (command.command_id, command.job_id, command.scene_epoch, command.product_id):
            raise ValueError("RECORDING_IDENTITY_MISMATCH")
        response_path = self.command_artifact(command.command_id, "response.json")
        if response_path:
            response = json.loads(response_path.read_text(encoding="utf-8"))
            expected = response.get("motion_sha256")
            if expected and hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError("RECORDING_HASH_MISMATCH")
        return recording

    def import_motion(self, command: RobotCommand) -> None:
        with self._import_lock:
            if self.motion(command) is not None:
                return
            scene_path = self.command_artifact(command.command_id, "scene.blend")
            if scene_path is None:
                raise ValueError("NO_SAVED_SCENE")
            # Fixed read-only scene export; does not call apply, journal or _complete.
            self._invoke(scene_path.parent, record_existing=True)
            if self.motion(command) is None:
                raise ValueError("NO_RECORDED_MOTION")
