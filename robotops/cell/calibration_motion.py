"""Ideal gantry controller samples and contact-preserving synthetic object motion.

These samples are computed and committed by the controller, then read by presentation.
This is a Cartesian/gimbal simulation, not robot IK or certified collision avoidance.
"""

from collections.abc import Iterator

import numpy as np
from scipy.spatial.transform import Rotation, Slerp

from robotops.calibration.configuration import framed
from robotops.calibration.contracts import Record
from robotops.calibration.errors import CalibrationError
from robotops.calibration.geometry import Array, from_xyzw, inverse
from robotops.calibration.runtime_contracts import CalibrationMachine
from robotops.domain.models import Pose, RobotCommand, WorldState


class ControllerFrame(Record):
    command_id: str
    index: int
    sim_time_s: float
    machine: CalibrationMachine
    object_pose: Pose
    attached: bool


def controller_frames(
    world: WorldState, command: RobotCommand, physical_tool: Array, *, grip_established: bool = True
) -> Iterator[ControllerFrame]:
    machine, intent = world.calibration_machine, command.calibrated_plan
    if machine is None or intent is None:
        raise CalibrationError("MEASURED_MOTION_CONTEXT_REQUIRED")
    obj = next(item for item in world.objects if item.product.product_id == command.product_id)
    grasp = np.array(intent.waypoints[1].flange.matrix) @ physical_tool
    object_in_grip = inverse(grasp) @ from_xyzw(obj.pose.position, obj.pose.quaternion_xyzw)
    placed = np.array(intent.waypoints[4].flange.matrix) @ physical_tool @ object_in_grip
    times = np.array([point.sim_time_s for point in intent.waypoints])
    matrices = [np.array(point.tcp.matrix) for point in intent.waypoints]
    rotations = Slerp(
        times, Rotation.from_matrix(np.array([matrix[:3, :3] for matrix in matrices]))
    )
    for index in range(round(float(times[-1]) * 24) + 1):
        time = index / 24
        low = min(int(np.searchsorted(times, time, side="right")) - 1, len(times) - 2)
        low = max(0, low)
        fraction = (time - times[low]) / (times[low + 1] - times[low])
        tcp = np.eye(4)
        tcp[:3, :3] = rotations([time]).as_matrix()[0]
        tcp[:3, 3] = matrices[low][:3, 3] * (1 - fraction) + matrices[low + 1][:3, 3] * fraction
        flange = tcp @ inverse(machine.tool.t_f_tcp.matrix)
        phase_index = max(
            0, min(int(np.searchsorted(times, time, side="right")) - 1, len(times) - 1)
        )
        attached = grip_established and float(times[1]) <= time < float(times[4])
        object_matrix = (
            flange @ physical_tool @ object_in_grip
            if attached
            else placed
            if grip_established and time >= float(times[4])
            else from_xyzw(obj.pose.position, obj.pose.quaternion_xyzw)
        )
        pose = obj.pose.model_copy(
            update={
                "position": tuple(object_matrix[:3, 3].tolist()),
                "quaternion_xyzw": tuple(
                    Rotation.from_matrix(object_matrix[:3, :3]).as_quat().tolist()
                ),
            }
        )
        reported = CalibrationMachine.model_validate(
            {
                **machine.model_dump(),
                "flange": framed(flange, "f", "b"),
                "tcp": framed(tcp, "tcp", "b"),
                "motion_phase": intent.waypoints[phase_index].phase,
                "settled": bool(np.any(np.isclose(times, time, atol=1e-8))),
            }
        )
        yield ControllerFrame(
            command_id=command.command_id,
            index=index,
            sim_time_s=time,
            machine=reported,
            object_pose=pose,
            attached=attached,
        )
