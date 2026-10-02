from concurrent.futures import ThreadPoolExecutor

import pytest

from robotops.cell.controller import CellController
from robotops.cell.runtime import CommunicationTimeout, SyntheticRuntime
from robotops.domain.models import CellMode, CommandStatus, Fault, RobotCommand, utc_now
from robotops.workflow.store import Conflict


@pytest.fixture
def runtime(tmp_path):
    return SyntheticRuntime(tmp_path / "runtime.db")


@pytest.fixture
def command(runtime):
    world = runtime.world()
    return RobotCommand(
        run_id="run",
        correlation_id="order",
        causation_id="plan",
        timestamp=utc_now(),
        action_plan_id="plan",
        job_id="job",
        order_id="order",
        order_line_id="line",
        product_id="product-red",
        source_id="source",
        destination_id="destination",
        target_pose=world.locations[1].pose,
        scene_epoch=world.scene_epoch,
        observation_id="obs",
        cell_generation=world.cell.generation,
        command_id="command",
    )


def test_duplicate_robot_command_and_restart(runtime, command):
    first = runtime.apply(command)
    assert first.status == CommandStatus.SUCCEEDED
    restarted = SyntheticRuntime(runtime.db.path)
    assert restarted.apply(command) == first
    assert restarted.world().objects[0].location_id == "destination"
    assert sum(e.event_type == "PICK_EFFECT" for e in restarted.events()) == 1
    assert sum(e.event_type == "DUPLICATE_SUPPRESSED" for e in restarted.events()) == 1


def test_duplicate_command_conflict(runtime, command):
    runtime.apply(command)
    with pytest.raises(Conflict, match="COMMAND_ID_PAYLOAD_CONFLICT"):
        runtime.apply(command.model_copy(update={"product_id": "product-blue"}))
    assert runtime.world().objects[1].location_id == "source"


@pytest.mark.parametrize(
    "mode",
    [CellMode.FAULTED, CellMode.ESTOP_LOGICAL, CellMode.RESETTING, CellMode.OFFLINE, CellMode.BUSY],
)
def test_cell_interlocks_block_motion(runtime, command, mode):
    runtime.set_cell(mode, "TEST")
    assert runtime.apply(command).status == CommandStatus.REJECTED
    assert runtime.world().step == 0


@pytest.mark.parametrize(
    "fault,expected_count", [(Fault.DROP_ACK_AFTER_EFFECT, 1), (Fault.DROP_ACK_BEFORE_EFFECT, 0)]
)
def test_lost_ack_journal_distinguishes_effect(runtime, command, fault, expected_count):
    with pytest.raises(CommunicationTimeout):
        runtime.apply(command, fault)
    receipt = runtime.journal(command.command_id)
    assert receipt.effect_count == expected_count
    assert runtime.world().step == expected_count
    assert sum(e.event_type == "PICK_EFFECT" for e in runtime.events()) == expected_count
    assert runtime.apply(command) == receipt
    assert runtime.world().step == expected_count


def test_concurrent_duplicate_delivery_applies_once(runtime, command):
    def deliver(_):
        return SyntheticRuntime(runtime.db.path).apply(command)

    with ThreadPoolExecutor(2) as pool:
        receipts = list(pool.map(deliver, range(2)))
    assert receipts[0] == receipts[1]
    assert runtime.world().step == 1


def test_reset_preserves_world_journal_and_invalidates_old_plan(runtime, command):
    runtime.apply(command)
    controller = CellController(runtime)
    controller.stop()
    controller.reset()
    assert runtime.world().objects[0].location_id == "destination"
    assert runtime.journal(command.command_id).effect_count == 1
    stale = command.model_copy(update={"command_id": "next", "product_id": "product-blue"})
    assert runtime.apply(stale).reason == "CELL_GENERATION_MISMATCH"


def test_scene_reset_keeps_history_and_rejects_old_epoch(runtime, command):
    runtime.reset()
    assert runtime.apply(command).reason == "SCENE_EPOCH_MISMATCH"
    assert runtime.world().step == 0


def test_command_failure_has_no_effect(runtime, command):
    receipt = runtime.apply(command, Fault.ROBOT_COMMAND_FAILURE)
    assert receipt.status == CommandStatus.FAILED and receipt.effect_count == 0
    assert runtime.world().step == 0
