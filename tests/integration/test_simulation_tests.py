from concurrent.futures import ThreadPoolExecutor
from threading import Event
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api.app import create_app
from robotops.blender.adapter import BlenderRuntime
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.domain.models import Fault
from robotops.faults.injection import OBSERVATION_FAULTS
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


def setup_world(path, runtime_type=SyntheticRuntime):
    settings = Settings()
    engine = Engine(
        Store(path / "workflow.db"), runtime_type(path / "runtime.db", settings), settings
    )
    app = create_app(engine.store, engine)
    return engine, app, TestClient(app)


def new_test(client, request_id=None):
    response = client.post("/simulation-tests", json={"request_id": request_id or str(uuid4())})
    assert response.status_code == 201, response.text
    return "/simulation-tests/" + response.json()["test_id"]


def run(client, order_request, prefix="", fault=None):
    if prefix:
        # New experiments use the six-SKU profile, while the original fixture
        # remains legacy. Keep the ERP identity and use the new fixture's item.
        fixture = client.get(prefix + "/fixtures").json()
        product = fixture["products"][0]["product_id"]
        line = order_request.lines[0].model_copy(
            update={
                "product_id": product,
                "source_id": fixture["product_sources"][product],
                "destination_id": fixture["destination_id"],
            }
        )
        order_request = order_request.model_copy(update={"lines": (line,)})
    response = client.post(
        prefix + "/orders",
        json=order_request.model_dump(mode="json"),
        headers={"Idempotency-Key": order_request.order_id},
    )
    assert response.status_code == 201, response.text
    job_id = response.json()["job_ids"][0]
    response = client.post(prefix + f"/jobs/{job_id}/run", json={"fault": fault})
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize("execution", [None, *Fault])
@pytest.mark.parametrize("observation", ["unreconciled", None, *sorted(OBSERVATION_FAULTS)])
def test_every_combination_can_start_an_independent_test_without_changing_old_evidence(
    tmp_path, order_request, execution, observation
):
    engine, app, client = setup_world(tmp_path)
    job = run(client, order_request, fault=execution)
    if job["state"] == "UNKNOWN_OUTCOME" and observation != "unreconciled":
        job = client.post(f"/jobs/{job['job_id']}/reconcile", json={"fault": observation}).json()
        if observation is not None:
            assert job["state"] == "REQUIRES_INTERVENTION"
    before = engine.runtime.world(), engine.runtime.events(), engine.store.timeline()
    routes = [
        "/orders",
        "/cell/scene",
        "/deliveries",
        f"/jobs/{job['job_id']}/evidence",
        f"/jobs/{job['job_id']}/playback",
        f"/deliveries/{engine.runtime.world().scene_epoch}/playback",
    ]
    saved = {route: client.get(route).json() for route in routes}
    metrics = client.get("/metrics").text
    prefix = new_test(client)
    fixture = client.get(prefix + "/fixtures").json()
    assert fixture["scene_epoch"] != engine.runtime.world().scene_epoch
    assert fixture["robot_profile_version"] == "hkm_inspired_v1"
    assert len(fixture["products"]) == 6
    assert all(
        item["location_id"] == fixture["product_sources"][item["product_id"]]
        for item in fixture["inventory"]
    )
    assert client.get(prefix + "/orders").json() == []
    assert client.get(prefix + "/cell").json()["mode"] == "READY"
    history = client.get("/simulation-tests").json()
    assert history["tests"][0]["outcomes"] == [job["state"]]
    assert not history["tests"][0]["active"]
    assert history["tests"][1]["active"]
    # Reused ERP identity belongs to a distinct experiment, not a retry of the old pick.
    fresh = run(client, order_request, prefix)
    assert fresh["state"] == "COMPLETED"
    active = app.state.test_registry.engine(history["active_test_id"])
    assert active.runtime.journal(fresh["command_id"]).effect_count == 1
    assert before == (engine.runtime.world(), engine.runtime.events(), engine.store.timeline())
    assert saved == {route: client.get(route).json() for route in routes}
    assert client.get("/metrics").text == metrics


@pytest.mark.parametrize("original", [True, False])
def test_archived_api_is_read_only_for_every_mutation_and_request_is_pinned(
    tmp_path, order_request, original
):
    _, _, client = setup_world(tmp_path)
    prefix = "" if original else new_test(client)
    job = run(client, order_request, prefix, Fault.DROP_ACK_AFTER_EFFECT)
    next_prefix = new_test(client)
    for route, payload in [
        ("/orders", order_request.model_dump(mode="json")),
        (f"/jobs/{job['job_id']}/run", {}),
        (f"/jobs/{job['job_id']}/reconcile", {}),
        (f"/jobs/{job['job_id']}/playback/import", {}),
        ("/fixtures/fresh-scene", {}),
        ("/cell/reset", {}),
    ]:
        result = client.post(prefix + route, json=payload, headers={"Idempotency-Key": "late"})
        assert result.status_code == 409
        assert result.json()["reason"] == "TEST_ARCHIVED_READ_ONLY"
    assert client.get(next_prefix + f"/jobs/{job['job_id']}").status_code == 404
    assert client.get(next_prefix + "/orders").json() == []
    assert client.get(prefix + f"/jobs/{job['job_id']}").json()["state"] == "UNKNOWN_OUTCOME"


def test_restart_recovers_only_active_world_and_keeps_uncertain_archive(tmp_path, order_request):
    engine, _, client = setup_world(tmp_path)
    original = run(client, order_request, fault=Fault.DROP_ACK_AFTER_EFFECT)
    prefix = new_test(client)
    current = run(client, order_request, prefix, Fault.DROP_ACK_AFTER_EFFECT)
    snapshot = engine.store.timeline(), engine.runtime.events(), engine.runtime.world()
    reopened = TestClient(create_app(Store(engine.store.path), recover=True))
    assert reopened.get("/simulation-tests").json()["active_test_id"] == prefix.split("/")[-1]
    assert reopened.get(prefix + f"/jobs/{current['job_id']}").json()["state"] == "COMPLETED"
    assert reopened.get(f"/jobs/{original['job_id']}").json()["state"] == "UNKNOWN_OUTCOME"
    assert snapshot == (engine.store.timeline(), engine.runtime.events(), engine.runtime.world())
    assert len(reopened.get("/simulation-tests").json()["tests"]) == 2


def test_creation_is_idempotent_even_after_a_later_test_has_started(tmp_path):
    _, _, client = setup_world(tmp_path)
    request_id = str(uuid4())
    first = new_test(client, request_id)
    epoch = client.get(first + "/fixtures").json()["scene_epoch"]
    assert new_test(client, request_id) == first
    last = new_test(client)
    assert new_test(client, request_id) == first
    history = client.get("/simulation-tests").json()
    assert history["active_test_id"] == last.split("/")[-1]
    assert [item["number"] for item in history["tests"]] == [1, 2, 3]
    assert client.get(first + "/fixtures").json()["scene_epoch"] == epoch
    assert client.post("/simulation-tests", json={"request_id": "../escape"}).status_code == 422
    assert client.get(f"/simulation-tests/{uuid4()}/orders").status_code == 404
    assert client.get("/simulation-tests/original/orders").status_code == 404


@pytest.mark.parametrize("guard", ["lease", "planning", "maintenance"])
def test_new_test_does_not_interrupt_owned_or_unfinished_operations(tmp_path, order_request, guard):
    engine, _, client = setup_world(tmp_path)
    if guard == "maintenance":
        engine.store.begin_scene_reset()
    else:
        job = run(client, order_request, fault=Fault.DROP_ACK_AFTER_EFFECT)
        if guard == "lease":
            assert engine.store.claim(job["job_id"], "worker", 120, reconcile=True)
        else:
            with engine.store.transaction() as db:
                db.execute("UPDATE jobs SET state='PLANNING'")
    response = client.post("/simulation-tests", json={"request_id": str(uuid4())})
    assert response.status_code == 409
    assert response.json()["reason"] == "TEST_OPERATION_IN_PROGRESS"
    assert client.get("/simulation-tests").json()["active_test_id"] == "original"


def test_two_hosts_serialize_new_test_against_in_flight_run(tmp_path, order_request, monkeypatch):
    engine, _, client = setup_world(tmp_path)
    entered, finish = Event(), Event()
    original_apply = engine.runtime.apply

    def delayed(command, fault=None):
        entered.set()
        assert finish.wait(10)
        return original_apply(command, fault)

    monkeypatch.setattr(engine.runtime, "apply", delayed)
    other = TestClient(create_app(Store(engine.store.path)))
    with ThreadPoolExecutor(2) as pool:
        future = pool.submit(run, client, order_request)
        try:
            assert entered.wait(10)
            response = other.post("/simulation-tests", json={"request_id": str(uuid4())})
            assert response.status_code == 409
            assert response.json()["reason"] == "TEST_OPERATION_IN_PROGRESS"
            assert other.get("/fixtures").status_code == 200  # Live reads continue.
        finally:
            finish.set()
        assert future.result()["state"] == "COMPLETED"
    assert new_test(other)


@pytest.mark.blender
def test_blender_history_keeps_exact_recording_after_new_test_and_restart(tmp_path, order_request):
    engine, _, client = setup_world(tmp_path, BlenderRuntime)
    first = run(client, order_request, fault=Fault.DROP_ACK_AFTER_EFFECT)
    client.post(
        f"/jobs/{first['job_id']}/reconcile", json={"fault": Fault.CONTRADICTORY_OBSERVATION}
    ).raise_for_status()
    recording = client.get(f"/jobs/{first['job_id']}/playback").json()
    image = client.get(f"/jobs/{first['job_id']}/artifact.png").content
    assert len(recording["recording"]["frames"]) == 100
    prefix = new_test(client)
    fresh = run(client, order_request, prefix)
    assert fresh["state"] == "COMPLETED"
    reopened = TestClient(create_app(engine.store, engine, recover=True))
    assert reopened.get(f"/jobs/{first['job_id']}/playback").json() == recording
    assert reopened.get(f"/jobs/{first['job_id']}/artifact.png").content == image
    assert reopened.get(f"/jobs/{first['job_id']}").json()["state"] == "REQUIRES_INTERVENTION"
    active = reopened.get(prefix + f"/jobs/{fresh['job_id']}/evidence").json()
    assert active["journal"]["effect_count"] == 1
    assert engine.runtime.journal(first["command_id"]).effect_count == 1


@pytest.mark.blender
@pytest.mark.parametrize("archive", [False, True])
def test_evidence_reads_never_commit_a_pending_blender_checkpoint(
    tmp_path, order_request, monkeypatch, archive
):
    engine, _, client = setup_world(tmp_path, BlenderRuntime)
    complete = engine.runtime._complete
    monkeypatch.setattr(engine.runtime, "_complete", lambda *args: None)
    job = run(client, order_request)
    assert job["state"] == "UNKNOWN_OUTCOME"
    monkeypatch.setattr(engine.runtime, "_complete", complete)
    snapshot = engine.runtime.world(), engine.runtime.events(), engine.store.timeline()
    receipt = engine.runtime.recorded_journal(job["command_id"])
    assert receipt.status == "RUNNING" and receipt.effect_count == 0
    # Blender's response contains a valid completed effect, but presentation
    # must not commit it or reinterpret the saved controller journal.
    replay = client.get(f"/jobs/{job['job_id']}/playback").json()
    assert len(replay["recording"]["frames"]) == 100
    if archive:
        new_test(client)
        client = TestClient(create_app(engine.store, engine, recover=True))
    for _ in range(2):
        evidence = client.get(f"/jobs/{job['job_id']}/evidence").json()
        assert evidence["journal"] == receipt.model_dump(mode="json")
        assert client.get(f"/jobs/{job['job_id']}/playback").json() == replay
        assert snapshot == (
            engine.runtime.world(),
            engine.runtime.events(),
            engine.store.timeline(),
        )
    result = client.post(f"/jobs/{job['job_id']}/reconcile", json={})
    if archive:
        assert result.status_code == 409
        assert engine.runtime.recorded_journal(job["command_id"]) == receipt
    else:
        assert result.json()["state"] == "COMPLETED"
        assert engine.runtime.recorded_journal(job["command_id"]).effect_count == 1
