"""Fixed version-2 HKM-inspired runtime: typed data in, Blender artifacts out.

The pure-data defensive checks deliberately use only the standard library and
canonical catalogue. The host performs its own strict schema/action preflight.
No unrestricted code, MCP, model client or physical robot control exists here.
"""

import copy
import hashlib
import json
import math
import re
import time
from datetime import UTC, datetime
from pathlib import Path

from robotops.hkm_geometry import (
    VISUAL_KINEMATICS_VERSION,
    camera_views,
    rotate_vector,
    scene_primitives,
    static_obstacle_bounds,
)
from robotops.presentation_io import write_snapshot
from robotops.robotics.catalogue_data import SYNTHETIC_GRASP_CONTACT_TOLERANCE_M, raw_catalogue

PICK_PHASES = (
    "PRE_GRASP",
    "APPROACH",
    "GRASP",
    "GRASP_CONFIRM",
    "LIFT",
    "SAFE_TRANSFER",
    "PRE_PLACE",
    "PLACE",
    "RELEASE",
    "RELEASE_CONFIRM",
    "RETRACT",
    "HOME",
)
TOOL_PHASES = {
    "TOOL_CHANGE_REQUESTED",
    "MOVE_TO_SAFE_POSE",
    "MOVE_TO_TOOL_DOCK",
    "RELEASE_CURRENT_TOOL",
    "VERIFY_FLANGE_EMPTY",
    "ENGAGE_REQUESTED_TOOL",
    "VERIFY_TOOL_ID",
    "RETREAT_FROM_TOOL_RACK",
    "TOOL_CHANGE_COMPLETED",
    "TOOL_CHANGE_NOT_REQUIRED",
}
COMMAND_FIELDS = set(
    """schema_version run_id correlation_id causation_id timestamp
action_plan_id job_id order_id order_line_id product_id source_id destination_id
kind target_pose scene_epoch cell_generation observation_id brain_version
selected_tool_id grasp_pose trajectory tool_selection robot_profile_version
product_catalog_version tool_spec_version frame_tree_version command_id required_tool_id""".split()
)
TRAJECTORY_FIELDS = set(
    """schema_version trajectory_id profile required_tool_id grasp_pose
target_tcp_pose product_attachment_offset_m waypoints estimated_sim_duration_s route_index
trajectory_planner_version collision_check_version timing_classification calibration_version
frame_tree_version""".split()
)


def _digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _identifier(value):
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= 160
        or not re.fullmatch(r"[\w.:-]+", value)
    ):
        raise ValueError("INVALID_COMMAND_IDENTITY")


def _vector(value, count=3):
    if (
        not isinstance(value, (list, tuple))
        or len(value) != count
        or not all(
            isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
            for v in value
        )
    ):
        raise ValueError("INVALID_FINITE_VECTOR")
    return value


def _pose(pose, workspace, check_workspace=True):
    if set(pose) - {
        "schema_version",
        "position",
        "quaternion_xyzw",
        "unit",
        "frame_id",
        "calibration_version",
    }:
        raise ValueError("UNKNOWN_POSE_FIELD")
    x, y, z = _vector(pose["position"])
    q = _vector(pose["quaternion_xyzw"], 4)
    if abs(sum(value * value for value in q) - 1) > 1e-6:
        raise ValueError("INVALID_QUATERNION")
    if (
        pose["unit"] != "m"
        or pose["frame_id"] != "cell_world"
        or pose["calibration_version"] != "hkm-cal-1"
    ):
        raise ValueError("SPATIAL_METADATA_MISMATCH")
    if check_workspace and (abs(q[0]) > 1e-9 or abs(q[1]) > 1e-9):
        raise ValueError("SYNTHETIC_PROFILE_REQUIRES_UPRIGHT_TOOL")
    if check_workspace and (
        math.hypot(x, y) > workspace["radial_limit_m"] + 1e-9
        or not workspace["min_z_m"] - 1e-9 <= z <= workspace["max_z_m"] + 1e-9
    ):
        raise ValueError("TCP_OUTSIDE_SYNTHETIC_WORKSPACE")


def _near(a, b):
    return len(a) == len(b) and max(abs(x - y) for x, y in zip(a, b, strict=True)) <= 1e-6


def _same_pose(a, b):
    return _near(a["position"], b["position"]) and _near(a["quaternion_xyzw"], b["quaternion_xyzw"])


def _at_dock(pose, dock):
    # Raw catalogue poses omit the default schema_version; compare all spatial
    # values exactly rather than the incidental serialization of that default.
    return all(
        pose[key] == dock[key]
        for key in ("position", "quaternion_xyzw", "unit", "frame_id", "calibration_version")
    )


def _contact_pose(product_pose, product, tool):
    pose = copy.deepcopy(product_pose)
    offset = product["dimensions_m"][2] / 2
    if tool["family"] == "fork":
        offset = -offset
    elif tool["family"] in {"pinch", "soft"}:
        offset = 0
    pose["position"][2] += offset
    return pose


def _compatible(product, tool):
    if (
        product["compatibility"][tool["tool_id"]] == "N"
        or product["mass_max_kg"] > tool["max_simulated_mass_kg"]
    ):
        return False
    geometry, constraint = product["geometry"], tool["constraints"]
    kind = constraint["kind"]
    if kind == "flat_top":
        return all(
            a >= b
            for a, b in zip(
                sorted(geometry["flat_top_m"]),
                sorted(constraint["minimum_flat_top_m"]),
                strict=True,
            )
        )
    if kind in {"grasp_width", "soft_envelope"}:
        key = "grasp_width_m" if kind == "grasp_width" else "soft_envelope_m"
        return constraint["minimum_width_m"] <= geometry[key] <= constraint["maximum_width_m"]
    return kind == "under_clearance" and geometry["under_clearance"]


def _bounds(product, tool, point, offset):
    q = point["pose"]["quaternion_xyzw"]
    cosine, sine = abs(1 - 2 * q[2] * q[2]), abs(2 * q[2] * q[3])
    tx, ty, tz = tool["collision_envelope_m"]
    cx, cy, cz = rotate_vector(tool.get("collision_offset_m", (0, 0, 0.09)), q)
    x, y = (cosine * tx + sine * ty) / 2, (sine * tx + cosine * ty) / 2
    low, high = [cx - x, cy - y, cz - tz / 2], [cx + x, cy + y, cz + tz / 2]
    if point["attached"]:
        px, py, pz = product["dimensions_m"]
        half = ((cosine * px + sine * py) / 2, (sine * px + cosine * py) / 2, pz / 2)
        for axis in range(3):
            low[axis] = min(low[axis], offset[axis] - half[axis])
            high[axis] = max(high[axis], offset[axis] + half[axis])
    return [value - 0.002 for value in low], [value + 0.002 for value in high]


def _intersects(start, end, minimum, maximum):
    entering, leaving = 0.0, 1.0
    for a, b, low, high in zip(start, end, minimum, maximum, strict=True):
        delta = b - a
        if abs(delta) < 1e-12:
            if a < low or a > high:
                return False
            continue
        one, two = (low - a) / delta, (high - a) / delta
        entering = max(entering, min(one, two))
        leaving = min(leaving, max(one, two))
        if entering > leaving:
            return False
    return True


def _collision_preflight(world, command, data, product, tools):
    obstacles = static_obstacle_bounds(data)
    products = {p["sku"]: p for p in data["products"]}
    for item in world["objects"]:
        if item["product"]["product_id"] == command["product_id"]:
            continue
        dimensions = products[item["product"]["sku"]]["dimensions_m"]
        q = item["pose"]["quaternion_xyzw"]
        rotated_axes = [rotate_vector(axis, q) for axis in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
        half = [
            sum(abs(rotated_axes[j][i]) * dimensions[j] / 2 for j in range(3)) for i in range(3)
        ]
        pos = item["pose"]["position"]
        obstacles.append(
            {
                "minimum": [pos[i] - half[i] for i in range(3)],
                "maximum": [pos[i] + half[i] for i in range(3)],
            }
        )
    trajectory = command["trajectory"]
    occupied = set(world["tool_state"]["rack_tool_ids"])
    released = None
    for start, end in zip(trajectory["waypoints"], trajectory["waypoints"][1:], strict=False):
        bounds = [
            _bounds(
                product,
                tools[p["active_tool_id"]]
                if p["active_tool_id"]
                else {
                    "collision_envelope_m": data["empty_flange_collision_envelope_m"],
                    "collision_offset_m": data["empty_flange_collision_offset_m"],
                },
                p,
                trajectory["product_attachment_offset_m"],
            )
            for p in (start, end)
        ]
        low = [min(b[0][axis] for b in bounds) for axis in range(3)]
        high = [max(b[1][axis] for b in bounds) for axis in range(3)]
        qa, qb = start["pose"]["quaternion_xyzw"], end["pose"]["quaternion_xyzw"]
        if abs(sum(a * b for a, b in zip(qa, qb, strict=True))) < 1 - 1e-12:
            radius = math.hypot(max(abs(low[0]), abs(high[0])), max(abs(low[1]), abs(high[1])))
            low[:2], high[:2] = [-radius, -radius], [radius, radius]
        rack_obstacles = []
        for tool_id in sorted(occupied):
            dock = data["layout"]["tool_docks"][tool_id]
            aligned = all(
                p["pose"]["position"][:2] == dock["position"][:2]
                and p["pose"]["position"][2] >= dock["position"][2] - 1e-9
                and p["pose"]["quaternion_xyzw"] == dock["quaternion_xyzw"]
                for p in (start, end)
            )
            engaging = (
                start["phase"] == "MOVE_TO_TOOL_DOCK"
                and start["active_tool_id"] is None
                and end["phase"] == "ENGAGE_REQUESTED_TOOL"
                and end["active_tool_id"] == tool_id
                and _at_dock(end["pose"], dock)
            )
            uncoupling = (
                tool_id == released
                and start["active_tool_id"] is None
                and end["active_tool_id"] is None
                and _at_dock(start["pose"], dock)
                and (start["phase"], end["phase"])
                in {
                    ("RELEASE_CURRENT_TOOL", "VERIFY_FLANGE_EMPTY"),
                    ("VERIFY_FLANGE_EMPTY", "MOVE_TO_SAFE_POSE"),
                }
            )
            if aligned and (engaging or uncoupling):
                continue
            rack_low, rack_high = _bounds(
                product, tools[tool_id], {"pose": dock, "attached": False}, (0, 0, 0)
            )
            rack_obstacles.append(
                {
                    "minimum": [a + b for a, b in zip(dock["position"], rack_low, strict=True)],
                    "maximum": [a + b for a, b in zip(dock["position"], rack_high, strict=True)],
                }
            )
        for obstacle in obstacles + rack_obstacles:
            minimum = [obstacle["minimum"][axis] - high[axis] for axis in range(3)]
            maximum = [obstacle["maximum"][axis] - low[axis] for axis in range(3)]
            if _intersects(start["pose"]["position"], end["pose"]["position"], minimum, maximum):
                raise ValueError("NO_COLLISION_FREE_SYNTHETIC_TRAJECTORY")
        if start["active_tool_id"] != end["active_tool_id"]:
            if (
                start["active_tool_id"] is not None
                and end["phase"] == "RELEASE_CURRENT_TOOL"
                and end["active_tool_id"] is None
                and _at_dock(end["pose"], data["layout"]["tool_docks"][start["active_tool_id"]])
            ):
                released = start["active_tool_id"]
                occupied.add(released)
            elif (
                end["phase"] == "ENGAGE_REQUESTED_TOOL"
                and start["active_tool_id"] is None
                and end["active_tool_id"] in occupied
                and _at_dock(end["pose"], data["layout"]["tool_docks"][end["active_tool_id"]])
            ):
                occupied.remove(end["active_tool_id"])
                released = None
            else:
                raise ValueError("INVALID_TOOL_TRANSITION")


def validate_request(request):
    """Independently fail closed BEFORE constructing any product-transfer effect."""
    if set(request) != {
        "schema_version",
        "operation",
        "world",
        "command",
        "visual_frame_seconds",
        "durable_payload_hash",
    }:
        raise ValueError("INVALID_RUNTIME_ENVELOPE")
    if request["schema_version"] != "2.0" or request["operation"] not in {
        "reset",
        "capture",
        "pick",
    }:
        raise ValueError("UNSUPPORTED_RUNTIME_VERSION_OR_OPERATION")
    pacing = request["visual_frame_seconds"]
    if (
        isinstance(pacing, bool)
        or not isinstance(pacing, (int, float))
        or not math.isfinite(pacing)
        or not 0 <= pacing <= 0.1
    ):
        raise ValueError("INVALID_VISUAL_PACING")
    data = raw_catalogue()
    world, command = request["world"], request["command"]
    if world["schema_version"] != "2.0" or world["robot_profile_version"] != "hkm_inspired_v1":
        raise ValueError("INVALID_WORLD_PROFILE")
    _identifier(world["scene_epoch"])
    tools = {tool["tool_id"]: tool for tool in data["tools"]}
    products = {p["sku"]: p for p in data["products"]}
    state = world["tool_state"]
    available = set(state["rack_tool_ids"])
    if len(available) != len(state["rack_tool_ids"]) or state["active_tool_id"] in available:
        raise ValueError("INVALID_TOOL_OCCUPANCY")
    if state["active_tool_id"]:
        available.add(state["active_tool_id"])
    if (
        not available <= tools.keys()
        or world["robot_state"]["active_tool_id"] != state["active_tool_id"]
    ):
        raise ValueError("UNKNOWN_OR_CONFLICTING_TOOL_STATE")
    for item in world["objects"]:
        _identifier(item["product"]["product_id"])
        if item["product"]["sku"] not in products:
            raise ValueError("UNKNOWN_PRODUCT_SKU")
        _pose(item["pose"], data["workspace"], False)
    if request["operation"] != "pick":
        if command is not None or request["durable_payload_hash"] is not None:
            raise ValueError("NON_PICK_CANNOT_CARRY_COMMAND")
        return data
    if not isinstance(command, dict) or set(command) != COMMAND_FIELDS:
        raise ValueError("INVALID_COMMAND_FIELDS")
    if (
        command["schema_version"] != "2.0"
        or command["kind"] != "PICK_AND_PLACE"
        or _digest(command) != request["durable_payload_hash"]
    ):
        raise ValueError("DURABLE_COMMAND_PAYLOAD_MISMATCH")
    for field in ("command_id", "job_id", "product_id", "source_id", "destination_id"):
        _identifier(command[field])
    for field, expected_version in (
        ("robot_profile_version", "hkm_inspired_v1"),
        ("product_catalog_version", data["product_catalog_version"]),
        ("tool_spec_version", data["tool_catalog_version"]),
        ("frame_tree_version", data["frame_tree_version"]),
    ):
        if command[field] != expected_version or world[field] != expected_version:
            raise ValueError("COMMAND_WORLD_VERSION_MISMATCH")
    if (
        command["scene_epoch"] != world["scene_epoch"]
        or command["cell_generation"] != world["cell"]["generation"]
    ):
        raise ValueError("COMMAND_SCENE_OR_CELL_MISMATCH")
    if world["cell"]["mode"] not in {"READY", "BUSY"} or state["changer_state"] != "READY":
        raise ValueError("CELL_OR_TOOL_NOT_READY")
    required = command["required_tool_id"]
    if required not in available or required != command["selected_tool_id"]:
        raise ValueError("REQUESTED_TOOL_UNAVAILABLE")
    selected = [
        item for item in world["objects"] if item["product"]["product_id"] == command["product_id"]
    ]
    if (
        len(selected) != 1
        or selected[0]["location_id"] != command["source_id"]
        or selected[0]["attached"]
    ):
        raise ValueError("SOURCE_PRECONDITION_FAILED")
    product, tool = products[selected[0]["product"]["sku"]], tools[required]
    if not _compatible(product, tool):
        raise ValueError("INVALID_PRODUCT_TOOL_PAIR")
    if command["destination_id"] != data["layout"]["destination"]["location_id"]:
        raise ValueError("INVALID_DESTINATION")
    _pose(command["target_pose"], data["workspace"])
    expected = list(data["layout"]["destination"]["pose"]["position"])
    slot = data["layout"]["destination_slots"][product["sku"]]
    expected = [a + b for a, b in zip(expected, slot, strict=True)]
    expected[2] += product["dimensions_m"][2] / 2
    if not _near(expected, command["target_pose"]["position"]):
        raise ValueError("DESTINATION_SLOT_MISMATCH")
    trajectory = command["trajectory"]
    if not isinstance(trajectory, dict) or set(trajectory) != TRAJECTORY_FIELDS:
        raise ValueError("INVALID_TRAJECTORY_FIELDS")
    if (
        trajectory["schema_version"] != "2.0"
        or trajectory["calibration_version"] != "hkm-cal-1"
        or trajectory["frame_tree_version"] != data["frame_tree_version"]
        or trajectory["trajectory_planner_version"] != "synthetic-trajectory-1"
        or trajectory["collision_check_version"] != "synthetic-aabb-preflight-1"
        or trajectory["timing_classification"] != "SIMULATOR_PRESENTATION_TIMING"
    ):
        raise ValueError("TRAJECTORY_VERSION_MISMATCH")
    points = trajectory["waypoints"]
    if (
        trajectory["profile"] != "SAFE_PICK_PLACE_V1"
        or trajectory["required_tool_id"] != required
        or not 14 <= len(points) <= 128
    ):
        raise ValueError("INVALID_TRAJECTORY_STRUCTURE")
    actual_grasp = _contact_pose(selected[0]["pose"], product, tool)
    expected_grasp = trajectory["grasp_pose"]
    _pose(expected_grasp, data["workspace"])
    expected_place = _contact_pose(command["target_pose"], product, tool)
    if (
        command["grasp_pose"] != expected_grasp
        or math.dist(actual_grasp["position"], expected_grasp["position"])
        > SYNTHETIC_GRASP_CONTACT_TOLERANCE_M
        or actual_grasp["quaternion_xyzw"] != expected_grasp["quaternion_xyzw"]
        or not _same_pose(trajectory["target_tcp_pose"], expected_place)
    ):
        raise ValueError("TRAJECTORY_CONTACT_MISMATCH")
    offset = _vector(trajectory["product_attachment_offset_m"])
    if not _near(
        offset,
        [
            a - b
            for a, b in zip(selected[0]["pose"]["position"], actual_grasp["position"], strict=True)
        ],
    ):
        raise ValueError("INVALID_ATTACHMENT_OFFSET")
    phases = [p["phase"] for p in points]
    if (
        phases[0] != "HOME"
        or phases[-1] != "HOME"
        or not set(phases) <= set(PICK_PHASES) | TOOL_PHASES
    ):
        raise ValueError("INVALID_TRAJECTORY_PHASE")
    cursor = 0
    for phase in PICK_PHASES:
        if phase not in phases[cursor:]:
            raise ValueError("MISSING_TRAJECTORY_PHASE")
        cursor = phases.index(phase, cursor) + 1
        if phase not in {"HOME", "SAFE_TRANSFER"} and phases.count(phase) != 1:
            raise ValueError("DUPLICATE_PICK_PHASE")
    grasp, release, pick_start = (
        phases.index("GRASP"),
        phases.index("RELEASE"),
        phases.index("PRE_GRASP"),
    )
    _validate_tool_change(points[:pick_start], state["active_tool_id"], required, data)
    previous = -1
    for index, point in enumerate(points):
        if (
            set(point)
            != {"schema_version", "phase", "pose", "sim_time_s", "attached", "active_tool_id"}
            or point["schema_version"] != "2.0"
            or not isinstance(point["attached"], bool)
        ):
            raise ValueError("INVALID_WAYPOINT_FIELDS")
        _pose(point["pose"], data["workspace"])
        now = point["sim_time_s"]
        if (
            isinstance(now, bool)
            or not isinstance(now, (int, float))
            or not math.isfinite(now)
            or now <= previous
        ):
            raise ValueError("INVALID_TRAJECTORY_TIME")
        previous = now
        if point["active_tool_id"] is not None and point["active_tool_id"] not in available:
            raise ValueError("TRAJECTORY_TOOL_UNAVAILABLE")
        if (
            point["attached"] != (grasp <= index < release)
            or index >= pick_start
            and point["active_tool_id"] != required
        ):
            raise ValueError("INVALID_TRAJECTORY_ATTACHMENT_OR_TOOL")
        if (
            point["phase"] in {"APPROACH", "GRASP", "GRASP_CONFIRM"}
            and point["pose"] != expected_grasp
        ):
            raise ValueError("INVALID_GRASP_WAYPOINT")
        if point["phase"] in {"PLACE", "RELEASE", "RELEASE_CONFIRM"} and not _same_pose(
            point["pose"], expected_place
        ):
            raise ValueError("INVALID_PLACE_WAYPOINT")
        if (
            point["phase"] == "SAFE_TRANSFER"
            and point["pose"]["position"][2] < data["workspace"]["safe_transfer_z_m"]
        ):
            raise ValueError("TRANSFER_BELOW_SAFE_PLANE")
    if (
        points[0]["sim_time_s"] != 0
        or not 0 < previous <= 29.9
        or abs(previous - trajectory["estimated_sim_duration_s"]) > 1e-6
    ):
        raise ValueError("INVALID_TRAJECTORY_DURATION")
    if (
        not _same_pose(points[0]["pose"], world["robot_state"]["tcp_pose"])
        or points[0]["active_tool_id"] != state["active_tool_id"]
    ):
        raise ValueError("INITIAL_MACHINE_STATE_MISMATCH")
    _collision_preflight(world, command, data, product, tools)
    return data


def _validate_tool_change(points, current, required, data):
    phases = [p["phase"] for p in points]
    if current == required:
        if phases != ["HOME", "TOOL_CHANGE_NOT_REQUIRED"] or any(
            p["active_tool_id"] != current for p in points
        ):
            raise ValueError("INVALID_UNNECESSARY_TOOL_CHANGE")
        return
    expected = [
        "HOME",
        "TOOL_CHANGE_REQUESTED",
        "MOVE_TO_SAFE_POSE",
        "MOVE_TO_TOOL_DOCK",
        "MOVE_TO_TOOL_DOCK",
        "RELEASE_CURRENT_TOOL",
        "VERIFY_FLANGE_EMPTY",
        "MOVE_TO_SAFE_POSE",
        "MOVE_TO_TOOL_DOCK",
        "ENGAGE_REQUESTED_TOOL",
        "VERIFY_TOOL_ID",
        "RETREAT_FROM_TOOL_RACK",
        "TOOL_CHANGE_COMPLETED",
    ]
    if phases != expected:
        raise ValueError("INVALID_TOOL_CHANGE_SEQUENCE")
    for index, point in enumerate(points):
        active = current if index < 5 else None if index < 9 else required
        if point["active_tool_id"] != active:
            raise ValueError("INVALID_TOOL_CHANGE_IDENTITY")
    old = data["layout"]["tool_docks"][current] if current else copy.deepcopy(points[0]["pose"])
    if current is None:
        old["position"][2] = data["workspace"]["safe_transfer_z_m"]
    new = data["layout"]["tool_docks"][required]
    if not all(_same_pose(points[index]["pose"], old) for index in (4, 5, 6)) or not all(
        _same_pose(points[index]["pose"], new) for index in (9, 10)
    ):
        raise ValueError("INVALID_TOOL_DOCK_CONTACT")


def _sample(points, sim_time):
    if sim_time >= points[-1]["sim_time_s"]:
        return copy.deepcopy(points[-1]), points[-1]["phase"]
    for start, end in zip(points, points[1:], strict=False):
        if start["sim_time_s"] <= sim_time < end["sim_time_s"]:
            fraction = (sim_time - start["sim_time_s"]) / (end["sim_time_s"] - start["sim_time_s"])
            amount = fraction * fraction * (3 - 2 * fraction)
            sample = copy.deepcopy(start)
            sample["pose"]["position"] = [
                a + (b - a) * amount
                for a, b in zip(start["pose"]["position"], end["pose"]["position"], strict=True)
            ]
            a, b = start["pose"]["quaternion_xyzw"], end["pose"]["quaternion_xyzw"]
            if sum(x * y for x, y in zip(a, b, strict=True)) < 0:
                b = [-v for v in b]
            q = [x + (y - x) * amount for x, y in zip(a, b, strict=True)]
            length = math.sqrt(sum(v * v for v in q))
            sample["pose"]["quaternion_xyzw"] = [v / length for v in q]
            return sample, end["phase"]
    raise ValueError("TIME_OUTSIDE_TRAJECTORY")


def _frame_world(original, command, data, sim_time):
    world = copy.deepcopy(original)
    trajectory = command["trajectory"]
    point, phase = _sample(trajectory["waypoints"], sim_time)
    active = point["active_tool_id"]
    available = set(original["tool_state"]["rack_tool_ids"])
    if original["tool_state"]["active_tool_id"]:
        available.add(original["tool_state"]["active_tool_id"])
    rack = [
        t["tool_id"] for t in data["tools"] if t["tool_id"] in available and t["tool_id"] != active
    ]
    world["tool_state"].update(
        active_tool_id=active,
        rack_tool_ids=rack,
        changer_state="CHANGING" if phase in TOOL_PHASES else "READY",
    )
    world["robot_state"].update(tcp_pose=point["pose"], active_tool_id=active, motion_phase=phase)
    product = next(
        item for item in world["objects"] if item["product"]["product_id"] == command["product_id"]
    )
    spec = next(p for p in data["products"] if p["sku"] == product["product"]["sku"])
    world["tool_state"]["grasp_width_m"] = spec["geometry"]["grasp_width_m"]
    world["tool_state"]["grip_amount"] = 1.0 if point["attached"] else 0.0
    release_time = next(p["sim_time_s"] for p in trajectory["waypoints"] if p["phase"] == "RELEASE")
    if point["attached"]:
        # This bounded synthetic grasp centers the product on the commanded
        # contact by at most the shared 5 mm tolerance. It is authored grasp
        # behavior, not pixel inference, calibrated compliance or robot physics.
        product["pose"] = copy.deepcopy(point["pose"])
        offset = rotate_vector(
            trajectory["product_attachment_offset_m"], point["pose"]["quaternion_xyzw"]
        )
        product["pose"]["position"] = [
            a + b for a, b in zip(point["pose"]["position"], offset, strict=True)
        ]
    elif sim_time >= release_time:
        product["pose"] = copy.deepcopy(command["target_pose"])
        product["location_id"] = command["destination_id"]
    product["attached"] = point["attached"]
    return world, phase


def _recording_header(command, world, objects, total_frames):
    return {
        "schema_version": "2.0",
        "source": "BLENDER_EVALUATED_SCENE",
        "command_id": command["command_id"],
        "job_id": command["job_id"],
        "scene_epoch": command["scene_epoch"],
        "product_id": command["product_id"],
        "frame_id": "cell_world",
        "unit": "m",
        "fps": 24,
        "total_frames": total_frames,
        "complete": False,
        "objects": objects,
        "frames": [],
        "robot_profile_version": "hkm_inspired_v1",
        "kinematics_version": VISUAL_KINEMATICS_VERSION,
        "calibration_version": "hkm-cal-1",
        "frame_tree_version": world["frame_tree_version"],
        "simulated_duration_s": command["trajectory"]["estimated_sim_duration_s"],
    }


def _append_frame(recording, primitives, metadata):
    moving = [p for p in primitives if "dynamic" in p["semantic_tags"]]
    recording["frames"].append(
        {
            "schema_version": "2.0",
            **metadata,
            "positions": {p["name"]: p["position"] for p in moving},
            "transforms": {
                p["name"]: {
                    "schema_version": "2.0",
                    **{key: p[key] for key in ("position", "quaternion_xyzw", "scale", "visible")},
                }
                for p in moving
            },
        }
    )
    recording["complete"] = len(recording["frames"]) == recording["total_frames"]


def _animate(directory, world, command, data, pacing):
    import bpy

    from blender.scripts.hkm_scene import bake_frame, sampled_primitives

    duration = command["trajectory"]["estimated_sim_duration_s"]
    total = math.ceil(duration * 24) + 1
    recording = _recording_header(command, world, sampled_primitives(), total)
    metadata = []
    start = time.monotonic()
    final = None
    for frame in range(1, total + 1):
        sim_time = min((frame - 1) / 24, duration)
        sample, phase = _frame_world(world, command, data, sim_time)
        bake_frame(frame, scene_primitives(sample, data))
        entry = {
            "frame": frame,
            "phase": phase,
            "sim_time_s": sim_time,
            "active_tool_id": sample["tool_state"]["active_tool_id"],
            "rack_tool_ids": sample["tool_state"]["rack_tool_ids"],
            "attached_product_id": command["product_id"]
            if next(
                item
                for item in sample["objects"]
                if item["product"]["product_id"] == command["product_id"]
            )["attached"]
            else None,
        }
        metadata.append(entry)
        _append_frame(recording, sampled_primitives(), entry)
        if frame == 1 or frame % 12 == 0 or frame == total:
            write_snapshot(directory / "motion.json", recording)
        if pacing:
            time.sleep(max(0, start + frame * pacing - time.monotonic()))
        final = sample
    bpy.context.scene["motion_frame_metadata"] = json.dumps(metadata, separators=(",", ":"))
    bpy.context.scene.frame_end = total
    bpy.context.scene.frame_set(total)
    final["tool_state"].pop("grasp_width_m")
    final["tool_state"].pop("grip_amount")
    final["tool_state"]["changer_state"] = "READY"
    final["robot_state"]["motion_phase"] = "HOME"
    final["step"] += 1
    final["timestamp"] = datetime.now(UTC).isoformat()
    # The saved physical world is read from Blender's evaluated product roots.
    for item in final["objects"]:
        obj = bpy.data.objects["Products/" + item["product"]["product_id"]]
        position, rotation, _ = obj.matrix_world.decompose()
        item["pose"]["position"] = list(position)
        item["pose"]["quaternion_xyzw"] = [rotation.x, rotation.y, rotation.z, rotation.w]
        obj["location_id"] = item["location_id"]
    return final


def _render_settings():
    import bpy

    for name, location, energy, size in (
        ("Lighting/Key", (0, -2, 4), 650, 5),
        ("Lighting/Rim", (-2, 2, 3), 400, 3),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.size = size
    scene = bpy.context.scene
    scene.world.color = (0.09, 0.11, 0.14)
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16
    scene.render.resolution_x = 800
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.fps = 24


def run(directory: Path, record_existing: bool = False):
    import bpy

    from blender.scripts.hkm_scene import build_scene, sampled_primitives

    request = json.loads((directory / "request.json").read_text(encoding="utf-8"))
    started = time.monotonic()

    def progress(stage):
        print(
            json.dumps(
                {
                    "component": "bounded_blender_runtime",
                    "stage": stage,
                    "command_id": (request["command"] or {}).get("command_id"),
                    "timestamp_utc": datetime.now(UTC).isoformat(),
                    "elapsed_s": round(time.monotonic() - started, 3),
                }
            ),
            flush=True,
        )

    progress("VALIDATING_REQUEST")
    data = validate_request(request)
    command, world = request["command"], copy.deepcopy(request["world"])
    if record_existing:
        response = json.loads((directory / "response.json").read_text(encoding="utf-8"))
        if (
            request["operation"] != "pick"
            or response["command_id"] != command["command_id"]
            or response["durable_payload_hash"] != request["durable_payload_hash"]
            or response["scene_sha256"]
            != hashlib.sha256((directory / "scene.blend").read_bytes()).hexdigest()
        ):
            raise ValueError("INVALID_SAVED_SCENE")
        bpy.ops.wm.open_mainfile(filepath=str(directory / "scene.blend"), use_scripts=False)
        metadata = json.loads(bpy.context.scene["motion_frame_metadata"])
        if not 1 <= len(metadata) <= 720:
            raise ValueError("INVALID_SAVED_MOTION_LENGTH")
        bpy.context.scene.frame_set(1)
        recording = _recording_header(command, world, sampled_primitives(), len(metadata))
        for entry in metadata:
            bpy.context.scene.frame_set(entry["frame"])
            _append_frame(recording, sampled_primitives(), entry)
        write_snapshot(directory / "motion.json", recording)
        progress("READ_ONLY_EXPORT_COMPLETED")
        return
    build_scene(scene_primitives(world, data), camera_views(data))
    _render_settings()
    progress("SCENE_CREATED")
    if request["operation"] == "pick":
        world = _animate(directory, world, command, data, request["visual_frame_seconds"])
        progress("ANIMATION_RECORDED")
    bpy.ops.wm.save_as_mainfile(filepath=str(directory / "scene.blend"))
    progress("SCENE_SAVED")
    bpy.context.scene.render.filepath = str(directory / "capture.png")
    progress("RENDER_STARTED")
    bpy.ops.render.render(write_still=True)
    progress("RENDER_COMPLETED")
    response = {
        "schema_version": "2.0",
        "world": world,
        "command_id": command["command_id"] if command else None,
        "effect_count": 1 if command else 0,
        "steps": [point["phase"] for point in command["trajectory"]["waypoints"]]
        if command
        else [],
        "blender_version": bpy.app.version_string,
        "runtime_profile_version": "hkm_inspired_v1",
        "durable_payload_hash": request["durable_payload_hash"],
        "scene_sha256": hashlib.sha256((directory / "scene.blend").read_bytes()).hexdigest(),
        "motion_sha256": hashlib.sha256((directory / "motion.json").read_bytes()).hexdigest()
        if command
        else None,
        "object_names": sorted(obj.name for obj in bpy.data.objects),
    }
    temporary = directory / "response.tmp"
    temporary.write_text(json.dumps(response, indent=2) + "\n", encoding="utf-8")
    temporary.replace(directory / "response.json")
    progress("RESPONSE_DURABLE")
