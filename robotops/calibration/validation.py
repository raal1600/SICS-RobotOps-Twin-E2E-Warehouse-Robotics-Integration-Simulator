"""Independent holdout evaluation. No fitting, tuning or oracle lookup happens here."""

import hashlib
import json
from collections.abc import Sequence
from typing import cast

import numpy as np

from robotops.calibration.contracts import (
    Candidate,
    ImageValidation,
    IndependentReference,
    Limits,
    MeasurementRejection,
    PoseSample,
    ReferenceValidation,
    ValidationReport,
    Vec2,
    Vec3,
)
from robotops.calibration.errors import CalibrationError
from robotops.calibration.geometry import inverse, point_rms, points, project, residual


def validate(
    candidate: Candidate,
    samples: Sequence[PoseSample],
    references: Sequence[IndependentReference],
    limits: Limits,
    report_id: str,
    rejected: Sequence[MeasurementRejection] = (),
) -> ValidationReport:
    """Metric-specific gates, independently recomputed residuals, and supported statistics.

    Dataset one-time allocation is enforced by the persistent lifecycle transaction.
    This pure function additionally rejects overlapping fit/validation identities.
    """
    if limits.fingerprint() != candidate.limits_fingerprint:
        raise CalibrationError("LIMITS_CHANGED_AFTER_FIT")
    if any(sample.partition != "validation" for sample in samples):
        raise CalibrationError("INDEPENDENT_VALIDATION_PARTITION_REQUIRED")
    if len({sample.capture_id for sample in samples}) != len(samples) or len(
        {reference.reference_id for reference in references}
    ) != len(references):
        raise CalibrationError("DUPLICATE_VALIDATION_OBSERVATION")
    if {r.capture_id for r in rejected} & {s.capture_id for s in samples}:
        raise CalibrationError("REJECTED_VALIDATION_MEASUREMENT_USED")
    dataset_ids = tuple(
        sorted({s.dataset_id for s in samples} | {r.dataset_id for r in references})
    )
    if set(dataset_ids) & set(candidate.dataset_ids) or set(candidate.sample_ids) & {
        sample.capture_id for sample in samples
    }:
        raise CalibrationError("FIT_VALIDATION_DATA_LEAKAGE")
    camera, board = candidate.camera, candidate.board
    for sample in samples:
        if (
            sample.camera_id != camera.camera_id
            or sample.configuration_fingerprint != camera.fingerprint()
            or sample.board_fingerprint != board.fingerprint()
        ):
            raise CalibrationError("VALIDATION_CONFIGURATION_MISMATCH")
    for reference in references:
        if (
            reference.measurement.camera_id != camera.camera_id
            or reference.measurement.configuration_fingerprint != camera.fingerprint()
            or reference.measurement.transform_fingerprint != candidate.x.fingerprint()
        ):
            raise CalibrationError("REFERENCE_CONFIGURATION_MISMATCH")
    failures: list[str] = []
    thresholds = {
        "PNP_RMS_PX": limits.max_pnp_rms_px,
        "CHAIN_RMS_PX": limits.max_chain_rms_px,
        "CHAIN_TRANSLATION_MM": limits.max_chain_translation_mm,
        "CHAIN_ROTATION_DEG": limits.max_chain_rotation_deg,
        "REFERENCE_ERROR_MM": limits.max_reference_error_mm,
    }
    failures.extend(f"MISSING_LIMIT_{key}" for key, value in thresholds.items() if value is None)
    if len(samples) < limits.min_samples:
        failures.append("INSUFFICIENT_INDEPENDENT_IMAGES")
    if len(references) < limits.min_samples:
        failures.append("INSUFFICIENT_INDEPENDENT_REFERENCES")
    images: list[ImageValidation] = []
    for sample in samples:
        a, b = np.asarray(sample.t_b_f.matrix), np.asarray(sample.t_c_t.matrix)
        x, y = np.asarray(candidate.x.matrix), np.asarray(candidate.y.matrix)
        measured = np.asarray(sample.image_points_px)
        object_points = np.asarray(sample.object_points_m)
        predicted_pnp = project(
            points(b, object_points),
            np.asarray(camera.rgb.k),
            np.asarray(camera.rgb.coefficients),
            camera.rgb.distortion_model,
        )
        predicted_chain = project(
            points(inverse(x) @ a @ y, object_points),
            np.asarray(camera.rgb.k),
            np.asarray(camera.rgb.coefficients),
            camera.rgb.distortion_model,
        )
        pnp_error, chain_error = measured - predicted_pnp, measured - predicted_chain
        translation_m, rotation_rad = residual(a @ y, x @ b)
        image = ImageValidation(
            capture_id=sample.capture_id,
            point_count=len(measured),
            pnp_rms_px=point_rms(pnp_error),
            chain_rms_px=point_rms(chain_error),
            chain_translation_mm=translation_m * 1000,
            chain_rotation_deg=float(np.rad2deg(rotation_rad)),
            pnp_residuals_px=cast(tuple[Vec2, ...], tuple(map(tuple, pnp_error.tolist()))),
            chain_residuals_px=cast(tuple[Vec2, ...], tuple(map(tuple, chain_error.tolist()))),
        )
        for key, value in (
            ("PNP_RMS_PX", image.pnp_rms_px),
            ("CHAIN_RMS_PX", image.chain_rms_px),
            ("CHAIN_TRANSLATION_MM", image.chain_translation_mm),
            ("CHAIN_ROTATION_DEG", image.chain_rotation_deg),
        ):
            threshold = thresholds[key]
            if threshold is not None and value > threshold:
                failures.append(f"{key}:{sample.capture_id}")
        images.append(image)
    checked_references: list[ReferenceValidation] = []
    for reference in references:
        expected, predicted = (
            np.asarray(reference.base_point_m),
            np.asarray(reference.measurement.point),
        )
        error_vector = predicted - expected
        error_mm = float(np.linalg.norm(error_vector) * 1000)
        checked_references.append(
            ReferenceValidation(
                reference_id=reference.reference_id,
                expected_base_m=reference.base_point_m,
                predicted_base_m=reference.measurement.point,
                error_vector_m=cast(Vec3, tuple(error_vector.tolist())),
                error_mm=error_mm,
            )
        )
        if limits.max_reference_error_mm is not None and error_mm > limits.max_reference_error_mm:
            failures.append(f"REFERENCE_ERROR_MM:{reference.reference_id}")
    spans = np.ptp([r.base_point_m for r in references], axis=0) if references else np.zeros(3)
    if (spans < np.asarray(limits.min_translation_span_m)).any():
        failures.append("INSUFFICIENT_REFERENCE_COVERAGE")
    magnitudes = np.array([r.error_mm for r in checked_references])
    point_count = sum(image.point_count for image in images)
    # All 2D points contribute equally, even when images have different corner counts.
    pnp_rms = (
        point_rms(np.concatenate([image.pnp_residuals_px for image in images])) if images else None
    )
    chain_rms = (
        point_rms(np.concatenate([image.chain_residuals_px for image in images]))
        if images
        else None
    )
    identity = {
        "samples": [s.fingerprint() for s in samples],
        "references": [r.fingerprint() for r in references],
    }
    dataset_hash = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return ValidationReport(
        report_id=report_id,
        candidate_id=candidate.candidate_id,
        candidate_fingerprint=candidate.fingerprint(),
        limits_fingerprint=limits.fingerprint(),
        dataset_ids=dataset_ids,
        dataset_fingerprint=dataset_hash,
        passed=not failures,
        failures=tuple(failures),
        images=tuple(images),
        references=tuple(checked_references),
        point_count=point_count,
        pnp_rms_px=pnp_rms,
        chain_rms_px=chain_rms,
        reference_count=len(references),
        reference_span_m=cast(Vec3, tuple(spans.tolist())),
        reference_median_mm=float(np.median(magnitudes)) if len(magnitudes) else None,
        reference_max_mm=float(np.max(magnitudes)) if len(magnitudes) else None,
        reference_p95_mm=float(np.quantile(magnitudes, 0.95, method=limits.quantile_method))
        if len(magnitudes) >= limits.minimum_p95_count
        else None,
        minimum_p95_count=limits.minimum_p95_count,
        rejected_measurements=tuple(rejected),
    )
