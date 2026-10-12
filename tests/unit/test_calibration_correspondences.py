"""Analytical corner faults, separate from fresh-image/browser acceptance datasets."""

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from robotops.calibration.configuration import default_board, default_camera, framed
from robotops.calibration.contracts import ArtifactRef, Capture, Limits
from robotops.calibration.errors import CalibrationError
from robotops.calibration.estimation import estimate_correspondences


def correspondence_fixture(z=0.9, tilt=0.4):
    camera, board = default_camera("analytical-camera"), default_board()
    # Independent pinhole equations, not the implementation's projection helper.
    rotation = Rotation.from_euler("xyz", [tilt, -0.22, 0.13]).as_matrix()
    translation = np.array([-0.1575, -0.1125, z])
    coordinates = np.asarray(board.corners_m) @ rotation.T + translation
    pixels = coordinates[:, :2] / coordinates[:, 2, None] * 950 + [479.5, 359.5]
    capture = Capture(
        capture_id="analytical-corners",
        dataset_id="analytical-only",
        camera_id=camera.camera_id,
        profile_id=camera.profile_id,
        configuration_fingerprint=camera.fingerprint(),
        board_fingerprint=board.fingerprint(),
        rgb=ArtifactRef(path="unused-analytical.png", sha256="0" * 64, media_type="image/png"),
        depth=ArtifactRef(
            path="unused-analytical.npy", sha256="0" * 64, media_type="application/x-npy"
        ),
        rgb_timestamp_s=1,
        depth_timestamp_s=1,
        robot_timestamp_s=1,
        settled=True,
        moving=False,
        t_b_f=framed(np.eye(4), "f", "b"),
        admitted=True,
        partition="fit",
    )
    return camera, board, capture, pixels, rotation, translation


@pytest.mark.parametrize("invalid", ["duplicate", "negative", "unknown"])
def test_invalid_corner_identity_never_enters_pnp(invalid):
    camera, board, capture, pixels, _, _ = correspondence_fixture()
    identities = np.arange(24, dtype=np.int32)
    identities[3] = {"duplicate": 2, "negative": -1, "unknown": 24}[invalid]
    with pytest.raises(CalibrationError, match="WRONG_OR_DUPLICATE_CORNER_IDS"):
        estimate_correspondences(capture, pixels, identities, camera, board, Limits())


def test_gross_corner_outliers_are_excluded_with_ids_and_correct_pose():
    camera, board, capture, pixels, rotation, translation = correspondence_fixture()
    pixels[3] += [25, -30]
    pixels[20] += [-35, 19]
    sample = estimate_correspondences(
        capture, pixels, np.arange(24, dtype=np.int32), camera, board, Limits()
    )
    assert set(sample.excluded_corner_ids) == {3, 20}
    assert set(sample.corner_ids) == set(range(24)) - {3, 20}
    np.testing.assert_allclose(np.asarray(sample.t_c_t.matrix)[:3, :3], rotation, atol=1e-7)
    np.testing.assert_allclose(np.asarray(sample.t_c_t.matrix)[:3, 3], translation, atol=1e-7)
    assert sample.pnp_rms_px < 1e-7


def test_distant_nearly_frontal_measurement_rejects_real_ippe_ambiguity():
    camera, board, capture, _, _, _ = correspondence_fixture()
    # Fixed development fixture: two physically distinct positive-depth IPPE
    # candidates remain within 0.08 px after actual LM. Neither is selected.
    rotation = Rotation.from_euler("x", 0.05).as_matrix()
    coordinates = np.asarray(board.corners_m) @ rotation.T + [-0.1575, -0.1125, 4.0]
    pixels = coordinates[:, :2] / coordinates[:, 2, None] * 950 + [479.5, 359.5]
    pixels += np.random.default_rng(167).normal(0, 0.12, pixels.shape)
    with pytest.raises(CalibrationError, match="UNRESOLVED_PLANAR_POSE_AMBIGUITY") as rejected:
        estimate_correspondences(
            capture, pixels, np.arange(24, dtype=np.int32), camera, board, Limits()
        )
    assert "Candidate point RMS" in rejected.value.detail


def test_swapped_correspondences_cannot_be_silently_treated_as_the_same_ids():
    camera, board, capture, pixels, rotation, translation = correspondence_fixture()
    identities = np.arange(24, dtype=np.int32)
    identities[2], identities[16] = identities[16], identities[2]
    sample = estimate_correspondences(capture, pixels, identities, camera, board, Limits())
    assert set(sample.excluded_corner_ids) == {2, 16}
    np.testing.assert_allclose(np.asarray(sample.t_c_t.matrix)[:3, :3], rotation, atol=1e-7)
    np.testing.assert_allclose(np.asarray(sample.t_c_t.matrix)[:3, 3], translation, atol=1e-7)
