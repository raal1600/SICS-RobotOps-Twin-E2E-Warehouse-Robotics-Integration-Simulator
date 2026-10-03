import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from apps.api.app import create_app
from robotops.blender.adapter import BlenderRuntime
from robotops.blender.visualization import DeliveryPlayback
from robotops.cell.runtime import SyntheticRuntime
from robotops.domain.models import Fault, JobState
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


@pytest.mark.parametrize(
    "runtime_type", [SyntheticRuntime, pytest.param(BlenderRuntime, marks=pytest.mark.blender)]
)
def test_full_delivery_replays_every_product_in_execution_order_after_restart_and_reset(
    tmp_path, order_request, runtime_type
):
    store = Store(tmp_path / "workflow.db")
    runtime = runtime_type(tmp_path / "runtime.db")
    engine = Engine(store, runtime)
    client = TestClient(create_app(store, engine))
    epoch = runtime.world().scene_epoch
    assert client.get(f"/deliveries/{epoch}/playback").json()["jobs"] == []
    jobs = {}
    # Reverse intake proves grouping follows persisted execution order, not creation time.
    for product in reversed(engine.settings.products):
        request = order_request.model_copy(
            update={
                "order_id": product.product_id,
                "lines": (
                    order_request.lines[0].model_copy(update={"product_id": product.product_id}),
                ),
            }
        )
        jobs[product.product_id] = store.intake(request, request.order_id).job_ids[0]
    execution_order = [jobs[product.product_id] for product in engine.settings.products]
    for job in execution_order:
        assert engine.run(job).state == JobState.COMPLETED
    group = client.get("/deliveries").json()[0]
    assert [item["job_id"] for item in group["executions"]] == execution_order
    route = f"/deliveries/{epoch}/playback"
    combined = client.get(route).json()
    assert [job["job_id"] for job in combined["jobs"]] == execution_order
    for item in combined["jobs"]:
        assert item == client.get(f"/jobs/{item['job_id']}/playback").json()
    if runtime_type is BlenderRuntime:
        assert sum(len(job["recording"]["frames"]) for job in combined["jobs"]) == 300
        for index, item in enumerate(combined["jobs"]):
            first = item["recording"]["frames"][0]["positions"]
            last = item["recording"]["frames"][-1]["positions"]
            name = "Products/" + item["product_id"]
            assert first[name][0] < 0 and last[name][0] > 0
            for previous in combined["jobs"][:index]:
                name = "Products/" + previous["product_id"]
                # Stationary objects use their recorded geometry pose; only animated
                # objects require a per-frame position override in MotionRecording.
                pose = first.get(
                    name,
                    next(
                        obj["position"]
                        for obj in item["recording"]["objects"]
                        if obj["name"] == name
                    ),
                )
                assert pose[0] > 0
    before = (store.timeline(), runtime.world(), runtime.events())
    restarted = TestClient(
        create_app(Store(store.path), Engine(Store(store.path), runtime_type(runtime.db.path)))
    )
    for _ in range(2):
        assert restarted.get(route).json() == combined
    assert before == (store.timeline(), runtime.world(), runtime.events())
    assert restarted.post("/fixtures/fresh-scene").status_code == 200
    assert restarted.get(route).json() == combined
    summaries = restarted.get("/deliveries").json()
    assert len(summaries) == 2
    assert not summaries[0]["current"] and summaries[1]["current"]
    assert summaries[1]["executions"] == []
    assert len([event for event in runtime.events() if event.event_type == "PICK_EFFECT"]) == 3
    assert restarted.get("/deliveries/missing/playback").status_code == 404


@pytest.mark.parametrize(
    "fault",
    [Fault.BRAIN_TIMEOUT, Fault.BRAIN_INVALID_OUTPUT, Fault.LOGICAL_ESTOP, Fault.CELL_FAULT],
)
def test_stationary_scenario_is_retained_as_its_own_delivery(tmp_path, order_request, fault):
    store = Store(tmp_path / "workflow.db")
    runtime = SyntheticRuntime(tmp_path / "runtime.db")
    engine = Engine(store, runtime)
    client = TestClient(create_app(store, engine))
    epoch = runtime.world().scene_epoch
    job = engine.run(store.intake(order_request, "key").job_ids[0], fault)
    assert job.state == JobState.FAILED
    clip = client.get(f"/deliveries/{epoch}/playback").json()
    assert clip["jobs"][0]["recording"] is None
    assert clip["jobs"][0]["job_state"] == "FAILED"
    assert any(event["reason"] == fault.value for event in clip["jobs"][0]["events"])
    assert client.post("/fixtures/fresh-scene").status_code == 200
    assert client.get(f"/deliveries/{epoch}/playback").json() == clip
    assert not any(event.event_type == "PICK_EFFECT" for event in runtime.events())


@pytest.mark.parametrize("intervention", [False, True])
def test_delivery_replay_never_clears_uncertainty_or_allows_a_fresh_scenario(
    tmp_path, order_request, intervention
):
    store = Store(tmp_path / "workflow.db")
    runtime = SyntheticRuntime(tmp_path / "runtime.db")
    engine = Engine(store, runtime)
    job = engine.run(store.intake(order_request, "key").job_ids[0], Fault.DROP_ACK_AFTER_EFFECT)
    if intervention:
        job = engine.reconcile(job.job_id, Fault.CONTRADICTORY_OBSERVATION)
    client = TestClient(create_app(store, engine))
    epoch = runtime.world().scene_epoch
    before = store.timeline(), runtime.world(), runtime.events()
    assert client.get(f"/deliveries/{epoch}/playback").json()["jobs"][0]["job_state"] == job.state
    assert client.post("/fixtures/fresh-scene").status_code == 409
    assert before == (store.timeline(), runtime.world(), runtime.events())


def test_delivery_contract_rejects_duplicate_jobs_and_mixed_scene_epochs(tmp_path, order_request):
    store = Store(tmp_path / "workflow.db")
    runtime = SyntheticRuntime(tmp_path / "runtime.db")
    engine = Engine(store, runtime)
    engine.run(store.intake(order_request, "key").job_ids[0])
    client = TestClient(create_app(store, engine))
    clip = client.get(f"/deliveries/{runtime.world().scene_epoch}/playback").json()
    with pytest.raises(ValidationError, match="DUPLICATE_DELIVERY_EXECUTION"):
        DeliveryPlayback.model_validate({**clip, "jobs": clip["jobs"] * 2})
    with pytest.raises(ValidationError, match="DELIVERY_SCENE_MISMATCH"):
        DeliveryPlayback.model_validate({**clip, "delivery_id": "wrong-scene"})
