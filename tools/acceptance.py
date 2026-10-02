"""Run real acceptance gates and derive criterion results from inspectable evidence."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree

from robotops.blender.adapter import executable
from tools.drift_check import ROOT, criterion_ids

REPO = "raal1600/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator"
PAGES = f"https://raal1600.github.io/{REPO.split('/')[1]}/"
SYNC_FILES = [
    "README.md",
    "PUBLICATION.md",
    "CODEX_GOAL_CHECKLIST.md",
    "GOAL_PROGRESS.md",
    "ACCEPTANCE_REPORT.md",
    "CITATION.cff",
    "reports/01-design.md",
    "reports/02-avgransning.md",
    "reports/03-diskussion.md",
    "publication/status.json",
    "publication/diagrams.json",
    "publication/style.css",
    "publication/references.json",
    "tools/build_publication.py",
    "contracts/openapi.json",
    "docs/implementation/acceptance.md",
    "docs/implementation/dependencies.md",
    "docs/security-exceptions.json",
    "docs/implementation/desktop.md",
    "docs/evidence/desktop-launcher.json",
    "docs/implementation/playback.md",
    "docs/implementation/blender.md",
    "docs/implementation/operations.md",
    "docs/implementation/contracts.md",
    "docs/adr/0003-recorded-motion-illustration.md",
]


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def source_identity() -> dict:
    names = git("ls-files", "--cached", "--others", "--exclude-standard").splitlines()
    content = hashlib.sha256()
    for name in sorted(set(names)):
        path = ROOT / name
        if (
            path.is_file()
            and not name.startswith("docs/evidence/")
            and name != "ACCEPTANCE_REPORT.md"
        ):
            content.update(name.encode() + b"\0" + path.read_bytes())
    return {
        "commit": git("rev-parse", "HEAD"),
        "dirty": bool(git("status", "--porcelain")),
        "source_sha256": content.hexdigest(),
    }


def read_junit(path: Path) -> dict[str, bool]:
    if not path.is_file():
        return {}
    return {
        case.attrib["classname"].replace(".", "/") + ".py::" + case.attrib["name"]: not any(
            case.find(kind) is not None for kind in ("failure", "error", "skipped")
        )
        for case in ElementTree.parse(path).iter("testcase")
    }


def evaluate(item: dict, gates: dict, suites: list[dict[str, bool]]) -> tuple[bool, list[str]]:
    failures = [name for name in item["gates"] if not gates.get(name, {}).get("passed", False)]
    for pattern in item["tests"]:
        for index, suite in enumerate(suites, 1):
            matched = [
                value
                for name, value in suite.items()
                if name.split("::")[-1].split("[")[0] == pattern
            ]
            if not matched or not all(matched):
                failures.append(f"run {index}: {pattern} missing/failed/skipped")
    return not failures, failures


def fetch(url: str) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "RobotOpsTwin-acceptance/1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.status, response.read()


def remote_checks(commit: str) -> dict:
    result: dict = {"commit": commit, "workflows": {}, "links": {}}
    for workflow in ("ci.yml", "publish-reports.yml"):
        url = f"https://api.github.com/repos/{REPO}/actions/workflows/{workflow}/runs?head_sha={commit}&per_page=10"
        try:
            _, body = fetch(url)
            runs = json.loads(body)["workflow_runs"]
            valid = [
                run for run in runs if run["head_sha"] == commit and run["conclusion"] == "success"
            ]
            result["workflows"][workflow] = {
                "passed": bool(valid),
                "query": url,
                "runs": [
                    {
                        key: run[key]
                        for key in ("id", "head_sha", "status", "conclusion", "html_url")
                    }
                    for run in runs
                ],
            }
        except (OSError, ValueError, KeyError) as exc:
            result["workflows"][workflow] = {"passed": False, "error": str(exc), "query": url}
    for name in (
        "build.json",
        "index.html",
        "governance.html",
        "design.html",
        "avgransning.html",
        "diskussion.html",
        "diagram.html",
        "kallor.html",
        "downloads/01-design.pdf",
        "downloads/02-avgransning.pdf",
        "downloads/03-diskussion.pdf",
        "downloads/robotops-twin-samlat.pdf",
        "sources/ACCEPTANCE_REPORT.md",
    ):
        try:
            status, body = fetch(PAGES + name)
            passed = status == 200
            if name == "build.json":
                result["manifest"] = json.loads(body)
                passed = passed and result["manifest"]["source_commit"] == commit
            if name == "governance.html":
                passed = (
                    passed and b"SUCCESS_CRITERIA.md" in body and b"ACCEPTANCE_REPORT.md" in body
                )
            if name.endswith(".pdf"):
                passed = passed and body.startswith(b"%PDF-")
            result["links"][name] = {
                "url": PAGES + name,
                "passed": passed,
                "status": status,
                "sha256": hashlib.sha256(body).hexdigest(),
            }
        except (OSError, ValueError, KeyError) as exc:
            result["links"][name] = {"passed": False, "error": str(exc)}
    return result


def refresh_remote(manifest_path: Path, mapping: dict) -> dict:
    """Add live remote attestation to an existing run without changing its local evidence."""
    out = manifest_path.resolve().parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    original = out / "local-manifest.json"
    if not original.exists():
        shutil.copyfile(manifest_path, original)
    remote = remote_checks(manifest["source"]["commit"])
    (out / "remote.json").write_text(json.dumps(remote, indent=2) + "\n", encoding="utf-8")
    command = [
        "uv",
        "run",
        "--locked",
        "python",
        "-m",
        "tools.dev",
        "acceptance",
        "--refresh-remote",
        manifest_path.relative_to(ROOT).as_posix(),
    ]
    for name, workflow in (("ci", "ci.yml"), ("publication_remote", "publish-reports.yml")):
        manifest["gates"][name] = {
            "passed": remote.get("workflows", {}).get(workflow, {}).get("passed", False),
            "command": command,
        }
    manifest["gates"]["pages"] = {
        "passed": bool(remote.get("links"))
        and all(item["passed"] for item in remote.get("links", {}).values()),
        "command": command,
    }
    manifest["remote_verified_at"] = datetime.now(UTC).isoformat()
    suites = [read_junit(out / f"tests-{i}.xml") for i in (1, 2)]
    manifest["criteria"] = render_report(manifest, mapping, suites, out)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def render_report(manifest: dict, mapping: dict, suites: list[dict], out: Path) -> dict:
    gates = manifest["gates"]
    results = {ident: evaluate(item, gates, suites) for ident, item in mapping.items()}
    musts = criterion_ids()
    done = all(results[ident][0] for ident in musts) and gates.get("ci", {}).get("passed", False)
    evidence = out.relative_to(ROOT).as_posix()
    lines = [
        "# Acceptance Report",
        "",
        f"**{'DONE' if done else 'NOT DONE'}** — generated from executed gates; missing evidence is FAIL.",
        "",
        f"Source commit: `{manifest['source']['commit']}`. Dirty at start: `{manifest['source']['dirty']}`.",
        f"Inspected source hash: `{manifest['source']['source_sha256']}` (excludes generated acceptance/evidence).",
        f"Run time (UTC): {manifest['started_at']}. This report does not attest a later commit.",
        "Evidence/status successors run the full workflows again. Their exact-SHA reports are retained in [CI artifacts](https://github.com/"
        + REPO
        + "/actions/workflows/ci.yml), and the deployed SHA is in [public build.json]("
        + PAGES
        + "build.json). See [ADR 0002](docs/adr/0002-acceptance-attestations.md).",
        "",
        f"[Full manifest and commands]({evidence}/manifest.json). Logs and JUnit are in the same directory.",
        "",
        "## Environment",
        "",
        "```json",
        json.dumps(manifest["environment"], indent=2),
        "```",
        "",
        "## Executed commands",
        "",
        "| Gate | Result | Command / evidence |",
        "|---|---|---|",
    ]
    for name, gate in gates.items():
        command = " ".join(gate.get("command", []))
        log = gate.get("log")
        ref = f"[{name} log]({log})" if log else f"[{name} evidence]({evidence}/remote.json)"
        lines.append(f"| {name} | {'PASS' if gate['passed'] else 'FAIL'} | `{command}` {ref} |")
    lines += [
        "",
        "## Every MUST",
        "",
        "| Criterion | Result | Verification / named test | Relevant files / explanation |",
        "|---|---|---|---|",
    ]
    for ident in sorted(musts):
        item = mapping[ident]
        passed, failures = results[ident]
        tests = ", ".join(f"`{name}`" for name in item["tests"]) or "Gate evidence"
        files = ", ".join(f"[{name}]({name})" for name in item["files"])
        explanation = item["explanation"] + (" Failure: " + "; ".join(failures) if failures else "")
        lines.append(
            f"| {ident} | {'PASS' if passed else 'FAIL'} | {', '.join(item['gates'])}: {tests} | {files}. {explanation} |"
        )
    lines += ["", "## SHOULD results and optional backlog", ""]
    for ident in sorted(criterion_ids(level="SHOULD")):
        passed, failures = results[ident]
        lines.append(
            f"- {ident}: {'PASS' if passed else 'FAIL'}. {mapping[ident]['explanation']}"
            + (" " + "; ".join(failures) if failures else "")
        )
    lines += [
        "",
        "Optional model provider/fallback, external ERP outbox, OPC UA, contact physics and real hardware remain non-blocking and unimplemented.",
        "",
        "## Windows desktop extension",
        "",
        "The native EXE starts an owned API in an embedded WebView2 window and closes its process tree on exit. Persistent state uses the same recovery rules. [Desktop lifecycle and build](docs/implementation/desktop.md), [actual Windows/Blender evidence](docs/evidence/desktop-launcher.json), and [Windows workflow](https://github.com/"
        + REPO
        + "/actions/workflows/desktop.yml) record its separate native build/window checks. Cross-platform close/reopen and independent-port tests are included in both mandatory suite runs above.",
        "",
        "## Documentation drift and synchronization",
        "",
        "Drift detected: yes. Design-only status, obsolete report command example, proposed network bridge, publication covers, tool commands and operational checklist lagged implementation. They were synchronized with the durable workflow, bounded Blender adapter, observation/recovery semantics and P7 evidence. External company claims were not promoted to independently verified facts.",
        "",
        "Synchronized source files:",
        "",
        *[f"- `{name}`" for name in SYNC_FILES],
        "",
        "Generated publication is rebuilt by tools/build_publication.py; PDFs/Pages are never manually edited. Local build evidence does not prove remote deployment. Missing final-SHA CI/Pages evidence remains FAIL.",
        "",
    ]
    (ROOT / "ACCEPTANCE_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    return {
        ident: {"passed": passed, "failures": failures}
        for ident, (passed, failures) in results.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--local",
        action="store_true",
        help="Run local gates; leave remote criteria FAIL and exit by local gates.",
    )
    parser.add_argument(
        "--report-only",
        type=Path,
        help="Re-render an existing manifest; does not rerun or refresh evidence.",
    )
    parser.add_argument(
        "--refresh-remote",
        type=Path,
        help="Verify live CI/Pages for an existing run's exact SHA, then regenerate its report.",
    )
    args = parser.parse_args()
    mapping = json.loads((ROOT / "docs/acceptance-map.json").read_text())
    if args.refresh_remote:
        manifest = refresh_remote(args.refresh_remote.resolve(), mapping)
        passed = all(manifest["criteria"][ident]["passed"] for ident in criterion_ids())
        print("All MUST criteria PASS" if passed else "NOT DONE: inspect ACCEPTANCE_REPORT.md")
        raise SystemExit(0 if passed else 1)
    if args.report_only:
        out = args.report_only.resolve().parent
        manifest = json.loads(args.report_only.read_text())
        render_report(manifest, mapping, [read_junit(out / f"tests-{i}.xml") for i in (1, 2)], out)
        return
    out = ROOT / "docs/evidence/acceptance" / datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    out.mkdir(parents=True, exist_ok=False)
    environment = {
        "python": sys.version,
        "platform": platform.platform(),
        "dependencies": {
            name: importlib.metadata.version(name)
            for name in (
                "fastapi",
                "pydantic",
                "pytest",
                "ruff",
                "mypy",
                "weasyprint",
                "bandit",
                "pip-audit",
            )
        },
        "lock_sha256": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
    }
    manifest = {
        "started_at": datetime.now(UTC).isoformat(),
        "source": source_identity(),
        "environment": environment,
        "gates": {},
    }

    def run(name: str, command: list[str]) -> None:
        print(f"Running {name}", flush=True)
        started = time.monotonic()
        try:
            process = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            code, output = process.returncode, process.stdout + process.stderr
        except OSError as exc:
            code, output = -1, str(exc)
        log = out / f"{name}.log"
        log.write_text(output, encoding="utf-8")
        manifest["gates"][name] = {
            "passed": code == 0,
            "exit_code": code,
            "command": command,
            "seconds": time.monotonic() - started,
            "log": log.relative_to(ROOT).as_posix(),
        }
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(f"{name}: exit {code}", flush=True)

    python = sys.executable
    uv = shutil.which("uv") or str(Path.home() / ".local/bin/uv.exe")
    run("setup", [uv, "sync", "--locked", "--all-groups"])
    try:
        run("blender_version", [executable(), "--version"])
    except FileNotFoundError as exc:
        manifest["gates"]["blender_version"] = {"passed": False, "error": str(exc)}
    run("security", [python, "-m", "tools.dev", "security"])
    for filename in ("bandit.json", "pip-audit.json", "security-review.json"):
        if (ROOT / "artifacts" / filename).exists():
            shutil.copyfile(ROOT / "artifacts" / filename, out / filename)
    for i in (1, 2):
        with tempfile.TemporaryDirectory(prefix=f"robotops-acceptance-{i}-") as directory:
            run(
                f"tests_{i}",
                [
                    python,
                    "-m",
                    "tools.dev",
                    "test",
                    f"--basetemp={directory}/fixtures",
                    f"--junitxml={out / f'tests-{i}.xml'}",
                    "--cov=robotops",
                    "--cov=apps",
                    f"--cov-report=json:{out / f'coverage-{i}.json'}",
                    "--cov-report=term",
                ],
            )
    suites = [read_junit(out / f"tests-{i}.xml") for i in (1, 2)]
    stable = bool(suites[0]) and suites[0] == suites[1] and all(suites[0].values())
    (out / "repeatability.json").write_text(
        json.dumps({"passed": stable, "test_count": len(suites[0]), "tests": suites}, indent=2)
    )
    manifest["gates"]["repeatability"] = {
        "passed": stable,
        "log": (out / "repeatability.json").relative_to(ROOT).as_posix(),
    }
    for name in ("lint", "typecheck"):
        run(name, [python, "-m", "tools.dev", name])
    for scenario in (
        "happy_path",
        "lost_ack_after_effect",
        "lost_ack_before_effect",
        "ambiguous",
        "restart",
        "logical_estop",
        "cell_fault",
    ):
        directory = ROOT / "runs" / out.name / scenario
        run(
            "demo_" + scenario,
            [
                python,
                "-m",
                "tools.dev",
                "demo",
                "--runtime",
                "blender",
                "--scenario",
                scenario,
                "--directory",
                str(directory),
            ],
        )
        if (directory / "result.json").exists():
            shutil.copyfile(directory / "result.json", out / f"demo-{scenario}.json")
    remote = (
        remote_checks(manifest["source"]["commit"])
        if not args.local
        else {"reason": "Remote gates not run; NOT DONE until final commit is verified."}
    )
    (out / "remote.json").write_text(json.dumps(remote, indent=2) + "\n")
    for name, workflow in (("ci", "ci.yml"), ("publication_remote", "publish-reports.yml")):
        manifest["gates"][name] = {
            "passed": remote.get("workflows", {}).get(workflow, {}).get("passed", False)
        }
    manifest["gates"]["pages"] = {
        "passed": bool(remote.get("links"))
        and all(item["passed"] for item in remote.get("links", {}).values())
    }
    render_report(manifest, mapping, suites, out)
    run("drift", [python, "-m", "tools.drift_check"])
    run("publication", [python, "-m", "tools.dev", "docs"])
    manifest["criteria"] = render_report(manifest, mapping, suites, out)
    run("publication_final", [python, "-m", "tools.dev", "docs"])
    if not manifest["gates"]["publication_final"]["passed"]:
        manifest["gates"]["publication"]["passed"] = False
    manifest["criteria"] = render_report(manifest, mapping, suites, out)
    for filename in ("drift.json",):
        if (ROOT / "artifacts" / filename).exists():
            shutil.copyfile(ROOT / "artifacts" / filename, out / filename)
    if (ROOT / "_site/build.json").exists():
        shutil.copyfile(ROOT / "_site/build.json", out / "publication-build.json")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    relevant = [
        gate["passed"]
        for name, gate in manifest["gates"].items()
        if not args.local or name not in {"ci", "publication_remote", "pages"}
    ]
    print(f"Evidence: {out}", flush=True)
    raise SystemExit(0 if all(relevant) else 1)


if __name__ == "__main__":
    main()
