"""SQLite repository: atomic intake, revision guards, causal events and fencing leases.

Transactions never include runtime calls. A committed command intent precedes dispatch.
"""

import hashlib
import json
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from robotops.domain.models import (
    ActionPlan,
    AuditEvent,
    Contract,
    JobState,
    Order,
    OrderRequest,
    PickJob,
    ReconciliationEvidence,
    Record,
    RobotCommand,
    RobotEvent,
    VerificationResult,
    new_id,
    stable_id,
    utc_now,
)
from robotops.workflow.states import RECONCILABLE, TERMINAL, guard


class Conflict(ValueError):
    pass


class NotFound(LookupError):
    pass


class OwnershipError(Conflict):
    pass


def digest(value: Contract) -> str:
    raw = json.dumps(value.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def metadata(
    record: Record, cause: str | None = None, now: datetime | None = None
) -> dict[str, Any]:
    return dict(
        run_id=record.run_id,
        correlation_id=record.correlation_id,
        causation_id=cause or record.causation_id,
        timestamp=now or utc_now(),
    )


@dataclass(frozen=True)
class Claim:
    job_id: str
    owner: str
    fence: int
    expires_at: datetime


class Store:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS records (
                    kind TEXT NOT NULL, id TEXT NOT NULL, body TEXT NOT NULL,
                    PRIMARY KEY(kind,id));
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS idempotency (
                    key TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, order_id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY, order_id TEXT NOT NULL, state TEXT NOT NULL,
                    revision INTEGER NOT NULL, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL,
                    order_id TEXT, job_id TEXT, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS lease (
                    cell_id TEXT PRIMARY KEY, job_id TEXT, owner TEXT, fence INTEGER NOT NULL,
                    expires TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            """)
            db.execute("INSERT OR IGNORE INTO meta VALUES ('run_id',?)", (new_id(),))
            self.run_id = str(db.execute("SELECT value FROM meta WHERE key='run_id'").fetchone()[0])

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA synchronous=FULL")
        db.execute("PRAGMA foreign_keys=ON")
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def readonly_connect(self) -> Iterator[sqlite3.Connection]:
        """Open an existing store without recreating a removed run database."""
        try:
            db = sqlite3.connect(
                self.path.resolve().as_uri() + "?mode=ro",
                uri=True,
                timeout=30,
                isolation_level=None,
            )
        except sqlite3.OperationalError as exc:
            if not self.path.is_file():
                raise NotFound("STORE_NO_LONGER_EXISTS") from exc
            raise
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA query_only=ON")
            yield db
        finally:
            db.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise

    @staticmethod
    def _record(db: sqlite3.Connection, ident: str, record: Contract) -> None:
        existing = db.execute(
            "SELECT body FROM records WHERE kind=? AND id=?", (type(record).__name__, ident)
        ).fetchone()
        body = record.model_dump_json()
        if existing and existing[0] != body:
            raise Conflict("IMMUTABLE_RECORD_CONFLICT")
        db.execute(
            "INSERT OR IGNORE INTO records VALUES (?,?,?)", (type(record).__name__, ident, body)
        )

    def save(self, ident: str, record: Contract) -> None:
        with self.transaction() as db:
            self._record(db, ident, record)

    def load[T: Contract](self, model: type[T], ident: str) -> T:
        with self.connect() as db:
            row = db.execute(
                "SELECT body FROM records WHERE kind=? AND id=?", (model.__name__, ident)
            ).fetchone()
            if row is None:
                raise NotFound(ident)
            return model.model_validate_json(row[0])

    @staticmethod
    def _job(db: sqlite3.Connection, job_id: str) -> PickJob:
        row = db.execute("SELECT body FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise NotFound(job_id)
        return PickJob.model_validate_json(row[0])

    def job(self, job_id: str) -> PickJob:
        with self.connect() as db:
            return self._job(db, job_id)

    @staticmethod
    def _write_job(db: sqlite3.Connection, job: PickJob) -> None:
        db.execute(
            "UPDATE jobs SET state=?,revision=?,body=? WHERE id=?",
            (job.state.value, job.revision, job.model_dump_json(), job.job_id),
        )

    @staticmethod
    def _event(db: sqlite3.Connection, event: AuditEvent) -> None:
        db.execute(
            "INSERT INTO events(id,order_id,job_id,body) VALUES (?,?,?,?)",
            (event.event_id, event.order_id, event.job_id, event.model_dump_json()),
        )

    @staticmethod
    def _last_cause(db: sqlite3.Connection, job: PickJob) -> str:
        row = db.execute(
            "SELECT id FROM events WHERE job_id=? ORDER BY sequence DESC LIMIT 1", (job.job_id,)
        ).fetchone()
        return str(row[0]) if row else job.causation_id

    def emit(
        self,
        job: PickJob,
        component: str,
        event_type: str,
        reason: str,
        *,
        evidence_ids: tuple[str, ...] = (),
        duration_ms: float = 0,
    ) -> AuditEvent:
        with self.transaction() as db:
            event = AuditEvent(
                **metadata(job, self._last_cause(db, job)),
                event_id=new_id(),
                component=component,
                event_type=event_type,
                reason=reason,
                order_id=job.order_id,
                job_id=job.job_id,
                command_id=job.command_id,
                duration_ms=duration_ms,
                evidence_ids=evidence_ids,
            )
            self._event(db, event)
            return event

    def ingest_robot_event(self, event: RobotEvent) -> None:
        """Import immutable controller events without granting access to world state."""
        body = event.model_dump(exclude={"scene_epoch", "step"})
        audit = AuditEvent.model_validate(body)
        with self.transaction() as db:
            existing = db.execute(
                "SELECT body FROM events WHERE id=?", (event.event_id,)
            ).fetchone()
            if existing:
                if existing[0] != audit.model_dump_json():
                    raise Conflict("EXTERNAL_EVENT_CONFLICT")
                return
            self._record(db, event.event_id, event)
            self._event(db, audit)

    def intake(
        self,
        request: OrderRequest,
        key: str,
        *,
        validate: Callable[[OrderRequest], None] | None = None,
    ) -> Order:
        if not key or len(key) > 160:
            raise ValueError("INVALID_IDEMPOTENCY_KEY")
        hashed = digest(request)
        with self.transaction() as db:
            row = db.execute(
                "SELECT payload_hash,order_id FROM idempotency WHERE key=?", (key,)
            ).fetchone()
            if row:
                if row[0] != hashed:
                    raise Conflict("IDEMPOTENCY_PAYLOAD_CONFLICT")
                return self._order(db, str(row[1]))
            existing = db.execute(
                "SELECT payload_hash FROM orders WHERE id=?", (request.order_id,)
            ).fetchone()
            if existing:
                if existing[0] != hashed:
                    raise Conflict("ORDER_ID_CONFLICT")
                db.execute(
                    "INSERT INTO idempotency VALUES (?,?,?)", (key, hashed, request.order_id)
                )
                return self._order(db, request.order_id)
            if db.execute("SELECT 1 FROM meta WHERE key='scene_reset'").fetchone():
                raise Conflict("SCENE_RESET_IN_PROGRESS")
            # Replays/conflicts retain their original semantics. Validate only
            # new intake, atomically before creating business or effect intent.
            if validate is not None:
                validate(request)
            now = utc_now()
            event_id = new_id()
            common = dict(
                run_id=self.run_id,
                correlation_id=stable_id("order", request.order_id),
                causation_id=event_id,
                timestamp=now,
            )
            jobs = tuple(
                PickJob(
                    **common,
                    job_id=stable_id(request.order_id, line.order_line_id),
                    order_id=request.order_id,
                    line=line,
                )
                for line in request.lines
            )
            order = Order(
                **common,
                order_id=request.order_id,
                lines=request.lines,
                job_ids=tuple(j.job_id for j in jobs),
            )
            db.execute(
                "INSERT INTO orders VALUES (?,?,?)",
                (order.order_id, hashed, order.model_dump_json()),
            )
            db.execute("INSERT INTO idempotency VALUES (?,?,?)", (key, hashed, order.order_id))
            self._event(
                db,
                AuditEvent(
                    **{**common, "causation_id": request.order_id},
                    event_id=event_id,
                    component="api",
                    event_type="ORDER_RECEIVED",
                    order_id=order.order_id,
                    reason="ACCEPTED",
                ),
            )
            for job in jobs:
                db.execute(
                    "INSERT INTO jobs VALUES (?,?,?,?,?)",
                    (job.job_id, order.order_id, job.state, job.revision, job.model_dump_json()),
                )
                self._event(
                    db,
                    AuditEvent(
                        **common,
                        event_id=new_id(),
                        component="workflow",
                        event_type="JOB_RECEIVED",
                        order_id=order.order_id,
                        job_id=job.job_id,
                        state_after=job.state,
                        reason="ORDER_LINE_CREATED",
                    ),
                )
            return order

    @staticmethod
    def _order(db: sqlite3.Connection, order_id: str) -> Order:
        row = db.execute("SELECT body FROM orders WHERE id=?", (order_id,)).fetchone()
        if row is None:
            raise NotFound(order_id)
        order = Order.model_validate_json(row[0])
        jobs = [Store._job(db, ident) for ident in order.job_ids]
        states = {job.state for job in jobs}
        if states == {JobState.COMPLETED}:
            status = JobState.COMPLETED
        else:
            priority = [
                JobState.REQUIRES_INTERVENTION,
                JobState.UNKNOWN_OUTCOME,
                JobState.RECONCILING,
                JobState.FAILED,
                JobState.EXECUTING,
                JobState.VERIFYING,
                JobState.READY_TO_EXECUTE,
                JobState.PLANNING,
                JobState.VALIDATED,
                JobState.RECEIVED,
            ]
            status = next(state for state in priority if state in states)
        if states <= TERMINAL and any(job.command_id is not None for job in jobs):
            guided = db.execute(
                "SELECT value FROM meta WHERE key=?", ("guided:" + order.job_ids[0],)
            ).fetchone()
            business = db.execute(
                "SELECT value FROM meta WHERE key=?", ("guided_business:" + order.order_id,)
            ).fetchone()
            if guided and business is None:
                # Verified physical success/failure is distinct from acknowledged
                # business completion. Pure planning rejection has no physical
                # command/outcome to reconcile and remains terminal FAILED.
                status = JobState.RECONCILING
        return order.model_copy(update={"status": status})

    def order(self, order_id: str) -> Order:
        with self.connect() as db:
            return self._order(db, order_id)

    def orders(self) -> list[Order]:
        with self.connect() as db:
            return [
                self._order(db, row[0])
                for row in db.execute("SELECT id FROM orders ORDER BY rowid")
            ]

    def execution_jobs(self) -> list[PickJob]:
        """Presentation ordering follows durable execution events, not order intake time."""
        with self.connect() as db:
            return [
                PickJob.model_validate_json(row[0])
                for row in db.execute("""
                SELECT j.body FROM jobs j LEFT JOIN (
                    SELECT job_id, MIN(sequence) AS started FROM events
                    WHERE json_extract(body, '$.state_after')='PLANNING' GROUP BY job_id
                ) e ON e.job_id=j.id
                ORDER BY e.started IS NULL, e.started, j.rowid
            """)
            ]

    def timeline(self, order_id: str | None = None) -> list[AuditEvent]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT body FROM events WHERE (? IS NULL OR order_id=?) ORDER BY sequence",
                (order_id, order_id),
            ).fetchall()
            return [AuditEvent.model_validate_json(row[0]) for row in rows]

    @staticmethod
    def _owned(db: sqlite3.Connection, claim: Claim, now: datetime) -> None:
        row = db.execute("SELECT * FROM lease WHERE cell_id='cell-1'").fetchone()
        if (
            row is None
            or row["job_id"] != claim.job_id
            or row["owner"] != claim.owner
            or row["fence"] != claim.fence
            or datetime.fromisoformat(row["expires"]) <= now
        ):
            raise OwnershipError("CLAIM_EXPIRED_OR_FENCED")

    def claim(
        self,
        job_id: str,
        owner: str,
        seconds: float,
        *,
        now: datetime | None = None,
        reconcile: bool = False,
    ) -> Claim | None:
        now = now or utc_now()
        with self.transaction() as db:
            job = self._job(db, job_id)
            if db.execute("SELECT 1 FROM meta WHERE key='scene_reset'").fetchone():
                return None
            if job.state in TERMINAL or (job.state in RECONCILABLE and not reconcile):
                return None
            row = db.execute("SELECT * FROM lease WHERE cell_id='cell-1'").fetchone()
            if row and row["job_id"] is not None and datetime.fromisoformat(row["expires"]) > now:
                return None
            # An uncertain different job quarantines the cell even after lease expiration.
            uncertain = db.execute("SELECT id,state FROM jobs WHERE id != ?", (job_id,)).fetchall()
            if any(JobState(r["state"]) in RECONCILABLE for r in uncertain):
                return None
            fence = int(row["fence"]) + 1 if row else 1
            expires = now + timedelta(seconds=seconds)
            db.execute(
                "INSERT OR REPLACE INTO lease VALUES ('cell-1',?,?,?,?)",
                (job_id, owner, fence, expires.isoformat()),
            )
            return Claim(job_id, owner, fence, expires)

    @staticmethod
    def _scene_reset_blocker(db: sqlite3.Connection) -> str | None:
        if db.execute(
            "SELECT 1 FROM jobs WHERE state NOT IN ('COMPLETED','FAILED') LIMIT 1"
        ).fetchone():
            return "SCENE_RESET_BLOCKED_UNRESOLVED_JOBS"
        lease = db.execute("SELECT * FROM lease WHERE cell_id='cell-1'").fetchone()
        if lease and lease["owner"] and datetime.fromisoformat(lease["expires"]) > utc_now():
            return "SCENE_RESET_BLOCKED_ACTIVE_WORKER"
        return None

    def scene_reset_blocker(self) -> str | None:
        with self.connect() as db:
            if db.execute("SELECT 1 FROM meta WHERE key='scene_reset'").fetchone():
                return "SCENE_RESET_IN_PROGRESS"
            return self._scene_reset_blocker(db)

    def test_operation_in_progress(self) -> bool:
        """A separate experiment may archive uncertainty, but never interrupt work."""
        with self.connect() as db:
            if db.execute("SELECT 1 FROM meta WHERE key='scene_reset'").fetchone():
                return True
            if db.execute(
                "SELECT 1 FROM jobs WHERE state IN "
                "('VALIDATED','PLANNING','READY_TO_EXECUTE','EXECUTING','VERIFYING','RECONCILING')"
            ).fetchone():
                return True
            lease = db.execute("SELECT * FROM lease WHERE cell_id='cell-1'").fetchone()
            return bool(
                lease and lease["owner"] and datetime.fromisoformat(lease["expires"]) > utc_now()
            )

    def pending_scene_reset(self) -> str | None:
        with self.connect() as db:
            row = db.execute("SELECT value FROM meta WHERE key='scene_reset'").fetchone()
            return str(row[0]) if row else None

    def begin_scene_reset(self) -> str:
        """Persist an exclusive maintenance intent; crashes never expire this guard."""
        with self.transaction() as db:
            pending = db.execute("SELECT value FROM meta WHERE key='scene_reset'").fetchone()
            if pending:
                return str(pending[0])
            reason = self._scene_reset_blocker(db)
            if reason:
                raise Conflict(reason)
            epoch = new_id()
            db.execute("INSERT INTO meta VALUES ('scene_reset',?)", (epoch,))
            self._event(
                db,
                AuditEvent(
                    run_id=self.run_id,
                    correlation_id=epoch,
                    causation_id=epoch,
                    timestamp=utc_now(),
                    event_id=stable_id(epoch, "requested"),
                    component="fixture",
                    event_type="SCENE_RESET_REQUESTED",
                    reason="EXPLICIT_FRESH_SCENE",
                ),
            )
            return epoch

    def finish_scene_reset(self, epoch: str) -> None:
        with self.transaction() as db:
            ident = stable_id(epoch, "completed")
            if db.execute("SELECT 1 FROM events WHERE id=?", (ident,)).fetchone():
                return
            pending = db.execute("SELECT value FROM meta WHERE key='scene_reset'").fetchone()
            if not pending or pending[0] != epoch:
                raise Conflict("SCENE_RESET_IDENTITY_MISMATCH")
            self._event(
                db,
                AuditEvent(
                    run_id=self.run_id,
                    correlation_id=epoch,
                    causation_id=stable_id(epoch, "requested"),
                    timestamp=utc_now(),
                    event_id=ident,
                    component="fixture",
                    event_type="SCENE_RESET_COMPLETED",
                    reason="PRODUCTS_RESTORED_HISTORY_RETAINED",
                ),
            )
            db.execute("DELETE FROM meta WHERE key='scene_reset' AND value=?", (epoch,))

    def release(self, claim: Claim) -> None:
        with self.transaction() as db:
            db.execute(
                "UPDATE lease SET job_id=NULL,owner=NULL WHERE cell_id='cell-1' AND fence=? AND owner=?",
                (claim.fence, claim.owner),
            )

    def transition(
        self,
        job_id: str,
        target: JobState,
        reason: str,
        *,
        claim: Claim,
        evidence: VerificationResult | ReconciliationEvidence | None = None,
        now: datetime | None = None,
    ) -> PickJob:
        now = now or utc_now()
        with self.transaction() as db:
            self._owned(db, claim, now)
            if claim.job_id != job_id:
                raise OwnershipError("WRONG_JOB_CLAIM")
            job = self._job(db, job_id)
            guard(job, target, evidence)
            evidence_ids: tuple[str, ...] = ()
            if evidence is not None:
                ident = (
                    evidence.evidence_id
                    if isinstance(evidence, ReconciliationEvidence)
                    else evidence.verification_id
                )
                self._record(db, ident, evidence)
                evidence_ids = (ident,)
            event_id = new_id()
            updated = job.model_copy(
                update={
                    "state": target,
                    "revision": job.revision + 1,
                    "causation_id": event_id,
                    "timestamp": now,
                }
            )
            self._write_job(db, updated)
            self._event(
                db,
                AuditEvent(
                    **metadata(job, self._last_cause(db, job), now),
                    event_id=event_id,
                    component="workflow",
                    event_type="JOB_TRANSITION",
                    order_id=job.order_id,
                    job_id=job_id,
                    command_id=job.command_id,
                    state_before=job.state,
                    state_after=target,
                    reason=reason,
                    evidence_ids=evidence_ids,
                ),
            )
            return updated

    def prepare(self, claim: Claim, plan: ActionPlan, command: RobotCommand) -> PickJob:
        with self.transaction() as db:
            self._owned(db, claim, utc_now())
            job = self._job(db, claim.job_id)
            if (
                job.state != JobState.PLANNING
                or plan.job_id != job.job_id
                or command.job_id != job.job_id
            ):
                raise Conflict("INVALID_COMMAND_INTENT")
            if command.action_plan_id != plan.action_plan_id:
                raise Conflict("PLAN_IDENTITY_MISMATCH")
            self._record(db, plan.action_plan_id, plan)
            self._record(db, command.command_id, command)
            # Guided command intent and outbox commit atomically before network I/O.
            if db.execute("SELECT 1 FROM meta WHERE key=?", ("guided:" + job.job_id,)).fetchone():
                body = json.dumps(
                    command.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
                )
                db.execute(
                    "INSERT OR IGNORE INTO integration_outbox VALUES (?,?,?,?)",
                    (command.command_id, digest(command), body, "PENDING"),
                )
            updated = job.model_copy(
                update={
                    "action_plan_id": plan.action_plan_id,
                    "command_id": command.command_id,
                    "revision": job.revision + 1,
                }
            )
            self._write_job(db, updated)
            self._event(
                db,
                AuditEvent(
                    **metadata(job, self._last_cause(db, job)),
                    event_id=command.command_id,
                    component="validator",
                    event_type="COMMAND_INTENT",
                    order_id=job.order_id,
                    job_id=job.job_id,
                    command_id=command.command_id,
                    reason="VALIDATED_DURABLE_COMMAND",
                    evidence_ids=(plan.action_plan_id,),
                ),
            )
            return updated

    def recoverable(self) -> list[PickJob]:
        with self.connect() as db:
            jobs = [PickJob.model_validate_json(r[0]) for r in db.execute("SELECT body FROM jobs")]
            # An inconclusive intervention remains paused across restart until
            # the operator explicitly requests another observation.
            return [
                job for job in jobs if job.state not in TERMINAL | {JobState.REQUIRES_INTERVENTION}
            ]

    def records_for_job[T: Contract](self, model: type[T], job_id: str) -> tuple[T, ...]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT body FROM records WHERE kind=? AND json_extract(body,'$.job_id')=? "
                "ORDER BY rowid",
                (model.__name__, job_id),
            ).fetchall()
            return tuple(model.model_validate_json(row[0]) for row in rows)
