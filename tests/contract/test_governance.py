import ast
import json
from pathlib import Path

from tools.acceptance import evaluate, read_junit
from tools.drift_check import check, criterion_ids
from tools.security_check import review


def test_knowledge_base_links_ids_sources_and_status():
    result = check()
    assert result["passed"], result["errors"]


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
