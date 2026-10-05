"""Independent edge service: durable AMQP inbox and real OPC UA sessions."""

import asyncio
import json
import os
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Literal

import psycopg
from asyncua.client.client import Client
from asyncua.ua.uaerrors import UaStatusCodeError
from fastapi import FastAPI, HTTPException
from pydantic import Field

from robotops.domain.models import Contract, RobotCommand
from robotops.lab.config import LabConfig
from robotops.lab.opcua import NAMESPACE, Changes, OPCClient
from robotops.lab.transport import DeliveryStore, EdgeAdapter
from robotops.workflow.store import Conflict, digest


class EdgeOperation(Contract):
    method: (
        Literal[
            "SubmitJob",
            "GetJobStatus",
            "CheckPreconditions",
            "BeginExecution",
            "ReportResult",
            "AcknowledgeResult",
            "RestartController",
        ]
        | None
    ) = None
    arguments: list[Any] = Field(default_factory=list, max_length=3)


@dataclass
class ActiveSession:
    client: Client
    cell: Any
    index: int
    subscription: Any
    changes: Changes

    async def close(self) -> None:
        try:
            await self.subscription.delete()
        finally:
            await self.client.disconnect()


class EdgeControl:
    def __init__(self, config: LabConfig):
        self.config = config
        self.store = DeliveryStore(config)
        self.sessions: dict[str, ActiveSession] = {}
        self.expiry: set[asyncio.Task[None]] = set()

    async def expire(self, command_id: str, session: ActiveSession) -> None:
        # An abandoned API callback must not retain sockets indefinitely. Expiry
        # only closes transport; the durable PLC claim is never reset.
        await asyncio.sleep(180)
        if self.sessions.get(command_id) is session:
            self.sessions.pop(command_id)
            await session.close()

    async def begin(self, command_id: str) -> dict[str, Any]:
        client = Client(self.config.opcua_url, timeout=self.config.timeout)
        await client.connect()
        session = None
        try:
            index = await client.get_namespace_index(NAMESPACE)
            cell = await client.nodes.objects.get_child([f"{index}:RobotCell"])
            changes = Changes(lambda event: self.store.protocol_event(command_id, event))
            subscription = await client.create_subscription(50, changes)
            nodes = [
                await cell.get_child([f"{index}:{group}", f"{index}:{name}"])
                for group, name in [
                    ("Command", "State"),
                    ("Robot", "MotionPhase"),
                    ("Robot", "Ready"),
                ]
            ]
            await subscription.subscribe_data_change(nodes, queuesize=100)
            session = ActiveSession(client, cell, index, subscription, changes)
            result = json.loads(await cell.call_method(f"{index}:BeginExecution", command_id))
            if not result.get("execute"):
                await session.close()
                return dict(result)
            self.sessions[command_id] = session
            deadline = asyncio.get_running_loop().time() + 2
            while "EXECUTING" not in changes.values:
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    break
                changes.received.clear()
                try:
                    await asyncio.wait_for(changes.received.wait(), timeout=remaining)
                except TimeoutError:
                    break
            expiry = asyncio.create_task(self.expire(command_id, session))
            self.expiry.add(expiry)
            expiry.add_done_callback(self.expiry.discard)
            return {**result, "subscription_retained_during_callback": True}
        except BaseException:
            if self.sessions.get(command_id) is session:
                self.sessions.pop(command_id, None)
            if session:
                await session.close()
            else:
                await client.disconnect()
            raise

    async def call(self, request: EdgeOperation) -> dict[str, Any]:
        method = request.method
        arguments = request.arguments
        if method == "SubmitJob":
            command = RobotCommand.model_validate_json(str(arguments[0]))
            inbox = self.store.inbox(command.command_id)
            if inbox is None or inbox["payload_hash"] != digest(command):
                raise Conflict("DURABLE_EDGE_IDENTITY_REQUIRED")
        if method == "BeginExecution":
            result = await self.begin(str(arguments[0]))
        elif method == "ReportResult" and str(arguments[0]) in self.sessions:
            session = self.sessions.pop(str(arguments[0]))
            try:
                session.changes.received.clear()
                result = json.loads(
                    await session.cell.call_method(f"{session.index}:ReportResult", *arguments)
                )
                try:
                    await asyncio.wait_for(session.changes.received.wait(), timeout=2)
                except TimeoutError:
                    pass
            finally:
                await session.close()
        else:
            result = await OPCClient(self.config.opcua_url, self.config.timeout)._call(
                method, tuple(arguments)
            )
        return {
            **result,
            "protocol": "OPC UA",
            "classification": "REAL PROTOCOL",
            "opcua_client_component": "edge-adapter",
            "edge_process_id": os.getpid(),
            "edge_control_protocol": "REST/JSON",
            "method": method or "Browse/Subscribe",
        }

    async def close(self) -> None:
        for task in self.expiry:
            task.cancel()
        await asyncio.gather(*self.expiry, return_exceptions=True)
        for session in self.sessions.values():
            await session.close()
        self.sessions.clear()


def create_app(config: LabConfig | None = None, *, consume: bool = True) -> FastAPI:
    selected = config or LabConfig.from_env()
    control = EdgeControl(selected)
    stopped = threading.Event()

    def consumer() -> None:
        adapter = EdgeAdapter(selected)
        while not stopped.is_set():
            try:
                adapter.consume_one()
            except (OSError, psycopg.Error):
                stopped.wait(1)
            except ValueError:
                # The consumer already rejected malformed/conflicting delivery
                # without requeue. Keep serving subsequent legitimate commands.
                pass
            stopped.wait(0.1)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        worker = threading.Thread(target=consumer, daemon=True) if consume else None
        if worker:
            worker.start()
        try:
            yield
        finally:
            stopped.set()
            if worker:
                await asyncio.to_thread(worker.join, 15)
            await control.close()

    app = FastAPI(title="RobotOps edge adapter — real AMQP and OPC UA", lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, Any]:
        with control.store.connect() as db:
            db.execute("SELECT 1")
        return {"status": "ok", "component": "edge-adapter", "process_id": os.getpid()}

    @app.post("/v1/opcua")
    async def opcua(request: EdgeOperation) -> dict[str, Any]:
        try:
            return await control.call(request)
        except (UaStatusCodeError, Conflict, ValueError, IndexError):
            raise HTTPException(409, "EDGE_OPCUA_COMMAND_REJECTED") from None
        except (TimeoutError, OSError):
            raise HTTPException(503, "EDGE_OPCUA_UNAVAILABLE") from None

    return app
