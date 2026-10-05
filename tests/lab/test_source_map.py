"""Displayed source references must execute on the real distributed lab path."""

import socket
import sys
import threading
import time
from dataclasses import replace
from pathlib import Path

import pytest
import uvicorn

from robotops.cell.runtime import SyntheticRuntime
from robotops.integration.engine import GuidedEngine
from robotops.integration.models import AuthorizeStage, CreateSession
from robotops.lab.business import create_app as business_app
from robotops.lab.postgres import PostgreSQLStore
from robotops.lab.transport import EdgeAdapter, LabBridge
from robotops.workflow.engine import Engine

pytestmark = pytest.mark.lab_integration
ROOT = Path(__file__).resolve().parents[2]


def test_every_lab_stage_source_symbol_executes_and_excerpt_matches(
    lab_config, tmp_path, order_request
):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        business_port = listener.getsockname()[1]
    config = replace(lab_config, wms_url=f"http://127.0.0.1:{business_port}")
    server = uvicorn.Server(
        uvicorn.Config(
            business_app(config), host="127.0.0.1", port=business_port, log_level="error"
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.01)
    assert server.started
    stopped = threading.Event()
    errors = []

    def consume():
        adapter = EdgeAdapter(config)
        try:
            while not stopped.is_set():
                adapter.consume_one()
                stopped.wait(0.05)
        except BaseException as exc:
            errors.append(exc)

    consumer = threading.Thread(target=consume, daemon=True)
    consumer.start()
    runtime = SyntheticRuntime(tmp_path / "runtime.db")
    workflow = Engine(PostgreSQLStore(config.postgres_dsn, tmp_path / "application.db"), runtime)
    workflow.lab = LabBridge(config, runtime)
    guided = GuidedEngine(workflow)
    session = guided.create(CreateSession(request=order_request, request_id="source-audit"))
    filenames = {}
    try:
        for stage in range(1, 23):
            assert session.current_stage == stage
            calls = set()

            def profile(frame, event, arg, calls=calls):
                if event == "call":
                    raw = frame.f_code.co_filename
                    if raw not in filenames:
                        filename = Path(raw).resolve()
                        filenames[raw] = (
                            filename.relative_to(ROOT).as_posix()
                            if filename.is_relative_to(ROOT)
                            else None
                        )
                    if filenames[raw] is not None:
                        calls.add((filenames[raw], frame.f_code.co_qualname))

            previous = sys.getprofile()
            sys.setprofile(profile)
            try:
                session = guided.authorize(
                    session.session_id,
                    AuthorizeStage(
                        request_id=f"source:{stage}",
                        expected_revision=session.revision,
                        stage=stage,
                    ),
                )
            finally:
                sys.setprofile(previous)
            step = session.steps[-1]
            assert step.status == "COMPLETED", step.model_dump_json()
            assert (step.source.path, step.source.symbol) in calls
            actual = [line.strip() for line in (ROOT / step.source.path).read_text().splitlines()]
            excerpt = [line.strip() for line in step.source.excerpt.splitlines()]
            assert excerpt and any(
                actual[index : index + len(excerpt)] == excerpt for index in range(len(actual))
            )
            if stage in {12, 13, 14, 17}:
                assert ("robotops/lab/edge_rpc.py", "EdgeRPC.call") in calls
            if stage == 16:
                assert ("robotops/lab/edge_rpc.py", "EdgeRPC.execute") in calls
        assert session.status == "COMPLETED"
        assert runtime.recorded_journal(session.command_id).effect_count == 1
        assert not errors
    finally:
        stopped.set()
        consumer.join(15)
        server.should_exit = True
        thread.join(15)
        assert not consumer.is_alive() and not thread.is_alive()
