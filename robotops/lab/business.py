"""Synthetic WMS with real REST and durable idempotent acknowledgement."""

import hashlib
import json
import os
from typing import Any, Literal

import psycopg
from fastapi import FastAPI, HTTPException

from robotops.domain.models import Contract
from robotops.lab.config import LabConfig


class BusinessOutcome(Contract):
    command_id: str
    job_id: str
    verified_outcome: Literal["COMPLETED", "FAILED"]
    wms_acknowledged: Literal[True] = True
    physical_retry: Literal[False] = False


class AcknowledgeBusiness(Contract):
    outcome: BusinessOutcome
    fail_once: bool = False


def create_app(config: LabConfig | None = None) -> FastAPI:
    selected = config or LabConfig.from_env()
    with psycopg.connect(selected.postgres_dsn) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS lab_wms_acknowledgements (
                command_id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, payload TEXT NOT NULL,
                acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
                failures INTEGER NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0)
        """)
    app = FastAPI(title="Synthetic WMS — real REST protocol")

    @app.get("/health")
    def health() -> dict[str, Any]:
        with psycopg.connect(selected.postgres_dsn) as db:
            db.execute("SELECT 1")
        return {
            "status": "ok",
            "process_id": os.getpid(),
            "system": "SIMULATED WMS",
            "protocol": "REAL REST/JSON",
        }

    @app.post("/v1/wms/acknowledgements")
    def acknowledge(request: AcknowledgeBusiness) -> dict[str, Any]:
        body = json.dumps(request.outcome.model_dump(mode="json"), sort_keys=True)
        hashed = hashlib.sha256(body.encode()).hexdigest()
        unavailable = False
        with psycopg.connect(selected.postgres_dsn) as db:
            db.execute("SELECT pg_advisory_xact_lock(74829303)")
            row = db.execute(
                "SELECT payload_hash,acknowledged,failures,attempts "
                "FROM lab_wms_acknowledgements WHERE command_id=%s",
                (request.outcome.command_id,),
            ).fetchone()
            if row and row[0] != hashed:
                raise HTTPException(409, "WMS_COMMAND_PAYLOAD_CONFLICT")
            db.execute(
                "INSERT INTO lab_wms_acknowledgements(command_id,payload_hash,payload) "
                "VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                (request.outcome.command_id, hashed, body),
            )
            failures = row[2] if row else 0
            attempts = (row[3] if row else 0) + 1
            if request.fail_once and not failures and not (row and row[1]):
                unavailable = True
                db.execute(
                    "UPDATE lab_wms_acknowledgements SET failures=1,attempts=%s "
                    "WHERE command_id=%s",
                    (attempts, request.outcome.command_id),
                )
            else:
                db.execute(
                    "UPDATE lab_wms_acknowledgements SET acknowledged=TRUE,attempts=%s "
                    "WHERE command_id=%s",
                    (attempts, request.outcome.command_id),
                )
        if unavailable:
            # Fault record commits independently from the intentionally failed response.
            raise HTTPException(503, "WMS_UNAVAILABLE_RETRY_BUSINESS_ACK_ONLY")
        return {
            **request.outcome.model_dump(mode="json"),
            "attempts": attempts,
            "acknowledgement_id": "wms:" + request.outcome.command_id,
            "classification": "REAL PROTOCOL",
            "system": "SIMULATED WMS",
            "protocol": "REST/JSON",
            "http_status": 200,
            "payload_hash": hashed,
        }

    return app
