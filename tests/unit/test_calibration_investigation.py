"""Analytically specified signatures; these fixtures are not image-driven acceptance."""

import math

import numpy as np
import pytest
from test_calibration_diagnostics import references

from robotops.calibration.acquisition import AcquisitionReport
from robotops.calibration.checks import evaluate_references
from robotops.calibration.configuration import default_camera, framed
from robotops.calibration.contracts import (
    Coverage,
    ImageValidation,
    Limits,
    MeasurementRejection,
    PointFailure,
    PoseSample,
    ValidationReport,
)
from robotops.calibration.diagnostics import InvestigationInputs, investigate
from robotops.calibration.errors import CalibrationError


def routine_inputs(points, previous=None):
    camera, limits = default_camera("camera-west"), Limits()
    report = evaluate_references("current", camera.camera_id, "approved", points, (), limits)
    return InvestigationInputs(
        camera=camera,
        limits=limits,
        source_kind="routine-check",
        source_id=report.check_id,
        source_fingerprint=report.fingerprint(),
        references=points,
        routine=report,
        previous_routine=previous,
    )


@pytest.mark.parametrize(
    "scale,offset,expected",
    [
        (1.08, (0, 0, 0), "SCALE_ERROR_COMPATIBLE"),
        (1000, (0, 0, 0), "THOUSANDFOLD_SCALE"),
        (0.001, (0, 0, 0), "THOUSANDFOLD_SCALE"),
        (1, (0.04, -0.02, 0.01), "RIGID_ERROR_COMPATIBLE"),
        (1, (0, 0, 0), "INSUFFICIENT_EVIDENCE"),
    ],
)
def test_independent_spatial_signatures_never_claim_a_unique_cause(scale, offset, expected):
    data = routine_inputs(references(scale=scale, offset=offset))
    before = data.model_dump_json()
    report = investigate("analytical", data)
    assert expected in {item.code for item in report.clues}
    assert report.conclusion == "INSUFFICIENT_EVIDENCE / UNKNOWN_CAUSE"
    assert data.model_dump_json() == before
    assert "Never changes X" in report.scope


def test_distance_and_sudden_change_need_supported_independent_data():
    points = references(scale=1.08)
    amended = tuple(
        item.model_copy(
            update={
                "measurement": item.measurement.model_copy(
                    update={
                        "calculation": item.measurement.calculation.model_copy(
                            update={
                                "outputs": {
                                    "p_c_m": [0, 0, 2 * index + 1],
                                }
                            }
                        ),
                        "point": tuple(np.asarray(item.base_point_m) + [0.01 * (index + 1), 0, 0]),
                    }
                )
            }
        )
        for index, item in enumerate(points)
    )
    previous = evaluate_references(
        "previous", "camera-west", "approved", references(), (), Limits()
    )
    report = investigate("distance", routine_inputs(amended, previous))
    codes = {item.code for item in report.clues}
    assert {"DISTANCE_DEPENDENT_ERROR", "SUDDEN_DETERIORATION"} <= codes
    assert next(item for item in report.clues if item.code == "DISTANCE_DEPENDENT_ERROR").metrics[
        "correlation"
    ] == pytest.approx(1)
    short = investigate("too-short", routine_inputs(amended[:2]))
    assert {item.code for item in short.clues} == {"INSUFFICIENT_EVIDENCE"}


def test_large_chain_low_pnp_edge_and_orientation_signatures_are_distinct():
    camera, limits = default_camera("camera-west"), Limits()
    samples, rows = [], []
    pixels = (
        (20, 20),
        (930, 20),
        (930, 700),
        (20, 700),
        (450, 300),
        (490, 300),
        (450, 370),
        (490, 370),
    )
    residuals = ((1.0, 0),) * 4 + ((0.1, 0),) * 4
    rms = math.sqrt((4 + 4 * 0.01) / 8)
    for index in range(8):
        angle = index / 7
        rotation = np.array(
            [
                [math.cos(angle), 0, math.sin(angle), 0],
                [0, 1, 0, 0],
                [-math.sin(angle), 0, math.cos(angle), 0],
                [0, 0, 0, 1],
            ]
        )
        sample = PoseSample(
            capture_id=f"analytic-{index}",
            dataset_id="independent",
            camera_id=camera.camera_id,
            configuration_fingerprint=camera.fingerprint(),
            board_fingerprint="analytical",
            t_b_f=framed(rotation, "f", "b"),
            t_c_t=framed(np.eye(4), "t", "c"),
            corner_ids=tuple(range(8)),
            object_points_m=tuple((index * 0.01, 0.0, 0.0) for index in range(8)),
            image_points_px=pixels,
            residuals_px=residuals,
            pnp_rms_px=rms,
            candidate_rms_px=(rms,),
            partition="validation",
        )
        samples.append(sample)
        rows.append(
            ImageValidation(
                capture_id=sample.capture_id,
                point_count=8,
                pnp_rms_px=rms,
                chain_rms_px=6,
                chain_translation_mm=2 * index,
                chain_rotation_deg=0,
                pnp_residuals_px=residuals,
                chain_residuals_px=((6.0, 0.0),) * 8,
            )
        )
    validation = ValidationReport(
        report_id="analytical-report",
        candidate_id="analytic-candidate",
        candidate_fingerprint="analytic",
        limits_fingerprint=limits.fingerprint(),
        dataset_ids=("independent",),
        dataset_fingerprint="analytic",
        passed=False,
        failures=("CHAIN_RMS_PX",),
        images=tuple(rows),
        references=(),
        point_count=64,
        pnp_rms_px=rms,
        chain_rms_px=6,
        reference_count=0,
        reference_span_m=(0, 0, 0),
        reference_median_mm=None,
        reference_max_mm=None,
        reference_p95_mm=None,
        minimum_p95_count=20,
    )
    data = InvestigationInputs(
        camera=camera,
        limits=limits,
        source_kind="validation",
        source_id=validation.report_id,
        source_fingerprint=validation.fingerprint(),
        samples=tuple(samples),
        validation=validation,
    )
    result = investigate("analytic-signatures", data)
    assert {row.code for row in result.clues} == {
        "LOW_PNP_HIGH_CHAIN",
        "IMAGE_EDGE_ERROR",
        "ORIENTATION_DEPENDENT_OFFSET",
    }
    with pytest.raises(CalibrationError, match="IMAGE_BINDING"):
        investigate("missing", data.model_copy(update={"samples": tuple(samples[:-1])}))


def test_pose_diversity_timing_and_rejected_depth_have_actionable_clues():
    camera, limits = default_camera("camera-west"), Limits()
    rejection = MeasurementRejection(
        capture_id="late",
        reason="ACQUISITION_REJECTED",
        detail="TIMESTAMP_MISMATCH",
        stage="acquisition",
    )
    quality = AcquisitionReport(
        report_id="quality",
        plan_id="plan",
        dataset_id="repeated",
        camera_id=camera.camera_id,
        capture_count=18,
        limits_fingerprint=limits.fingerprint(),
        accepted_capture_ids=(),
        rejections=(rejection,),
        coverage=Coverage(
            sample_count=0,
            translation_span_m=(0, 0, 0),
            rotation_singular_values_rad=(0, 0, 0),
            image_fraction=0,
            failures=("INSUFFICIENT_COVERAGE",),
        ),
        ready_to_fit=False,
        next_action="Collect varied poses",
    )
    report = investigate(
        "quality",
        InvestigationInputs(
            camera=camera,
            limits=limits,
            source_kind="acquisition-report",
            source_id=quality.report_id,
            source_fingerprint=quality.fingerprint(),
            acquisition=quality,
            rejections=(rejection,),
        ),
    )
    assert {item.code for item in report.clues} == {
        "ACQUISITION_ALIGNMENT_REJECTED",
        "INSUFFICIENT_POSE_DIVERSITY",
    }
    point = PointFailure(
        camera_id=camera.camera_id,
        code="MIXED_FOREGROUND_BACKGROUND_DEPTH",
        detail="mixed",
        selected_rgb_pixel=(10, 10),
    )
    report = investigate(
        "depth",
        InvestigationInputs(
            camera=camera,
            limits=limits,
            source_kind="runtime-point-error",
            source_id="capture",
            source_fingerprint=point.fingerprint(),
            point_error=point,
        ),
    )
    assert report.clues[0].code == "DEPTH_ASSOCIATION_REJECTED"


def test_collapsed_reference_geometry_does_not_produce_nan_diagnostic_scale():
    collapsed = tuple(
        item.model_copy(
            update={"measurement": item.measurement.model_copy(update={"point": (0, 0, 0)})}
        )
        for item in references()
    )
    report = investigate("collapsed", routine_inputs(collapsed))
    assert report.clues[0].code == "INSUFFICIENT_EVIDENCE"
