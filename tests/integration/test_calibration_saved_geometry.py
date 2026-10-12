"""Saved capture geometry agrees with controller records and cannot mutate current state."""

import json

import numpy as np
from fastapi.testclient import TestClient

from apps.api.app import create_app
from robotops.calibration.contracts import Capture
from robotops.calibration.lifecycle import Mutation
from robotops.calibration.reproduction import reproduce
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


def test_saved_capture_pose_and_plan_are_read_only_and_survive_physical_camera_movement(tmp_path):
    runtime = SyntheticRuntime(tmp_path / "runtime.db", Settings.calibration(seed=83))
    engine = Engine(Store(tmp_path / "workflow.db"), runtime)
    service = engine.calibration
    camera = "camera-west"
    service.configure(camera, Mutation(request_id="configure", expected_revision=0))
    acquired = service.acquire(
        camera, "presented-fit", Mutation(request_id="acquire", expected_revision=1)
    )
    capture = service.store.record("capture", acquired.record_ids[0], Capture)
    with TestClient(create_app(engine.store, engine, test_registry=False)) as client:
        query = {"camera_id": camera, "capture_id": capture.capture_id, "mode": "capture"}
        before = (
            runtime.world().fingerprint()
            if hasattr(runtime.world(), "fingerprint")
            else runtime.world().model_dump_json()
        )
        states = service.store.states()
        response = client.get("/calibration/geometry", params=query)
        assert response.status_code == 200, response.text
        scene = response.json()
        shapes = {item["name"]: item for item in scene["scene"]["objects"]}
        np.testing.assert_array_equal(
            shapes["Robot/ToolChanger"]["position"], np.array(capture.t_b_f.matrix)[:3, 3]
        )
        assert any(name.startswith("Board/marker-") for name in shapes)
        assert len(shapes) < 512
        assert "Instructor geometry" in scene["scope"]
        poses = client.get("/calibration/geometry", params={**query, "mode": "poses"})
        assert poses.status_code == 200
        rows = poses.json()["numbers"]["poses"]
        assert len(rows) == 18 and sum(row["accepted_board_pose"] for row in rows) >= 10
        assert (
            client.get(
                "/calibration/geometry", params={**query, "camera_id": "camera-east"}
            ).status_code
            == 409
        )
        assert client.post("/calibration/geometry", json=query).status_code == 405
        assert service.store.states() == states
        assert (
            runtime.world().fingerprint()
            if hasattr(runtime.world(), "fingerprint")
            else runtime.world().model_dump_json()
        ) == before
        service.move_camera(
            camera, Mutation(request_id="move", expected_revision=2), (0.04, 0, 0), (0, 0.025, 0)
        )
        moved = runtime.world().model_dump_json()
        assert client.get("/calibration/geometry", params=query).json() == scene
        assert runtime.world().model_dump_json() == moved
        current = service.sensor.presentation_snapshot(runtime.world())
        current_west = next(item for item in current.objects if item.name == "Sensor/camera-west")
        assert (
            abs(current_west.position[0] - shapes["Sensor/camera-west"]["position"][0] - 0.04)
            < 1e-12
        )
    manifest = service.evidence_manifest()
    assert len(manifest["controller"]["capture_presentations"]) == 18
    exported = service.export(tmp_path / "export")
    result = reproduce(exported.parent)
    assert result["passed"], result
    assert not result["different_trace_source_ids"]
    assert len(result["capture_presentation_results"]) == 18
    assert all(item["matches_saved"] for item in result["capture_presentation_results"])
    (tmp_path / "capture-presentation.json").write_text(
        json.dumps(scene, indent=2), encoding="utf-8"
    )
