from datetime import datetime

from robotops.brain.deterministic import observed_obstacles
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
from robotops.robotics.catalogue import product_spec, tool_spec
from robotops.robotics.selector import select_tool
from robotops.robotics.trajectory import plan_trajectory, validate_trajectory


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
        expected_target = self.settings.target_pose(plan.product_id, destination)
        if destination.location_id != plan.destination_id or plan.target_pose != expected_target:
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
        if self.settings.is_hkm:
            self._validate_hkm(plan, observation, now or utc_now())
        elif plan.schema_version != "1.0":
            raise ValueError("LEGACY_PROFILE_REQUIRES_VERSION_1")
        return plan

    def _validate_hkm(self, plan: ActionPlan, observation: WorldObservation, now: datetime) -> None:
        observation = WorldObservation.model_validate(observation.model_dump())
        if plan.schema_version != "2.0" or observation.schema_version != "2.0":
            raise ValueError("HKM_PROFILE_REQUIRES_VERSION_2")
        machine = observation.machine_telemetry
        if machine is None:
            raise ValueError("OBSERVED_MACHINE_TELEMETRY_REQUIRED")
        age = (now - machine.captured_at).total_seconds()
        if age < 0 or age > self.settings.freshness_seconds:
            raise ValueError("STALE_OR_FUTURE_MACHINE_TELEMETRY")
        if (
            machine.source != "SIMULATED_CELL_TELEMETRY"
            or machine.cell_generation != observation.cell_generation
            or machine.tcp_pose.frame_id != self.settings.frame_id
            or machine.tcp_pose.calibration_version != self.settings.calibration_version
        ):
            raise ValueError("MACHINE_TELEMETRY_METADATA_MISMATCH")
        if plan.brain_version not in {"deterministic-hkm-1", "structured-1"}:
            raise ValueError("HKM_BRAIN_VERSION_MISMATCH")
        product = next(
            product for product in self.settings.products if product.product_id == plan.product_id
        )
        specification = product_spec(product.sku)
        if plan.source_id != self.settings.source_for(product.product_id):
            raise ValueError("FIXTURE_SOURCE_MISMATCH")
        selection = select_tool(specification, machine.tool_state, product_id=product.product_id)
        if plan.selected_tool_id != selection.selected_tool_id or plan.tool_selection != selection:
            raise ValueError("TOOL_SELECTION_EVIDENCE_MISMATCH")
        if plan.trajectory is None or plan.selected_tool_id is None:
            raise ValueError("HKM_TRAJECTORY_AND_TOOL_REQUIRED")
        source = next(obj for obj in observation.objects if obj.product_id == plan.product_id)
        barriers = observed_obstacles(self.settings, observation, plan.product_id)
        selected = tool_spec(plan.selected_tool_id)
        validate_trajectory(
            plan.trajectory,
            specification,
            selected,
            obstacles=barriers,
            source_pose=source.pose,
            target_pose=plan.target_pose,
            tool_state=machine.tool_state,
        )
        # Rebuilding the bounded deterministic profile also verifies preparation
        # dock poses, phases, timing and the original observed machine start pose.
        expected = plan_trajectory(
            specification,
            selected,
            source.pose,
            plan.target_pose,
            initial_tcp=machine.tcp_pose,
            tool_state=machine.tool_state,
            obstacles=barriers,
        )
        if plan.trajectory != expected or plan.grasp_pose != expected.grasp_pose:
            raise ValueError("TRAJECTORY_INTENT_MISMATCH")
