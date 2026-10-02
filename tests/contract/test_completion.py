import json

import pytest

from tools import acceptance
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
    manifest["criteria"]["SC-REC-004"]["passed"] = False
    with pytest.raises(ValueError, match="Every MUST"):
        completion_status(manifest)


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
