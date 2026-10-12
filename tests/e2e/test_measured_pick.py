"""Real application workflow consumes a fresh image-derived approved calibration."""

import json

import numpy as np
import pytest

from robotops.blender.adapter import BlenderRuntime
from robotops.calibration.lifecycle import Mutation
from robotops.calibration.replay import controller_recording
from robotops.calibration.reproduction import reproduce
from robotops.calibration.tcp import ToolMeasurements, ToolVerification, verify_measurements
from robotops.cell.calibration_motion import ControllerFrame
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.domain.models import (
    JobState,
    OrderLine,
    OrderRequest,
    PresentationSnapshot,
    RobotCommand,
    WorldObservation,
)
from robotops.integration.engine import GuidedEngine
from robotops.integration.models import AuthorizeStage, CreateSession
from robotops.observation.quality import quality
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


def _order(store, settings, identity):
    return store.intake(
        OrderRequest(
            order_id=identity,
            lines=(
                OrderLine(
                    order_line_id=f"line-{identity}",
                    product_id=settings.products[0].product_id,
                    source_id="source",
                    destination_id="destination",
                ),
            ),
        ),
        identity,
    )


@pytest.mark.parametrize(
    "runtime_type", [SyntheticRuntime, pytest.param(BlenderRuntime, marks=pytest.mark.blender)]
)
@pytest.mark.parametrize("command_mode", ["flange", "tcp"])
def test_approved_calibration_drives_real_command_contact_and_fresh_verification(
    tmp_path, runtime_type, command_mode
):
    settings = Settings.calibration(seed=211, calibration_command_mode=command_mode)
    runtime = runtime_type(tmp_path / "runtime.db", settings)
    store = Store(tmp_path / "workflow.db")
    engine = Engine(store, runtime, settings)
    calibration = engine.calibration
    assert calibration is not None
    unapproved = _order(store, settings, "not-approved")
    blocked = engine.run(unapproved.job_ids[0])
    assert blocked.state == JobState.FAILED
    assert blocked.command_id is None
    assert runtime.world().step == 0
    for camera in ("camera-west", "camera-east"):
        calibration.configure(camera, Mutation(request_id="setup", expected_revision=0))
        calibration.acquire(
            camera, f"{camera}-controller-fit", Mutation(request_id="capture", expected_revision=1)
        )
        calibration.fit(
            camera,
            f"{camera}-controller-fit",
            f"{camera}-controller-candidate",
            Mutation(request_id="fit", expected_revision=2),
        )
        evaluated = calibration.validate(
            camera,
            f"{camera}-controller-candidate",
            f"{camera}-controller-unused-final",
            Mutation(request_id="validate", expected_revision=3),
        )
        report = calibration.report(evaluated.record_ids[0])
        (tmp_path / f"{camera}-independent-validation.json").write_text(
            report.model_dump_json(indent=2), encoding="utf-8"
        )
        assert report.passed, report.failures
        calibration.store.approve(
            camera,
            f"{camera}-controller-candidate",
            report.report_id,
            "Simulated acceptance operator",
            Mutation(request_id="approve", expected_revision=5),
        )
    camera = "camera-west"
    checked = calibration.prepare_tool(
        camera, Mutation(request_id="tool-check", expected_revision=6)
    )
    assert checked.state.active_validity == "VERIFIED"
    machine_after_check = runtime.world().calibration_machine
    assert (
        calibration.prepare_tool(camera, Mutation(request_id="tool-check", expected_revision=6))
        == checked
    )
    assert runtime.world().calibration_machine == machine_after_check
    tool_measurements = calibration.store.record(
        "tool-measurements", checked.record_ids[0], ToolMeasurements
    )
    tool_report = calibration.store.record(
        "tool-verification", checked.record_ids[0], ToolVerification
    )
    assert verify_measurements(tool_measurements) == tool_report
    assert (
        tool_report.passed
        and len(tool_measurements.pivot_flange_poses) == 6
        and len(tool_measurements.probes) == 4
    )
    order = _order(store, settings, "measured-pick")
    job = engine.run(order.job_ids[0])
    (tmp_path / "job-result.json").write_text(job.model_dump_json(indent=2), encoding="utf-8")
    with store.readonly_connect() as db:
        reasons = [
            json.loads(row[0])["reason"]
            for row in db.execute("SELECT body FROM events ORDER BY sequence DESC LIMIT 8")
        ]
    assert job.state == JobState.COMPLETED, (job, reasons)
    assert job.command_id is not None
    command = store.load(RobotCommand, job.command_id)
    assert command.schema_version == "3.0"
    assert command.calibrated_plan is not None
    target = command.calibrated_plan.target
    assert target.mode == command_mode
    assert target.command_target == (
        target.tcp_target if command_mode == "tcp" else target.flange_target
    )
    # The reported tool is +180 mm along flange z; grasp orientation points down.
    # Golden coordinate difference is independent of the transform helper.
    np.testing.assert_allclose(
        np.array(target.flange_target.matrix)[:3, 3] - np.array(target.tcp_target.matrix)[:3, 3],
        [0, 0, 0.18],
        atol=1e-12,
    )
    restarted_mode = runtime_type(runtime.db.path, Settings.calibration())
    assert restarted_mode.world().calibration_machine.command_mode == command_mode
    assert restarted_mode.settings.calibration_command_mode == command_mode
    start_world = store.load(PresentationSnapshot, command.job_id).world
    assert runtime.rejection_reason(start_world, command, None) is None
    # Non-executing adversarial copies: a second 180 mm offset cannot pass the
    # physical target gate, even when the wire fields and grasp waypoint agree.
    bad = command.model_dump(mode="json")
    wrong_target = bad["calibrated_plan"]["target"]
    field = "tcp_target" if command_mode == "tcp" else "flange_target"
    wrong_target[field]["matrix"][2][3] += 0.18
    wrong_target["command_target"] = wrong_target[field]
    bad["calibrated_plan"]["waypoints"][1]["tcp" if command_mode == "tcp" else "flange"] = (
        wrong_target[field]
    )
    doubled = RobotCommand.model_validate(bad)
    assert runtime.rejection_reason(start_world, doubled, None) == (
        "DOUBLE_TOOL_OFFSET_OR_COMMAND_TARGET_MISMATCH"
        if command_mode == "tcp"
        else "SYNTHETIC_CONTACT_MISSED: Computed TCP did not contact the physical top patch"
    )
    changed_mode = start_world.model_copy(
        update={
            "calibration_machine": start_world.calibration_machine.model_copy(
                update={"command_mode": "flange" if command_mode == "tcp" else "tcp"}
            )
        }
    )
    assert (
        runtime.rejection_reason(changed_mode, command, None) == "CONTROLLER_COMMAND_MODE_CHANGED"
    )
    artifact = calibration.store.active(camera)
    assert command.calibrated_plan.observed_object.binding.artifact_id == artifact.artifact_id
    assert command.calibrated_plan.target.calculation.inputs["point"]["point"] == list(
        command.calibrated_plan.observed_object.surface_point.point
    )
    before = store.load(WorldObservation, command.observation_id)
    assert before.objects[0].location_id == "source"
    assert before.objects[0].confidence is None and before.objects[0].uncertainty_m is None
    assert before.objects[0].calibrated_object.measurement_quality.passed
    receipt = runtime.journal(command.command_id)
    assert receipt.effect_count == 1
    assert runtime.world().objects[0].location_id == "destination"
    # An off-center but admissible contact keeps its physical offset through transfer.
    expected_center = (
        np.array(settings.locations[1].pose.position)
        + np.array(settings.locations[0].pose.position)
        + [0, 0, 0.04]
        - np.array(command.calibrated_plan.target.tcp_target.matrix)[:3, 3]
    )
    assert np.allclose(runtime.world().objects[0].pose.position, expected_center, atol=1e-9)
    with runtime.db.readonly_connect() as db:
        reported = [
            ControllerFrame.model_validate_json(row[0])
            for row in db.execute(
                "SELECT body FROM calibration_motion_frames WHERE command_id=? ORDER BY sample_index",
                (command.command_id,),
            )
        ]
    assert len(reported) == 121 and reported[-1].sim_time_s == 5
    recording = controller_recording(store, runtime, command)
    assert recording is not None and recording.complete
    assert recording.source == "SYNTHETIC_CONTROLLER_REPORTS"
    assert len(recording.frames) == len(reported)
    for visual, actual in zip(recording.frames, reported, strict=True):
        assert np.allclose(
            visual.positions["Robot/ToolChanger"], np.array(actual.machine.flange.matrix)[:3, 3]
        )
        assert np.allclose(
            visual.positions["Robot/ActiveTool"], np.array(actual.machine.tcp.matrix)[:3, 3]
        )
        assert np.allclose(
            visual.positions["Product/calibration-red-cube"], actual.object_pose.position
        )
        assert visual.attached_product_id == (command.product_id if actual.attached else None)
    if isinstance(runtime, BlenderRuntime):
        evaluated = runtime.motion(command)
        assert evaluated is not None, [
            path.read_text(encoding="utf-8")[-2000:]
            for path in runtime.artifacts.glob("*/runtime.log")
        ]
        assert evaluated.complete and evaluated.source == "BLENDER_EVALUATED_CONTROLLER_REPLAY"
        assert len(evaluated.frames) == len(reported)
        for visual, actual in zip(evaluated.frames, reported, strict=True):
            assert np.allclose(
                visual.positions["Robot/ToolChanger"],
                np.array(actual.machine.flange.matrix)[:3, 3],
                atol=1e-6,
                rtol=0,
            )
            assert np.allclose(
                visual.positions["Robot/ActiveTool"],
                np.array(actual.machine.tcp.matrix)[:3, 3],
                atol=1e-6,
                rtol=0,
            )
            assert np.allclose(
                visual.positions["Product/calibration-red-cube"],
                actual.object_pose.position,
                atol=1e-6,
                rtol=0,
            )
            quat = visual.transforms["Robot/ToolChanger"].quaternion_xyzw
            from scipy.spatial.transform import Rotation

            assert np.allclose(
                Rotation.from_quat(quat).as_matrix(),
                np.array(actual.machine.flange.matrix)[:3, :3],
                atol=1e-6,
                rtol=0,
            )
        capture_path = runtime.command_artifact(command.command_id, "capture.png")
        assert capture_path.read_bytes().startswith(b"\x89PNG")
        response_path = runtime.command_artifact(command.command_id, "response.json")
        assert (
            json.loads(response_path.read_text())["authority"] == "PRESENTATION_ONLY_NO_EXECUTION"
        )
        assert runtime._complete(command, response_path.parent) is None
        before_import = runtime.world()
        motion_path = runtime.command_artifact(command.command_id, "motion.json")
        # Retain the first export; import reconstructs only the missing presentation.
        motion_path.rename(motion_path.with_name("motion.first.json"))
        runtime.import_motion(command)
        assert runtime.world() == before_import
        imported = runtime.motion(command)
        assert imported is not None and imported.complete
        assert np.allclose(
            imported.frames[48].positions["Robot/ToolChanger"],
            evaluated.frames[48].positions["Robot/ToolChanger"],
            atol=1e-6,
            rtol=0,
        )
    with runtime.db.readonly_connect() as db:
        before_replay = db.execute("SELECT COUNT(*) FROM controller_journal").fetchone()[0]
    assert controller_recording(store, runtime, command) == recording
    with runtime.db.readonly_connect() as db:
        assert db.execute("SELECT COUNT(*) FROM controller_journal").fetchone()[0] == before_replay
    after = engine.measured_observer.fresh()
    assert after.objects[0].location_id == "destination"
    assert after.captured_at > receipt.timestamp
    assert after.observation_id != before.observation_id
    assert after.model_version == "measured-rgbd-observer-2"
    assert quality(after, command.product_id, settings, after.captured_at) is None
    # Test-only evidence mutations, never stored or dispatched: unknown statistics
    # cannot substitute for the measured gates, and a stale quality binding rejects.
    detected = after.objects[0]
    unproven = detected.calibrated_object.model_copy(update={"measurement_quality": None})
    missing_checks = after.model_copy(
        update={"objects": (detected.model_copy(update={"calibrated_object": unproven}),)}
    )
    assert (
        quality(missing_checks, command.product_id, settings, after.captured_at)
        == "MEASUREMENT_QUALITY_EVIDENCE_REQUIRED"
    )
    forged = detected.calibrated_object.measurement_quality.model_copy(
        update={"point_fingerprint": "unrelated"}
    )
    stale_checks = after.model_copy(
        update={
            "objects": (
                detected.model_copy(
                    update={
                        "calibrated_object": detected.calibrated_object.model_copy(
                            update={"measurement_quality": forged}
                        )
                    }
                ),
            )
        }
    )
    assert (
        quality(stale_checks, command.product_id, settings, after.captured_at)
        == "MEASUREMENT_QUALITY_POINT_BINDING_MISMATCH"
    )
    original_receipt = receipt.model_dump(mode="json")
    # The same immutable command cannot cause a second transfer, including after invalidation.
    calibration.store.invalidate(
        camera, "CAMERA_MOUNT_SUSPECT", Mutation(request_id="invalidate", expected_revision=7)
    )
    assert runtime.apply(command).model_dump(mode="json") == original_receipt
    assert runtime.world().step == 1
    if isinstance(runtime, BlenderRuntime):
        assert len(list(runtime.artifacts.glob("*/request.json"))) == 1
    with runtime.db.readonly_connect() as db:
        count = db.execute("SELECT COUNT(*) FROM calibration_captures").fetchone()[0]
        assert count == 72
    (tmp_path / "command-and-receipt.json").write_text(
        json.dumps(
            {
                "command": command.model_dump(mode="json"),
                "receipt": original_receipt,
                "post_observation": after.model_dump(mode="json"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    saved_state = calibration.store.state(camera)
    saved_world = runtime.world()
    bundle = calibration.export(tmp_path / "complete-evidence")
    reproduced = reproduce(bundle.parent)
    (tmp_path / "reproduction.json").write_text(json.dumps(reproduced, indent=2), encoding="utf-8")
    assert reproduced["passed"], reproduced
    assert len(reproduced["validation_results"]) == 2
    assert len(reproduced["optical_model_results"]) == 2
    assert len(reproduced["acquisition_results"]) == 2
    assert all(
        item["matches_saved"] and item["ready_to_fit"] for item in reproduced["acquisition_results"]
    )
    assert len(reproduced["runtime_point_results"]) >= 4
    assert len(reproduced["reference_calculation_results"]) == 48
    assert len(reproduced["surface_detection_results"]) >= 52
    assert len(reproduced["camera_agreement_results"]) >= 2
    assert len(reproduced["measurement_quality_results"]) >= 2
    # Planning can be recomputed during revalidation. Preserve each actual call;
    # it is the immutable command/effect count that must remain exactly one.
    assert reproduced["target_results"]
    assert len({item["record_id"] for item in reproduced["target_results"]}) == 1
    assert len(reproduced["tool_results"]) == 1
    assert reproduced["controller_results"] == [
        {
            "command_id": command.command_id,
            "matches_saved": True,
            "effect_count": 1,
            "controller_frame_count": 121,
        }
    ]
    assert calibration.store.state(camera) == saved_state
    assert runtime.world() == saved_world


@pytest.mark.parametrize("guided_mode", [False, True])
def test_camera_change_after_effect_keeps_original_command_until_reobservation(
    tmp_path, monkeypatch, guided_mode
):
    settings = Settings.calibration(seed=211)
    runtime = SyntheticRuntime(tmp_path / "runtime.db", settings)
    engine = Engine(Store(tmp_path / "workflow.db"), runtime, settings)
    calibration = engine.calibration
    assert calibration is not None

    def mutation(camera, name):
        return Mutation(request_id=name, expected_revision=calibration.store.state(camera).revision)

    for camera in ("camera-west", "camera-east"):
        calibration.configure(camera, Mutation(request_id="configure", expected_revision=0))
        calibration.acquire(camera, f"{camera}-controller-fit", mutation(camera, "acquire"))
        calibration.fit(
            camera,
            f"{camera}-controller-fit",
            f"{camera}-controller-candidate",
            mutation(camera, "fit"),
        )
        result = calibration.validate(
            camera,
            f"{camera}-controller-candidate",
            f"{camera}-controller-unused-final",
            mutation(camera, "validate"),
        )
        report = calibration.report(result.record_ids[0])
        assert report.passed, report.failures
        calibration.store.approve(
            camera,
            report.candidate_id,
            report.report_id,
            "Simulated fault acceptance operator",
            mutation(camera, "approve"),
        )
    calibration.prepare_tool("camera-west", mutation("camera-west", "tool"))
    applied = runtime.apply

    def physical_move_after_effect(command, fault=None):
        receipt = applied(command, fault)
        assert receipt.effect_count == 1
        # Actual isolated hardware/configuration notice occurs between the physical
        # controller commit and the next sensor observation, not a mocked response.
        calibration.move_camera(
            "camera-west",
            mutation("camera-west", "mount-moved-after-effect"),
            (0.04, 0, 0),
            (0, 0.025, 0),
        )
        return receipt

    monkeypatch.setattr(runtime, "apply", physical_move_after_effect)
    if guided_mode:
        guided = GuidedEngine(engine)
        session = guided.create(
            CreateSession(
                request_id="uncertain-measured",
                request=OrderRequest(
                    order_id="uncertain-measured-pick",
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
                    request_id=f"authorize-{session.revision}",
                    expected_revision=session.revision,
                    stage=session.pending_authorization.stage,
                ),
            )
        assert session.status == "UNKNOWN_OUTCOME"
        assert session.steps[-1].stage == 18
        assert session.steps[-1].output["retry_permitted"] is False
        job = engine.store.job(session.job_id)
    else:
        order = _order(engine.store, settings, "uncertain-measured-pick")
        job = engine.run(order.job_ids[0])
    assert job.state == JobState.UNKNOWN_OUTCOME
    command = engine.store.load(RobotCommand, job.command_id)
    original_command = command.model_dump_json()
    assert runtime.recorded_journal(command.command_id).effect_count == 1
    assert runtime.world().objects[0].location_id == "destination"
    with engine.store.readonly_connect() as db:
        failures = [
            json.loads(row[0])
            for row in db.execute(
                "SELECT body FROM calibration_records WHERE kind='observation-failure'"
            )
        ]
    assert failures[-1]["command_id"] == command.command_id
    assert failures[-1]["code"] == "ACTIVE_CALIBRATION_SUSPECT"
    # Restart and unresolved evidence can query the original; they cannot send it.
    restarted = Engine(Store(engine.store.path), SyntheticRuntime(runtime.db.path))
    if guided_mode:
        guided = GuidedEngine(restarted)
    for _ in range(2):
        if guided_mode:
            session = guided.reconcile(
                session.session_id,
                AuthorizeStage(
                    request_id=f"unresolved-{session.revision}",
                    expected_revision=session.revision,
                    stage=session.current_stage,
                ),
            )
            assert session.status == "UNKNOWN_OUTCOME"
            assert session.steps[-1].output["code"] == "ACTIVE_CALIBRATION_SUSPECT"
        else:
            assert restarted.reconcile(job.job_id).state == JobState.UNKNOWN_OUTCOME
    assert restarted.runtime.world().step == 1
    calibration = restarted.calibration
    assert calibration is not None
    camera = "camera-west"
    calibration.begin_measurements(camera, mutation(camera, "recovery-begin"))
    calibration.acquire(camera, "recovery-fit-unused", mutation(camera, "recovery-acquire"))
    calibration.fit(
        camera, "recovery-fit-unused", "recovery-candidate", mutation(camera, "recovery-fit")
    )
    evaluated = calibration.validate(
        camera, "recovery-candidate", "recovery-final-unused", mutation(camera, "recovery-validate")
    )
    report = calibration.report(evaluated.record_ids[0])
    assert report.passed, report.failures
    calibration.store.approve(
        camera,
        "recovery-candidate",
        report.report_id,
        "Simulated recovery operator",
        mutation(camera, "recovery-approve"),
    )
    calibration.prepare_tool(camera, mutation(camera, "recovery-tool"))
    assert (
        calibration.store.active(camera).artifact_id
        != command.calibrated_plan.observed_object.binding.artifact_id
    )
    if guided_mode:
        session = guided.reconcile(
            session.session_id,
            AuthorizeStage(
                request_id="after-approved-recovery",
                expected_revision=session.revision,
                stage=session.current_stage,
            ),
        )
        for _ in range(5):
            if session.status == "COMPLETED":
                break
            session = guided.authorize(
                session.session_id,
                AuthorizeStage(
                    request_id=f"business-{session.revision}",
                    expected_revision=session.revision,
                    stage=session.pending_authorization.stage,
                ),
            )
        assert session.status == "COMPLETED"
        recovered = restarted.store.job(job.job_id)
    else:
        recovered = restarted.reconcile(job.job_id)
    assert recovered.state == JobState.COMPLETED
    assert restarted.store.load(RobotCommand, job.command_id).model_dump_json() == original_command
    assert restarted.runtime.world().step == 1
    assert sum(event.event_type == "PICK_EFFECT" for event in restarted.runtime.events()) == 1
    (tmp_path / "recovery-result.json").write_text(
        json.dumps(
            {
                "original_command": command.model_dump(mode="json"),
                "reconciled_job": recovered.model_dump(mode="json"),
                "failures": failures,
                "new_artifact_id": calibration.store.active(camera).artifact_id,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
