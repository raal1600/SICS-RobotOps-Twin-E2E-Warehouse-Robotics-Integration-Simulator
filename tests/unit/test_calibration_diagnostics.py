"""Independent analytical signatures; comparisons never become operational corrections."""

import itertools

import numpy as np
import pytest

from robotops.calibration.checks import diagnose, evaluate_references
from robotops.calibration.configuration import default_camera
from robotops.calibration.contracts import (
    Calculation,
    IndependentReference,
    Limits,
    PointMeasurement,
)
from robotops.calibration.errors import CalibrationError
from robotops.calibration.estimation import pose_conditioning


def references(scale=1.0, offset=(0.0, 0.0, 0.0)):
    result = []
    for index, expected in enumerate(itertools.product((-0.2, 0.2), (-0.1, 0.1), (0.3, 0.7))):
        measured = tuple(
            scale * point + shift for point, shift in zip(expected, offset, strict=True)
        )
        result.append(
            IndependentReference(
                reference_id=f"reference-{index}",
                dataset_id="analytic-survey",
                base_point_m=expected,
                measurement=PointMeasurement(
                    point=measured,
                    camera_id="camera-west",
                    configuration_fingerprint="golden",
                    transform_fingerprint="golden",
                    selected_rgb_pixel=(12, 20),
                    native_depth_pixel=(5, 9),
                    raw_depth_value=1000,
                    calculation=Calculation(
                        function="analytical-fixture",
                        formula="s*p + offset",
                        inputs={},
                        outputs={},
                        decision="test fixture",
                    ),
                ),
            )
        )
    return tuple(result)


def test_scale_and_rigid_signatures_are_clues_not_automatic_calibration():
    scale = diagnose(references(scale=1.06, offset=(0.01, 0.02, 0.03)))
    rigid = diagnose(references(offset=(0.04, -0.03, 0.02)))
    assert scale.clues == ("SCALE_ERROR_COMPATIBLE",)
    assert scale.diagnostic_scale == pytest.approx(1 / 1.06)
    assert scale.similarity_residual_rms_mm < 1e-8
    assert scale.rigid_residual_rms_mm > 5
    assert rigid.clues == ("RIGID_ERROR_COMPATIBLE",)
    assert rigid.rigid_residual_rms_mm < 1e-8
    assert scale.conclusion == rigid.conclusion == "INSUFFICIENT_EVIDENCE / UNKNOWN_CAUSE"
    assert "never changes X" in scale.scope
    assert diagnose(()).clues == ()
    assert diagnose(references()[:2]).conclusion == "INSUFFICIENT_EVIDENCE / UNKNOWN_CAUSE"


def test_routine_check_fails_bad_points_missing_limits_or_rejected_measurements():
    good = evaluate_references(
        "routine-good", "camera-west", "approved-1", references(), (), Limits()
    )
    assert good.passed and good.maximum_error_mm == 0
    assert not evaluate_references(
        "bad", "camera-west", "approved-1", references(scale=1.1), (), Limits()
    ).passed
    assert not evaluate_references(
        "missing",
        "camera-west",
        "approved-1",
        references(),
        (),
        Limits(max_reference_error_mm=None),
    ).passed
    assert not evaluate_references(
        "depth-error", "camera-west", "approved-1", references(), ("capture-3",), Limits()
    ).passed


def test_image_only_pose_conditioning_rejects_collinear_or_distant_observations():
    pose = np.eye(4)
    pose[2, 3] = 1.0
    camera = default_camera("camera-west")
    collinear = np.array([[index * 0.02, 0, 0] for index in range(10)])
    with pytest.raises(CalibrationError, match="PNP_POSE_UNDERCONSTRAINED"):
        pose_conditioning(pose, collinear, camera, 0.2, Limits())
    pose[2, 3] = 20.0
    square = np.array([[x, y, 0] for x, y in itertools.product((0.0, 0.1, 0.2), (0.0, 0.1, 0.2))])
    with pytest.raises(CalibrationError, match="PNP_POSE_UNDERCONSTRAINED"):
        pose_conditioning(pose, square, camera, 0.2, Limits())
