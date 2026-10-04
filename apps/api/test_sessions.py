"""Independent experiments with durable identity, explicit deletion and bounded cleanup."""

import json
import shutil
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path
from uuid import UUID

from pydantic import AwareDatetime, Field, field_validator
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from apps.api.cell_profiles import CELL_PROFILE_SCHEMAS, HKM, LEGACY, profile_for, profile_settings
from robotops.blender.adapter import BlenderRuntime
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.domain.models import Contract, Identifier, JobState, utc_now
from robotops.workflow.engine import Engine
from robotops.workflow.store import Conflict, NotFound, Store


class StartTestRequest(Contract):
    request_id: UUID
    cell_profile_id: Identifier = "hkm_inspired_v1"


class DeleteTestRequest(Contract):
    request_id: UUID


class ClearTestsRequest(DeleteTestRequest):
    expected_test_ids: list[str] = Field(max_length=10000)

    @field_validator("expected_test_ids")
    @classmethod
    def valid_identities(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("DUPLICATE_TEST_ID")
        for value in values:
            if value != "original" and str(UUID(value)) != value:
                raise ValueError("INVALID_TEST_ID")
        return values


class SimulationTest(Contract):
    test_id: str
    number: int
    created_at: AwareDatetime
    active: bool
    order_count: int
    outcomes: list[JobState]
    cell_profile_id: Identifier
    cell_display_name: str


class TestHistory(Contract):
    active_test_id: str | None
    tests: list[SimulationTest]


class TestDeletion(Contract):
    request_id: UUID
    deleted_test_ids: list[str]
    cleanup_pending: bool
    history: TestHistory


TEST_SCHEMAS = (
    *CELL_PROFILE_SCHEMAS,
    StartTestRequest,
    DeleteTestRequest,
    ClearTestsRequest,
    SimulationTest,
    TestHistory,
    TestDeletion,
)


class TestRegistry:
    """Catalog writes serialize mutations; a separate barrier protects file lifetime.

    The DELETE-journal access database holds shared locks through complete HTTP responses.
    Normal reads remain available during motion. Deletion requires its exclusive lock,
    followed by the catalog lock, and cannot race a read, download, or world mutation.
    Tombstones commit before filesystem removal and survive failed cleanup/process restart.
    """

    def __init__(
        self,
        original: Engine | None = None,
        *,
        data_dir: Path | None = None,
        runtime_type: type[SyntheticRuntime] = SyntheticRuntime,
        settings: Settings | None = None,
    ):
        selected_dir = original.store.path.parent if original else data_dir
        if selected_dir is None:
            raise ValueError("WORKSPACE_DIRECTORY_REQUIRED")
        self.data_dir = selected_dir.resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.root = self.data_dir / "simulation-tests"
        self._plain_path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "catalog.db"
        self.barrier = self.root / "access.db"
        self._plain_path(self.path)
        self._plain_path(self.barrier)
        self.runtime_type = (
            (BlenderRuntime if isinstance(original.runtime, BlenderRuntime) else SyntheticRuntime)
            if original
            else runtime_type
        )
        self.settings = original.settings if original else (settings or Settings.hkm())
        self.original = original
        self.engines: dict[str, Engine] = {"original": original} if original else {}
        self.lock = threading.RLock()
        with closing(sqlite3.connect(self.barrier)) as barrier, barrier:
            if not barrier.execute("SELECT 1 FROM sqlite_master WHERE name='guard'").fetchone():
                barrier.execute("PRAGMA journal_mode=DELETE")
                barrier.execute("CREATE TABLE guard (id INTEGER PRIMARY KEY)")
                barrier.execute("INSERT INTO guard VALUES (1)")
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS tests (
                    number INTEGER PRIMARY KEY AUTOINCREMENT,
                    id TEXT UNIQUE NOT NULL, created TEXT NOT NULL,
                    cell_profile_id TEXT, deleted TEXT, cleanup_pending INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS active (id INTEGER PRIMARY KEY, test_id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS requests (
                    id TEXT PRIMARY KEY, payload TEXT NOT NULL, targets TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS workspace_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            """)
            original_paths = (
                (original.store.path, original.runtime.db.path)
                if original and isinstance(original.runtime, SyntheticRuntime)
                else (self.data_dir / "workflow.db", self.data_dir / "runtime.db")
            )
            for key, source in zip(("workflow_name", "runtime_name"), original_paths, strict=True):
                name = source.name if source.parent.resolve() == self.data_dir else "UNSAFE_PATH"
                if not db.execute("SELECT 1 FROM workspace_meta WHERE key=?", (key,)).fetchone():
                    db.execute("INSERT INTO workspace_meta VALUES (?,?)", (key, name))
            self.original_names = dict(db.execute("SELECT key,value FROM workspace_meta"))
            columns = {row[1] for row in db.execute("PRAGMA table_info(tests)")}
            for name, statement in (
                ("cell_profile_id", "ALTER TABLE tests ADD COLUMN cell_profile_id TEXT"),
                ("deleted", "ALTER TABLE tests ADD COLUMN deleted TEXT"),
                (
                    "cleanup_pending",
                    "ALTER TABLE tests ADD COLUMN cleanup_pending INTEGER NOT NULL DEFAULT 0",
                ),
            ):
                if name not in columns:
                    db.execute(statement)
            # Tombstones remain rows forever, so original cannot be reintroduced.
            if not db.execute("SELECT 1 FROM tests LIMIT 1").fetchone():
                db.execute(
                    "INSERT INTO tests(id,created,cell_profile_id) VALUES ('original',?,?)",
                    (utc_now().isoformat(), profile_for(self.settings).cell_profile_id),
                )
                db.execute("INSERT OR IGNORE INTO active VALUES (1,'original')")
        with self.access():
            with self.connect() as db:
                rows = db.execute("SELECT * FROM tests WHERE deleted IS NULL").fetchall()
            for row in rows:
                engine = self.engine(row["id"])
                if row["cell_profile_id"] != profile_for(engine.settings).cell_profile_id:
                    with self.connect() as db:
                        db.execute(
                            "UPDATE tests SET cell_profile_id=? WHERE id=?",
                            (profile_for(engine.settings).cell_profile_id, row["id"]),
                        )
            self.original = self.engines.get("original") if self.exists("original") else None
            if self.original is None:
                self.engines.pop("original", None)
        self.retry_cleanup()

    @staticmethod
    def _plain_path(path: Path) -> None:
        if path.is_symlink() or path.is_junction():
            raise Conflict("TEST_STORAGE_UNSAFE_PATH")

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
    def access(self, *, exclusive: bool = False) -> Iterator[None]:
        db = sqlite3.connect(self.barrier, timeout=0.2, isolation_level=None)
        try:
            try:
                db.execute("BEGIN EXCLUSIVE" if exclusive else "BEGIN")
                db.execute("SELECT id FROM guard WHERE id=1").fetchone()
            except sqlite3.OperationalError as exc:
                raise Conflict("TEST_OPERATION_IN_PROGRESS") from exc
            yield
        finally:
            db.rollback()
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
    def current(db: sqlite3.Connection) -> str | None:
        row = db.execute("SELECT test_id FROM active WHERE id=1").fetchone()
        return str(row[0]) if row else None

    def active_id(self) -> str | None:
        with self.connect() as db:
            return self.current(db)

    def exists(self, test_id: str) -> bool:
        with self.connect() as db:
            return bool(
                db.execute(
                    "SELECT 1 FROM tests WHERE id=? AND deleted IS NULL", (test_id,)
                ).fetchone()
            )

    def directory(self, test_id: str) -> Path:
        directory = self.data_dir if test_id == "original" else self.root / str(UUID(test_id))
        self._plain_path(self.data_dir)
        self._plain_path(self.root)
        self._plain_path(directory)
        expected = self.data_dir if test_id == "original" else self.root / test_id
        if (
            self.data_dir.resolve() != self.data_dir
            or self.root.resolve() != self.data_dir / "simulation-tests"
            or directory.resolve() != expected
        ):
            raise Conflict("TEST_STORAGE_UNSAFE_PATH")
        return directory

    def engine(self, test_id: str) -> Engine:
        with self.connect() as db:
            row = db.execute(
                "SELECT cell_profile_id FROM tests WHERE id=? AND deleted IS NULL", (test_id,)
            ).fetchone()
        if row is None:
            raise NotFound(test_id)
        with self.lock:
            if test_id not in self.engines:
                self.engines[test_id] = self.make_engine(test_id, row[0])
            return self.engines[test_id]

    def make_engine(self, test_id: str, profile_id: str | None = None) -> Engine:
        directory = self.directory(test_id)
        settings = (
            self.settings
            if test_id == "original"
            else Settings(visual_frame_seconds=self.settings.visual_frame_seconds)
            if profile_id == LEGACY.cell_profile_id
            else profile_settings(
                profile_id or HKM.cell_profile_id,
                visual_frame_seconds=self.settings.visual_frame_seconds,
            )
        )
        # Existing worlds resolve their persisted execution settings without migration.
        runtime_name = (
            self.original_names["runtime_name"] if test_id == "original" else "runtime.db"
        )
        workflow_name = (
            self.original_names["workflow_name"] if test_id == "original" else "workflow.db"
        )
        if any(
            name == "UNSAFE_PATH" or Path(name).name != name
            for name in (runtime_name, workflow_name)
        ):
            raise Conflict("TEST_STORAGE_UNSAFE_PATH")
        runtime = self.runtime_type(directory / runtime_name, settings)
        return Engine(Store(directory / workflow_name), runtime, runtime.settings)

    @contextmanager
    def mutation(self, test_id: str) -> Iterator[None]:
        with self.exclusive() as db:
            if not db.execute(
                "SELECT 1 FROM tests WHERE id=? AND deleted IS NULL", (test_id,)
            ).fetchone():
                raise NotFound(test_id)
            if self.current(db) != test_id:
                raise Conflict("TEST_ARCHIVED_READ_ONLY")
            yield

    @staticmethod
    def _request(db: sqlite3.Connection, request_id: UUID, payload: str) -> list[str] | None:
        row = db.execute("SELECT * FROM requests WHERE id=?", (str(request_id),)).fetchone()
        if row is None:
            return None
        if row["payload"] != payload:
            raise Conflict("TEST_REQUEST_CONFLICT")
        result: list[str] = json.loads(row["targets"])
        return result

    def start(self, request_id: UUID, cell_profile_id: str = "hkm_inspired_v1") -> SimulationTest:
        test_id = str(request_id)
        payload = json.dumps(["start", cell_profile_id])
        with self.access():
            with self.exclusive() as db:
                self._request(db, request_id, payload)
                row = db.execute("SELECT * FROM tests WHERE id=?", (test_id,)).fetchone()
                if row:
                    if row["cell_profile_id"] != cell_profile_id:
                        raise Conflict("TEST_REQUEST_CONFLICT")
                    if row["deleted"]:
                        raise Conflict("TEST_DELETED")
                else:
                    profile_settings(
                        cell_profile_id, visual_frame_seconds=self.settings.visual_frame_seconds
                    )
                    active = self.current(db)
                    if active and self.engine(active).store.test_operation_in_progress():
                        raise Conflict("TEST_OPERATION_IN_PROGRESS")
                    fresh = self.make_engine(test_id, cell_profile_id)
                    if profile_for(fresh.settings).cell_profile_id != cell_profile_id:
                        raise Conflict("CELL_PROFILE_STATE_MISMATCH")
                    db.execute(
                        "INSERT INTO tests(id,created,cell_profile_id) VALUES (?,?,?)",
                        (test_id, utc_now().isoformat(), cell_profile_id),
                    )
                    db.execute("INSERT OR REPLACE INTO active VALUES (1,?)", (test_id,))
                db.execute(
                    "INSERT OR IGNORE INTO requests VALUES (?,?,?)",
                    (test_id, payload, json.dumps([test_id])),
                )
            return next(item for item in self.history().tests if item.test_id == test_id)

    def history(self) -> TestHistory:
        with self.access():
            with self.connect() as db:
                active = self.current(db)
                rows = db.execute(
                    "SELECT * FROM tests WHERE deleted IS NULL ORDER BY number"
                ).fetchall()
            summaries = []
            for row in rows:
                engine = self.engine(row["id"])
                profile = profile_for(engine.settings)
                summaries.append(
                    SimulationTest(
                        test_id=row["id"],
                        number=row["number"],
                        created_at=row["created"],
                        active=row["id"] == active,
                        order_count=len(engine.store.orders()),
                        outcomes=[job.state for job in engine.store.execution_jobs()],
                        cell_profile_id=profile.cell_profile_id,
                        cell_display_name=profile.display_name,
                    )
                )
            return TestHistory(active_test_id=active, tests=summaries)

    def _cleanup_paths(self, test_id: str) -> list[Path]:
        directory = self.directory(test_id)
        stems = (self.original_names["workflow_name"], self.original_names["runtime_name"])
        if any(stem == "UNSAFE_PATH" or Path(stem).name != stem for stem in stems):
            raise Conflict("TEST_STORAGE_UNSAFE_PATH")
        paths = (
            [directory]
            if test_id != "original"
            else [
                directory / name
                for stem in stems
                for name in (stem, stem + "-wal", stem + "-shm", stem + "-journal")
            ]
            + [directory / "blender-artifacts"]
        )
        # Validate the whole finite subtree before touching any member. Never follow
        # links/junctions or recursively remove the workspace/catalog directory.
        for path in paths:
            self._plain_path(path)
            if path.exists() and path.is_dir():
                for child in path.rglob("*"):
                    self._plain_path(child)
                    if not child.resolve().is_relative_to(path.resolve()):
                        raise Conflict("TEST_STORAGE_UNSAFE_PATH")
        return paths

    def _cleanup(self, test_id: str) -> bool:
        try:
            for path in self._cleanup_paths(test_id):
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink(missing_ok=True)
        except (OSError, Conflict):
            return False
        self.engines.pop(test_id, None)
        with self.exclusive() as db:
            db.execute("UPDATE tests SET cleanup_pending=0 WHERE id=?", (test_id,))
        return True

    def retry_cleanup(self) -> None:
        with self.connect() as db:
            pending = db.execute(
                "SELECT id FROM tests WHERE deleted IS NOT NULL AND cleanup_pending=1"
            ).fetchall()
        if not pending:
            return
        try:
            with self.access(exclusive=True):
                for row in pending:
                    self._cleanup(row[0])
        except Conflict as exc:
            if str(exc) != "TEST_OPERATION_IN_PROGRESS":
                raise
            # Another host is serving a live response. Keep durable cleanup intent
            # for a later restart/explicit retry without interrupting that work.

    def delete(
        self,
        request_id: UUID,
        *,
        test_id: str | None = None,
        expected_test_ids: list[str] | None = None,
    ) -> TestDeletion:
        payload = json.dumps(
            ["delete", test_id]
            if test_id is not None
            else ["clear", sorted(expected_test_ids or [])]
        )
        with self.access(exclusive=True):
            with self.exclusive() as db:
                targets = self._request(db, request_id, payload)
                if targets is None:
                    live = [
                        row[0]
                        for row in db.execute(
                            "SELECT id FROM tests WHERE deleted IS NULL ORDER BY number"
                        )
                    ]
                    if test_id is not None:
                        if not db.execute("SELECT 1 FROM tests WHERE id=?", (test_id,)).fetchone():
                            raise NotFound(test_id)
                        targets = [test_id]
                    else:
                        if set(live) != set(expected_test_ids or []):
                            raise Conflict("TEST_HISTORY_CHANGED")
                        targets = live
                    for identity in targets:
                        if (
                            identity in live
                            and self.engine(identity).store.test_operation_in_progress()
                        ):
                            raise Conflict("TEST_OPERATION_IN_PROGRESS")
                        self._cleanup_paths(identity)
                    for identity in targets:
                        db.execute(
                            "UPDATE tests SET deleted=COALESCE(deleted,?),cleanup_pending=1 WHERE id=?",
                            (utc_now().isoformat(), identity),
                        )
                        db.execute("DELETE FROM active WHERE test_id=?", (identity,))
                    db.execute(
                        "INSERT INTO requests VALUES (?,?,?)",
                        (str(request_id), payload, json.dumps(targets)),
                    )
            pending = False
            for identity in targets:
                pending = not self._cleanup(identity) or pending
        return TestDeletion(
            request_id=request_id,
            deleted_test_ids=targets,
            cleanup_pending=pending,
            history=self.history(),
        )

    def recover(self) -> None:
        with self.access():
            identity = self.active_id()
            if identity is not None:
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
        # Management and static UI remain available in an empty workspace.
        if (
            path
            in {
                "/",
                "/simulation-tests",
                "/simulation-tests/clear",
                "/cell-profiles",
                "/health",
                "/openapi.json",
                "/docs",
                "/redoc",
            }
            or path.startswith("/ui/")
            or (
                path.startswith("/simulation-tests/")
                and path.endswith("/delete")
                and len(path.split("/")) == 4
            )
        ):
            await self.app(scope, receive, send)
            return
        identity = "original"
        target = self.app
        try:
            with self.registry.access():
                if path.startswith("/simulation-tests/"):
                    identity, separator, rest = path[len("/simulation-tests/") :].partition("/")
                    if not separator or identity == "original":
                        raise NotFound(identity)
                    engine = self.registry.engine(identity)
                    if identity not in self.children:
                        from apps.api.app import create_app

                        self.children[identity] = create_app(
                            engine.store, engine, test_registry=False
                        )
                    target = self.children[identity]
                    scope = {**scope, "path": "/" + rest, "raw_path": ("/" + rest).encode()}
                else:
                    self.registry.engine(identity)
                read_only = identity != self.registry.active_id()
                scope = {**scope, "state": {**scope.get("state", {}), "test_read_only": read_only}}
                if scope["method"] not in {"GET", "HEAD", "OPTIONS"}:
                    with self.registry.mutation(identity):
                        await target(scope, receive, send)
                else:
                    await target(scope, receive, send)
        except (Conflict, NotFound) as exc:
            status = 409 if isinstance(exc, Conflict) else 404
            await JSONResponse({"reason": str(exc)}, status_code=status)(scope, receive, send)
