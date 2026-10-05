import asyncio
import socket
import threading
import time
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
import uvicorn
from psycopg import sql
from psycopg.conninfo import make_conninfo

from robotops.cell.runtime import SyntheticRuntime
from robotops.domain.models import RobotCommand
from robotops.lab.config import LabConfig
from robotops.lab.edge import create_app as edge_app
from robotops.lab.journal import PLCJournal
from robotops.lab.opcua import VirtualPLC
from robotops.lab.transport import broker
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


@pytest.fixture
def lab_command(tmp_path, order_request):
    runtime = SyntheticRuntime(tmp_path / "runtime.db")
    store = Store(tmp_path / "workflow.db")
    engine = Engine(store, runtime)
    order = store.intake(order_request, "lab-test")
    engine.run(order.job_ids[0])
    job = store.job(order.job_ids[0])
    command = store.load(RobotCommand, job.command_id)
    # The plan is now immutable; execute against a fresh runtime with the same epoch.
    target = SyntheticRuntime(tmp_path / "target.db")
    target.reset(command.scene_epoch)
    return command, target


class RunningPLC:
    def __init__(self, path: Path):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        self.endpoint = f"opc.tcp://127.0.0.1:{port}/robotops/"
        self.path = path
        self.ready = threading.Event()
        self.loop = asyncio.new_event_loop()
        self.stop_event = None
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.error = None

    def run(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.serve())
        except BaseException as exc:
            self.error = exc
            self.ready.set()
        finally:
            self.loop.close()

    async def serve(self):
        self.stop_event = asyncio.Event()
        server = VirtualPLC(self.endpoint, PLCJournal(self.path))
        await server.start()
        self.ready.set()
        try:
            await self.stop_event.wait()
        finally:
            await server.stop()

    def start(self):
        self.thread.start()
        assert self.ready.wait(15)
        if self.error:
            raise self.error
        return self

    def stop(self):
        if not self.thread.is_alive():
            return
        self.loop.call_soon_threadsafe(self.stop_event.set)
        self.thread.join(15)
        assert not self.thread.is_alive()


@pytest.fixture
def running_plc(tmp_path):
    server = RunningPLC(tmp_path / "plc.db").start()
    try:
        yield server
    finally:
        server.stop()


@pytest.fixture
def lab_config(running_plc):
    original = LabConfig.from_env()
    schema = "lab_test_" + uuid4().hex
    with psycopg.connect(original.postgres_dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    config = replace(
        original,
        opcua_url=running_plc.endpoint,
        postgres_dsn=make_conninfo(original.postgres_dsn, options=f"-c search_path={schema}"),
        queue="robotops.test." + uuid4().hex,
        routing_key="test." + uuid4().hex,
    )
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    config = replace(config, edge_url=f"http://127.0.0.1:{port}")
    edge_server = uvicorn.Server(
        uvicorn.Config(
            edge_app(config, consume=False), host="127.0.0.1", port=port, log_level="error"
        )
    )
    edge_thread = threading.Thread(target=edge_server.run, daemon=True)
    edge_thread.start()
    deadline = time.monotonic() + 15
    while not edge_server.started and time.monotonic() < deadline:
        time.sleep(0.01)
    assert edge_server.started
    yield config
    edge_server.should_exit = True
    edge_thread.join(15)
    assert not edge_thread.is_alive()
    connection = broker(config)
    try:
        connection.channel().queue_delete(queue=config.queue)
    finally:
        connection.close()
    with psycopg.connect(original.postgres_dsn, autocommit=True) as db:
        db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
