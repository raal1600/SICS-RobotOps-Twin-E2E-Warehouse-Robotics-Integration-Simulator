"""An operator can resolve a paused test through new evidence, never another pick."""

from concurrent.futures import ThreadPoolExecutor
from itertools import count
from threading import Event
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api.app import create_app
from robotops.blender.adapter import BlenderRuntime
from robotops.cell.runtime import SyntheticRuntime
from robotops.domain.models import Fault, JobState, OrderRequest
from robotops.faults.injection import OBSERVATION_FAULTS
from robotops.workflow.engine import Engine
from robotops.workflow.store import Conflict, Store


def system(path, runtime_type=SyntheticRuntime):
    store = Store(path / "workflow.db")
    runtime = runtime_type(path / "runtime.db")
    engine = Engine(store, runtime)
    return engine, TestClient(create_app(store, engine, recover=True))


def intake(client, request):
    response = client.post(
        "/orders",
        json=request.model_dump(mode="json"),
        headers={"Idempotency-Key": request.order_id},
    )
    assert response.status_code == 201, response.text
    return response.json()["job_ids"][0]


@pytest.mark.parametrize(
    "runtime_type", [SyntheticRuntime, pytest.param(BlenderRuntime, marks=pytest.mark.blender)]
)
@pytest.mark.parametrize("ack", [Fault.DROP_ACK_AFTER_EFFECT, Fault.DROP_ACK_BEFORE_EFFECT])
def test_reobserve_intervention_and_continue_same_delivery(
    tmp_path, order_request, runtime_type, ack, monkeypatch
):
    # IDs deliberately sort opposite to capture order. Latest evidence must be
    # selected by durable insertion order, never accidental UUID ordering.
    ids = count(1000, -1)
    monkeypatch.setattr("robotops.workflow.engine.new_id", lambda: f"record-{next(ids):04}")
    engine, client = system(tmp_path, runtime_type)
    job_id = intake(client, order_request)
    path = f"/jobs/{job_id}"
    job = client.post(path + "/run", json={"fault": ack}).json()
    assert job["state"] == "UNKNOWN_OUTCOME"
    command_id = job["command_id"]
    epoch = engine.runtime.world().scene_epoch
    expected_effects = int(ack == Fault.DROP_ACK_AFTER_EFFECT)
    blue_request = OrderRequest.model_validate(
        {
            "order_id": "order-blue",
            "lines": [{**order_request.lines[0].model_dump(), "product_id": "product-blue"}],
        }
    )
    blue_id = intake(client, blue_request)
    # Every degradation can be tried repeatedly on the SAME job. No fixture reset,
    # new world or replacement command is needed to obtain another observation.
    for fault in sorted(OBSERVATION_FAULTS):
        for _ in range(2):
            before = client.get(path + "/evidence").json()["reconciliations"]
            response = client.post(path + "/reconcile", json={"fault": fault})
            assert response.status_code == 200, response.text
            assert response.json()["state"] == "REQUIRES_INTERVENTION"
            assert response.json()["command_id"] == command_id
            evidence = client.get(path + "/evidence").json()
            assert evidence["reconciliations"][:-1] == before
            assert evidence["reconciliations"][-1]["verification"]["verdict"] == "INCONCLUSIVE"
            assert client.post(path + "/run", json={}).json()["state"] == "REQUIRES_INTERVENTION"
            assert client.post(f"/jobs/{blue_id}/run", json={}).json()["state"] == "RECEIVED"
            assert client.post("/fixtures/fresh-scene", json={}).status_code == 409
            assert (
                sum(e.event_type == "PICK_EFFECT" for e in engine.runtime.events())
                == expected_effects
            )

    # Restart and read-only review cannot silently clear intervention or collect
    # an undegraded observation. It requires another explicit operator request.
    saved = client.get(path + "/evidence").json()
    history = engine.store.timeline()
    engine, client = system(tmp_path, runtime_type)
    assert client.get(path + "/evidence").json() == saved
    assert engine.store.timeline() == history
    assert client.post("/cell/reset").status_code == 200
    assert client.get(path).json()["state"] == "REQUIRES_INTERVENTION"
    response = client.post(path + "/reconcile", json={})
    expected = "COMPLETED" if expected_effects else "FAILED"
    assert response.status_code == 200 and response.json()["state"] == expected
    assert response.json()["command_id"] == command_id
    assert client.get("/orders/order-1").json()["status"] == expected
    evidence = client.get(path + "/evidence").json()
    assert evidence["reconciliations"][:-1] == saved["reconciliations"]
    observations = [e["observation"] for e in evidence["reconciliations"]]
    assert len({o["observation_id"] for o in observations}) == len(observations)
    assert observations[-1]["captured_at"] >= observations[-2]["captured_at"]
    assert all(e["command"]["command_id"] == command_id for e in evidence["reconciliations"])
    assert engine.runtime.world().scene_epoch == epoch
    assert sum(e.event_type == "PICK_EFFECT" for e in engine.runtime.events()) == expected_effects
    events = engine.store.timeline("order-1")
    assert sum(e.event_type == "COMMAND_INTENT" for e in events) == 1
    # Gateway dispatch and controller delivery each log the same transport once.
    for component in ("gateway", "runtime"):
        assert (
            sum(e.event_type == "COMMAND_DISPATCHED" and e.component == component for e in events)
            == 1
        )
    assert sum(e.reason == "OPERATOR_REOBSERVATION" for e in events) == len(observations) - 1
    assert sum(e.event_type == "JOURNAL_QUERIED" for e in events) == len(observations)
    assert all(
        e.state_after == "RECONCILING"
        for e in events
        if e.event_type == "JOB_TRANSITION" and e.state_before == "REQUIRES_INTERVENTION"
    )
    assert client.post(path + "/reconcile", json={}).status_code == 409
    # The existing next order is now eligible, and both executions stay in this
    # delivery's replay. Re-observation adds events, never duplicate motion clips.
    assert client.post(f"/jobs/{blue_id}/run", json={}).json()["state"] == "COMPLETED"
    assert (
        sum(e.event_type == "PICK_EFFECT" for e in engine.runtime.events()) == expected_effects + 1
    )
    assert engine.runtime.world().scene_epoch == epoch
    delivery = client.get(f"/deliveries/{epoch}/playback").json()
    assert [j["job_id"] for j in delivery["jobs"]] == [job_id, blue_id]
    assert len(client.get("/simulation-tests").json()["tests"]) == 1


def test_intervention_reobservation_holds_claim_and_fences_other_workers(
    tmp_path, order_request, monkeypatch
):
    engine, client = system(tmp_path)
    job_id = intake(client, order_request)
    engine.run(job_id, Fault.DROP_ACK_AFTER_EFFECT)
    engine.reconcile(job_id, Fault.CONTRADICTORY_OBSERVATION)
    entered, finish = Event(), Event()
    observe = engine.observer.observe

    def delayed(*args):
        entered.set()
        assert finish.wait(10)
        return observe(*args)

    monkeypatch.setattr(engine.observer, "observe", delayed)
    other = Engine(Store(engine.store.path), SyntheticRuntime(engine.runtime.db.path))
    with ThreadPoolExecutor(1) as pool:
        pending = pool.submit(engine.reconcile, job_id)
        try:
            assert entered.wait(10)
            with pytest.raises(Conflict, match="JOB_OWNED_OR_CELL_QUARANTINED"):
                other.reconcile(job_id)
            assert other.run(job_id).state == JobState.REQUIRES_INTERVENTION
            assert other.store.claim(job_id, "unsafe-execution", 60) is None
        finally:
            finish.set()
        assert pending.result().state == JobState.COMPLETED
    assert len(engine.evidence(job_id).reconciliations) == 2
    assert sum(e.event_type == "PICK_EFFECT" for e in engine.runtime.events()) == 1


def test_archived_intervention_cannot_be_reobserved(tmp_path, order_request):
    engine, client = system(tmp_path)
    job_id = intake(client, order_request)
    engine.run(job_id, Fault.DROP_ACK_AFTER_EFFECT)
    engine.reconcile(job_id, Fault.CONTRADICTORY_OBSERVATION)
    saved = engine.evidence(job_id)
    client.post("/simulation-tests", json={"request_id": str(uuid4())})
    response = client.post(f"/jobs/{job_id}/reconcile", json={})
    assert response.status_code == 409
    assert response.json()["reason"] == "TEST_ARCHIVED_READ_ONLY"
    assert engine.evidence(job_id) == saved


def test_normal_reobservation_cannot_resolve_missing_journal(tmp_path, order_request, monkeypatch):
    engine, client = system(tmp_path)
    job_id = intake(client, order_request)
    engine.run(job_id, Fault.DROP_ACK_AFTER_EFFECT)
    engine.reconcile(job_id, Fault.CONTRADICTORY_OBSERVATION)
    with monkeypatch.context() as patch:
        patch.setattr(engine.runtime, "journal", lambda command_id: None)
        result = engine.reconcile(job_id)
        assert result.state == JobState.REQUIRES_INTERVENTION
        latest = engine.evidence(job_id).reconciliations[-1]
        assert latest.verification.reason == "JOURNAL_UNAVAILABLE"
        assert latest.receipt is None
    assert engine.reconcile(job_id).state == JobState.COMPLETED
    assert len(engine.evidence(job_id).reconciliations) == 3
    assert sum(e.event_type == "PICK_EFFECT" for e in engine.runtime.events()) == 1
