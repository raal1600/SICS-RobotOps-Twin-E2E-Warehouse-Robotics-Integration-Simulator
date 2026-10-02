from typing import Annotated

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse

from robotops.domain.models import AuditEvent, Order, OrderRequest, PickJob
from robotops.workflow.store import Conflict, NotFound, Store


def create_app(store: Store) -> FastAPI:
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

    return app
