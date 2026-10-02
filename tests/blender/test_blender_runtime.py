import json
from pathlib import Path

import pytest

from robotops.blender.adapter import BlenderRuntime
from robotops.cell.controller import CellController
from robotops.cell.runtime import CommunicationTimeout
from robotops.domain.models import Fault, JobState, RobotCommand
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store

pytestmark = pytest.mark.blender


@pytest.mark.parametrize("fault", [None, Fault.DROP_ACK_AFTER_EFFECT])
def test_real_blender_pick_and_lost_ack(tmp_path, order_request, fault):
    runtime = BlenderRuntime(tmp_path / "runtime.db")
    store = Store(tmp_path / "workflow.db")
    engine = Engine(store, runtime)
    job_id = store.intake(order_request, "key").job_ids[0]
    result = engine.run(job_id, fault)
    if fault:
        assert result.state == JobState.UNKNOWN_OUTCOME
        result = Engine(Store(store.path), BlenderRuntime(runtime.db.path)).reconcile(job_id)
    assert result.state == JobState.COMPLETED
    assert runtime.world().objects[0].location_id == "destination"
    assert sum(e.event_type == "PICK_EFFECT" for e in runtime.events()) == 1
    command = store.load(RobotCommand, result.command_id)
    runtime.apply(command)
    assert sum(e.event_type == "PICK_EFFECT" for e in runtime.events()) == 1
    responses = list(runtime.artifacts.glob("*/response.json"))
    assert len(responses) == 1
    response = json.loads(responses[0].read_text())
    assert response["steps"] == ["APPROACH", "ATTACH", "LIFT", "TRANSFER", "DETACH"]
    assert {
        "RobotOpsTwin/Cell",
        "Robot",
        "Gripper",
        "SourceTote",
        "DestinationTote",
        "Products/product-red",
        "OverviewCamera",
        "ObservationCamera",
    } <= set(response["object_names"])
    assert responses[0].with_name("capture.png").read_bytes().startswith(b"\x89PNG")
    assert responses[0].with_name("scene.blend").stat().st_size > 10000
    evidence = Path("artifacts/blender") / ("lost-ack" if fault else "happy")
    evidence.mkdir(parents=True, exist_ok=True)
    for name in ["response.json", "capture.png", "runtime.log", "scene.blend"]:
        (evidence / name).write_bytes(responses[0].with_name(name).read_bytes())


def test_real_blender_reset_capture_and_epoch(tmp_path):
    runtime = BlenderRuntime(tmp_path / "runtime.db")
    before = runtime.world().scene_epoch
    after = runtime.reset()
    assert after.scene_epoch != before and after.step == 0
    artifact = runtime.capture(tmp_path / "overview.png")
    assert artifact.read_bytes().startswith(b"\x89PNG")


@pytest.mark.parametrize("corrupt", [False, True])
def test_blender_response_loss_or_corruption_never_reexecutes(tmp_path, order_request, corrupt):
    class LoseReply(BlenderRuntime):
        def _invoke(self, directory):
            super()._invoke(directory)
            if corrupt:
                (directory / "response.json").write_text("incomplete checkpoint")
            raise CommunicationTimeout("PROCESS_REPLY_LOST")

    runtime = LoseReply(tmp_path / "runtime.db")
    store = Store(tmp_path / "workflow.db")
    job_id = store.intake(order_request, "key").job_ids[0]
    assert Engine(store, runtime).run(job_id).state == JobState.UNKNOWN_OUTCOME
    restarted = BlenderRuntime(runtime.db.path)
    result = Engine(Store(store.path), restarted).reconcile(job_id)
    assert result.state == (JobState.REQUIRES_INTERVENTION if corrupt else JobState.COMPLETED)
    command = store.load(RobotCommand, result.command_id)
    restarted.apply(command)
    assert len(list(runtime.artifacts.glob("*/request.json"))) == 1
    if corrupt:
        CellController(restarted).reset()
        another = command.model_copy(
            update={
                "command_id": "unsafe-replacement",
                "cell_generation": restarted.world().cell.generation,
            }
        )
        assert restarted.apply(another).effect_count == 0
        assert len(list(runtime.artifacts.glob("*/request.json"))) == 1
