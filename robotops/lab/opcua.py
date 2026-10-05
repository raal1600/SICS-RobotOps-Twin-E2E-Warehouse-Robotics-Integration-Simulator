"""Actual OPC UA binary TCP server/client for the synthetic PLC."""

import asyncio
import json
import os
from collections.abc import Callable
from typing import Any

from asyncua import ua
from asyncua.client.client import Client
from asyncua.common.methods import uamethod
from asyncua.server.server import Server

from robotops.domain.models import WorldState, utc_now
from robotops.lab.journal import PLCJournal

NAMESPACE = "urn:robotops:integration-lab:cell-1"


class VirtualPLC:
    def __init__(self, endpoint: str, journal: PLCJournal):
        self.endpoint = endpoint
        self.journal = journal
        self.server = Server()
        self.nodes: dict[str, Any] = {}

    async def start(self) -> None:
        await self.server.init()
        self.server.set_endpoint(self.endpoint)
        self.server.set_server_name("RobotOps synthetic virtual PLC — real OPC UA")
        self.server.set_security_policy([ua.SecurityPolicyType.NoSecurity])
        index = await self.server.register_namespace(NAMESPACE)
        cell = await self.server.nodes.objects.add_object(index, "RobotCell")
        retained = self.journal.latest() or {}
        for group, variables in {
            "Cell": {
                "State": "UNAVAILABLE_NO_WORLD_SNAPSHOT",
                "Generation": -1,
                "BootId": self.journal.boot_id,
                "ProcessId": os.getpid(),
                "FaultCode": "",
            },
            "Command": {
                "ActiveCommandId": retained.get("command_id", ""),
                "PayloadHash": retained.get("payload_hash", ""),
                "State": retained.get("state", "IDLE"),
                "ResultSequence": retained.get("result_sequence", 0),
                "LastResult": json.dumps(retained),
            },
            "Robot": {
                "Ready": False,
                "ActiveToolId": "UNAVAILABLE_NO_WORLD_SNAPSHOT",
                "TCPPose": "UNAVAILABLE_NO_WORLD_SNAPSHOT",
                "MotionPhase": "NO_COMMAND",
            },
        }.items():
            obj = await cell.add_object(index, group)
            for name, value in variables.items():
                self.nodes[f"{group}/{name}"] = await obj.add_variable(index, name, value)

        async def update(result: dict[str, Any]) -> str:
            for key, path in {
                "command_id": "Command/ActiveCommandId",
                "payload_hash": "Command/PayloadHash",
                "state": "Command/State",
                "result_sequence": "Command/ResultSequence",
            }.items():
                if key in result:
                    await self.nodes[path].write_value(result[key])
            await self.nodes["Command/LastResult"].write_value(json.dumps(result))
            return json.dumps(result)

        @uamethod
        async def submit(parent: Any, payload: str) -> str:
            return await update(self.journal.submit(json.loads(payload)))

        @uamethod
        async def status(parent: Any, command_id: str) -> str:
            return json.dumps(self.journal.status(command_id))

        @uamethod
        async def preconditions(parent: Any, command_id: str, snapshot: str) -> str:
            result = self.journal.preconditions(command_id, json.loads(snapshot))
            world = WorldState.model_validate_json(snapshot)
            await self.nodes["Cell/State"].write_value(world.cell.mode.value)
            await self.nodes["Cell/Generation"].write_value(result["cell_generation"])
            await self.nodes["Robot/Ready"].write_value(result["state"] == "READY")
            await self.nodes["Robot/TCPPose"].write_value(
                world.robot_state.tcp_pose.model_dump_json()
                if world.robot_state
                else "UNAVAILABLE_IN_LEGACY_RUNTIME"
            )
            await self.nodes["Robot/MotionPhase"].write_value(
                world.robot_state.motion_phase if world.robot_state else "READY"
            )
            if result["active_tool_id"]:
                await self.nodes["Robot/ActiveToolId"].write_value(result["active_tool_id"])
            return await update(result)

        @uamethod
        async def begin(parent: Any, command_id: str) -> str:
            result = self.journal.begin(command_id)
            if result.get("execute"):
                await self.nodes["Robot/Ready"].write_value(False)
                await self.nodes["Robot/MotionPhase"].write_value("EXECUTING_SIMULATED_CONTROLLER")
                await self.nodes["Robot/TCPPose"].write_value("UNAVAILABLE_DURING_MOTION")
            return await update(result)

        @uamethod
        async def result(parent: Any, command_id: str, payload: str) -> str:
            receipt = json.loads(payload)
            retained = self.journal.result(command_id, receipt)
            await self.nodes["Robot/MotionPhase"].write_value("CONTROLLER_" + receipt["status"])
            await self.nodes["Robot/Ready"].write_value(False)
            await self.nodes["Robot/TCPPose"].write_value("UNAVAILABLE_AWAITING_FRESH_OBSERVATION")
            await self.nodes["Cell/State"].write_value("RESULT_RETAINED_AWAITING_FRESH_OBSERVATION")
            if receipt.get("active_tool_id"):
                await self.nodes["Robot/ActiveToolId"].write_value(receipt["active_tool_id"])
            return await update(retained)

        @uamethod
        async def acknowledge(parent: Any, command_id: str, sequence: int) -> str:
            return await update(self.journal.acknowledge(command_id, sequence))

        @uamethod
        async def restart(parent: Any) -> str:
            result = self.journal.restart()
            await self.nodes["Cell/BootId"].write_value(result["boot_id"])
            await self.nodes["Cell/State"].write_value("UNAVAILABLE_AFTER_CONTROLLER_BOOT")
            await self.nodes["Robot/Ready"].write_value(False)
            await self.nodes["Robot/TCPPose"].write_value("UNAVAILABLE_AFTER_CONTROLLER_BOOT")
            await self.nodes["Robot/MotionPhase"].write_value("QUERY_RETAINED_COMMAND_JOURNAL")
            return json.dumps(result)

        for name, callback, inputs in [
            ("SubmitJob", submit, [ua.VariantType.String]),
            ("GetJobStatus", status, [ua.VariantType.String]),
            ("CheckPreconditions", preconditions, [ua.VariantType.String, ua.VariantType.String]),
            ("BeginExecution", begin, [ua.VariantType.String]),
            ("ReportResult", result, [ua.VariantType.String, ua.VariantType.String]),
            ("AcknowledgeResult", acknowledge, [ua.VariantType.String, ua.VariantType.Int64]),
            ("RestartController", restart, []),
        ]:
            await cell.add_method(index, name, callback, inputs, [ua.VariantType.String])
        await self.server.start()

    async def stop(self) -> None:
        await self.server.stop()


class Changes:
    def __init__(self, on_change: Callable[[dict[str, Any]], None] | None = None) -> None:
        self.values: list[Any] = []
        self.received = asyncio.Event()
        self.on_change = on_change

    def datachange_notification(self, node: Any, value: Any, data: Any) -> None:
        self.values.append(value)
        if self.on_change:
            self.on_change(
                {
                    "node": node.nodeid.to_string(),
                    "node_id": node.nodeid.to_string(),
                    "value": value,
                    "timestamp": utc_now().isoformat(),
                    "protocol": "OPC UA",
                    "classification": "REAL PROTOCOL",
                    "operation": "DataChangeNotification",
                }
            )
        self.received.set()


class OPCClient:
    def __init__(self, endpoint: str, timeout: float = 10):
        self.endpoint = endpoint
        self.timeout = timeout

    async def _call(self, method: str | None, args: tuple[Any, ...]) -> dict[str, Any]:
        async with Client(self.endpoint, timeout=self.timeout) as client:
            index = await client.get_namespace_index(NAMESPACE)
            cell = await client.nodes.objects.get_child([f"{index}:RobotCell"])
            children = await cell.get_children()
            state = await cell.get_child([f"{index}:Command", f"{index}:State"])
            changes = Changes()
            subscription = await client.create_subscription(50, changes)
            await subscription.subscribe_data_change(state)
            try:
                if method is None:
                    process = await cell.get_child([f"{index}:Cell", f"{index}:ProcessId"])
                    result: dict[str, Any] = {
                        "state": await state.read_value(),
                        "server_process_id": await process.read_value(),
                    }
                else:
                    result = json.loads(await cell.call_method(f"{index}:{method}", *args))
                try:
                    await asyncio.wait_for(changes.received.wait(), timeout=min(self.timeout, 2))
                except TimeoutError:
                    pass
                return {
                    **result,
                    "protocol": "OPC UA",
                    "classification": "REAL PROTOCOL",
                    "system": "SIMULATED SYSTEM",
                    "method": method or "Browse/Subscribe",
                    "namespace": NAMESPACE,
                    "browsed_children": len(children),
                    "subscription_created": True,
                    "subscription_notifications": changes.values,
                    "security_mode": "None (isolated development lab)",
                }
            finally:
                await subscription.delete()

    def call(self, method: str | None = None, *args: Any) -> dict[str, Any]:
        try:
            return asyncio.run(self._call(method, args))
        except (ConnectionError, TimeoutError, OSError):
            raise OSError("OPCUA_UNAVAILABLE_QUERY_ORIGINAL_COMMAND") from None
