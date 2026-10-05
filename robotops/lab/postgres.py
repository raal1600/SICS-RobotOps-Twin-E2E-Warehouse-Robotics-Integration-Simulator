"""PostgreSQL implementation of the existing Store transaction contract.

The small SQL adapter handles the existing repository's SQLite spellings, preserving
one workflow implementation. Every write transaction takes a transaction-scoped
advisory lock, matching SQLite BEGIN IMMEDIATE's serial writer semantics. Network
operations and human authorization waits happen outside these transactions.
"""

import re
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, cast

import psycopg

from robotops.workflow.store import Store


class Row:
    def __init__(self, names: list[str], values: Sequence[Any]):
        self.names = names
        self.values = values

    def __getitem__(self, key: int | str) -> Any:
        return self.values[key if isinstance(key, int) else self.names.index(key)]


class Cursor:
    def __init__(self, cursor: psycopg.Cursor[Any]):
        self.cursor = cursor
        self.rowcount = cursor.rowcount

    def fetchone(self) -> Row | None:
        value = self.cursor.fetchone()
        if value is None:
            return None
        return Row([column.name for column in self.cursor.description or []], value)

    def fetchall(self) -> list[Row]:
        return list(self)

    def __iter__(self) -> Iterator[Row]:
        while (row := self.fetchone()) is not None:
            yield row


class Connection:
    def __init__(self, raw: psycopg.Connection[Any]):
        self.raw = raw

    def execute(self, sql: str, params: Sequence[Any] = ()) -> Cursor:
        sql = sql.strip().rstrip(";")
        if sql.startswith("PRAGMA"):
            return Cursor(self.raw.execute("SELECT 1"))
        sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "BIGSERIAL PRIMARY KEY")
        sql = re.sub(
            r"json_extract\((\w+(?:\.\w+)?),\s*'\$\.(\w+)'\)",
            r"(\1::jsonb->>'\2')",
            sql,
        )
        # ctid provides stable insertion order while rows remain immutable. Jobs use
        # causal event sequence first; ctid is only the pre-execution tie breaker.
        sql = re.sub(r"\browid\b", "ctid", sql)
        if "INSERT OR IGNORE" in sql:
            sql = sql.replace("INSERT OR IGNORE", "INSERT") + " ON CONFLICT DO NOTHING"
        if "INSERT OR REPLACE INTO lease" in sql:
            sql = (
                "INSERT INTO lease VALUES ('cell-1',?,?,?,?) "
                "ON CONFLICT(cell_id) DO UPDATE SET job_id=excluded.job_id,"
                "owner=excluded.owner,fence=excluded.fence,expires=excluded.expires"
            )
        if "INSERT OR REPLACE INTO meta" in sql:
            sql = (
                "INSERT INTO meta VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value"
            )
        # PostgreSQL cannot infer the type of an isolated NULL parameter.
        sql = sql.replace("? IS NULL", "CAST(? AS TEXT) IS NULL")
        return Cursor(self.raw.execute(sql.replace("?", "%s"), params))

    def executescript(self, script: str) -> None:
        for statement in script.split(";"):
            if statement.strip():
                self.execute(statement)


class PostgreSQLStore(Store):
    def __init__(self, dsn: str, artifact_path: Path = Path("runs/lab/application.db")):
        self.dsn = dsn
        super().__init__(artifact_path)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        with psycopg.connect(self.dsn, autocommit=True, connect_timeout=10) as raw:
            yield cast(sqlite3.Connection, Connection(raw))

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with psycopg.connect(self.dsn, autocommit=True, connect_timeout=10) as raw:
            with raw.transaction():
                raw.execute("SELECT pg_advisory_xact_lock(74829301)")
                yield cast(sqlite3.Connection, Connection(raw))

    @contextmanager
    def readonly_connect(self) -> Iterator[sqlite3.Connection]:
        with psycopg.connect(self.dsn, autocommit=True, connect_timeout=10) as raw:
            with raw.transaction():
                raw.execute("SET TRANSACTION READ ONLY")
                yield cast(sqlite3.Connection, Connection(raw))
