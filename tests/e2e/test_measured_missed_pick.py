"""Image-derived command executes, but failed grip leaves the object for fresh verification."""

import numpy as np
import pytest
from pydantic import ValidationError
from scipy.spatial.transform import Rotation

from robotops.blender.adapter import BlenderRuntime
from robotops.calibration.diagnostics import InvestigationReport
from robotops.calibration.lifecycle import Mutation
from robotops.calibration.outcome import PickOutcome
from robotops.calibration.replay import controller_recording
from robotops.calibration.reproduction import reproduce
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.domain.models import (
    CommandReceipt,
    Fault,
    JobState,
    OrderLine,
    OrderRequest,
    RobotCommand,
)
from robotops.integration.engine import GuidedEngine
from robotops.integration.models import AuthorizeStage, CreateSession
from robotops.workflow.engine import Engine
from robotops.workflow.store import Conflict, Store


@pytest.mark.parametrize(
    "runtime_type", [SyntheticRuntime, pytest.param(BlenderRuntime, marks=pytest.mark.blender)]
)
def test_actual_missed_pick_keeps_unknown_cause_original_command_and_unchanged_calibration(
    tmp_path,
    runtime_type,
):
    settings = Settings.calibration(seed=37)
    runtime = runtime_type(tmp_path / "runtime.db", settings)
    store = Store(tmp_path / "workflow.db")
    engine = Engine(store, runtime)
    calibration = engine.calibration

    def request(camera, identity):
        return Mutation(
            request_id=identity, expected_revision=calibration.store.state(camera).revision
        )

    for camera in ("camera-west", "camera-east"):
        calibration.configure(camera, Mutation(request_id="configure", expected_revision=0))
        calibration.acquire(camera, camera + "-fit", request(camera, "capture"))
        calibration.fit(camera, camera + "-fit", camera + "-candidate", request(camera, "fit"))
        checked = calibration.validate(
            camera, camera + "-candidate", camera + "-unused-final", request(camera, "validate")
        )
        report = calibration.report(checked.record_ids[0])
        assert report.passed, report.failures
        calibration.store.approve(
            camera,
            report.candidate_id,
            report.report_id,
            "Simulated missed-pick test operator",
            request(camera, "approve"),
        )
    calibration.prepare_tool("camera-west", request("camera-west", "tool-check"))
    approvals = {
        camera: calibration.store.active(camera) for camera in ("camera-west", "camera-east")
    }
    original_object = runtime.world().objects[0]
    guided = GuidedEngine(engine)
    session = guided.create(
        CreateSession(
            request_id="missed-pick",
            fault=Fault.MISSED_PICK.value,
            request=OrderRequest(
                order_id="missed-pick",
                lines=(
                    OrderLine(
                        order_line_id="line",
                        product_id=settings.products[0].product_id,
                        source_id="source",
                        destination_id="destination",
                    ),
                ),
            ),
        )
    )
    for _ in range(24):
        if session.status in {"COMPLETED", "FAILED", "UNKNOWN_OUTCOME"}:
            break
        session = guided.authorize(
            session.session_id,
            AuthorizeStage(
                request_id=f"approve-{session.revision}",
                expected_revision=session.revision,
                stage=session.pending_authorization.stage,
            ),
        )
    assert session.status == "COMPLETED", session
    assert store.job(session.job_id).state == JobState.FAILED
    command = store.load(RobotCommand, session.command_id)
    receipt = runtime.recorded_journal(command.command_id)
    assert receipt.reason == "GRASP_NOT_ESTABLISHED" and receipt.effect_count == 0
    assert receipt.calibrated_receipt.executed_waypoint_count == 6
    assert receipt.calibrated_receipt.motion_without_transfer == "GRASP_NOT_ESTABLISHED"
    assert runtime.world().objects[0] == original_object
    recording = controller_recording(store, runtime, command)
    assert recording.complete and len(recording.frames) == 121
    assert all(frame.attached_product_id is None for frame in recording.frames)
    if isinstance(runtime, BlenderRuntime):
        evaluated = runtime.motion(command)
        assert evaluated is not None and evaluated.complete
        assert evaluated.source == "BLENDER_EVALUATED_CONTROLLER_REPLAY"
        assert len(evaluated.frames) == 121
        for frame, reported in zip(evaluated.frames, recording.frames, strict=True):
            assert frame.attached_product_id is None
            np.testing.assert_allclose(
                frame.positions["Product/calibration-red-cube"],
                original_object.pose.position,
                atol=1e-6,
                rtol=0,
            )
            for name in ("Robot/ToolChanger", "Robot/ActiveTool"):
                np.testing.assert_allclose(
                    frame.positions[name],
                    reported.positions[name],
                    atol=1e-6,
                    rtol=0,
                )
                np.testing.assert_allclose(
                    Rotation.from_quat(frame.transforms[name].quaternion_xyzw).as_matrix(),
                    Rotation.from_quat(reported.transforms[name].quaternion_xyzw).as_matrix(),
                    atol=1e-6,
                    rtol=0,
                )
    events = runtime.events()
    assert not any(event.event_type == "PICK_EFFECT" for event in events)
    assert sum(event.event_type == "PICK_ATTEMPT_NO_TRANSFER" for event in events) == 1
    assert runtime.apply(command) == receipt
    assert len(controller_recording(store, runtime, command).frames) == 121
    restarted = runtime_type(runtime.db.path, settings)
    assert restarted.apply(command) == receipt
    assert restarted.world() == runtime.world()
    assert sum(event.event_type == "PICK_ATTEMPT_NO_TRANSFER" for event in restarted.events()) == 1
    if isinstance(restarted, BlenderRuntime):
        assert len(list(restarted.artifacts.glob("*/request.json"))) == 1
    verification = session.context["verification"]
    outcome = calibration.store.record(
        "pick-outcome", "pick-" + verification["verification_id"], PickOutcome
    )
    assert outcome.verification.verdict == "VERIFIED_FAILURE"
    assert outcome.observation.captured_at > receipt.timestamp
    assert outcome.observation.objects[0].location_id == "source"
    assert outcome.observation.objects[0].calibrated_object.measurement_quality.passed
    inspected = calibration.investigate(
        "camera-west", "pick-outcome", outcome.outcome_id, request("camera-west", "investigate")
    )
    investigation = calibration.store.record(
        "investigation", inspected.record_ids[0], InvestigationReport
    )
    assert investigation.conclusion == "INSUFFICIENT_EVIDENCE / UNKNOWN_CAUSE"
    assert {item.code for item in investigation.clues} == {"MISSED_TRANSFER_CAUSE_UNRESOLVED"}
    for camera, artifact in approvals.items():
        assert calibration.store.active(camera) == artifact
    assert len(store.records_for_job(RobotCommand, command.job_id)) == 1
    assert session.context["wms_ack"] is True
    assert (
        next(step for step in session.steps if step.stage == 20).output["verified_outcome"]
        == "FAILED"
    )
    for changes in ({"status": "SUCCEEDED"}, {"effect_count": 1}, {"reason": "PICK_APPLIED"}):
        with pytest.raises(ValidationError):
            CommandReceipt.model_validate({**receipt.model_dump(mode="json"), **changes})
    bundle = calibration.export(tmp_path / "missed-pick-evidence")
    reproduced = reproduce(bundle.parent)
    assert reproduced["passed"], reproduced
    assert len(reproduced["pick_outcome_results"]) == 1
    assert reproduced["controller_results"][0]["effect_count"] == 0


def test_missed_pick_scenario_cannot_silently_change_the_legacy_robot_profile(
    tmp_path, order_request
):
    runtime = SyntheticRuntime(tmp_path / "runtime.db")
    engine = Engine(Store(tmp_path / "workflow.db"), runtime)
    with pytest.raises(Conflict, match="MISSED_PICK_REQUIRES_MEASURED_CELL"):
        GuidedEngine(engine).create(
            CreateSession(request_id="unsupported", request=order_request, fault="MISSED_PICK")
        )
    assert runtime.world().step == 0
