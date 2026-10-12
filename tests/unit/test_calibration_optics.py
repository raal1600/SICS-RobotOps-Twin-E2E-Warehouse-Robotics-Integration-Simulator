import numpy as np
import pytest

from robotops.calibration.artifacts import SensorArtifacts
from robotops.calibration.configuration import default_camera
from robotops.calibration.contracts import Board, Limits
from robotops.calibration.errors import CalibrationError
from robotops.calibration.geometry import project, undistort
from robotops.calibration.lifecycle import CalibrationStore, Mutation
from robotops.calibration.optics import OpticalReference, OpticsLimits, verify_camera_model
from robotops.calibration.service import CalibrationService
from robotops.calibration.synthetic import SyntheticSensorWorld
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


def golden_references(camera):
    # Independent analytical pinhole equations. No project/deproject helper computes expectations.
    values = []
    for name, stream, frame in (("rgb", camera.rgb, "c"), ("depth", camera.depth, "d")):
        points = [
            (x, y, 1.0) for y in np.linspace(-0.32, 0.32, 5) for x in np.linspace(-0.44, 0.44, 7)
        ]
        pixels = [
            (stream.k[0][0] * x + stream.k[0][2], stream.k[1][1] * y + stream.k[1][2])
            for x, y, _ in points
        ]
        values.append(
            OpticalReference(
                measurement_id=f"independent-{name}",
                camera_id=camera.camera_id,
                profile_id=camera.profile_id,
                stream=name,
                optical_frame=frame,
                width=stream.width,
                height=stream.height,
                optical_points_m=tuple(points),
                measured_pixels_px=tuple(pixels),
            )
        )
    return tuple(values)


@pytest.mark.parametrize(
    "change", ["nominal", "focal", "crop", "resize", "profile", "model", "threshold"]
)
def test_optics_check_is_profile_specific_and_not_an_extrinsic_calibration(change):
    camera = default_camera("camera-west")
    references = golden_references(camera)
    limits = OpticsLimits()
    if change == "focal":
        k = np.array(camera.rgb.k)
        k[0, 0] *= 1.08
        camera = camera.model_copy(
            update={"rgb": camera.rgb.model_copy(update={"k": tuple(map(tuple, k))})}
        )
    elif change == "crop":
        camera = camera.model_copy(
            update={"rgb": camera.rgb.model_copy(update={"crop_xy": (32, 32)})}
        )
    elif change == "resize":
        camera = camera.model_copy(
            update={"depth": camera.depth.model_copy(update={"resize_xy": (0.5, 0.5)})}
        )
    elif change == "profile":
        camera = camera.model_copy(update={"profile_id": "unsupported-new-profile"})
    elif change == "model":
        camera = camera.model_copy(
            update={
                "rgb": camera.rgb.model_copy(
                    update={"distortion_model": "fisheye", "coefficients": (0, 0, 0, 0)}
                )
            }
        )
    elif change == "threshold":
        limits = limits.model_copy(update={"max_rms_px": None})
    result = verify_camera_model(camera, references, limits, "check")
    assert result.passed == (change == "nominal"), result
    if change == "nominal":
        assert all(row.rms_px < 1e-10 for row in result.streams)
    else:
        assert result.failures
    assert "x" not in result.model_dump() and "y" not in result.model_dump()


def test_both_streams_and_spatial_coverage_are_required():
    camera = default_camera("camera-west")
    references = golden_references(camera)
    missing = verify_camera_model(camera, references[:1], OpticsLimits(), "missing")
    assert not missing.passed and "BOTH_OPTICAL_STREAM_REFERENCES_REQUIRED" in missing.failures
    repeated = references[0].model_copy(
        update={
            "optical_points_m": ((0, 0, 1.0),) * 40,
            "measured_pixels_px": ((camera.rgb.k[0][2], camera.rgb.k[1][2]),) * 40,
        }
    )
    assert not verify_camera_model(
        camera, (repeated, references[1]), OpticsLimits(), "repeated"
    ).passed


def test_fisheye_projection_and_undistortion_have_independent_off_axis_golden_values():
    k = np.array([[400, 0, 320], [0, 400, 240], [0, 0, 1]])
    # Zero-coefficient fisheye maps radius r to atan(r), not r as pinhole does.
    theta = np.arctan(0.5)
    expected = np.array([[320 + 400 * theta, 240], [320, 240 + 400 * theta]])
    pixels = project(np.array([[0.5, 0, 1], [0, 1, 2]]), k, np.array([0, 0, 0, 0]), "fisheye")
    assert np.allclose(pixels, expected, atol=1e-10)
    assert np.allclose(
        undistort(expected, k, np.array([0, 0, 0, 0]), "fisheye"), [[0.5, 0], [0, 0.5]], atol=1e-10
    )


def test_synthetic_factory_reference_is_separate_from_declared_model_and_installation(tmp_path):
    sensor = SyntheticSensorWorld(61, SensorArtifacts(tmp_path / "images"))
    camera = sensor.cameras["camera-west"]
    original = sensor.optical_references(camera.camera_id)
    sensor._physical_cameras[camera.camera_id][:3, 3] += [0.5, 0.1, -0.2]
    assert (
        sensor.optical_references(camera.camera_id) == original
    )  # Installation X is not an optics input.
    k = np.array(camera.rgb.k)
    k[0, 0] *= 0.9
    sensor.cameras[camera.camera_id] = camera.model_copy(
        update={"rgb": camera.rgb.model_copy(update={"k": tuple(map(tuple, k))})}
    )
    assert sensor.optical_references(camera.camera_id) == original
    assert not verify_camera_model(
        sensor.cameras[camera.camera_id], original, OpticsLimits(), "wrong"
    ).passed


def test_bad_model_and_missing_verification_block_fitting_at_backend(tmp_path):
    service = CalibrationService(Store(tmp_path / "workflow.db"), seed=61)
    camera = service.sensor.cameras["camera-west"]
    service.sensor.cameras[camera.camera_id] = camera.model_copy(
        update={"rgb": camera.rgb.model_copy(update={"crop_xy": (20, 20)})}
    )
    configured = service.configure(
        camera.camera_id, Mutation(request_id="configure", expected_revision=0)
    )
    assert configured.state.camera_model_report_id
    with pytest.raises(CalibrationError, match="CAMERA_MODEL_NOT_VERIFIED"):
        service.fit(
            camera.camera_id, "anything", "blocked", Mutation(request_id="fit", expected_revision=1)
        )
    old = CalibrationStore(Store(tmp_path / "historical.db"))
    state = old.configure(
        camera,
        service.sensor.board,
        configured.state.limits,
        Mutation(request_id="older", expected_revision=0),
    ).state
    with pytest.raises(CalibrationError, match="CAMERA_MODEL_VERIFICATION_REQUIRED"):
        old.require_camera_model(state)


@pytest.mark.parametrize(
    "change", ["intrinsics", "board_dimensions", "depth_scale", "registration"]
)
def test_wrong_reported_configuration_never_changes_physical_sensor_images(tmp_path, change):
    sensor = SyntheticSensorWorld(67, SensorArtifacts(tmp_path / "images"))
    camera_id = "camera-west"
    pose = sensor.planned_poses("fit")[0]
    first = sensor.acquire(camera_id, pose, "fixed-input", 0, "fit", Limits())
    camera = sensor.cameras[camera_id]
    if change == "intrinsics":
        k = np.array(camera.rgb.k)
        k[0, 0] *= 1.1
        sensor.cameras[camera_id] = camera.model_copy(
            update={"rgb": camera.rgb.model_copy(update={"k": tuple(map(tuple, k))})}
        )
    elif change == "depth_scale":
        sensor.cameras[camera_id] = camera.model_copy(update={"depth_scale_m": 0.0012})
    elif change == "registration":
        from robotops.calibration.configuration import framed

        wrong = np.eye(4)
        wrong[0, 3] = -0.1
        sensor.cameras[camera_id] = camera.model_copy(update={"t_c_d": framed(wrong, "d", "c")})
    else:
        sensor.board = Board.model_validate(
            {
                **sensor.board.model_dump(),
                "square_length_m": sensor.board.square_length_m * 1.1,
                "marker_length_m": sensor.board.marker_length_m * 1.1,
                "measured_dimensions_m": tuple(
                    value * 1.1 for value in sensor.board.measured_dimensions_m
                ),
                "corners_m": (np.array(sensor.board.corners_m) * 1.1).tolist(),
            }
        )
    second = sensor.acquire(camera_id, pose, "fixed-input", 0, "fit", Limits())
    assert second.rgb == first.rgb and second.depth == first.depth
    assert (
        second.configuration_fingerprint != first.configuration_fingerprint
        or second.board_fingerprint != first.board_fingerprint
    )


@pytest.mark.parametrize(
    "kind", ["model_focal", "model_profile", "model_crop", "model_resize", "model_distortion"]
)
def test_durable_model_fault_has_failed_optics_gate_and_explicit_restoration(tmp_path, kind):
    engine = Engine(
        Store(tmp_path / "workflow.db"),
        SyntheticRuntime(tmp_path / "runtime.db", Settings.calibration(seed=73)),
    )
    service = engine.calibration
    camera_id = "camera-west"
    first = service.configure(camera_id, Mutation(request_id="initial", expected_revision=0))
    service.introduce_fault(
        camera_id, kind, Mutation(request_id="wrong-model", expected_revision=1)
    )
    changed = service.configure(camera_id, Mutation(request_id="record-wrong", expected_revision=2))
    assert changed.state.camera.fingerprint() != first.state.camera.fingerprint()
    with pytest.raises(CalibrationError, match="CAMERA_MODEL_NOT_VERIFIED"):
        service.store.require_camera_model(changed.state)
    restarted = Engine(
        Store(tmp_path / "workflow.db"), SyntheticRuntime(tmp_path / "runtime.db")
    ).calibration
    assert restarted.sensor.cameras[camera_id] == changed.state.camera
    restarted.introduce_fault(
        camera_id, "restore_model", Mutation(request_id="restore", expected_revision=3)
    )
    restored = restarted.configure(
        camera_id, Mutation(request_id="record-restored", expected_revision=4)
    )
    assert restarted.store.require_camera_model(restored.state).passed
    assert restored.state.active_validity != "VERIFIED"
    assert restored.state.active_artifact_id is None
