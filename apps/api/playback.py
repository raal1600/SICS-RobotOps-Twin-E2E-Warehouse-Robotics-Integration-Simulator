"""Presentation-only access to recorded Blender motion; never dispatches commands."""

from robotops.blender.adapter import BlenderRuntime
from robotops.blender.visualization import (
    DeliveryExecution,
    DeliveryPlayback,
    DeliverySummary,
    JobPlayback,
    VisualObject,
    VisualScene,
)
from robotops.domain.models import JobState, PresentationSnapshot, RobotCommand
from robotops.scene_geometry import cell_meshes
from robotops.workflow.engine import Engine
from robotops.workflow.store import NotFound


def deliveries(workflow: Engine) -> list[DeliverySummary]:
    world = workflow.runtime.world()
    groups: dict[str, DeliverySummary] = {}
    for job in workflow.store.execution_jobs():
        try:
            snapshot = workflow.store.load(PresentationSnapshot, job.job_id)
            epoch, started = snapshot.world.scene_epoch, snapshot.timestamp
        except NotFound:
            if job.command_id is None:
                continue  # No evidence tying this older attempt to a particular scene.
            command = workflow.store.load(RobotCommand, job.command_id)
            epoch, started = command.scene_epoch, command.timestamp
        if epoch not in groups:
            groups[epoch] = DeliverySummary(
                delivery_id=epoch,
                started_at=started,
                current=epoch == world.scene_epoch,
            )
        groups[epoch].executions.append(
            DeliveryExecution(
                job_id=job.job_id,
                order_id=job.order_id,
                product_id=job.line.product_id,
                state=job.state,
            )
        )
    if world.scene_epoch not in groups:
        groups[world.scene_epoch] = DeliverySummary(
            delivery_id=world.scene_epoch,
            started_at=world.timestamp,
            current=True,
        )
    return list(groups.values())


def delivery_playback(workflow: Engine, delivery_id: str) -> DeliveryPlayback:
    summary = next((item for item in deliveries(workflow) if item.delivery_id == delivery_id), None)
    if summary is None:
        raise NotFound(delivery_id)
    jobs = [playback(workflow, item.job_id) for item in summary.executions]
    scene = jobs[0].scene if jobs else visual_scene(workflow)
    if not jobs and scene.scene_epoch != delivery_id:
        raise NotFound(delivery_id)  # A concurrent reset changed the empty current scene.
    return DeliveryPlayback(
        delivery_id=delivery_id,
        scene=scene,
        jobs=jobs,
    )


def visual_scene(workflow: Engine, job_id: str | None = None) -> VisualScene:
    snapshot = None
    if job_id:
        try:
            snapshot = workflow.store.load(PresentationSnapshot, job_id)
        except NotFound:
            pass  # Legacy history must not be represented as a historical snapshot.
    world = snapshot.world if snapshot else workflow.runtime.world()
    return VisualScene(
        source="SAVED_START_SCENE" if snapshot else "CURRENT_WORLD_REFERENCE",
        scene_epoch=world.scene_epoch,
        timestamp=snapshot.timestamp if snapshot else world.timestamp,
        cell_mode=world.cell.mode,
        objects=[VisualObject.model_validate(item) for item in cell_meshes(world.model_dump())],
    )


def playback(workflow: Engine, job_id: str) -> JobPlayback:
    job = workflow.store.job(job_id)
    result = JobPlayback(
        job_id=job_id,
        command_id=job.command_id,
        job_state=job.state,
        status="UNAVAILABLE",
        reason="No Blender motion was recorded for this command.",
        scene=visual_scene(workflow, job_id),
        product_id=job.line.product_id,
        events=[event for event in workflow.store.timeline(job.order_id) if event.job_id == job_id],
    )
    runtime = workflow.runtime
    if not isinstance(runtime, BlenderRuntime):
        return result.model_copy(update={"reason": "Headless runtime has no Blender recording."})
    if job.command_id is None:
        return result.model_copy(
            update={
                "status": "UNAVAILABLE" if job.state == JobState.FAILED else "WAITING",
                "reason": "No robot command dispatched. No motion is inferred.",
            }
        )
    command = workflow.store.load(RobotCommand, job.command_id)
    try:
        recording = runtime.motion(command)
        if recording is None:
            saved = runtime.command_artifact(command.command_id, "scene.blend")
            return result.model_copy(
                update={
                    "status": "WAITING" if job.state == JobState.EXECUTING else "UNAVAILABLE",
                    "can_import": saved is not None,
                    "reason": "Load the original saved Blender animation."
                    if saved
                    else result.reason,
                }
            )
    except (ValueError, OSError, KeyError):
        return result.model_copy(
            update={"reason": "Recording unavailable or integrity check failed."}
        )
    status = (
        "RECORDED"
        if recording.complete
        else ("RECORDING" if job.state == JobState.EXECUTING else "PARTIAL")
    )
    return result.model_copy(
        update={
            "status": status,
            "recording": recording,
            "reason": "Recorded simulator poses. Business outcome remains the job status above.",
        }
    )
