"""Guided boundaries prove persisted authorization, conservative recovery, and no read effects."""

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from apps.api.app import create_app, create_workspace_app
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.domain.models import Fault, JobState
from robotops.integration.engine import GuidedEngine
from robotops.integration.models import AuthorizeStage, CreateSession
from robotops.integration.store import sanitize
from robotops.workflow.engine import Engine
from robotops.workflow.store import Conflict, Store


@pytest.fixture
def guided(tmp_path):
    store = Store(tmp_path / "app.db")
    engine = Engine(store, SyntheticRuntime(tmp_path / "runtime.db", Settings()))
    return GuidedEngine(engine)


def advance(guided, session):
    return guided.authorize(
        session.session_id,
        AuthorizeStage(
            request_id=f"approve-{session.revision}",
            expected_revision=session.revision,
            stage=session.current_stage,
        ),
    )


def until(guided, session, stage):
    for _ in range(80):
        if session.current_stage == stage or session.status == "COMPLETED":
            return session
        session = advance(guided, session)
        assert session.status == "WAITING_AUTHORIZATION", session.model_dump_json()
    raise AssertionError("did not reach stage")


def test_guided_authorization_is_bounded_durable_and_physically_gated(guided, order_request):
    session = guided.create(CreateSession(request=order_request, request_id="create"))
    assert guided.workflow.store.orders() == []
    assert session.current_stage == 1
    session = until(guided, session, 4)
    assert guided.workflow.store.orders() == []
    session = advance(guided, session)
    assert len(guided.workflow.store.orders()) == 1
    with pytest.raises(Conflict, match="GUIDED"):
        guided.workflow.run(session.job_id)
    session = until(guided, session, 15)
    assert guided.workflow.runtime.recorded_journal(session.command_id) is None
    assert guided.workflow.store.job(session.job_id).state == JobState.READY_TO_EXECUTE
    assert session.pending_authorization.label == "AUTHORIZE ROBOT EXECUTION"
    with guided.workflow.store.connect() as db:
        assert not db.in_transaction
        assert db.execute("SELECT state FROM integration_outbox").fetchone()[0] == "LOCAL_DELIVERED"
        assert db.execute("SELECT owner FROM lease").fetchone()[0] is None
    resumed = GuidedEngine(Engine(guided.workflow.store, guided.workflow.runtime))
    resumed.workflow.recover()
    assert resumed.get(session.session_id).revision == session.revision
    assert resumed.workflow.runtime.recorded_journal(session.command_id) is None
    session = advance(resumed, session)
    assert session.current_stage == 16
    assert resumed.workflow.runtime.recorded_journal(session.command_id) is None
    session = advance(resumed, session)
    assert resumed.workflow.runtime.recorded_journal(session.command_id).effect_count == 1
    session = until(resumed, session, 22)
    session = advance(resumed, session)
    assert session.status == "COMPLETED"
    assert len(session.steps) == 22
    assert [step.stage for step in session.steps] == list(range(1, 23))
    assert all(step.source.excerpt for step in session.steps)
    assert all(step.classification != "REAL PROTOCOL" for step in session.steps)
    assert resumed.workflow.store.order(session.order_id).status == JobState.COMPLETED


def test_revision_guard_and_double_click_are_idempotent(guided, order_request):
    session = guided.create(CreateSession(request=order_request, request_id="create"))
    request = AuthorizeStage(request_id="same", expected_revision=0, stage=1)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: guided.authorize(session.session_id, request), range(2)))
    current = guided.get(session.session_id)
    assert current.current_stage == 2
    assert len(current.steps) == 1
    assert all(result.current_stage in {1, 2} for result in results)
    with pytest.raises(Conflict, match="REVISION"):
        guided.authorize(session.session_id, request.model_copy(update={"request_id": "different"}))
    with pytest.raises(Conflict, match="IDEMPOTENCY"):
        guided.authorize(session.session_id, request.model_copy(update={"stage": 2}))
    assert (
        guided.create(CreateSession(request=order_request, request_id="create")).session_id
        == session.session_id
    )


@pytest.mark.parametrize(
    "fault,effects,outcome",
    [
        (Fault.DROP_ACK_AFTER_EFFECT, 1, JobState.COMPLETED),
        (Fault.DROP_ACK_BEFORE_EFFECT, 0, JobState.FAILED),
        (Fault.STALE_OBSERVATION, 1, JobState.COMPLETED),
        (Fault.MISSING_OBSERVATION, 1, JobState.COMPLETED),
    ],
)
def test_uncertain_run_queries_original_identity_and_never_repeats_effect(
    guided, order_request, fault, effects, outcome
):
    session = guided.create(
        CreateSession(request=order_request, request_id="create", fault=fault.value)
    )
    session = until(guided, session, 19)
    session = advance(guided, session)
    assert session.status == "UNKNOWN_OUTCOME"
    assert session.pending_authorization is None
    command_id = session.command_id
    request = AuthorizeStage(
        request_id="reconcile", expected_revision=session.revision, stage=session.current_stage
    )
    session = guided.reconcile(session.session_id, request)
    assert guided.reconcile(session.session_id, request).revision == session.revision
    assert session.command_id == command_id
    assert guided.workflow.store.job(session.job_id).state == outcome
    receipt = guided.workflow.runtime.recorded_journal(command_id)
    assert (receipt.effect_count if receipt else 0) == effects
    assert session.context["reconciliation"]["physical_resend"] is False
    assert (
        len(
            [
                event
                for event in guided.workflow.store.timeline(session.order_id)
                if event.event_type == "COMMAND_DISPATCHED" and event.component == "gateway"
            ]
        )
        == 1
    )


@pytest.mark.parametrize(
    "fault,failed_stage",
    [
        ("BROKER_TRANSIENT", 10),
        ("EDGE_TRANSIENT", 11),
        ("OPC_UA_DISCONNECT", 12),
        ("WMS_UNAVAILABLE", 20),
    ],
)
def test_transient_retries_only_current_safe_boundary(guided, order_request, fault, failed_stage):
    session = guided.create(CreateSession(request=order_request, request_id="create", fault=fault))
    session = until(guided, session, failed_stage)
    session = advance(guided, session)
    assert session.status == "RETRYABLE_FAILURE"
    assert session.current_stage == failed_stage
    session = advance(guided, session)
    assert session.status == "WAITING_AUTHORIZATION"
    session = until(guided, session, 22)
    session = advance(guided, session)
    assert session.status == "COMPLETED"
    assert guided.workflow.runtime.recorded_journal(session.command_id).effect_count == 1
    assert (
        len(
            [
                event
                for event in guided.workflow.store.timeline(session.order_id)
                if event.event_type == "COMMAND_DISPATCHED" and event.component == "gateway"
            ]
        )
        == 1
    )


def test_readonly_routes_and_stream_do_not_advance(guided, order_request):
    app = create_app(guided.workflow.store, guided.workflow, test_registry=False)
    with TestClient(app) as client:
        created = client.post(
            "/v1/wms/tasks",
            json={"request": order_request.model_dump(mode="json"), "request_id": "api"},
        )
        assert created.status_code == 202
        session = created.json()
        ident = session["session_id"]
        live_before = client.get(f"/integration/sessions/{ident}/live")
        assert live_before.status_code == 200
        assert live_before.json()["command_id"] is None
        assert live_before.json()["events"] == []
        assert client.get(f"/integration/sessions/{ident}").json() == session
        with client.websocket_connect(f"/integration/sessions/{ident}/stream") as socket:
            snapshot = socket.receive_json()
            socket.send_json({"authorize": True, "stage": 1})
            assert socket.receive_json()["read_only"] is True
            assert snapshot["revision"] == 0
        for _ in range(3):
            assert client.get(f"/integration/sessions/{ident}").json()["revision"] == 0
        assert client.get("/orders").json() == []
        assert (
            client.post(
                f"/integration/sessions/{ident}/authorize",
                json={"request_id": "a", "stage": 1, "expected_revision": 0},
            ).json()["current_stage"]
            == 2
        )
        waiting = until(guided, guided.get(ident), 15)
        persisted = guided.get(ident).model_dump_json()
        for _ in range(3):
            live = client.get(f"/integration/sessions/{ident}/live")
            assert live.json()["command_id"] == waiting.command_id
            assert live.json()["classification"] == "SIMULATED SYSTEM"
        assert guided.get(ident).model_dump_json() == persisted
        assert guided.workflow.runtime.recorded_journal(waiting.command_id) is None


@pytest.mark.parametrize("operation,close_code", [("clear", 4409), ("delete", 4404)])
@pytest.mark.parametrize("scoped", [False, True])
def test_active_stream_closes_when_world_is_cleared_or_deleted(
    tmp_path, order_request, operation, close_code, scoped
):
    app = create_workspace_app(tmp_path, settings=Settings())
    with TestClient(app) as client:
        identity = "original"
        if scoped:
            new_test = client.post(
                "/simulation-tests",
                json={"request_id": str(uuid4()), "cell_profile_id": "hkm_inspired_v1"},
            )
            assert new_test.status_code == 201
            identity = new_test.json()["test_id"]
        prefix = f"/simulation-tests/{identity}" if scoped else ""
        directory = app.state.test_registry.directory(identity)
        created = client.post(
            prefix + "/v1/wms/tasks",
            json={"request": order_request.model_dump(mode="json"), "request_id": "watched"},
        )
        assert created.status_code == 202
        ident = created.json()["session_id"]
        with client.websocket_connect(prefix + f"/integration/sessions/{ident}/stream") as socket:
            assert socket.receive_json()["revision"] == 0
            body = {"request_id": str(uuid4())}
            if operation == "clear":
                body["expected_revision"] = 1
            response = client.post(f"/simulation-tests/{identity}/{operation}", json=body)
            assert response.status_code == 200, response.text
            with pytest.raises(WebSocketDisconnect) as closed:
                socket.receive_json()
            assert closed.value.code == close_code
        if operation == "delete":
            assert not (directory / "workflow.db").exists()
            assert not (directory / "runtime.db").exists()
        else:
            assert client.get(prefix + "/integration/sessions").json() == []
            assert client.get(prefix + "/orders").json() == []
        assert client.get(prefix + f"/integration/sessions/{ident}").status_code == 404
        if operation == "delete":
            assert not (directory / "workflow.db").exists()


def test_trace_sanitization():
    assert sanitize(
        {
            "password": "supersecret",
            "endpoint": "amqp://me:pass@host/path",
            "nested": {"Authorization": "secret"},
        }
    ) == {
        "password": "[REDACTED]",
        "endpoint": "amqp://[REDACTED]@host/path",
        "nested": {"Authorization": "[REDACTED]"},
    }


def test_trace_sanitizes_exception_text_headers_and_credentials(guided, order_request, monkeypatch):
    secret = "UNIQUE-SYNTHETIC-SECRET-123"
    payload = {
        "api_key": secret,
        "x-api-key": secret,
        "credentials": {"username": "test", "value": secret},
        "private-key": secret,
        "access_key": secret,
        "idempotency_key": "public-operation-1",
        "wire": f"postgres://user:{secret}@localhost/db?api_key={secret}&token={secret}",
        "exception": f"password='{secret}' Authorization: Bearer {secret}",
        "pem": "-----BEGIN " + f"PRIVATE KEY-----\n{secret}\n-----END PRIVATE KEY-----",
    }
    cleaned = sanitize(payload)
    assert secret not in str(cleaned)
    assert cleaned["idempotency_key"] == "public-operation-1"
    session = guided.create(CreateSession(request=order_request, request_id="secret-test"))
    monkeypatch.setattr(
        guided,
        "_execute",
        lambda *args: (_ for _ in ()).throw(
            OSError(f"postgres://user:{secret}@localhost/db password={secret}")
        ),
    )
    failed = advance(guided, session)
    assert secret not in failed.model_dump_json()
    assert secret not in guided.store.get(session.session_id).model_dump_json()


def test_guided_metrics_are_readonly_and_include_stage_attempts(guided, order_request):
    from robotops.observability.metrics import prometheus

    session = guided.create(CreateSession(request=order_request, request_id="metrics"))
    session = advance(guided, session)
    before = guided.get(session.session_id)
    metrics = prometheus(guided.workflow.store)
    assert 'robotops_guided_stage_duration_seconds_count{stage="1"} 1' in metrics
    assert 'robotops_guided_sessions_current{status="WAITING_AUTHORIZATION"} 1' in metrics
    assert guided.get(session.session_id) == before


def test_multiple_lines_require_each_physical_gate_and_acknowledgement(guided, order_request):
    from robotops.domain.models import OrderLine

    request = order_request.model_copy(
        update={
            "lines": (
                *order_request.lines,
                OrderLine(
                    order_line_id="line-2",
                    product_id="product-blue",
                    source_id="source",
                    destination_id="destination",
                ),
            )
        }
    )
    session = guided.create(CreateSession(request=request, request_id="multi"))
    session = until(guided, session, 22)
    session = advance(guided, session)
    assert session.status == "COMPLETED"
    assert len(session.job_ids) == 2
    gates = [step for step in session.steps if step.stage == 15]
    acknowledgements = [step for step in session.steps if step.stage == 20]
    assert len(gates) == len(acknowledgements) == 2
    assert len({step.job_id for step in gates}) == 2
    for job_id in session.job_ids:
        job = guided.workflow.store.job(job_id)
        assert job.state == JobState.COMPLETED
        assert guided.workflow.runtime.recorded_journal(job.command_id).effect_count == 1
    assert guided.workflow.store.order(session.order_id).status == JobState.COMPLETED
