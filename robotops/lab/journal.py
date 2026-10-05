"""Durable virtual PLC command identity and execution-permit state machine.

SQLite FULL synchronous commits are the controller's retained memory in this lab.
The physical runtime has its own independent journal: no database transaction is
claimed to atomically include a robot effect. EXECUTING survives crashes as unknown.
"""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from robotops.cell.runtime import SyntheticRuntime
from robotops.domain.models import CommandReceipt, RobotCommand, WorldState, new_id
from robotops.workflow.store import Conflict, digest


class PLCJournal:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.boot_id = new_id()
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS plc_commands (
                    command_id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL,
                    payload TEXT NOT NULL, state TEXT NOT NULL, permit TEXT,
                    result TEXT, result_sequence INTEGER NOT NULL DEFAULT 0,
                    acknowledged INTEGER NOT NULL DEFAULT 0, boot_id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS plc_results (
                    command_id TEXT NOT NULL, sequence INTEGER NOT NULL, receipt TEXT NOT NULL,
                    PRIMARY KEY(command_id,sequence));
            """)
            columns = {row["name"] for row in db.execute("PRAGMA table_info(plc_commands)")}
            if "validated_boot_id" not in columns:
                # Existing retained commands stay fenced until fresh validation.
                db.execute("ALTER TABLE plc_commands ADD COLUMN validated_boot_id TEXT")

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA synchronous=FULL")
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _status(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "command_id": row["command_id"],
            "payload_hash": row["payload_hash"],
            "state": row["state"],
            "result_sequence": row["result_sequence"],
            "result": json.loads(row["result"]) if row["result"] else None,
            "acknowledged": bool(row["acknowledged"]),
            "accepted_boot_id": row["boot_id"],
            "validated_boot_id": row["validated_boot_id"],
        }

    def submit(self, payload: dict[str, Any]) -> dict[str, Any]:
        command = RobotCommand.model_validate(payload)
        hashed = digest(command)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute(
                "SELECT * FROM plc_commands WHERE command_id=?", (command.command_id,)
            ).fetchone()
            if previous:
                if previous["payload_hash"] != hashed:
                    raise Conflict("COMMAND_ID_PAYLOAD_CONFLICT")
                return {**self._status(previous), "duplicate": True, "effect_permitted": False}
            db.execute(
                "INSERT INTO plc_commands(command_id,payload_hash,payload,state,boot_id) "
                "VALUES (?,?,?,'ACCEPTED',?)",
                (command.command_id, hashed, command.model_dump_json(), self.boot_id),
            )
        return {**self.status(command.command_id), "duplicate": False, "effect_permitted": False}

    def status(self, command_id: str) -> dict[str, Any]:
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM plc_commands WHERE command_id=?", (command_id,)
            ).fetchone()
        if row is None:
            return {"command_id": command_id, "state": "NOT_FOUND", "result": None}
        return {**self._status(row), "boot_id": self.boot_id}

    def restart(self) -> dict[str, Any]:
        previous = self.boot_id
        self.boot_id = new_id()
        return {
            "previous_boot_id": previous,
            "boot_id": self.boot_id,
            "restart_kind": "SIMULATED_CONTROLLER_BOOT",
            "journal_retained": True,
            "execution_claims_reset": False,
        }

    def latest(self) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM plc_commands ORDER BY rowid DESC LIMIT 1").fetchone()
        return self._status(row) if row else None

    def preconditions(self, command_id: str, world_payload: dict[str, Any]) -> dict[str, Any]:
        world = WorldState.model_validate(world_payload)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM plc_commands WHERE command_id=?", (command_id,)
            ).fetchone()
            if row is None:
                raise Conflict("COMMAND_NOT_ACCEPTED")
            command = RobotCommand.model_validate_json(row["payload"])
            if row["payload_hash"] != digest(command):
                raise Conflict("JOURNAL_HASH_MISMATCH")
            reason = SyntheticRuntime.rejection_reason(world, command, None)
            if reason:
                raise Conflict(reason)
            if row["state"] in {"ACCEPTED", "READY"}:
                db.execute(
                    "UPDATE plc_commands SET state='READY',validated_boot_id=? WHERE command_id=?",
                    (self.boot_id, command_id),
                )
        return {
            **self.status(command_id),
            "identity_retained": True,
            "ordinary_operational_checks": True,
            "safety_rated": False,
            "cell_generation": world.cell.generation,
            "scene_epoch": world.scene_epoch,
            "active_tool_id": world.tool_state.active_tool_id if world.tool_state else None,
            "checks": [
                "scene_epoch",
                "cell_generation",
                "cell_ready",
                "source",
                "tool",
                "trajectory",
                "payload_hash",
                "controller_boot",
            ],
            "rechecked_by_runtime_at_effect": True,
        }

    def begin(self, command_id: str) -> dict[str, Any]:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM plc_commands WHERE command_id=?", (command_id,)
            ).fetchone()
            if row is None:
                raise Conflict("COMMAND_NOT_ACCEPTED")
            if row["state"] == "ACCEPTED":
                raise Conflict("PLC_PRECONDITIONS_REQUIRED")
            if row["state"] != "READY":
                return {
                    **self._status(row),
                    "execute": False,
                    "reason": "QUERY_ORIGINAL_JOURNAL_DO_NOT_REPEAT",
                }
            if row["validated_boot_id"] != self.boot_id:
                raise Conflict("PLC_BOOT_CHANGED_RECHECK_PRECONDITIONS")
            # Never clear or recycle this permit, including after a restart.
            permit = new_id()
            db.execute(
                "UPDATE plc_commands SET state='EXECUTING',permit=? WHERE command_id=?",
                (permit, command_id),
            )
        return {
            **self._status(row),
            "boot_id": self.boot_id,
            "state": "EXECUTING",
            "execute": True,
            "permit": permit,
            "interface": "simulated controller interface",
        }

    def result(self, command_id: str, receipt: dict[str, Any]) -> dict[str, Any]:
        receipt = CommandReceipt.model_validate(receipt).model_dump(mode="json")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM plc_commands WHERE command_id=?", (command_id,)
            ).fetchone()
            if row is None or row["state"] in {"ACCEPTED", "READY"}:
                raise Conflict("EXECUTION_WAS_NOT_AUTHORIZED")
            if receipt.get("command_id") != command_id:
                raise Conflict("RESULT_COMMAND_IDENTITY_MISMATCH")
            if receipt.get("payload_hash") != row["payload_hash"]:
                raise Conflict("RESULT_PAYLOAD_HASH_MISMATCH")
            command = RobotCommand.model_validate_json(row["payload"])
            if receipt["job_id"] != command.job_id or receipt["scene_epoch"] != command.scene_epoch:
                raise Conflict("RESULT_JOB_OR_SCENE_MISMATCH")
            encoded = json.dumps(receipt, sort_keys=True)
            if row["result"] and row["result"] != encoded:
                if json.loads(row["result"])["status"] not in {"RUNNING", "STATUS_UNKNOWN"}:
                    raise Conflict("IMMUTABLE_RESULT_CONFLICT")
            if row["result"] != encoded:
                sequence = row["result_sequence"] + 1
                db.execute(
                    "INSERT INTO plc_results VALUES (?,?,?)", (command_id, sequence, encoded)
                )
                db.execute(
                    "UPDATE plc_commands SET state=?,result=?,result_sequence=?,acknowledged=0 "
                    "WHERE command_id=?",
                    (receipt["status"], encoded, sequence, command_id),
                )
        return self.status(command_id)

    def acknowledge(self, command_id: str, sequence: int) -> dict[str, Any]:
        with self.connect() as db:
            row = db.execute(
                "SELECT result_sequence,result FROM plc_commands WHERE command_id=?", (command_id,)
            ).fetchone()
            if row is None or not row["result"] or row["result_sequence"] != sequence:
                raise Conflict("RESULT_SEQUENCE_MISMATCH")
            db.execute("UPDATE plc_commands SET acknowledged=1 WHERE command_id=?", (command_id,))
        return self.status(command_id)
