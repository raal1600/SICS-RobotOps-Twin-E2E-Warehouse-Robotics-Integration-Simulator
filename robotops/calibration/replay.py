"""Read-only 3D playback from committed controller reports and saved scene geometry."""

from functools import lru_cache

import numpy as np

from robotops.blender.visualization import (
    MotionRecording,
    VisualFrame,
    VisualScene,
    VisualTransform,
)
from robotops.calibration.contracts import CalibrationArtifact
from robotops.calibration.errors import CalibrationError
from robotops.calibration.lifecycle import CalibrationStore
from robotops.calibration.visualization import cell_geometry
from robotops.cell.calibration_motion import ControllerFrame
from robotops.cell.runtime import SyntheticRuntime
from robotops.domain.models import CommandStatus, PresentationSnapshot, RobotCommand
from robotops.workflow.store import NotFound, Store


def controller_recording(
    store: Store, runtime: SyntheticRuntime, command: RobotCommand
) -> MotionRecording | None:
    intent = command.calibrated_plan
    if intent is None:
        return None
    try:
        snapshot = store.load(PresentationSnapshot, command.job_id)
        scene = store.load(VisualScene, command.job_id)
    except NotFound:
        return None  # Earlier prototypes without saved camera geometry stay honestly unavailable.
    with store.readonly_connect() as db:
        artifact = CalibrationStore._record(
            db, "artifact", intent.observed_object.binding.artifact_id, CalibrationArtifact
        )
    with runtime.db.readonly_connect() as db:
        rows = db.execute(
            "SELECT body FROM calibration_motion_frames WHERE command_id=? ORDER BY sample_index",
            (command.command_id,),
        ).fetchall()
    if not rows:
        return None
    receipt = runtime.recorded_journal(command.command_id)
    return _build_recording(
        snapshot.model_dump_json(),
        scene.model_dump_json(),
        artifact.model_dump_json(),
        command.model_dump_json(),
        tuple(row[0] for row in rows),
        bool(
            receipt
            and (
                receipt.status == CommandStatus.SUCCEEDED
                or receipt.calibrated_receipt
                and receipt.calibrated_receipt.motion_without_transfer
            )
        ),
    )


@lru_cache(maxsize=8)
def _build_recording(
    snapshot_json: str,
    scene_json: str,
    artifact_json: str,
    command_json: str,
    rows: tuple[str, ...],
    motion_completed: bool,
) -> MotionRecording:
    # Only immutable input bytes are cached, bounded to eight recordings. Every GET
    # still reads persisted identities/status; a changed input cannot reuse a result.
    snapshot = PresentationSnapshot.model_validate_json(snapshot_json)
    scene = VisualScene.model_validate_json(scene_json)
    artifact = CalibrationArtifact.model_validate_json(artifact_json)
    command = RobotCommand.model_validate_json(command_json)
    intent = command.calibrated_plan
    if intent is None:
        raise CalibrationError("MEASURED_REPLAY_COMMAND_REQUIRED")
    reports = [ControllerFrame.model_validate_json(row) for row in rows]
    originals = {obj.name: obj for obj in scene.objects}
    frames = []
    for report in reports:
        world = snapshot.world.model_copy(
            update={
                "calibration_machine": report.machine,
                "objects": tuple(
                    obj.model_copy(update={"pose": report.object_pose, "attached": report.attached})
                    if obj.product.product_id == command.product_id
                    else obj
                    for obj in snapshot.world.objects
                ),
            }
        )
        # Camera geometry comes only from the saved scene, never today's sensor layout.
        shapes, _ = cell_geometry(world, artifact.candidate.board, {}, np.eye(4), {})
        transforms = {
            obj.name: VisualTransform(
                position=obj.position,
                quaternion_xyzw=obj.quaternion_xyzw or (0, 0, 0, 1),
                scale=tuple(
                    size / original
                    for size, original in zip(obj.size, originals[obj.name].size, strict=True)
                ),
                visible=obj.visible if obj.visible is not None else True,
            )
            for obj in shapes
            if obj.name in originals
        }
        frames.append(
            VisualFrame.model_validate(
                {
                    "schema_version": "3.0",
                    "frame": report.index + 1,
                    "phase": report.machine.motion_phase,
                    "positions": {obj.name: obj.position for obj in shapes},
                    "transforms": transforms,
                    "sim_time_s": report.sim_time_s,
                    "active_tool_id": report.machine.tool.tool_id,
                    "rack_tool_ids": (),
                    "attached_product_id": command.product_id if report.attached else None,
                }
            )
        )
    duration = intent.waypoints[-1].sim_time_s
    total = round(duration * 24) + 1
    return MotionRecording(
        schema_version="3.0",
        source="SYNTHETIC_CONTROLLER_REPORTS",
        command_id=command.command_id,
        job_id=command.job_id,
        scene_epoch=command.scene_epoch,
        product_id=command.product_id,
        frame_id="b",
        total_frames=total,
        complete=motion_completed and len(frames) == total,
        objects=scene.objects,
        frames=frames,
        robot_profile_version="synthetic_calibration_gantry_v1",
        kinematics_version="IDEAL_GANTRY_GIMBAL_V1",
        calibration_version="synthetic-gantry-geometry-1",
        frame_tree_version="base-optical-explicit-1",
        simulated_duration_s=duration,
    )
