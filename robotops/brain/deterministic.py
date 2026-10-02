from robotops.domain.models import (
    ActionPlan,
    InventoryLocation,
    PickJob,
    WorldObservation,
    stable_id,
)
from robotops.workflow.store import metadata


class DeterministicBrain:
    def plan(
        self, job: PickJob, observation: WorldObservation, destination: InventoryLocation
    ) -> ActionPlan:
        return ActionPlan(
            **metadata(job, observation.observation_id, observation.timestamp),
            action_plan_id=stable_id(job.job_id, observation.observation_id),
            job_id=job.job_id,
            order_id=job.order_id,
            order_line_id=job.line.order_line_id,
            product_id=job.line.product_id,
            source_id=job.line.source_id,
            destination_id=job.line.destination_id,
            target_pose=destination.pose,
            scene_epoch=observation.scene_epoch,
            observation_id=observation.observation_id,
            cell_generation=observation.cell_generation,
        )


def parse_structured_output(payload: str) -> ActionPlan:
    """Optional provider boundary only. It cannot execute code or send robot commands."""
    return ActionPlan.model_validate_json(payload)
