"""Shared physical board changes cannot silently reuse an old mounting/approval."""

import numpy as np
import pytest

from robotops.calibration.contracts import CalibrationArtifact, Capture, Limits, PoseSample
from robotops.calibration.errors import CalibrationError
from robotops.calibration.lifecycle import Mutation
from robotops.calibration.synthetic import instructor_reference
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.workflow.engine import Engine
from robotops.workflow.store import Conflict, Store


def create(tmp_path, seed=83):
    runtime = SyntheticRuntime(tmp_path / "runtime.db", Settings.calibration(seed=seed))
    engine = Engine(Store(tmp_path / "workflow.db"), runtime)
    return runtime, engine, engine.calibration


def mutation(service, camera, identity):
    return Mutation(request_id=identity, expected_revision=service.store.state(camera).revision)


def approve(service, camera, prefix):
    service.acquire(camera, prefix + "-fit", mutation(service, camera, prefix + "-measure"))
    service.fit(
        camera, prefix + "-fit", prefix + "-candidate", mutation(service, camera, prefix + "-fit")
    )
    receipt = service.validate(
        camera,
        prefix + "-candidate",
        prefix + "-unused-final",
        mutation(service, camera, prefix + "-validate"),
    )
    report = service.report(receipt.record_ids[0])
    assert report.passed, report.failures
    service.store.approve(
        camera,
        prefix + "-candidate",
        report.report_id,
        "Simulated board-change test operator",
        mutation(service, camera, prefix + "-approve"),
    )
    return service.store.active(camera)


def test_remount_blocks_both_cameras_and_recovers_new_y_without_moving_physical_x(tmp_path):
    runtime, engine, service = create(tmp_path)
    cameras = ("camera-west", "camera-east")
    previous = {}
    for camera in cameras:
        service.configure(camera, Mutation(request_id="configure", expected_revision=0))
        previous[camera] = approve(service, camera, camera + "-original")
    # The oracle is used only by this test, never supplied to calibration or planning.
    truth_before = {camera: instructor_reference(service.sensor, camera) for camera in cameras}
    request = mutation(service, cameras[0], "board-remount")
    old_other_revision = service.store.state(cameras[1]).revision
    receipt = service.introduce_fault(cameras[0], "board_remount", request)
    generation = runtime.world().cell.generation
    mount_id = service.sensor.board.mounting_id
    for camera in cameras:
        assert service.store.state(camera).active_validity == "SUSPECT_INVALID"
        assert service.store.state(camera).active_artifact_id == previous[camera].artifact_id
        assert (
            service.store.record("artifact", previous[camera].artifact_id, CalibrationArtifact)
            == previous[camera]
        )
        with pytest.raises(CalibrationError, match="SUSPECT"):
            service.store.active(camera)
        with pytest.raises(CalibrationError, match="CURRENT_CANDIDATE_VALIDATION_REQUIRED"):
            service.store.approve(
                camera,
                previous[camera].candidate.candidate_id,
                previous[camera].validation.report_id,
                "Unsafe old approval",
                mutation(service, camera, "unsafe-rollback"),
            )
        physical_x, physical_y = instructor_reference(service.sensor, camera)
        np.testing.assert_array_equal(physical_x, truth_before[camera][0])
        assert np.linalg.norm(physical_y[:3, 3] - truth_before[camera][1][:3, 3]) > 0.006
    assert service.store.state(cameras[1]).revision == old_other_revision + 1
    with pytest.raises(Conflict, match="STALE"):
        service.store.begin_measurements(
            cameras[1],
            Mutation(request_id="concurrent-old-revision", expected_revision=old_other_revision),
        )
    assert service.introduce_fault(cameras[0], "board_remount", request) == receipt
    assert runtime.world().cell.generation == generation
    assert service.sensor.board.mounting_id == mount_id

    # Restart retains the physical mounting, board identity and independent gate states.
    restarted = Engine(Store(tmp_path / "workflow.db"), SyntheticRuntime(tmp_path / "runtime.db"))
    service = restarted.calibration
    assert service.sensor.board.mounting_id == mount_id
    for camera in cameras:
        service.configure(camera, mutation(service, camera, "record-new-board"))
        current = approve(service, camera, camera + "-remounted")
        assert current.candidate.board.mounting_id == mount_id
        assert current.artifact_id != previous[camera].artifact_id
        physical_x, physical_y = instructor_reference(service.sensor, camera)
        np.testing.assert_allclose(
            np.array(current.candidate.x.matrix)[:3, 3], physical_x[:3, 3], atol=0.005, rtol=0
        )
        np.testing.assert_allclose(
            np.array(current.candidate.y.matrix)[:3, 3], physical_y[:3, 3], atol=0.005, rtol=0
        )
        (tmp_path / f"{camera}-remount-artifact.json").write_text(
            current.model_dump_json(indent=2), encoding="utf-8"
        )
    # An old network retry does not reapply a physical remount or invalidate new approval.
    assert service.introduce_fault(cameras[0], "board_remount", request) == receipt
    assert all(
        service.store.active(camera).candidate.board.mounting_id == mount_id for camera in cameras
    )
    service.prepare_tool(cameras[0], mutation(service, cameras[0], "new-tool-check"))
    observation = restarted.measured_observer.fresh()
    assert observation.calibrated_observation
    assert len(observation.calibrated_observation.bindings) == 2


def test_wrong_metric_board_has_real_detected_corners_but_cannot_fit_rigid_chain(tmp_path):
    runtime, engine, service = create(tmp_path, 59)
    camera = "camera-west"
    service.configure(camera, Mutation(request_id="configure", expected_revision=0))
    sensor = service.sensor
    pose = sensor.planned_poses("fit")[0]
    original_board = sensor.board
    rgb, depth = sensor._render(
        sensor.cameras[camera], np.array(pose.matrix), np.random.default_rng(41)
    )
    service.introduce_fault(
        camera, "board_dimensions", mutation(service, camera, "wrong-dimensions")
    )
    assert sensor.board.square_length_m == pytest.approx(original_board.square_length_m * 1.08)
    after_rgb, after_depth = sensor._render(
        sensor.cameras[camera], np.array(pose.matrix), np.random.default_rng(41)
    )
    np.testing.assert_array_equal(after_rgb, rgb)
    np.testing.assert_array_equal(after_depth, depth)
    service.configure(camera, mutation(service, camera, "record-wrong-dimensions"))
    receipt = service.acquire(
        camera, "wrong-metric-board", mutation(service, camera, "measure-wrong")
    )
    samples = []
    for identity in receipt.record_ids:
        try:
            samples.append(service.store.record("sample", identity, PoseSample))
        except LookupError:
            pass
    assert len(samples) >= Limits().min_samples
    assert max(sample.pnp_rms_px for sample in samples) < Limits().max_pnp_rms_px
    with pytest.raises(CalibrationError, match="NO_RELIABLE_TRAINING_CONSENSUS"):
        service.fit(
            camera, "wrong-metric-board", "must-not-fit", mutation(service, camera, "fit-wrong")
        )
    assert service.store.state(camera).active_artifact_id is None
    service.introduce_fault(
        camera, "restore_board_dimensions", mutation(service, camera, "restore-dimensions")
    )
    assert sensor.board == original_board
    old_capture = service.store.record("capture", receipt.record_ids[0], Capture)
    assert old_capture.board_fingerprint != sensor.board.fingerprint()
    with pytest.raises(Conflict, match="CAPTURE_BOARD_CONFIGURATION_CHANGED"):
        sensor.acquire(camera, pose, "wrong-metric-board", 0, "fit", Limits())
    service.configure(camera, mutation(service, camera, "record-correct-dimensions"))
    recovered = approve(service, camera, "restored-metric-board")
    assert recovered.candidate.board == original_board
