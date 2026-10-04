from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from apps.api.app import create_app
from robotops.brain.deterministic import DeterministicBrain
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.domain.models import (
    ActionPlan,
    CommandStatus,
    Fault,
    JobState,
    OrderLine,
    OrderRequest,
    ReconciliationEvidence,
    RobotCommand,
    Verdict,
)
from robotops.observability.metrics import prometheus
from robotops.robotics.catalogue import fixture_target_pose
from robotops.workflow.engine import Engine
from robotops.workflow.store import Conflict, Store, digest


def system(directory):
    runtime = SyntheticRuntime(directory / "runtime.db", Settings.hkm())
    return Engine(Store(directory / "workflow.db"), runtime)


def request_for(engine, sku="SKU-B", identity="hkm-order"):
    product = next(item for item in engine.settings.products if item.sku == sku)
    return OrderRequest(
        order_id=identity,
        lines=(
            OrderLine(
                order_line_id="line",
                product_id=product.product_id,
                source_id=engine.settings.source_for(product.product_id),
                destination_id=engine.settings.destination_id,
            ),
        ),
    )


def create_job(engine, sku="SKU-B", identity="hkm-order"):
    request = request_for(engine, sku, identity)
    return engine.store.intake(request, identity + "-key").job_ids[0]


def effects(engine):
    return sum(event.event_type == "PICK_EFFECT" for event in engine.runtime.events())


def metrics(engine):
    return {
        line.split()[0]: float(line.split()[1])
        for line in prometheus(engine.store).splitlines()
        if line and not line.startswith("#")
    }


def prepared_command(engine, sku="SKU-B"):
    job = engine.store.job(create_job(engine, sku))
    observation = engine.observer.observe(engine.runtime.world())
    destination = next(
        location
        for location in engine.settings.locations
        if location.location_id == job.line.destination_id
    )
    plan = DeterministicBrain(engine.settings).plan(job, observation, destination)
    return RobotCommand(
        **plan.model_dump(),
        command_id="hkm-defensive-command",
        required_tool_id=plan.selected_tool_id,
    )


def test_hkm_full_tool_showcase_persists_decisions_tools_and_six_distinct_effects(tmp_path):
    engine = system(tmp_path)
    expected = [
        "EE_VAC_SINGLE",
        "EE_VAC_ARRAY",
        "EE_ADAPTIVE_SOFT",
        "EE_PINCH_NARROW",
        "EE_PINCH_WIDE",
        "EE_SUPPORT_FORK",
    ]
    command_ids = []
    motion_durations = []
    for product, selected in zip(engine.settings.products, expected, strict=True):
        job_id = create_job(engine, product.sku, "order-" + product.sku)
        result = engine.run(job_id)
        assert result.state == JobState.COMPLETED
        plan = engine.store.load(ActionPlan, result.action_plan_id)
        command = engine.store.load(RobotCommand, result.command_id)
        command_ids.append(command.command_id)
        motion_durations.append(command.trajectory.estimated_sim_duration_s)
        assert command.required_tool_id == plan.selected_tool_id == selected
        assert plan.tool_selection.sku == product.sku
        assert plan.tool_selection.selected_tool_id == selected
        assert len(plan.tool_selection.candidate_tools) == 6
        timeline = engine.store.timeline(result.order_id)
        assert any(
            event.event_type == "GRASP_SELECTION_EVALUATED"
            and event.evidence_ids == (plan.action_plan_id,)
            for event in timeline
        )
        assert any(event.event_type == "TRAJECTORY_PLANNED" for event in timeline)
        assert sum(event.event_type == "PICK_EFFECT" for event in timeline) == 1
        runtime_events = [event.event_type for event in engine.runtime.events(command.command_id)]
        if product.sku == "SKU-A":
            assert "TOOL_CHANGE_NOT_REQUIRED" in runtime_events
        else:
            assert (
                "TOOL_CHANGE_REQUESTED" in runtime_events
                and "TOOL_CHANGE_COMPLETED" in runtime_events
            )
            assert runtime_events.index("TOOL_CHANGE_COMPLETED") < runtime_events.index(
                "PICK_EFFECT"
            )
        current = engine.runtime.world()
        assert current.tool_state.active_tool_id == current.robot_state.active_tool_id == selected
        assert len(current.tool_state.rack_tool_ids) == 5
        assert selected not in current.tool_state.rack_tool_ids
        moved = next(obj for obj in current.objects if obj.product.product_id == product.product_id)
        assert moved.location_id == engine.settings.destination_id
        assert moved.pose == fixture_target_pose(product.sku)
        receipt = engine.runtime.recorded_journal(command.command_id)
        assert receipt.effect_count == 1 and receipt.payload_hash == digest(command)
        assert receipt.active_tool_id == selected
    assert len(set(command_ids)) == 6 and effects(engine) == 6
    assert len({obj.pose.position for obj in engine.runtime.world().objects}) == 6
    restarted = Engine(Store(engine.store.path), SyntheticRuntime(engine.runtime.db.path))
    assert restarted.settings.is_hkm
    assert restarted.runtime.world().tool_state == engine.runtime.world().tool_state
    assert restarted.runtime.world().robot_state == engine.runtime.world().robot_state
    assert restarted.recover() == []
    assert effects(restarted) == 6
    measured = metrics(restarted)
    for name, expected_count in {
        "orders_total": 6,
        "jobs_completed_total": 6,
        "commands_total": 6,
        "pick_effects_total": 6,
        "tool_changes_total": 5,
        "tool_selection_failures_total": 0,
        "trajectory_plans_total": 6,
        "trajectory_rejections_total": 0,
        "collision_preflight_failures_total": 0,
        "observations_total": 12,
        "simulated_motion_duration_s_count": 6,
        "pipeline_latency_ms_count": 6,
    }.items():
        assert measured["robotops_" + name] == expected_count
    assert measured["robotops_simulated_motion_duration_s_sum"] == pytest.approx(
        sum(motion_durations)
    )
    assert measured["robotops_pipeline_latency_ms_sum"] > 0
    assert measured["robotops_pipeline_latency_ms_sum"] == pytest.approx(
        measured["robotops_pipeline_latency_seconds_sum"] * 1000
    )


@pytest.mark.parametrize("restart", [False, True])
def test_hkm_lost_ack_after_effect_reconciles_original_command_exactly_once(tmp_path, restart):
    engine = system(tmp_path)
    job_id = create_job(engine)
    unknown = engine.run(job_id, Fault.DROP_ACK_AFTER_EFFECT)
    assert unknown.state == JobState.UNKNOWN_OUTCOME and effects(engine) == 1
    original_id = unknown.command_id
    assert engine.run(job_id).state == JobState.UNKNOWN_OUTCOME
    if restart:
        engine = Engine(Store(engine.store.path), SyntheticRuntime(engine.runtime.db.path))
        result = engine.recover()[0]
    else:
        result = engine.reconcile(job_id)
    assert result.state == JobState.COMPLETED and result.command_id == original_id
    command = engine.store.load(RobotCommand, original_id)
    assert engine.runtime.apply(command).effect_count == 1
    assert effects(engine) == 1
    assert len(engine.store.orders()) == 1
    with engine.store.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 1
        assert (
            db.execute("SELECT COUNT(*) FROM records WHERE kind='RobotCommand'").fetchone()[0] == 1
        )
    with engine.runtime.db.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM controller_journal").fetchone()[0] == 1
    events = engine.store.timeline(result.order_id)
    assert sum(event.event_type == "COMMAND_INTENT" for event in events) == 1
    assert any(event.state_after == "UNKNOWN_OUTCOME" for event in events)
    assert any(event.state_after == "RECONCILING" for event in events)
    assert any(
        event.event_type == "JOURNAL_QUERIED" and event.command_id == original_id
        for event in events
    )
    evidence = engine.store.records_for_job(ReconciliationEvidence, job_id)[0]
    assert evidence.command.command_id == original_id
    assert evidence.observation.captured_at >= evidence.receipt.timestamp
    assert evidence.verification.verdict == Verdict.VERIFIED_SUCCESS
    assert evidence.receipt.effect_count == 1
    measured = metrics(engine)
    for name in (
        "commands_total",
        "pick_effects_total",
        "command_timeouts_total",
        "jobs_unknown_outcome_total",
        "reconciliations_success_total",
    ):
        assert measured["robotops_" + name] == 1
    assert measured["robotops_reconciliations_inconclusive_total"] == 0


def test_hkm_lost_ack_before_effect_uses_fresh_evidence_and_never_changes_tool(tmp_path):
    engine = system(tmp_path)
    before = engine.runtime.world()
    job_id = create_job(engine)
    unknown = engine.run(job_id, Fault.DROP_ACK_BEFORE_EFFECT)
    assert unknown.state == JobState.UNKNOWN_OUTCOME and effects(engine) == 0
    result = engine.reconcile(job_id)
    assert result.state == JobState.FAILED and result.command_id == unknown.command_id
    assert engine.runtime.world().objects == before.objects
    assert engine.runtime.world().tool_state == before.tool_state
    assert effects(engine) == 0


@pytest.mark.parametrize(
    "fault",
    [
        Fault.CONTRADICTORY_OBSERVATION,
        Fault.LOW_CONFIDENCE_OBSERVATION,
        Fault.STALE_OBSERVATION,
        Fault.MISSING_OBSERVATION,
        Fault.POSE_UNCERTAINTY,
    ],
)
def test_hkm_ambiguous_evidence_remains_intervention_until_fresh_same_command_review(
    tmp_path, fault
):
    engine = system(tmp_path)
    job_id = create_job(engine)
    unknown = engine.run(job_id, Fault.DROP_ACK_AFTER_EFFECT)
    result = engine.reconcile(job_id, fault)
    assert result.state == JobState.REQUIRES_INTERVENTION
    assert result.command_id == unknown.command_id and effects(engine) == 1
    first = engine.store.records_for_job(ReconciliationEvidence, job_id)[0]
    assert first.verification.verdict == Verdict.INCONCLUSIVE
    assert first.receipt.effect_count == 1
    restarted = Engine(Store(engine.store.path), SyntheticRuntime(engine.runtime.db.path))
    assert restarted.recover() == []
    resolved = restarted.reconcile(job_id)
    assert resolved.state == JobState.COMPLETED and resolved.command_id == unknown.command_id
    attempts = restarted.store.records_for_job(ReconciliationEvidence, job_id)
    assert len(attempts) == 2 and attempts[0] == first
    assert attempts[1].verification.verdict == Verdict.VERIFIED_SUCCESS
    assert effects(restarted) == 1
    measured = metrics(restarted)
    assert measured["robotops_reconciliations_total"] == 2
    assert measured["robotops_reconciliations_inconclusive_total"] == 1
    assert measured["robotops_reconciliations_success_total"] == 1
    assert measured["robotops_jobs_intervention_total"] == 1
    for observation_fault, name in (
        (Fault.LOW_CONFIDENCE_OBSERVATION, "observations_low_confidence_total"),
        (Fault.STALE_OBSERVATION, "observations_stale_total"),
        (Fault.CONTRADICTORY_OBSERVATION, "observations_contradictory_total"),
    ):
        assert measured["robotops_" + name] == int(fault == observation_fault)


def test_hkm_duplicate_order_and_payload_conflict_do_not_add_robot_effects(tmp_path):
    engine = system(tmp_path)
    client = TestClient(create_app(engine.store, engine))
    request = request_for(engine)
    headers = {"Idempotency-Key": "hkm-api-key"}
    first = client.post("/orders", json=request.model_dump(mode="json"), headers=headers)
    assert first.status_code == 201
    job_id = first.json()["job_ids"][0]
    assert client.post(f"/jobs/{job_id}/run", json={}).json()["state"] == "COMPLETED"
    duplicate = client.post("/orders", json=request.model_dump(mode="json"), headers=headers)
    assert duplicate.json()["job_ids"] == [job_id] and duplicate.json()["status"] == "COMPLETED"
    changed = request_for(engine, "SKU-C", request.order_id)
    assert (
        client.post("/orders", json=changed.model_dump(mode="json"), headers=headers).status_code
        == 409
    )
    assert len(engine.store.orders()) == 1 and effects(engine) == 1
    command = engine.store.load(RobotCommand, engine.store.job(job_id).command_id)
    engine.runtime.apply(command)
    with pytest.raises(Conflict, match="COMMAND_ID_PAYLOAD_CONFLICT"):
        engine.runtime.apply(command.model_copy(update={"causation_id": "changed-payload"}))
    assert effects(engine) == 1


@pytest.mark.parametrize(
    "failure", ["unavailable", "wrong_pair", "workspace", "calibration", "trajectory", "collision"]
)
def test_hkm_defensive_machine_boundary_blocks_invalid_execution_before_transfer(tmp_path, failure):
    engine = system(tmp_path)
    command = prepared_command(engine, "SKU-D" if failure == "wrong_pair" else "SKU-B")
    original = engine.runtime.world()
    if failure == "unavailable":
        state = original.tool_state.model_copy(
            update={
                "rack_tool_ids": tuple(
                    tool
                    for tool in original.tool_state.rack_tool_ids
                    if tool != command.required_tool_id
                )
            }
        )
        with engine.runtime.db.transaction() as db:
            engine.runtime._write_world(db, original.model_copy(update={"tool_state": state}))
    elif failure == "wrong_pair":
        choice = "EE_VAC_SINGLE"
        candidates = tuple(
            candidate.model_copy(update={"eligible": True})
            if candidate.tool_id == choice
            else candidate
            for candidate in command.tool_selection.candidate_tools
        )
        decision = command.tool_selection.model_copy(
            update={"selected_tool_id": choice, "candidate_tools": candidates}
        )
        command = command.model_copy(
            update={
                "required_tool_id": choice,
                "selected_tool_id": choice,
                "tool_selection": decision,
                "trajectory": command.trajectory.model_copy(update={"required_tool_id": choice}),
            }
        )
    elif failure == "workspace":
        command = command.model_copy(
            update={"target_pose": command.target_pose.model_copy(update={"position": (2, 0, 0.5)})}
        )
    elif failure == "calibration":
        command = command.model_copy(
            update={
                "target_pose": command.target_pose.model_copy(
                    update={"calibration_version": "stale-calibration"}
                )
            }
        )
    elif failure == "trajectory":
        points = command.trajectory.waypoints
        altered = points[0].model_copy(
            update={"pose": points[0].pose.model_copy(update={"position": (0.05, -0.6, 1.02)})}
        )
        command = command.model_copy(
            update={
                "trajectory": command.trajectory.model_copy(
                    update={"waypoints": (altered,) + points[1:]}
                )
            }
        )
    elif failure == "collision":
        moving = next(
            obj for obj in original.objects if obj.product.product_id == command.product_id
        )
        objects = tuple(
            obj.model_copy(update={"pose": moving.pose}) if obj.product.sku == "SKU-F" else obj
            for obj in original.objects
        )
        with engine.runtime.db.transaction() as db:
            engine.runtime._write_world(db, original.model_copy(update={"objects": objects}))
    before = engine.runtime.world()
    if failure == "calibration":
        with pytest.raises(ValueError):
            engine.runtime.apply(command)
    else:
        receipt = engine.runtime.apply(command)
        assert receipt.status == CommandStatus.REJECTED and receipt.effect_count == 0
    assert effects(engine) == 0
    assert engine.runtime.world().objects == before.objects
    assert engine.runtime.world().tool_state == before.tool_state


def test_hkm_two_workers_and_duplicate_delivery_retain_single_command_effect(tmp_path):
    engine = system(tmp_path)
    job_id = create_job(engine)

    def worker(_):
        return Engine(Store(engine.store.path), SyntheticRuntime(engine.runtime.db.path)).run(
            job_id
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(worker, range(2)))
    assert engine.store.job(job_id).state == JobState.COMPLETED and effects(engine) == 1


def test_hkm_repeated_fixtures_have_identical_semantic_decisions_and_outcomes(tmp_path):
    results = []
    for index in range(2):
        engine = system(tmp_path / str(index))
        job = engine.run(create_job(engine, "SKU-F"))
        plan = engine.store.load(ActionPlan, job.action_plan_id)
        results.append(
            (
                job.state,
                plan.selected_tool_id,
                plan.tool_selection.candidate_tools,
                plan.trajectory,
                tuple(obj.pose for obj in engine.runtime.world().objects),
                effects(engine),
            )
        )
    assert results[0] == results[1]
