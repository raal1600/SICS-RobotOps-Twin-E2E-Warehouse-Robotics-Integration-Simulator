"""An old estimate may be tested again, but its old approval cannot be restored."""

import pytest

from robotops.calibration.contracts import CalibrationArtifact, Candidate
from robotops.calibration.errors import CalibrationError
from robotops.calibration.lifecycle import Mutation
from robotops.calibration.reproduction import reproduce
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.workflow.engine import Engine
from robotops.workflow.store import Conflict, Store


def request(service, identity, camera="camera-west"):
    return Mutation(request_id=identity, expected_revision=service.store.state(camera).revision)


def initial(tmp_path):
    runtime = SyntheticRuntime(tmp_path / "runtime.db", Settings.calibration(seed=83))
    engine = Engine(Store(tmp_path / "workflow.db"), runtime)
    service = engine.calibration
    camera = "camera-west"
    service.configure(camera, Mutation(request_id="configure", expected_revision=0))
    service.acquire(camera, "original-fit", request(service, "capture"))
    service.fit(camera, "original-fit", "original", request(service, "fit"))
    receipt = service.validate(camera, "original", "original-final", request(service, "validate"))
    assert service.report(receipt.record_ids[0]).passed
    service.store.approve(
        camera,
        "original",
        receipt.record_ids[0],
        "Simulated test operator",
        request(service, "approve"),
    )
    return runtime, engine, service, service.store.active(camera)


def test_saved_estimate_requires_unused_validation_and_new_approval_then_survives_restart(tmp_path):
    runtime, engine, service, original = initial(tmp_path)
    camera = "camera-west"
    service.introduce_fault(camera, "depth_scale", request(service, "wrong-depth"))
    service.introduce_fault(camera, "restore_sensor", request(service, "restore-depth"))
    reuse_request = request(service, "reuse")
    receipt = service.reuse_estimate(camera, original.artifact_id, "rechecked", reuse_request)
    assert receipt.operation == "reuse-estimate"
    assert receipt.state.workflow_state == "CANDIDATE"
    assert receipt.state.active_validity == "SUSPECT_INVALID"
    assert receipt.state.active_artifact_id == original.artifact_id
    candidate = service.store.record("candidate", "rechecked", Candidate)
    assert candidate.x == original.candidate.x and candidate.y == original.candidate.y
    assert candidate.sample_ids == original.candidate.sample_ids
    assert candidate.source_fingerprints == original.candidate.source_fingerprints
    assert candidate.reused_from.artifact_fingerprint == original.fingerprint()
    assert candidate.reused_from.candidate_fingerprint == original.candidate.fingerprint()
    assert not candidate.active
    assert runtime.world().calibration_machine.board_mounted
    with pytest.raises(CalibrationError, match="SUSPECT"):
        service.store.active(camera)
    with pytest.raises(Conflict, match="IDEMPOTENCY"):
        service.reuse_estimate(camera, original.artifact_id, "changed-id", reuse_request)
    with pytest.raises(CalibrationError, match="ALREADY_USED"):
        service.validate(camera, "rechecked", "original-final", request(service, "reused-holdout"))
    with pytest.raises(CalibrationError, match="CURRENT_CANDIDATE_VALIDATION_REQUIRED"):
        service.store.approve(
            camera,
            "rechecked",
            original.validation.report_id,
            "Cannot reuse old approval",
            request(service, "old-report"),
        )
    checked = service.validate(
        camera, "rechecked", "genuinely-unused-final", request(service, "new-validation")
    )
    assert service.report(checked.record_ids[0]).passed
    assert service.store.state(camera).active_validity == "SUSPECT_INVALID"
    service.store.approve(
        camera,
        "rechecked",
        checked.record_ids[0],
        "New simulated approval",
        request(service, "new-approval"),
    )
    renewed = service.store.active(camera)
    assert renewed.artifact_id != original.artifact_id
    assert renewed.approval.timestamp_utc != original.approval.timestamp_utc
    state = service.store.state(camera)
    assert (
        service.reuse_estimate(camera, original.artifact_id, "rechecked", reuse_request) == receipt
    )
    assert service.store.state(camera) == state
    restarted = Engine(Store(tmp_path / "workflow.db"), SyntheticRuntime(tmp_path / "runtime.db"))
    assert restarted.calibration.store.active(camera) == renewed
    assert (
        restarted.calibration.store.record("artifact", original.artifact_id, CalibrationArtifact)
        == original
    )
    (tmp_path / "revalidated-artifact.json").write_text(
        renewed.model_dump_json(indent=2), encoding="utf-8"
    )
    service.export(tmp_path / "export")
    reproduced = reproduce(tmp_path / "export")
    assert reproduced["passed"], reproduced
    reused = next(item for item in reproduced["results"] if item["candidate_id"] == "rechecked")
    assert reused["saved_estimate_lineage_matches"]
    assert reused["reused_from_artifact"] == original.artifact_id


def test_moved_camera_cannot_rollback_and_remounted_board_cannot_reuse_old_y(tmp_path):
    runtime, engine, service, original = initial(tmp_path)
    camera = "camera-west"
    service.move_camera(camera, request(service, "move"), (0.04, 0, 0), (0, 0.025, 0))
    receipt = service.reuse_estimate(
        camera, original.artifact_id, "old-at-new-mount", request(service, "reuse")
    )
    assert receipt.state.active_validity == "SUSPECT_INVALID"
    checked = service.validate(
        camera, "old-at-new-mount", "new-mount-final", request(service, "validate-moved")
    )
    report = service.report(checked.record_ids[0])
    assert not report.passed
    assert report.reference_max_mm > 5
    with pytest.raises(CalibrationError):
        service.store.approve(
            camera,
            "old-at-new-mount",
            report.report_id,
            "Unsafe rollback",
            request(service, "deny"),
        )
    assert service.store.state(camera).active_artifact_id == original.artifact_id
    with pytest.raises(CalibrationError, match="SUSPECT"):
        service.store.active(camera)
    service.introduce_fault(camera, "board_remount", request(service, "remount"))
    with pytest.raises(CalibrationError, match="CONFIGURATION_NOT_APPLICABLE"):
        service.reuse_estimate(
            camera, original.artifact_id, "wrong-y", request(service, "deny-remount")
        )
    service.configure(camera, request(service, "record-board"))
    with pytest.raises(CalibrationError, match="CONFIGURATION_NOT_APPLICABLE"):
        service.reuse_estimate(
            camera, original.artifact_id, "wrong-y-again", request(service, "deny-new-board")
        )
    (tmp_path / "rejected-rollback.json").write_text(
        report.model_dump_json(indent=2), encoding="utf-8"
    )
