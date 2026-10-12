"""Routine reference checks and conservative, non-authorizing diagnostic comparisons."""

import numpy as np

from robotops.calibration.contracts import IndependentReference, Limits, Record, ReferenceValidation


class Diagnostic(Record):
    conclusion: str
    clues: tuple[str, ...]
    next_measurements: tuple[str, ...]
    rigid_residual_rms_mm: float | None = None
    similarity_residual_rms_mm: float | None = None
    diagnostic_scale: float | None = None
    scope: str = (
        "Hypothesis comparison only; never changes X, depth scale, tool geometry or approval"
    )


class RoutineCheck(Record):
    check_id: str
    camera_id: str
    artifact_id: str
    references: tuple[ReferenceValidation, ...]
    failed_capture_ids: tuple[str, ...]
    passed: bool
    failures: tuple[str, ...]
    maximum_error_mm: float | None
    reference_count: int
    diagnostic: Diagnostic
    scope: str = "Observes combined RGB/depth-to-base reference accuracy. Does not independently verify the TCP, grasp, flex or robot kinematics."


def diagnose(references: tuple[IndependentReference, ...]) -> Diagnostic:
    """Fit competing diagnostic explanations, never an operational calibration.

    Distributed 3D surveyed points are necessary to distinguish uniform scale from
    rigid offset. A single missed pick cannot distinguish either from tool/contact error.
    The similarity scale is an explanation of the error, never an applied correction.
    """
    unclear = Diagnostic(
        conclusion="INSUFFICIENT_EVIDENCE / UNKNOWN_CAUSE",
        clues=(),
        next_measurements=(
            "Observe independent reference points at varied depths and positions.",
            "Check camera profile/registration, tool metrology, timing and mechanical stability separately.",
        ),
    )
    if len(references) < 6:
        return unclear
    measured = np.array([reference.measurement.point for reference in references])
    expected = np.array([reference.base_point_m for reference in references])
    left, right = measured - measured.mean(axis=0), expected - expected.mean(axis=0)
    if np.linalg.matrix_rank(right, tol=0.01) < 3 or np.linalg.matrix_rank(left, tol=0.00001) < 3:
        return unclear
    u, singular, vt = np.linalg.svd(left.T @ right)
    signs = np.diag([1.0, 1.0, float(np.linalg.det(u @ vt))])
    rotation = u @ signs @ vt
    scale = float(np.sum(singular * np.diag(signs)) / np.sum(left**2))
    rigid_error = float(np.sqrt(np.mean(np.sum((left @ rotation - right) ** 2, axis=1))) * 1000)
    similarity_error = float(
        np.sqrt(np.mean(np.sum((scale * left @ rotation - right) ** 2, axis=1))) * 1000
    )
    scale_signature = (
        abs(scale - 1) > 0.01 and similarity_error < rigid_error / 3 and similarity_error < 5
    )
    rigid_signature = (
        rigid_error < 5 and np.linalg.norm(measured.mean(axis=0) - expected.mean(axis=0)) > 0.01
    )
    clues = (
        ("SCALE_ERROR_COMPATIBLE",)
        if scale_signature
        else ("RIGID_ERROR_COMPATIBLE",)
        if rigid_signature
        else ("NO_UNIQUE_ERROR_SIGNATURE",)
    )
    return Diagnostic(
        conclusion="INSUFFICIENT_EVIDENCE / UNKNOWN_CAUSE",
        clues=clues,
        next_measurements=(
            "Verify depth scale/semantics using independent distances; do not absorb scale into X.",
        )
        if scale_signature
        else (
            "Compare camera mounting and reported flange timing with independent RGB board observations.",
            "Verify TCP separately; reference-point observations do not observe tool geometry.",
        ),
        rigid_residual_rms_mm=rigid_error,
        similarity_residual_rms_mm=similarity_error,
        diagnostic_scale=scale,
    )


def evaluate_references(
    identity: str,
    camera_id: str,
    artifact_id: str,
    references: tuple[IndependentReference, ...],
    failed: tuple[str, ...],
    limits: Limits,
) -> RoutineCheck:
    rows = []
    for reference in references:
        vector = np.array(reference.measurement.point) - reference.base_point_m
        rows.append(
            ReferenceValidation(
                reference_id=reference.reference_id,
                expected_base_m=reference.base_point_m,
                predicted_base_m=reference.measurement.point,
                error_vector_m=tuple(vector.tolist()),
                error_mm=float(np.linalg.norm(vector) * 1000),
            )
        )
    maximum = max((row.error_mm for row in rows), default=None)
    failures = []
    if failed:
        failures.append("REFERENCE_MEASUREMENT_REJECTED")
    if (
        len(rows) < 6
        or np.linalg.matrix_rank(
            np.array([row.expected_base_m for row in rows])
            - np.mean([row.expected_base_m for row in rows], axis=0)
        )
        < 3
    ):
        failures.append("INSUFFICIENT_REFERENCE_COVERAGE")
    if limits.max_reference_error_mm is None:
        failures.append("MISSING_REFERENCE_LIMIT")
    elif maximum is None or maximum > limits.max_reference_error_mm:
        failures.append("REFERENCE_ERROR_LIMIT_EXCEEDED")
    return RoutineCheck(
        check_id=identity,
        camera_id=camera_id,
        artifact_id=artifact_id,
        references=tuple(rows),
        failed_capture_ids=failed,
        passed=not failures,
        failures=tuple(failures),
        maximum_error_mm=maximum,
        reference_count=len(rows),
        diagnostic=diagnose(references),
    )
