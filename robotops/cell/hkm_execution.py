"""Private-world defensive execution checks. Never imported by the verifier.

The workflow's planning check is repeated at the machine boundary against current
controller state. The only product effect remains one journalled transfer.
"""

from math import dist
from typing import Any

from robotops.domain.models import RobotCommand, WorldState
from robotops.robotics.catalogue import fixture_target_pose, load_catalogue, product_spec, tool_spec
from robotops.robotics.catalogue_data import SYNTHETIC_GRASP_CONTACT_TOLERANCE_M
from robotops.robotics.models import RobotState, ToolState
from robotops.robotics.selector import evaluate_candidate
from robotops.robotics.trajectory import (
    default_obstacles,
    plan_trajectory,
    product_obstacles,
    translated,
)


def validate_execution(world: WorldState, command: RobotCommand) -> None:
    if world.schema_version != "2.0" or command.schema_version != "2.0":
        raise ValueError("RUNTIME_PROFILE_VERSION_MISMATCH")
    if (
        world.tool_state is None
        or world.robot_state is None
        or command.trajectory is None
        or command.required_tool_id is None
    ):
        raise ValueError("HKM_EXECUTION_METADATA_REQUIRED")
    catalogue = load_catalogue()
    product = next(obj for obj in world.objects if obj.product.product_id == command.product_id)
    specification = product_spec(product.product.sku)
    tool = tool_spec(command.required_tool_id)
    if (
        command.destination_id != catalogue.layout.destination.location_id
        or command.target_pose != fixture_target_pose(specification.sku)
    ):
        raise ValueError("TARGET_POSE_MISMATCH")
    if command.source_id != catalogue.layout.sources[specification.sku].location_id:
        raise ValueError("SOURCE_PRECONDITION_FAILED")
    candidate = evaluate_candidate(specification, tool, world.tool_state, specification.mass_max_kg)
    if not candidate.eligible:
        raise ValueError("TOOL_EXECUTION_REJECTED:" + ",".join(candidate.reasons))
    observed_source = translated(
        command.trajectory.grasp_pose, command.trajectory.product_attachment_offset_m
    )
    if (
        observed_source.frame_id != product.pose.frame_id
        or observed_source.calibration_version != product.pose.calibration_version
        or observed_source.quaternion_xyzw != product.pose.quaternion_xyzw
        or dist(observed_source.position, product.pose.position)
        > SYNTHETIC_GRASP_CONTACT_TOLERANCE_M
        or product.attached
    ):
        raise ValueError("GRASP_SOURCE_PRECONDITION_FAILED")
    obstacles = default_obstacles() + product_obstacles(
        [
            (obj.product.product_id, product_spec(obj.product.sku), obj.pose)
            for obj in world.objects
        ],
        exclude_product_id=command.product_id,
    )
    expected = plan_trajectory(
        specification,
        tool,
        observed_source,
        command.target_pose,
        initial_tcp=world.robot_state.tcp_pose,
        tool_state=world.tool_state,
        obstacles=obstacles,
    )
    if expected != command.trajectory:
        raise ValueError("RUNTIME_TRAJECTORY_MISMATCH")


def final_machine(world: WorldState, command: RobotCommand) -> tuple[RobotState, ToolState]:
    if world.tool_state is None or command.trajectory is None or command.required_tool_id is None:
        raise ValueError("HKM_EXECUTION_METADATA_REQUIRED")
    available = set(world.tool_state.rack_tool_ids)
    if world.tool_state.active_tool_id:
        available.add(world.tool_state.active_tool_id)
    available.remove(command.required_tool_id)
    tools = ToolState(
        active_tool_id=command.required_tool_id,
        rack_tool_ids=tuple(
            tool.tool_id for tool in load_catalogue().tools if tool.tool_id in available
        ),
    )
    robot = RobotState(
        tcp_pose=command.trajectory.waypoints[-1].pose,
        active_tool_id=command.required_tool_id,
        motion_phase="HOME",
    )
    return robot, tools


def receipt_metadata(
    world: WorldState, command: RobotCommand, *, effect: bool = False
) -> dict[str, Any]:
    if command.schema_version == "1.0":
        return {}
    if command.trajectory is None:
        raise ValueError("HKM_TRAJECTORY_REQUIRED")
    active = world.tool_state.active_tool_id if world.tool_state else None
    return dict(
        schema_version="2.0",
        active_tool_id=command.required_tool_id if effect else active,
        tool_change_performed=effect and active != command.required_tool_id,
        trajectory_id=command.trajectory.trajectory_id,
        runtime_profile_version="hkm_inspired_v1",
    )
