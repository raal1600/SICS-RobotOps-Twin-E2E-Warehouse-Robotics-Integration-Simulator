"""Observation-only checks; no simulator/runtime import is permitted here."""

from datetime import datetime
from math import dist

from robotops.config import Settings
from robotops.domain.models import WorldObservation


def quality(
    observation: WorldObservation, product_id: str, settings: Settings, now: datetime
) -> str | None:
    age = (now - observation.captured_at).total_seconds()
    if age < 0 or age > settings.freshness_seconds:
        return "STALE_OR_FUTURE_OBSERVATION"
    if observation.calibration_version != settings.calibration_version:
        return "CALIBRATION_MISMATCH"
    objects = [obj for obj in observation.objects if obj.product_id == product_id]
    if not objects:
        return "MISSING_OBSERVATION"
    if len(objects) != 1:
        return "CONTRADICTORY_OBSERVATION"
    obj = objects[0]
    if settings.is_measured:
        if (
            observation.schema_version != "3.0"
            or observation.calibrated_observation is None
            or obj.calibrated_object is None
        ):
            return "IMAGE_DERIVED_CALIBRATED_OBSERVATION_REQUIRED"
        measured = obj.calibrated_object.surface_point.point
        expected_center = (measured[0], measured[1], measured[2] - 0.04)
        if dist(obj.pose.position, expected_center) > 1e-9:
            return "OBSERVATION_POINT_GEOMETRY_MISMATCH"
        checks = obj.calibrated_object.measurement_quality
        if checks is None:
            return "MEASUREMENT_QUALITY_EVIDENCE_REQUIRED"
        if (
            checks.point_fingerprint != obj.calibrated_object.surface_point.fingerprint()
            or checks.capture_id != obj.calibrated_object.binding.capture_id
            or checks.artifact_id != obj.calibrated_object.binding.artifact_id
        ):
            return "MEASUREMENT_QUALITY_POINT_BINDING_MISMATCH"
        if not checks.passed:
            return "MEASUREMENT_QUALITY_FAILED"
        if obj.confidence is not None or obj.uncertainty_m is not None:
            return "RULE_GATES_ARE_NOT_STATISTICAL_ESTIMATES"
    else:
        if obj.confidence is None or obj.uncertainty_m is None:
            return "MISSING_OBSERVATION_QUALITY"
        if obj.confidence < settings.min_confidence:
            return "LOW_CONFIDENCE"
        if obj.uncertainty_m > settings.max_uncertainty_m:
            return "POSE_UNCERTAINTY"
    if (
        obj.pose.frame_id != settings.frame_id
        or obj.pose.calibration_version != settings.calibration_version
    ):
        return "SPATIAL_METADATA_MISMATCH"
    return None
