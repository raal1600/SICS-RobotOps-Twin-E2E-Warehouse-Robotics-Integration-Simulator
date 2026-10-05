"""Independent experiments with durable identity, explicit deletion and bounded cleanup."""

import hashlib
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


class ClearTestRequest(DeleteTestRequest):
    expected_revision: int = Field(ge=1)


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
    revision: int = Field(default=1, ge=1)
    clearing: bool = False


class TestHistory(Contract):
    active_test_id: str | None
    tests: list[SimulationTest]


class TestDeletion(Contract):
    request_id: UUID
    deleted_test_ids: list[str]
    cleanup_pending: bool
    history: TestHistory


class TestClearing(Contract):
    request_id: UUID
    test_id: str
    cleanup_pending: bool
    history: TestHistory


TEST_SCHEMAS = (
    *CELL_PROFILE_SCHEMAS,
    StartTestRequest,
    DeleteTestRequest,
    ClearTestRequest,
    ClearTestsRequest,
    SimulationTest,
    TestHistory,
    TestDeletion,
    TestClearing,
)


class TestRegistry:
    """Catalog writes serialize mutations; a separate barrier protects file lifetime.

    The DELETE-journal access database holds shared locks through complete HTTP responses.
    Normal reads remain available during motion. Deletion requires its exclusive lock,
    followed by the catalog lock, and cannot race a read, download, or world mutation.
    Temporary cleanup intent commits before removal. Completed deletion removes the
    catalog entry; only anonymous request digests remain to reject stale retries.
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
        self.engine_revisions: dict[str, int] = {"original": 1} if original else {}
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
                CREATE TABLE IF NOT EXISTS request_guards (
                    id_digest TEXT PRIMARY KEY, payload_digest TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS workspace_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            """)
            db.execute("BEGIN IMMEDIATE")
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
                ("revision", "ALTER TABLE tests ADD COLUMN revision INTEGER NOT NULL DEFAULT 1"),
                ("clearing", "ALTER TABLE tests ADD COLUMN clearing INTEGER NOT NULL DEFAULT 0"),
                ("reset_settings", "ALTER TABLE tests ADD COLUMN reset_settings TEXT"),
            ):
                if name not in columns:
                    db.execute(statement)
            # A workspace marker, not deleted test rows, prevents empty restart
            # from recreating the original test. Existing live labels are preserved.
            initialized = db.execute(
                "SELECT 1 FROM workspace_meta WHERE key='initialized'"
            ).fetchone()
            if not initialized and not db.execute("SELECT 1 FROM tests LIMIT 1").fetchone():
                db.execute(
                    "INSERT INTO tests(id,created,cell_profile_id) VALUES ('original',?,?)",
                    (utc_now().isoformat(), profile_for(self.settings).cell_profile_id),
                )
                db.execute("INSERT OR IGNORE INTO active VALUES (1,'original')")
            db.execute("INSERT OR IGNORE INTO workspace_meta VALUES ('initialized','1')")
            if db.execute("SELECT 1 FROM sqlite_master WHERE name='requests'").fetchone():
                for row in db.execute("SELECT id,payload FROM requests").fetchall():
                    self._remember(db, UUID(row[0]), row[1])
                db.execute("DROP TABLE requests")
            for row in db.execute(
                "SELECT id,cell_profile_id FROM tests WHERE id!='original' AND cell_profile_id IS NOT NULL"
            ):
                # Also protect pre-receipt catalogs when their test is later deleted.
                self._remember(
                    db, UUID(row[0]), json.dumps(["start", row[1] or LEGACY.cell_profile_id])
                )
            db.commit()
        self.retry_cleanup()
        with self.access():
            with self.connect() as db:
                rows = db.execute(
                    "SELECT * FROM tests WHERE deleted IS NULL AND clearing=0"
                ).fetchall()
            for row in rows:
                engine = self.engine(row["id"])
                resolved_profile = profile_for(engine.settings).cell_profile_id
                with self.connect() as db:
                    if row["cell_profile_id"] != resolved_profile:
                        db.execute(
                            "UPDATE tests SET cell_profile_id=? WHERE id=?",
                            (resolved_profile, row["id"]),
                        )
                    if row["id"] != "original":
                        self._remember(db, UUID(row["id"]), json.dumps(["start", resolved_profile]))
            self.original = self.engines.get("original") if self.exists("original") else None
            if self.original is None:
                self.engines.pop("original", None)

    @staticmethod
    def _plain_path(path: Path) -> None:
        if path.is_symlink() or path.is_junction():
            raise Conflict("TEST_STORAGE_UNSAFE_PATH")

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=0.2, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA synchronous=FULL")
        db.execute("PRAGMA secure_delete=ON")
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
                "SELECT cell_profile_id,revision,clearing FROM tests WHERE id=? AND deleted IS NULL",
                (test_id,),
            ).fetchone()
        if row is None:
            raise NotFound(test_id)
        if row["clearing"]:
            raise Conflict("TEST_CLEAR_PENDING")
        with self.lock:
            if test_id not in self.engines or self.engine_revisions.get(test_id) != row["revision"]:
                self.engines[test_id] = self.make_engine(test_id, row[0])
                self.engine_revisions[test_id] = row["revision"]
            return self.engines[test_id]

    def make_engine(
        self, test_id: str, profile_id: str | None = None, reset_settings: Settings | None = None
    ) -> Engine:
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
        runtime = self.runtime_type(directory / runtime_name, reset_settings or settings)
        return Engine(Store(directory / workflow_name), runtime, runtime.settings)

    @contextmanager
    def mutation(self, test_id: str, expected_revision: int | None = None) -> Iterator[None]:
        with self.exclusive() as db:
            row = db.execute(
                "SELECT revision,clearing FROM tests WHERE id=? AND deleted IS NULL", (test_id,)
            ).fetchone()
            if row is None:
                raise NotFound(test_id)
            if db.execute("SELECT 1 FROM tests WHERE clearing=1 AND deleted IS NULL").fetchone():
                raise Conflict("TEST_CLEAR_PENDING")
            if expected_revision is not None and expected_revision != row["revision"]:
                raise Conflict("TEST_REVISION_CHANGED")
            if self.current(db) != test_id:
                raise Conflict("TEST_ARCHIVED_READ_ONLY")
            yield

    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    @classmethod
    def _request(cls, db: sqlite3.Connection, request_id: UUID, payload: str) -> bool:
        row = db.execute(
            "SELECT payload_digest FROM request_guards WHERE id_digest=?",
            (cls._hash(str(request_id)),),
        ).fetchone()
        if row is None:
            return False
        if row[0] != cls._hash(payload):
            raise Conflict("TEST_REQUEST_CONFLICT")
        return True

    @classmethod
    def _remember(cls, db: sqlite3.Connection, request_id: UUID, payload: str) -> None:
        db.execute(
            "INSERT OR IGNORE INTO request_guards VALUES (?,?)",
            (cls._hash(str(request_id)), cls._hash(payload)),
        )

    @staticmethod
    def _next_number(db: sqlite3.Connection) -> int:
        used = {row[0] for row in db.execute("SELECT number FROM tests")}
        number = 1
        while number in used:
            number += 1
        return number

    def start(self, request_id: UUID, cell_profile_id: str = "hkm_inspired_v1") -> SimulationTest:
        test_id = str(request_id)
        payload = json.dumps(["start", cell_profile_id])
        with self.access():
            with self.exclusive() as db:
                known = self._request(db, request_id, payload)
                row = db.execute("SELECT * FROM tests WHERE id=?", (test_id,)).fetchone()
                if row:
                    if row["cell_profile_id"] != cell_profile_id:
                        raise Conflict("TEST_REQUEST_CONFLICT")
                    if row["deleted"]:
                        raise Conflict("TEST_DELETED")
                else:
                    if known:
                        raise Conflict("TEST_DELETED")
                    if db.execute(
                        "SELECT 1 FROM tests WHERE clearing=1 AND deleted IS NULL"
                    ).fetchone():
                        raise Conflict("TEST_CLEAR_PENDING")
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
                        "INSERT INTO tests(number,id,created,cell_profile_id) VALUES (?,?,?,?)",
                        (self._next_number(db), test_id, utc_now().isoformat(), cell_profile_id),
                    )
                    db.execute("INSERT OR REPLACE INTO active VALUES (1,?)", (test_id,))
                self._remember(db, request_id, payload)
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
                engine = None if row["clearing"] else self.engine(row["id"])
                profile = (
                    profile_for(engine.settings)
                    if engine
                    else (LEGACY if row["cell_profile_id"] == LEGACY.cell_profile_id else HKM)
                )
                summaries.append(
                    SimulationTest(
                        test_id=row["id"],
                        number=row["number"],
                        created_at=row["created"],
                        active=row["id"] == active,
                        order_count=len(engine.store.orders()) if engine else 0,
                        outcomes=[job.state for job in engine.store.execution_jobs()]
                        if engine
                        else [],
                        cell_profile_id=profile.cell_profile_id,
                        cell_display_name=profile.display_name,
                        revision=row["revision"],
                        clearing=bool(row["clearing"]),
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

    def _remove_world(self, test_id: str) -> bool:
        try:
            for path in self._cleanup_paths(test_id):
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink(missing_ok=True)
        except (OSError, Conflict):
            return False
        self.engines.pop(test_id, None)
        self.engine_revisions.pop(test_id, None)
        return True

    def _cleanup(self, test_id: str) -> bool:
        with self.connect() as db:
            row = db.execute("SELECT deleted FROM tests WHERE id=?", (test_id,)).fetchone()
        if row is None:
            return True
        if row[0] is None:
            raise Conflict("TEST_NOT_DELETED")
        if not self._remove_world(test_id):
            return False
        with self.exclusive() as db:
            db.execute("DELETE FROM tests WHERE id=?", (test_id,))
            db.execute(
                "UPDATE sqlite_sequence SET seq=(SELECT COALESCE(MAX(number),0) FROM tests) WHERE name='tests'"
            )
        return True

    def retry_cleanup(self) -> None:
        with self.connect() as db:
            pending = db.execute("SELECT id FROM tests WHERE deleted IS NOT NULL").fetchall()
            clearing = db.execute(
                "SELECT id FROM tests WHERE clearing=1 AND deleted IS NULL"
            ).fetchall()
        if not pending and not clearing:
            return
        try:
            with self.access(exclusive=True):
                for row in pending:
                    self._cleanup(row[0])
                for row in clearing:
                    self._finish_clear(row[0])
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
                known = self._request(db, request_id, payload)
                targets = [test_id] if test_id is not None else sorted(expected_test_ids or [])
                if not known:
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
                        clearing = db.execute(
                            "SELECT clearing FROM tests WHERE id=?", (identity,)
                        ).fetchone()[0]
                        if (
                            identity in live
                            and not clearing
                            and self.engine(identity).store.test_operation_in_progress()
                        ):
                            raise Conflict("TEST_OPERATION_IN_PROGRESS")
                        self._cleanup_paths(identity)
                    for identity in targets:
                        db.execute(
                            "UPDATE tests SET deleted=COALESCE(deleted,?),cleanup_pending=1,clearing=0,reset_settings=NULL WHERE id=?",
                            (utc_now().isoformat(), identity),
                        )
                        db.execute("DELETE FROM active WHERE test_id=?", (identity,))
                    self._remember(db, request_id, payload)
            pending = False
            for identity in targets:
                pending = not self._cleanup(identity) or pending
        return TestDeletion(
            request_id=request_id,
            deleted_test_ids=targets,
            cleanup_pending=pending,
            history=self.history(),
        )

    def _finish_clear(self, test_id: str) -> bool:
        """Resume the explicit reset before permitting any new work in that world."""
        with self.connect() as db:
            row = db.execute("SELECT * FROM tests WHERE id=? AND clearing=1", (test_id,)).fetchone()
        if row is None:
            return True
        if not self._remove_world(test_id):
            return False
        settings = Settings.model_validate_json(row["reset_settings"])
        fresh = self.make_engine(test_id, row["cell_profile_id"], settings)
        with self.exclusive() as db:
            db.execute("UPDATE tests SET clearing=0,reset_settings=NULL WHERE id=?", (test_id,))
            db.execute("INSERT OR REPLACE INTO active VALUES (1,?)", (test_id,))
        self.engines[test_id] = fresh
        self.engine_revisions[test_id] = row["revision"]
        return True

    def clear(self, request_id: UUID, test_id: str, expected_revision: int) -> TestClearing:
        payload = json.dumps(["reset", test_id, expected_revision])
        with self.access(exclusive=True):
            with self.exclusive() as db:
                known = self._request(db, request_id, payload)
                row = db.execute(
                    "SELECT * FROM tests WHERE id=? AND deleted IS NULL", (test_id,)
                ).fetchone()
                if row is None:
                    raise NotFound(test_id)
                if not known:
                    if row["revision"] != expected_revision:
                        raise Conflict("TEST_REVISION_CHANGED")
                    if not row["clearing"]:
                        if db.execute(
                            "SELECT 1 FROM tests WHERE clearing=1 AND deleted IS NULL"
                        ).fetchone():
                            raise Conflict("TEST_CLEAR_PENDING")
                        for identity in {test_id, self.current(db)}:
                            if (
                                identity is not None
                                and self.engine(identity).store.test_operation_in_progress()
                            ):
                                raise Conflict("TEST_OPERATION_IN_PROGRESS")
                        self._cleanup_paths(test_id)
                        settings = self.engine(test_id).settings.model_dump_json()
                        db.execute(
                            "UPDATE tests SET clearing=1,revision=revision+1,reset_settings=? WHERE id=?",
                            (settings, test_id),
                        )
                    self._remember(db, request_id, payload)
            # An old retry cannot clear a newer revision or erase its orders.
            pending = False
            if (
                not known
                or row["clearing"]
                and row["revision"] in {expected_revision, expected_revision + 1}
            ):
                pending = not self._finish_clear(test_id)
        return TestClearing(
            request_id=request_id, test_id=test_id, cleanup_pending=pending, history=self.history()
        )

    def recover(self) -> None:
        with self.access():
            identity = self.active_id()
            if identity is not None:
                with self.connect() as db:
                    if db.execute(
                        "SELECT 1 FROM tests WHERE clearing=1 AND deleted IS NULL"
                    ).fetchone():
                        return
                with self.mutation(identity):
                    self.engine(identity).recover()


class TestScopeMiddleware:
    def __init__(self, app: ASGIApp, registry: TestRegistry):
        self.app = app
        self.registry = registry
        self.children: dict[str, tuple[Engine, ASGIApp]] = {}
        self.original = registry.original

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
                "/simulation-tests/delete-all",
                "/cell-profiles",
                "/health",
                "/openapi.json",
                "/docs",
                "/redoc",
            }
            or path.startswith("/ui/")
            or (
                path.startswith("/simulation-tests/")
                and (path.endswith("/delete") or path.endswith("/clear"))
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
                    scope = {**scope, "path": "/" + rest, "raw_path": ("/" + rest).encode()}
                engine = self.registry.engine(identity)
                if identity != "original" or engine is not self.original:
                    cached = self.children.get(identity)
                    if cached is None or cached[0] is not engine:
                        from apps.api.app import create_app

                        cached = (engine, create_app(engine.store, engine, test_registry=False))
                        self.children[identity] = cached
                    target = cached[1]
                read_only = identity != self.registry.active_id()
                scope = {**scope, "state": {**scope.get("state", {}), "test_read_only": read_only}}
                if scope["method"] not in {"GET", "HEAD", "OPTIONS"}:
                    revision_header = dict(scope["headers"]).get(b"x-test-revision")
                    try:
                        revision = int(revision_header) if revision_header else None
                    except ValueError as exc:
                        raise Conflict("TEST_REVISION_CHANGED") from exc
                    with self.registry.mutation(identity, revision):
                        await target(scope, receive, send)
                else:
                    await target(scope, receive, send)
        except (Conflict, NotFound) as exc:
            status = 409 if isinstance(exc, Conflict) else 404
            await JSONResponse({"reason": str(exc)}, status_code=status)(scope, receive, send)
