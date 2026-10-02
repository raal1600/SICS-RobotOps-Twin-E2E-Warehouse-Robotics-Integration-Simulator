"""Observation-only checks; no simulator/runtime import is permitted here."""

from datetime import datetime

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
