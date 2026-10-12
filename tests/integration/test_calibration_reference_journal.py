"""Reference acquisition is real, durable and distinct from coordinate estimation."""

from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest

from robotops.calibration.artifacts import SensorArtifacts
from robotops.calibration.contracts import ReferenceBatch, SurfaceDetection
from robotops.calibration.faults import FaultRecord, definition
from robotops.calibration.lifecycle import Mutation
from robotops.calibration.reproduction import reproduce
from robotops.calibration.trace import ComputationTrace, result_record_keys
from robotops.cell.calibration_sensor import ControllerSensor
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.workflow.engine import Engine
from robotops.workflow.store import Conflict, Store


def request(service, identity):
    return Mutation(
        request_id=identity, expected_revision=service.store.state("camera-west").revision
    )


def test_reference_batch_is_atomic_idempotent_and_preserved_after_restart_and_camera_movement(
    tmp_path,
):
    runtime = SyntheticRuntime(tmp_path / "runtime.db", Settings.calibration(seed=197))
    files = SensorArtifacts(tmp_path / "images")
    sensor = ControllerSensor(runtime, files)
    before = runtime.world()
    with ThreadPoolExecutor(max_workers=3) as pool:
        batches = list(
            pool.map(
                lambda _: sensor.reference_batch("camera-west", "survey", "validation"), range(3)
            )
        )
    assert batches[0] == batches[1] == batches[2]
    assert runtime.world() == before
    batch = batches[0]
    assert len(batch.captures) == 24
    assert len({item.capture.capture_id for item in batch.captures}) == 24
    # Independent analytical survey endpoints, not calculated with a candidate X.
    assert batch.captures[0].base_point_m == (-0.18, -0.12, 0.3)
    assert batch.captures[-1].base_point_m == (0.18, 0.12, 0.75)
    restored = ControllerSensor(SyntheticRuntime(tmp_path / "runtime.db"), files)
    assert restored.reference_batch("camera-west", "survey", "validation") == batch
    restored.move_camera("camera-west", "later-movement", (0.03, 0, 0), (0, 0, 0))
    assert restored.reference_batch("camera-west", "survey", "validation") == batch
    fresh = restored.reference_batch("camera-west", "new-survey", "routine")
    assert fresh.captures[0].capture.rgb != batch.captures[0].capture.rgb
    assert fresh.captures[0].capture.rgb_timestamp_s > batch.captures[0].capture.rgb_timestamp_s
    with pytest.raises(Conflict, match="REFERENCE_CAPTURE_IDEMPOTENCY_CONFLICT"):
        restored.reference_batch("camera-west", "survey", "routine")
    with runtime.db.readonly_connect() as db:
        assert db.execute("SELECT COUNT(*) FROM calibration_reference_batches").fetchone()[0] == 2
    restored.apply_fault(
        FaultRecord(
            fault_id="changed-model", camera_id="camera-west", definition=definition("model_focal")
        )
    )
    with pytest.raises(Conflict, match="REFERENCE_CAPTURE_IDEMPOTENCY_CONFLICT"):
        restored.reference_batch("camera-west", "survey", "validation")


def test_interrupted_validation_reuses_saved_measurements_and_exports_real_detection_and_depth_calls(
    tmp_path, monkeypatch
):
    runtime = SyntheticRuntime(tmp_path / "runtime.db", Settings.calibration(seed=83))
    engine = Engine(Store(tmp_path / "workflow.db"), runtime)
    service = engine.calibration
    camera = "camera-west"
    service.configure(camera, Mutation(request_id="configure", expected_revision=0))
    service.acquire(camera, "fit", request(service, "acquire"))
    service.fit(camera, "fit", "candidate", request(service, "fit"))
    validate_request = request(service, "validate")

    def interrupted(*args, **kwargs):
        raise ConnectionError("Isolated test failure before final report commit")

    with monkeypatch.context() as patch:
        patch.setattr(service.store, "save_validation", interrupted)
        with pytest.raises(ConnectionError, match="before final report commit"):
            service.validate(camera, "candidate", "unused-final", validate_request)
    with service.store.store.readonly_connect() as db:
        batch = ReferenceBatch.model_validate_json(
            db.execute(
                "SELECT body FROM calibration_records WHERE kind='reference-batch'"
            ).fetchone()[0]
        )
    assert service.store.state(camera).active_artifact_id is None
    assert service.store.state(camera).workflow_state == "INDEPENDENT_VALIDATION"
    restarted = Engine(Store(tmp_path / "workflow.db"), SyntheticRuntime(tmp_path / "runtime.db"))
    service = restarted.calibration
    result = service.validate(camera, "candidate", "unused-final", validate_request)
    assert service.report(result.record_ids[0]).passed
    assert service.store.record("reference-batch", batch.batch_id, ReferenceBatch) == batch
    assert service.validate(camera, "candidate", "unused-final", validate_request) == result
    with service.store.store.readonly_connect() as db:
        traces = [
            ComputationTrace.model_validate_json(row[0])
            for row in db.execute(
                "SELECT body FROM calibration_records WHERE kind='calculation-trace'"
            )
        ]
    indexed = {key: trace for trace in traces for key in result_record_keys(trace)}
    for item in batch.captures:
        identity = item.capture.capture_id
        assert indexed[("capture", identity)].symbol == "ControllerSensor.reference_batch"
        assert indexed[("surface-detection", identity)].symbol == "identify_surface"
        depth = indexed[("reference", identity)]
        assert depth.symbol == "reconstruct"
        assert depth.source["loaded_function_verification"] == "MATCHED_PYTHON_CODE"
        assert depth.inputs["independent_surveyed_base_point_m"] == list(item.base_point_m)
        assert depth.output["point"] != list(
            item.base_point_m
        )  # No copy of the survey into measured output.
        detection = service.store.record("surface-detection", identity, SurfaceDetection)
        mask = service.artifacts.read_mask(detection.mask)
        assert mask.dtype == np.bool_ and mask.shape == (720, 960)
        assert int(mask.sum()) == detection.selected_pixel_count
    service.store.approve(
        camera,
        "candidate",
        result.record_ids[0],
        "Simulated reference-journal operator",
        request(service, "approve"),
    )
    checked = service.routine_check(camera, request(service, "routine"))
    assert checked.state.active_validity == "VERIFIED"
    service.introduce_fault(camera, "depth_zero", request(service, "missing"))
    rejected = service.routine_check(camera, request(service, "failed-routine"))
    assert rejected.state.active_validity == "SUSPECT_INVALID"
    manifest = service.export(tmp_path / "bundle")
    reproduced = reproduce(manifest.parent)
    assert reproduced["passed"], reproduced
    assert len(reproduced["reference_calculation_results"]) >= 48
    assert len(reproduced["routine_check_results"]) == 2
    failed_check = next(
        item
        for item in reproduced["routine_check_results"]
        if item["check_id"] == "check-failed-routine"
    )
    assert failed_check["rejections_rechecked"] == 24
    assert all(item["matches_saved"] for item in reproduced["surface_detection_results"])
