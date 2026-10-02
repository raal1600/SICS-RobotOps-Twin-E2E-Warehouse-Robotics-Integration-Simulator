"""Fail closed on unreviewed findings; retain full scanner output and exact scopes."""

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def finding_scope(finding: dict) -> tuple[str, str, str]:
    path = Path(finding["filename"].replace("\\", "/"))
    if path.is_absolute():
        path = path.relative_to(ROOT)
    source = (ROOT / path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    line = finding["line_number"]
    nodes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.Import, ast.ImportFrom))
        and node.lineno <= line <= (node.end_lineno or node.lineno)
    ]
    node = min(nodes, key=lambda item: (item.end_lineno or item.lineno) - item.lineno)
    scope = node.name if isinstance(node, ast.FunctionDef) else "import subprocess"
    fingerprint = hashlib.sha256(ast.dump(node).encode()).hexdigest()
    return path.as_posix(), scope, fingerprint


def review(findings: list[dict], exceptions: list[dict]) -> list[dict]:
    results = []
    for finding in findings:
        path, scope, fingerprint = finding_scope(finding)
        matches = [
            item
            for item in exceptions
            if (item["path"], item["scope"], item["ast_sha256"], item["test_id"])
            == (path, scope, fingerprint, finding["test_id"])
        ]
        results.append(
            {
                "path": path,
                "scope": scope,
                "test_id": finding["test_id"],
                "ast_sha256": fingerprint,
                "reviewed": bool(matches) and finding["issue_severity"] == "LOW",
                "rationale": matches[0]["rationale"] if matches else "UNREVIEWED",
            }
        )
    return results


def main() -> None:
    out = ROOT / "artifacts"
    out.mkdir(exist_ok=True)
    bandit = subprocess.run(
        [
            sys.executable,
            "-m",
            "bandit",
            "-r",
            "robotops",
            "apps",
            "blender/scripts",
            "--ignore-nosec",
            "-f",
            "json",
            "-o",
            str(out / "bandit.json"),
        ],
        cwd=ROOT,
        check=False,
    )
    audit = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip_audit",
            "--strict",
            "--format",
            "json",
            "--output",
            str(out / "pip-audit.json"),
        ],
        cwd=ROOT,
        check=False,
    )
    raw = json.loads((out / "bandit.json").read_text(encoding="utf-8"))
    exceptions = json.loads((ROOT / "docs/security-exceptions.json").read_text())
    reviewed = review(raw["results"], exceptions)
    passed = (
        bandit.returncode in {0, 1}
        and not raw["errors"]
        and all(item["reviewed"] for item in reviewed)
        and audit.returncode == 0
    )
    result = {
        "passed": passed,
        "lock_sha256": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
        "bandit_exit": bandit.returncode,
        "pip_audit_exit": audit.returncode,
        "findings": reviewed,
    }
    (out / "security-review.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
