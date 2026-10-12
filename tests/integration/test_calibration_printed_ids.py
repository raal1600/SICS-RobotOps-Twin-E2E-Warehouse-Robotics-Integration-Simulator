"""Wrong printed IDs are real image content, not injected detector answers."""

import cv2
import numpy as np
import pytest

from robotops.calibration.acquisition import AcquisitionReport
from robotops.calibration.contracts import Capture, MeasurementRejection
from robotops.calibration.errors import CalibrationError
from robotops.calibration.lifecycle import Mutation
from robotops.calibration.reproduction import reproduce
from robotops.calibration.synthetic import instructor_reference
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


def test_wrong_printed_ids_change_images_and_saved_scene_then_require_new_measurements(tmp_path):
    runtime = SyntheticRuntime(tmp_path / "runtime.db", Settings.calibration(seed=83))
    service = Engine(Store(tmp_path / "workflow.db"), runtime).calibration
    camera = "camera-west"

    def request(identity):
        return Mutation(request_id=identity, expected_revision=service.store.state(camera).revision)

    for identity in (camera, "camera-east"):
        service.configure(identity, Mutation(request_id="configure", expected_revision=0))
    board = service.sensor.board
    original_x, original_y = instructor_reference(service.sensor, camera)
    fault = service.introduce_fault(camera, "board_marker_ids", request("bad-print"))
    assert service.sensor.board == board
    for state in service.store.states():
        assert state.active_validity == "SUSPECT_INVALID"
    actual_x, actual_y = instructor_reference(service.sensor, camera)
    np.testing.assert_array_equal(actual_x, original_x)
    np.testing.assert_array_equal(actual_y, original_y)
    acquired = service.acquire(camera, "wrong-ids", request("capture-wrong"))
    assert len(acquired.record_ids) == 18
    with service.store.store.readonly_connect() as db:
        report = AcquisitionReport.model_validate_json(
            db.execute(
                "SELECT body FROM calibration_records WHERE kind='acquisition-report'"
            ).fetchone()[0]
        )
    assert not report.ready_to_fit and not report.accepted_capture_ids
    capture_id = "wrong-ids-camera-west-000"
    capture = service.store.record("capture", capture_id, Capture)
    image = service.artifacts.read_rgb(capture.rgb)
    detected_ids = cv2.aruco.ArucoDetector(
        cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
    ).detectMarkers(image)[1]
    assert detected_ids is not None and len(detected_ids) >= 5
    assert set(detected_ids.ravel()).issubset(set(range(17, 34)))
    rejection = service.store.record("rejection", capture_id, MeasurementRejection)
    assert rejection.reason == "MARKER_IDS_DO_NOT_MATCH_BOARD"
    assert "Unexpected detected marker IDs" in rejection.detail
    assert fault.record_ids[0] in capture.sensor_fault_ids
    saved = service.sensor.capture_presentation(capture_id)
    ids = {
        int(obj.name.split("-")[1])
        for obj in saved.scene.objects
        if obj.name.startswith("Board/marker-")
    }
    assert ids == set(range(17, 34))
    with pytest.raises(CalibrationError, match="INSUFFICIENT_MEASUREMENT"):
        service.fit(camera, "wrong-ids", "invalid", request("fit-wrong"))
    service.introduce_fault(camera, "restore_board_print", request("restore-print"))
    assert service.sensor.capture_presentation(capture_id) == saved
    assert service.store.state(camera).active_validity == "SUSPECT_INVALID"
    service.begin_measurements(camera, request("new-measurements"))
    service.acquire(camera, "restored-ids", request("capture-restored"))
    service.fit(camera, "restored-ids", "new-candidate", request("fit-restored"))
    checked = service.validate(
        camera, "new-candidate", "unused-print-final", request("validate-restored")
    )
    assert service.report(checked.record_ids[0]).passed
    service.store.approve(
        camera,
        "new-candidate",
        checked.record_ids[0],
        "Simulated print-check operator",
        request("new-approval"),
    )
    assert service.store.active(camera).candidate.board == board
    service.export(tmp_path / "export")
    result = reproduce(tmp_path / "export")
    assert result["passed"], result
