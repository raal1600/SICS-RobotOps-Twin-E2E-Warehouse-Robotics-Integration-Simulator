import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from apps.api.app import create_app
from robotops.blender.adapter import BlenderRuntime
from robotops.config import Settings
from robotops.domain.models import Fault, JobState, RobotCommand
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store

pytestmark = pytest.mark.blender


def test_live_recording_replay_restart_and_legacy_import_are_read_only(tmp_path, order_request):
    store = Store(tmp_path / "workflow.db")
    runtime = BlenderRuntime(tmp_path / "runtime.db", Settings(visual_frame_seconds=0.02))
    engine = Engine(store, runtime)
    client = TestClient(create_app(store, engine))
    job_id = store.intake(order_request, "key").job_ids[0]
    route = f"/jobs/{job_id}/playback"
    assert client.get(route).json()["status"] == "WAITING"
    counts = set()
    with ThreadPoolExecutor(max_workers=1) as pool:
        running = pool.submit(engine.run, job_id, Fault.DROP_ACK_AFTER_EFFECT)
        while not running.done():
            data = client.get(route).json()
            if data["status"] == "RECORDING":
                counts.add(len(data["recording"]["frames"]))
                assert data["job_state"] == "EXECUTING"
            time.sleep(0.05)
        job = running.result()
    assert len(counts) >= 2
    assert job.state == JobState.UNKNOWN_OUTCOME
    result = client.get(route).json()
    assert result["status"] == "RECORDED" and result["job_state"] == "UNKNOWN_OUTCOME"
    recording = result["recording"]
    command = store.load(RobotCommand, job.command_id)
    target = command.target_pose.position
    name = "Products/" + command.product_id
    frames = recording["frames"]
    source = frames[0]["positions"][name]
    assert source[0] < 0 and frames[19]["positions"][name] == source
    assert frames[39]["positions"][name][2] > source[2] + 0.35
    assert frames[69]["positions"][name][0] == pytest.approx(target[0])
    assert frames[89]["positions"][name] == pytest.approx(target)
    assert frames[99]["positions"][name] == pytest.approx(runtime.world().objects[0].pose.position)
    assert client.get(f"/jobs/{job_id}/artifact.png").content.startswith(b"\x89PNG")
    assert client.get("/ui/playback.js").status_code == 200
    before = (
        runtime.world(),
        runtime.events(),
        store.timeline(),
        runtime.journal(command.command_id),
    )
    restarted = TestClient(
        create_app(Store(store.path), Engine(Store(store.path), BlenderRuntime(runtime.db.path)))
    )
    for _ in range(3):
        assert restarted.get(route).json() == result
        assert restarted.post(route + "/import").json() == result
    assert before == (
        runtime.world(),
        runtime.events(),
        store.timeline(),
        runtime.journal(command.command_id),
    )

    # Older runs retain keyed .blend files but have no motion export or export digest.
    path = runtime.command_artifact(command.command_id, "motion.json")
    response_path = path.with_name("response.json")
    response = json.loads(response_path.read_bytes())
    response.pop("motion_sha256")
    response_path.write_text(json.dumps(response), encoding="utf-8")
    scene_digest = hashlib.sha256(path.with_name("scene.blend").read_bytes()).hexdigest()
    path.unlink()
    assert restarted.get(route).json()["can_import"]
    loaded = restarted.post(route + "/import")
    assert loaded.status_code == 200 and loaded.json()["recording"] == recording
    assert hashlib.sha256(path.with_name("scene.blend").read_bytes()).hexdigest() == scene_digest
    assert before == (
        runtime.world(),
        runtime.events(),
        store.timeline(),
        runtime.journal(command.command_id),
    )
    # The illustration cannot force success when observation evidence contradicts it.
    assert (
        engine.reconcile(job_id, Fault.CONTRADICTORY_OBSERVATION).state
        == JobState.REQUIRES_INTERVENTION
    )
    assert restarted.get(route).json()["job_state"] == "REQUIRES_INTERVENTION"
    assert sum(e.event_type == "PICK_EFFECT" for e in runtime.events()) == 1


def test_recording_corruption_partial_and_path_boundaries(tmp_path, order_request):
    store = Store(tmp_path / "workflow.db")
    runtime = BlenderRuntime(tmp_path / "runtime.db")
    engine = Engine(store, runtime)
    job_id = store.intake(order_request, "key").job_ids[0]
    job = engine.run(job_id, Fault.DROP_ACK_AFTER_EFFECT)
    client = TestClient(create_app(store, engine))
    route = f"/jobs/{job_id}/playback"
    path = runtime.command_artifact(job.command_id, "motion.json")
    original = path.read_bytes()
    data = json.loads(original)
    data["frames"][0]["positions"]["Gripper"][0] += 0.1
    path.write_text(json.dumps(data), encoding="utf-8")
    assert client.get(route).json()["status"] == "UNAVAILABLE"  # digest mismatch
    path.with_name("response.json").unlink()  # interrupted operation, no final checkpoint
    data["complete"] = False
    data["frames"] = data["frames"][:12]
    path.write_text(json.dumps(data), encoding="utf-8")
    assert client.get(route).json()["status"] == "PARTIAL"
    data["job_id"] = "different-job"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert client.get(route).json()["status"] == "UNAVAILABLE"
    path.write_bytes(b"bad json")
    assert client.post(route + "/import").status_code == 409
    path.write_bytes(b"x" * 2_000_001)
    assert client.get(route).json()["status"] == "UNAVAILABLE"
    with pytest.raises(ValueError, match="INVALID_ARTIFACT_NAME"):
        runtime.command_artifact(job.command_id, "../workflow.db")
    with runtime.db.transaction() as db:
        db.execute(
            "UPDATE meta SET value=? WHERE key=?", (str(tmp_path), "exchange:" + job.command_id)
        )
    assert client.get(route).json()["status"] == "UNAVAILABLE"
    with pytest.raises(ValueError, match="ARTIFACT_OUTSIDE_RUNTIME"):
        runtime.command_artifact(job.command_id, "scene.blend")


@pytest.mark.parametrize(
    "fault", [Fault.DROP_ACK_BEFORE_EFFECT, Fault.LOGICAL_ESTOP, Fault.BRAIN_INVALID_OUTPUT]
)
def test_unexecuted_commands_never_invent_motion(tmp_path, order_request, fault):
    store = Store(tmp_path / "workflow.db")
    runtime = BlenderRuntime(tmp_path / "runtime.db")
    engine = Engine(store, runtime)
    job_id = store.intake(order_request, "key").job_ids[0]
    engine.run(job_id, fault)
    client = TestClient(create_app(store, engine))
    result = client.get(f"/jobs/{job_id}/playback").json()
    assert result["recording"] is None and not result["can_import"]
    assert client.get(f"/jobs/{job_id}/artifact.png").status_code == 404
    assert client.post(f"/jobs/{job_id}/playback/import").status_code == 409
    assert not list(runtime.artifacts.glob("*/motion.json"))
