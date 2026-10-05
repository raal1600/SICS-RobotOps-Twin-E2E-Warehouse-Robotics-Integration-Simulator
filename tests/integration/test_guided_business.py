"""Verified robot work, WMS ACK and ERP completion are distinct durable facts."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.app import create_app
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.domain.models import Fault, JobState, OrderLine, OrderRequest, stable_id
from robotops.integration.engine import GuidedEngine
from robotops.integration.models import AuthorizeStage, CreateSession
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def guided(tmp_path):
    store = Store(tmp_path / "app.db")
    return GuidedEngine(Engine(store, SyntheticRuntime(tmp_path / "runtime.db", Settings())))


def advance(guided, session):
    return guided.authorize(
        session.session_id,
        AuthorizeStage(
            request_id=f"advance:{session.revision}",
            expected_revision=session.revision,
            stage=session.current_stage,
        ),
    )


def reach(guided, session, stage):
    for _ in range(80):
        if session.current_stage == stage:
            return session
        session = advance(guided, session)
        assert session.status == "WAITING_AUTHORIZATION", session.model_dump_json()
    raise AssertionError(f"Stage {stage} not reached")


def test_wms_outage_cannot_complete_erp_order_before_business_stage(guided, order_request):
    session = guided.create(
        CreateSession(request=order_request, request_id="business", fault="WMS_UNAVAILABLE")
    )
    session = reach(guided, session, 20)
    assert guided.workflow.store.job(session.job_id).state == JobState.COMPLETED
    assert guided.workflow.store.order(session.order_id).status == JobState.RECONCILING
    session = advance(guided, session)
    assert session.status == "RETRYABLE_FAILURE"
    with TestClient(
        create_app(guided.workflow.store, guided.workflow, test_registry=False)
    ) as client:
        order = client.get(f"/orders/{session.order_id}").json()
        assert order["status"] == "RECONCILING"
        assert client.get("/orders").json()[0]["status"] == "RECONCILING"
    session = advance(guided, session)
    assert session.current_stage == 21 and session.context["wms_ack"] is True
    assert guided.workflow.store.order(session.order_id).status == JobState.RECONCILING
    session = advance(guided, session)
    assert guided.workflow.store.order(session.order_id).status == JobState.COMPLETED
    assert session.steps[-1].state_before == "RECONCILING"
    assert session.steps[-1].state_after == "COMPLETED"
    assert session.steps[-1].output["business_status"] == "COMPLETED"
    events = guided.workflow.store.timeline(session.order_id)
    assert len([event for event in events if event.event_type == "ERP_BUSINESS_COMPLETED"]) == 1
    assert guided.workflow.runtime.recorded_journal(session.command_id).effect_count == 1
    restarted = Store(guided.workflow.store.path)
    assert restarted.order(session.order_id).status == JobState.COMPLETED


def test_erp_completion_requires_durable_acknowledgement_for_every_order_line(guided):
    request = OrderRequest(
        order_id="multi-business",
        lines=tuple(
            OrderLine(
                order_line_id=f"line-{colour}",
                product_id=f"product-{colour}",
                source_id="source",
                destination_id="destination",
            )
            for colour in ("red", "blue")
        ),
    )
    session = reach(
        guided, guided.create(CreateSession(request=request, request_id="multi-business")), 21
    )
    assert len(session.job_ids) == 2
    assert guided.workflow.store.order(session.order_id).status == JobState.RECONCILING
    # A context boolean cannot replace a committed acknowledgement for an earlier line.
    missing_ack = stable_id(session.session_id, f"stage:20:{session.job_ids[0]}")
    with guided.workflow.store.transaction() as db:
        db.execute("DELETE FROM integration_effects WHERE id=?", (missing_ack,))
    session = advance(guided, session)
    assert session.status == "RETRYABLE_FAILURE" and session.current_stage == 21
    assert session.steps[-1].output["error"] == "DURABLE_WMS_ACKNOWLEDGEMENT_REQUIRED_FOR_EVERY_JOB"
    assert guided.workflow.store.order(session.order_id).status == JobState.RECONCILING
    for job_id in session.job_ids:
        command_id = guided.workflow.store.job(job_id).command_id
        assert guided.workflow.runtime.recorded_journal(command_id).effect_count == 1


def test_verified_physical_failure_is_not_erp_failure_until_business_ack(guided, order_request):
    session = reach(
        guided,
        guided.create(
            CreateSession(
                request=order_request,
                request_id="physical-failure",
                fault=Fault.ROBOT_COMMAND_FAILURE.value,
            )
        ),
        20,
    )
    assert guided.workflow.store.job(session.job_id).state == JobState.FAILED
    assert guided.workflow.store.order(session.order_id).status == JobState.RECONCILING
    session = advance(guided, session)
    assert guided.workflow.store.order(session.order_id).status == JobState.RECONCILING
    session = advance(guided, session)
    assert session.steps[-1].output["business_status"] == "FAILED"
    assert guided.workflow.store.order(session.order_id).status == JobState.FAILED
    assert guided.workflow.runtime.recorded_journal(session.command_id).effect_count == 0


def test_business_receipt_order_marker_and_audit_event_commit_atomically(
    guided, order_request, monkeypatch
):
    session = reach(
        guided, guided.create(CreateSession(request=order_request, request_id="atomic")), 21
    )
    original = guided.workflow.store._event

    def interrupted(db, event):
        if event.event_type == "ERP_BUSINESS_COMPLETED":
            raise OSError("business commit interrupted")
        return original(db, event)

    monkeypatch.setattr(guided.workflow.store, "_event", interrupted)
    session = advance(guided, session)
    assert session.status == "RETRYABLE_FAILURE"
    assert guided.workflow.store.order(session.order_id).status == JobState.RECONCILING
    with guided.workflow.store.connect() as db:
        assert (
            db.execute(
                "SELECT 1 FROM integration_effects WHERE kind='ERP_BUSINESS_STATUS'"
            ).fetchone()
            is None
        )
    monkeypatch.setattr(guided.workflow.store, "_event", original)
    session = advance(guided, session)
    assert guided.workflow.store.order(session.order_id).status == JobState.COMPLETED
    assert guided.workflow.runtime.recorded_journal(session.command_id).effect_count == 1


@pytest.mark.parametrize("fault", [None, Fault.DROP_ACK_AFTER_EFFECT.value])
def test_every_displayed_source_symbol_actually_executed_and_excerpt_matches_file(
    guided, order_request, fault
):
    session = guided.create(CreateSession(request=order_request, request_id="sources", fault=fault))
    for _ in range(30):
        calls = set()

        def profile(frame, event, arg, calls=calls):
            if event == "call":
                path = Path(frame.f_code.co_filename)
                if path.is_absolute() and path.is_relative_to(ROOT):
                    calls.add((path.relative_to(ROOT).as_posix(), frame.f_code.co_qualname))

        previous = sys.getprofile()
        sys.setprofile(profile)
        try:
            if session.status == "UNKNOWN_OUTCOME":
                session = guided.reconcile(
                    session.session_id,
                    AuthorizeStage(
                        request_id=f"reconcile:{session.revision}",
                        expected_revision=session.revision,
                        stage=session.current_stage,
                    ),
                )
            else:
                session = advance(guided, session)
        finally:
            sys.setprofile(previous)
        step = session.steps[-1]
        source = step.source
        assert (source.path, source.symbol) in calls, (step.stage, source, calls)
        actual_lines = [line.strip() for line in (ROOT / source.path).read_text().splitlines()]
        excerpt_lines = [line.strip() for line in source.excerpt.splitlines()]
        assert excerpt_lines and any(
            actual_lines[index : index + len(excerpt_lines)] == excerpt_lines
            for index in range(len(actual_lines))
        ), (step.stage, source)
        if session.status == "COMPLETED":
            break
    assert session.status == "COMPLETED"
