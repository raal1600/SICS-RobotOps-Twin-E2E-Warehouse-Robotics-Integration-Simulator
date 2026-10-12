"""Independent synthetic TCP metrology and explicit point-to-pose construction."""

from collections.abc import Sequence
from typing import Literal, Self, cast

import numpy as np
from pydantic import Field, model_validator

from robotops.calibration.configuration import framed
from robotops.calibration.contracts import (
    Calculation,
    Id,
    PointMeasurement,
    Record,
    Tool,
    Transform,
    Vec3,
)
from robotops.calibration.errors import CalibrationError
from robotops.calibration.geometry import inverse, points, residual, rigid, transform


class ToolProbe(Record):
    tcp_reference_point_m: Vec3
    measured_flange_point_m: Vec3


class ToolMeasurements(Record):
    """Independent fixture observations, retained before any tool can be enabled."""

    measurement_id: Id
    tool: Tool
    pivot_flange_poses: tuple[Transform, ...]
    probes: tuple[ToolProbe, ...]
    machine_fingerprint: str
    scene_epoch: str
    cell_generation: int = Field(ge=0)
    captured_at_utc: str
    max_translation_mm: float = Field(default=1, gt=0)
    max_orientation_deg: float = Field(default=0.25, gt=0)
    scope: str = "SIMULATION_ONLY: independent synthetic pivot fixture and indexed axis probes; not executed robot calibration motion"


class ToolVerification(Record):
    verification_id: str
    tool_fingerprint: str
    pivot_count: int
    pivot_rank: int
    pivot_tip_f_m: Vec3
    pivot_center_b_m: Vec3
    pivot_rms_mm: float
    probe_count: int
    translation_error_mm: float
    orientation_error_deg: float
    passed: bool
    failures: tuple[str, ...]
    scope: Literal["SIMULATION_ONLY"] = "SIMULATION_ONLY"


class GraspSpecification(Record):
    # Orientation is expressed explicitly as a TCP-to-base rotation, not inferred from a point.
    orientation_b_tcp: tuple[Vec3, Vec3, Vec3]
    contact_offset_b_m: Vec3
    approach_direction_b: Vec3
    approach_distance_m: float = Field(gt=0, le=0.5)
    orientation_source: str = Field(min_length=1)
    contact_source: str = Field(min_length=1)
    approach_source: str = Field(min_length=1)


class TargetPose(Record):
    mode: Literal["tcp", "flange"]
    configured_tool_id: str
    tool_fingerprint: str
    tcp_target: Transform
    flange_target: Transform
    command_target: Transform
    approach_tcp: Transform
    calculation: Calculation

    @model_validator(mode="after")
    def controller_mode(self) -> Self:
        if (self.tcp_target.source, self.tcp_target.destination) != ("tcp", "b"):
            raise ValueError("TCP_TARGET_FRAME_DIRECTION")
        if (self.flange_target.source, self.flange_target.destination) != ("f", "b"):
            raise ValueError("FLANGE_TARGET_FRAME_DIRECTION")
        if (self.approach_tcp.source, self.approach_tcp.destination) != ("tcp", "b"):
            raise ValueError("APPROACH_FRAME_DIRECTION")
        expected = self.tcp_target if self.mode == "tcp" else self.flange_target
        if self.command_target != expected:
            raise ValueError("CONTROLLER_TARGET_MODE_MISMATCH")
        return self


def verify_tool(
    tool: Tool,
    pivot_flange_poses: Sequence[Transform],
    probes: Sequence[ToolProbe],
    verification_id: str,
    *,
    max_translation_mm: float = 1,
    max_orientation_deg: float = 0.25,
) -> ToolVerification:
    """Pivot estimates translation only; indexed 3D metrology probes check full orientation.

    Probe measurements must come from independent synthetic metrology, not from the
    configured tool transform under test. These are simulation limits, not site approval.
    """
    if len(pivot_flange_poses) < 6 or len(probes) < 4:
        raise CalibrationError("INSUFFICIENT_TCP_MEASUREMENTS")
    if max_translation_mm <= 0 or max_orientation_deg <= 0:
        raise CalibrationError("TCP_LIMITS_REQUIRED")
    if any((p.source, p.destination) != ("f", "b") for p in pivot_flange_poses):
        raise CalibrationError("FLANGE_FRAME_DIRECTION")
    matrices = [np.asarray(p.matrix) for p in pivot_flange_poses]
    system = np.vstack([np.column_stack((m[:3, :3], -np.eye(3))) for m in matrices])
    response = -np.concatenate([m[:3, 3] for m in matrices])
    fitted, _, rank, _ = np.linalg.lstsq(system, response, rcond=None)
    if rank != 6:
        raise CalibrationError("TCP_PIVOT_UNOBSERVABLE")
    pivot_errors = (system @ fitted - response).reshape(-1, 3)
    rms_mm = float(np.sqrt(np.sum(pivot_errors**2) / len(matrices)) * 1000)
    reference = np.asarray([p.tcp_reference_point_m for p in probes])
    measured = np.asarray([p.measured_flange_point_m for p in probes])
    a, b = reference - reference.mean(axis=0), measured - measured.mean(axis=0)
    if np.linalg.matrix_rank(a) < 3 or np.linalg.matrix_rank(b) < 3:
        raise CalibrationError("TCP_ORIENTATION_PROBES_DEGENERATE")
    u, _, vt = np.linalg.svd(a.T @ b)
    correction = np.diag([1, 1, np.linalg.det(vt.T @ u.T)])
    rotation = vt.T @ correction @ u.T
    metrology = transform(rotation, measured.mean(axis=0) - rotation @ reference.mean(axis=0))
    configured = np.asarray(tool.t_f_tcp.matrix)
    translation, angle = residual(configured, metrology)
    tip_difference = float(np.linalg.norm(fitted[:3] - configured[:3, 3]))
    probe_residual = float(np.max(np.linalg.norm(points(metrology, reference) - measured, axis=1)))
    translation_mm = max(translation, tip_difference, probe_residual) * 1000
    angle_deg = float(np.rad2deg(angle))
    failures = []
    if translation_mm > max_translation_mm or rms_mm > max_translation_mm:
        failures.append("TCP_TRANSLATION_CHECK_FAILED")
    if angle_deg > max_orientation_deg:
        failures.append("TOOL_ORIENTATION_CHECK_FAILED")
    return ToolVerification(
        verification_id=verification_id,
        tool_fingerprint=tool.fingerprint(),
        pivot_count=len(matrices),
        pivot_rank=int(rank),
        pivot_tip_f_m=cast(Vec3, tuple(fitted[:3].tolist())),
        pivot_center_b_m=cast(Vec3, tuple(fitted[3:].tolist())),
        pivot_rms_mm=rms_mm,
        probe_count=len(probes),
        translation_error_mm=translation_mm,
        orientation_error_deg=angle_deg,
        passed=not failures,
        failures=tuple(failures),
    )


def verify_measurements(measurements: ToolMeasurements) -> ToolVerification:
    return verify_tool(
        measurements.tool,
        measurements.pivot_flange_poses,
        measurements.probes,
        measurements.measurement_id,
        max_translation_mm=measurements.max_translation_mm,
        max_orientation_deg=measurements.max_orientation_deg,
    )


def construct_target(
    point: PointMeasurement,
    grasp: GraspSpecification,
    tool: Tool,
    verification: ToolVerification,
    mode: Literal["tcp", "flange"],
) -> TargetPose:
    if not verification.passed or verification.tool_fingerprint != tool.fingerprint():
        raise CalibrationError("CURRENT_TOOL_VERIFICATION_REQUIRED")
    if mode not in ("tcp", "flange"):
        raise CalibrationError("UNSUPPORTED_CONTROLLER_TARGET_MODE")
    direction = np.asarray(grasp.approach_direction_b)
    if not np.isclose(np.linalg.norm(direction), 1, atol=1e-7):
        raise CalibrationError("APPROACH_DIRECTION_NOT_NORMALIZED")
    orientation = np.asarray(grasp.orientation_b_tcp)
    tcp = transform(orientation, np.asarray(point.point) + np.asarray(grasp.contact_offset_b_m))
    flange = rigid(tcp @ inverse(tool.t_f_tcp.matrix))
    approach = tcp.copy()
    approach[:3, 3] -= direction * grasp.approach_distance_m
    tcp_record, flange_record = framed(tcp, "tcp", "b"), framed(flange, "f", "b")
    selected = tcp_record if mode == "tcp" else flange_record
    return TargetPose(
        mode=mode,
        configured_tool_id=tool.tool_id,
        tool_fingerprint=tool.fingerprint(),
        tcp_target=tcp_record,
        flange_target=flange_record,
        command_target=selected,
        approach_tcp=framed(approach, "tcp", "b"),
        calculation=Calculation(
            function="robotops.calibration.tcp.construct_target",
            formula="T_b_f_target=T_b_tcp_target*inv(T_f_tcp); TCP API receives T_b_tcp_target unchanged",
            inputs={
                "point": point.model_dump(mode="json"),
                "grasp": grasp.model_dump(mode="json"),
                "t_f_tcp": tool.t_f_tcp.model_dump(mode="json"),
                "mode": mode,
                "tool_verification_id": verification.verification_id,
            },
            outputs={
                "tcp_target": tcp_record.model_dump(mode="json"),
                "flange_target": flange_record.model_dump(mode="json"),
                "command_target": selected.model_dump(mode="json"),
            },
            decision="TARGET_CONSTRUCTED; reachability, collision and execution authorization still required",
        ),
    )
