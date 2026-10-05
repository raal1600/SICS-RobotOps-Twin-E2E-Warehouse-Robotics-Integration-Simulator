"""Real OPC UA health-probe latency must not silently revoke an active session."""

import asyncio
import socket
from contextlib import asynccontextmanager
from dataclasses import replace

import pytest
from asyncua import ua
from asyncua.client.ua_client import UaClientState
from asyncua.common.callback import CallbackType

from robotops.lab.edge import EdgeControl, EdgeOperation
from robotops.lab.journal import PLCJournal
from robotops.lab.opcua import OPCClient, VirtualPLC

pytestmark = pytest.mark.lab_integration


class DelayedServerState:
    """Delay only a real external ServerState read, leaving method traffic intact."""

    def __init__(self):
        self.delay = None
        self.started = asyncio.Event()
        self.finished = asyncio.Event()
        self.release = asyncio.Event()

    async def before_read(self, event, service):
        if self.delay is None or not event.is_external:
            return
        if not any(
            item.NodeId == ua.NodeId(ua.ObjectIds.Server_ServerStatus_State)
            and item.AttributeId == ua.AttributeIds.Value
            for item in event.request_params.NodesToRead
        ):
            return
        self.started.set()
        try:
            await asyncio.wait_for(self.release.wait(), timeout=self.delay)
        except TimeoutError:
            pass
        self.finished.set()


@asynccontextmanager
async def retained_execution(tmp_path, lab_config, command, runtime):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    endpoint = f"opc.tcp://127.0.0.1:{port}/slow-health/"
    plc = VirtualPLC(endpoint, PLCJournal(tmp_path / "slow-health.db"))
    probe = DelayedServerState()
    await plc.start()
    plc.server.subscribe_server_callback(CallbackType.PreRead, probe.before_read)
    config = replace(lab_config, opcua_url=endpoint, timeout=2.5)
    control = EdgeControl(config)
    wire = OPCClient(endpoint, config.timeout)
    try:
        accepted = await wire._call("SubmitJob", (command.model_dump_json(),))
        assert accepted["state"] == "ACCEPTED"
        assert accepted["effect_permitted"] is False
        checked = await wire._call(
            "CheckPreconditions", (command.command_id, runtime.world().model_dump_json())
        )
        assert checked["state"] == "READY"
        assert runtime.world().step == 0
        claim = await control.call(
            EdgeOperation(method="BeginExecution", arguments=[command.command_id])
        )
        assert claim["execute"] and claim["subscription_retained_during_callback"]
        yield plc, probe, control, wire, claim
    finally:
        probe.delay = None
        probe.release.set()
        try:
            await control.close()
        finally:
            await plc.stop()


def test_slow_real_server_state_probe_preserves_original_execution_session(
    tmp_path, lab_config, lab_command
):
    command, runtime = lab_command
    callbacks = []

    def execute_callback():
        callbacks.append(command.command_id)
        return runtime.apply(command)

    async def scenario():
        async with retained_execution(tmp_path, lab_config, command, runtime) as context:
            plc, probe, control, wire, claim = context
            session = control.sessions[command.command_id]
            protocol = session.client.uaclient.protocol
            token = protocol.authentication_token
            probe.delay = 1.3  # Exceeds asyncua's old 1s watchdog, below the 2.5s budget.
            await asyncio.wait_for(probe.started.wait(), timeout=5)
            await asyncio.wait_for(probe.finished.wait(), timeout=3)
            assert control.sessions[command.command_id] is session
            assert session.client.uaclient.protocol is protocol
            assert protocol.authentication_token == token
            assert plc.journal.status(command.command_id)["state"] == "EXECUTING"
            with plc.journal.connect() as db:
                assert (
                    db.execute("SELECT permit FROM plc_commands").fetchone()[0] == claim["permit"]
                )
            receipt = execute_callback()
            result = await control.call(
                EdgeOperation(
                    method="ReportResult",
                    arguments=[command.command_id, receipt.model_dump_json()],
                )
            )
            assert protocol.authentication_token == token
            assert result["result"]["effect_count"] == 1
            assert result["result_sequence"] == 1
            assert command.command_id not in control.sessions
            retained = await wire._call("GetJobStatus", (command.command_id,))
            assert retained["result"] == result["result"]
            duplicate = await control.call(
                EdgeOperation(method="BeginExecution", arguments=[command.command_id])
            )
            if duplicate["execute"]:
                execute_callback()
            assert duplicate["execute"] is False
            assert callbacks == [command.command_id]
            assert runtime.world().step == 1
            with plc.journal.connect() as db:
                assert db.execute("SELECT count(*) FROM plc_commands").fetchone()[0] == 1
                assert db.execute("SELECT count(*) FROM plc_results").fetchone()[0] == 1

    asyncio.run(scenario())


def test_sustained_real_server_state_delay_is_bounded_without_a_second_execution(
    tmp_path, lab_config, lab_command
):
    command, runtime = lab_command
    callbacks = []

    def execute_callback():
        callbacks.append(command.command_id)
        return runtime.apply(command)

    async def scenario():
        async with retained_execution(tmp_path, lab_config, command, runtime) as context:
            plc, probe, control, wire, claim = context
            session = control.sessions[command.command_id]
            receipt = execute_callback()
            probe.delay = 30
            async with session.client.uaclient.subscribe_state() as state:
                await asyncio.wait_for(probe.started.wait(), timeout=5)
                started = asyncio.get_running_loop().time()
                await state.wait_for_state(UaClientState.DISCONNECTED, timeout=4)
                assert asyncio.get_running_loop().time() - started < 4
            # The physical effect has happened, but communication loss cannot turn
            # it into a successful controller report or authorize another callback.
            started = asyncio.get_running_loop().time()
            with pytest.raises((ConnectionError, TimeoutError, OSError)):
                await asyncio.wait_for(
                    control.call(
                        EdgeOperation(
                            method="ReportResult",
                            arguments=[command.command_id, receipt.model_dump_json()],
                        )
                    ),
                    timeout=4,
                )
            assert asyncio.get_running_loop().time() - started < 4
            assert command.command_id not in control.sessions
            probe.delay = None
            probe.release.set()
            await asyncio.wait_for(probe.finished.wait(), timeout=2)
            retained = await wire._call("GetJobStatus", (command.command_id,))
            assert retained["state"] == "EXECUTING"
            assert retained["result"] is None and retained["result_sequence"] == 0
            duplicate = await control.call(
                EdgeOperation(method="BeginExecution", arguments=[command.command_id])
            )
            if duplicate["execute"]:
                execute_callback()
            assert duplicate["execute"] is False
            assert duplicate["reason"] == "QUERY_ORIGINAL_JOURNAL_DO_NOT_REPEAT"
            assert callbacks == [command.command_id]
            assert runtime.world().step == 1
            with plc.journal.connect() as db:
                rows = db.execute("SELECT permit FROM plc_commands").fetchall()
                assert len(rows) == 1 and rows[0][0] == claim["permit"]
                assert db.execute("SELECT count(*) FROM plc_results").fetchone()[0] == 0

    asyncio.run(scenario())
