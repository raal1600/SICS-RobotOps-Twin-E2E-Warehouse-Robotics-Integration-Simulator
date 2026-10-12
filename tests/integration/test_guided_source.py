"""Source inspection reads known files without executing code or changing a run."""

import hashlib

import pytest
from fastapi.testclient import TestClient

from apps.api.app import create_app
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.integration.engine import GuidedEngine
from robotops.integration.models import AuthorizeStage, CreateSession, SourceReference
from robotops.integration.source import current_source, symbol_range
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


def test_source_route_reads_full_current_file_without_mutating_saved_evidence(
    tmp_path, order_request
):
    workflow = Engine(
        Store(tmp_path / "app.db"), SyntheticRuntime(tmp_path / "runtime.db", Settings())
    )
    guided = GuidedEngine(workflow)
    session = guided.create(CreateSession(request=order_request, request_id="source-run"))
    session = guided.authorize(
        session.session_id,
        AuthorizeStage(request_id="demand", expected_revision=session.revision, stage=1),
    )
    saved = session.model_dump(mode="json")
    step = session.steps[0]
    route = f"/integration/sessions/{session.session_id}/steps/{step.step_id}/source"
    with TestClient(create_app(workflow.store, workflow)) as client:
        response = client.get(route)
        assert response.status_code == 200
        source = response.json()
        assert source["status"] == "available"
        assert source["path"] == step.source.path
        assert "class GuidedEngine:" in source["content"]
        assert "def reconcile(" in source["content"]
        assert source["line_count"] > 100
        assert source["excerpt_start_line"] is not None
        assert source["symbol_end_line"] > source["symbol_start_line"]
        assert source["symbol_kind"] == "function"
        assert "not a snapshot" in source["scope"]
        assert hashlib.sha256(source["content"].encode()).hexdigest() == source["displayed_sha256"]
        assert client.get(route.replace(step.step_id, "missing")).status_code == 404
    assert guided.get(session.session_id).model_dump(mode="json") == saved
    assert workflow.runtime.world().step == 0


@pytest.mark.parametrize("path", ["../config.py", "C:/private.py", "robotops/config.py", ".env"])
def test_source_reader_rejects_files_outside_the_stage_allowlist(path):
    result = current_source(SourceReference(path=path, symbol="anything", excerpt="saved"))
    assert result["status"] == "unavailable"
    assert "content" not in result


def test_source_reader_redacts_current_code_and_handles_missing_files(tmp_path, monkeypatch):
    monkeypatch.setattr("robotops.integration.source.SOURCE_ROOT", tmp_path)
    path = tmp_path / "robotops/workflow/engine.py"
    path.parent.mkdir(parents=True)
    path.write_text('password = "must-not-leak"\ndef example():\n    return 1\n', encoding="utf-8")
    reference = SourceReference(
        path="robotops/workflow/engine.py", symbol="example", excerpt="older code"
    )
    result = current_source(reference)
    assert result["status"] == "available"
    assert "must-not-leak" not in result["content"]
    assert "REDACTED" in result["content"]
    assert result["excerpt_start_line"] is None
    assert (result["symbol_start_line"], result["symbol_end_line"]) == (2, 3)
    path.unlink()
    assert current_source(reference)["status"] == "unavailable"


def test_symbol_range_selects_the_named_function_including_decorators_and_nested_body():
    source = "class A:\n    @staticmethod\n    async def run():\n        if True:\n            return 1\n\n    def next(self):\n        return 2\n\nclass B:\n    def run(self):\n        return 3\n"
    assert symbol_range(source, "A.run") == (2, 5, "function")
    assert symbol_range(source, "B.run") == (11, 12, "function")
    assert symbol_range(source, "A") == (1, 8, "class")
    assert symbol_range(source, "A.missing") is None
    assert symbol_range("not valid Python:\n", "A") is None


def test_multiline_redaction_never_points_to_wrong_displayed_lines(tmp_path, monkeypatch):
    monkeypatch.setattr("robotops.integration.source.SOURCE_ROOT", tmp_path)
    path = tmp_path / "robotops/workflow/engine.py"
    path.parent.mkdir(parents=True)
    # A Python string continued across lines is collapsed by the existing sanitizer.
    path.write_text(
        'password = "private' + "\\" + '\nvalue"\ndef example():\n    return 1\n', encoding="utf-8"
    )
    result = current_source(
        SourceReference(path="robotops/workflow/engine.py", symbol="example", excerpt="")
    )
    assert "private" not in result["content"]
    assert result["symbol_start_line"] is None
    assert result["symbol_end_line"] is None
