"""Interrupted operations resume by persisted identity; physical work is never replayed."""

from datetime import timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from apps.api.app import create_app
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.domain.models import CellMode, Fault, JobState, WorldObservation, utc_now
from robotops.integration.engine import GuidedEngine
from robotops.integration.models import AuthorizeStage, CreateSession
from robotops.workflow.engine import Engine
from robotops.workflow.store import Conflict, Store


@pytest.fixture
def guided(tmp_path):
    store = Store(tmp_path / "app.db")
    return GuidedEngine(Engine(store, SyntheticRuntime(tmp_path / "runtime.db", Settings())))


def authorize(guided, session):
    return guided.authorize(
        session.session_id,
        AuthorizeStage(
            request_id=f"authorize:{session.revision}",
            expected_revision=session.revision,
            stage=session.current_stage,
        ),
    )


def reach(guided, session, stage):
    for _ in range(60):
        if session.current_stage == stage:
            return session
        session = authorize(guided, session)
        assert session.status == "WAITING_AUTHORIZATION", session.model_dump_json()
    raise AssertionError(f"Stage {stage} not reached")


def expired(guided, session):
    session = guided.store.get(session.session_id).model_copy(
        update={"updated_at": utc_now() - timedelta(hours=1)}
    )
    with guided.workflow.store.transaction() as db:
        db.execute(
            "UPDATE execution_sessions SET body=? WHERE id=?",
            (session.model_dump_json(), session.session_id),
        )
    return session


def recover(guided, session):
    return guided.reconcile(
        session.session_id,
        AuthorizeStage(
            request_id=f"recover:{session.revision}",
            expected_revision=session.revision,
            stage=session.current_stage,
        ),
    )


@pytest.mark.parametrize("stage", [*range(1, 16), *range(17, 23)])
def test_resume_after_nonphysical_operation_commits_before_session_checkpoint(
    guided, order_request, monkeypatch, stage
):
    session = guided.create(CreateSession(request=order_request, request_id="crash"))
    session = reach(guided, session, stage)
    original = guided._execute

    def interrupted(saved, context):
        original(saved, context)
        raise SystemExit("process died before session checkpoint")

    monkeypatch.setattr(guided, "_execute", interrupted)
    with pytest.raises(SystemExit):
        authorize(guided, session)
    snapshot = guided.store.get(session.session_id)
    assert snapshot.status == "EXECUTING_STAGE"
    # Reload/GET remains read-only even when the process that did the work died.
    restarted = GuidedEngine(Engine(guided.workflow.store, guided.workflow.runtime))
    assert restarted.get(session.session_id).revision == snapshot.revision
    with pytest.raises(Conflict, match="STILL_IN_PROGRESS"):
        recover(restarted, snapshot)
    assert restarted.store.get(session.session_id).revision == snapshot.revision
    session = recover(restarted, expired(restarted, snapshot))
    assert session.current_stage == min(stage + 1, 22)
    if stage != 22:
        session = reach(restarted, session, 22)
        session = authorize(restarted, session)
    assert session.status == "COMPLETED"
    assert restarted.workflow.runtime.recorded_journal(session.command_id).effect_count == 1
    sends = [
        event
        for event in restarted.workflow.store.timeline(session.order_id)
        if event.component == "gateway" and event.event_type == "COMMAND_DISPATCHED"
    ]
    assert len(sends) == 1


def test_partial_command_commit_recovers_original_command_without_reprepare(
    guided, order_request, monkeypatch
):
    session = reach(
        guided, guided.create(CreateSession(request=order_request, request_id="command")), 8
    )
    original = guided.workflow.store.transition

    def interrupted(job_id, target, reason, **kwargs):
        if target == JobState.READY_TO_EXECUTE:
            raise SystemExit("process died after command/outbox commit")
        return original(job_id, target, reason, **kwargs)

    monkeypatch.setattr(guided.workflow.store, "transition", interrupted)
    with pytest.raises(SystemExit):
        authorize(guided, session)
    job = guided.workflow.store.job(session.job_id)
    assert job.state == JobState.PLANNING and job.command_id is not None
    monkeypatch.setattr(guided.workflow.store, "transition", original)
    resumed = recover(guided, expired(guided, session))
    assert resumed.current_stage == 9 and resumed.command_id == job.command_id
    assert guided.workflow.store.job(job.job_id).state == JobState.READY_TO_EXECUTE
    assert guided.workflow.runtime.recorded_journal(job.command_id) is None


@pytest.mark.parametrize("after_effect", [False, True])
def test_interrupted_physical_stage_queries_or_renews_gate_never_dispatches(
    guided, order_request, monkeypatch, after_effect
):
    session = reach(
        guided, guided.create(CreateSession(request=order_request, request_id="physical")), 16
    )
    original = guided._execute

    def interrupted(saved, context):
        if after_effect:
            original(saved, context)
        raise SystemExit("process died during physical stage")

    monkeypatch.setattr(guided, "_execute", interrupted)
    with pytest.raises(SystemExit):
        authorize(guided, session)
    monkeypatch.setattr(guided, "_execute", original)
    session = expired(guided, session)
    sends_before = len(
        [e for e in guided.workflow.store.timeline() if e.event_type == "COMMAND_DISPATCHED"]
    )
    recovered = recover(guided, session)
    assert (
        len([e for e in guided.workflow.store.timeline() if e.event_type == "COMMAND_DISPATCHED"])
        == sends_before
    )
    receipt = guided.workflow.runtime.recorded_journal(recovered.command_id)
    if after_effect:
        assert recovered.current_stage == 20
        assert receipt.effect_count == 1
        assert recovered.context["reconciliation"]["physical_resend"] is False
    else:
        assert receipt is None
        assert recovered.current_stage == 15
        assert recovered.pending_authorization.label == "AUTHORIZE ROBOT EXECUTION"
        assert recovered.context["physical_authorized"] is False
    recovered = reach(guided, recovered, 22)
    recovered = authorize(guided, recovered)
    assert recovered.status == "COMPLETED"
    assert guided.workflow.runtime.recorded_journal(recovered.command_id).effect_count == 1


@pytest.mark.parametrize("fault", [Fault.BRAIN_TIMEOUT, Fault.BRAIN_INVALID_OUTPUT])
def test_planning_rejection_is_terminal_and_creates_no_command(guided, order_request, fault):
    session = guided.create(
        CreateSession(request=order_request, request_id="planning", fault=fault.value)
    )
    session = authorize(guided, reach(guided, session, 6))
    assert session.status == "FAILED"
    assert session.pending_authorization is None
    assert guided.workflow.store.job(session.job_id).state == JobState.FAILED
    assert guided.workflow.store.order(session.order_id).status == JobState.FAILED
    assert session.command_id is None and guided.workflow.runtime.world().step == 0


def test_human_review_outlasting_freshness_returns_to_real_observation(
    guided, order_request, monkeypatch
):
    session = reach(
        guided, guided.create(CreateSession(request=order_request, request_id="freshness")), 7
    )
    old_observation = guided.workflow.store.load(
        WorldObservation, session.context["pre_observation_id"]
    )
    with monkeypatch.context() as clock:
        clock.setattr(
            "robotops.brain.validation.utc_now",
            lambda: old_observation.captured_at + timedelta(minutes=1),
        )
        session = authorize(guided, session)
    assert session.current_stage == 5 and session.status == "RETRYABLE_FAILURE"
    assert "pre_observation_id" not in session.context
    session = authorize(guided, session)
    assert session.context["pre_observation_id"] != old_observation.observation_id
    session = reach(guided, session, 8)
    assert guided.workflow.runtime.world().step == 0


def test_local_plc_preconditions_reject_cell_change_before_physical_gate(guided, order_request):
    session = reach(
        guided, guided.create(CreateSession(request=order_request, request_id="precondition")), 14
    )
    guided.workflow.runtime.set_cell(CellMode.FAULTED, "test changed cell")
    session = authorize(guided, session)
    assert session.status == "RETRYABLE_FAILURE" and session.current_stage == 14
    assert session.steps[-1].output["error"] == "CELL_NOT_READY"
    assert guided.workflow.runtime.recorded_journal(session.command_id) is None


def test_legacy_reconciliation_endpoint_cannot_advance_guided_session(guided, order_request):
    session = guided.create(
        CreateSession(
            request=order_request, request_id="bypass", fault=Fault.DROP_ACK_AFTER_EFFECT.value
        )
    )
    session = reach(guided, session, 17)
    with TestClient(
        create_app(guided.workflow.store, guided.workflow, test_registry=False)
    ) as client:
        response = client.post(f"/jobs/{session.job_id}/reconcile", json={"fault": None})
    assert response.status_code == 409
    assert "GUIDED" in response.text
    assert guided.store.get(session.session_id).revision == session.revision
    assert guided.workflow.runtime.recorded_journal(session.command_id).effect_count == 1


def test_committed_dispatch_without_result_remains_uncertain_and_never_resends(
    guided, order_request, monkeypatch
):
    session = reach(
        guided, guided.create(CreateSession(request=order_request, request_id="intent")), 16
    )

    def interrupted(*args):
        raise SystemExit("process died after intent but before effect/result evidence")

    monkeypatch.setattr(guided.workflow.gateway, "send", interrupted)
    with pytest.raises(SystemExit):
        authorize(guided, session)
    assert guided.workflow.store.job(session.job_id).state == JobState.EXECUTING
    recovered = recover(guided, expired(guided, session))
    assert recovered.status == "UNKNOWN_OUTCOME"
    assert guided.workflow.store.job(session.job_id).state == JobState.REQUIRES_INTERVENTION
    assert guided.workflow.runtime.recorded_journal(session.command_id) is None
    assert guided.workflow.runtime.world().step == 0
    assert recovered.context["reconciliation"]["physical_resend"] is False


def test_injected_failure_before_network_has_truthful_wire_and_code_trace(guided, order_request):
    session = reach(
        guided,
        guided.create(
            CreateSession(request=order_request, request_id="wire", fault="BROKER_TRANSIENT")
        ),
        10,
    )

    def forbidden_publish(*args):
        raise AssertionError("injected outage must not claim or attempt broker traffic")

    guided.lab = SimpleNamespace(publish=forbidden_publish)
    failed = authorize(guided, session)
    step = failed.steps[-1]
    assert step.classification == "SIMULATED SYSTEM"
    assert step.output["network_attempted"] is False
    assert step.output["injected_failure"] is True
    assert step.source.symbol == "GuidedEngine._execute"
    assert "fault_for_stage" in step.source.excerpt


@pytest.mark.parametrize("fault", [None, "STALE_OBSERVATION"])
def test_reconciliation_idempotency_binds_observation_fault(guided, order_request, fault):
    session = guided.create(
        CreateSession(
            request=order_request, request_id="reconcile-fault", fault=Fault.DROP_ACK_AFTER_EFFECT
        )
    )
    session = reach(guided, session, 19)
    session = authorize(guided, session)
    assert session.status == "UNKNOWN_OUTCOME"
    request = {
        "request_id": "original-recovery",
        "expected_revision": session.revision,
        "fault": fault,
    }
    with TestClient(
        create_app(guided.workflow.store, guided.workflow, test_registry=False)
    ) as client:
        path = f"/integration/sessions/{session.session_id}/reconcile"
        first = client.post(path, json=request)
        assert first.status_code == 200
        repeated = client.post(path, json=request)
        assert repeated.status_code == 200
        assert repeated.json()["revision"] == first.json()["revision"]
        conflicting = client.post(
            path, json={**request, "fault": None if fault else "STALE_OBSERVATION"}
        )
        assert conflicting.status_code == 409
        assert conflicting.json()["reason"] == "AUTHORIZATION_IDEMPOTENCY_CONFLICT"
        assert client.get(path.removesuffix("/reconcile")).json() == first.json()
    assert guided.workflow.runtime.recorded_journal(session.command_id).effect_count == 1
