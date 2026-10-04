from robotops.config import Settings
from robotops.domain.models import (
    ActionPlan,
    InventoryLocation,
    PickJob,
    WorldObservation,
    stable_id,
)
from robotops.observation.quality import quality
from robotops.robotics.catalogue import load_catalogue, product_spec, tool_spec
from robotops.robotics.models import CollisionObstacle
from robotops.robotics.selector import select_tool
from robotops.robotics.trajectory import default_obstacles, plan_trajectory, product_obstacles
from robotops.workflow.store import metadata


def observed_obstacles(
    settings: Settings, observation: WorldObservation, moving_product_id: str
) -> tuple[CollisionObstacle, ...]:
    """Use only explicit observed product poses plus static catalogue fixtures."""
    products = {product.product_id: product for product in settings.products}
    if any(obj.product_id not in products for obj in observation.objects):
        raise ValueError("UNKNOWN_OBSERVED_PRODUCT")
    sensed = []
    for product_id, product in products.items():
        reason = quality(observation, product_id, settings, observation.timestamp)
        if reason:
            raise ValueError(reason)
        obj = next(obj for obj in observation.objects if obj.product_id == product_id)
        if obj.location_id not in observation.covered_locations:
            raise ValueError("COLLISION_OBSERVATION_COVERAGE_INSUFFICIENT")
        sensed.append((product_id, product_spec(product.sku), obj.pose))
    return default_obstacles() + product_obstacles(sensed, exclude_product_id=moving_product_id)


class DeterministicBrain:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def plan(
        self, job: PickJob, observation: WorldObservation, destination: InventoryLocation
    ) -> ActionPlan:
        if self.settings.is_hkm:
            return self._hkm_plan(job, observation, destination)
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

    def _hkm_plan(
        self, job: PickJob, observation: WorldObservation, destination: InventoryLocation
    ) -> ActionPlan:
        observation = WorldObservation.model_validate(observation.model_dump())
        if observation.schema_version != "2.0" or observation.machine_telemetry is None:
            raise ValueError("HKM_OBSERVATION_REQUIRED")
        product = next(
            product
            for product in self.settings.products
            if product.product_id == job.line.product_id
        )
        specification = product_spec(product.sku)
        barriers = observed_obstacles(self.settings, observation, product.product_id)
        obj = next(obj for obj in observation.objects if obj.product_id == product.product_id)
        machine = observation.machine_telemetry
        selection = select_tool(specification, machine.tool_state, product_id=product.product_id)
        target = self.settings.target_pose(product.product_id, destination)
        trajectory = plan_trajectory(
            specification,
            tool_spec(selection.selected_tool_id),
            obj.pose,
            target,
            initial_tcp=machine.tcp_pose,
            tool_state=machine.tool_state,
            obstacles=barriers,
        )
        catalogue = load_catalogue()
        return ActionPlan(
            schema_version="2.0",
            **metadata(job, observation.observation_id, observation.timestamp),
            action_plan_id=stable_id(job.job_id, observation.observation_id),
            job_id=job.job_id,
            order_id=job.order_id,
            order_line_id=job.line.order_line_id,
            product_id=product.product_id,
            source_id=job.line.source_id,
            destination_id=job.line.destination_id,
            target_pose=target,
            scene_epoch=observation.scene_epoch,
            observation_id=observation.observation_id,
            cell_generation=observation.cell_generation,
            brain_version="deterministic-hkm-1",
            selected_tool_id=selection.selected_tool_id,
            grasp_pose=trajectory.grasp_pose,
            trajectory=trajectory,
            tool_selection=selection,
            robot_profile_version=catalogue.profile_version,
            product_catalog_version=catalogue.product_catalog_version,
            tool_spec_version=catalogue.tool_catalog_version,
            frame_tree_version=catalogue.frame_tree_version,
        )


def parse_structured_output(payload: str) -> ActionPlan:
    """Optional provider boundary only. It cannot execute code or send robot commands."""
    return ActionPlan.model_validate_json(payload)
