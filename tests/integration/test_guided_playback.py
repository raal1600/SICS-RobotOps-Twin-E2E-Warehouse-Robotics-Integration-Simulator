"""Scenario labels come from saved job authority, never the current selector or runtime fault."""

import json

import pytest
from fastapi.testclient import TestClient

from apps.api.app import create_app
from apps.api.playback import execution_scenario
from robotops.cell.runtime import SyntheticRuntime
from robotops.domain.models import OrderLine
from robotops.integration.engine import GuidedEngine
from robotops.integration.models import AuthorizeStage, CreateSession
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store

LAB_SCENARIOS = [
    None,
    "DUPLICATE_DELIVERY",
    "BROKER_TRANSIENT",
    "EDGE_TRANSIENT",
    "OPC_UA_DISCONNECT",
    "PLC_RESTART",
    "WMS_UNAVAILABLE",
]


def intake(guided, request, fault):
    session = guided.create(CreateSession(request=request, request_id="saved", fault=fault))
    for _ in range(4):
        session = guided.authorize(
            session.session_id,
            AuthorizeStage(
                request_id=f"stage-{session.current_stage}",
                stage=session.current_stage,
                expected_revision=session.revision,
            ),
        )
    return session


@pytest.mark.parametrize("fault", LAB_SCENARIOS)
def test_playback_scenario_survives_reload_for_every_line_without_read_effects(
    tmp_path, order_request, fault
):
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
    store = Store(tmp_path / "workflow.db")
    runtime = SyntheticRuntime(tmp_path / "runtime.db")
    guided = GuidedEngine(Engine(store, runtime))
    session = intake(guided, request, fault)
    # The saved current job can move on; earlier lines still have their own authority link.
    saved = session.model_copy(update={"job_id": session.job_ids[1]})
    with store.transaction() as db:
        db.execute(
            "UPDATE execution_sessions SET body=? WHERE id=?",
            (saved.model_dump_json(), session.session_id),
        )
    reopened = Store(store.path)
    workflow = Engine(reopened, SyntheticRuntime(runtime.db.path))
    client = TestClient(create_app(reopened, workflow, test_registry=False))
    before = guided.store.get(session.session_id).model_dump_json()
    world = runtime.world().model_dump_json()
    timeline = store.timeline(session.order_id)
    for job_id in session.job_ids:
        response = client.get(f"/jobs/{job_id}/playback")
        assert response.status_code == 200
        assert response.json()["execution_scenario"] == {
            "schema_version": "1.0",
            "source": "GUIDED_SESSION",
            "session_id": session.session_id,
            "fault": fault,
        }
        assert response.json()["recording"] is None
    assert guided.store.get(session.session_id).model_dump_json() == before
    assert runtime.world().model_dump_json() == world
    assert store.timeline(session.order_id) == timeline
    assert all(store.job(job).command_id is None for job in session.job_ids)
    # The helper uses read-only connections; obtaining metadata cannot bootstrap tables.
    with store.readonly_connect() as db:
        assert db.execute("SELECT COUNT(*) FROM execution_sessions").fetchone()[0] == 1


@pytest.mark.parametrize("damage", ["missing", "invalid", "different_order"])
def test_unavailable_saved_scenario_never_becomes_a_baseline(tmp_path, order_request, damage):
    store = Store(tmp_path / "workflow.db")
    workflow = Engine(store, SyntheticRuntime(tmp_path / "runtime.db"))
    guided = GuidedEngine(workflow)
    session = intake(guided, order_request, "DUPLICATE_DELIVERY")
    with store.transaction() as db:
        if damage == "missing":
            db.execute("DELETE FROM execution_sessions WHERE id=?", (session.session_id,))
        else:
            body = session.model_dump(mode="json")
            if damage == "invalid":
                body.pop("request")
            else:
                body["order_id"] = "a-different-order"
            db.execute(
                "UPDATE execution_sessions SET body=? WHERE id=?",
                (json.dumps(body), session.session_id),
            )
    assert execution_scenario(workflow, store.job(session.job_id)) is None


def test_legacy_playback_scenario_read_does_not_create_guided_schema(tmp_path, order_request):
    store = Store(tmp_path / "legacy.db")
    workflow = Engine(store, SyntheticRuntime(tmp_path / "runtime.db"))
    job = store.job(store.intake(order_request, "legacy").job_ids[0])
    assert execution_scenario(workflow, job) is None
    with store.readonly_connect() as db:
        assert (
            db.execute("SELECT name FROM sqlite_master WHERE name='execution_sessions'").fetchone()
            is None
        )
