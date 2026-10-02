from datetime import datetime

from robotops.config import Settings
from robotops.domain.models import (
    ActionPlan,
    CellMode,
    CellState,
    InventoryLocation,
    PickJob,
    WorldObservation,
    utc_now,
)
from robotops.observation.quality import quality


class ActionValidator:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def validate(
        self,
        plan: ActionPlan,
        job: PickJob,
        observation: WorldObservation,
        cell: CellState,
        destination: InventoryLocation,
        *,
        now: datetime | None = None,
    ) -> ActionPlan:
        plan = ActionPlan.model_validate_json(plan.model_dump_json())
        expected = (
            job.job_id,
            job.order_id,
            job.line.order_line_id,
            job.line.product_id,
            job.line.source_id,
            job.line.destination_id,
            job.run_id,
            job.correlation_id,
        )
        actual = (
            plan.job_id,
            plan.order_id,
            plan.order_line_id,
            plan.product_id,
            plan.source_id,
            plan.destination_id,
            plan.run_id,
            plan.correlation_id,
        )
        if expected != actual:
            raise ValueError("PLAN_OWNERSHIP_MISMATCH")
        if cell.mode != CellMode.READY:
            raise ValueError("CELL_NOT_READY")
        if (
            plan.cell_generation != cell.generation
            or observation.cell_generation != cell.generation
        ):
            raise ValueError("CELL_GENERATION_MISMATCH")
        if (
            plan.scene_epoch != observation.scene_epoch
            or plan.observation_id != observation.observation_id
        ):
            raise ValueError("OBSERVATION_IDENTITY_MISMATCH")
        reason = quality(observation, plan.product_id, self.settings, now or utc_now())
        if reason:
            raise ValueError(reason)
        obj = next(obj for obj in observation.objects if obj.product_id == plan.product_id)
        if obj.location_id != plan.source_id or plan.source_id not in observation.covered_locations:
            raise ValueError("SOURCE_NOT_OBSERVED")
        if destination.location_id != plan.destination_id or plan.target_pose != destination.pose:
            raise ValueError("DESTINATION_MISMATCH")
        if (
            plan.target_pose.frame_id != self.settings.frame_id
            or plan.target_pose.calibration_version != self.settings.calibration_version
        ):
            raise ValueError("SPATIAL_METADATA_MISMATCH")
        if not all(
            low <= value <= high
            for low, value, high in zip(
                self.settings.workspace_min,
                plan.target_pose.position,
                self.settings.workspace_max,
                strict=True,
            )
        ):
            raise ValueError("WORKSPACE_BOUNDS")
        return plan
