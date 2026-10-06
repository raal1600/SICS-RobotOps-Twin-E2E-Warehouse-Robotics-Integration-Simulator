import hashlib
import json

import pytest

from tools import drift_check


@pytest.fixture
def repository(tmp_path, monkeypatch):
    (tmp_path / "publication").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "reports").mkdir()
    (tmp_path / "SUCCESS_CRITERIA.md").write_text("**SC-ARCH-001 MUST**\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("Current status.\n", encoding="utf-8")
    (tmp_path / "publication/references.json").write_text("[]", encoding="utf-8")
    (tmp_path / "publication/diagrams.json").write_text("{}", encoding="utf-8")
    (tmp_path / "publication/status.json").write_text(
        '{"summary":"Current status."}', encoding="utf-8"
    )
    (tmp_path / "docs/acceptance-map.json").write_text(
        '{"SC-ARCH-001":{"files":[]}}', encoding="utf-8"
    )
    (tmp_path / "Makefile").write_text(
        "setup test lint typecheck demo acceptance docs security:\n", encoding="utf-8"
    )
    monkeypatch.setattr(drift_check.subprocess, "check_output", lambda *args, **kwargs: b"")
    return tmp_path


def write_snapshot(root, text="[Original context](target.md)\n", folder="sources"):
    archive = root / "docs/evidence/frozen"
    snapshot = archive / folder / "original.md"
    snapshot.parent.mkdir(parents=True)
    snapshot.write_bytes(text.encode("utf-8"))
    data = {
        "archive_root": "docs/evidence/frozen",
        "copied": [
            {
                "archive_path": snapshot.relative_to(root).as_posix(),
                "archive_relative": snapshot.relative_to(archive).as_posix(),
                "source": "reports/original.md",
                "kind": "historical_source_copy",
                "sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest(),
                "bytes": snapshot.stat().st_size,
            }
        ],
    }
    manifest = archive / "inputs.json"
    manifest.write_text(json.dumps(data), encoding="utf-8")
    return snapshot, manifest, data


def test_verified_relocated_snapshot_retains_original_bytes_and_reports_binding(repository):
    (repository / "reports/target.md").write_text("Current status.\n", encoding="utf-8")
    snapshot, manifest, data = write_snapshot(repository)
    before = snapshot.read_bytes()
    result = drift_check.check(repository)
    assert result["passed"], result["errors"]
    assert snapshot.read_bytes() == before
    assert result["archived_markdown_snapshots"] == [
        {
            "path": data["copied"][0]["archive_path"],
            "source": "reports/original.md",
            "sha256": hashlib.sha256(before).hexdigest(),
            "bytes": len(before),
            "manifest": "docs/evidence/frozen/inputs.json",
            "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        }
    ]


@pytest.mark.parametrize("mutation", ["tampered", "missing"])
def test_changed_or_missing_snapshot_fails_closed(repository, mutation):
    snapshot, _, _ = write_snapshot(repository)
    if mutation == "tampered":
        snapshot.write_text("[Tampered](missing.md)\n", encoding="utf-8")
    else:
        snapshot.unlink()
    result = drift_check.check(repository)
    assert not result["passed"]
    assert not result["archived_markdown_snapshots"]
    assert any("Invalid archived Markdown manifest" in error for error in result["errors"])
    if mutation == "tampered":
        assert any("Broken repository link" in error for error in result["errors"])


def test_manifest_cannot_exempt_destination_outside_its_archive(repository):
    _, manifest, data = write_snapshot(repository)
    readme = repository / "README.md"
    readme.write_text("Current status. [Broken](missing.md)\n", encoding="utf-8")
    data["copied"][0].update(
        archive_path="README.md",
        archive_relative="../../../README.md",
        sha256=hashlib.sha256(readme.read_bytes()).hexdigest(),
        bytes=readme.stat().st_size,
    )
    manifest.write_text(json.dumps(data), encoding="utf-8")
    result = drift_check.check(repository)
    assert not result["passed"]
    assert not result["archived_markdown_snapshots"]
    assert any("invalid or duplicate Markdown destination" in e for e in result["errors"])
    assert "Broken repository link: README.md: missing.md" in result["errors"]


@pytest.mark.parametrize("name", ["docs/evidence/frozen/index.md", "docs/current.md"])
def test_unlisted_archive_and_current_markdown_links_remain_checked(repository, name):
    write_snapshot(repository)
    (repository / name).write_text("[Broken](missing.md)\n", encoding="utf-8")
    result = drift_check.check(repository)
    assert not result["passed"]
    assert len(result["archived_markdown_snapshots"]) == 1
    assert f"Broken repository link: {name}: missing.md" in result["errors"]


@pytest.mark.parametrize("mutation", ["invalid_json", "wrong_root", "duplicate", "no_source"])
def test_invalid_manifest_never_exempts_markdown(repository, mutation):
    _, manifest, data = write_snapshot(repository)
    if mutation == "wrong_root":
        data["archive_root"] = "docs/evidence/other"
    elif mutation == "duplicate":
        data["copied"].append(data["copied"][0])
    elif mutation == "no_source":
        del data["copied"][0]["source"]
    manifest.write_text("{" if mutation == "invalid_json" else json.dumps(data), encoding="utf-8")
    result = drift_check.check(repository)
    assert not result["passed"]
    assert not result["archived_markdown_snapshots"]
    assert any("Invalid archived Markdown manifest" in error for error in result["errors"])
    assert any("Broken repository link" in error for error in result["errors"])


def test_snapshot_exemption_preserves_criterion_source_and_diagram_checks(repository):
    write_snapshot(
        repository,
        "SC-ARCH-999 S99 {{figure:unknown}} [Historical](missing.md)\n",
        folder="reports",
    )
    result = drift_check.check(repository)
    assert not result["passed"]
    assert len(result["archived_markdown_snapshots"]) == 1
    assert any("Unknown criterion SC-ARCH-999" in error for error in result["errors"])
    assert any("Unknown source S99" in error for error in result["errors"])
    assert any("Unknown diagram unknown" in error for error in result["errors"])
    assert not any("Broken repository link" in error for error in result["errors"])
