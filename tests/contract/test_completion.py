import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tools import acceptance, sync_status
from tools.drift_check import criterion_ids
from tools.sync_status import completion_status


def test_completion_requires_every_must_and_all_remote_gates():
    assert completion_status(None) == "NOT DONE"
    with pytest.raises(ValueError, match="Every MUST"):
        completion_status({})
    manifest = {"criteria": {ident: {"passed": True} for ident in criterion_ids()}}
    with pytest.raises(ValueError, match="Remote"):
        completion_status(manifest)
    manifest["gates"] = {name: {"passed": True} for name in ("ci", "publication_remote", "pages")}
    assert completion_status(manifest) == "DONE"
    manifest["criteria"]["HKM-VIS-MUST-025"]["passed"] = False
    with pytest.raises(ValueError, match="Every MUST"):
        completion_status(manifest)
    manifest["criteria"]["HKM-VIS-MUST-025"]["passed"] = True
    manifest["criteria"]["SC-REC-004"]["passed"] = False
    with pytest.raises(ValueError, match="Every MUST"):
        completion_status(manifest)


def test_status_sync_uses_current_utc_date_and_marks_unaccepted_revision_pending(
    tmp_path, monkeypatch
):
    class FixedClock:
        @staticmethod
        def now(zone):
            assert zone is UTC
            return datetime(2031, 2, 3, 0, 5, tzinfo=UTC)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sync_status, "datetime", FixedClock)
    Path("publication").mkdir()
    Path("reports").mkdir()
    Path("reports/design.md").write_text(
        "<!-- implementation-status:start -->\nold\n<!-- implementation-status:end -->\n"
        "Historical research stays unchanged.\n",
        encoding="utf-8",
    )
    Path("README.md").write_text("**Aktuell status:** old\n\nSetup unchanged.\n", encoding="utf-8")
    sync_status.update("HKM-P0", "Enhancement pending acceptance.")
    report = Path("reports/design.md").read_text(encoding="utf-8")
    assert "Implementation status, 2031-02-03:" in report
    assert "Historical research stays unchanged." in report
    assert "Enhancement pending acceptance. Status: NOT DONE." in report
    assert json.loads(Path("publication/status.json").read_text())["status"] == "NOT DONE"
    assert "**NOT DONE**" in Path("README.md").read_text()


def test_remote_refresh_retains_failed_local_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(acceptance, "ROOT", tmp_path)
    monkeypatch.setattr(
        acceptance,
        "remote_checks",
        lambda commit: {
            "commit": commit,
            "workflows": {name: {"passed": True} for name in ("ci.yml", "publish-reports.yml")},
            "links": {"build.json": {"passed": True}},
        },
    )
    monkeypatch.setattr(
        acceptance,
        "render_report",
        lambda manifest, mapping, suites, out: {
            "SC-REC-004": {"passed": manifest["gates"]["tests_1"]["passed"]}
        },
    )
    path = tmp_path / "manifest.json"
    original = {"source": {"commit": "original-sha"}, "gates": {"tests_1": {"passed": False}}}
    path.write_text(json.dumps(original))
    refreshed = acceptance.refresh_remote(path, {})
    assert refreshed["source"] == original["source"]
    assert refreshed["gates"]["tests_1"]["passed"] is False
    assert refreshed["criteria"]["SC-REC-004"]["passed"] is False
    assert json.loads((tmp_path / "local-manifest.json").read_text()) == original
