"""Camera-model verification from independent camera-local reference measurements.

The local simulator supplies a declared synthetic factory metrology fixture. Its
surveyed points are expressed in each optical frame and its measured image positions
are independent of the working-cell X/Y fit. This is not a hardware certificate,
an installation calibration, or a check of depth scale/registration/tool geometry.
"""

from typing import Literal, Self

import numpy as np
from pydantic import Field, model_validator

from robotops.calibration.contracts import Camera, Id, Record, Vec2, Vec3
from robotops.calibration.geometry import point_rms, project


class OpticalReference(Record):
    measurement_id: Id
    camera_id: Id
    profile_id: Id
    stream: Literal["rgb", "depth"]
    optical_frame: Literal["c", "d"]
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    crop_xy: tuple[int, int] = (0, 0)
    resize_xy: Vec2 = (1, 1)
    optical_points_m: tuple[Vec3, ...]
    measured_pixels_px: tuple[Vec2, ...]
    fixture_id: Literal["synthetic-camera-local-survey-1"] = "synthetic-camera-local-survey-1"
    provenance: Literal["SYNTHETIC_FACTORY_REFERENCE_FIXTURE"] = (
        "SYNTHETIC_FACTORY_REFERENCE_FIXTURE"
    )
    scope: str = "Synthetic camera-local metrology observations, not working-cell RGB-D captures or real hardware certification"

    @model_validator(mode="after")
    def correspondence(self) -> Self:
        if len(self.optical_points_m) != len(self.measured_pixels_px) or not self.optical_points_m:
            raise ValueError("OPTICAL_REFERENCE_CORRESPONDENCE_MISSING")
        if any(point[2] <= 0 for point in self.optical_points_m):
            raise ValueError("OPTICAL_REFERENCE_BEHIND_CAMERA")
        if self.optical_frame != ("c" if self.stream == "rgb" else "d"):
            raise ValueError("OPTICAL_REFERENCE_FRAME_MISMATCH")
        return self


class OpticsLimits(Record):
    limits_id: Literal["synthetic-optical-reference-budget-1"] = (
        "synthetic-optical-reference-budget-1"
    )
    max_rms_px: float | None = Field(default=0.5, gt=0)
    max_error_px: float | None = Field(default=1, gt=0)
    min_points_per_stream: int = Field(default=30, ge=12)
    min_image_fraction: float = Field(default=0.35, gt=0, lt=1)
    scope: Literal["SIMULATION_ONLY"] = "SIMULATION_ONLY"
    justification: str = "Synthetic reference readout noise is 0.08 px per coordinate. Separate 0.5 px RMS and 1 px maximum gates reserve subpixel model error; these are not SICS or production tolerances."


class OpticalStreamReport(Record):
    measurement_id: Id
    stream: Literal["rgb", "depth"]
    point_count: int
    rms_px: float
    maximum_px: float
    image_fraction: float
    predicted_pixels_px: tuple[Vec2, ...]
    residuals_px: tuple[Vec2, ...]
    failures: tuple[str, ...]


class CameraModelReport(Record):
    report_id: Id
    camera_id: Id
    camera_configuration_fingerprint: str
    measurement_fingerprints: tuple[str, ...]
    limits: OpticsLimits
    streams: tuple[OpticalStreamReport, ...]
    passed: bool
    failures: tuple[str, ...]
    limitations: tuple[str, ...] = (
        "Synthetic factory fixture only; no real camera was measured.",
        "Checks projection for the exact profile and model; does not determine camera-to-robot X.",
        "Does not verify depth scale/semantics, RGB-depth registration, TCP, timing or working-cell mechanics.",
    )


def verify_camera_model(
    camera: Camera, measurements: tuple[OpticalReference, ...], limits: OpticsLimits, report_id: str
) -> CameraModelReport:
    failures: list[str] = []
    reports = []
    if {item.stream for item in measurements} != {"rgb", "depth"} or len(measurements) != 2:
        failures.append("BOTH_OPTICAL_STREAM_REFERENCES_REQUIRED")
    if limits.max_rms_px is None or limits.max_error_px is None:
        failures.append("MISSING_OPTICS_LIMITS")
    for observation in measurements:
        stream = camera.rgb if observation.stream == "rgb" else camera.depth
        rejected = []
        if observation.camera_id != camera.camera_id or observation.profile_id != camera.profile_id:
            rejected.append("OPTICAL_REFERENCE_PROFILE_MISMATCH")
        if (observation.width, observation.height) != (stream.width, stream.height):
            rejected.append("OPTICAL_REFERENCE_SIZE_MISMATCH")
        if observation.crop_xy != stream.crop_xy or observation.resize_xy != stream.resize_xy:
            rejected.append("OPTICAL_REFERENCE_CROP_RESIZE_MISMATCH")
        expected = project(
            np.asarray(observation.optical_points_m),
            np.asarray(stream.k),
            np.asarray(stream.coefficients),
            stream.distortion_model,
        )
        measured = np.asarray(observation.measured_pixels_px)
        if (
            (measured < 0).any()
            or (measured[:, 0] >= stream.width).any()
            or (measured[:, 1] >= stream.height).any()
        ):
            rejected.append("OPTICAL_REFERENCE_OUTSIDE_IMAGE")
        errors = measured - expected
        rms = point_rms(errors)
        maximum = float(np.max(np.linalg.norm(errors, axis=1)))
        # Bounding coverage plus all four quadrants; repeated points cannot meet the count.
        fraction = float(np.prod(np.ptp(measured, axis=0)) / (stream.width * stream.height))
        center = measured - [stream.width / 2, stream.height / 2]
        quadrants = {(bool(x > 0), bool(y > 0)) for x, y in center}
        if (
            len(np.unique(measured, axis=0)) < limits.min_points_per_stream
            or fraction < limits.min_image_fraction
            or len(quadrants) != 4
        ):
            rejected.append("INSUFFICIENT_OPTICAL_REFERENCE_COVERAGE")
        if limits.max_rms_px is not None and rms > limits.max_rms_px:
            rejected.append("OPTICAL_MODEL_RMS_LIMIT")
        if limits.max_error_px is not None and maximum > limits.max_error_px:
            rejected.append("OPTICAL_MODEL_MAXIMUM_LIMIT")
        failures.extend(f"{observation.stream}:{reason}" for reason in rejected)
        reports.append(
            OpticalStreamReport(
                measurement_id=observation.measurement_id,
                stream=observation.stream,
                point_count=len(measured),
                rms_px=rms,
                maximum_px=maximum,
                image_fraction=fraction,
                predicted_pixels_px=tuple(map(tuple, expected.tolist())),
                residuals_px=tuple(map(tuple, errors.tolist())),
                failures=tuple(rejected),
            )
        )
    return CameraModelReport(
        report_id=report_id,
        camera_id=camera.camera_id,
        camera_configuration_fingerprint=camera.fingerprint(),
        measurement_fingerprints=tuple(item.fingerprint() for item in measurements),
        limits=limits,
        streams=tuple(reports),
        passed=not failures,
        failures=tuple(failures),
    )
