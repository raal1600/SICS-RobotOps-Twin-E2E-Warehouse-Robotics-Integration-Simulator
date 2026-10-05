"""Explicit test lifecycle actions never cross worlds or replay robot effects."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from threading import Event
from uuid import uuid4

import pytest
from fastapi.responses import FileResponse
from fastapi.testclient import TestClient

from apps.api.app import create_app, create_workspace_app
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.domain.models import Fault
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


def workspace(path, *, legacy=False):
    app = create_workspace_app(path, settings=Settings() if legacy else Settings.hkm())
    return app.state.test_registry, TestClient(app)


def start(client, request_id=None, profile="hkm_inspired_v1"):
    response = client.post(
        "/simulation-tests",
        json={
            "request_id": str(request_id or uuid4()),
            "cell_profile_id": profile,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["test_id"]


def delete(client, identity, request_id=None):
    return client.post(
        f"/simulation-tests/{identity}/delete",
        json={
            "request_id": str(request_id or uuid4()),
        },
    )


def clear(client, request_id=None, expected=None):
    if expected is None:
        expected = [test["test_id"] for test in client.get("/simulation-tests").json()["tests"]]
    return client.post(
        "/simulation-tests/clear",
        json={
            "request_id": str(request_id or uuid4()),
            "expected_test_ids": expected,
        },
    )


def run(client, prefix="", *, fault=None):
    fixture = client.get(prefix + "/fixtures").json()
    product = fixture["products"][0]["product_id"]
    order_id = str(uuid4())
    response = client.post(
        prefix + "/orders",
        headers={"Idempotency-Key": order_id},
        json={
            "order_id": order_id,
            "lines": [
                {
                    "order_line_id": "line",
                    "product_id": product,
                    "source_id": fixture["product_sources"][product],
                    "destination_id": fixture["destination_id"],
                }
            ],
        },
    )
    assert response.status_code == 201, response.text
    job_id = response.json()["job_ids"][0]
    response = client.post(prefix + f"/jobs/{job_id}/run", json={"fault": fault})
    assert response.status_code == 200, response.text
    return response.json()


def test_cell_selection_is_explicit_persisted_and_legacy_history_is_unchanged(tmp_path):
    registry, client = workspace(tmp_path, legacy=True)
    before = registry.engine("original").runtime.world().model_dump_json()
    profiles = client.get("/cell-profiles").json()
    assert profiles["default_cell_profile_id"] == "hkm_inspired_v1"
    assert [p["cell_profile_id"] for p in profiles["profiles"] if p["selectable"]] == [
        "hkm_inspired_v1"
    ]
    assert (
        client.get("/simulation-tests").json()["tests"][0]["cell_profile_id"]
        == "legacy_cartesian_v1"
    )
    identity = start(client)
    with registry.connect() as db:
        assert (
            db.execute("SELECT cell_profile_id FROM tests WHERE id=?", (identity,)).fetchone()[0]
            == "hkm_inspired_v1"
        )
    reopened, other = workspace(tmp_path)
    history = other.get("/simulation-tests").json()
    assert [t["cell_profile_id"] for t in history["tests"]] == [
        "legacy_cartesian_v1",
        "hkm_inspired_v1",
    ]
    assert len(other.get(f"/simulation-tests/{identity}/fixtures").json()["products"]) == 6
    assert reopened.engine("original").runtime.world().model_dump_json() == before


@pytest.mark.parametrize("profile", ["legacy_cartesian_v1", "unknown_cell"])
def test_unavailable_profile_rejected_before_creating_test_or_directory(tmp_path, profile):
    registry, client = workspace(tmp_path)
    identity = str(uuid4())
    response = client.post(
        "/simulation-tests", json={"request_id": identity, "cell_profile_id": profile}
    )
    assert response.status_code == 409
    assert response.json()["reason"] == "CELL_PROFILE_NOT_AVAILABLE"
    assert not (registry.root / identity).exists()
    assert [t["test_id"] for t in client.get("/simulation-tests").json()["tests"]] == ["original"]


def test_creation_uuid_conflicts_on_changed_profile_and_never_resurrects_deleted_test(tmp_path):
    registry, client = workspace(tmp_path)
    request_id = uuid4()
    identity = start(client, request_id)
    assert start(client, request_id) == identity
    response = client.post(
        "/simulation-tests",
        json={"request_id": str(request_id), "cell_profile_id": "legacy_cartesian_v1"},
    )
    assert response.status_code == 409 and response.json()["reason"] == "TEST_REQUEST_CONFLICT"
    assert delete(client, identity).status_code == 200
    response = client.post("/simulation-tests", json={"request_id": str(request_id)})
    assert response.status_code == 409 and response.json()["reason"] == "TEST_DELETED"
    assert not (registry.root / identity).exists()


def test_delete_archived_world_purges_only_its_evidence_and_blocks_cached_hosts(tmp_path):
    registry, client = workspace(tmp_path)
    identity = start(client)
    prefix = f"/simulation-tests/{identity}"
    job = run(client, prefix, fault=Fault.DROP_ACK_AFTER_EFFECT)
    newer = start(client)
    other_registry, other = workspace(tmp_path)
    assert other.get(prefix + f"/jobs/{job['job_id']}").status_code == 200
    directory = registry.root / identity
    artifacts = directory / "blender-artifacts" / "checkpoint"
    artifacts.mkdir(parents=True)
    (artifacts / "scene.blend").write_bytes(b"saved evidence")
    marker = tmp_path / "keep-user-file.txt"
    marker.write_text("keep")
    snapshot = registry.engine(newer).runtime.world().model_dump_json()
    response = delete(client, identity)
    assert response.status_code == 200, response.text
    assert response.json()["deleted_test_ids"] == [identity]
    assert response.json()["cleanup_pending"] is False
    assert response.json()["history"]["active_test_id"] == newer
    assert not directory.exists() and marker.read_text() == "keep"
    for viewer in (client, other):
        for route in (
            "/orders",
            "/fixtures",
            f"/jobs/{job['job_id']}/evidence",
            f"/jobs/{job['job_id']}/artifact.png",
        ):
            assert viewer.get(prefix + route).status_code == 404
        assert viewer.post(prefix + "/cell/reset").status_code == 404
    assert registry.engine(newer).runtime.world().model_dump_json() == snapshot
    assert other_registry.active_id() == newer


def test_delete_original_preserves_catalog_siblings_and_does_not_recreate_it_on_restart(
    tmp_path, monkeypatch
):
    registry, client = workspace(tmp_path)
    identity = start(client)
    (tmp_path / "unrelated.txt").write_text("keep")
    assert delete(client, "original").status_code == 200
    assert not (tmp_path / "workflow.db").exists()
    assert not (tmp_path / "runtime.db").exists()
    assert (registry.root / identity / "runtime.db").exists()
    assert registry.path.exists()
    constructor = SyntheticRuntime.__init__

    def observe_init(self, path, settings=None):
        assert path != tmp_path / "runtime.db", "Deleted original must not be constructed"
        constructor(self, path, settings)

    monkeypatch.setattr(SyntheticRuntime, "__init__", observe_init)
    _, reopened = workspace(tmp_path)
    assert reopened.get("/orders").status_code == 404
    assert reopened.get("/").status_code == 200
    assert reopened.get(f"/simulation-tests/{identity}/fixtures").status_code == 200
    assert (tmp_path / "unrelated.txt").read_text() == "keep"
    assert not (tmp_path / "runtime.db").exists()


def test_deleting_active_does_not_activate_or_recover_uncertain_archive(tmp_path):
    registry, client = workspace(tmp_path)
    old = run(client, fault=Fault.DROP_ACK_AFTER_EFFECT)
    before = registry.engine("original").store.timeline()
    identity = start(client)
    response = delete(client, identity)
    assert response.json()["history"]["active_test_id"] is None
    assert response.json()["history"]["tests"][0]["active"] is False
    reopened, other = workspace(tmp_path)
    assert other.get(f"/jobs/{old['job_id']}").json()["state"] == "UNKNOWN_OUTCOME"
    assert other.post(f"/jobs/{old['job_id']}/reconcile", json={}).status_code == 409
    assert reopened.engine("original").store.timeline() == before
    new = start(other)
    assert other.get("/simulation-tests").json()["active_test_id"] == new


def test_delete_last_test_leaves_empty_usable_workspace_and_restarts_at_test_one(tmp_path):
    registry, client = workspace(tmp_path)
    response = delete(client, "original")
    assert response.status_code == 200
    assert response.json()["history"] == {
        "schema_version": "1.0",
        "active_test_id": None,
        "tests": [],
    }
    _, other = workspace(tmp_path)
    assert other.get("/simulation-tests").json()["tests"] == []
    for route in ("/", "/ui/app.js", "/cell-profiles", "/health"):
        assert other.get(route).status_code == 200
    identity = start(other)
    assert other.get("/simulation-tests").json()["tests"][0]["number"] == 1
    with registry.connect() as db:
        assert db.execute("SELECT 1 FROM tests WHERE id='original'").fetchone() is None
    assert (registry.root / identity).exists()


def test_clear_requires_confirmed_snapshot_and_retry_never_deletes_later_test(tmp_path):
    registry, client = workspace(tmp_path)
    first = start(client)
    request_id = uuid4()
    stale = clear(client, request_id, ["original"])
    assert stale.status_code == 409 and stale.json()["reason"] == "TEST_HISTORY_CHANGED"
    assert registry.exists("original") and registry.exists(first)
    response = clear(client, request_id, [first, "original"])
    assert response.status_code == 200
    assert set(response.json()["deleted_test_ids"]) == {first, "original"}
    assert not response.json()["cleanup_pending"]
    assert response.json()["history"]["tests"] == []
    new = start(client)
    retry = clear(client, request_id, ["original", first])
    assert retry.status_code == 200
    assert retry.json()["history"]["active_test_id"] == new
    assert (registry.root / new / "runtime.db").exists()
    conflict = clear(client, request_id, [new])
    assert conflict.status_code == 409 and conflict.json()["reason"] == "TEST_REQUEST_CONFLICT"


def test_empty_clear_and_delete_retries_are_idempotent_and_request_ids_are_bound(tmp_path):
    _, client = workspace(tmp_path)
    request_id = uuid4()
    assert delete(client, "original", request_id).status_code == 200
    assert delete(client, "original", request_id).status_code == 200
    assert clear(client).status_code == 200
    newer = start(client)
    response = delete(client, newer, request_id)
    assert response.status_code == 409 and response.json()["reason"] == "TEST_REQUEST_CONFLICT"
    assert delete(client, str(uuid4())).status_code == 404
    assert (
        client.post(
            "/simulation-tests/clear",
            json={"request_id": str(uuid4()), "expected_test_ids": ["original", "original"]},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/simulation-tests/clear",
            json={"request_id": str(uuid4()), "expected_test_ids": ["../escape"]},
        ).status_code
        == 422
    )


@pytest.mark.parametrize("operation", ["delete", "clear"])
@pytest.mark.parametrize("guard", ["lease", "planning", "maintenance"])
def test_deletion_refuses_active_work_and_clear_is_atomic(tmp_path, operation, guard):
    registry, client = workspace(tmp_path)
    identity = start(client)
    active = registry.engine(identity)
    if guard == "maintenance":
        active.store.begin_scene_reset()
    else:
        job = run(client, f"/simulation-tests/{identity}", fault=Fault.DROP_ACK_AFTER_EFFECT)
        if guard == "lease":
            assert active.store.claim(job["job_id"], "worker", 120, reconcile=True)
        else:
            with active.store.transaction() as db:
                db.execute("UPDATE jobs SET state='PLANNING'")
    response = delete(client, identity) if operation == "delete" else clear(client)
    assert response.status_code == 409 and response.json()["reason"] == "TEST_OPERATION_IN_PROGRESS"
    assert registry.exists("original") and registry.exists(identity)
    assert (tmp_path / "runtime.db").exists() and (registry.root / identity / "runtime.db").exists()


def test_restart_finishes_committed_tombstone_after_crash_before_cleanup(tmp_path, monkeypatch):
    registry, client = workspace(tmp_path)
    request_id = uuid4()

    def crash(identity):
        raise RuntimeError("simulated process exit after durable tombstone")

    monkeypatch.setattr(registry, "_cleanup", crash)
    with pytest.raises(RuntimeError, match="simulated process exit"):
        delete(client, "original", request_id)
    assert (tmp_path / "runtime.db").exists()
    assert not registry.exists("original")
    _, reopened = workspace(tmp_path)
    assert reopened.get("/simulation-tests").json()["tests"] == []
    assert not (tmp_path / "runtime.db").exists()
    assert delete(reopened, "original", request_id).json()["cleanup_pending"] is False


def test_partial_cleanup_failure_stays_hidden_and_retry_removes_remaining_files(
    tmp_path, monkeypatch
):
    registry, client = workspace(tmp_path)
    request_id = uuid4()
    unlink = Path.unlink

    def locked(path, *args, **kwargs):
        if path == tmp_path / "runtime.db":
            raise PermissionError("file temporarily in use")
        return unlink(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "unlink", locked)
        response = delete(client, "original", request_id)
    assert response.status_code == 200 and response.json()["cleanup_pending"] is True
    assert not (tmp_path / "workflow.db").exists() and (tmp_path / "runtime.db").exists()
    assert client.get("/fixtures").status_code == 404
    assert client.get("/simulation-tests").json()["tests"] == []
    assert delete(client, "original", request_id).json()["cleanup_pending"] is False
    assert not (tmp_path / "runtime.db").exists()
    with registry.connect() as db:
        assert db.execute("SELECT 1 FROM tests WHERE id='original'").fetchone() is None


@pytest.mark.parametrize("kind", ["symlink", "junction", "escape"])
def test_cleanup_rejects_linked_or_escaped_storage_before_tombstoning(tmp_path, monkeypatch, kind):
    registry, client = workspace(tmp_path)
    identity = start(client)
    directory = registry.root / identity
    if kind == "escape":
        resolve = Path.resolve
        monkeypatch.setattr(
            Path,
            "resolve",
            lambda path, *a, **k: (
                tmp_path / "outside" if path == directory else resolve(path, *a, **k)
            ),
        )
    else:
        method = "is_symlink" if kind == "symlink" else "is_junction"
        original = getattr(Path, method)
        monkeypatch.setattr(Path, method, lambda path: path == directory or original(path))
    response = delete(client, identity)
    assert response.status_code == 409 and response.json()["reason"] == "TEST_STORAGE_UNSAFE_PATH"
    assert registry.exists(identity) and (directory / "runtime.db").exists()


@pytest.mark.parametrize("operation", ["delete", "clear"])
def test_two_hosts_refuse_deletion_during_motion_but_keep_live_reads(
    tmp_path, monkeypatch, operation
):
    registry, client = workspace(tmp_path)
    _, other = workspace(tmp_path)
    runtime = registry.engine("original").runtime
    entered, finish = Event(), Event()
    apply = runtime.apply

    def delayed(command, fault=None):
        entered.set()
        assert finish.wait(10)
        return apply(command, fault)

    monkeypatch.setattr(runtime, "apply", delayed)
    with ThreadPoolExecutor(2) as pool:
        future = pool.submit(run, client)
        try:
            assert entered.wait(10)
            response = (
                delete(other, "original")
                if operation == "delete"
                else clear(other, expected=["original"])
            )
            assert response.status_code == 409
            assert response.json()["reason"] == "TEST_OPERATION_IN_PROGRESS"
            assert other.get("/fixtures").status_code == 200
        finally:
            finish.set()
        job = future.result()
    assert job["state"] == "COMPLETED"
    assert runtime.journal(job["command_id"]).effect_count == 1
    assert delete(other, "original").status_code == 200


def test_deletion_barrier_covers_deferred_file_response_until_all_bytes_are_sent(
    tmp_path, monkeypatch
):
    registry, client = workspace(tmp_path)
    _, other = workspace(tmp_path)
    # Add a file response to this app: the lifecycle middleware must cover its ASGI send,
    # not just the synchronous route handler that returns the FileResponse object.
    payload = tmp_path / "download.bin"
    payload.write_bytes(b"persisted evidence" * 100)

    @client.app.get("/download")
    def download():
        return FileResponse(payload)

    entered, finish = Event(), Event()
    call = FileResponse.__call__

    async def delayed(self, scope, receive, send):
        if self.path == payload:
            entered.set()
            assert finish.wait(10)
        await call(self, scope, receive, send)

    monkeypatch.setattr(FileResponse, "__call__", delayed)
    with ThreadPoolExecutor(2) as pool:
        response = pool.submit(client.get, "/download")
        try:
            assert entered.wait(10)
            blocked = delete(other, "original")
            assert blocked.status_code == 409
        finally:
            finish.set()
        assert response.result().content == payload.read_bytes()
    assert delete(other, "original").status_code == 200
    assert payload.exists() and registry.path.exists()


def test_legacy_catalog_upgrade_keeps_ids_numbers_and_saved_profiles(tmp_path):
    engine = Engine(
        Store(tmp_path / "workflow.db"), SyntheticRuntime(tmp_path / "runtime.db", Settings())
    )
    root = tmp_path / "simulation-tests"
    root.mkdir()
    identity = str(uuid4())
    SyntheticRuntime(root / identity / "runtime.db", Settings())
    Store(root / identity / "workflow.db")
    with closing(sqlite3.connect(root / "catalog.db")) as db, db:
        db.executescript(
            "CREATE TABLE tests(number INTEGER PRIMARY KEY AUTOINCREMENT,id TEXT UNIQUE NOT NULL,created TEXT NOT NULL); CREATE TABLE active(id INTEGER PRIMARY KEY,test_id TEXT NOT NULL);"
        )
        timestamp = engine.runtime.world().timestamp.isoformat()
        db.executemany(
            "INSERT INTO tests(id,created) VALUES (?,?)",
            [("original", timestamp), (identity, timestamp)],
        )
        db.execute("INSERT INTO active VALUES (1,?)", (identity,))
    app = create_app(engine.store, engine)
    history = TestClient(app).get("/simulation-tests").json()
    assert [item["number"] for item in history["tests"]] == [1, 2]
    assert [item["cell_profile_id"] for item in history["tests"]] == ["legacy_cartesian_v1"] * 2
    _, reopened = workspace(tmp_path)
    assert reopened.get("/simulation-tests").json() == history


def test_empty_workspace_bootstrap_never_initializes_or_recovers_any_runtime(tmp_path, monkeypatch):
    _, client = workspace(tmp_path)
    assert clear(client).status_code == 200

    def forbidden(*args, **kwargs):
        raise AssertionError("Empty workspace must not construct or recover a runtime")

    monkeypatch.setattr(SyntheticRuntime, "__init__", forbidden)
    monkeypatch.setattr(Engine, "recover", forbidden)
    registry, other = workspace(tmp_path)
    assert registry.original is None
    assert other.get("/simulation-tests").json()["active_test_id"] is None
    assert not (tmp_path / "runtime.db").exists()


def test_openapi_remains_stable_after_clear_and_empty_workspace_restart(tmp_path):
    _, client = workspace(tmp_path)
    contract = client.get("/openapi.json").json()
    assert clear(client).status_code == 200
    _, reopened = workspace(tmp_path)
    assert reopened.get("/openapi.json").json() == contract
    assert "/jobs/{job_id}/run" in contract["paths"]


def test_custom_original_database_names_are_persisted_and_cleanup_is_exact(tmp_path):
    engine = Engine(
        Store(tmp_path / "business.sqlite"),
        SyntheticRuntime(tmp_path / "controller.sqlite", Settings()),
    )
    client = TestClient(create_app(engine.store, engine))
    # These unrelated files must not be mistaken for the configured databases.
    (tmp_path / "workflow.db").write_bytes(b"unrelated")
    (tmp_path / "runtime.db").write_bytes(b"unrelated")
    assert delete(client, "original").status_code == 200
    assert not engine.store.path.exists() and not engine.runtime.db.path.exists()
    assert (tmp_path / "workflow.db").read_bytes() == b"unrelated"
    assert (tmp_path / "runtime.db").read_bytes() == b"unrelated"
    _, restarted = workspace(tmp_path)
    assert restarted.get("/simulation-tests").json()["tests"] == []
    assert not engine.runtime.db.path.exists()


def test_outside_workspace_runtime_is_never_deleted(tmp_path):
    data = tmp_path / "workspace"
    engine = Engine(
        Store(data / "workflow.db"), SyntheticRuntime(tmp_path / "outside-runtime.db", Settings())
    )
    client = TestClient(create_app(engine.store, engine))
    response = delete(client, "original")
    assert response.status_code == 409 and response.json()["reason"] == "TEST_STORAGE_UNSAFE_PATH"
    assert engine.runtime.db.path.exists() and engine.store.path.exists()


def test_start_refuses_orphan_world_with_different_cell_without_relabeling_it(tmp_path):
    registry, client = workspace(tmp_path)
    identity = uuid4()
    directory = registry.root / str(identity)
    legacy = SyntheticRuntime(directory / "runtime.db", Settings())
    before = legacy.world().model_dump_json()
    response = client.post(
        "/simulation-tests",
        json={"request_id": str(identity), "cell_profile_id": "hkm_inspired_v1"},
    )
    assert (
        response.status_code == 409 and response.json()["reason"] == "CELL_PROFILE_STATE_MISMATCH"
    )
    assert not registry.exists(str(identity))
    assert registry.active_id() == "original"
    assert legacy.world().model_dump_json() == before


def test_additional_host_can_bootstrap_while_reads_are_in_flight_without_cleanup(tmp_path):
    registry, _ = workspace(tmp_path)
    with registry.access():
        app = create_workspace_app(tmp_path, recover=False)
        assert app.state.test_registry.active_id() == "original"


def test_pending_cleanup_defers_on_live_response_and_later_restart_finishes_it(
    tmp_path, monkeypatch
):
    registry, client = workspace(tmp_path)
    original_cleanup = registry._cleanup
    monkeypatch.setattr(registry, "_cleanup", lambda identity: False)
    assert delete(client, "original").json()["cleanup_pending"] is True
    monkeypatch.setattr(registry, "_cleanup", original_cleanup)
    with registry.access():
        app = create_workspace_app(tmp_path, recover=False)
        assert app.state.test_registry.active_id() is None
        assert (tmp_path / "runtime.db").exists()
    create_workspace_app(tmp_path, recover=False)
    assert not (tmp_path / "runtime.db").exists()


def reset_test(client, identity="original", *, request_id=None, revision=1):
    return client.post(
        f"/simulation-tests/{identity}/clear",
        json={"request_id": str(request_id or uuid4()), "expected_revision": revision},
    )


def test_deleted_numbers_are_reused_without_renumbering_survivors_or_retaining_test_data(tmp_path):
    registry, client = workspace(tmp_path)
    second = start(client)
    third = start(client)
    assert delete(client, second).status_code == 200
    replacement = start(client)
    history = client.get("/simulation-tests").json()["tests"]
    assert [(item["test_id"], item["number"]) for item in history] == [
        ("original", 1),
        (replacement, 2),
        (third, 3),
    ]
    assert replacement != second and not (registry.root / second).exists()
    with registry.connect() as db:
        assert db.execute("SELECT * FROM tests WHERE id=?", (second,)).fetchone() is None
        # Retry protection keeps only digests, not a hidden test or raw payload/ID.
        dump = "\n".join(db.iterdump())
        assert second not in dump
        assert not db.execute("SELECT 1 FROM sqlite_master WHERE name='requests'").fetchone()
    assert delete(client, "original").status_code == 200
    assert delete(client, third).status_code == 200
    assert delete(client, replacement).status_code == 200
    reopened, other = workspace(tmp_path)
    assert other.get("/simulation-tests").json()["tests"] == []
    fresh = start(other)
    assert reopened.history().tests[0].number == 1
    assert fresh not in {second, third, replacement}


@pytest.mark.parametrize("identity_kind", ["original", "new"])
@pytest.mark.parametrize("fault", [None, Fault.DROP_ACK_AFTER_EFFECT, Fault.LOGICAL_ESTOP])
def test_clear_keeps_identity_number_profile_and_restores_an_empty_runnable_test(
    tmp_path, identity_kind, fault
):
    registry, client = workspace(tmp_path)
    identity = "original" if identity_kind == "original" else start(client)
    prefix = "" if identity == "original" else f"/simulation-tests/{identity}"
    old_job = run(client, prefix, fault=fault)
    if fault == Fault.DROP_ACK_AFTER_EFFECT:
        review = client.post(
            prefix + f"/jobs/{old_job['job_id']}/reconcile",
            json={"fault": "CONTRADICTORY_OBSERVATION"},
        )
        assert review.json()["state"] == "REQUIRES_INTERVENTION"
    before = next(test for test in registry.history().tests if test.test_id == identity)
    old_epoch = registry.engine(identity).runtime.world().scene_epoch
    other_registry, other = workspace(tmp_path)
    assert other.get(prefix + "/orders").json()
    artifact = registry.directory(identity) / "blender-artifacts" / "old-motion.json"
    artifact.parent.mkdir(exist_ok=True)
    artifact.write_text("old test evidence")
    response = reset_test(client, identity)
    assert response.status_code == 200, response.text
    assert response.json()["cleanup_pending"] is False
    after = next(test for test in registry.history().tests if test.test_id == identity)
    assert (after.test_id, after.number, after.created_at, after.cell_profile_id) == (
        before.test_id,
        before.number,
        before.created_at,
        before.cell_profile_id,
    )
    assert after.revision == 2 and not after.clearing and after.active
    assert not after.outcomes and after.order_count == 0 and not artifact.exists()
    assert registry.engine(identity).runtime.world().scene_epoch != old_epoch
    for viewer in (client, other):
        assert viewer.get(prefix + "/orders").json() == []
        assert viewer.get(prefix + f"/jobs/{old_job['job_id']}/evidence").status_code == 404
        fixtures = viewer.get(prefix + "/fixtures").json()
        assert all(
            item["location_id"] == fixtures["product_sources"][item["product_id"]]
            for item in fixtures["inventory"]
        )
        assert viewer.get(prefix + "/cell").json()["mode"] == "READY"
    assert other_registry.engine(identity).runtime.journal(old_job["command_id"]) is None
    again = run(other, prefix)
    assert again["state"] == "COMPLETED" and again["command_id"] != old_job["command_id"]
    assert other_registry.engine(identity).runtime.journal(again["command_id"]).effect_count == 1


def test_clear_selected_archive_activates_only_its_fresh_run_and_preserves_other_test(tmp_path):
    registry, client = workspace(tmp_path)
    old = run(client, fault=Fault.DROP_ACK_AFTER_EFFECT)
    newer = start(client)
    newer_job = run(client, f"/simulation-tests/{newer}")
    preserved = registry.engine(newer).evidence(newer_job["job_id"]).model_dump_json()
    response = reset_test(client)
    assert response.status_code == 200, response.text
    assert registry.active_id() == "original"
    assert client.get("/orders").json() == []
    assert client.get(f"/jobs/{old['job_id']}").status_code == 404
    assert registry.engine(newer).evidence(newer_job["job_id"]).model_dump_json() == preserved
    assert client.post(f"/simulation-tests/{newer}/cell/reset").status_code == 409


def test_clear_retries_and_stale_requests_cannot_erase_or_execute_a_new_run(tmp_path):
    registry, client = workspace(tmp_path)
    request_id = uuid4()
    assert reset_test(client, request_id=request_id).status_code == 200
    job = run(client)
    original = registry.engine("original").evidence(job["job_id"]).model_dump_json()
    assert reset_test(client, request_id=request_id).status_code == 200
    assert registry.engine("original").evidence(job["job_id"]).model_dump_json() == original
    assert reset_test(client, revision=1).json()["reason"] == "TEST_REVISION_CHANGED"
    assert (
        reset_test(client, request_id=request_id, revision=2).json()["reason"]
        == "TEST_REQUEST_CONFLICT"
    )
    blocked = client.post("/cell/reset", headers={"X-Test-Revision": "1"})
    assert blocked.status_code == 409 and blocked.json()["reason"] == "TEST_REVISION_CHANGED"
    assert reset_test(client, revision=2).status_code == 200
    new_job = run(client)
    assert reset_test(client, request_id=request_id).status_code == 200
    assert registry.engine("original").store.job(new_job["job_id"]).state.value == "COMPLETED"


def test_clear_crash_resumes_reset_on_restart_without_recovering_discarded_command(
    tmp_path, monkeypatch
):
    registry, client = workspace(tmp_path)
    old = run(client, fault=Fault.DROP_ACK_AFTER_EFFECT)
    request_id = uuid4()
    with monkeypatch.context() as patch:

        def crash(identity):
            raise RuntimeError("exit after durable clear intent")

        patch.setattr(registry, "_finish_clear", crash)
        with pytest.raises(RuntimeError, match="durable clear intent"):
            reset_test(client, request_id=request_id)
    assert client.get("/orders").json()["reason"] == "TEST_CLEAR_PENDING"
    assert registry.history().tests[0].clearing
    reopened, other = workspace(tmp_path)
    assert other.get("/orders").json() == []
    assert reopened.history().tests[0].revision == 2
    assert not reopened.history().tests[0].clearing
    assert reopened.engine("original").runtime.journal(old["command_id"]) is None
    job = run(other)
    assert reset_test(other, request_id=request_id).status_code == 200
    assert reopened.engine("original").store.job(job["job_id"]).state.value == "COMPLETED"


def test_clear_locked_files_remains_explicitly_pending_until_same_request_finishes(
    tmp_path, monkeypatch
):
    registry, client = workspace(tmp_path)
    run(client)
    request_id = uuid4()
    with monkeypatch.context() as patch:
        patch.setattr(registry, "_remove_world", lambda identity: False)
        result = reset_test(client, request_id=request_id)
    assert result.status_code == 200 and result.json()["cleanup_pending"]
    assert registry.history().tests[0].clearing
    assert client.post("/cell/reset").status_code == 409
    result = reset_test(client, request_id=request_id)
    assert result.status_code == 200 and not result.json()["cleanup_pending"]
    assert client.get("/orders").json() == []
    assert run(client)["state"] == "COMPLETED"


@pytest.mark.parametrize("guard", ["lease", "planning", "maintenance"])
def test_clear_refuses_active_work_even_when_clearing_an_archive(tmp_path, guard):
    registry, client = workspace(tmp_path)
    new = start(client)
    active = registry.engine(new)
    if guard == "maintenance":
        active.store.begin_scene_reset()
    else:
        job = run(client, f"/simulation-tests/{new}", fault=Fault.DROP_ACK_AFTER_EFFECT)
        if guard == "lease":
            assert active.store.claim(job["job_id"], "worker", 120, reconcile=True)
        else:
            with active.store.transaction() as db:
                db.execute("UPDATE jobs SET state='PLANNING'")
    response = reset_test(client)
    assert response.status_code == 409 and response.json()["reason"] == "TEST_OPERATION_IN_PROGRESS"
    assert registry.history().tests[0].revision == 1
    assert registry.active_id() == new


def test_old_deleted_catalog_rows_are_purged_on_upgrade_without_touching_survivors(tmp_path):
    registry, client = workspace(tmp_path)
    kept = start(client)
    snapshot = registry.engine(kept).runtime.world().model_dump_json()
    # Reproduce the former completed-tombstone and raw request-receipt storage.
    with registry.connect() as db:
        db.execute(
            "UPDATE tests SET deleted='2026-10-05T00:00:00Z',cleanup_pending=0 WHERE id='original'"
        )
        db.execute(
            "CREATE TABLE requests(id TEXT PRIMARY KEY,payload TEXT NOT NULL,targets TEXT NOT NULL)"
        )
        request_id = str(uuid4())
        db.execute(
            "INSERT INTO requests VALUES (?,?,?)",
            (request_id, '["delete", "original"]', '["original"]'),
        )
    reopened, other = workspace(tmp_path)
    with reopened.connect() as db:
        assert db.execute("SELECT 1 FROM tests WHERE id='original'").fetchone() is None
        assert not db.execute("SELECT 1 FROM sqlite_master WHERE name='requests'").fetchone()
    assert not (tmp_path / "runtime.db").exists()
    assert reopened.engine(kept).runtime.world().model_dump_json() == snapshot
    assert delete(other, "original", request_id).status_code == 200
    replacement = start(other)
    assert next(t for t in reopened.history().tests if t.test_id == replacement).number == 1


def test_delete_migrated_test_without_old_profile_or_receipt_cannot_resurrect_it(tmp_path):
    registry, client = workspace(tmp_path)
    request_id = uuid4()
    identity = start(client, request_id)
    with registry.connect() as db:
        db.execute("UPDATE tests SET cell_profile_id=NULL WHERE id=?", (identity,))
        db.execute("DELETE FROM request_guards")
    reopened, client = workspace(tmp_path)
    assert delete(client, identity).status_code == 200
    response = client.post(
        "/simulation-tests",
        json={"request_id": str(request_id), "cell_profile_id": "hkm_inspired_v1"},
    )
    assert response.status_code == 409 and response.json()["reason"] == "TEST_DELETED"
    assert not reopened.directory(identity).exists()


def test_pending_clear_can_resume_with_new_confirmation_without_extra_revision(
    tmp_path, monkeypatch
):
    registry, client = workspace(tmp_path)
    run(client)
    with monkeypatch.context() as patch:
        patch.setattr(registry, "_remove_world", lambda identity: False)
        assert reset_test(client).json()["cleanup_pending"]
    result = reset_test(client, revision=2)
    assert result.status_code == 200 and not result.json()["cleanup_pending"]
    assert registry.history().tests[0].revision == 2
    assert client.get("/orders").json() == []
    assert run(client)["state"] == "COMPLETED"
