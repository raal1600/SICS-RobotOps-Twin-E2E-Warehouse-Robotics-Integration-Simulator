"""REST mutations and strictly read-only persisted-session WebSocket snapshots."""

import asyncio
from contextlib import nullcontext
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import Field

from robotops.domain.models import Contract, Fault
from robotops.integration.engine import GuidedEngine
from robotops.integration.inspection import code_catalog, inspect_step
from robotops.integration.models import (
    AuthorizeStage,
    CreateSession,
    ExecutionSession,
    SourceReference,
)
from robotops.integration.source import current_source
from robotops.integration.store import sanitize
from robotops.workflow.engine import Engine
from robotops.workflow.store import Conflict, NotFound, Store


class ReconcileSession(Contract):
    request_id: str = Field(min_length=1, max_length=160)
    expected_revision: int = Field(ge=0)
    fault: Fault | None = None


def mount_guided_routes(app: FastAPI, store: Store | None, workflow: Engine | None) -> None:
    guided = GuidedEngine(workflow) if workflow is not None else None

    def get_guided() -> GuidedEngine:
        if guided is None:
            raise NotFound("original")
        return guided

    @app.post("/integration/sessions", response_model=ExecutionSession, status_code=201)
    @app.post("/v1/wms/tasks", response_model=ExecutionSession, status_code=202)
    def create_session(request: CreateSession) -> ExecutionSession:
        return get_guided().create(request)

    @app.get("/integration/sessions", response_model=list[ExecutionSession])
    def sessions() -> list[ExecutionSession]:
        engine = get_guided()
        return [engine.present(session) for session in engine.store.list()]

    @app.get("/integration/sessions/{session_id}", response_model=ExecutionSession)
    def session(session_id: str) -> ExecutionSession:
        return get_guided().get(session_id)

    @app.get("/integration/sessions/{session_id}/export")
    def export_session(session_id: str) -> dict[str, Any]:
        saved = get_guided().get(session_id)
        return dict(
            sanitize(
                {
                    "format": "robotops-guided-run-v1",
                    "scope": "Persisted session snapshot with stage records and evidence references. Referenced job records and motion files are not embedded.",
                    "session": saved.model_dump(mode="json"),
                }
            )
        )

    @app.get("/integration/sessions/{session_id}/steps/{step_id}/source")
    def step_source(session_id: str, step_id: str, component: str = "entry") -> dict[str, Any]:
        saved = get_guided().get(session_id)
        step = next((step for step in saved.steps if step.step_id == step_id), None)
        if step is None:
            raise NotFound(step_id)
        item = next((item for item in code_catalog(saved, step) if item["key"] == component), None)
        if item is None:
            raise NotFound(component)
        reference = (
            step.source
            if component == "entry"
            else SourceReference(path=item["path"], symbol=item["symbol"], excerpt="")
        )
        return {**current_source(reference), "component": component, "role": item["role"]}

    @app.get("/integration/sessions/{session_id}/steps/{step_id}/inspection")
    def step_inspection(session_id: str, step_id: str) -> dict[str, Any]:
        engine = get_guided()
        saved = engine.get(session_id)
        step = next((step for step in saved.steps if step.step_id == step_id), None)
        if step is None:
            raise NotFound(step_id)
        return inspect_step(engine.workflow, saved, step)

    @app.get("/integration/sessions/{session_id}/live")
    def live_protocol_status(session_id: str) -> dict[str, Any]:
        engine = get_guided()
        saved = engine.get(session_id)
        if engine.lab is not None and saved.command_id is not None:
            return dict(engine.lab.live_status(saved.command_id))
        return {
            "command_id": saved.command_id,
            "state": saved.status,
            "classification": "SIMULATED SYSTEM",
            "events": [],
            "meaning": "Local controller interface; live view below uses recorded simulator motion.",
        }

    @app.post("/integration/sessions/{session_id}/authorize", response_model=ExecutionSession)
    def authorize(session_id: str, request: AuthorizeStage) -> ExecutionSession:
        return get_guided().authorize(session_id, request)

    @app.post("/integration/sessions/{session_id}/reconcile", response_model=ExecutionSession)
    def reconcile(session_id: str, request: ReconcileSession) -> ExecutionSession:
        engine = get_guided()
        original = engine.get(session_id)
        previous = engine.store.prior_authorization(session_id, request.request_id)
        return engine.reconcile(
            session_id,
            AuthorizeStage(
                request_id=request.request_id,
                expected_revision=request.expected_revision,
                stage=previous.stage if previous else original.current_stage,
            ),
            request.fault,
        )

    @app.websocket("/integration/sessions/{session_id}/stream")
    async def stream(websocket: WebSocket, session_id: str) -> None:
        await websocket.accept()
        try:
            engine = get_guided()

            # No workflow/runtime method is called; opening/reconnecting is read-only.
            def read_snapshot() -> ExecutionSession:
                guard = websocket.scope.get("test_stream_read_guard")
                with guard() if guard is not None else nullcontext():
                    return engine.get(session_id)

            revision = -1
            while True:
                snapshot = await asyncio.to_thread(read_snapshot)
                if snapshot.revision != revision:
                    await websocket.send_json(snapshot.model_dump(mode="json"))
                    revision = snapshot.revision
                try:
                    message = await asyncio.wait_for(websocket.receive(), timeout=0.25)
                    if message["type"] == "websocket.disconnect":
                        return
                    # Client messages cannot grant authorization or mutate anything.
                    await websocket.send_json({"read_only": True, "revision": revision})
                except TimeoutError:
                    pass
        except NotFound:
            await websocket.close(code=4404)
        except Conflict:
            await websocket.close(code=4409)
        except WebSocketDisconnect:
            return
