"""Physical-world checks for the explicitly synthetic gantry/gimbal cell.

No calibrated perception is derived here. World coordinates are used only for
simulation effects/contact checks and controller telemetry, never for estimation.
"""

from typing import Literal

import numpy as np

from robotops.calibration.configuration import framed
from robotops.calibration.contracts import Tool
from robotops.calibration.errors import CalibrationError
from robotops.calibration.geometry import Array, from_xyzw, inverse
from robotops.calibration.runtime_contracts import CalibratedReceipt, CalibrationMachine
from robotops.domain.models import RobotCommand, WorldState

CUBE_SIDE_M = 0.08
WORKSPACE_MIN = np.array([-0.45, -0.45, 0.15])
WORKSPACE_MAX = np.array([0.45, 0.45, 1.15])


def configured_tool() -> Tool:
    transform = np.eye(4)
    transform[2, 3] = 0.18
    return Tool(
        tool_id="synthetic-vacuum-1",
        configuration_revision="tool-1",
        t_f_tcp=framed(transform, "tcp", "f"),
    )


def initial_machine(command_mode: Literal["tcp", "flange"] = "flange") -> CalibrationMachine:
    tool = configured_tool()
    flange = np.eye(4)
    flange[:3, 3] = [0, 0, 0.6]
    return CalibrationMachine(
        flange=framed(flange, "f", "b"),
        tcp=framed(flange @ np.asarray(tool.t_f_tcp.matrix), "tcp", "b"),
        tool=tool,
        board_mounted=True,
        command_mode=command_mode,
    )


def validate_execution(
    world: WorldState, command: RobotCommand, physical_tool: Array | None = None
) -> None:
    machine, intent = world.calibration_machine, command.calibrated_plan
    if (
        world.schema_version != "3.0"
        or command.schema_version != "3.0"
        or machine is None
        or intent is None
    ):
        raise CalibrationError("MEASURED_CELL_CONTRACT_REQUIRED")
    if machine.board_mounted:
        raise CalibrationError("REMOVE_CALIBRATION_BOARD_BEFORE_PICK")
    if not machine.settled:
        raise CalibrationError("ROBOT_NOT_SETTLED")
    if (
        intent.target.tool_fingerprint != machine.tool.fingerprint()
        or intent.tool_verification_id != machine.tool_verification_id
    ):
        raise CalibrationError("CURRENT_TOOL_VERIFICATION_REQUIRED")
    product = next(obj for obj in world.objects if obj.product.product_id == command.product_id)
    # The contact is checked against the physical surface, independent of the estimator.
    physical_pose = from_xyzw(product.pose.position, product.pose.quaternion_xyzw)
    physical_top = physical_pose @ np.array([0, 0, CUBE_SIDE_M / 2, 1])
    if intent.target.mode != machine.command_mode:
        raise CalibrationError("CONTROLLER_COMMAND_MODE_CHANGED")
    commanded = np.asarray(intent.target.command_target.matrix)
    grasp_flange = (
        commanded
        if machine.command_mode == "flange"
        else commanded @ inverse(machine.tool.t_f_tcp.matrix)
    )
    if not np.allclose(grasp_flange, intent.target.flange_target.matrix, atol=1e-8, rtol=0):
        raise CalibrationError("DOUBLE_TOOL_OFFSET_OR_COMMAND_TARGET_MISMATCH")
    actual_tcp = grasp_flange @ (
        np.asarray(machine.tool.t_f_tcp.matrix) if physical_tool is None else physical_tool
    )
    if np.linalg.norm(actual_tcp[:3, 3] - physical_top[:3]) > intent.contact_radius_m:
        raise CalibrationError(
            "SYNTHETIC_CONTACT_MISSED", "Computed TCP did not contact the physical top patch"
        )
    if product.attached:
        raise CalibrationError("PRODUCT_ALREADY_ATTACHED")
    # Vacuum normal is declared separately; a measured point alone cannot pass this check.
    if float(actual_tcp[:3, 2] @ physical_pose[:3, 2]) > -0.99:
        raise CalibrationError("GRASP_ORIENTATION_CONTACT_MISMATCH")
    for waypoint in intent.waypoints:
        flange, tcp = np.asarray(waypoint.flange.matrix), np.asarray(waypoint.tcp.matrix)
        if not np.allclose(
            flange @ np.asarray(machine.tool.t_f_tcp.matrix), tcp, atol=1e-8, rtol=0
        ):
            raise CalibrationError("TRAJECTORY_TOOL_OFFSET_MISMATCH")
        for position in (flange[:3, 3], tcp[:3, 3]):
            if (position < WORKSPACE_MIN).any() or (position > WORKSPACE_MAX).any():
                raise CalibrationError("MEASURED_GANTRY_WORKSPACE_BOUNDS")
        # Fixed supporting bench ends at z=0.31 m. A 20 mm end-effector envelope
        # must remain above it; cube contact itself is handled separately above.
        if min(flange[2, 3], tcp[2, 3]) - 0.02 < 0.31:
            raise CalibrationError("SYNTHETIC_BENCH_COLLISION")
    destination_top = np.asarray(command.target_pose.position) + [0, 0, CUBE_SIDE_M / 2]
    if not np.allclose(
        np.asarray(intent.waypoints[4].tcp.matrix)[:3, 3], destination_top, atol=1e-8
    ):
        raise CalibrationError("PLACEMENT_TARGET_MISMATCH")


def final_machine(world: WorldState, command: RobotCommand) -> CalibrationMachine:
    if world.calibration_machine is None or command.calibrated_plan is None:
        raise CalibrationError("MEASURED_CELL_CONTRACT_REQUIRED")
    last = command.calibrated_plan.waypoints[-1]
    return CalibrationMachine.model_validate(
        {
            **world.calibration_machine.model_dump(),
            "flange": last.flange,
            "tcp": last.tcp,
            "motion_phase": last.phase,
            "settled": True,
        }
    )


def receipt_metadata(
    world: WorldState, command: RobotCommand, *, effect: bool, motion_without_transfer: bool = False
) -> dict[str, object]:
    if world.calibration_machine is None or command.calibrated_plan is None:
        raise CalibrationError("MEASURED_CELL_CONTRACT_REQUIRED")
    if effect and motion_without_transfer:
        raise CalibrationError("CONTRADICTORY_MOTION_OUTCOME")
    return {
        "schema_version": "3.0",
        "calibrated_receipt": CalibratedReceipt(
            binding=command.calibrated_plan.observed_object.binding,
            tool_fingerprint=world.calibration_machine.tool.fingerprint(),
            executed_waypoint_count=len(command.calibrated_plan.waypoints)
            if effect or motion_without_transfer
            else 0,
            final_machine=final_machine(world, command)
            if effect or motion_without_transfer
            else world.calibration_machine,
            motion_without_transfer="GRASP_NOT_ESTABLISHED" if motion_without_transfer else None,
        ),
    }
