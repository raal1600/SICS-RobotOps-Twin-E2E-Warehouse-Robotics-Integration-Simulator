from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse

from apps.api.playback import playback, visual_scene
from robotops.blender.adapter import BlenderRuntime
from robotops.blender.visualization import JobPlayback, VisualScene
from robotops.cell.controller import CellController
from robotops.cell.runtime import SyntheticRuntime
from robotops.domain.models import (
    AuditEvent,
    CellState,
    Contract,
    Fault,
    JobEvidence,
    Order,
    OrderRequest,
    PickJob,
    RobotCommand,
)
from robotops.observability.metrics import prometheus
from robotops.workflow.engine import Engine
from robotops.workflow.store import Conflict, NotFound, Store


class ExecutionRequest(Contract):
    fault: Fault | None = None


def create_app(store: Store, engine: Engine | None = None) -> FastAPI:
    workflow = engine or Engine(store, SyntheticRuntime(store.path.with_name("runtime.db")))
    app = FastAPI(
        title="RobotOps Twin",
        version="1.0",
        description=(
            "Local independent synthetic simulator. Completion means verified business outcome. "
            "No physical safety guarantees; bind to loopback only."
        ),
    )

    @app.exception_handler(Conflict)
    async def conflict_handler(request: Request, exc: Conflict) -> JSONResponse:
        return JSONResponse(status_code=409, content={"reason": str(exc)})

    @app.exception_handler(NotFound)
    async def not_found_handler(request: Request, exc: NotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"reason": "NOT_FOUND"})

    @app.post("/orders", response_model=Order, status_code=201)
    def create_order(
        payload: OrderRequest, idempotency_key: Annotated[str, Header(min_length=1, max_length=160)]
    ) -> Order:
        return store.intake(payload, idempotency_key)

    @app.get("/orders", response_model=list[Order])
    def orders() -> list[Order]:
        return store.orders()

    @app.get("/orders/{order_id}", response_model=Order)
    def order(order_id: str) -> Order:
        return store.order(order_id)

    @app.get("/orders/{order_id}/timeline", response_model=list[AuditEvent])
    def timeline(order_id: str) -> list[AuditEvent]:
        store.order(order_id)
        return store.timeline(order_id)

    @app.get("/jobs/{job_id}", response_model=PickJob)
    def job(job_id: str) -> PickJob:
        return store.job(job_id)

    @app.get("/health")
    def health() -> dict[str, str]:
        store.orders()
        return {"status": "ok", "scope": "synthetic-local-simulator"}

    @app.post("/jobs/{job_id}/run", response_model=PickJob)
    def run(job_id: str, request: ExecutionRequest) -> PickJob:
        return workflow.run(job_id, request.fault)

    @app.post("/jobs/{job_id}/reconcile", response_model=PickJob)
    def reconcile(job_id: str, request: ExecutionRequest) -> PickJob:
        return workflow.reconcile(job_id, request.fault)

    @app.get("/cell", response_model=CellState)
    def cell() -> CellState:
        return workflow.runtime.world().cell

    @app.get("/cell/scene", response_model=VisualScene)
    def scene() -> VisualScene:
        return visual_scene(workflow)

    @app.post("/cell/reset", response_model=CellState)
    def reset_cell() -> CellState:
        cell = CellController(workflow.runtime).reset()
        workflow.gateway.sync_events()
        return cell

    @app.get("/jobs/{job_id}/evidence", response_model=JobEvidence)
    def evidence(job_id: str) -> JobEvidence:
        return workflow.evidence(job_id)

    @app.get("/jobs/{job_id}/playback", response_model=JobPlayback)
    def recorded_motion(job_id: str) -> JobPlayback:
        return playback(workflow, job_id)

    @app.post("/jobs/{job_id}/playback/import", response_model=JobPlayback)
    def import_recorded_motion(job_id: str) -> JobPlayback:
        job = store.job(job_id)
        if not isinstance(workflow.runtime, BlenderRuntime) or job.command_id is None:
            raise HTTPException(409, "No original Blender animation")
        try:
            workflow.runtime.import_motion(store.load(RobotCommand, job.command_id))
        except (ValueError, OSError, TimeoutError) as exc:
            raise HTTPException(409, "Cannot load original Blender recording") from exc
        return playback(workflow, job_id)

    @app.get("/jobs/{job_id}/artifact.png", response_class=FileResponse)
    def job_artifact(job_id: str) -> FileResponse:
        job = store.job(job_id)
        path = None
        if isinstance(workflow.runtime, BlenderRuntime) and job.command_id:
            path = workflow.runtime.command_artifact(job.command_id, "capture.png")
        if path is None:
            raise HTTPException(404, "No Blender artifact for this job")
        return FileResponse(path, media_type="image/png")

    @app.get("/metrics", response_class=PlainTextResponse)
    def metrics() -> PlainTextResponse:
        workflow.gateway.sync_events()
        return PlainTextResponse(prometheus(store), media_type="text/plain; version=0.0.4")

    @app.get("/fixtures")
    def fixtures() -> dict[str, object]:
        return {
            "runtime": "blender" if isinstance(workflow.runtime, BlenderRuntime) else "headless",
            "products": [product.model_dump(mode="json") for product in workflow.settings.products],
            "source_id": workflow.settings.locations[0].location_id,
            "destination_id": workflow.settings.locations[1].location_id,
        }

    @app.get("/artifacts/latest.png", response_class=FileResponse)
    def artifact() -> FileResponse:
        path = (
            workflow.runtime.latest_artifact()
            if isinstance(workflow.runtime, BlenderRuntime)
            else None
        )
        if path is None:
            raise HTTPException(404, "No Blender artifact yet")
        return FileResponse(path, media_type="image/png")

    @app.get("/", response_class=FileResponse)
    def dashboard() -> FileResponse:
        return FileResponse(
            Path(__file__).parents[1] / "erp_ui" / "index.html", media_type="text/html"
        )

    @app.get("/ui/app.js", response_class=FileResponse)
    def javascript() -> FileResponse:
        return FileResponse(
            Path(__file__).parents[1] / "erp_ui" / "app.js", media_type="text/javascript"
        )

    @app.get("/ui/{script}", response_class=FileResponse)
    def playback_javascript(script: Literal["playback.js", "scene-view.js"]) -> FileResponse:
        return FileResponse(
            Path(__file__).parents[1] / "erp_ui" / script, media_type="text/javascript"
        )

    @app.get("/ui/vendor/{script}", response_class=FileResponse)
    def vendor_javascript(
        script: Literal["three.module.min.js", "three.core.min.js", "OrbitControls.js"],
    ) -> FileResponse:
        return FileResponse(
            Path(__file__).parents[1] / "erp_ui" / "vendor" / script,
            media_type="text/javascript",
        )

    return app
