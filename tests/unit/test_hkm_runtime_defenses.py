"""Exercise the fixed Blender script's independent checks without importing bpy."""

import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from blender.scripts.hkm_runtime import (
    _collision_preflight,
    _frame_world,
    _sample,
    validate_request,
)
from robotops.blender.adapter import BlenderRuntime
from robotops.brain.deterministic import DeterministicBrain
from robotops.cell.hkm_execution import validate_execution
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.domain.models import OrderLine, OrderRequest, RobotCommand, WorldState
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store, digest


def runtime_request(tmp_path, sku="SKU-B", pose_noise_m=0):
    settings = Settings.hkm(pose_noise_m=pose_noise_m)
    runtime = SyntheticRuntime(tmp_path / "runtime.db", settings)
    engine = Engine(Store(tmp_path / "workflow.db"), runtime)
    product = next(p for p in settings.products if p.sku == sku)
    order = engine.store.intake(
        OrderRequest(
            order_id="runtime-order",
            lines=(
                OrderLine(
                    order_line_id="runtime-line",
                    product_id=product.product_id,
                    source_id=settings.source_for(product.product_id),
                    destination_id=settings.destination_id,
                ),
            ),
        ),
        "runtime-key",
    )
    job = engine.store.job(order.job_ids[0])
    observation = engine.observer.observe(runtime.world())
    destination = next(p for p in settings.locations if p.location_id == settings.destination_id)
    plan = DeterministicBrain(settings).plan(job, observation, destination)
    command = RobotCommand(
        **plan.model_dump(), command_id="runtime-command", required_tool_id=plan.selected_tool_id
    )
    return {
        "schema_version": "2.0",
        "operation": "pick",
        "world": runtime.world().model_dump(mode="json"),
        "command": command.model_dump(mode="json"),
        "visual_frame_seconds": 0,
        "durable_payload_hash": digest(command),
    }


@pytest.mark.parametrize("sku", ["SKU-A", "SKU-B", "SKU-C", "SKU-D", "SKU-E", "SKU-F"])
def test_fixed_runtime_independently_accepts_each_valid_preferred_tool_plan(tmp_path, sku):
    request = runtime_request(tmp_path, sku)
    original = copy.deepcopy(request)
    assert validate_request(request)["profile_version"] == "hkm_inspired_v1"
    assert request == original


@pytest.mark.parametrize(
    "path,value,reason",
    [
        (("command", "unexpected_python"), "raise Exception()", "COMMAND_FIELDS"),
        (("command", "scene_epoch"), "different-epoch", "SCENE_OR_CELL"),
        (("command", "command_id"), "../../escape", "IDENTITY"),
        (("command", "product_id"), "missing-product", "SOURCE_PRECONDITION"),
        (("command", "source_id"), "wrong-source", "SOURCE_PRECONDITION"),
        (("command", "robot_profile_version"), "unknown-profile", "VERSION_MISMATCH"),
        (("command", "target_pose", "position"), [2, 0, 0.4], "WORKSPACE"),
        (("command", "target_pose", "position"), [0, 1.1, 0.4], "SLOT_MISMATCH"),
        (("command", "target_pose", "quaternion_xyzw"), [0, 0, 0, 2], "QUATERNION"),
        (("command", "target_pose", "calibration_version"), "stale-cal", "METADATA_MISMATCH"),
        (("command", "trajectory", "calibration_version"), "stale-cal", "TRAJECTORY_VERSION"),
        (("command", "trajectory", "arbitrary_field"), "ignored?", "TRAJECTORY_FIELDS"),
        (("command", "trajectory", "waypoints", 3, "pose", "position"), [2, 0, 1], "WORKSPACE"),
        (
            ("command", "trajectory", "waypoints", 5, "active_tool_id"),
            "EE_VAC_SINGLE",
            "CHANGE_IDENTITY",
        ),
        (
            ("command", "trajectory", "waypoints", 5, "phase"),
            "VERIFY_FLANGE_EMPTY",
            "CHANGE_SEQUENCE",
        ),
        (("command", "trajectory", "waypoints", 1, "sim_time_s"), True, "TRAJECTORY_TIME"),
        (("command", "trajectory", "waypoints", 14, "attached"), True, "ATTACHMENT_OR_TOOL"),
        (("world", "cell", "mode"), "ESTOP", "NOT_READY"),
        (("world", "tool_state", "changer_state"), "FAULTED", "NOT_READY"),
        (("world", "tool_state", "rack_tool_ids"), ["EE_PINCH_NARROW"], "UNAVAILABLE"),
        (("world", "tool_state", "rack_tool_ids"), ["EE_VAC_SINGLE"], "OCCUPANCY"),
        (("visual_frame_seconds",), 1, "PACING"),
    ],
)
def test_fixed_runtime_rejects_unsafe_or_untyped_request_before_effect(
    tmp_path, path, value, reason
):
    request = runtime_request(tmp_path)
    node = request
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    # Rehash to prove the semantic defense is independent of transport integrity.
    request["durable_payload_hash"] = hashlib.sha256(
        json.dumps(request["command"], sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    with pytest.raises(ValueError, match=reason):
        validate_request(request)


def test_fixed_runtime_hash_mismatch_cannot_authorize_modified_command(tmp_path):
    request = runtime_request(tmp_path)
    request["command"]["command_id"] = "replacement-command"
    with pytest.raises(ValueError, match="PAYLOAD_MISMATCH"):
        validate_request(request)


def test_fixed_runtime_nan_waypoint_and_product_pose_are_rejected(tmp_path):
    request = runtime_request(tmp_path)
    request["world"]["objects"][0]["pose"]["position"][0] = float("nan")
    with pytest.raises(ValueError, match="FINITE_VECTOR"):
        validate_request(request)


def test_motion_sampling_is_read_only_smooth_and_preserves_attach_release(tmp_path):
    request = runtime_request(tmp_path)
    original = copy.deepcopy(request)
    data = validate_request(request)
    command = request["command"]
    points = command["trajectory"]["waypoints"]
    for phase, attached in (
        ("GRASP", True),
        ("LIFT", True),
        ("PLACE", True),
        ("RELEASE", False),
        ("HOME", False),
    ):
        point = next(p for p in reversed(points) if p["phase"] == phase)
        world, _ = _frame_world(request["world"], command, data, point["sim_time_s"])
        product = next(
            p for p in world["objects"] if p["product"]["product_id"] == command["product_id"]
        )
        assert product["attached"] is attached
        if phase in {"RELEASE", "HOME"}:
            assert product["pose"] == command["target_pose"]
            assert product["location_id"] == command["destination_id"]
        if attached:
            expected = [
                a + b
                for a, b in zip(
                    point["pose"]["position"],
                    command["trajectory"]["product_attachment_offset_m"],
                    strict=True,
                )
            ]
            assert product["pose"]["position"] == pytest.approx(expected)
    start, end = points[1:3]
    elapsed = end["sim_time_s"] - start["sim_time_s"]
    sample, _ = _sample(points, start["sim_time_s"] + elapsed * 0.25)
    assert sample["pose"]["position"] == pytest.approx(
        [
            a + (b - a) * 0.15625
            for a, b in zip(start["pose"]["position"], end["pose"]["position"], strict=True)
        ]
    )
    assert request == original


def test_fixed_runtime_capture_and_reset_cannot_smuggle_a_pick_command(tmp_path):
    request = runtime_request(tmp_path)
    for operation in ("capture", "reset"):
        request["operation"] = operation
        with pytest.raises(ValueError, match="NON_PICK_CANNOT"):
            validate_request(request)
    request["command"] = request["durable_payload_hash"] = None
    assert validate_request(request)["profile_version"] == "hkm_inspired_v1"


def test_fixed_runtime_rejects_lateral_tool_contact_and_return_into_occupied_dock(tmp_path):
    original = runtime_request(tmp_path)
    for mutation in ("lateral", "returned-tool"):
        request = copy.deepcopy(original)
        points = request["command"]["trajectory"]["waypoints"]
        if mutation == "lateral":
            index = next(
                i for i, point in enumerate(points) if point["phase"] == "ENGAGE_REQUESTED_TOOL"
            )
            points[index - 1]["pose"]["position"][0] += 0.04
        else:
            old_dock = validate_request(original)["layout"]["tool_docks"]["EE_VAC_SINGLE"]
            next(point for point in points if point["phase"] == "PRE_GRASP")["pose"] = old_dock
        request["durable_payload_hash"] = hashlib.sha256(
            json.dumps(request["command"], sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        with pytest.raises(ValueError, match="NO_COLLISION_FREE_SYNTHETIC_TRAJECTORY"):
            validate_request(request)


def test_fixed_runtime_rejects_rotation_sweep_between_clear_endpoint_bounds(tmp_path, monkeypatch):
    request = runtime_request(tmp_path, "SKU-F")
    data = validate_request(request)
    world, command = request["world"], request["command"]
    world["objects"] = [
        p for p in world["objects"] if p["product"]["product_id"] == command["product_id"]
    ]
    world["tool_state"].update(active_tool_id="EE_SUPPORT_FORK", rack_tool_ids=[])
    points = command["trajectory"]["waypoints"]
    for point in points:
        point["pose"]["position"] = [0, 0, 1]
        point["active_tool_id"] = "EE_SUPPORT_FORK"
        point["attached"] = True
    obstacle = {"minimum": [-0.01, 0.22, 0.99], "maximum": [0.01, 0.24, 1.03]}
    monkeypatch.setattr("blender.scripts.hkm_runtime.static_obstacle_bounds", lambda _: [obstacle])
    product = next(p for p in data["products"] if p["sku"] == "SKU-F")
    tools = {p["tool_id"]: p for p in data["tools"]}
    _collision_preflight(world, command, data, product, tools)
    for point in points[len(points) // 2 :]:
        point["pose"]["quaternion_xyzw"] = [0, 0, 1, 0]
    with pytest.raises(ValueError, match="NO_COLLISION_FREE_SYNTHETIC_TRAJECTORY"):
        _collision_preflight(world, command, data, product, tools)


@pytest.mark.parametrize("noise,allowed", [(0.001, True), (0.006, False)])
def test_host_and_fixed_runtime_share_bounded_noisy_grasp_contact(tmp_path, noise, allowed):
    request = runtime_request(tmp_path, pose_noise_m=noise)
    world = WorldState.model_validate(request["world"])
    command = RobotCommand.model_validate(request["command"])
    if not allowed:
        with pytest.raises(ValueError, match="GRASP_SOURCE_PRECONDITION_FAILED"):
            validate_execution(world, command)
        with pytest.raises(ValueError, match="TRAJECTORY_CONTACT_MISMATCH"):
            validate_request(request)
        return
    validate_execution(world, command)
    data = validate_request(request)
    grasp = next(p for p in request["command"]["trajectory"]["waypoints"] if p["phase"] == "GRASP")
    centered, _ = _frame_world(request["world"], request["command"], data, grasp["sim_time_s"])
    before = next(p for p in world.objects if p.product.product_id == command.product_id)
    after = next(p for p in centered["objects"] if p["product"]["product_id"] == command.product_id)
    assert abs(after["pose"]["position"][0] - before.pose.position[0]) == pytest.approx(noise)
    assert after["attached"] is True


def test_fixed_runtime_noisy_contact_does_not_allow_waypoints_to_deviate_from_plan(tmp_path):
    request = runtime_request(tmp_path, pose_noise_m=0.001)
    grasp = next(p for p in request["command"]["trajectory"]["waypoints"] if p["phase"] == "GRASP")
    grasp["pose"]["position"][0] += 1e-7
    request["durable_payload_hash"] = hashlib.sha256(
        json.dumps(request["command"], sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    with pytest.raises(ValueError, match="INVALID_GRASP_WAYPOINT"):
        validate_request(request)


def test_runtime_manifest_covers_fixed_runtime_closure_and_canonical_data(monkeypatch):
    runtime = object.__new__(BlenderRuntime)
    runtime.executable = "fixture-blender"
    monkeypatch.setattr(
        "robotops.blender.adapter.subprocess.run",
        lambda *a, **kw: SimpleNamespace(stdout="Blender fixture\n"),
    )
    manifest = runtime.manifest()
    files = manifest["runtime_files_sha256"]
    assert set(files) == {
        "blender/scripts/runtime.py",
        "blender/scripts/hkm_runtime.py",
        "blender/scripts/hkm_scene.py",
        "robotops/hkm_geometry.py",
        "robotops/scene_geometry.py",
        "robotops/presentation_io.py",
        "robotops/robotics/catalogue_data.py",
        "robotops/robotics/catalogue-v1.json",
    }
    root = Path(__file__).resolve().parents[2]
    for filename, expected in files.items():
        assert hashlib.sha256((root / filename).read_bytes()).hexdigest() == expected
    assert (
        manifest["runtime_closure_sha256"]
        == hashlib.sha256(
            json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
