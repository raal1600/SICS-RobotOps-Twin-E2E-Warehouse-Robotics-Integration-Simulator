"""Inspect geometry numerically, without treating presentation as sensor evidence."""

import copy
import math

import pytest

from robotops.hkm_geometry import (
    FLANGE_TO_TCP_M,
    LINK_LENGTH_M,
    camera_quaternion,
    camera_views,
    linkage_points,
    primitive_bounds,
    robot_primitives,
    scene_primitives,
    static_obstacle_bounds,
    tool_primitives,
)
from robotops.robotics.catalogue_data import raw_catalogue
from robotops.scene_geometry import cell_meshes


def fixture_world():
    data = raw_catalogue()
    world = {
        "profile_version": "hkm_inspired_v1",
        "cell": {"mode": "READY"},
        "robot_state": {"tcp_pose": data["layout"]["home_tcp_pose"]},
        "tool_state": {
            "active_tool_id": data["tools"][0]["tool_id"],
            "rack_tool_ids": [tool["tool_id"] for tool in data["tools"][1:]],
        },
        "objects": [],
    }
    for spec in data["products"]:
        source = data["layout"]["sources"][spec["sku"]]
        pose = copy.deepcopy(source["pose"])
        pose["position"][2] += spec["dimensions_m"][2] / 2 + source.get(
            "product_support_offset_m", 0
        )
        world["objects"].append(
            {
                "product": {"product_id": "product-" + spec["sku"] + "-01", "sku": spec["sku"]},
                "location_id": source["location_id"],
                "pose": pose,
            }
        )
    return world


def rotate(vector, quaternion):
    """Independent quaternion rotation oracle for the displayed beam endpoints."""
    x, y, z, w = quaternion
    vx, vy, vz = vector
    return (
        (1 - 2 * (y * y + z * z)) * vx + 2 * (x * y - z * w) * vy + 2 * (x * z + y * w) * vz,
        2 * (x * y + z * w) * vx + (1 - 2 * (x * x + z * z)) * vy + 2 * (y * z - x * w) * vz,
        2 * (x * z - y * w) * vx + 2 * (y * z + x * w) * vy + (1 - 2 * (x * x + y * y)) * vz,
    )


def test_hkm_scene_is_deterministic_typed_and_has_complete_hierarchy():
    world = fixture_world()
    original = copy.deepcopy(world)
    parts = scene_primitives(world)
    assert parts == scene_primitives(world)
    assert world == original
    names = {part["name"] for part in parts}
    assert len(names) == len(parts) < 512
    assert {
        "Robot/BaseColumn",
        "Robot/RotaryBase",
        "Robot/UpperAssembly",
        "Robot/WristAssembly",
        "Robot/ToolFlange",
        "Robot/ToolChanger",
        "Conveyor",
        "ControlCabinet/LogicalEstop",
        "Enclosure/OperatorGate",
    } <= names
    for part in parts:
        assert part["schema_version"] == "2.0"
        assert part["primitive"] in {"box", "cylinder"}
        assert part["parent_name"] is None or part["parent_name"] in names
        assert part["parent_name"] != part["name"]
        assert all(
            math.isfinite(value)
            for field in ("position", "size", "quaternion_xyzw", "scale")
            for value in part[field]
        )
        assert all(value > 0 for value in part["size"])
        assert sum(value**2 for value in part["quaternion_xyzw"]) == pytest.approx(1)
        assert 0 <= part["opacity"] <= 1
        visited = {part["name"]}
        parent = part["parent_name"]
        by_name = {item["name"]: item for item in parts}
        while parent:
            assert parent not in visited
            visited.add(parent)
            parent = by_name[parent]["parent_name"]


@pytest.mark.parametrize(
    "radius,z",
    [(0, 0.16), (0, 1.02), (0, 1.15), (0.6, 0.16), (0.6, 1.15), (1.55, 0.16), (1.55, 1.15)],
)
@pytest.mark.parametrize("angle", [0, 1.1, -2.4])
def test_hkm_link_endpoints_remain_connected_and_lengths_constant(radius, z, angle):
    tcp = (radius * math.cos(angle), radius * math.sin(angle), z)
    anchors = linkage_points(tcp)
    parts = {item["name"]: item for item in robot_primitives(tcp)}
    for side in ("Left", "Right"):
        for segment, first, last in (("Upper", "Shoulder", "Elbow"), ("Lower", "Elbow", "Wrist")):
            beam = parts[f"Robot/ParallelLink{side}{segment}"]
            assert beam["size"][2] == pytest.approx(LINK_LENGTH_M)
            delta = rotate((0, 0, beam["size"][2] / 2), beam["quaternion_xyzw"])
            start = tuple(a - b for a, b in zip(beam["position"], delta, strict=True))
            end = tuple(a + b for a, b in zip(beam["position"], delta, strict=True))
            assert start == pytest.approx(anchors[side + first])
            assert end == pytest.approx(anchors[side + last])
    middle = tuple(
        (a + b) / 2 for a, b in zip(anchors["LeftWrist"], anchors["RightWrist"], strict=True)
    )
    assert middle == pytest.approx((tcp[0], tcp[1], tcp[2] + FLANGE_TO_TCP_M))


def test_hkm_link_orientation_changes_with_tcp_and_invalid_pose_is_rejected():
    start = {p["name"]: p for p in robot_primitives((0, -0.6, 1.02))}
    end = {p["name"]: p for p in robot_primitives((1.08, -0.68, 0.4))}
    for side in ("Left", "Right"):
        for segment in ("Upper", "Lower"):
            name = f"Robot/ParallelLink{side}{segment}"
            assert start[name]["quaternion_xyzw"] != end[name]["quaternion_xyzw"]
    for invalid in ((math.nan, 0, 0.5), (0, math.inf, 0.5), (5, 0, 0.5)):
        with pytest.raises(ValueError):
            robot_primitives(invalid)


def test_hkm_six_sources_products_and_tools_derive_from_catalogue():
    data, world = raw_catalogue(), fixture_world()
    parts = {item["name"]: item for item in scene_primitives(world)}
    assert [
        parts["Locations/" + source["location_id"]]["label"]
        for source in data["layout"]["sources"].values()
    ] == list("ABCDEF")
    for item, spec in zip(world["objects"], data["products"], strict=True):
        product = parts["Products/" + item["product"]["product_id"]]
        assert product["size"] == tuple(spec["dimensions_m"])
        assert product["position"] == tuple(item["pose"]["position"])
        assert product["product_id"] == item["product"]["product_id"]
    roots = [parts["Tools/" + tool["tool_id"]] for tool in data["tools"]]
    assert len(roots) == 6
    assert sum(tool["parent_name"] == "Robot/ToolChanger" for tool in roots) == 1
    assert sum(tool["parent_name"].startswith("ToolRack/Dock") for tool in roots) == 5
    assert all(tool["visible"] for tool in roots)
    changed_catalogue = copy.deepcopy(data)
    changed_catalogue["products"][0]["dimensions_m"][0] += 0.01
    altered = {item["name"]: item for item in scene_primitives(world, changed_catalogue)}
    assert altered["Products/product-SKU-A-01"]["size"][0] == pytest.approx(0.13)


@pytest.mark.parametrize("tool_id", [tool["tool_id"] for tool in raw_catalogue()["tools"]])
def test_hkm_tool_switch_preserves_identity_and_rack_occupancy(tool_id):
    world = fixture_world()
    ids = [tool["tool_id"] for tool in raw_catalogue()["tools"]]
    original_names = {item["name"] for item in scene_primitives(world)}
    world["tool_state"] = {
        "active_tool_id": tool_id,
        "rack_tool_ids": [i for i in ids if i != tool_id],
    }
    parts = scene_primitives(world)
    assert {item["name"] for item in parts} == original_names
    mounted = [part for part in parts if part["parent_name"] == "Robot/ToolChanger"]
    assert [part["tool_id"] for part in mounted] == [tool_id]
    assert mounted[0]["position"] == pytest.approx((0, -0.6, 1.115))
    assert all(p["visible"] for p in parts if "tool" in p["semantic_tags"])


def test_hkm_tool_absence_and_gripper_closing_are_presented_without_new_assets():
    world = fixture_world()
    world["tool_state"]["active_tool_id"] = None
    world["tool_state"]["rack_tool_ids"] = ["EE_VAC_SINGLE"]
    parts = scene_primitives(world)
    assert not [part for part in parts if part["parent_name"] == "Robot/ToolChanger"]
    assert {part["tool_id"] for part in parts if part.get("tool_id") and part["visible"]} == {
        "EE_VAC_SINGLE"
    }
    open_gripper = tool_primitives("EE_PINCH_WIDE", (0, 0, 0.6), grip_amount=0)
    closed = tool_primitives("EE_PINCH_WIDE", (0, 0, 0.6), grasp_width_m=0.09, grip_amount=1)
    assert [part["name"] for part in open_gripper] == [part["name"] for part in closed]
    before = next(p for p in open_gripper if p["name"].endswith("RightJaw"))
    after = next(p for p in closed if p["name"].endswith("RightJaw"))
    assert after["position"][0] < before["position"][0]
    with pytest.raises(ValueError, match="UNKNOWN_VISUAL_TOOL"):
        tool_primitives("arbitrary-tool", (0, 0, 0.6))


def test_hkm_camera_views_are_distinct_and_sensor_metadata_is_preserved():
    cameras = camera_views()
    assert [camera["name"] for camera in cameras] == [
        "Camera/OperatorOverview",
        "Camera/OverheadObservation",
        "Camera/SideInspection",
    ]
    assert len({tuple(camera["position"]) for camera in cameras}) == 3
    assert sum(camera["role"] == "SYNTHETIC_SENSOR" for camera in cameras) == 2
    for camera, spec in zip(cameras, raw_catalogue()["cameras"], strict=True):
        for key in ("sensor_id", "frame_id", "calibration_version", "camera_model_version"):
            assert camera[key] == spec[key]


def test_hkm_camera_calibration_orientation_matches_actual_blender_view_direction():
    for camera, spec in zip(camera_views(), raw_catalogue()["cameras"], strict=True):
        expected = camera_quaternion(camera["position"], camera["target"])
        assert spec["pose"]["quaternion_xyzw"] == pytest.approx(expected, abs=1e-12)
        forward = rotate((0, 0, -1), expected)
        direction = [b - a for a, b in zip(camera["position"], camera["target"], strict=True)]
        length = math.sqrt(sum(value * value for value in direction))
        assert forward == pytest.approx([v / length for v in direction], abs=1e-12)


def test_collision_obstacles_derive_from_visible_geometry_and_open_front_lips():
    parts = {p["name"].replace("/", ":"): p for p in scene_primitives(fixture_world())}
    obstacles = static_obstacle_bounds()
    assert obstacles
    for obstacle in obstacles:
        assert obstacle["obstacle_id"] in parts
        expected = primitive_bounds(parts[obstacle["obstacle_id"]])
        assert obstacle["minimum"] == pytest.approx(expected[0])
        assert obstacle["maximum"] == pytest.approx(expected[1])
    for source in raw_catalogue()["layout"]["sources"].values():
        name = "Locations:" + source["location_id"]
        assert parts[name + ":FrontWall"]["size"][2] == 0.03
        assert parts[name + ":RightWall"]["size"][2] == 0.05
        assert parts[name + ":BackWall"]["size"][2] == source["wall_height_m"]


@pytest.mark.parametrize("tool", raw_catalogue()["tools"], ids=lambda tool: tool["tool_id"])
def test_every_tool_mesh_fits_its_canonical_collision_envelope(tool):
    offset = tool["collision_offset_m"]
    low = [offset[i] - tool["collision_envelope_m"][i] / 2 for i in range(3)]
    high = [offset[i] + tool["collision_envelope_m"][i] / 2 for i in range(3)]
    for part in tool_primitives(tool["tool_id"], (0, 0, 0)):
        mesh_low, mesh_high = primitive_bounds(part)
        assert all(mesh_low[i] >= low[i] - 1e-9 for i in range(3)), part["name"]
        assert all(mesh_high[i] <= high[i] + 1e-9 for i in range(3)), part["name"]


def test_hkm_does_not_replace_legacy_cartesian_geometry():
    legacy = {
        "locations": [
            {"location_id": "SOURCE", "pose": {"position": [-0.5, 0, 0.1]}},
            {"location_id": "DEST", "pose": {"position": [0.5, 0, 0.1]}},
        ],
        "objects": [
            {
                "product": {"product_id": "red"},
                "location_id": "SOURCE",
                "pose": {"position": [-0.5, 0, 0.2]},
            }
        ],
    }
    names = {item["name"] for item in cell_meshes(legacy)}
    assert {"RobotCrossrail", "RobotCarriage", "RobotSpindle", "Gripper", "Products/red"} <= names
    assert "Robot/RotaryBase" not in names
