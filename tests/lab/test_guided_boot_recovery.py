"""Controller boot changes renew checks/consent only before dispatch intent."""

from datetime import timedelta

import pytest

from robotops.cell.runtime import SyntheticRuntime
from robotops.domain.models import JobState, utc_now
from robotops.integration.engine import GuidedEngine
from robotops.integration.models import AuthorizeStage, CreateSession
from robotops.lab.postgres import PostgreSQLStore
from robotops.lab.transport import EdgeAdapter, LabBridge
from robotops.workflow.engine import Engine
from robotops.workflow.store import Conflict

pytestmark = pytest.mark.lab_integration


@pytest.fixture
def guided(lab_config, tmp_path):
    runtime = SyntheticRuntime(tmp_path / "runtime.db")
    workflow = Engine(PostgreSQLStore(lab_config.postgres_dsn, tmp_path / "app.db"), runtime)
    workflow.lab = LabBridge(lab_config, runtime)
    return GuidedEngine(workflow)


def authorize(guided, session):
    if session.current_stage == 11:
        EdgeAdapter(guided.lab.config).consume_one()
    return guided.authorize(
        session.session_id,
        AuthorizeStage(
            request_id=f"advance:{session.revision}",
            expected_revision=session.revision,
            stage=session.current_stage,
        ),
    )


def ready(guided, order_request):
    session = guided.create(CreateSession(request=order_request, request_id="boot-change"))
    while session.current_stage < 16:
        session = authorize(guided, session)
        assert session.status == "WAITING_AUTHORIZATION", session.model_dump_json()
    return session


def reconcile(guided, session):
    return guided.reconcile(
        session.session_id,
        AuthorizeStage(
            request_id=f"recover:{session.revision}",
            expected_revision=session.revision,
            stage=session.current_stage,
        ),
    )


def test_boot_change_before_dispatch_rechecks_then_requires_renewed_physical_consent(
    guided, order_request
):
    session = ready(guided, order_request)
    command_id = session.command_id
    old_boot = guided.lab.status(command_id)["boot_id"]
    guided.lab.restart()
    session = authorize(guided, session)
    assert session.status == "RETRYABLE_FAILURE" and session.current_stage == 14
    assert session.context["physical_authorized"] is False
    assert session.steps[-1].output["dispatch_intent_committed"] is False
    assert session.steps[-1].output["controller_status"]["boot_id"] != old_boot
    assert guided.workflow.store.job(session.job_id).state == JobState.READY_TO_EXECUTE
    assert guided.workflow.runtime.recorded_journal(command_id) is None
    assert guided.workflow.runtime.world().step == 0
    assert all(event.reason != "DISPATCH_INTENT" for event in guided.workflow.store.timeline())
    session = authorize(guided, session)
    assert session.current_stage == 15
    assert session.pending_authorization.label == "AUTHORIZE ROBOT EXECUTION"
    assert session.context["physical_authorized"] is False
    session = authorize(guided, session)
    assert session.current_stage == 16 and session.command_id == command_id
    assert guided.workflow.runtime.world().step == 0
    session = authorize(guided, session)
    assert session.current_stage == 17
    assert guided.workflow.runtime.recorded_journal(command_id).effect_count == 1
    assert guided.workflow.runtime.world().step == 1


def test_boot_change_after_dispatch_intent_remains_uncertain_without_repeat(
    guided, order_request, monkeypatch
):
    session = ready(guided, order_request)
    original = guided.lab.authorize_execute

    def restart_after_preflight(command_id, callback):
        guided.lab.restart()
        return original(command_id, callback)

    monkeypatch.setattr(guided.lab, "authorize_execute", restart_after_preflight)
    session = authorize(guided, session)
    assert session.status == "UNKNOWN_OUTCOME" and session.current_stage == 16
    assert guided.workflow.store.job(session.job_id).state == JobState.EXECUTING
    assert guided.workflow.runtime.recorded_journal(session.command_id) is None
    monkeypatch.setattr(guided.lab, "authorize_execute", original)
    recovered = reconcile(guided, session)
    assert recovered.status == "UNKNOWN_OUTCOME"
    assert guided.workflow.store.job(session.job_id).state == JobState.REQUIRES_INTERVENTION
    assert recovered.context["reconciliation"]["physical_resend"] is False
    with pytest.raises(Conflict, match="NOT_WAITING_AUTHORIZATION"):
        authorize(guided, recovered)
    assert guided.workflow.runtime.world().step == 0
    assert guided.lab.status(session.command_id)["state"] == "READY"


def test_interrupted_unstarted_lab_dispatch_returns_to_preconditions(
    guided, order_request, monkeypatch
):
    session = ready(guided, order_request)

    def interrupted(*args):
        raise SystemExit("Process stopped before dispatch handler")

    monkeypatch.setattr(guided, "_execute", interrupted)
    with pytest.raises(SystemExit):
        authorize(guided, session)
    saved = guided.store.get(session.session_id).model_copy(
        update={"updated_at": utc_now() - timedelta(hours=1)}
    )
    with guided.workflow.store.transaction() as db:
        db.execute(
            "UPDATE execution_sessions SET body=? WHERE id=?",
            (saved.model_dump_json(), saved.session_id),
        )
    guided.lab.restart()
    recovered = reconcile(guided, saved)
    assert recovered.current_stage == 14
    assert recovered.status == "WAITING_AUTHORIZATION"
    assert recovered.context["physical_authorized"] is False
    assert guided.workflow.runtime.world().step == 0
    assert guided.workflow.runtime.recorded_journal(session.command_id) is None
