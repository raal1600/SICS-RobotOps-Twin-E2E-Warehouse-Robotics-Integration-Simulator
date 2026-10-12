"""Compare independent camera estimates without fusing conflicting coordinates."""

from math import dist

import numpy as np

from robotops.calibration.contracts import CalibrationArtifact, Limits, PointMeasurement, Record
from robotops.calibration.errors import CalibrationError
from robotops.calibration.geometry import residual


class CameraAgreement(Record):
    agreement_id: str
    primary_camera: str
    secondary_camera: str
    primary_artifact_id: str
    secondary_artifact_id: str
    primary_point_m: tuple[float, float, float]
    secondary_point_m: tuple[float, float, float]
    difference_mm: float
    limit_mm: float
    shared_mount_identity: str | None
    mounting_translation_mm: float | None
    mounting_rotation_deg: float | None
    passed: bool
    failures: tuple[str, ...]
    decision: str = (
        "Use the primary measurement only if agreement passes; do not average conflicting cameras"
    )


def compare_cameras(
    identity: str,
    primary: PointMeasurement,
    secondary: PointMeasurement,
    first: CalibrationArtifact,
    second: CalibrationArtifact,
    first_limits: Limits,
    second_limits: Limits,
) -> CameraAgreement:
    if primary.camera_id == secondary.camera_id:
        raise CalibrationError("INDEPENDENT_CAMERAS_REQUIRED")
    for measured, artifact in ((primary, first), (secondary, second)):
        if (
            measured.camera_id != artifact.candidate.camera.camera_id
            or measured.transform_fingerprint != artifact.candidate.x.fingerprint()
            or measured.configuration_fingerprint != artifact.candidate.camera.fingerprint()
        ):
            raise CalibrationError("CAMERA_AGREEMENT_ARTIFACT_MISMATCH")
    if first_limits.max_reference_error_mm is None or second_limits.max_reference_error_mm is None:
        raise CalibrationError("MISSING_REFERENCE_LIMIT")
    difference = dist(primary.point, secondary.point) * 1000
    limit = first_limits.max_reference_error_mm + second_limits.max_reference_error_mm
    failures = []
    if difference > limit:
        failures.append("CAMERA_POINTS_DISAGREE")
    mount, translation, rotation = None, None, None
    if first.candidate.board.fingerprint() == second.candidate.board.fingerprint():
        mount = first.candidate.board.mounting_id
        translation_m, rotation_rad = residual(
            np.array(first.candidate.y.matrix), np.array(second.candidate.y.matrix)
        )
        translation, rotation = translation_m * 1000, float(np.rad2deg(rotation_rad))
        if (
            first_limits.max_chain_translation_mm is None
            or second_limits.max_chain_translation_mm is None
            or first_limits.max_chain_rotation_deg is None
            or second_limits.max_chain_rotation_deg is None
        ):
            failures.append("MISSING_MOUNT_AGREEMENT_LIMIT")
        elif (
            translation
            > first_limits.max_chain_translation_mm + second_limits.max_chain_translation_mm
            or rotation > first_limits.max_chain_rotation_deg + second_limits.max_chain_rotation_deg
        ):
            failures.append("UNCHANGED_MOUNT_ESTIMATES_DISAGREE")
    return CameraAgreement(
        agreement_id=identity,
        primary_camera=primary.camera_id,
        secondary_camera=secondary.camera_id,
        primary_artifact_id=first.artifact_id,
        secondary_artifact_id=second.artifact_id,
        primary_point_m=primary.point,
        secondary_point_m=secondary.point,
        difference_mm=difference,
        limit_mm=limit,
        shared_mount_identity=mount,
        mounting_translation_mm=translation,
        mounting_rotation_deg=rotation,
        passed=not failures,
        failures=tuple(failures),
    )
