"""Blender presentation of measured-controller evidence, never execution authority."""

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING

from robotops.blender.visualization import VisualScene
from robotops.calibration.replay import controller_recording
from robotops.domain.models import RobotCommand, new_id
from robotops.workflow.store import Store

if TYPE_CHECKING:
    from robotops.blender.adapter import BlenderRuntime


def workflow(runtime: "BlenderRuntime") -> Store:
    with runtime.db.readonly_connect() as db:
        row = db.execute("SELECT value FROM meta WHERE key='calibration_workflow_name'").fetchone()
    if row is None or Path(row[0]).name != row[0]:
        raise ValueError("MEASURED_PRESENTATION_STORE_NOT_BOUND")
    return Store(runtime.db.path.with_name(row[0]))


def present(runtime: "BlenderRuntime", command: RobotCommand | None = None) -> Path:
    """Called only by explicit mutation/capture actions, never a GET or reconnect.

    A command's first presentation attempt has a durable exchange identity. Repeated
    dispatch/reconciliation cannot render a second physical story or reapply a pick.
    Artifacts are supplementary: controller receipts retain their original outcome.
    """
    with runtime._import_lock:
        if command is not None:
            with runtime.db.readonly_connect() as db:
                prior = db.execute(
                    "SELECT value FROM meta WHERE key=?", ("exchange:" + command.command_id,)
                ).fetchone()
            if prior:
                return Path(prior[0])
        store = workflow(runtime)
        if command is not None:
            scene = store.load(VisualScene, command.job_id)
            recording = controller_recording(store, runtime, command)
            if recording is None or not recording.complete:
                raise ValueError("COMMITTED_CONTROLLER_RECORDING_REQUIRED")
        else:
            # The sensor adapter supplies physical geometry; no estimator reads it.
            from robotops.calibration.artifacts import SensorArtifacts
            from robotops.cell.calibration_sensor import ControllerSensor

            sensor = ControllerSensor(
                runtime, SensorArtifacts(store.path.parent / "calibration" / "images")
            )
            scene = sensor.presentation_snapshot(runtime.world())
            recording = None
        directory = runtime.artifacts / new_id()
        directory.mkdir()
        request = {
            "schema_version": "3.0",
            "operation": "present_committed_controller" if command else "present_current_scene",
            "scene": scene.model_dump(mode="json"),
            "recording": recording.model_dump(mode="json") if recording else None,
        }
        (directory / "request.json").write_text(
            json.dumps(request, allow_nan=False), encoding="utf-8"
        )
        if command is not None:
            with runtime.db.transaction() as db:
                db.execute(
                    "INSERT INTO meta VALUES (?,?)",
                    ("exchange:" + command.command_id, str(directory)),
                )
        runtime._invoke(directory)
        response = json.loads((directory / "response.json").read_text(encoding="utf-8"))
        if response.get("authority") != "PRESENTATION_ONLY_NO_EXECUTION":
            raise ValueError("BLENDER_PRESENTATION_RESPONSE_INVALID")
        for name in (
            "request.json",
            "scene.blend",
            "capture.png",
            *(["motion.json"] if command else []),
        ):
            if hashlib.sha256((directory / name).read_bytes()).hexdigest() != response.get(
                "hashes", {}
            ).get(name):
                raise ValueError("BLENDER_PRESENTATION_HASH_MISMATCH:" + name)
        if command is not None and runtime.motion(command) is None:
            raise ValueError("BLENDER_EVALUATED_RECORDING_MISSING")
        with runtime.db.transaction() as db:
            db.execute(
                "INSERT OR REPLACE INTO meta VALUES ('latest_artifact',?)",
                (str(directory / "capture.png"),),
            )
        return directory
