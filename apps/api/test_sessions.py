"""Independent synthetic experiments; archived outcomes never become resolved by reset."""

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID

from pydantic import AwareDatetime
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from robotops.blender.adapter import BlenderRuntime
from robotops.cell.runtime import SyntheticRuntime
from robotops.domain.models import Contract, JobState, utc_now
from robotops.workflow.engine import Engine
from robotops.workflow.store import Conflict, NotFound, Store


class StartTestRequest(Contract):
    request_id: UUID


class SimulationTest(Contract):
    test_id: str
    number: int
    created_at: AwareDatetime
    active: bool
    order_count: int
    outcomes: list[JobState]


class TestHistory(Contract):
    active_test_id: str
    tests: list[SimulationTest]


TEST_SCHEMAS = (StartTestRequest, SimulationTest, TestHistory)


class TestRegistry:
    """SQLite serializes API mutations and test creation across host processes.

    The transaction spans a mutation, including Blender completion. Starting a
    new test cannot race an in-flight run/reconcile/reset. It never changes the
    old world's jobs, journal or scene. HTTP reads remain available during motion.
    """

    def __init__(self, original: Engine):
        self.original = original
        self.root = original.store.path.parent / "simulation-tests"
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "catalog.db"
        self.engines = {"original": original}
        self.lock = threading.RLock()
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS tests (
                    number INTEGER PRIMARY KEY AUTOINCREMENT,
                    id TEXT UNIQUE NOT NULL, created TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS active (id INTEGER PRIMARY KEY, test_id TEXT NOT NULL);
            """)
            db.execute(
                "INSERT INTO tests(id,created) SELECT 'original',? "
                "WHERE NOT EXISTS (SELECT 1 FROM tests WHERE id='original')",
                (utc_now().isoformat(),),
            )
            db.execute("INSERT OR IGNORE INTO active VALUES (1,'original')")

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=0.2, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA synchronous=FULL")
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def exclusive(self) -> Iterator[sqlite3.Connection]:
        with self.connect() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
            except sqlite3.OperationalError as exc:
                raise Conflict("TEST_OPERATION_IN_PROGRESS") from exc
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise

    @staticmethod
    def current(db: sqlite3.Connection) -> str:
        return str(db.execute("SELECT test_id FROM active WHERE id=1").fetchone()[0])

    def active_id(self) -> str:
        with self.connect() as db:
            return self.current(db)

    def engine(self, test_id: str) -> Engine:
        with self.connect() as db:
            if not db.execute("SELECT 1 FROM tests WHERE id=?", (test_id,)).fetchone():
                raise NotFound(test_id)
        with self.lock:
            if test_id not in self.engines:
                self.engines[test_id] = self.make_engine(test_id)
            return self.engines[test_id]

    def make_engine(self, test_id: str) -> Engine:
        # Only generated, catalogued UUIDs can select a directory.
        directory = self.root / str(UUID(test_id))
        settings = self.original.settings
        runtime_type = (
            BlenderRuntime
            if isinstance(self.original.runtime, BlenderRuntime)
            else SyntheticRuntime
        )
        return Engine(
            Store(directory / "workflow.db"),
            runtime_type(directory / "runtime.db", settings),
            settings,
        )

    @contextmanager
    def mutation(self, test_id: str) -> Iterator[None]:
        with self.exclusive() as db:
            if self.current(db) != test_id:
                raise Conflict("TEST_ARCHIVED_READ_ONLY")
            yield

    def start(self, request_id: UUID) -> SimulationTest:
        test_id = str(request_id)
        with self.exclusive() as db:
            # Re-delivery cannot archive another test or create another world.
            if not db.execute("SELECT 1 FROM tests WHERE id=?", (test_id,)).fetchone():
                previous = self.engine(self.current(db))
                if previous.store.test_operation_in_progress():
                    raise Conflict("TEST_OPERATION_IN_PROGRESS")
                # Initialize before committing the pointer. A crash leaves the old
                # active identity intact; an unlisted directory has no commands.
                self.make_engine(test_id)
                db.execute(
                    "INSERT INTO tests(id,created) VALUES (?,?)", (test_id, utc_now().isoformat())
                )
                db.execute("UPDATE active SET test_id=? WHERE id=1", (test_id,))
        return next(item for item in self.history().tests if item.test_id == test_id)

    def history(self) -> TestHistory:
        with self.connect() as db:
            active = self.current(db)
            rows = db.execute("SELECT * FROM tests ORDER BY number").fetchall()
        summaries = []
        for row in rows:
            store = self.engine(row["id"]).store
            summaries.append(
                SimulationTest(
                    test_id=row["id"],
                    number=row["number"],
                    created_at=row["created"],
                    active=row["id"] == active,
                    order_count=len(store.orders()),
                    outcomes=[job.state for job in store.execution_jobs()],
                )
            )
        return TestHistory(active_test_id=active, tests=summaries)

    def recover(self) -> None:
        identity = self.active_id()
        with self.mutation(identity):
            self.engine(identity).recover()


class TestScopeMiddleware:
    def __init__(self, app: ASGIApp, registry: TestRegistry):
        self.app = app
        self.registry = registry
        self.children: dict[str, ASGIApp] = {}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope["path"]
        identity = "original"
        target = self.app
        try:
            if path.startswith("/simulation-tests/"):
                identity, separator, rest = path[len("/simulation-tests/") :].partition("/")
                if not separator or identity == "original":
                    raise NotFound(identity)
                engine = self.registry.engine(identity)
                if identity not in self.children:
                    from apps.api.app import create_app

                    self.children[identity] = create_app(engine.store, engine, test_registry=False)
                target = self.children[identity]
                scope = {**scope, "path": "/" + rest, "raw_path": ("/" + rest).encode()}
            read_only = identity != self.registry.active_id()
            scope = {**scope, "state": {**scope.get("state", {}), "test_read_only": read_only}}
            if scope["method"] not in {"GET", "HEAD", "OPTIONS"} and path != "/simulation-tests":
                with self.registry.mutation(identity):
                    await target(scope, receive, send)
            else:
                await target(scope, receive, send)
        except (Conflict, NotFound) as exc:
            status = 409 if isinstance(exc, Conflict) else 404
            await JSONResponse({"reason": str(exc)}, status_code=status)(scope, receive, send)
