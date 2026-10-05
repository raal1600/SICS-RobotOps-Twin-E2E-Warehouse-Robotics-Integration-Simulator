"""Single retained lab cell API. Business/session durability is PostgreSQL."""

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from apps.api.app import create_app as application
from apps.api.cell_profiles import CellProfiles, cell_profiles, profile_for
from apps.api.test_sessions import SimulationTest, TestHistory
from robotops.blender.adapter import BlenderRuntime
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.lab.config import LabConfig
from robotops.lab.postgres import PostgreSQLStore
from robotops.lab.transport import LabBridge
from robotops.workflow.engine import Engine


def create_app() -> FastAPI:
    config = LabConfig.from_env()
    root = Path(os.getenv("ROBOTOPS_LAB_DATA", "runs/lab"))
    settings = Settings.hkm()
    runtime_name = os.getenv("ROBOTOPS_LAB_RUNTIME", "synthetic")
    if runtime_name not in {"synthetic", "blender"}:
        raise ValueError("ROBOTOPS_LAB_RUNTIME must be synthetic or blender")
    runtime_type = BlenderRuntime if runtime_name == "blender" else SyntheticRuntime
    runtime = runtime_type(root / "runtime.db", settings)
    store = PostgreSQLStore(config.postgres_dsn, root / "application.db")
    workflow = Engine(store, runtime, settings)
    workflow.lab = LabBridge(config, runtime)  # type: ignore[attr-defined]
    app = application(store, workflow, test_registry=False)
    app.state.workflow = workflow
    app.router.routes = [
        route for route in app.router.routes if getattr(route, "path", "") != "/health"
    ]

    @app.get("/health")
    def health() -> dict[str, Any]:
        with store.readonly_connect() as db:
            db.execute("SELECT 1").fetchone()
        return {
            "status": "ok",
            "process_id": os.getpid(),
            "profile": "lab",
            "database": "PostgreSQL",
            "scope": "independent synthetic simulator; real AMQP and OPC UA",
            "runtime": runtime_name,
            "capabilities": {
                "test_lifecycle": False,
                "guided_execution": True,
                "distributed_protocols": True,
            },
        }

    @app.get("/simulation-tests", response_model=TestHistory)
    def history() -> TestHistory:
        orders = store.orders()
        profile = profile_for(settings)
        return TestHistory(
            active_test_id="original",
            tests=[
                SimulationTest(
                    test_id="original",
                    number=1,
                    created_at=runtime.world().timestamp,
                    active=True,
                    order_count=len(orders),
                    outcomes=[order.status for order in orders],
                    cell_profile_id=profile.cell_profile_id,
                    cell_display_name=profile.display_name,
                )
            ],
        )

    @app.get("/cell-profiles", response_model=CellProfiles)
    def profiles() -> CellProfiles:
        return cell_profiles()

    return app
