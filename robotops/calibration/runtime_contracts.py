"""Measured-cell extensions to version 3 application contracts.

These fields never serialize into historical v1/v2 observations or commands. The
profile is an ideal synthetic Cartesian gantry with an orientable gimbal, not HKM IK.
"""

from typing import Final, Literal, Self

import numpy as np
from pydantic import Field, SerializerFunctionWrapHandler, model_serializer, model_validator

from robotops.calibration.contracts import Capture, Id, PointMeasurement, Record, Tool, Transform
from robotops.calibration.tcp import GraspSpecification, TargetPose

PROFILE: Final = "synthetic_calibration_gantry_v1"


class CalibrationMachine(Record):
    profile: Literal["synthetic_calibration_gantry_v1"] = PROFILE
    flange: Transform
    tcp: Transform
    tool: Tool
    board_mounted: bool
    tool_verification_id: Id | None = None
    motion_phase: str = "IDLE"
    settled: bool = True
    command_mode: Literal["tcp", "flange"] = "flange"

    @model_validator(mode="after")
    def consistent_report(self) -> Self:
        if (self.flange.source, self.flange.destination) != ("f", "b"):
            raise ValueError("FLANGE_FRAME_DIRECTION")
        if (self.tcp.source, self.tcp.destination) != ("tcp", "b"):
            raise ValueError("TCP_FRAME_DIRECTION")
        expected = np.asarray(self.flange.matrix) @ np.asarray(self.tool.t_f_tcp.matrix)
        if not np.allclose(expected, self.tcp.matrix, atol=1e-8, rtol=0):
            raise ValueError("CONTROLLER_FLANGE_TCP_REPORT_CONFLICT")
        return self


class ArtifactBinding(Record):
    camera_id: Id
    artifact_id: Id
    artifact_fingerprint: str
    camera_configuration_fingerprint: str
    capture_id: Id


class ObservationFailure(Record):
    attempt_id: Id
    job_id: str
    command_id: str | None
    attempted_at_utc: str
    code: str
    detail: str
    saved_capture_ids: tuple[str, ...]
    scope: Literal["Failed observation attempt; no measured point or physical outcome inferred"] = (
        "Failed observation attempt; no measured point or physical outcome inferred"
    )


class MeasurementQuality(Record):
    quality_id: Id
    camera_id: Id
    capture_id: Id
    artifact_id: Id
    point_fingerprint: str
    surface_mask_sha256: str
    selected_pixel_count: int = Field(gt=0)
    agreement_id: Id
    correspondence_error_px: float = Field(ge=0)
    correspondence_limit_px: float = Field(gt=0)
    overlap_difference_mm: float = Field(ge=0)
    overlap_limit_mm: float = Field(gt=0)
    validation_reference_max_mm: float = Field(ge=0)
    validation_limit_mm: float = Field(gt=0)
    passed: bool
    failures: tuple[str, ...]
    confidence_estimate: Literal["NOT_ESTIMATED"] = "NOT_ESTIMATED"
    point_uncertainty_estimate: Literal["NOT_ESTIMATED"] = "NOT_ESTIMATED"
    scope: str = (
        "Measured gate results for this synthetic color-coded object, not a statistical probability "
        "or point uncertainty bound. Holdout error and acceptance limits are not fresh-point accuracy guarantees."
    )

    @model_validator(mode="after")
    def decision(self) -> Self:
        if self.passed == bool(self.failures):
            raise ValueError("MEASUREMENT_QUALITY_STATUS_INCONSISTENT")
        return self


class CalibratedObject(Record):
    binding: ArtifactBinding
    surface_point: PointMeasurement
    perception_method: Literal["DECLARED_SYNTHETIC_COLOR_PATCH"] = "DECLARED_SYNTHETIC_COLOR_PATCH"
    geometry_assumption: str = (
        "Known rigid cube, visible top patch; orientation supplied separately by the fixture"
    )
    measurement_quality: MeasurementQuality | None = None

    @model_serializer(mode="wrap")
    def retain_prior_object(  # type: ignore[no-untyped-def]
        self, handler: SerializerFunctionWrapHandler
    ):
        result: dict[str, object] = handler(self)
        if self.measurement_quality is None:
            result.pop("measurement_quality", None)
        return result

    @model_validator(mode="after")
    def bound_point(self) -> Self:
        if (
            self.binding.camera_id != self.surface_point.camera_id
            or self.binding.camera_configuration_fingerprint
            != self.surface_point.configuration_fingerprint
        ):
            raise ValueError("POINT_CAMERA_BINDING_MISMATCH")
        if self.measurement_quality is not None and (
            self.measurement_quality.capture_id != self.binding.capture_id
            or self.measurement_quality.artifact_id != self.binding.artifact_id
            or self.measurement_quality.camera_id != self.binding.camera_id
            or self.measurement_quality.point_fingerprint != self.surface_point.fingerprint()
        ):
            raise ValueError("MEASUREMENT_QUALITY_POINT_BINDING_MISMATCH")
        return self


class CalibratedObservation(Record):
    profile: Literal["synthetic_calibration_gantry_v1"] = PROFILE
    machine: CalibrationMachine
    bindings: tuple[ArtifactBinding, ...]
    limitations: tuple[str, ...] = (
        "Synthetic RGB-D sensor arrays; known color-coded rigid objects only.",
        "Object orientation and grasp geometry come from the declared fixture, not depth alone.",
    )


class MachineWaypoint(Record):
    phase: Literal["PRE_GRASP", "GRASP", "LIFT", "TRANSFER", "PLACE", "RETRACT"]
    sim_time_s: float = Field(ge=0)
    flange: Transform
    tcp: Transform
    attached: bool


class CalibratedPlan(Record):
    profile: Literal["synthetic_calibration_gantry_v1"] = PROFILE
    observed_object: CalibratedObject
    grasp: GraspSpecification
    target: TargetPose
    tool_verification_id: Id
    waypoints: tuple[MachineWaypoint, ...]
    contact_radius_m: float = Field(default=0.01, gt=0, le=0.01)
    supporting_bindings: tuple[ArtifactBinding, ...] = ()

    @model_serializer(mode="wrap")
    def retain_prior_command(  # type: ignore[no-untyped-def]
        self, handler: SerializerFunctionWrapHandler
    ):
        result: dict[str, object] = handler(self)
        if not self.supporting_bindings:
            result.pop("supporting_bindings", None)
        return result

    @model_validator(mode="after")
    def motion_contract(self) -> Self:
        ids = [binding.camera_id for binding in self.supporting_bindings]
        if len(set(ids)) != len(ids) or self.observed_object.binding.camera_id in ids:
            raise ValueError("DUPLICATE_CAMERA_BINDING")
        if tuple(point.phase for point in self.waypoints) != (
            "PRE_GRASP",
            "GRASP",
            "LIFT",
            "TRANSFER",
            "PLACE",
            "RETRACT",
        ):
            raise ValueError("CALIBRATED_MOTION_PHASES_REQUIRED")
        if any(
            a.sim_time_s >= b.sim_time_s
            for a, b in zip(self.waypoints, self.waypoints[1:], strict=False)
        ):
            raise ValueError("CALIBRATED_MOTION_TIME_ORDER")
        if (
            self.waypoints[1].tcp != self.target.tcp_target
            or self.waypoints[1].flange != self.target.flange_target
        ):
            raise ValueError("GRASP_TARGET_MOTION_MISMATCH")
        return self


class CalibratedReceipt(Record):
    profile: Literal["synthetic_calibration_gantry_v1"] = PROFILE
    binding: ArtifactBinding
    tool_fingerprint: str
    executed_waypoint_count: int = Field(ge=0)
    final_machine: CalibrationMachine
    motion_without_transfer: Literal["GRASP_NOT_ESTABLISHED"] | None = None

    @model_serializer(mode="wrap")
    def retain_prior_receipt(  # type: ignore[no-untyped-def]
        self, handler: SerializerFunctionWrapHandler
    ):
        result: dict[str, object] = handler(self)
        if self.motion_without_transfer is None:
            result.pop("motion_without_transfer", None)
        return result


class SensorSnapshot(Record):
    scene_epoch: str
    step: int = Field(ge=0)
    cell_generation: int = Field(ge=0)
    machine: CalibrationMachine
    captures: tuple[Capture, ...]
