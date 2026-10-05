"""Short transactions persist authorization before any bounded operation.

A crash after reservation remains EXECUTING_STAGE until explicit bounded recovery.
Expired nonphysical stages may resume using retained identities. A physical stage
only reconciles its original command or returns to the physical gate if dispatch
intent provably never committed. Recovery never dispatches a physical command.
"""

import hashlib
import json
import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from robotops.domain.models import AuditEvent, JobState, stable_id, utc_now
from robotops.integration.models import (
    AuthorizationDecision,
    AuthorizeStage,
    CreateSession,
    ExecutionSession,
)
from robotops.workflow.store import Conflict, NotFound, Store, digest, metadata


def sanitize(value: Any) -> Any:
    """Defense in depth for trace payloads, including credential-bearing URLs."""
    if isinstance(value, dict):
        return {
            str(k): "[REDACTED]"
            if any(
                secret in re.sub(r"[^a-z0-9]", "", str(k).lower())
                for secret in (
                    "password",
                    "secret",
                    "token",
                    "authorization",
                    "privatekey",
                    "connectionstring",
                    "apikey",
                    "credential",
                    "accesskey",
                )
            )
            else sanitize(v)
            for k, v in value.items()
        }
    if isinstance(value, (tuple, list)):
        return [sanitize(v) for v in value]
    if isinstance(value, str):
        value = re.sub(
            r"-----BEGIN (?:[A-Z ]* )?PRIVATE KEY-----.*?-----END (?:[A-Z ]* )?PRIVATE KEY-----",
            "[REDACTED PRIVATE KEY]",
            value,
            flags=re.DOTALL,
        )
        value = re.sub(r"(\w+://)[^/\s]+@", r"\1[REDACTED]@", value)
        value = re.sub(r"(?i)\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+", r"\1 [REDACTED]", value)
        value = re.sub(
            r"(?i)((?:password|passwd|token|secret|api[_-]?key|access[_-]?key|credential|authorization)\s*[=:]\s*)(?:\"[^\"]*\"|'[^']*'|[^\s&,;]+)",
            r"\1[REDACTED]",
            value,
        )
        return re.sub(r"(?i)\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+", r"\1 [REDACTED]", value)
    return value


class IntegrationStore:
    def __init__(self, store: Store):
        self.store = store
        with store.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS execution_sessions (
                    id TEXT PRIMARY KEY, request_id TEXT UNIQUE NOT NULL,
                    payload_hash TEXT NOT NULL, revision INTEGER NOT NULL, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS authorization_decisions (
                    id TEXT PRIMARY KEY, session_id TEXT NOT NULL, request_id TEXT NOT NULL,
                    payload_hash TEXT NOT NULL, body TEXT NOT NULL,
                    UNIQUE(session_id,request_id));
                CREATE TABLE IF NOT EXISTS integration_effects (
                    id TEXT PRIMARY KEY, kind TEXT NOT NULL, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS integration_outbox (
                    id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, body TEXT NOT NULL,
                    state TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS integration_inbox (
                    id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, body TEXT NOT NULL,
                    deliveries INTEGER NOT NULL);
            """)
            db.execute("INSERT OR IGNORE INTO meta VALUES ('guided_schema','1')")

    @contextmanager
    def _read(self) -> Iterator[sqlite3.Connection]:
        try:
            with self.store.readonly_connect() as db:
                yield db
        except sqlite3.OperationalError as exc:
            if "no such table" in str(exc):
                raise NotFound("GUIDED_STORE_NO_LONGER_EXISTS") from exc
            raise

    def get(self, ident: str) -> ExecutionSession:
        with self._read() as db:
            row = db.execute("SELECT body FROM execution_sessions WHERE id=?", (ident,)).fetchone()
        if row is None:
            raise NotFound(ident)
        return ExecutionSession.model_validate_json(row[0])

    def list(self) -> list[ExecutionSession]:
        with self._read() as db:
            rows = db.execute("SELECT body FROM execution_sessions ORDER BY id").fetchall()
        return [ExecutionSession.model_validate_json(row[0]) for row in rows]

    def prior_authorization(self, session_id: str, request_id: str) -> AuthorizationDecision | None:
        with self._read() as db:
            row = db.execute(
                "SELECT body FROM authorization_decisions WHERE session_id=? AND request_id=?",
                (session_id, request_id),
            ).fetchone()
        return AuthorizationDecision.model_validate_json(row[0]) if row else None

    def create(self, request: CreateSession) -> ExecutionSession:
        ident = stable_id(self.store.run_id, "session:" + request.request_id)
        session = ExecutionSession(
            session_id=ident,
            execution_session_id=ident,
            correlation_id=stable_id("order", request.request.order_id),
            request=request.request,
            request_id=request.request_id,
            order_id=request.request.order_id,
            fault=request.fault,
        )
        with self.store.transaction() as db:
            row = db.execute(
                "SELECT payload_hash,body FROM execution_sessions WHERE request_id=?",
                (request.request_id,),
            ).fetchone()
            if row:
                if row[0] != digest(request):
                    raise Conflict("SESSION_IDEMPOTENCY_CONFLICT")
                return ExecutionSession.model_validate_json(row[1])
            # A job can have only one guided authority, including before durable intake.
            for row in db.execute("SELECT body FROM execution_sessions").fetchall():
                if (
                    ExecutionSession.model_validate_json(row[0]).order_id
                    == request.request.order_id
                ):
                    raise Conflict("ORDER_ALREADY_HAS_EXECUTION_SESSION")
            if db.execute(
                "SELECT 1 FROM orders WHERE id=?", (request.request.order_id,)
            ).fetchone():
                raise Conflict("ORDER_ALREADY_INTAKEN_USE_NEW_GUIDED_ORDER")
            db.execute(
                "INSERT INTO execution_sessions VALUES (?,?,?,?,?)",
                (ident, request.request_id, digest(request), 0, session.model_dump_json()),
            )
        return session

    def reserve(
        self,
        ident: str,
        request: AuthorizeStage,
        *,
        recovery: bool = False,
        recovery_fault: str | None = None,
    ) -> tuple[ExecutionSession, bool]:
        request_hash = digest(request)
        if recovery_fault is not None:
            request_hash = hashlib.sha256(
                f"{request_hash}:recovery_fault:{recovery_fault}".encode()
            ).hexdigest()
        with self.store.transaction() as db:
            row = db.execute("SELECT body FROM execution_sessions WHERE id=?", (ident,)).fetchone()
            if row is None:
                raise NotFound(ident)
            session = ExecutionSession.model_validate_json(row[0])
            replay = db.execute(
                "SELECT payload_hash FROM authorization_decisions WHERE session_id=? AND request_id=?",
                (ident, request.request_id),
            ).fetchone()
            if replay:
                if replay[0] != request_hash:
                    raise Conflict("AUTHORIZATION_IDEMPOTENCY_CONFLICT")
                return session, False
            if (
                session.revision != request.expected_revision
                or session.current_stage != request.stage
            ):
                raise Conflict("AUTHORIZATION_REVISION_OR_STAGE_CONFLICT")
            allowed = (
                {"UNKNOWN_OUTCOME", "EXECUTING_STAGE"}
                if recovery
                else {"WAITING_AUTHORIZATION", "RETRYABLE_FAILURE"}
            )
            if session.status not in allowed:
                raise Conflict("SESSION_NOT_WAITING_AUTHORIZATION")
            decision = AuthorizationDecision(
                authorization_id=stable_id(ident, request.request_id),
                session_id=ident,
                request_id=request.request_id,
                stage=request.stage,
                expected_revision=request.expected_revision,
                decision=request.decision,
            )
            db.execute(
                "INSERT INTO authorization_decisions VALUES (?,?,?,?,?)",
                (
                    decision.authorization_id,
                    ident,
                    request.request_id,
                    request_hash,
                    decision.model_dump_json(),
                ),
            )
            session = session.model_copy(
                update={
                    "revision": session.revision + 1,
                    "status": "EXECUTING_STAGE",
                    "pending_authorization": None,
                    "updated_at": utc_now(),
                }
            )
            db.execute(
                "UPDATE execution_sessions SET revision=?,body=? WHERE id=?",
                (session.revision, session.model_dump_json(), ident),
            )
            return session, True

    def finish(self, session: ExecutionSession, reserved_revision: int) -> ExecutionSession:
        with self.store.transaction() as db:
            row = db.execute(
                "SELECT revision FROM execution_sessions WHERE id=?", (session.session_id,)
            ).fetchone()
            if row is None or row[0] != reserved_revision:
                raise Conflict("SESSION_COMPLETION_FENCED")
            db.execute(
                "UPDATE execution_sessions SET revision=?,body=? WHERE id=?",
                (session.revision, session.model_dump_json(), session.session_id),
            )
        return session

    def effect(self, ident: str, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(sanitize(payload), sort_keys=True)
        with self.store.transaction() as db:
            row = db.execute("SELECT body FROM integration_effects WHERE id=?", (ident,)).fetchone()
            if row:
                return dict(json.loads(row[0]))
            db.execute("INSERT INTO integration_effects VALUES (?,?,?)", (ident, kind, body))
        return dict(json.loads(body))

    def complete_business(self, session: ExecutionSession, ident: str) -> dict[str, Any]:
        """Commit ERP outcome only after each verified job has its durable WMS ACK."""
        with self.store.transaction() as db:
            jobs = [self.store._job(db, job_id) for job_id in session.job_ids]
            if not jobs or any(
                job.state not in {JobState.COMPLETED, JobState.FAILED} for job in jobs
            ):
                raise Conflict("VERIFIED_ORDER_OUTCOMES_REQUIRED")
            acknowledgement_ids = []
            for job in jobs:
                ack_id = stable_id(session.session_id, f"stage:20:{job.job_id}")
                row = db.execute(
                    "SELECT kind,body FROM integration_effects WHERE id=?", (ack_id,)
                ).fetchone()
                ack = json.loads(row[1]) if row else {}
                if (
                    row is None
                    or row[0] != "WMS_ACKNOWLEDGEMENT"
                    or ack.get("job_id") != job.job_id
                    or ack.get("command_id") != job.command_id
                    or ack.get("verified_outcome") != job.state.value
                    or ack.get("wms_acknowledged") is not True
                ):
                    raise Conflict("DURABLE_WMS_ACKNOWLEDGEMENT_REQUIRED_FOR_EVERY_JOB")
                acknowledgement_ids.append(ack_id)
            status = (
                JobState.COMPLETED
                if all(job.state == JobState.COMPLETED for job in jobs)
                else JobState.FAILED
            )
            payload = {
                "order_id": session.order_id,
                "business_status": status.value,
                "wms_acknowledged": True,
                "wms_acknowledgement_ids": acknowledgement_ids,
            }
            encoded = json.dumps(payload, sort_keys=True)
            previous = db.execute(
                "SELECT body FROM integration_effects WHERE id=?", (ident,)
            ).fetchone()
            if previous and previous[0] != encoded:
                raise Conflict("IMMUTABLE_BUSINESS_OUTCOME_CONFLICT")
            db.execute(
                "INSERT OR IGNORE INTO integration_effects VALUES (?,?,?)",
                (ident, "ERP_BUSINESS_STATUS", encoded),
            )
            db.execute(
                "INSERT OR IGNORE INTO meta VALUES (?,?)",
                ("guided_business:" + session.order_id, ident),
            )
            if not previous:
                self.store._event(
                    db,
                    AuditEvent(
                        **metadata(jobs[-1]),
                        event_id=stable_id(ident, "business-completed"),
                        component="erp",
                        event_type="ERP_BUSINESS_COMPLETED",
                        order_id=session.order_id,
                        state_before=JobState.RECONCILING,
                        state_after=status,
                        reason="VERIFIED_OUTCOMES_AND_DURABLE_WMS_ACKNOWLEDGEMENTS",
                        evidence_ids=(ident, *acknowledgement_ids),
                    ),
                )
            return payload

    def enqueue(self, command: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(command, sort_keys=True, separators=(",", ":"))
        hashed = hashlib.sha256(body.encode()).hexdigest()
        with self.store.transaction() as db:
            row = db.execute(
                "SELECT payload_hash FROM integration_outbox WHERE id=?", (command["command_id"],)
            ).fetchone()
            if row and row[0] != hashed:
                raise Conflict("OUTBOX_IDENTITY_CONFLICT")
            db.execute(
                "INSERT OR IGNORE INTO integration_outbox VALUES (?,?,?,?)",
                (command["command_id"], hashed, body, "PENDING"),
            )
        return {
            "message_id": command["command_id"],
            "payload_hash": hashed,
            "state": "PENDING",
            "network_side_effect": False,
        }

    def publish_local(self, command_id: str) -> dict[str, Any]:
        with self.store.transaction() as db:
            row = db.execute(
                "SELECT id FROM integration_outbox WHERE id=?", (command_id,)
            ).fetchone()
            if row is None:
                raise Conflict("OUTBOX_MISSING")
            db.execute(
                "UPDATE integration_outbox SET state='LOCAL_DELIVERED' WHERE id=?", (command_id,)
            )
        return {
            "message_id": command_id,
            "transport": "in-process",
            "publisher_confirm": False,
            "classification": "SIMULATED SYSTEM",
            "amqp_used": False,
        }

    def deliver_local(self, command_id: str) -> dict[str, Any]:
        with self.store.transaction() as db:
            row = db.execute(
                "SELECT payload_hash,body FROM integration_outbox WHERE id=?", (command_id,)
            ).fetchone()
            if row is None:
                raise Conflict("OUTBOX_MISSING")
            existing = db.execute(
                "SELECT payload_hash FROM integration_inbox WHERE id=?", (command_id,)
            ).fetchone()
            if existing and existing[0] != row[0]:
                raise Conflict("INBOX_IDENTITY_CONFLICT")
            db.execute(
                "INSERT OR IGNORE INTO integration_inbox VALUES (?,?,?,1)",
                (command_id, row[0], row[1]),
            )
            if existing:
                db.execute(
                    "UPDATE integration_inbox SET deliveries=deliveries+1 WHERE id=?", (command_id,)
                )
            count = db.execute(
                "SELECT deliveries FROM integration_inbox WHERE id=?", (command_id,)
            ).fetchone()[0]
        return {
            "message_id": command_id,
            "durable_inbox": True,
            "deliveries": count,
            "consumer_ack": "LOCAL_INBOX_COMMIT",
            "physical_effect": False,
        }
