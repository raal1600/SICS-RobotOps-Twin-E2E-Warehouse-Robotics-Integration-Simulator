"""Missing tolerances block authority durably; restoring values is not approval."""

import pytest

from robotops.calibration.contracts import CalibrationArtifact, Limits
from robotops.calibration.errors import CalibrationError
from robotops.calibration.lifecycle import Mutation
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


def test_missing_limits_retry_restart_and_controlled_revalidation(tmp_path):
    runtime = SyntheticRuntime(tmp_path / "runtime.db", Settings.calibration(seed=37))
    workflow = Store(tmp_path / "workflow.db")
    service = Engine(workflow, runtime).calibration
    camera = "camera-west"

    def mutation(identity):
        return Mutation(request_id=identity, expected_revision=service.store.state(camera).revision)

    service.configure(camera, Mutation(request_id="configure", expected_revision=0))
    service.acquire(camera, "fit", mutation("acquire"))
    service.fit(camera, "fit", "candidate", mutation("fit"))
    validation = service.validate(camera, "candidate", "final-original", mutation("validate"))
    service.store.approve(
        camera, "candidate", validation.record_ids[0], "Simulated operator", mutation("approve")
    )
    original = service.store.active(camera)
    original_physics = runtime.world()
    request = mutation("remove-limit")
    receipt = service.introduce_fault(camera, "missing_reference_limit", request)
    assert receipt.state.limits.max_reference_error_mm is None
    assert receipt.state.active_artifact_id == original.artifact_id
    assert service.introduce_fault(camera, "missing_reference_limit", request) == receipt
    assert runtime.world() == original_physics  # No hardware fault or controller effect.
    assert service.store.state(camera).revision == receipt.state.revision
    with pytest.raises(CalibrationError, match="ACTIVE_CALIBRATION_SUSPECT"):
        service.store.active(camera)
    with pytest.raises(CalibrationError, match="CANDIDATE_CONFIGURATION_NOT_APPLICABLE"):
        service.store.approve(
            camera, "candidate", validation.record_ids[0], "Simulated operator", mutation("denied")
        )
    service = Engine(Store(tmp_path / "workflow.db"), runtime).calibration
    assert service.store.state(camera) == receipt.state
    service.introduce_fault(camera, "restore_limits", mutation("restore-limit"))
    assert service.store.state(camera).limits == Limits()
    with pytest.raises(CalibrationError, match="ACTIVE_CALIBRATION_SUSPECT"):
        service.store.active(camera)
    with pytest.raises(CalibrationError, match="CURRENT_CANDIDATE_VALIDATION_REQUIRED"):
        service.store.approve(
            camera,
            "candidate",
            validation.record_ids[0],
            "Simulated operator",
            mutation("old-approval"),
        )
    service.reuse_estimate(camera, original.artifact_id, "revalidated", mutation("reuse"))
    validated = service.validate(camera, "revalidated", "unused-final-2", mutation("validate-2"))
    assert service.report(validated.record_ids[0]).passed
    assert service.store.state(camera).active_validity == "SUSPECT_INVALID"
    service.store.approve(
        camera,
        "revalidated",
        validated.record_ids[0],
        "New simulated approval",
        mutation("approve-2"),
    )
    active = service.store.active(camera)
    assert active.artifact_id != original.artifact_id
    assert active.candidate.x == original.candidate.x
    assert service.store.record("artifact", original.artifact_id, CalibrationArtifact) == original
