import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.app import create_app
from robotops.blender.adapter import BlenderRuntime
from robotops.cell.runtime import CommunicationTimeout
from robotops.config import Settings
from robotops.domain.models import (
    Fault,
    JobState,
    OrderLine,
    OrderRequest,
    RobotCommand,
    WorldState,
)
from robotops.hkm_geometry import rotate_vector, tool_primitives
from robotops.observation.model import ObservationModel
from robotops.robotics.catalogue import load_catalogue
from robotops.robotics.trajectory import REQUIRED_PICK_PHASES
from robotops.workflow.engine import Engine
from robotops.workflow.store import Conflict, Store, digest

pytestmark = pytest.mark.blender


def make_engine(path):
    runtime = BlenderRuntime(path / "runtime.db", Settings.hkm())
    return Engine(Store(path / "workflow.db"), runtime, runtime.settings)


def intake(engine, index=0, order_id="blender-hkm"):
    product = engine.settings.products[index]
    request = OrderRequest(
        order_id=order_id,
        lines=(
            OrderLine(
                order_line_id="line",
                product_id=product.product_id,
                source_id=engine.settings.source_for(product.product_id),
                destination_id=engine.settings.destination_id,
            ),
        ),
    )
    return engine.store.intake(request, order_id).job_ids[0]


def failure_context(engine):
    return {
        "events": [(event.event_type, event.reason) for event in engine.store.timeline()[-5:]],
        "logs": [
            path.read_text(encoding="utf-8")[-1500:]
            for path in engine.runtime.artifacts.glob("*/runtime.log")
        ],
    }


def assert_recording(engine, command, before):
    runtime = engine.runtime
    catalogue = load_catalogue()
    recording = runtime.motion(command)
    assert recording is not None and recording.complete
    assert recording.schema_version == "2.0"
    assert recording.source == "BLENDER_EVALUATED_SCENE"
    assert recording.kinematics_version == "HKM_INSPIRED_VISUAL_KINEMATICS_V1"
    assert recording.command_id == command.command_id
    assert recording.total_frames == len(recording.frames)
    assert recording.frames[-1].sim_time_s == pytest.approx(recording.simulated_duration_s)
    assert set(REQUIRED_PICK_PHASES) <= {frame.phase for frame in recording.frames}
    objects = {item.name: item for item in recording.objects}
    assert {
        "RobotOpsTwin/Cell",
        "Robot/BaseColumn",
        "Robot/RotaryBase",
        "Robot/UpperAssembly",
        "Robot/WristAssembly",
        "Robot/ToolFlange",
        "Robot/ToolChanger",
        "ToolRack",
        "Conveyor",
        "ControlCabinet",
        "ControlCabinet/LogicalEstop",
        "Enclosure/OperatorGate",
        *(f"ToolRack/Dock{index:02}" for index in range(1, 7)),
        *("Locations/" + source.location_id for source in catalogue.layout.sources.values()),
        "Locations/" + catalogue.layout.destination.location_id,
        *("Tools/" + tool.tool_id for tool in catalogue.tools),
        *("Products/" + item.product_id for item in engine.settings.products),
    } <= objects.keys()
    assert not {"RobotCarriage", "RobotArm", "RobotSpindle"} & objects.keys()
    assert {
        objects["Locations/" + source.location_id].label
        for source in catalogue.layout.sources.values()
    } == set("ABCDEF")
    assert (
        len({objects["Products/" + item.product_id].size for item in engine.settings.products}) == 6
    )
    for side in ("Left", "Right"):
        for segment in ("Upper", "Lower"):
            name = f"Robot/ParallelLink{side}{segment}"
            rotations = {
                tuple(round(v, 5) for v in frame.transforms[name].quaternion_xyzw)
                for frame in recording.frames
            }
            assert len(rotations) > 10, name

    product_name = "Products/" + command.product_id
    original = next(
        item for item in before.objects if item.product.product_id == command.product_id
    )
    final = next(
        item for item in runtime.world().objects if item.product.product_id == command.product_id
    )
    assert recording.frames[0].transforms[product_name].position == pytest.approx(
        original.pose.position, abs=1e-6
    )
    assert recording.frames[-1].transforms[product_name].position == pytest.approx(
        final.pose.position, abs=1e-6
    )
    assert final.pose.position == pytest.approx(command.target_pose.position, abs=1e-6)
    assert final.location_id == command.destination_id and not final.attached
    attached = [
        frame for frame in recording.frames if frame.attached_product_id == command.product_id
    ]
    assert len(attached) > 20
    offsets = []
    for frame in attached:
        assert frame.active_tool_id == command.required_tool_id
        tool = frame.transforms["Tools/" + frame.active_tool_id]
        product = frame.transforms[product_name]
        inverse_rotation = tuple(-v for v in tool.quaternion_xyzw[:3]) + (tool.quaternion_xyzw[3],)
        offsets.append(
            rotate_vector(
                tuple(a - b for a, b in zip(product.position, tool.position, strict=True)),
                inverse_rotation,
            )
        )
    assert all(offset == pytest.approx(offsets[0], abs=1e-6) for offset in offsets)
    assert (
        math.dist(
            attached[0].transforms[product_name].position,
            attached[-1].transforms[product_name].position,
        )
        > 0.4
    )
    release_time = next(
        point.sim_time_s for point in command.trajectory.waypoints if point.phase == "RELEASE"
    )
    released = [frame for frame in recording.frames if frame.sim_time_s >= release_time]
    assert released and all(frame.attached_product_id is None for frame in released)
    assert all(
        frame.transforms[product_name].position
        == pytest.approx(command.target_pose.position, abs=1e-6)
        for frame in released
    )

    tool_ids = {tool.tool_id for tool in catalogue.tools}
    for frame in recording.frames:
        rack = set(frame.rack_tool_ids)
        assert len(rack) == (5 if frame.active_tool_id else 6)
        assert frame.active_tool_id not in rack
        assert rack | ({frame.active_tool_id} if frame.active_tool_id else set()) == tool_ids
        for tool_id in rack:
            tool = frame.transforms["Tools/" + tool_id]
            expected = tool_primitives(tool_id, catalogue.layout.tool_docks[tool_id].position)[0]
            assert tool.position == pytest.approx(expected["position"], abs=1e-6)
            assert tool.visible
        if frame.active_tool_id:
            mounted = frame.transforms["Tools/" + frame.active_tool_id]
            changer = frame.transforms["Robot/ToolChanger"]
            assert math.dist(mounted.position, changer.position) == pytest.approx(0.015, abs=1e-6)
            assert mounted.visible
    return recording


def test_hkm_real_blender_six_tool_showcase_articulates_attaches_and_releases(tmp_path):
    engine = make_engine(tmp_path)
    catalogue = load_catalogue()
    evidence = Path("artifacts/hkm-blender/tool-showcase")
    evidence.mkdir(parents=True, exist_ok=True)
    summaries = []
    for index, product in enumerate(catalogue.products):
        before = engine.runtime.world()
        job = engine.run(intake(engine, index, "showcase-" + product.sku))
        assert job.state == JobState.COMPLETED, failure_context(engine)
        command = engine.store.load(RobotCommand, job.command_id)
        assert command.required_tool_id == product.preferred_tool_id
        assert command.tool_selection.selected_tool_id == product.preferred_tool_id
        recording = assert_recording(engine, command, before)
        world = engine.runtime.world()
        assert world.tool_state.active_tool_id == product.preferred_tool_id
        assert world.robot_state.active_tool_id == product.preferred_tool_id
        assert len(world.tool_state.rack_tool_ids) == 5
        assert engine.runtime.journal(command.command_id).effect_count == 1
        events = engine.runtime.events(command.command_id)
        assert sum(event.event_type == "PICK_EFFECT" for event in events) == 1
        expected = "TOOL_CHANGE_NOT_REQUIRED" if index == 0 else "TOOL_CHANGE_COMPLETED"
        assert expected in {event.event_type for event in events}
        assert expected in {frame.phase for frame in recording.frames}
        if index:
            assert any(frame.active_tool_id is None for frame in recording.frames)
        path = engine.runtime.command_artifact(command.command_id, "response.json")
        response = json.loads(path.read_text(encoding="utf-8"))
        assert response["effect_count"] == 1
        assert {
            "Camera/OperatorOverview",
            "Camera/OverheadObservation",
            "Camera/SideInspection",
        } <= set(response["object_names"])
        assert (
            response["scene_sha256"]
            == hashlib.sha256(path.with_name("scene.blend").read_bytes()).hexdigest()
        )
        assert (
            response["motion_sha256"]
            == hashlib.sha256(path.with_name("motion.json").read_bytes()).hexdigest()
        )
        assert path.with_name("capture.png").read_bytes().startswith(b"\x89PNG")
        output = evidence / product.sku
        output.mkdir(exist_ok=True)
        for name in (
            "request.json",
            "response.json",
            "motion.json",
            "capture.png",
            "runtime.log",
            "scene.blend",
        ):
            shutil.copyfile(path.with_name(name), output / name)
        summaries.append(
            {
                "sku": product.sku,
                "tool": command.required_tool_id,
                "command_id": command.command_id,
                "effect_count": 1,
                "frames": recording.total_frames,
            }
        )
    assert sum(event.event_type == "PICK_EFFECT" for event in engine.runtime.events()) == 6
    assert len(list(engine.runtime.artifacts.glob("*/response.json"))) == 6
    assert all(
        obj.location_id == engine.settings.destination_id for obj in engine.runtime.world().objects
    )
    reopened = BlenderRuntime(engine.runtime.db.path)
    assert reopened.world().tool_state == engine.runtime.world().tool_state
    assert reopened.world().robot_state == engine.runtime.world().robot_state
    (evidence / "summary.json").write_text(json.dumps(summaries, indent=2) + "\n", encoding="utf-8")


def test_hkm_real_lost_ack_restart_ambiguity_and_read_only_replay_keep_one_command(tmp_path):
    engine = make_engine(tmp_path)
    job = engine.run(intake(engine, 1), Fault.DROP_ACK_AFTER_EFFECT)
    assert job.state == JobState.UNKNOWN_OUTCOME, failure_context(engine)
    original_id = job.command_id
    command = engine.store.load(RobotCommand, original_id)
    assert engine.runtime.journal(original_id).effect_count == 1
    restarted = Engine(Store(engine.store.path), BlenderRuntime(engine.runtime.db.path))
    assert (
        restarted.reconcile(job.job_id, Fault.CONTRADICTORY_OBSERVATION).state
        == JobState.REQUIRES_INTERVENTION
    )
    before = restarted.runtime.world(), restarted.runtime.events(), restarted.store.timeline()
    client = TestClient(create_app(restarted.store, restarted))
    for _ in range(2):
        replay = client.get(f"/jobs/{job.job_id}/playback").json()
        assert replay["status"] == "RECORDED"
        assert replay["job_state"] == "REQUIRES_INTERVENTION"
        assert client.get(f"/jobs/{job.job_id}/evidence").status_code == 200
    original_recording = restarted.runtime.motion(command)
    motion_path = restarted.runtime.command_artifact(original_id, "motion.json")
    response_path = motion_path.with_name("response.json")
    response = json.loads(response_path.read_text(encoding="utf-8"))
    response.pop("motion_sha256")  # Saved scenes without a retained recording can be exported.
    response_path.write_text(json.dumps(response), encoding="utf-8")
    scene_hash = hashlib.sha256(motion_path.with_name("scene.blend").read_bytes()).hexdigest()
    motion_path.unlink()
    imported = client.post(f"/jobs/{job.job_id}/playback/import")
    assert imported.status_code == 200 and imported.json()["status"] == "RECORDED"
    reexported = restarted.runtime.motion(command)
    assert reexported.command_id == original_recording.command_id
    assert len(reexported.frames) == len(original_recording.frames)
    for original_frame, exported_frame in zip(
        original_recording.frames, reexported.frames, strict=True
    ):
        assert exported_frame.phase == original_frame.phase
        assert exported_frame.active_tool_id == original_frame.active_tool_id
        assert exported_frame.rack_tool_ids == original_frame.rack_tool_ids
        assert exported_frame.attached_product_id == original_frame.attached_product_id
        for name, transform in original_frame.transforms.items():
            exported = exported_frame.transforms[name]
            assert exported.position == pytest.approx(transform.position, abs=1e-6)
            assert exported.quaternion_xyzw == pytest.approx(transform.quaternion_xyzw, abs=1e-6)
            assert exported.visible == transform.visible
    assert (
        hashlib.sha256(motion_path.with_name("scene.blend").read_bytes()).hexdigest() == scene_hash
    )
    assert before == (
        restarted.runtime.world(),
        restarted.runtime.events(),
        restarted.store.timeline(),
    )
    resolved = restarted.reconcile(job.job_id)
    assert resolved.state == JobState.COMPLETED and resolved.command_id == original_id
    assert restarted.runtime.apply(command).effect_count == 1
    with pytest.raises(Conflict):
        restarted.runtime.apply(command.model_copy(update={"source_id": "changed"}))
    assert sum(event.event_type == "PICK_EFFECT" for event in restarted.runtime.events()) == 1
    assert sum(event.event_type == "COMMAND_CREATED" for event in restarted.store.timeline()) == 1
    assert len(list(restarted.runtime.artifacts.glob("*/request.json"))) == 1


def test_hkm_scene_hash_corruption_keeps_pending_checkpoint_uncertain(tmp_path, monkeypatch):
    engine = make_engine(tmp_path)
    complete = engine.runtime._complete
    monkeypatch.setattr(engine.runtime, "_complete", lambda *args: None)
    job = engine.run(intake(engine))
    assert job.state == JobState.UNKNOWN_OUTCOME, failure_context(engine)
    scene = engine.runtime.command_artifact(job.command_id, "scene.blend")
    assert scene is not None
    original = scene.read_bytes()
    scene.write_bytes(original + b"corrupt")
    monkeypatch.setattr(engine.runtime, "_complete", complete)
    assert engine.reconcile(job.job_id).state == JobState.REQUIRES_INTERVENTION
    assert sum(event.event_type == "PICK_EFFECT" for event in engine.runtime.events()) == 0
    scene.write_bytes(original)
    assert engine.reconcile(job.job_id).state == JobState.COMPLETED
    assert sum(event.event_type == "PICK_EFFECT" for event in engine.runtime.events()) == 1
    assert len(list(engine.runtime.artifacts.glob("*/request.json"))) == 1


def test_hkm_coordinated_exchange_world_tampering_cannot_replace_durable_inventory(
    tmp_path, monkeypatch
):
    engine = make_engine(tmp_path)
    complete = engine.runtime._complete
    monkeypatch.setattr(engine.runtime, "_complete", lambda *args: None)
    job = engine.run(intake(engine))
    assert job.state == JobState.UNKNOWN_OUTCOME, failure_context(engine)
    command = engine.store.load(RobotCommand, job.command_id)
    response_path = engine.runtime.command_artifact(command.command_id, "response.json")
    assert response_path is not None, failure_context(engine)
    request_path = response_path.with_name("request.json")
    request = json.loads(request_path.read_text(encoding="utf-8"))
    response = json.loads(response_path.read_text(encoding="utf-8"))
    durable = engine.runtime.world()
    unrelated_id = engine.settings.products[-1].product_id
    unrelated = next(obj for obj in durable.objects if obj.product.product_id == unrelated_id)
    changed_pose = unrelated.pose.model_dump(mode="json")
    changed_pose["position"][1] += 0.025
    # Corrupt both exchange artifacts consistently, leaving command identity,
    # payload hash, picked product and .blend/hash untouched. A comparison of
    # the response only against request.world would trust this fabricated pose.
    for artifact in (request, response):
        item = next(
            item
            for item in artifact["world"]["objects"]
            if item["product"]["product_id"] == unrelated_id
        )
        item["pose"] = changed_pose
    assert request["command"] == command.model_dump(mode="json")
    assert request["durable_payload_hash"] == response["durable_payload_hash"] == digest(command)
    assert (
        response["scene_sha256"]
        == hashlib.sha256(response_path.with_name("scene.blend").read_bytes()).hexdigest()
    )
    # Ensure this targets the durable-start comparison, not an earlier command
    # or collision rejection caused by the unrelated object's small displacement.
    altered_start = WorldState.model_validate(request["world"])
    assert engine.runtime.rejection_reason(altered_start, command, None) is None
    request_path.write_text(json.dumps(request), encoding="utf-8")
    response_path.write_text(json.dumps(response), encoding="utf-8")
    monkeypatch.setattr(engine.runtime, "_complete", complete)
    assert engine.runtime._complete(command, response_path.parent) is None
    receipt = engine.runtime.journal(command.command_id)
    assert receipt.effect_count == 0 and receipt.status != "SUCCEEDED"
    result = engine.reconcile(job.job_id)
    assert result.state == JobState.REQUIRES_INTERVENTION
    assert result.command_id == command.command_id
    assert engine.runtime.world() == durable
    assert (
        next(
            obj.pose
            for obj in engine.runtime.world().objects
            if obj.product.product_id == unrelated_id
        )
        == unrelated.pose
    )
    assert sum(event.event_type == "PICK_EFFECT" for event in engine.runtime.events()) == 0
    assert sum(event.event_type == "PICK_EFFECT" for event in engine.store.timeline()) == 0
    assert len(list(engine.runtime.artifacts.glob("*/request.json"))) == 1


def test_hkm_blender_capture_has_real_hierarchy_and_calibrated_synthetic_cameras(tmp_path):
    engine = make_engine(tmp_path)
    before = engine.runtime.world()
    assert engine.runtime.capture(tmp_path / "overview.png").read_bytes().startswith(b"\x89PNG")
    scene = next(engine.runtime.artifacts.glob("*/scene.blend"))
    output = tmp_path / "scene-inspection.json"
    script = tmp_path / "inspect_scene.py"
    # This fixed test-only probe inspects a saved artifact. The application still
    # invokes only its checked-in bounded runtime; no user code crosses it.
    script.write_text(
        "import bpy, json, sys\n"
        "from pathlib import Path\n"
        "objects = {}\n"
        "for obj in bpy.data.objects:\n"
        "    objects[obj.name] = {'type': obj.type, 'parent': obj.parent.name if obj.parent else None}\n"
        "    if obj.type == 'CAMERA':\n"
        "        objects[obj.name]['camera'] = {key: obj.get(key) for key in "
        "('sensor_id','frame_id','calibration_version','camera_model_version','role')}\n"
        "    if obj.type == 'FONT':\n"
        "        objects[obj.name]['text'] = obj.data.body\n"
        "Path(sys.argv[sys.argv.index('--') + 1]).write_text(json.dumps(objects), encoding='utf-8')\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            engine.runtime.executable,
            "--background",
            "--disable-autoexec",
            str(scene),
            "--python-exit-code",
            "2",
            "--python",
            str(script),
            "--",
            str(output),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    objects = json.loads(output.read_text(encoding="utf-8"))
    assert objects["Robot/BaseColumn"]["type"] == "MESH"
    assert objects["Robot/RotaryBase"]["parent"] == "Robot/BaseColumn"
    assert objects["Robot/ToolChanger"]["parent"] == "Robot/ToolFlange"
    assert objects["Robot/ParallelLinkLeftUpper"]["parent"] == "Robot/UpperAssembly"
    cameras = [item["camera"] for item in objects.values() if item["type"] == "CAMERA"]
    catalogue = load_catalogue()
    assert len(cameras) == 3
    assert {camera["sensor_id"] for camera in cameras} == {
        spec.sensor_id for spec in catalogue.cameras
    }
    for spec in catalogue.cameras:
        camera = next(item for item in cameras if item["sensor_id"] == spec.sensor_id)
        assert camera["frame_id"] == spec.frame_id
        assert camera["calibration_version"] == spec.calibration_version
        assert camera["camera_model_version"] == spec.camera_model_version
        assert camera["role"] == ("PRESENTATION" if spec.presentation_only else "SYNTHETIC_SENSOR")
    for letter, source in zip("ABCDEF", catalogue.layout.sources.values(), strict=True):
        assert objects[f"Locations/{source.location_id}/Label"]["text"] == letter
    assert engine.runtime.world() == before
    assert engine.runtime.events() == []


@pytest.mark.parametrize(
    "corrupt",
    [
        "hash",
        "epoch",
        "missing_product",
        "source",
        "tool",
        "workspace",
        "trajectory",
        "calibration",
    ],
)
def test_hkm_fixed_blender_process_rejects_broken_request_before_effect(tmp_path, corrupt):
    engine = make_engine(tmp_path)
    job = engine.store.job(intake(engine, 1))
    world = engine.runtime.world()
    observation = ObservationModel(engine.settings).observe(world)
    destination = next(
        location for location in world.locations if location.location_id == job.line.destination_id
    )
    plan = engine.brain.plan(job, observation, destination)
    engine.validator.validate(plan, job, observation, world.cell, destination)
    command = RobotCommand(
        **plan.model_dump(), command_id="defensive-command", required_tool_id=plan.selected_tool_id
    )
    directory = engine.runtime._exchange("pick", world, command)
    request = json.loads((directory / "request.json").read_text(encoding="utf-8"))
    if corrupt == "hash":
        request["durable_payload_hash"] = "0" * 64
    elif corrupt == "epoch":
        request["world"]["scene_epoch"] = "wrong-epoch"
    elif corrupt == "missing_product":
        request["world"]["objects"] = [
            item
            for item in request["world"]["objects"]
            if item["product"]["product_id"] != command.product_id
        ]
    elif corrupt == "source":
        request["command"]["source_id"] = "wrong-source"
    elif corrupt == "tool":
        request["world"]["tool_state"]["rack_tool_ids"].remove(command.required_tool_id)
    elif corrupt == "workspace":
        request["command"]["target_pose"]["position"] = [3, 0, 0.8]
    elif corrupt == "trajectory":
        request["command"]["trajectory"]["waypoints"] = []
    else:
        request["command"]["target_pose"]["calibration_version"] = "stale-calibration"
    if corrupt != "hash":
        request["durable_payload_hash"] = hashlib.sha256(
            json.dumps(request["command"], sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    (directory / "request.json").write_text(json.dumps(request), encoding="utf-8")
    with pytest.raises(CommunicationTimeout, match="BLENDER_PROCESS_FAILED"):
        engine.runtime._invoke(directory)
    assert "ValueError" in (directory / "runtime.log").read_text(encoding="utf-8")
    assert not (directory / "response.json").exists()
    assert not (directory / "motion.json").exists()
    assert not (directory / "scene.blend").exists()
    assert engine.runtime.world() == world
    assert engine.runtime.events() == []
