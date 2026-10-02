from concurrent.futures import ThreadPoolExecutor
from time import sleep

import pytest
from fastapi.testclient import TestClient

from apps.api.app import create_app
from robotops.brain.deterministic import DeterministicBrain
from robotops.cell.controller import CellController
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.domain.models import Fault, JobState, ReconciliationEvidence, RobotCommand
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


@pytest.fixture
def system(tmp_path, order_request):
    store = Store(tmp_path / "workflow.db")
    runtime = SyntheticRuntime(tmp_path / "runtime.db")
    engine = Engine(store, runtime)
    client = TestClient(create_app(store, engine))
    order = client.post(
        "/orders", json=order_request.model_dump(mode="json"), headers={"Idempotency-Key": "key"}
    ).json()
    return store, runtime, engine, client, order["job_ids"][0]


def effects(runtime):
    return sum(e.event_type == "PICK_EFFECT" for e in runtime.events())


def test_happy_path(system):
    store, runtime, engine, client, job_id = system
    response = client.post(f"/jobs/{job_id}/run", json={})
    assert response.status_code == 200 and response.json()["state"] == "COMPLETED"
    assert client.get("/orders/order-1").json()["status"] == "COMPLETED"
    assert runtime.world().objects[0].location_id == "destination"
    assert effects(runtime) == 1
    timeline = client.get("/orders/order-1/timeline").json()
    assert any(e["event_type"] == "PICK_EFFECT" for e in timeline)
    assert [e["state_after"] for e in timeline if e["event_type"] == "JOB_TRANSITION"] == [
        "VALIDATED",
        "PLANNING",
        "READY_TO_EXECUTE",
        "EXECUTING",
        "VERIFYING",
        "COMPLETED",
    ]
    assert len({e["correlation_id"] for e in timeline}) == 1
    ids = {e["event_id"] for e in timeline} | {"order-1"}
    assert all(e["causation_id"] in ids for e in timeline)


def test_lost_ack_after_effect(system):
    store, runtime, engine, client, job_id = system
    uncertain = engine.run(job_id, Fault.DROP_ACK_AFTER_EFFECT)
    assert uncertain.state == JobState.UNKNOWN_OUTCOME
    assert effects(runtime) == 1
    assert runtime.world().objects[0].location_id == "destination"
    command_id = uncertain.command_id
    assert engine.run(job_id).state == JobState.UNKNOWN_OUTCOME
    response = client.post(f"/jobs/{job_id}/reconcile", json={})
    assert response.status_code == 200 and response.json()["state"] == "COMPLETED"
    assert response.json()["command_id"] == command_id
    assert effects(runtime) == 1
    timeline = store.timeline("order-1")
    assert sum(e.event_type == "COMMAND_INTENT" for e in timeline) == 1
    assert any(e.event_type == "JOURNAL_QUERIED" and e.command_id == command_id for e in timeline)
    assert any(e.state_after == "RECONCILING" for e in timeline)
    event = next(e for e in timeline if e.event_type == "RECONCILIATION_RESULT")
    evidence = store.load(ReconciliationEvidence, event.evidence_ids[0])
    assert evidence.command.command_id == command_id
    assert evidence.observation.captured_at >= evidence.receipt.timestamp
    assert evidence.receipt.effect_count == 1


def test_lost_ack_before_effect(system):
    store, runtime, engine, client, job_id = system
    uncertain = engine.run(job_id, Fault.DROP_ACK_BEFORE_EFFECT)
    assert uncertain.state == JobState.UNKNOWN_OUTCOME
    assert effects(runtime) == 0
    result = engine.reconcile(job_id)
    assert result.state == JobState.FAILED
    assert result.command_id == uncertain.command_id
    assert effects(runtime) == 0
    assert runtime.world().objects[0].location_id == "source"


def test_restart_unknown_outcome(system):
    store, runtime, engine, client, job_id = system
    original = engine.run(job_id, Fault.DROP_ACK_AFTER_EFFECT)
    restarted = Engine(Store(store.path), SyntheticRuntime(runtime.db.path))
    assert restarted.recover()[0].state == JobState.COMPLETED
    assert restarted.store.job(job_id).command_id == original.command_id
    assert effects(runtime) == 1
    assert len(restarted.store.timeline()) > len([])


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
def test_ambiguous_reconciliation_never_fabricates_success(system, fault):
    store, runtime, engine, client, job_id = system
    assert engine.run(job_id, Fault.DROP_ACK_AFTER_EFFECT).state == JobState.UNKNOWN_OUTCOME
    result = engine.reconcile(job_id, fault)
    assert result.state == JobState.REQUIRES_INTERVENTION
    assert store.order("order-1").status == JobState.REQUIRES_INTERVENTION
    assert effects(runtime) == 1


@pytest.mark.parametrize(
    "fault",
    [Fault.CONTRADICTORY_OBSERVATION, Fault.LOW_CONFIDENCE_OBSERVATION, Fault.STALE_OBSERVATION],
)
def test_degraded_post_execution_observation_is_unknown(system, fault):
    store, runtime, engine, client, job_id = system
    assert engine.run(job_id, fault).state == JobState.UNKNOWN_OUTCOME
    assert effects(runtime) == 1


@pytest.mark.parametrize(
    "fault", [Fault.LOGICAL_ESTOP, Fault.CELL_FAULT, Fault.ROBOT_COMMAND_FAILURE]
)
def test_fault_and_logical_estop_block_effect(system, fault):
    store, runtime, engine, client, job_id = system
    assert engine.run(job_id, fault).state == JobState.FAILED
    assert effects(runtime) == 0
    assert any(e.reason == fault.value for e in store.timeline())


def test_reset_does_not_mark_unknown_success(system):
    store, runtime, engine, client, job_id = system
    engine.run(job_id, Fault.DROP_ACK_AFTER_EFFECT)
    CellController(runtime).fault()
    client.post("/cell/reset")
    assert store.job(job_id).state == JobState.UNKNOWN_OUTCOME
    assert engine.run(job_id).state == JobState.UNKNOWN_OUTCOME
    assert engine.reconcile(job_id).state == JobState.COMPLETED
    assert effects(runtime) == 1


@pytest.mark.parametrize("fault", [Fault.BRAIN_TIMEOUT, Fault.BRAIN_INVALID_OUTPUT])
def test_brain_failures_cannot_reach_gateway(system, fault):
    store, runtime, engine, client, job_id = system
    assert engine.run(job_id, fault).state == JobState.FAILED
    assert effects(runtime) == 0
    assert not runtime.events()
    assert not any(e.event_type == "COMMAND_DISPATCHED" for e in store.timeline())


def test_actual_slow_brain_timeout_discards_late_output(system):
    store, runtime, engine, client, job_id = system

    class SlowBrain(DeterministicBrain):
        def plan(self, *args):
            sleep(0.1)
            return super().plan(*args)

    engine = Engine(store, runtime, Settings(brain_timeout_seconds=0.001), brain=SlowBrain())
    assert engine.run(job_id).state == JobState.FAILED
    sleep(0.12)
    assert effects(runtime) == 0


def test_two_worker_claim_race_executes_once(system):
    store, runtime, engine, client, job_id = system

    def worker(_):
        return Engine(Store(store.path), SyntheticRuntime(runtime.db.path)).run(job_id)

    with ThreadPoolExecutor(2) as pool:
        list(pool.map(worker, range(2)))
    assert store.job(job_id).state == JobState.COMPLETED
    assert effects(runtime) == 1


def test_duplicate_robot_command_after_completed_job(system):
    store, runtime, engine, client, job_id = system
    completed = engine.run(job_id)
    command = store.load(RobotCommand, completed.command_id)
    engine.gateway.send(command)
    assert effects(runtime) == 1
    assert sum(e.event_type == "DUPLICATE_SUPPRESSED" for e in store.timeline()) == 1


def test_duplicate_order_same_payload_and_conflict_e2e(system, order_request):
    store, runtime, engine, client, job_id = system
    engine.run(job_id)
    same = client.post(
        "/orders", json=order_request.model_dump(mode="json"), headers={"Idempotency-Key": "key"}
    )
    assert same.json()["status"] == "COMPLETED"
    assert same.json()["job_ids"] == [job_id]
    assert (
        client.post(
            "/orders",
            json={**order_request.model_dump(mode="json"), "order_id": "changed"},
            headers={"Idempotency-Key": "key"},
        ).status_code
        == 409
    )
    engine.run(job_id)
    assert effects(runtime) == 1
