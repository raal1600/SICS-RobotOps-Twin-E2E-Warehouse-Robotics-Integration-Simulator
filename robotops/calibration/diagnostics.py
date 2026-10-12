"""Evidence-limited diagnostic clues. No solver, approval or parameter update lives here."""

from typing import Literal

import numpy as np
from pydantic import Field
from scipy.spatial.transform import Rotation

from robotops.calibration.acquisition import AcquisitionReport
from robotops.calibration.checks import RoutineCheck, diagnose
from robotops.calibration.contracts import (
    Calculation,
    Camera,
    Id,
    IndependentReference,
    Limits,
    MeasurementRejection,
    PointFailure,
    PoseSample,
    Record,
    ValidationReport,
)
from robotops.calibration.errors import CalibrationError
from robotops.calibration.outcome import PickOutcome
from robotops.calibration.tcp import ToolVerification

InvestigationKind = Literal[
    "validation",
    "routine-check",
    "acquisition-report",
    "tool-verification",
    "rejection",
    "runtime-point-error",
    "pick-outcome",
]


class InvestigationInputs(Record):
    camera: Camera
    limits: Limits
    source_kind: InvestigationKind
    source_id: Id
    source_fingerprint: str
    samples: tuple[PoseSample, ...] = ()
    references: tuple[IndependentReference, ...] = ()
    rejections: tuple[MeasurementRejection, ...] = ()
    validation: ValidationReport | None = None
    routine: RoutineCheck | None = None
    previous_routine: RoutineCheck | None = None
    acquisition: AcquisitionReport | None = None
    tool: ToolVerification | None = None
    point_error: PointFailure | None = None
    pick_outcome: PickOutcome | None = None


class DiagnosticClue(Record):
    code: str
    observation: str
    metrics: dict[str, float] = Field(default_factory=dict)
    investigate: str
    next_measurement: str
    limitation: str


class InvestigationReport(Record):
    investigation_id: Id
    camera_id: Id
    inputs_fingerprint: str
    source_kind: InvestigationKind
    source_id: Id
    source_fingerprint: str
    conclusion: Literal["INSUFFICIENT_EVIDENCE / UNKNOWN_CAUSE"] = (
        "INSUFFICIENT_EVIDENCE / UNKNOWN_CAUSE"
    )
    clues: tuple[DiagnosticClue, ...]
    calculation: Calculation
    scope: str = (
        "Non-authorizing comparison of saved measurements. Clues suggest further checks, "
        "not proven causes. Never changes X, depth scale, TCP, limits or approval. "
        "A missed pick alone does not establish a calibration fault."
    )


def investigate(identity: str, data: InvestigationInputs) -> InvestigationReport:
    """Frozen SIMULATION_ONLY screening rules, separate from acceptance thresholds."""
    clues: list[DiagnosticClue] = []
    selected = {
        "validation": data.validation,
        "routine-check": data.routine,
        "acquisition-report": data.acquisition,
        "tool-verification": data.tool,
        "rejection": data.rejections[0] if data.rejections else None,
        "runtime-point-error": data.point_error,
        "pick-outcome": data.pick_outcome,
    }[data.source_kind]
    if selected is None or selected.fingerprint() != data.source_fingerprint:
        raise CalibrationError("INVESTIGATION_SOURCE_BINDING_MISMATCH")
    reference_rows = (
        data.validation.references
        if data.validation
        else data.routine.references
        if data.routine
        else ()
    )
    if (data.validation or data.routine) and {r.reference_id for r in reference_rows} != {
        r.reference_id for r in data.references
    }:
        raise CalibrationError("INVESTIGATION_REFERENCE_BINDING_MISMATCH")

    def add(
        code: str,
        observation: str,
        suspects: str,
        next_measurement: str,
        limitation: str,
        **metrics: float,
    ) -> None:
        clues.append(
            DiagnosticClue(
                code=code,
                observation=observation,
                metrics=metrics,
                investigate=suspects,
                next_measurement=next_measurement,
                limitation=limitation,
            )
        )

    camera, limits = data.camera, data.limits
    if any(item.camera_id != camera.camera_id for item in data.samples):
        raise CalibrationError("INVESTIGATION_CAMERA_MISMATCH")
    report = data.validation
    if report:
        sample_map = {sample.capture_id: sample for sample in data.samples}
        if set(sample_map) != {row.capture_id for row in report.images}:
            raise CalibrationError("INVESTIGATION_IMAGE_BINDING_MISMATCH")
        if report.limits_fingerprint != limits.fingerprint():
            raise CalibrationError("INVESTIGATION_LIMITS_MISMATCH")
        if (
            report.pnp_rms_px is not None
            and report.chain_rms_px is not None
            and limits.max_pnp_rms_px is not None
            and limits.max_chain_rms_px is not None
            and report.pnp_rms_px <= limits.max_pnp_rms_px
            and report.chain_rms_px > limits.max_chain_rms_px
        ):
            add(
                "LOW_PNP_HIGH_CHAIN",
                "The board image fits but the robot-to-camera chain does not.",
                "X, transform inverses/directions, flange pose semantics, Y and timestamp alignment.",
                "Acquire settled board views with independently checked flange poses and timestamps.",
                "Small PnP error does not validate the installed camera transform.",
                pnp_rms_px=report.pnp_rms_px,
                chain_rms_px=report.chain_rms_px,
            )
        edge, center, angles, offsets = [], [], [], []
        first_rotation = None
        for row in report.images:
            sample = sample_map[row.capture_id]
            if len(sample.image_points_px) != len(row.pnp_residuals_px):
                raise CalibrationError("INVESTIGATION_CORNER_BINDING_MISMATCH")
            for pixel, error in zip(sample.image_points_px, row.pnp_residuals_px, strict=True):
                radius = max(
                    abs(2 * pixel[0] / camera.rgb.width - 1),
                    abs(2 * pixel[1] / camera.rgb.height - 1),
                )
                norm = float(np.linalg.norm(error))
                if radius >= 0.65:
                    edge.append(norm)
                elif radius <= 0.35:
                    center.append(norm)
            rotation = Rotation.from_matrix(np.asarray(sample.t_b_f.matrix)[:3, :3])
            if first_rotation is None:
                first_rotation = rotation
            angles.append(float((rotation * first_rotation.inv()).magnitude()))
            offsets.append(row.chain_translation_mm)
        if len(edge) >= 12 and len(center) >= 12:
            edge_median, center_median = float(np.median(edge)), float(np.median(center))
            if edge_median > max(0.5, 3 * center_median):
                add(
                    "IMAGE_EDGE_ERROR",
                    "Image residuals are larger near the image edges.",
                    "Intrinsics, distortion model, crop/resolution and corner detection.",
                    "Measure an independent board across the image, then verify the active optical profile.",
                    "This pattern cannot uniquely distinguish optics from image-feature errors.",
                    edge_median_px=edge_median,
                    center_median_px=center_median,
                    edge_points=float(len(edge)),
                    center_points=float(len(center)),
                )
        correlation = _correlation(angles, offsets, 8, 0.3)
        if correlation is not None and correlation > 0.75 and max(offsets) - min(offsets) > 3:
            add(
                "ORIENTATION_DEPENDENT_OFFSET",
                "Chain translation error grows with flange rotation.",
                "Flange/TCP conventions, board mounting Y, tool offset and mechanical flex.",
                "Repeat varied rotations at fixed positions; verify the tool and board mounting independently.",
                "Position and orientation may be confounded; board images do not directly verify the TCP.",
                correlation=correlation,
                angular_span_rad=max(angles) - min(angles),
                offset_span_mm=max(offsets) - min(offsets),
            )

    if data.references:
        diagnostic = diagnose(data.references)
        if diagnostic.diagnostic_scale is not None:
            scale = diagnostic.diagnostic_scale
            if 0.0008 < scale < 0.0012 or 800 < scale < 1200:
                add(
                    "THOUSANDFOLD_SCALE",
                    "Independent reference geometry is compatible with a roughly 1000-fold scale discrepancy.",
                    "Meter/millimeter conventions and depth-unit declarations.",
                    "Check raw units against a separately measured distance before any rigid fitting.",
                    "The diagnostic scale is not applied to the camera transform or depth values.",
                    diagnostic_scale=scale,
                )
            elif "SCALE_ERROR_COMPATIBLE" in diagnostic.clues:
                add(
                    "SCALE_ERROR_COMPATIBLE",
                    "A scale-plus-rigid hypothesis explains these references better than a rigid-only hypothesis.",
                    "Depth scale, range-versus-axial semantics and metric dimensions.",
                    "Measure independent distances at several depths; keep X fixed during that check.",
                    "Similarity fitting is a diagnostic comparison, never an operational correction.",
                    diagnostic_scale=scale,
                    rigid_rms_mm=float(diagnostic.rigid_residual_rms_mm or 0),
                    similarity_rms_mm=float(diagnostic.similarity_residual_rms_mm or 0),
                )
            elif "RIGID_ERROR_COMPATIBLE" in diagnostic.clues:
                add(
                    "RIGID_ERROR_COMPATIBLE",
                    "The reference error is compatible with a rigid offset.",
                    "Camera mount, frame direction, timing and residual robot error.",
                    "Cross-check RGB board-chain evidence and reported flange timing independently.",
                    "These combined RGB-D references cannot uniquely identify a moved camera.",
                    rigid_rms_mm=float(diagnostic.rigid_residual_rms_mm or 0),
                )
        distances, errors = [], []
        for item in data.references:
            pc = item.measurement.calculation.outputs.get("p_c_m")
            if isinstance(pc, list) and len(pc) == 3:
                distances.append(float(np.linalg.norm(pc)))
                errors.append(
                    float(
                        np.linalg.norm(np.asarray(item.measurement.point) - item.base_point_m)
                        * 1000
                    )
                )
        correlation = _correlation(distances, errors, 6, 0.3)
        if correlation is not None and correlation > 0.75 and max(errors) - min(errors) > 3:
            add(
                "DISTANCE_DEPENDENT_ERROR",
                "Reference error increases with measured camera distance.",
                "Depth scale/bias, range semantics or angular error in X.",
                "Compare independent near/far distances and RGB chain residuals without adjusting X.",
                "Distance correlation does not distinguish depth error from an angular transform error.",
                correlation=correlation,
                distance_span_m=max(distances) - min(distances),
                error_span_mm=max(errors) - min(errors),
            )

    codes = {item.reason for item in data.rejections}
    for rejected in data.rejections:
        if rejected.reason == "ACQUISITION_REJECTED":
            codes.update(rejected.detail.split(", "))
    if data.point_error:
        codes.add(data.point_error.code)
    if any(
        any(word in code for word in ("MIXED", "OCCLU", "OBJECT_EDGE", "AMBIGUOUS_DEPTH"))
        for code in codes
    ):
        add(
            "DEPTH_ASSOCIATION_REJECTED",
            "A saved depth result cannot be associated with a unique visible surface.",
            "RGB/depth registration, occlusion and foreground/background mixing.",
            "Inspect native depth, the RGB mask and correspondence near the object edge.",
            "No valid target exists for this rejected point; do not substitute background depth.",
        )
    if any("TIMESTAMP" in code or "SETTL" in code or "MOVING" in code for code in codes):
        add(
            "ACQUISITION_ALIGNMENT_REJECTED",
            "Recorded motion or timing failed acquisition admission.",
            "Settling and RGB/depth/flange timestamp alignment.",
            "Wait for settling, verify clocks, then acquire a new identified capture.",
            "A timing rejection does not prove X is wrong.",
        )
    if data.acquisition and data.acquisition.coverage.failures:
        coverage = data.acquisition.coverage
        add(
            "INSUFFICIENT_POSE_DIVERSITY",
            "The measured dataset fails its declared coverage/conditioning requirements.",
            "Pose diversity, repeated or single-axis poses, metric dimensions and mechanical flex.",
            "Collect planned multi-axis rotations and varied positions/depths; inspect excluded views.",
            "More images at nearly the same pose do not supply independent geometric constraints.",
            accepted_images=float(coverage.sample_count),
            minimum_rotation_singular_rad=min(coverage.rotation_singular_values_rad),
        )
    if data.tool and not data.tool.passed:
        add(
            "INDEPENDENT_TOOL_CHECK_FAILED",
            "Separate tool metrology failed; changing camera X is not a remedy.",
            "Physical TCP/tool geometry and its declared configuration.",
            "Inspect pivot and indexed orientation probes, correct the tool, and repeat its independent check.",
            "This does not establish a camera mounting fault or calibrate robot kinematics.",
            translation_error_mm=data.tool.translation_error_mm,
            orientation_error_deg=data.tool.orientation_error_deg,
        )
    current, previous = data.routine, data.previous_routine
    if (
        current
        and previous
        and current.artifact_id == previous.artifact_id
        and current.camera_id == previous.camera_id
        and current.maximum_error_mm is not None
        and previous.maximum_error_mm is not None
        and current.maximum_error_mm > max(5, previous.maximum_error_mm * 3)
    ):
        add(
            "SUDDEN_DETERIORATION",
            "A later reference check is substantially worse for the same artifact.",
            "Mount, profile, registration, board/tool changes and mechanical behavior.",
            "Review recorded configuration changes and repeat independent reference and tool checks.",
            "A change over time is a clue, not proof of which component moved.",
            prior_max_mm=previous.maximum_error_mm,
            current_max_mm=current.maximum_error_mm,
        )
    if data.pick_outcome and data.pick_outcome.verification.verdict == "VERIFIED_FAILURE":
        pick = data.pick_outcome
        add(
            "MISSED_TRANSFER_CAUSE_UNRESOLVED",
            "The original command and fresh observation confirm no completed product transfer.",
            "Contact/adhesion, tool geometry, perception, camera/depth registration, timing and mechanical behavior.",
            "Keep X unchanged. Inspect the original target and contact, then collect independent references and separate tool measurements before authorizing another attempt.",
            "A failed transfer does not distinguish these causes. No automatic second pick or calibration update is authorized.",
            recorded_effect_count=float(pick.receipt.effect_count) if pick.receipt else 0,
        )
    if not clues:
        add(
            "INSUFFICIENT_EVIDENCE",
            "The selected evidence does not distinguish a cause.",
            "Camera mounting, depth/registration, timing, TCP, contact and mechanics separately.",
            "Collect independent references at varied depths and check the tool; retain the original command if its outcome is uncertain.",
            "No automatic recalibration or second pick follows from this investigation.",
        )
    return InvestigationReport(
        investigation_id=identity,
        camera_id=camera.camera_id,
        inputs_fingerprint=data.fingerprint(),
        source_kind=data.source_kind,
        source_id=data.source_id,
        source_fingerprint=data.source_fingerprint,
        clues=tuple(clues),
        calculation=Calculation(
            function="robotops.calibration.diagnostics.investigate",
            formula="SIMULATION_ONLY diagnostic-screen-1: pointwise norms; edge/center medians; Pearson correlation with support/span guards; rigid-versus-similarity comparison. Units are never combined into a score.",
            inputs=data.model_dump(mode="json"),
            outputs={"clues": [item.model_dump(mode="json") for item in clues]},
            decision="INSUFFICIENT_EVIDENCE / UNKNOWN_CAUSE; no operational parameters changed",
        ),
    )


def _correlation(x: list[float], y: list[float], count: int, span: float) -> float | None:
    if len(x) < count or max(x) - min(x) < span or np.std(y) < 1e-9:
        return None
    return float(np.corrcoef(x, y)[0, 1])
