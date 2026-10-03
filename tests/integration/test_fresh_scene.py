from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from apps.api.app import create_app
from robotops.blender.adapter import BlenderRuntime
from robotops.cell.runtime import SyntheticRuntime
from robotops.domain.models import CommandReceipt, CommandStatus, Fault, JobState, RobotCommand
from robotops.workflow.engine import Engine
from robotops.workflow.store import Conflict, Store


@pytest.mark.parametrize(
    "runtime_type", [SyntheticRuntime, pytest.param(BlenderRuntime, marks=pytest.mark.blender)]
)
def test_all_products_can_be_picked_again_after_explicit_fresh_scene(
    tmp_path, order_request, runtime_type
):
    store = Store(tmp_path / "workflow.db")
    runtime = runtime_type(tmp_path / "runtime.db")
    engine = Engine(store, runtime)
    client = TestClient(create_app(store, engine))
    originals = []
    for index, product in enumerate(engine.settings.products):
        request = order_request.model_copy(
            update={
                "order_id": f"first-{index}",
                "lines": (
                    order_request.lines[0].model_copy(update={"product_id": product.product_id}),
                ),
            }
        )
        job = engine.run(store.intake(request, request.order_id).job_ids[0])
        assert job.state == JobState.COMPLETED
        replay = client.get(f"/jobs/{job.job_id}/playback").json()
        if runtime_type is BlenderRuntime:
            assert len(replay["recording"]["frames"]) == 100
        originals.append((job, replay, store.timeline(job.order_id)))
    assert all(
        item["location_id"] == "destination" for item in client.get("/fixtures").json()["inventory"]
    )
    # Reproduce the reported rejection instead of bypassing the source precondition.
    duplicate = order_request.model_copy(update={"order_id": "already-picked"})
    rejected = engine.run(store.intake(duplicate, duplicate.order_id).job_ids[0])
    assert rejected.state == JobState.FAILED and rejected.command_id is None
    assert "PLANNING_REJECTED:SOURCE_NOT_OBSERVED" in [
        e.reason for e in store.timeline(duplicate.order_id)
    ]
    epoch = runtime.world().scene_epoch
    response = client.post("/fixtures/fresh-scene", json={})
    assert response.status_code == 200
    assert response.json()["scene_epoch"] != epoch
    assert runtime.world().step == 0
    assert all(
        item["location_id"] == "source" for item in client.get("/fixtures").json()["inventory"]
    )
    for job, replay, timeline in originals:
        assert client.get(f"/jobs/{job.job_id}/playback").json() == replay
        assert store.timeline(job.order_id) == timeline
        command = store.load(RobotCommand, job.command_id)
        assert runtime.apply(command).effect_count == 1
        assert runtime.world().step == 0  # Redelivery never repeats an old pick in a new scene.
    for index, product in enumerate(engine.settings.products):
        request = order_request.model_copy(
            update={
                "order_id": f"second-{index}",
                "lines": (
                    order_request.lines[0].model_copy(update={"product_id": product.product_id}),
                ),
            }
        )
        job = engine.run(store.intake(request, request.order_id).job_ids[0])
        assert job.state == JobState.COMPLETED
        assert runtime.journal(job.command_id).effect_count == 1
    assert len([event for event in runtime.events() if event.event_type == "PICK_EFFECT"]) == 6


@pytest.mark.parametrize("state", ["pending", "unknown", "intervention"])
def test_fresh_scene_cannot_hide_pending_or_uncertain_work(tmp_path, order_request, state):
    store = Store(tmp_path / "workflow.db")
    runtime = SyntheticRuntime(tmp_path / "runtime.db")
    engine = Engine(store, runtime)
    job_id = store.intake(order_request, "key").job_ids[0]
    if state != "pending":
        engine.run(job_id, Fault.DROP_ACK_AFTER_EFFECT)
    if state == "intervention":
        engine.reconcile(job_id, Fault.CONTRADICTORY_OBSERVATION)
    before = (runtime.world(), runtime.events(), store.timeline(), store.job(job_id))
    client = TestClient(create_app(store, engine))
    result = client.post("/fixtures/fresh-scene", json={})
    assert result.status_code == 409
    assert result.json()["reason"] == "SCENE_RESET_BLOCKED_UNRESOLVED_JOBS"
    assert before == (runtime.world(), runtime.events(), store.timeline(), store.job(job_id))
    assert client.get("/fixtures").json()["scene_reset_blocked_reason"] == result.json()["reason"]


@pytest.mark.parametrize("effect_saved", [False, True])
def test_fresh_scene_restart_finishes_original_maintenance_intent(
    tmp_path, order_request, effect_saved
):
    store = Store(tmp_path / "workflow.db")
    runtime = SyntheticRuntime(tmp_path / "runtime.db")
    engine = Engine(store, runtime)
    job = engine.run(store.intake(order_request, "key").job_ids[0])
    epoch = store.begin_scene_reset()
    if effect_saved:
        runtime.reset(scene_epoch=epoch)
    with pytest.raises(Conflict, match="SCENE_RESET_IN_PROGRESS"):
        store.intake(order_request.model_copy(update={"order_id": "next"}), "next")
    assert store.claim(job.job_id, "other", 120) is None
    restarted = Engine(Store(store.path), SyntheticRuntime(runtime.db.path))
    restarted.recover()
    assert runtime.world().scene_epoch == epoch
    assert runtime.world().step == 0
    assert store.pending_scene_reset() is None
    assert len([e for e in runtime.events() if e.event_type == "SCENE_RESET"]) == 1
    # Late completion/reset of the previous request cannot rewind a later scene.
    restarted.start_fresh_scene()
    current = runtime.world()
    runtime.reset(scene_epoch=epoch)
    store.finish_scene_reset(epoch)
    assert runtime.world() == current


def test_scene_reset_and_order_intake_serialize_between_workers(tmp_path, order_request):
    store = Store(tmp_path / "workflow.db")

    def reset():
        try:
            return Store(store.path).begin_scene_reset()
        except Conflict:
            return None

    def intake():
        try:
            return Store(store.path).intake(order_request, "key")
        except Conflict:
            return None

    with ThreadPoolExecutor(2) as pool:
        a, b = pool.submit(reset), pool.submit(intake)
        assert (a.result() is None) != (b.result() is None)


def test_fresh_scene_refuses_active_worker_even_after_terminal_transition(tmp_path, order_request):
    store = Store(tmp_path / "workflow.db")
    job_id = store.intake(order_request, "key").job_ids[0]
    claim = store.claim(job_id, "worker", 120)
    store.transition(job_id, JobState.FAILED, "NO_DISPATCH", claim=claim)
    with pytest.raises(Conflict, match="ACTIVE_WORKER"):
        store.begin_scene_reset()
    store.release(claim)
    assert store.begin_scene_reset()


def test_runtime_scene_reset_refuses_unresolved_controller_receipt(tmp_path, order_request):
    store = Store(tmp_path / "workflow.db")
    runtime = SyntheticRuntime(tmp_path / "runtime.db")
    job = Engine(store, runtime).run(store.intake(order_request, "key").job_ids[0])
    receipt = runtime.journal(job.command_id).model_copy(
        update={
            "status": CommandStatus.STATUS_UNKNOWN,
            "effect_count": 0,
        }
    )
    receipt = CommandReceipt.model_validate_json(receipt.model_dump_json())
    with runtime.db.transaction() as db:
        db.execute(
            "UPDATE controller_journal SET receipt=? WHERE id=?",
            (receipt.model_dump_json(), job.command_id),
        )
    before = runtime.world(), runtime.events()
    with pytest.raises(Conflict, match="UNCERTAIN_COMMAND"):
        runtime.reset()
    assert before == (runtime.world(), runtime.events())


def test_scene_preparation_error_keeps_recoverable_intent(tmp_path, monkeypatch):
    store = Store(tmp_path / "workflow.db")
    runtime = SyntheticRuntime(tmp_path / "runtime.db")
    engine = Engine(store, runtime)

    def interrupted(scene_epoch=None):
        raise TimeoutError("INTERRUPTED_FIXTURE_RENDER")

    monkeypatch.setattr(runtime, "reset", interrupted)
    client = TestClient(create_app(store, engine))
    response = client.post("/fixtures/fresh-scene", json={})
    assert response.status_code == 503 and "Reopen" in response.json()["detail"]
    epoch = store.pending_scene_reset()
    assert epoch is not None
    Engine(Store(store.path), SyntheticRuntime(runtime.db.path)).recover()
    assert runtime.world().scene_epoch == epoch
    assert store.pending_scene_reset() is None
