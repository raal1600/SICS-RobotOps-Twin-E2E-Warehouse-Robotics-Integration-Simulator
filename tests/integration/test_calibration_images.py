"""Fresh rendered pixels -> real detection/PnP -> measured inactive calibration.

The oracle is deliberately used only after fitting to assert numerical accuracy.
This is numerical/image integration evidence, not yet browser/runtime acceptance.
"""

import json

import cv2
import numpy as np
import pytest

from robotops.calibration.artifacts import SensorArtifacts
from robotops.calibration.configuration import framed
from robotops.calibration.contracts import IndependentReference, Limits, MeasurementRejection
from robotops.calibration.depth import reconstruct
from robotops.calibration.errors import CalibrationError
from robotops.calibration.estimation import estimate_board, fit
from robotops.calibration.geometry import residual
from robotops.calibration.perception import reference_center
from robotops.calibration.synthetic import SyntheticSensorWorld, instructor_reference
from robotops.calibration.validation import validate


@pytest.mark.parametrize("seed", [29, 83])
@pytest.mark.parametrize("camera_id", ["camera-west", "camera-east"])
def test_fresh_images_recover_hidden_calibration(tmp_path, seed, camera_id):
    artifacts = SensorArtifacts(tmp_path / "images")
    world = SyntheticSensorWorld(seed, artifacts)
    limits = Limits()
    captures, samples, acquisition_rejections = [], [], []
    camera = world.cameras[camera_id]
    for i, pose in enumerate(world.planned_poses("fit")):
        capture = world.acquire(camera_id, pose, f"seed-{seed}-fit", i, "fit", limits)
        rgb = artifacts.read_rgb(capture.rgb)
        captures.append(capture)
        try:
            sample = estimate_board(capture, rgb, camera, world.board, limits)
        except CalibrationError as error:
            # The new image-only sensitivity gate can reject a detected but weak
            # pose. Preserve that decision; count/coverage and X/Y accuracy below
            # still have to pass without weakening any numerical acceptance limit.
            assert error.code == "PNP_POSE_UNDERCONSTRAINED"
            acquisition_rejections.append(
                {"capture_id": capture.capture_id, "reason": error.code, "detail": error.detail}
            )
            continue
        samples.append(sample)
        if i == 0:
            overlay = rgb.copy()
            cv2.aruco.drawDetectedCornersCharuco(
                overlay,
                np.array(sample.image_points_px, dtype=np.float32).reshape(-1, 1, 2),
                np.array(sample.corner_ids, dtype=np.int32).reshape(-1, 1),
            )
            artifacts.rgb(overlay)
    assert len(samples) >= limits.min_samples
    assert len(samples) + len(acquisition_rejections) == len(captures)
    # No oracle access occurred during measurement or estimation.
    unknown = fit(samples, camera, world.board, limits, "image-estimate")
    truth_x, truth_y = instructor_reference(world, camera_id)
    known = fit(samples, camera, world.board, limits, "known-mount", framed(truth_y, "t", "f"))
    errors = {}
    for label, candidate in (("known", known), ("unknown", unknown)):
        x_error = residual(np.array(candidate.x.matrix), truth_x)
        y_error = residual(np.array(candidate.y.matrix), truth_y)
        errors[label] = {
            "x_translation_m": x_error[0],
            "x_angle_rad": x_error[1],
            "y_translation_m": y_error[0],
            "y_angle_rad": y_error[1],
        }
    (tmp_path / "measurements.json").write_text(
        json.dumps(
            {
                "seed": seed,
                "captures": [c.model_dump(mode="json") for c in captures],
                "samples": [s.model_dump(mode="json") for s in samples],
                "acquisition_rejections": acquisition_rejections,
                "candidates": [known.model_dump(mode="json"), unknown.model_dump(mode="json")],
                "instructor_errors": errors,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    # Separate development accuracy assertions, not automatic operational approval.
    for error in errors.values():
        assert error["x_translation_m"] < 0.005, errors
        assert error["x_angle_rad"] < np.deg2rad(0.4), errors
        assert error["y_translation_m"] < 0.005, errors
        assert error["y_angle_rad"] < np.deg2rad(0.4), errors

    # Freeze the unknown-mount candidate before generating its final holdout.
    fingerprint = unknown.fingerprint()
    holdout, rejected, holdout_captures = [], [], []
    for i, pose in enumerate(world.planned_poses("validation")):
        capture = world.acquire(camera_id, pose, f"seed-{seed}-final", i, "validation", limits)
        holdout_captures.append(capture)
        try:
            holdout.append(
                estimate_board(
                    capture, artifacts.read_rgb(capture.rgb), camera, world.board, limits
                )
            )
        except CalibrationError as error:
            # Admission occurs before looking at the candidate or chain/reference residuals.
            # Failed image acquisition is preserved, never filtered by final validation accuracy.
            assert error.code in {
                "INSUFFICIENT_DETECTED_CORNERS",
                "UNRESOLVED_PLANAR_POSE_AMBIGUITY",
                "PNP_POSE_UNDERCONSTRAINED",
            }
            rejected.append(
                MeasurementRejection(
                    capture_id=capture.capture_id,
                    reason=error.code,
                    detail=error.detail,
                    stage="board_pose",
                )
            )
    references = []
    reference_captures = world.reference_captures(camera_id, f"seed-{seed}-references")
    for item in reference_captures:
        rgb = artifacts.read_rgb(item.capture.rgb)
        pixel, mask = reference_center(rgb)
        measurement = reconstruct(
            pixel,
            artifacts.read_depth(item.capture.depth),
            camera,
            unknown.x,
            limits,
            rgb_surface_mask=mask,
        )
        references.append(
            IndependentReference(
                reference_id=item.reference_id,
                dataset_id=item.capture.dataset_id,
                base_point_m=item.base_point_m,
                measurement=measurement,
            )
        )
    report = validate(unknown, holdout, references, limits, "final-validation", rejected)
    assert unknown.fingerprint() == fingerprint
    (tmp_path / "validation.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
    (tmp_path / "reference-captures.json").write_text(
        json.dumps(
            [
                {
                    "capture": item.capture.model_dump(mode="json"),
                    "reference_base_m": item.base_point_m,
                }
                for item in reference_captures
            ],
            indent=2,
        ),
        encoding="utf-8",
    )
    (tmp_path / "holdout-captures.json").write_text(
        json.dumps([capture.model_dump(mode="json") for capture in holdout_captures], indent=2),
        encoding="utf-8",
    )
    assert report.passed, report.failures
    assert report.reference_count == 24
    assert report.reference_p95_mm is not None
