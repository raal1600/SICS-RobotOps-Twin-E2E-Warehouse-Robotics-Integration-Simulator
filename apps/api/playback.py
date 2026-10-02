"""Presentation-only access to recorded Blender motion; never dispatches commands."""

from robotops.blender.adapter import BlenderRuntime
from robotops.blender.visualization import JobPlayback
from robotops.domain.models import JobState, RobotCommand
from robotops.workflow.engine import Engine


def playback(workflow: Engine, job_id: str) -> JobPlayback:
    job = workflow.store.job(job_id)
    result = JobPlayback(
        job_id=job_id,
        command_id=job.command_id,
        job_state=job.state,
        status="UNAVAILABLE",
        reason="No Blender motion was recorded for this command.",
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
