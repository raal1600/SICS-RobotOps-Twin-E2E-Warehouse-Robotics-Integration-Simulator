"""Source evidence must identify the actual Python callable, not an unrelated file."""

import hashlib
import json
from functools import partial

import pytest

from robotops.calibration import provenance
from robotops.calibration.configuration import default_board
from robotops.calibration.errors import CalibrationError
from robotops.calibration.lifecycle import CalibrationStore
from robotops.calibration.trace import recorded_call
from robotops.workflow.store import Store

PATH = "robotops/calibration/configuration.py"


def test_loaded_function_and_bound_method_match_compiled_but_unexecuted_saved_source(tmp_path):
    snapshot = provenance.source_snapshot(PATH, "default_board")
    verified = provenance.verify_loaded_callable(
        snapshot, PATH, "default_board", partial(default_board)
    )
    assert verified["loaded_function_verification"] == "MATCHED_PYTHON_CODE"
    assert verified["loaded_code_sha256"] == verified["compiled_source_code_sha256"]
    store = CalibrationStore(Store(tmp_path / "world.db"))
    path, symbol = "robotops/calibration/lifecycle.py", "CalibrationStore.reuse_estimate"
    bound = provenance.verify_loaded_callable(
        provenance.source_snapshot(path, symbol), path, symbol, store.reuse_estimate
    )
    assert bound["loaded_function_verification"] == "MATCHED_PYTHON_CODE"
    # Inspecting the method's nested transaction code never calls it or changes state.
    assert store.states() == []


def test_source_changed_after_import_is_rejected_before_call_and_error_is_saved(
    tmp_path, monkeypatch
):
    snapshot = provenance.source_snapshot(PATH, "default_board")
    altered = {**snapshot, "content": snapshot["content"].replace("range(24)", "range(23)")}
    monkeypatch.setattr("robotops.calibration.trace.source_snapshot", lambda *args: altered.copy())
    store = CalibrationStore(Store(tmp_path / "world.db"))
    with pytest.raises(CalibrationError, match="LOADED_SOURCE_MISMATCH"):
        recorded_call(
            store, "camera-west", "mismatch", PATH, "default_board", {}, partial(default_board)
        )
    with store.store.readonly_connect() as db:
        rows = db.execute(
            "SELECT body FROM calibration_records WHERE kind='calculation-trace'"
        ).fetchall()
    assert len(rows) == 1
    record = json.loads(rows[0][0])
    assert record["output"] is None
    assert "LOADED_SOURCE_MISMATCH" in record["error"]
    assert record["source"]["loaded_function_verification"] == "UNVERIFIED"


def test_wrong_callable_or_lambda_cannot_claim_an_allowlisted_function_executed():
    snapshot = provenance.source_snapshot(PATH, "default_board")
    effects = []
    with pytest.raises(CalibrationError, match="IDENTITY_MISMATCH"):
        provenance.verify_loaded_callable(
            snapshot, PATH, "default_board", lambda: effects.append(True)
        )
    assert effects == []
    with pytest.raises(CalibrationError, match="DIRECT_PYTHON_CALL_REQUIRED"):
        provenance.verify_loaded_callable(snapshot, PATH, "default_board", object())
    with pytest.raises(CalibrationError, match="IDENTITY_MISMATCH"):
        provenance.verify_loaded_callable(
            snapshot, "../../private.py", "default_board", default_board
        )


def test_raw_file_hash_is_distinct_from_normalized_display_hash(tmp_path, monkeypatch):
    file = tmp_path / PATH
    file.parent.mkdir(parents=True)
    raw = b"def default_board():\r\n    return 1\r\n"
    file.write_bytes(raw)
    monkeypatch.setattr(provenance, "ROOT", tmp_path)
    snapshot = provenance.source_snapshot(PATH, "default_board")
    assert snapshot["file_bytes_sha256"] == hashlib.sha256(raw).hexdigest()
    assert snapshot["displayed_sha256"] == hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    assert snapshot["file_bytes_sha256"] != snapshot["displayed_sha256"]


def test_successful_actual_call_records_matched_loaded_function(tmp_path):
    store = CalibrationStore(Store(tmp_path / "world.db"))
    result = recorded_call(
        store, "camera-west", "actual", PATH, "default_board", {}, partial(default_board)
    )
    assert result.corner_ids == tuple(range(24))
    with store.store.readonly_connect() as db:
        record = json.loads(
            db.execute(
                "SELECT body FROM calibration_records WHERE kind='calculation-trace'"
            ).fetchone()[0]
        )
    assert record["error"] is None
    assert record["output"] == result.model_dump(mode="json")
    assert record["source"]["loaded_function_verification"] == "MATCHED_PYTHON_CODE"
