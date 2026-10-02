import json
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from apps.api.app import create_app
from robotops.blender.visualization import MotionRecording
from robotops.workflow.store import Store


def test_headless_and_missing_jobs_have_no_blender_replay(tmp_path, order_request):
    store = Store(tmp_path / "workflow.db")
    job_id = store.intake(order_request, "key").job_ids[0]
    client = TestClient(create_app(store))
    assert client.get(f"/jobs/{job_id}/playback").json()["status"] == "UNAVAILABLE"
    assert client.post(f"/jobs/{job_id}/playback/import").status_code == 409
    assert client.get("/jobs/absent/playback").status_code == 404


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
        ["node", "--test", "tests/ui/playback.test.cjs"], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert Path("apps/erp_ui/playback.js").is_file()
