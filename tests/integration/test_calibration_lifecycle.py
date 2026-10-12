import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from robotops.calibration.configuration import default_board, default_camera
from robotops.calibration.contracts import Limits
from robotops.calibration.errors import CalibrationError
from robotops.calibration.lifecycle import CalibrationStore, Mutation
from robotops.calibration.service import CalibrationService
from robotops.workflow.store import Conflict, Store


def test_real_images_to_durable_separate_approval_and_invalidation(tmp_path):
    store = Store(tmp_path / "workflow.db")
    service = CalibrationService(store, seed=29)
    camera_id = "camera-west"
    configured = service.configure(camera_id, Mutation(request_id="configure", expected_revision=0))
    assert configured.state.active_artifact_id is None
    with pytest.raises(CalibrationError, match="APPROVED_CALIBRATION_REQUIRED"):
        service.store.active(camera_id)
    acquisition = Mutation(request_id="capture", expected_revision=1)
    measured = service.acquire(camera_id, "fit-measurements", acquisition)
    assert service.acquire(camera_id, "fit-measurements", acquisition) == measured
    with pytest.raises(Conflict, match="IDEMPOTENCY"):
        service.acquire(camera_id, "different-measurements", acquisition)
    fitted = service.fit(
        camera_id,
        "fit-measurements",
        "candidate-one",
        Mutation(request_id="fit", expected_revision=2),
    )
    assert fitted.state.workflow_state == "CANDIDATE"
    assert fitted.state.active_validity == "UNVERIFIED"
    with pytest.raises(CalibrationError, match="APPROVED_CALIBRATION_REQUIRED"):
        service.store.active(camera_id)
    validation_request = Mutation(request_id="validate", expected_revision=3)
    evaluated = service.validate(camera_id, "candidate-one", "unused-final", validation_request)
    report = service.report(evaluated.record_ids[0])
    assert report.passed, report.failures
    assert (
        service.validate(camera_id, "candidate-one", "unused-final", validation_request)
        == evaluated
    )
    assert evaluated.state.active_artifact_id is None
    assert evaluated.state.revision == 5
    approval_request = Mutation(request_id="approve", expected_revision=5)
    approved = service.store.approve(
        camera_id, "candidate-one", report.report_id, "Simulated test operator", approval_request
    )
    assert approved.state.active_validity == "VERIFIED"
    artifact = service.store.active(camera_id)
    assert artifact.approval.scope == "SIMULATED_OPERATOR_APPROVAL"
    assert (
        service.store.approve(
            camera_id,
            "candidate-one",
            report.report_id,
            "Simulated test operator",
            approval_request,
        )
        == approved
    )
    # A new process/store object must retain the same artifact and explicit approval.
    restored = CalibrationService(Store(tmp_path / "workflow.db"), seed=29)
    assert restored.store.active(camera_id) == artifact
    manifest_path = restored.export(tmp_path / "export")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert any(record["kind"] == "artifact" for record in manifest["records"])
    # 60 native depth arrays plus 24 independently detected reference masks.
    assert len(list((tmp_path / "export" / "images").rglob("*.npy"))) == 84
    with pytest.raises(FileExistsError):
        restored.export(tmp_path / "export")
    unchanged = restored.store.state(camera_id)
    restored.store.invalidate(
        camera_id,
        "ROUTINE_REFERENCE_CHECK_FAILED",
        Mutation(request_id="suspect", expected_revision=unchanged.revision),
    )
    with pytest.raises(CalibrationError, match="ACTIVE_CALIBRATION_SUSPECT"):
        restored.store.active(camera_id)
    # Historical candidate and approval remain readable without restoring permission.
    assert restored.store.state(camera_id).active_artifact_id == artifact.artifact_id
    with pytest.raises(CalibrationError, match="ALREADY_USED"):
        restored.store.reserve_validation(
            camera_id,
            "candidate-one",
            ("unused-final-board",),
            Mutation(request_id="reuse", expected_revision=7),
        )
    with pytest.raises(Conflict, match="WORLD_SEED_IMMUTABLE"):
        CalibrationService(Store(tmp_path / "workflow.db"), seed=30)


def test_concurrent_configuration_commits_once_with_revision_and_key_guards(tmp_path):
    repository = CalibrationStore(Store(tmp_path / "workflow.db"))
    camera, board, limits = default_camera("camera"), default_board(), Limits()
    request = Mutation(request_id="same", expected_revision=0)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(
            pool.map(lambda _: repository.configure(camera, board, limits, request), range(3))
        )
    assert results[0] == results[1] == results[2]
    assert repository.state("camera").revision == 1
    with pytest.raises(Conflict, match="IDEMPOTENCY"):
        repository.configure(
            camera, board, limits.model_copy(update={"max_reference_error_mm": 1}), request
        )
    with pytest.raises(Conflict, match="STALE"):
        repository.configure(
            camera, board, limits, Mutation(request_id="different", expected_revision=0)
        )


def test_bad_timing_keeps_raw_capture_and_rejection_without_fit_samples(tmp_path):
    service = CalibrationService(Store(tmp_path / "workflow.db"), seed=83)
    service.configure("camera-east", Mutation(request_id="configure", expected_revision=0))
    measured = service.acquire(
        "camera-east",
        "bad-timing",
        Mutation(request_id="measure", expected_revision=1),
        timestamp_skew_s=0.1,
        settled=False,
    )
    assert len(measured.record_ids) == 18
    with service.store.store.readonly_connect() as db:
        assert (
            db.execute("SELECT COUNT(*) FROM calibration_records WHERE kind='capture'").fetchone()[
                0
            ]
            == 18
        )
        assert (
            db.execute(
                "SELECT COUNT(*) FROM calibration_records WHERE kind='rejection'"
            ).fetchone()[0]
            == 18
        )
        assert (
            db.execute("SELECT COUNT(*) FROM calibration_records WHERE kind='sample'").fetchone()[0]
            == 0
        )
    with pytest.raises(CalibrationError, match="INSUFFICIENT_MEASUREMENT"):
        service.fit(
            "camera-east",
            "bad-timing",
            "bad-candidate",
            Mutation(request_id="fit", expected_revision=2),
        )
