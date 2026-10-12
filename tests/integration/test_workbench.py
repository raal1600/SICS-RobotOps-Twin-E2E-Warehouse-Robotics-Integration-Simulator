"""Proof claims remain tied to original, persisted results across recovery."""

import pytest
from fastapi.testclient import TestClient

from apps.api.app import create_app
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.integration.engine import GuidedEngine
from robotops.integration.models import AuthorizeStage, CreateSession
from robotops.integration.presentation import project
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


@pytest.fixture
def guided(tmp_path):
    return GuidedEngine(
        Engine(Store(tmp_path / "app.db"), SyntheticRuntime(tmp_path / "runtime.db", Settings()))
    )


def advance(engine, session):
    return engine.authorize(
        session.session_id,
        AuthorizeStage(
            request_id=f"advance-{session.revision}",
            expected_revision=session.revision,
            stage=session.current_stage,
        ),
    )


def until(engine, session, stage):
    for _ in range(30):
        if session.current_stage == stage:
            return session
        session = advance(engine, session)
    raise AssertionError("Stage not reached")


def proofs(session):
    return {item["key"]: item for item in session.workbench["proofs"]}


def test_proof_ladder_does_not_infer_later_boundaries_or_real_broker(guided, order_request):
    session = guided.create(CreateSession(request=order_request, request_id="start"))
    assert all(p["state"] == "unproven" for p in proofs(session).values())
    session = until(guided, session, 15)
    assert session.pending_authorization.label == "AUTHORIZE ROBOT EXECUTION"
    evidence = proofs(session)
    assert evidence["broker"]["state"] == "simulated"
    assert evidence["controller"]["state"] == "established"
    assert evidence["execution"]["state"] == "unproven"
    assert evidence["verification"]["state"] == "unproven"
    session = until(guided, session, 18)
    assert proofs(session)["execution"]["state"] == "established"
    assert proofs(session)["verification"]["state"] == "unproven"
    session = until(guided, session, 20)
    assert proofs(session)["verification"]["state"] == "established"
    assert proofs(session)["wms"]["state"] == "unproven"
    assert proofs(session)["erp"]["state"] == "unproven"
    restored = guided.get(session.session_id)
    assert restored.workbench == session.workbench
    assert guided.store.get(session.session_id).workbench == {}
    for proof in proofs(restored).values():
        if proof["state"] == "established":
            step = next(s for s in restored.steps if s.step_id == proof["step_id"])
            assert step.evidence_ids and proof["field"].startswith("output")


@pytest.mark.parametrize("fault", ["DROP_ACK_AFTER_EFFECT", "WMS_UNAVAILABLE"])
def test_recovery_proof_and_identity_do_not_repeat_physical_work(guided, order_request, fault):
    session = guided.create(CreateSession(request=order_request, request_id="start", fault=fault))
    session = until(guided, session, 19)
    session = advance(guided, session)
    command = session.command_id
    if fault == "DROP_ACK_AFTER_EFFECT":
        assert session.workbench["status"] == "Robot outcome not yet proven"
        assert proofs(session)["verification"]["state"] == "unproven"
        assert session.pending_authorization is None
        session = guided.reconcile(
            session.session_id,
            AuthorizeStage(
                request_id="reconcile",
                expected_revision=session.revision,
                stage=session.current_stage,
            ),
        )
        assert proofs(session)["verification"]["state"] == "established"
        assert proofs(session)["verification"]["step_id"] == session.steps[-1].step_id
    else:
        session = advance(guided, session)
        assert session.workbench["status"] == "Business acknowledgement failed"
        assert proofs(session)["verification"]["state"] == "established"
        assert proofs(session)["wms"]["state"] == "failed"
        assert proofs(session)["erp"]["state"] == "unproven"
        assert session.pending_authorization.label == "Retry WMS acknowledgement"
    session = until(guided, session, 22)
    session = advance(guided, session)
    assert session.command_id == command
    assert guided.workflow.runtime.recorded_journal(command).effect_count == 1
    assert proofs(session)["erp"]["state"] == "established"


def test_missing_or_mismatched_records_and_other_jobs_never_establish_success(
    guided, order_request
):
    session = until(
        guided, guided.create(CreateSession(request=order_request, request_id="start")), 20
    )
    verification = session.steps[-1]
    for output in ({}, {**verification.output, "command_id": "another-command"}):
        changed = session.model_copy(
            update={
                "steps": (*session.steps[:-1], verification.model_copy(update={"output": output}))
            }
        )
        assert (
            next(p for p in project(changed)["proofs"] if p["key"] == "verification")["state"]
            == "unproven"
        )
    other = session.model_copy(update={"job_id": "another-job", "command_id": "another-command"})
    assert all(
        p["state"] == "unproven"
        for p in project(other)["proofs"]
        if p["key"] not in {"intent", "durable"}
    )


def test_export_is_readonly_sanitized_and_explicit_about_scope(guided, order_request):
    session = until(
        guided, guided.create(CreateSession(request=order_request, request_id="start")), 5
    )
    step = session.steps[-1].model_copy(
        update={
            "output": {
                "password": "must-not-leak",
                "url": "amqp://user:must-not-leak@example.invalid",
            }
        }
    )
    saved = guided.store.get(session.session_id).model_copy(
        update={"steps": (*session.steps[:-1], step)}
    )
    with guided.workflow.store.transaction() as db:
        db.execute(
            "UPDATE execution_sessions SET body=? WHERE id=?",
            (saved.model_dump_json(), saved.session_id),
        )
    with TestClient(create_app(guided.workflow.store, guided.workflow)) as client:
        response = client.get(f"/integration/sessions/{session.session_id}/export")
    assert response.status_code == 200
    assert "must-not-leak" not in response.text
    assert "not embedded" in response.json()["scope"]
    assert guided.get(session.session_id).revision == session.revision
    assert guided.workflow.runtime.world().step == 0


def test_failed_execution_request_is_uncertainty_not_proof_of_physical_failure(
    guided, order_request
):
    session = until(
        guided, guided.create(CreateSession(request=order_request, request_id="start")), 17
    )
    execution = session.steps[-1].model_copy(
        update={
            "status": "FAILED",
            "output": {"error": "connection lost after dispatch"},
            "state_after": "UNKNOWN_OUTCOME",
        }
    )
    unknown = session.model_copy(
        update={"steps": (*session.steps[:-1], execution), "status": "UNKNOWN_OUTCOME"}
    )
    proof = next(p for p in project(unknown)["proofs"] if p["key"] == "execution")
    assert proof["state"] == "unproven"
    assert "Do not retry the pick" in proof["fact"]
