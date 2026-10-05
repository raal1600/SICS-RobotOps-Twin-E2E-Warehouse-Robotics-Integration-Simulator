"""The automatic demonstration is a client of the same bounded guided REST engine."""

from fastapi.testclient import TestClient

from apps.api.app import create_app
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store
from tools.integration_demo import drive


def test_automatic_driver_requires_explicit_physical_consent_and_resumes_original(tmp_path):
    store = Store(tmp_path / "workflow.db")
    runtime = SyntheticRuntime(tmp_path / "runtime.db", Settings.hkm())
    engine = Engine(store, runtime)
    with TestClient(create_app(store, engine, test_registry=False)) as client:
        waiting = drive(client, scenario="happy_path", authorize_robot=False)
        assert waiting["session"]["current_stage"] == 15
        assert waiting["session"]["status"] == "WAITING_AUTHORIZATION"
        assert runtime.world().step == 0
        assert waiting["evidence"]["journal"] is None
        completed = drive(
            client,
            scenario="happy_path",
            authorize_robot=True,
            session_id=waiting["session"]["session_id"],
        )
        assert completed["session"]["status"] == "COMPLETED"
        assert len(completed["session"]["steps"]) == 22
        assert completed["evidence"]["journal"]["effect_count"] == 1
        assert len(store.orders()) == 1
        assert completed["session"]["command_id"] == waiting["session"]["command_id"]


def test_automatic_lost_ack_demo_queries_original_without_another_pick(tmp_path):
    store = Store(tmp_path / "workflow.db")
    runtime = SyntheticRuntime(tmp_path / "runtime.db", Settings.hkm())
    engine = Engine(store, runtime)
    with TestClient(create_app(store, engine, test_registry=False)) as client:
        result = drive(client, scenario="lost_ack_after_effect", authorize_robot=True)
        assert result["session"]["status"] == "COMPLETED"
        assert result["evidence"]["journal"]["effect_count"] == 1
        assert len(result["evidence"]["reconciliations"]) == 1
        assert runtime.world().step == 1
        events = store.timeline(result["session"]["order_id"])
        assert (
            sum(
                event.component == "gateway" and event.event_type == "COMMAND_DISPATCHED"
                for event in events
            )
            == 1
        )
