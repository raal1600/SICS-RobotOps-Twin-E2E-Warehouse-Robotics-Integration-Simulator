"""Engineering inspection preserves execution authority and evidence provenance."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.app import create_app
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.integration.engine import GuidedEngine
from robotops.integration.inspection import COMPONENTS, code_catalog, facts, inspect_step
from robotops.integration.models import AuthorizeStage, CreateSession
from robotops.integration.source import symbol_line
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


@pytest.fixture
def saved(tmp_path, order_request):
    engine = GuidedEngine(
        Engine(Store(tmp_path / "app.db"), SyntheticRuntime(tmp_path / "runtime.db", Settings()))
    )
    session = engine.create(CreateSession(request=order_request, request_id="engineering"))
    while session.current_stage < 15:
        session = engine.authorize(
            session.session_id,
            AuthorizeStage(
                request_id=f"stage-{session.current_stage}",
                expected_revision=session.revision,
                stage=session.current_stage,
            ),
        )
    return engine, session


def test_inspection_reads_saved_and_current_evidence_without_work(saved, monkeypatch):
    engine, session = saved
    step = next(s for s in session.steps if s.stage == 8)
    before = engine.get(session.session_id).model_dump(mode="json")
    world = engine.workflow.runtime.world()

    # The route must never open a writable workflow connection or contact runtime.
    def forbidden(*args, **kwargs):
        raise AssertionError("Inspection attempted execution or a writable connection")

    monkeypatch.setattr(engine.workflow.store, "connect", forbidden)
    monkeypatch.setattr(engine.workflow.runtime, "world", forbidden)
    data = inspect_step(engine.workflow, session, step)
    assert data["records"]["items"]
    assert engine.get(session.session_id).model_dump(mode="json") == before
    monkeypatch.undo()
    assert engine.workflow.runtime.world() == world


def test_rest_inspection_and_source_are_read_only_and_scoped(saved, monkeypatch):
    engine, session = saved
    step = next(s for s in session.steps if s.stage == 14)
    app = create_app(engine.workflow.store, engine.workflow)
    before = engine.get(session.session_id).model_dump(mode="json")
    world = engine.workflow.runtime.world()

    def forbidden(*args, **kwargs):
        raise AssertionError("Inspection attempted a writable connection or runtime access")

    monkeypatch.setattr(engine.workflow.store, "connect", forbidden)
    monkeypatch.setattr(engine.workflow.runtime, "world", forbidden)
    route = f"/integration/sessions/{session.session_id}/steps/{step.step_id}"
    with TestClient(app) as client:
        response = client.get(route + "/inspection")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["command_id"] == step.command_id
        assert data["protocol"]["classification"] == step.classification
        assert any(item["kind"] == "RobotCommand" for item in data["records"]["items"])
        assert any(item["scope"] == "Current row, read now" for item in data["records"]["items"])
        assert any(item["kind"] == "WorldObservation" for item in data["records"]["items"])
        assert "not a saved configuration" in data["run"]["current_reference"]["scope"]
        assert data["run"]["missing"]
        assert all(item["key"] != "plc" for item in data["source_catalog"])
        assert client.get(route + "/source?component=plc").status_code == 404
        assert client.get(route + "/source?component=../../config.py").status_code == 404
        source = client.get(route + "/source?component=validator").json()
        assert source["path"] == "robotops/brain/validation.py"
        assert "class ActionValidator" in source["content"]
        assert (
            client.get(
                route.replace(step.step_id, "another-session-step") + "/inspection"
            ).status_code
            == 404
        )
    assert engine.get(session.session_id).model_dump(mode="json") == before
    monkeypatch.undo()
    assert engine.workflow.runtime.world() == world


def test_lab_catalog_exposes_actual_plc_edge_and_business_implementations(saved):
    _, session = saved
    session = session.model_copy(update={"profile": "lab"})
    step = session.steps[-1]
    keys = {item["key"] for item in code_catalog(session, step)}
    assert {"plc", "opc-client", "plc-journal", "edge", "edge-rpc", "postgres"} <= keys
    assert "wms" in {
        item["key"] for item in code_catalog(session, step.model_copy(update={"stage": 20}))
    }
    for _, path, symbol, _ in COMPONENTS.values():
        assert symbol_line(Path(path).read_text(encoding="utf-8"), symbol), (path, symbol)


def test_record_links_do_not_fall_forward_to_a_later_job(saved):
    engine, session = saved
    original = session.steps[-1]
    later = original.model_copy(
        update={
            "job_id": "unrelated-job",
            "command_id": "unrelated-command",
            "step_id": "unrelated-step",
            "output": {"observation_id": "unrelated-observation"},
        }
    )
    with engine.workflow.store.connect() as db:
        db.execute(
            "INSERT INTO records VALUES (?,?,?)",
            (
                "WorldObservation",
                "unrelated-observation",
                json.dumps({"marker": "UNRELATED-PRIVATE-RECORD"}),
            ),
        )
    changed = session.model_copy(
        update={
            "job_id": "unrelated-job",
            "command_id": "unrelated-command",
            "steps": (*session.steps, later),
        }
    )
    data = inspect_step(engine.workflow, changed, original)
    assert data["job_id"] == original.job_id
    assert "UNRELATED-PRIVATE-RECORD" not in json.dumps(data)
    assert all(item["step_id"] != "unrelated-step" for item in data["related_steps"])


def test_absence_false_and_aggregate_checks_are_not_individual_success(saved):
    engine, session = saved
    step = session.steps[-1].model_copy(
        update={
            "wire": {"ack": False, "result": None, "events": []},
            "output": {"valid": True, "checks": ["source", "tool"]},
        }
    )
    data = inspect_step(engine.workflow, session, step)
    assert data["protocol"]["facts"] == facts(step.wire, "wire")
    assert [f["value"] for f in data["protocol"]["facts"]] == [False, None, []]
    assert "not an individual pass/fail" in data["decisions"]["scope"]
    assert len(data["decisions"]["facts"]) == 2
