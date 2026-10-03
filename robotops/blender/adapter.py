import hashlib
import json
import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Any

from robotops.blender.visualization import MotionRecording
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
            "schema_version": "1.0",
            "operation": operation,
            "world": world.model_dump(mode="json"),
            "command": command.model_dump(mode="json") if command else None,
            "visual_frame_seconds": self.settings.visual_frame_seconds,
        }
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
        try:
            process = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=self.settings.runtime_timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            (directory / ("replay.log" if record_existing else "runtime.log")).write_text(
                str(exc), encoding="utf-8"
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
            with self.db.transaction() as db:
                row = db.execute(
                    "SELECT receipt FROM controller_journal WHERE id=?", (command.command_id,)
                ).fetchone()
                if row is None:
                    return None
                original = CommandReceipt.model_validate_json(row[0])
                if original.status == CommandStatus.SUCCEEDED:
                    return original
                current = self._world(db)
                if current.scene_epoch != world.scene_epoch or world.step != current.step + 1:
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
                        "status": CommandStatus.SUCCEEDED,
                        "effect_count": 1,
                        "reason": "BLENDER_PICK_APPLIED",
                        "timestamp": utc_now(),
                    }
                )
                db.execute(
                    "UPDATE controller_journal SET receipt=? WHERE id=?",
                    (receipt.model_dump_json(), command.command_id),
                )
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
        return {
            "adapter": "blender-batch-1",
            "blender": version.stdout.splitlines()[0],
            "script_sha256": hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
            "gpu_required": False,
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
        if path.stat().st_size > 2_000_000:
            raise ValueError("RECORDING_TOO_LARGE")
        recording = MotionRecording.model_validate_json(path.read_bytes())
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
