import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from threading import Event, current_thread

import pytest
from asyncua.ua.uaerrors import UaStatusCodeError

from robotops.lab.journal import PLCJournal
from robotops.lab.opcua import OPCClient
from robotops.workflow.store import Conflict


def test_journal_never_regrants_execution_even_after_restart(tmp_path, lab_command):
    command, runtime = lab_command
    path = tmp_path / "journal.db"
    journal = PLCJournal(path)
    assert journal.submit(command.model_dump(mode="json"))["effect_permitted"] is False
    assert runtime.world().step == 0
    journal.preconditions(command.command_id, runtime.world().model_dump(mode="json"))
    with ThreadPoolExecutor(max_workers=4) as pool:
        claims = list(pool.map(lambda _: journal.begin(command.command_id), range(4)))
    assert sum(claim["execute"] for claim in claims) == 1
    restart = PLCJournal(path)
    assert restart.boot_id != journal.boot_id
    assert restart.begin(command.command_id)["execute"] is False
    assert restart.submit(command.model_dump(mode="json"))["duplicate"] is True
    receipt = runtime.apply(command)
    result = restart.result(command.command_id, receipt.model_dump(mode="json"))
    assert result["result"]["effect_count"] == 1
    assert restart.acknowledge(command.command_id, 1)["acknowledged"]
    assert restart.begin(command.command_id)["execute"] is False
    assert runtime.world().step == 1


def test_journal_rejects_payload_and_result_conflicts(tmp_path, lab_command):
    command, runtime = lab_command
    journal = PLCJournal(tmp_path / "journal.db")
    journal.submit(command.model_dump(mode="json"))
    payload = command.model_dump(mode="json")
    payload["cell_generation"] += 1
    with pytest.raises(Conflict, match="PAYLOAD_CONFLICT"):
        journal.submit(payload)
    world = runtime.world()
    receipt = runtime.apply(command).model_dump(mode="json")
    with pytest.raises(Conflict, match="NOT_AUTHORIZED"):
        journal.result(command.command_id, receipt)
    journal.preconditions(command.command_id, world.model_dump(mode="json"))
    journal.begin(command.command_id)
    journal.result(command.command_id, receipt)
    with pytest.raises(Conflict, match="SEQUENCE_MISMATCH"):
        journal.acknowledge(command.command_id, 2)


@pytest.mark.parametrize("process_restart", [False, True])
def test_restart_invalidates_readiness_until_fresh_checks(tmp_path, lab_command, process_restart):
    command, runtime = lab_command
    path = tmp_path / "journal.db"
    journal = PLCJournal(path)
    journal.submit(command.model_dump(mode="json"))
    checked = journal.preconditions(command.command_id, runtime.world().model_dump(mode="json"))
    assert checked["validated_boot_id"] == journal.boot_id
    if process_restart:
        journal = PLCJournal(path)
    else:
        journal.restart()
    with pytest.raises(Conflict, match="BOOT_CHANGED_RECHECK"):
        journal.begin(command.command_id)
    assert runtime.world().step == 0
    fresh = journal.preconditions(command.command_id, runtime.world().model_dump(mode="json"))
    assert fresh["validated_boot_id"] == journal.boot_id != checked["validated_boot_id"]
    assert journal.begin(command.command_id)["execute"]
    journal.restart()
    assert not journal.begin(command.command_id)["execute"]


def test_uncertain_controller_checkpoint_can_be_reconciled_to_immutable_final(
    tmp_path, lab_command
):
    command, runtime = lab_command
    journal = PLCJournal(tmp_path / "journal.db")
    journal.submit(command.model_dump(mode="json"))
    journal.preconditions(command.command_id, runtime.world().model_dump(mode="json"))
    journal.begin(command.command_id)
    final = runtime.apply(command).model_dump(mode="json")
    provisional = {
        **final,
        "status": "STATUS_UNKNOWN",
        "effect_count": 0,
        "reason": "CHECKPOINT_PENDING",
    }
    assert journal.result(command.command_id, provisional)["result_sequence"] == 1
    assert not journal.begin(command.command_id)["execute"]
    assert journal.result(command.command_id, final)["result_sequence"] == 2
    assert journal.result(command.command_id, final)["result_sequence"] == 2
    with pytest.raises(Conflict, match="IMMUTABLE_RESULT"):
        journal.result(command.command_id, provisional)
    with journal.connect() as db:
        assert db.execute("SELECT count(*) FROM plc_results").fetchone()[0] == 2


def test_acknowledgement_cannot_mark_a_concurrently_advanced_result(
    tmp_path, lab_command, monkeypatch
):
    command, runtime = lab_command
    journal = PLCJournal(tmp_path / "journal.db")
    journal.submit(command.model_dump(mode="json"))
    journal.preconditions(command.command_id, runtime.world().model_dump(mode="json"))
    journal.begin(command.command_id)
    final = runtime.apply(command).model_dump(mode="json")
    provisional = {**final, "status": "STATUS_UNKNOWN", "effect_count": 0, "reason": "PENDING"}
    journal.result(command.command_id, provisional)
    read, resume = Event(), Event()
    connect = journal.connect

    class PausedCursor:
        def __init__(self, cursor):
            self.cursor = cursor

        def fetchone(self):
            row = self.cursor.fetchone()
            read.set()
            assert resume.wait(10), "Acknowledgement test did not resume its reader"
            return row

    class PausedConnection:
        def __init__(self, db):
            self.db = db

        def execute(self, statement, parameters=()):
            cursor = self.db.execute(statement, parameters)
            if statement.startswith("SELECT result_sequence,result FROM plc_commands"):
                return PausedCursor(cursor)
            return cursor

    @contextmanager
    def interleaved_connection():
        with connect() as db:
            if current_thread().name.startswith("ack-reader"):
                yield PausedConnection(db)
            else:
                # A competing real SQLite writer reports contention immediately;
                # no sleep or scheduling assumption determines the interleaving.
                db.execute("PRAGMA busy_timeout=0")
                yield db

    monkeypatch.setattr(journal, "connect", interleaved_connection)
    advanced = False
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="ack-reader") as pool:
        acknowledgement = pool.submit(journal.acknowledge, command.command_id, 1)
        try:
            assert read.wait(10), "Acknowledgement did not read its original sequence"
            try:
                journal.result(command.command_id, final)
                advanced = True
            except sqlite3.OperationalError as error:
                assert "locked" in str(error)
        finally:
            resume.set()
        acknowledgement.result(timeout=10)
    if not advanced:
        journal.result(command.command_id, final)
    retained = journal.status(command.command_id)
    assert retained["result_sequence"] == 2
    assert retained["acknowledged"] is False
    assert retained["result"]["effect_count"] == runtime.world().step == 1
    with pytest.raises(Conflict, match="SEQUENCE_MISMATCH"):
        journal.acknowledge(command.command_id, 1)


def test_real_opcua_browse_subscription_acceptance_gate_and_result(running_plc, lab_command):
    command, runtime = lab_command
    client = OPCClient(running_plc.endpoint)
    connect = client.call()
    assert connect["subscription_created"]
    assert connect["subscription_notifications"]
    assert connect["browsed_children"] >= 8
    submitted = client.call("SubmitJob", command.model_dump_json())
    assert submitted["state"] == "ACCEPTED"
    assert submitted["effect_permitted"] is False
    assert runtime.world().step == 0
    assert client.call("SubmitJob", command.model_dump_json())["duplicate"]
    conflict = command.model_copy(update={"cell_generation": command.cell_generation + 1})
    with pytest.raises(UaStatusCodeError):
        client.call("SubmitJob", conflict.model_dump_json())
    with pytest.raises(UaStatusCodeError):
        client.call("BeginExecution", command.command_id)
    checked = client.call(
        "CheckPreconditions", command.command_id, runtime.world().model_dump_json()
    )
    assert checked["state"] == "READY"
    client.call("RestartController")
    with pytest.raises(UaStatusCodeError):
        client.call("BeginExecution", command.command_id)
    assert runtime.world().step == 0
    client.call("CheckPreconditions", command.command_id, runtime.world().model_dump_json())
    claim = client.call("BeginExecution", command.command_id)
    assert claim["execute"]
    assert claim["payload_hash"] == checked["payload_hash"]
    receipt = runtime.apply(command)
    result = client.call("ReportResult", command.command_id, receipt.model_dump_json())
    assert result["result"]["effect_count"] == 1
    assert client.call("GetJobStatus", command.command_id)["result"] == result["result"]
    assert client.call("AcknowledgeResult", command.command_id, 1)["acknowledged"]
    assert not client.call("BeginExecution", command.command_id)["execute"]
    assert runtime.world().step == 1
