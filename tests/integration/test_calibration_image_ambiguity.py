"""Real synthetic RGB can contain two unresolved positive-depth planar solutions."""

import json

from robotops.calibration.acquisition import AcquisitionReport
from robotops.calibration.contracts import Capture
from robotops.calibration.errors import CalibrationError
from robotops.calibration.estimation import estimate_board
from robotops.calibration.lifecycle import Mutation
from robotops.calibration.reproduction import reproduce
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


def test_actual_near_frontal_rgb_rejects_ambiguity_and_preserves_competing_scores(tmp_path):
    engine = Engine(
        Store(tmp_path / "workflow.db"),
        SyntheticRuntime(tmp_path / "runtime.db", Settings.calibration(seed=173)),
    )
    service = engine.calibration
    camera = "camera-west"
    service.configure(camera, Mutation(request_id="configure", expected_revision=0))
    acquired = service.acquire(
        camera,
        "weak-planar",
        Mutation(request_id="capture", expected_revision=1),
        scenario="near_frontal",
    )
    with service.store.store.readonly_connect() as db:
        report = AcquisitionReport.model_validate_json(
            db.execute(
                "SELECT body FROM calibration_records WHERE kind='acquisition-report'"
            ).fetchone()[0]
        )
    ambiguous = [
        item for item in report.rejections if item.reason == "UNRESOLVED_PLANAR_POSE_AMBIGUITY"
    ]
    assert ambiguous, report
    assert not report.ready_to_fit and acquired.state.active_artifact_id is None
    state = service.store.state(camera)
    for rejected in ambiguous:
        capture = service.store.record("capture", rejected.capture_id, Capture)
        assert capture.admitted  # Settled/aligned acquisition; the image pose itself is unresolved.
        assert "Candidate point RMS:" in rejected.detail
        assert rejected.calculation is not None
        candidates = rejected.calculation.outputs["positive_depth_candidates"]
        assert len(candidates) == 2
        assert all(
            item["t_c_t"]["source"] == "t" and item["t_c_t"]["destination"] == "c"
            for item in candidates
        )
        assert 0 <= rejected.calculation.outputs["rms_gap_px"] < state.limits.ambiguity_gap_px
        try:
            estimate_board(
                capture,
                service.artifacts.read_rgb(capture.rgb),
                state.camera,
                state.board,
                state.limits,
            )
        except CalibrationError as error:
            assert error.code == rejected.reason and error.detail == rejected.detail
            assert error.calculation == rejected.calculation.model_dump(mode="json")
        else:
            raise AssertionError("Saved ambiguous RGB unexpectedly yielded an accepted pose")
    exported = service.export(tmp_path / "ambiguous-evidence")
    reproduced = reproduce(exported.parent)
    assert reproduced["passed"], reproduced
    (tmp_path / "ambiguity-summary.json").write_text(
        json.dumps(
            {
                "rejections": [row.model_dump(mode="json") for row in ambiguous],
                "reproduced": reproduced,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
