"""Controller-backed acquisition faults preserve raw evidence and support recovery."""

import numpy as np
import pytest

from robotops.calibration.acquisition import AcquisitionReport, CapturePlan
from robotops.calibration.contracts import Capture
from robotops.calibration.errors import CalibrationError
from robotops.calibration.lifecycle import Mutation
from robotops.calibration.reproduction import reproduce
from robotops.calibration.trace import ComputationTrace, result_record_key
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


@pytest.mark.parametrize("scenario", ["repeated", "single_axis", "timestamp_skew", "unsettled"])
def test_bad_capture_plan_keeps_images_report_and_blocks_fitting(tmp_path, scenario):
    runtime = SyntheticRuntime(tmp_path / "runtime.db", Settings.calibration(seed=83))
    engine = Engine(Store(tmp_path / "workflow.db"), runtime)
    service = engine.calibration
    assert service is not None
    camera = "camera-west"
    service.configure(camera, Mutation(request_id="configure", expected_revision=0))
    request = Mutation(request_id="measure", expected_revision=1)
    result = service.acquire(camera, "bad-measurements", request, scenario=scenario)
    assert service.acquire(camera, "bad-measurements", request, scenario=scenario) == result
    assert len(result.record_ids) == 18 and result.state.active_artifact_id is None
    with service.store.store.readonly_connect() as db:
        plan = CapturePlan.model_validate_json(
            db.execute("SELECT body FROM calibration_records WHERE kind='capture-plan'").fetchone()[
                0
            ]
        )
        report = AcquisitionReport.model_validate_json(
            db.execute(
                "SELECT body FROM calibration_records WHERE kind='acquisition-report'"
            ).fetchone()[0]
        )
    assert plan.scenario == scenario and report.capture_count == 18
    with service.store.store.readonly_connect() as db:
        traces = [
            ComputationTrace.model_validate_json(row[0])
            for row in db.execute(
                "SELECT body FROM calibration_records WHERE kind='calculation-trace'"
            )
        ]
    linked = {result_record_key(trace): trace for trace in traces if result_record_key(trace)}
    for identity in result.record_ids:
        captured_call = linked[("capture", identity)]
        assert captured_call.symbol == "ControllerSensor.acquire"
        assert captured_call.path == "robotops/cell/calibration_sensor.py"
        assert captured_call.output["capture_id"] == identity
        if identity in report.accepted_capture_ids:
            assert linked[("sample", identity)].symbol == "estimate_board"
            assert linked[("sample", identity)].trace_id != captured_call.trace_id
        else:
            assert linked[("rejection", identity)].error
    assert not report.ready_to_fit
    if scenario in {"repeated", "single_axis"}:
        assert len(report.accepted_capture_ids) >= 10
        assert "INSUFFICIENT_ROTATION_DIVERSITY" in report.coverage.failures
        if scenario == "single_axis":
            assert min(report.coverage.translation_span_m) > 0.12
        else:
            assert max(report.coverage.translation_span_m) < 0.001
    else:
        assert not report.accepted_capture_ids and len(report.rejections) == 18
    for identity in result.record_ids:
        capture = service.store.record("capture", identity, Capture)
        assert service.artifacts.read_rgb(capture.rgb).shape == (720, 960, 3)
        assert service.artifacts.read_depth(capture.depth).shape == (480, 640)
        if scenario == "timestamp_skew":
            assert "TIMESTAMP_MISMATCH" in capture.rejection_codes
        if scenario == "unsettled":
            assert not capture.settled and capture.moving
    with pytest.raises(CalibrationError, match="INSUFFICIENT_MEASUREMENT"):
        service.fit(
            camera,
            "bad-measurements",
            "must-not-exist",
            Mutation(request_id="bad-fit", expected_revision=2),
        )
    with runtime.db.readonly_connect() as db:
        assert db.execute("SELECT count(*) FROM calibration_captures").fetchone()[0] == 18
    assert service.store.state(camera).candidate_id is None
    exported = service.export(tmp_path / "evidence")
    reproduced = reproduce(exported.parent)
    assert reproduced["passed"], reproduced
    assert reproduced["acquisition_results"] == [
        {
            "report_id": report.report_id,
            "matches_saved": True,
            "accepted_count": len(report.accepted_capture_ids),
            "rejected_count": len(report.rejections),
            "ready_to_fit": False,
        }
    ]
    # Independent recovery uses fresh images and identities, never edits failed data.
    if scenario == "single_axis":
        service.begin_measurements(camera, Mutation(request_id="recover", expected_revision=2))
        service.acquire(
            camera, "varied-measurements", Mutation(request_id="good-measure", expected_revision=3)
        )
        candidate = service.fit(
            camera,
            "varied-measurements",
            "inactive",
            Mutation(request_id="good-fit", expected_revision=4),
        )
        assert (
            candidate.state.workflow_state == "CANDIDATE"
            and candidate.state.active_artifact_id is None
        )
        assert (
            service.store.record("acquisition-report", report.report_id, AcquisitionReport)
            == report
        )
        assert np.isfinite(np.asarray(plan.flange_poses[0].matrix)).all()
