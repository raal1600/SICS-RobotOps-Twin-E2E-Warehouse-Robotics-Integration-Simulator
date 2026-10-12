"""Independent analytical fixtures for frame semantics and Park-Martin mapping."""

from pathlib import Path

import cv2
import numpy as np
import pytest
from pydantic import ValidationError
from scipy.spatial.transform import Rotation

from robotops.calibration.artifacts import SensorArtifacts
from robotops.calibration.configuration import default_board, default_camera, framed
from robotops.calibration.contracts import ArtifactRef, Limits, PoseSample, Stream, Transform
from robotops.calibration.errors import CalibrationError
from robotops.calibration.estimation import fit
from robotops.calibration.geometry import from_xyzw, inverse, point_rms, points, rigid, rigid_mean


def analytical_samples():
    """Construct B independently with numpy.linalg.inv, not calibration geometry helpers."""
    camera, board = default_camera("fixture-camera"), default_board()
    x = np.eye(4)
    x[:3, :3] = Rotation.from_euler("xyz", [0.2, -0.13, 0.31]).as_matrix()
    x[:3, 3] = [-0.2, 0.14, -1.4]
    y = np.eye(4)
    y[:3, :3] = Rotation.from_euler("xyz", [-0.13, 0.24, -0.09]).as_matrix()
    y[:3, 3] = [0.017, -0.027, 0.13]
    rng = np.random.default_rng(829)
    result = []
    for i in range(30):
        a = np.eye(4)
        a[:3, :3] = Rotation.from_euler("xyz", rng.uniform(-0.5, 0.5, 3)).as_matrix()
        a[:3, 3] = rng.uniform([-0.3, -0.3, 0.3], [0.3, 0.3, 0.8])
        b = np.linalg.inv(x) @ a @ y
        rvec, _ = cv2.Rodrigues(b[:3, :3])
        pixels, _ = cv2.projectPoints(
            np.array(board.corners_m), rvec, b[:3, 3], np.array(camera.rgb.k), None
        )
        result.append(
            PoseSample(
                capture_id=f"sample-{i}",
                dataset_id="analytical-fit",
                camera_id=camera.camera_id,
                configuration_fingerprint=camera.fingerprint(),
                board_fingerprint=board.fingerprint(),
                t_b_f=framed(a, "f", "b"),
                t_c_t=framed(b, "t", "c"),
                corner_ids=board.corner_ids,
                object_points_m=board.corners_m,
                image_points_px=tuple(map(tuple, pixels.reshape(-1, 2))),
                residuals_px=((0, 0),) * 24,
                pnp_rms_px=0,
                candidate_rms_px=(0,),
                partition="fit",
            )
        )
    return camera, board, result, x, y


def test_transform_direction_with_explicit_golden_coordinates():
    matrix = np.array([[0, -1, 0, 2], [1, 0, 0, 3], [0, 0, 1, 4], [0, 0, 0, 1.0]])
    assert points(matrix, np.array([[2, 5, 7]])).tolist() == [[-3, 5, 11]]
    assert inverse(matrix).tolist() == [[0, 1, 0, -3], [-1, 0, 0, 2], [0, 0, 1, -4], [0, 0, 0, 1]]
    assert np.allclose(from_xyzw([2, 3, 4], [0, 0, 2**-0.5, 2**-0.5]), matrix)
    with pytest.raises(CalibrationError, match="INVALID_XYZW"):
        from_xyzw([0, 0, 0], [0, 0, 0, 2])


@pytest.mark.parametrize("case", ["nan", "scale", "reflection", "last-row"])
def test_invalid_rigid_transform(case):
    matrix = np.eye(4)
    if case == "nan":
        matrix[0, 3] = np.nan
    elif case == "scale":
        matrix[1, 1] = 2
    elif case == "reflection":
        matrix[1, 1] = -1
    else:
        matrix[3, 0] = 1
    with pytest.raises(CalibrationError):
        rigid(matrix)


def test_rigid_mean_is_not_elementwise_matrix_average():
    a, b = np.eye(4), np.eye(4)
    b[:3, :3] = Rotation.from_euler("z", 120, degrees=True).as_matrix()
    b[0, 3] = 2
    value = rigid_mean([a, b])
    expected = np.array([[0.5, -(3**0.5) / 2, 0], [3**0.5 / 2, 0.5, 0], [0, 0, 1]])
    assert np.allclose(value[:3, :3], expected)
    assert value[:3, 3].tolist() == [1, 0, 0]
    assert np.isclose(np.linalg.det(value[:3, :3]), 1)


def test_rms_counts_points_not_scalar_coordinates():
    assert point_rms(np.array([[3, 4], [0, 5]])) == 5


@pytest.mark.parametrize("known", [True, False])
def test_known_x_y_and_opencv_direction_mapping(known):
    camera, board, samples, x, y = analytical_samples()
    candidate = fit(
        samples, camera, board, Limits(), "golden", framed(y, "t", "f") if known else None
    )
    assert np.allclose(candidate.x.matrix, x, atol=1e-10)
    assert np.allclose(candidate.y.matrix, y, atol=1e-10)
    assert not np.allclose(candidate.x.matrix, np.linalg.inv(x))
    assert candidate.active is False
    assert candidate.status == "CANDIDATE"
    # Check the actual hand-eye relative-motion equation with an independently computed inverse.
    ai, aj = [np.array(s.t_b_f.matrix) for s in samples[:2]]
    bi, bj = [np.array(s.t_c_t.matrix) for s in samples[:2]]
    estimated_y = np.array(candidate.y.matrix)
    assert np.allclose(
        np.linalg.inv(aj) @ ai @ estimated_y, estimated_y @ np.linalg.inv(bj) @ bi, atol=1e-10
    )


@pytest.mark.parametrize("known", [True, False])
def test_training_consensus_excludes_bad_robot_reports_without_using_holdout(known):
    camera, board, samples, x, y = analytical_samples()
    bad_indices = (0, 9, 17)
    for index in bad_indices:
        wrong = np.array(samples[index].t_b_f.matrix)
        wrong[:3, 3] += [0.05, -0.03, 0.04]
        samples[index] = samples[index].model_copy(update={"t_b_f": framed(wrong, "f", "b")})
    fitted = fit(samples, camera, board, Limits(), "robust", framed(y, "t", "f") if known else None)
    assert np.allclose(fitted.x.matrix, x, atol=1e-10)
    assert np.allclose(fitted.y.matrix, y, atol=1e-10)
    assert fitted.excluded_sample_ids == tuple(f"sample-{i}" for i in bad_indices)
    assert len(fitted.sample_ids) == 27 and fitted.coverage.sample_count == 27
    assert fitted.fit_diagnostics.policy.scope == "SIMULATION_ONLY"
    excluded = [row for row in fitted.fit_diagnostics.residuals if not row.included]
    assert all(row.translation_mm > 50 for row in excluded)
    assert (
        fit(samples, camera, board, Limits(), "robust", framed(y, "t", "f") if known else None)
        == fitted
    )


def test_conflicting_training_populations_do_not_create_a_candidate():
    camera, board, samples, _, _ = analytical_samples()
    for index in range(15):
        wrong = np.array(samples[index].t_b_f.matrix)
        wrong[0, 3] += 0.09
        samples[index] = samples[index].model_copy(update={"t_b_f": framed(wrong, "f", "b")})
    with pytest.raises(CalibrationError, match="NO_RELIABLE_TRAINING_CONSENSUS"):
        fit(samples, camera, board, Limits(), "unresolved")


def test_repeated_poses_are_not_evidence_and_holdout_is_not_training():
    camera, board, samples, _, _ = analytical_samples()
    repeated = [samples[0].model_copy(update={"capture_id": f"repeat-{i}"}) for i in range(30)]
    with pytest.raises(CalibrationError, match="INSUFFICIENT.*DIVERSITY"):
        fit(repeated, camera, board, Limits(), "repeated")
    with pytest.raises(CalibrationError, match="HOLDOUT_CANNOT_FIT"):
        fit(
            [s.model_copy(update={"partition": "validation"}) for s in samples],
            camera,
            board,
            Limits(),
            "leaked",
        )
    with pytest.raises(CalibrationError, match="DUPLICATE_FIT_SAMPLE"):
        fit(samples + [samples[0]], camera, board, Limits(), "duplicated")


def test_strict_camera_model_and_configuration_fingerprints():
    camera = default_camera("camera")
    changed = camera.model_copy(update={"profile_id": "changed"})
    assert changed.fingerprint() != camera.fingerprint()
    with pytest.raises(ValidationError, match="DISTORTION_MODEL_MISMATCH"):
        Stream.model_validate({**camera.rgb.model_dump(), "distortion_model": "fisheye"})
    with pytest.raises(ValidationError):
        Transform.model_validate({**camera.t_c_d.model_dump(), "translation_unit": "mm"})


def test_artifact_hashes_no_pickle_or_arbitrary_paths(tmp_path: Path):
    artifacts = SensorArtifacts(tmp_path)
    image = np.full((10, 20, 3), 87, dtype=np.uint8)
    reference = artifacts.rgb(image)
    assert artifacts.rgb(image) == reference
    assert np.array_equal(artifacts.read_rgb(reference), image)
    raw = np.array([[0, np.nan], [12, np.inf]], dtype=np.float32)
    depth = artifacts.depth(raw)
    assert np.array_equal(artifacts.read_depth(depth), raw, equal_nan=True)
    with pytest.raises(ValidationError, match="UNSAFE_ARTIFACT_PATH"):
        ArtifactRef(path="../escape.png", sha256="0" * 64, media_type="image/png")
    (tmp_path / reference.path).write_bytes(b"tampered")
    with pytest.raises(CalibrationError, match="ARTIFACT_HASH_MISMATCH"):
        artifacts.read(reference)
