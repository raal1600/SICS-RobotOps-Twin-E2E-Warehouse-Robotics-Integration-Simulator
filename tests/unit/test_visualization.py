import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from apps.api.app import create_app
from robotops.blender.visualization import MotionRecording
from robotops.cell.runtime import SyntheticRuntime
from robotops.domain.models import Fault, OrderRequest, PresentationSnapshot
from robotops.presentation_io import write_snapshot
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


def test_headless_and_missing_jobs_have_no_blender_replay(tmp_path, order_request):
    store = Store(tmp_path / "workflow.db")
    job_id = store.intake(order_request, "key").job_ids[0]
    client = TestClient(create_app(store))
    assert client.get(f"/jobs/{job_id}/playback").json()["status"] == "UNAVAILABLE"
    assert client.post(f"/jobs/{job_id}/playback/import").status_code == 409
    assert client.get("/jobs/absent/playback").status_code == 404


def test_scene_is_visible_before_execution_and_historical_snapshot_survives_later_orders(
    tmp_path, order_request
):
    store = Store(tmp_path / "workflow.db")
    runtime = SyntheticRuntime(tmp_path / "runtime.db")
    engine = Engine(store, runtime)
    client = TestClient(create_app(store, engine))
    initial = client.get("/cell/scene").json()
    assert initial["source"] == "CURRENT_WORLD_REFERENCE"
    assert len(initial["objects"]) > 20
    job_id = store.intake(order_request, "key").job_ids[0]
    assert client.get(f"/jobs/{job_id}/playback").json()["scene"] == initial
    engine.run(job_id, Fault.BRAIN_TIMEOUT)
    saved = client.get(f"/jobs/{job_id}/playback").json()
    assert saved["scene"]["source"] == "SAVED_START_SCENE"
    second = OrderRequest.model_validate({**order_request.model_dump(), "order_id": "second"})
    next_job = store.intake(second, "key2").job_ids[0]
    engine.run(next_job)
    assert client.get("/cell/scene").json()["objects"] != initial["objects"]
    restarted = TestClient(
        create_app(Store(store.path), Engine(Store(store.path), SyntheticRuntime(runtime.db.path)))
    )
    assert restarted.get(f"/jobs/{job_id}/playback").json() == saved
    # Legacy jobs lacking a snapshot explicitly expose only a current reference.
    with store.transaction() as db:
        db.execute(
            "DELETE FROM records WHERE kind=? AND id=?", (PresentationSnapshot.__name__, job_id)
        )
    legacy = restarted.get(f"/jobs/{job_id}/playback").json()
    assert legacy["scene"]["source"] == "CURRENT_WORLD_REFERENCE"
    assert legacy["scene"]["objects"] == client.get("/cell/scene").json()["objects"]


def test_offline_viewer_assets_have_pinned_integrity_and_confined_routes(tmp_path):
    vendor = Path("apps/erp_ui/vendor")
    manifest = json.loads((vendor / "manifest.json").read_text())
    assert manifest["version"] == "0.180.0" and manifest["license"] == "MIT"
    lock = json.loads((vendor / "package-lock.json").read_text())
    assert lock["packages"]["node_modules/three"]["version"] == manifest["version"]
    assert lock["packages"]["node_modules/three"]["integrity"] == manifest["integrity"]
    client = TestClient(create_app(Store(tmp_path / "workflow.db")))
    for name, digest in manifest["sha256"].items():
        assert hashlib.sha256((vendor / name).read_bytes()).hexdigest() == digest
        if name.endswith(".js"):
            response = client.get("/ui/vendor/" + name)
            assert response.content == (vendor / name).read_bytes()
    assert client.get("/ui/scene-view.js").status_code == 200
    for name, media_type in [("workflow-guide.js", "text/javascript"), ("theme.css", "text/css")]:
        response = client.get("/ui/" + name)
        assert response.content == (Path("apps/erp_ui") / name).read_bytes()
        assert response.headers["content-type"].startswith(media_type)
    assert client.get("/ui/vendor/manifest.json").status_code == 422
    assert client.get("/ui/unknown.js").status_code == 422


@pytest.mark.parametrize("invalid", ["gap", "duplicate", "unknown", "complete", "nan"])
def test_visual_schema_rejects_fabricated_or_noncontiguous_records(invalid):
    data = {
        "command_id": "c1",
        "job_id": "j1",
        "scene_epoch": "e1",
        "product_id": "p1",
        "frame_id": "cell_world",
        "complete": False,
        "objects": [
            {"name": "Gripper", "position": [0, 0, 0], "size": [1, 1, 1], "color": [1, 0, 0]}
        ],
        "frames": [{"frame": 1, "phase": "APPROACH", "positions": {"Gripper": [0, 0, 0]}}],
    }
    MotionRecording.model_validate(data)
    if invalid == "gap":
        data["frames"][0]["frame"] = 2
    elif invalid == "duplicate":
        data["objects"] *= 2
    elif invalid == "unknown":
        data["frames"][0]["positions"]["Unrecorded"] = [1, 0, 0]
    elif invalid == "complete":
        data["complete"] = True
    else:
        data["frames"][0]["positions"]["Gripper"][0] = float("nan")
    with pytest.raises(ValidationError):
        MotionRecording.model_validate_json(json.dumps(data))


def test_playback_controls_never_dispatch_and_preserve_partial_recording_limits():
    result = subprocess.run(
        [
            "node",
            "--test",
            "tests/ui/playback.test.cjs",
            "tests/ui/dashboard.test.cjs",
            "tests/ui/workflow-guide.test.cjs",
            "tests/ui/investigation.test.cjs",
            "tests/ui/integration-console.test.cjs",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert Path("apps/erp_ui/playback.js").is_file()


@pytest.mark.parametrize("persistent", [False, True])
def test_snapshot_publication_retries_only_sharing_lock_and_retains_old_data(
    tmp_path, monkeypatch, persistent
):
    path = tmp_path / "motion.json"
    write_snapshot(path, {"frame": 4})
    replace = Path.replace
    calls = []

    def busy(source, destination):
        calls.append(source)
        assert json.loads(path.read_text()) == {"frame": 4}
        if persistent or len(calls) < 4:
            raise PermissionError("Windows reader sharing lock")
        return replace(source, destination)

    monkeypatch.setattr(Path, "replace", busy)
    monkeypatch.setattr("robotops.presentation_io.time.sleep", lambda _: None)
    if persistent:
        with pytest.raises(PermissionError):
            write_snapshot(path, {"frame": 8})
        assert len(calls) == 50
        assert json.loads(path.read_text()) == {"frame": 4}
    else:
        write_snapshot(path, {"frame": 8})
        assert len(calls) == 4
        assert json.loads(path.read_text()) == {"frame": 8}
