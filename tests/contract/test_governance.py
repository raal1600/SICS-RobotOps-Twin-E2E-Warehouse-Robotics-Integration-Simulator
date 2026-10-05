import ast
import json
from pathlib import Path

from tools import drift_check
from tools.acceptance import evaluate, read_junit
from tools.drift_check import check, criterion_ids
from tools.security_check import review


def test_knowledge_base_links_ids_sources_and_status():
    result = check()
    assert result["passed"], result["errors"]


def test_drift_rejects_unknown_hkm_criterion_and_missing_hkm_mapping(tmp_path, monkeypatch):
    (tmp_path / "publication").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "SUCCESS_CRITERIA.md").write_text(
        "**SC-ARCH-001 MUST**\n**HKM-VIS-MUST-001 MUST**\n", encoding="utf-8"
    )
    (tmp_path / "README.md").write_text("Current status.\n", encoding="utf-8")
    (tmp_path / "publication/references.json").write_text("[]")
    (tmp_path / "publication/diagrams.json").write_text("{}")
    (tmp_path / "publication/status.json").write_text('{"summary":"Current status."}')
    (tmp_path / "Makefile").write_text("setup test lint typecheck demo acceptance docs security:\n")
    mapping = {ident: {"files": []} for ident in criterion_ids(tmp_path)}
    (tmp_path / "docs/acceptance-map.json").write_text(json.dumps(mapping))
    monkeypatch.setattr(drift_check.subprocess, "check_output", lambda *args, **kwargs: b"")
    assert check(tmp_path)["passed"]
    (tmp_path / "README.md").write_text("Current status. HKM-VIS-MUST-999\n")
    assert any("Unknown criterion HKM-VIS-MUST-999" in e for e in check(tmp_path)["errors"])
    (tmp_path / "README.md").write_text("Current status.\n")
    del mapping["HKM-VIS-MUST-001"]
    (tmp_path / "docs/acceptance-map.json").write_text(json.dumps(mapping))
    assert any("Acceptance mapping mismatch" in e for e in check(tmp_path)["errors"])


def test_domain_boundary_has_no_blender_or_network_dependency():
    for folder in ("robotops/domain", "robotops/brain", "robotops/verification"):
        for path in Path(folder).glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                modules = []
                if isinstance(node, ast.ImportFrom):
                    modules = [node.module or ""]
                elif isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                assert not any(
                    any(
                        word in module
                        for word in (
                            "bpy",
                            "blender.adapter",
                            "requests",
                            "httpx",
                            "openai",
                            "subprocess",
                        )
                    )
                    for module in modules
                ), path


def test_acceptance_rejects_absent_failed_skipped_and_unrun_evidence(tmp_path):
    xml = tmp_path / "tests.xml"
    xml.write_text(
        '<testsuite><testcase classname="x" name="test_ok"/><testcase classname="x" name="test_bad"><failure/></testcase><testcase classname="x" name="test_hidden"><skipped/></testcase></testsuite>'
    )
    suite = read_junit(xml)
    for name in ("test_bad", "test_hidden", "test_missing"):
        assert (
            evaluate(
                {"gates": ["suite"], "tests": [name]}, {"suite": {"passed": True}}, [suite, suite]
            )[0]
            is False
        )
    assert evaluate({"gates": ["unrun"], "tests": ["test_ok"]}, {}, [suite, suite])[0] is False
    assert evaluate(
        {"gates": ["suite"], "tests": ["test_ok"]}, {"suite": {"passed": True}}, [suite, suite]
    )[0]
    mapping = json.loads(Path("docs/acceptance-map.json").read_text())
    assert criterion_ids() <= mapping.keys()
    assert all(item["gates"] and item["files"] and item["explanation"] for item in mapping.values())


def test_security_exceptions_reject_changed_scope_and_severity():
    exceptions = json.loads(Path("docs/security-exceptions.json").read_text())
    finding = {
        "filename": "robotops/blender/adapter.py",
        "line_number": 5,
        "test_id": "B404",
        "issue_severity": "LOW",
    }
    assert review([finding], exceptions)[0]["reviewed"]
    assert not review([{**finding, "issue_severity": "HIGH"}], exceptions)[0]["reviewed"]
    changed = [{**item, "ast_sha256": "changed"} for item in exceptions]
    assert not review([finding], changed)[0]["reviewed"]


def test_criterion_registry_accepts_both_revisions_without_dropping_legacy_ids(tmp_path):
    (tmp_path / "SUCCESS_CRITERIA.md").write_text(
        "**SC-ARCH-001 MUST**\n**SC-ARCH-004 SHOULD**\n"
        "**HKM-VIS-MUST-001 MUST**\n**HKM-VIS-MUST-025 MUST**\n",
        encoding="utf-8",
    )
    assert criterion_ids(tmp_path) == {"SC-ARCH-001", "HKM-VIS-MUST-001", "HKM-VIS-MUST-025"}
    assert criterion_ids(tmp_path, "SHOULD") == {"SC-ARCH-004"}
    actual = criterion_ids()
    assert len({ident for ident in actual if ident.startswith("SC-")}) == 85
    assert {ident for ident in actual if ident.startswith("HKM-")} == {
        f"HKM-VIS-MUST-{number:03d}" for number in range(1, 26)
    }


def test_investigation_criteria_are_additive_and_required_by_registry(tmp_path):
    (tmp_path / "SUCCESS_CRITERIA.md").write_text(
        "**SC-ARCH-001 MUST**\n**HKM-VIS-MUST-025 MUST**\n**UI-INV-MUST-001 MUST**\n",
        encoding="utf-8",
    )
    assert criterion_ids(tmp_path) == {"SC-ARCH-001", "HKM-VIS-MUST-025", "UI-INV-MUST-001"}
    assert {ident for ident in criterion_ids() if ident.startswith("UI-INV-")} == {
        f"UI-INV-MUST-{number:03d}" for number in range(1, 9)
    }
