"""Measured rule gates, explicitly distinct from a statistical confidence model."""

import math

from robotops.calibration.agreement import CameraAgreement
from robotops.calibration.contracts import (
    CalibrationArtifact,
    Limits,
    PointMeasurement,
    SurfaceDetection,
)
from robotops.calibration.errors import CalibrationError
from robotops.calibration.runtime_contracts import MeasurementQuality


def assess_measurement(
    point: PointMeasurement,
    detection: SurfaceDetection,
    agreement: CameraAgreement,
    artifact: CalibrationArtifact,
    limits: Limits,
) -> MeasurementQuality:
    """Summarize actual gates; neither reference accuracy nor a color rule is a probability."""
    if (
        point.camera_id != detection.camera_id
        or point.camera_id != agreement.primary_camera
        or artifact.artifact_id != agreement.primary_artifact_id
        or artifact.candidate.camera.fingerprint() != point.configuration_fingerprint
        or artifact.candidate.x.fingerprint() != point.transform_fingerprint
        or artifact.candidate.limits_fingerprint != limits.fingerprint()
        or detection.selected_rgb_pixel != point.selected_rgb_pixel
        or detection.method != "red_cube_top"
    ):
        raise CalibrationError("MEASUREMENT_QUALITY_INPUT_BINDING_MISMATCH")
    correspondence = point.calculation.outputs.get("correspondence_error_px")
    if (
        not isinstance(correspondence, int | float)
        or isinstance(correspondence, bool)
        or not math.isfinite(correspondence)
    ):
        raise CalibrationError("MEASUREMENT_QUALITY_CORRESPONDENCE_MISSING")
    maximum = artifact.validation.reference_max_mm
    if maximum is None or limits.max_reference_error_mm is None:
        raise CalibrationError("MEASUREMENT_QUALITY_REFERENCE_LIMIT_REQUIRED")
    failures = []
    if correspondence > limits.max_correspondence_error_px:
        failures.append("RGB_DEPTH_CORRESPONDENCE_LIMIT")
    if not agreement.passed or agreement.difference_mm > agreement.limit_mm:
        failures.append("CAMERA_AGREEMENT_FAILED")
    if not artifact.validation.passed or maximum > limits.max_reference_error_mm:
        failures.append("INDEPENDENT_REFERENCE_VALIDATION_FAILED")
    return MeasurementQuality(
        quality_id=detection.capture_id,
        camera_id=point.camera_id,
        capture_id=detection.capture_id,
        artifact_id=artifact.artifact_id,
        point_fingerprint=point.fingerprint(),
        surface_mask_sha256=detection.mask.sha256,
        selected_pixel_count=detection.selected_pixel_count,
        agreement_id=agreement.agreement_id,
        correspondence_error_px=float(correspondence),
        correspondence_limit_px=limits.max_correspondence_error_px,
        overlap_difference_mm=agreement.difference_mm,
        overlap_limit_mm=agreement.limit_mm,
        validation_reference_max_mm=maximum,
        validation_limit_mm=limits.max_reference_error_mm,
        passed=not failures,
        failures=tuple(failures),
    )
