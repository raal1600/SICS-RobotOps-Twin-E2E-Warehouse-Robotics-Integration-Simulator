from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse

from apps.api.cell_profiles import CellProfiles, cell_profiles
from apps.api.guided import mount_guided_routes
from apps.api.playback import deliveries, delivery_playback, playback, visual_scene
from apps.api.test_sessions import (
    ClearTestRequest,
    ClearTestsRequest,
    DeleteTestRequest,
    SimulationTest,
    StartTestRequest,
    TestClearing,
    TestDeletion,
    TestHistory,
    TestRegistry,
    TestScopeMiddleware,
)
from robotops.blender.adapter import BlenderRuntime
from robotops.blender.visualization import (
    DeliveryPlayback,
    DeliverySummary,
    JobPlayback,
    VisualScene,
)
from robotops.cell.controller import CellController
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
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
from robotops.robotics.catalogue import load_catalogue
from robotops.workflow.engine import Engine
from robotops.workflow.store import Conflict, NotFound, Store


class ExecutionRequest(Contract):
    fault: Fault | None = None


def create_app(
    store: Store | None,
    engine: Engine | None = None,
    *,
    test_registry: bool = True,
    recover: bool = False,
    workspace_registry: TestRegistry | None = None,
) -> FastAPI:
    workflow = engine or (
        Engine(store, SyntheticRuntime(store.path.with_name("runtime.db"), Settings.hkm()))
        if store is not None
        else None
    )
    app = FastAPI(
        title="RobotOps Twin",
        version="1.0",
        description=(
            "Local independent synthetic simulator. Completion means verified business outcome. "
            "No physical safety guarantees; bind to loopback only."
            " Test history and creation use /simulation-tests. Original-world routes remain at /;"
            " other worlds use /simulation-tests/{test_id} plus the same route."
            " Only the active test accepts writes. Archives retain their original outcomes."
        ),
    )
    if test_registry:
        registry = workspace_registry or TestRegistry(workflow)
        app.state.test_registry = registry
        if recover:
            registry.recover()
        app.add_middleware(TestScopeMiddleware, registry=registry)

        @app.get("/simulation-tests", response_model=TestHistory)
        def test_history() -> TestHistory:
            return registry.history()

        @app.post("/simulation-tests", response_model=SimulationTest, status_code=201)
        def start_test(request: StartTestRequest) -> SimulationTest:
            return registry.start(request.request_id, request.cell_profile_id)

        @app.get("/cell-profiles", response_model=CellProfiles)
        def available_cells() -> CellProfiles:
            return cell_profiles()

        @app.post("/simulation-tests/delete-all", response_model=TestDeletion)
        @app.post("/simulation-tests/clear", response_model=TestDeletion, deprecated=True)
        def clear_tests(request: ClearTestsRequest) -> TestDeletion:
            return registry.delete(request.request_id, expected_test_ids=request.expected_test_ids)

        @app.post("/simulation-tests/{test_id}/delete", response_model=TestDeletion)
        def delete_test(test_id: str, request: DeleteTestRequest) -> TestDeletion:
            return registry.delete(request.request_id, test_id=test_id)

        @app.post("/simulation-tests/{test_id}/clear", response_model=TestClearing)
        def clear_test(test_id: str, request: ClearTestRequest) -> TestClearing:
            return registry.clear(request.request_id, test_id, request.expected_revision)

    @app.exception_handler(Conflict)
    async def conflict_handler(request: Request, exc: Conflict) -> JSONResponse:
        return JSONResponse(status_code=409, content={"reason": str(exc)})

    @app.exception_handler(NotFound)
    async def not_found_handler(request: Request, exc: NotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"reason": "NOT_FOUND"})

    @app.get("/health")
    def health() -> dict[str, str]:
        # An intentionally empty workspace is a healthy application, not a missing robot.
        if test_registry:
            with registry.connect() as db:
                db.execute("SELECT 1").fetchone()
        elif store is not None:
            store.orders()
        return {"status": "ok", "scope": "synthetic-local-simulator"}

    mount_world_routes(app, store, workflow)

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

    @app.get("/ui/theme.css", response_class=FileResponse)
    def dashboard_styles() -> FileResponse:
        return FileResponse(
            Path(__file__).parents[1] / "erp_ui" / "theme.css", media_type="text/css"
        )

    @app.get("/ui/{script}", response_class=FileResponse)
    def playback_javascript(
        script: Literal[
            "playback.js",
            "scene-view.js",
            "workflow-guide.js",
            "integration-console.js",
            "workspace.js",
            "workspace.css",
        ],
    ) -> FileResponse:
        return FileResponse(
            Path(__file__).parents[1] / "erp_ui" / script,
            media_type="text/css" if script.endswith(".css") else "text/javascript",
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


def mount_world_routes(app: FastAPI, store: Store | None, workflow: Engine | None) -> None:
    mount_guided_routes(app, store, workflow)

    def get_store() -> Store:
        if store is None:
            raise NotFound("original")
        return store

    def get_workflow() -> Engine:
        if workflow is None:
            raise NotFound("original")
        return workflow

    @app.post("/orders", response_model=Order, status_code=201)
    def create_order(
        payload: OrderRequest, idempotency_key: Annotated[str, Header(min_length=1, max_length=160)]
    ) -> Order:
        if getattr(get_workflow(), "lab", None) is not None:
            raise Conflict("LAB_REQUIRES_VERSIONED_WMS_INTAKE")

        def validate_fixture(request: OrderRequest) -> None:
            products = {product.product_id for product in get_workflow().settings.products}
            for line in request.lines:
                if line.product_id not in products:
                    raise HTTPException(422, "PRODUCT_NOT_IN_FIXTURE")
                if line.source_id != get_workflow().settings.source_for(line.product_id):
                    raise HTTPException(422, "PRODUCT_SOURCE_MISMATCH")
                if line.destination_id != get_workflow().settings.destination_id:
                    raise HTTPException(422, "DESTINATION_MISMATCH")

        return get_store().intake(payload, idempotency_key, validate=validate_fixture)

    @app.get("/orders", response_model=list[Order])
    def orders() -> list[Order]:
        return get_store().orders()

    @app.get("/orders/{order_id}", response_model=Order)
    def order(order_id: str) -> Order:
        return get_store().order(order_id)

    @app.get("/orders/{order_id}/timeline", response_model=list[AuditEvent])
    def timeline(order_id: str) -> list[AuditEvent]:
        get_store().order(order_id)
        return get_store().timeline(order_id)

    @app.get("/jobs/{job_id}", response_model=PickJob)
    def job(job_id: str) -> PickJob:
        return get_store().job(job_id)

    @app.post("/jobs/{job_id}/run", response_model=PickJob)
    def run(job_id: str, request: ExecutionRequest) -> PickJob:
        if getattr(get_workflow(), "lab", None) is not None:
            raise Conflict("LAB_REQUIRES_BOUNDED_INTEGRATION_STAGES")
        return get_workflow().run(job_id, request.fault)

    @app.post("/jobs/{job_id}/reconcile", response_model=PickJob)
    def reconcile(job_id: str, request: ExecutionRequest) -> PickJob:
        """Collect fresh evidence for the original command, including after intervention.

        An explicit request may reopen REQUIRES_INTERVENTION through RECONCILING.
        Each attempt retains its evidence; insufficient evidence pauses the job again.
        No pick is sent. COMPLETED/FAILED jobs and archived tests cannot be reopened.
        """
        if get_workflow().is_guided(job_id):
            raise Conflict("GUIDED_JOB_REQUIRES_STAGE_AUTHORIZATION")
        return get_workflow().reconcile(job_id, request.fault)

    @app.get("/cell", response_model=CellState)
    def cell() -> CellState:
        return get_workflow().runtime.world().cell

    @app.get("/cell/scene", response_model=VisualScene)
    def scene() -> VisualScene:
        return visual_scene(get_workflow())

    @app.post("/fixtures/fresh-scene", response_model=VisualScene)
    def fresh_scene() -> VisualScene:
        try:
            get_workflow().start_fresh_scene()
        except (TimeoutError, OSError) as exc:
            raise HTTPException(
                503, "Scene preparation interrupted. Reopen the app to resume the saved request."
            ) from exc
        return visual_scene(get_workflow())

    @app.post("/cell/reset", response_model=CellState)
    def reset_cell() -> CellState:
        cell = CellController(get_workflow().runtime).reset()
        get_workflow().gateway.sync_events()
        return cell

    @app.get("/jobs/{job_id}/evidence", response_model=JobEvidence)
    def evidence(job_id: str) -> JobEvidence:
        return get_workflow().evidence(job_id)

    @app.get("/jobs/{job_id}/playback", response_model=JobPlayback)
    def recorded_motion(job_id: str) -> JobPlayback:
        return playback(get_workflow(), job_id)

    @app.get("/deliveries", response_model=list[DeliverySummary])
    def recorded_deliveries() -> list[DeliverySummary]:
        return deliveries(get_workflow())

    @app.get("/deliveries/{delivery_id}/playback", response_model=DeliveryPlayback)
    def recorded_delivery(delivery_id: str) -> DeliveryPlayback:
        return delivery_playback(get_workflow(), delivery_id)

    @app.post("/jobs/{job_id}/playback/import", response_model=JobPlayback)
    def import_recorded_motion(job_id: str) -> JobPlayback:
        job = get_store().job(job_id)
        runtime = get_workflow().runtime
        if not isinstance(runtime, BlenderRuntime) or job.command_id is None:
            raise HTTPException(409, "No original Blender animation")
        try:
            runtime.import_motion(get_store().load(RobotCommand, job.command_id))
        except (ValueError, OSError, TimeoutError) as exc:
            raise HTTPException(409, "Cannot load original Blender recording") from exc
        return playback(get_workflow(), job_id)

    @app.get("/jobs/{job_id}/artifact.png", response_class=FileResponse)
    def job_artifact(job_id: str) -> FileResponse:
        job = get_store().job(job_id)
        path = None
        runtime = get_workflow().runtime
        if isinstance(runtime, BlenderRuntime) and job.command_id:
            path = runtime.command_artifact(job.command_id, "capture.png")
        if path is None:
            raise HTTPException(404, "No Blender artifact for this job")
        return FileResponse(path, media_type="image/png")

    @app.get("/metrics", response_class=PlainTextResponse)
    def metrics() -> PlainTextResponse:
        return PlainTextResponse(prometheus(get_store()), media_type="text/plain; version=0.0.4")

    @app.get("/fixtures")
    def fixtures() -> dict[str, object]:
        world = get_workflow().runtime.world()
        return {
            "runtime": "blender"
            if isinstance(get_workflow().runtime, BlenderRuntime)
            else "headless",
            "products": [
                product.model_dump(mode="json") for product in get_workflow().settings.products
            ],
            "source_id": get_workflow().settings.locations[0].location_id,
            "product_sources": {
                product.product_id: get_workflow().settings.source_for(product.product_id)
                for product in get_workflow().settings.products
            },
            "destination_id": get_workflow().settings.destination_id,
            "robot_profile_version": get_workflow().settings.robot_profile_version,
            "catalogue": (
                load_catalogue().model_dump(mode="json") if get_workflow().settings.is_hkm else None
            ),
            "scene_epoch": world.scene_epoch,
            "inventory": [
                {"product_id": obj.product.product_id, "location_id": obj.location_id}
                for obj in world.objects
            ],
            "scene_reset_blocked_reason": get_store().scene_reset_blocker(),
        }

    @app.get("/artifacts/latest.png", response_class=FileResponse)
    def artifact() -> FileResponse:
        runtime = get_workflow().runtime
        path = runtime.latest_artifact() if isinstance(runtime, BlenderRuntime) else None
        if path is None:
            raise HTTPException(404, "No Blender artifact yet")
        return FileResponse(path, media_type="image/png")


def create_workspace_app(
    data_dir: Path,
    *,
    runtime_type: type[SyntheticRuntime] = SyntheticRuntime,
    settings: Settings | None = None,
    recover: bool = True,
) -> FastAPI:
    """Open the catalog before any runtime, including an intentionally empty workspace."""
    registry = TestRegistry(data_dir=data_dir, runtime_type=runtime_type, settings=settings)
    original = registry.original
    return create_app(
        original.store if original else None, original, recover=recover, workspace_registry=registry
    )
