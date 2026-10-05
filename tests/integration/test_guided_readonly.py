"""A stale reader cannot recreate a run after it was removed or replaced."""

import sqlite3

import pytest

from robotops.integration.models import CreateSession
from robotops.integration.store import IntegrationStore
from robotops.workflow.store import NotFound, Store


@pytest.mark.parametrize("operation", ["get", "list", "prior_authorization"])
@pytest.mark.parametrize("replacement", [False, True])
def test_deleted_guided_store_reads_do_not_recreate_database(
    tmp_path, order_request, operation, replacement
):
    path = tmp_path / "workflow.db"
    store = Store(path)
    integration = IntegrationStore(store)
    session = integration.create(CreateSession(request=order_request, request_id="readonly"))
    path.unlink()
    if replacement:
        # A cleared registry can replace the path with another store, without guided schema.
        Store(path)
    before = path.read_bytes() if replacement else None
    arguments = {
        "get": (session.session_id,),
        "list": (),
        "prior_authorization": (session.session_id, "old-request"),
    }[operation]
    with pytest.raises(NotFound):
        getattr(integration, operation)(*arguments)
    if replacement:
        assert path.read_bytes() == before
        with store.readonly_connect() as db:
            assert (
                db.execute(
                    "SELECT name FROM sqlite_master WHERE name='execution_sessions'"
                ).fetchone()
                is None
            )
    else:
        assert not path.exists()


def test_readonly_connection_rejects_mutation(tmp_path):
    store = Store(tmp_path / "workflow.db")
    with store.readonly_connect() as db:
        assert db.execute("PRAGMA query_only").fetchone()[0] == 1
        assert db.execute("SELECT value FROM meta WHERE key='run_id'").fetchone()[0] == store.run_id
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            db.execute("INSERT INTO meta VALUES ('read-mutation','forbidden')")
    with store.connect() as db:
        assert db.execute("SELECT value FROM meta WHERE key='read-mutation'").fetchone() is None


def test_guided_read_operations_use_readonly_connections(tmp_path, order_request, monkeypatch):
    store = Store(tmp_path / "workflow.db")
    integration = IntegrationStore(store)
    session = integration.create(CreateSession(request=order_request, request_id="readonly"))

    def forbidden_write_connection():
        raise AssertionError("Reading a session opened a write-capable connection")

    monkeypatch.setattr(store, "connect", forbidden_write_connection)
    assert integration.get(session.session_id) == session
    assert integration.list() == [session]
    assert integration.prior_authorization(session.session_id, "none") is None
