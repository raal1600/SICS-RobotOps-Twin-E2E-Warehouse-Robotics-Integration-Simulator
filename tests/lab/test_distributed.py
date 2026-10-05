"""Mandatory real-service lane; run with ROBOTOPS_LAB_TESTS=1, never mock the wire."""

from dataclasses import replace
from uuid import uuid4

import psycopg
import pytest

from robotops.cell.runtime import CommunicationTimeout
from robotops.domain.models import Fault, RobotCommand
from robotops.lab.postgres import PostgreSQLStore
from robotops.lab.transport import EdgeAdapter, LabBridge
from robotops.workflow.engine import Engine
from robotops.workflow.store import Conflict

pytestmark = pytest.mark.lab_integration


def test_postgres_full_repository_intake_and_atomic_outbox(tmp_path, lab_config, order_request):
    from robotops.cell.runtime import SyntheticRuntime

    store = PostgreSQLStore(lab_config.postgres_dsn, tmp_path / "app.db")
    request = order_request.model_copy(update={"order_id": "pg-" + uuid4().hex})
    order = store.intake(request, request.order_id)
    assert store.intake(request, request.order_id) == order
    runtime = SyntheticRuntime(tmp_path / "runtime.db")
    engine = Engine(store, runtime)
    job = engine.run(order.job_ids[0])
    command = store.load(RobotCommand, job.command_id)
    assert store.order(order.order_id).status == "COMPLETED"
    assert store.execution_jobs()
    assert store.records_for_job(RobotCommand, job.job_id) == (command,)
    bridge = LabBridge(lab_config, runtime)
    queued = bridge.enqueue(command.model_dump(mode="json"))
    assert queued["network_effect"] is False
    with psycopg.connect(lab_config.postgres_dsn) as db:
        assert (
            db.execute(
                "SELECT state FROM lab_outbox WHERE command_id=%s", (command.command_id,)
            ).fetchone()[0]
            == "PENDING"
        )
    conflict = command.model_copy(update={"cell_generation": command.cell_generation + 1})
    with pytest.raises(Conflict):
        bridge.enqueue(conflict.model_dump(mode="json"))


@pytest.mark.parametrize(
    "fault,effects", [(Fault.DROP_ACK_BEFORE_EFFECT, 0), (Fault.DROP_ACK_AFTER_EFFECT, 1)]
)
def test_real_pg_rabbit_edge_opc_duplicate_and_lost_ack(lab_config, lab_command, fault, effects):
    command, runtime = lab_command
    # Each parametrized/process invocation gets unique durable identity.
    command = command.model_copy(update={"command_id": uuid4().hex})
    bridge = LabBridge(lab_config, runtime)
    edge = EdgeAdapter(lab_config)
    bridge.enqueue(command.model_dump(mode="json"))
    assert bridge.publish(command.command_id)["publisher_confirm"]
    assert edge.consume_one(lose_ack=True)["consumer_ack_sent"] is False
    redelivery = edge.consume_one()
    assert redelivery["redelivered"]
    delivered = bridge.edge_deliver(command.command_id)
    assert delivered["deliveries"] == 2
    assert delivered["consumer_ack_sent"]
    assert bridge.opc_connect()["subscription_notifications"]
    assert bridge.submit(command.model_dump(mode="json"))["state"] == "ACCEPTED"
    assert runtime.world().step == 0
    assert bridge.preconditions(command.command_id)["state"] == "READY"
    with pytest.raises(CommunicationTimeout):
        bridge.authorize_execute(
            command.command_id,
            lambda: runtime.apply(command, fault).model_dump(mode="json"),
        )
    assert runtime.world().step == effects
    assert bridge.status(command.command_id)["state"] == "EXECUTING"
    streamed = bridge.live_status(command.command_id)
    assert streamed["read_only"]
    assert any(event["value"] == "EXECUTING" for event in streamed["events"])
    assert all(event["operation"] == "DataChangeNotification" for event in streamed["events"])
    with pytest.raises(TimeoutError, match="ALREADY_CLAIMED"):
        bridge.authorize_execute(
            command.command_id, lambda: pytest.fail("MUST NOT repeat physical execution")
        )
    original = runtime.journal(command.command_id)
    bridge.record_result(command.command_id, original.model_dump(mode="json"))
    # Another actual AMQP delivery and SubmitJob must return the original result.
    bridge.publish(command.command_id)
    edge.consume_one()
    duplicate = bridge.submit(command.model_dump(mode="json"))
    assert duplicate["duplicate"]
    assert duplicate["result"]["effect_count"] == effects
    replay = bridge.authorize_execute(
        command.command_id, lambda: pytest.fail("duplicate callback invoked")
    )
    assert replay["effect_count"] == effects
    assert runtime.world().step == effects
    assert bridge.acknowledge_result(command.command_id, 1)["acknowledged"]


def test_broker_failure_retains_outbox_and_opc_disconnect_never_executes(
    lab_config, lab_command, running_plc
):
    command, runtime = lab_command
    command = command.model_copy(update={"command_id": uuid4().hex})
    unavailable = replace(lab_config, amqp_url="amqp://guest:guest@127.0.0.1:1/%2F", timeout=0.2)
    bridge = LabBridge(unavailable, runtime)
    bridge.enqueue(command.model_dump(mode="json"))
    with pytest.raises(OSError, match="OUTBOX_RETAINED"):
        bridge.publish(command.command_id)
    assert bridge.store.outbox(command.command_id)["state"] == "PENDING"
    disconnected = LabBridge(
        replace(lab_config, edge_url="http://127.0.0.1:1", timeout=0.2), runtime
    )
    with pytest.raises(OSError):
        disconnected.authorize_execute(
            command.command_id, lambda: pytest.fail("No permit received")
        )
    assert runtime.world().step == 0
    running_plc.stop()
    with pytest.raises(OSError, match="EDGE_OPCUA_UNAVAILABLE"):
        LabBridge(lab_config, runtime).opc_connect()
    assert runtime.world().step == 0


def test_edge_control_rejects_submission_without_durable_delivery(lab_config, lab_command):
    command, runtime = lab_command
    bridge = LabBridge(lab_config, runtime)
    with pytest.raises(Conflict, match="EDGE_OPCUA_COMMAND_REJECTED"):
        bridge.opc.call("SubmitJob", command.model_dump_json())
    assert bridge.status(command.command_id)["state"] == "NOT_FOUND"
    assert runtime.world().step == 0
