import ast
from math import isclose, sqrt
from pathlib import Path

import pytest

from robotops.domain.base import Pose
from robotops.robotics.catalogue import (
    RoboticsCatalogue,
    fixture_source_pose,
    fixture_target_pose,
    initial_tool_state,
    load_catalogue,
    product_spec,
    tool_spec,
)
from robotops.robotics.models import CollisionObstacle, ToolState, WorkspaceProfile
from robotops.robotics.selector import ToolSelectionError, evaluate_candidate, select_tool
from robotops.robotics.trajectory import (
    REQUIRED_PICK_PHASES,
    collision_free,
    default_obstacles,
    grasp_pose,
    plan_trajectory,
    product_obstacles,
    segment_intersects_aabb,
    segment_samples,
    smoothstep,
    validate_trajectory,
    validate_workspace,
)


@pytest.mark.parametrize(
    "sku,expected",
    [
        ("SKU-A", "EE_VAC_SINGLE"),
        ("SKU-B", "EE_VAC_ARRAY"),
        ("SKU-C", "EE_ADAPTIVE_SOFT"),
        ("SKU-D", "EE_PINCH_NARROW"),
        ("SKU-E", "EE_PINCH_WIDE"),
        ("SKU-F", "EE_SUPPORT_FORK"),
    ],
)
def test_hkm_preferred_tools_and_reasoning_are_deterministic(sku, expected):
    product = product_spec(sku)
    first = select_tool(product, initial_tool_state())
    second = select_tool(product, initial_tool_state())
    assert first == second
    assert first.selected_tool_id == expected
    winner = next(candidate for candidate in first.candidate_tools if candidate.tool_id == expected)
    assert winner.eligible and "PREFERRED_FOR_PRODUCT_FAMILY" in winner.reasons
    assert "MASS_WITHIN_SIMULATED_LIMIT" in winner.reasons
    assert "SYNTHETIC_GEOMETRY_COMPATIBLE" in winner.reasons
    assert first.assessed_mass_kg == product.mass_max_kg


def test_hkm_candidate_mass_geometry_and_availability_are_independent_constraints():
    state = initial_tool_state()
    small = product_spec("SKU-A")
    too_heavy = evaluate_candidate(small, tool_spec("EE_VAC_SINGLE"), state, 0.81)
    assert not too_heavy.eligible
    assert "SIMULATED_MASS_LIMIT_EXCEEDED" in too_heavy.reasons
    tiny_surface = small.model_copy(
        update={"geometry": small.geometry.model_copy(update={"flat_top_m": (0.01, 0.01)})}
    )
    bad_geometry = evaluate_candidate(tiny_surface, tool_spec("EE_VAC_SINGLE"), state, 0.4)
    assert not bad_geometry.eligible
    assert "INSUFFICIENT_PLANAR_TOP_SURFACE" in bad_geometry.reasons
    absent = ToolState(active_tool_id=None, rack_tool_ids=())
    with pytest.raises(ToolSelectionError, match="NO_COMPATIBLE_AVAILABLE_TOOL") as caught:
        select_tool(small, absent)
    assert len(caught.value.candidates) == 6
    assert all("TOOL_UNAVAILABLE" in candidate.reasons for candidate in caught.value.candidates)
    with pytest.raises(ToolSelectionError, match="NO_COMPATIBLE_AVAILABLE_TOOL"):
        select_tool(small, state.model_copy(update={"changer_state": "FAULTED"}))
    bottle_fork = evaluate_candidate(
        product_spec("SKU-D"), tool_spec("EE_SUPPORT_FORK"), state, 0.75
    )
    assert "DISALLOWED_PRODUCT_TOOL_PAIR" in bottle_fork.reasons
    assert "NO_SYNTHETIC_UNDER_CLEARANCE" in bottle_fork.reasons
    medium_narrow = evaluate_candidate(
        product_spec("SKU-B"), tool_spec("EE_PINCH_NARROW"), state, 0.8
    )
    assert "GEOMETRY_OUTSIDE_SIMULATED_GRASP_RANGE" in medium_narrow.reasons


@pytest.mark.parametrize("mass", [0, -1, float("nan"), float("inf")])
def test_hkm_selector_rejects_invalid_mass(mass):
    with pytest.raises(ToolSelectionError, match="INVALID_PRODUCT_MASS"):
        select_tool(product_spec("SKU-A"), initial_tool_state(), mass_kg=mass)


def test_hkm_selector_uses_catalogue_order_for_equal_scores():
    product = product_spec("SKU-A")
    # The preferred single cup is absent, so equally eligible alternatives tie.
    state = ToolState(active_tool_id=None, rack_tool_ids=("EE_PINCH_NARROW", "EE_VAC_ARRAY"))
    result = select_tool(product, state)
    assert result.selected_tool_id == "EE_VAC_ARRAY"
    tied = [candidate for candidate in result.candidate_tools if candidate.eligible]
    assert len(tied) == 2 and tied[0].score == tied[1].score
    mounted = ToolState(active_tool_id="EE_PINCH_NARROW", rack_tool_ids=("EE_VAC_ARRAY",))
    assert select_tool(product, mounted).selected_tool_id == "EE_PINCH_NARROW"


@pytest.mark.parametrize(
    "position,reason",
    [
        ((1.551, 0, 0.5), "WORKSPACE_RADIAL_LIMIT"),
        ((0, 0, 0.159), "WORKSPACE_HEIGHT_LIMIT"),
        ((0, 0, 1.151), "WORKSPACE_HEIGHT_LIMIT"),
    ],
)
def test_hkm_workspace_rejects_outside_radius_or_height(position, reason):
    with pytest.raises(ValueError, match=reason):
        validate_workspace(Pose(position=position, calibration_version="hkm-cal-1"))


def test_hkm_workspace_accepts_boundary_and_blocks_frame_calibration_tilt():
    for position in ((1.55, 0, 0.16), (0, 0, 1.15), (0, 0, 1.02)):
        validate_workspace(Pose(position=position, calibration_version="hkm-cal-1"))
    with pytest.raises(ValueError, match="SPATIAL_METADATA_MISMATCH"):
        validate_workspace(Pose(position=(0, 0, 0.5)))
    with pytest.raises(ValueError, match="SPATIAL_METADATA_MISMATCH"):
        validate_workspace(
            Pose(position=(0, 0, 0.5), frame_id="camera_overhead", calibration_version="hkm-cal-1")
        )
    with pytest.raises(ValueError, match="UPRIGHT"):
        validate_workspace(
            Pose(
                position=(0, 0, 0.5), quaternion_xyzw=(1, 0, 0, 0), calibration_version="hkm-cal-1"
            )
        )


def test_hkm_six_product_trajectory_sequence_fits_static_and_observed_obstacles():
    catalogue = load_catalogue()
    state = initial_tool_state()
    poses = {product.sku: fixture_source_pose(product.sku) for product in catalogue.products}
    for product in catalogue.products:
        barriers = default_obstacles() + product_obstacles(
            [(other.sku, other, poses[other.sku]) for other in catalogue.products],
            exclude_product_id=product.sku,
        )
        tool = tool_spec(product.preferred_tool_id)
        target = fixture_target_pose(product.sku)
        trajectory = plan_trajectory(
            product, tool, poses[product.sku], target, tool_state=state, obstacles=barriers
        )
        again = plan_trajectory(
            product, tool, poses[product.sku], target, tool_state=state, obstacles=barriers
        )
        assert trajectory == again
        phases = [point.phase for point in trajectory.waypoints]
        assert set(REQUIRED_PICK_PHASES) <= set(phases)
        assert trajectory.estimated_sim_duration_s == trajectory.waypoints[-1].sim_time_s
        assert trajectory.timing_classification == "SIMULATOR_PRESENTATION_TIMING"
        assert collision_free(trajectory, product, tool, barriers)
        if state.active_tool_id == tool.tool_id:
            assert "TOOL_CHANGE_NOT_REQUIRED" in phases
        else:
            for phase in (
                "TOOL_CHANGE_REQUESTED",
                "RELEASE_CURRENT_TOOL",
                "VERIFY_FLANGE_EMPTY",
                "ENGAGE_REQUESTED_TOOL",
                "VERIFY_TOOL_ID",
                "RETREAT_FROM_TOOL_RACK",
                "TOOL_CHANGE_COMPLETED",
            ):
                assert phase in phases
            empty = next(
                point for point in trajectory.waypoints if point.phase == "VERIFY_FLANGE_EMPTY"
            )
            assert empty.active_tool_id is None
        assert all(
            point.pose.position[2] >= catalogue.workspace.safe_transfer_z_m
            for point in trajectory.waypoints
            if point.phase == "SAFE_TRANSFER"
        )
        assert next(point for point in trajectory.waypoints if point.phase == "GRASP").attached
        assert not next(
            point for point in trajectory.waypoints if point.phase == "RELEASE"
        ).attached
        poses[product.sku] = target
        state = ToolState(
            active_tool_id=tool.tool_id,
            rack_tool_ids=tuple(
                item.tool_id for item in catalogue.tools if item.tool_id != tool.tool_id
            ),
        )


def test_hkm_collision_alternative_is_finite_and_deterministic():
    product = product_spec("SKU-A")
    tool = tool_spec(product.preferred_tool_id)
    obstacle = CollisionObstacle(
        obstacle_id="transfer-blocker", minimum=(0.30, 0.08, 0.98), maximum=(0.40, 0.18, 1.20)
    )
    arguments = (product, tool, fixture_source_pose(product.sku), fixture_target_pose(product.sku))
    direct = plan_trajectory(*arguments, obstacles=())
    assert direct.route_index == 0
    assert not collision_free(direct, product, tool, (obstacle,))
    alternative = plan_trajectory(*arguments, obstacles=(obstacle,))
    assert alternative.route_index == 1
    assert alternative == plan_trajectory(*arguments, obstacles=(obstacle,))
    impossible = CollisionObstacle(
        obstacle_id="sealed-space", minimum=(-2, -2, 0), maximum=(2, 2, 2)
    )
    with pytest.raises(ValueError, match="^NO_COLLISION_FREE_SYNTHETIC_TRAJECTORY$"):
        plan_trajectory(*arguments, obstacles=(impossible,))


def test_hkm_collision_preflight_catalogue_copy_cost_is_independent_of_segments(monkeypatch):
    product = product_spec("SKU-B")
    tool = tool_spec(product.preferred_tool_id)
    obstacles = default_obstacles()
    trajectory = plan_trajectory(
        product,
        tool,
        fixture_source_pose(product.sku),
        fixture_target_pose(product.sku),
        obstacles=obstacles,
    )
    assert len(trajectory.waypoints) > 20  # Includes release, empty flange and a new tool.
    state = initial_tool_state()
    original_copy = RoboticsCatalogue.model_copy
    copies = []

    def counted_copy(self, *args, **kwargs):
        copies.append(self)
        return original_copy(self, *args, **kwargs)

    monkeypatch.setattr(RoboticsCatalogue, "model_copy", counted_copy)
    assert collision_free(trajectory, product, tool, obstacles, tool_state=state)
    # One independent preflight catalogue retains caller mutation isolation.
    # Copy cost cannot multiply by segments or occupied rack positions.
    assert len(copies) == 1


def test_hkm_thin_obstacles_cannot_fall_between_collision_samples():
    samples = segment_samples((0, 0, 0), (1, 0, 0))
    assert len(samples) == 41 and samples[0] == (0, 0, 0) and samples[-1] == (1, 0, 0)
    assert segment_intersects_aabb(
        (0, 0, 0), (1, 0, 0), (0.01001, -0.001, -0.001), (0.01002, 0.001, 0.001)
    )
    assert not segment_intersects_aabb((0, 0, 0), (1, 0, 0), (0.1, 0.1, 0.1), (0.2, 0.2, 0.2))
    assert not segment_intersects_aabb((0, 0, 0), (0.1, 0.1, 0.1), (1, 1, 1), (2, 2, 2))
    with pytest.raises(ValueError, match="INVALID_SEGMENT_SPACING"):
        segment_samples((0, 0, 0), (1, 0, 0), 0)


def test_hkm_rotating_tool_sweep_cannot_hide_between_endpoint_bounds():
    product = product_spec("SKU-F")
    tool = tool_spec(product.preferred_tool_id)
    original = plan_trajectory(
        product, tool, fixture_source_pose(product.sku), fixture_target_pose(product.sku)
    )
    # Isolate a stationary TCP: the long fork clears this obstacle at 0 and
    # 180 degrees, but its tip hits it midway through the yaw rotation.
    pose = Pose(position=(0, 0, 1), calibration_version="hkm-cal-1")
    points = tuple(
        point.model_copy(update={"pose": pose, "active_tool_id": tool.tool_id, "attached": True})
        for point in original.waypoints
    )
    obstacle = CollisionObstacle(
        obstacle_id="yaw-sweep-obstacle",
        minimum=(-0.01, 0.22, 0.99),
        maximum=(0.01, 0.24, 1.03),
    )
    fixed = original.model_copy(update={"waypoints": points})
    assert collision_free(fixed, product, tool, (obstacle,))
    turning = tuple(
        point.model_copy(update={"pose": pose.model_copy(update={"quaternion_xyzw": (0, 0, 1, 0)})})
        if index >= len(points) // 2
        else point
        for index, point in enumerate(points)
    )
    assert not collision_free(
        original.model_copy(update={"waypoints": turning}), product, tool, (obstacle,)
    )


def test_hkm_observed_tilted_product_uses_all_rotation_axes_for_collision():
    bottle = product_spec("SKU-D")
    pose = Pose(
        position=(0, 0, 0.4),
        quaternion_xyzw=(sqrt(0.5), 0, 0, sqrt(0.5)),
        calibration_version="hkm-cal-1",
    )
    obstacle = product_obstacles([("bottle", bottle, pose)])[0]
    assert obstacle.minimum == pytest.approx((-0.0375, -0.115, 0.3625))
    assert obstacle.maximum == pytest.approx((0.0375, 0.115, 0.4375))


def test_hkm_idle_tool_obstacles_follow_observed_rack_occupancy():
    product = product_spec("SKU-A")
    tool = tool_spec(product.preferred_tool_id)
    trajectory = plan_trajectory(
        product, tool, fixture_source_pose(product.sku), fixture_target_pose(product.sku)
    )
    idle_dock = load_catalogue().layout.tool_docks["EE_VAC_ARRAY"]
    points = tuple(point.model_copy(update={"pose": idle_dock}) for point in trajectory.waypoints)
    crossing = trajectory.model_copy(update={"waypoints": points})
    assert not collision_free(crossing, product, tool, (), tool_state=initial_tool_state())
    no_idle_tools = ToolState(active_tool_id=tool.tool_id, rack_tool_ids=())
    assert collision_free(crossing, product, tool, (), tool_state=no_idle_tools)


def test_hkm_only_registered_vertical_docking_contact_is_exempt():
    product = product_spec("SKU-B")
    tool = tool_spec(product.preferred_tool_id)
    trajectory = plan_trajectory(
        product, tool, fixture_source_pose(product.sku), fixture_target_pose(product.sku)
    )
    state = initial_tool_state()
    assert collision_free(trajectory, product, tool, (), tool_state=state)
    engage_index = next(
        index
        for index, point in enumerate(trajectory.waypoints)
        if point.phase == "ENGAGE_REQUESTED_TOOL"
    )
    points = list(trajectory.waypoints)
    approach = points[engage_index - 1]
    x, y, z = approach.pose.position
    points[engage_index - 1] = approach.model_copy(
        update={"pose": approach.pose.model_copy(update={"position": (x + 0.04, y, z)})}
    )
    assert not collision_free(
        trajectory.model_copy(update={"waypoints": tuple(points)}),
        product,
        tool,
        (),
        tool_state=state,
    )
    # After uncoupling, the original tool becomes a real rack obstacle again.
    points = tuple(
        point.model_copy(update={"pose": load_catalogue().layout.tool_docks[state.active_tool_id]})
        if point.phase == "PRE_GRASP"
        else point
        for point in trajectory.waypoints
    )
    assert not collision_free(
        trajectory.model_copy(update={"waypoints": points}), product, tool, (), tool_state=state
    )


def test_hkm_grasp_contact_conventions_and_smooth_presentation():
    for sku, sign in (
        ("SKU-A", 1),
        ("SKU-B", 1),
        ("SKU-C", 0),
        ("SKU-D", 0),
        ("SKU-E", 0),
        ("SKU-F", -1),
    ):
        product = product_spec(sku)
        source = fixture_source_pose(sku)
        tcp = grasp_pose(source, product, tool_spec(product.preferred_tool_id))
        assert isclose(
            tcp.position[2] - source.position[2], sign * product.dimensions_m[2] / 2, abs_tol=1e-12
        )
    assert [smoothstep(value) for value in (-1, 0, 0.5, 1, 2)] == [0, 0, 0.5, 1, 1]
    assert smoothstep(0.01) < 0.001


def test_hkm_trajectory_defensively_rejects_invalid_pair_unavailable_and_modified_plan():
    product = product_spec("SKU-A")
    tool = tool_spec(product.preferred_tool_id)
    source, target = fixture_source_pose(product.sku), fixture_target_pose(product.sku)
    with pytest.raises(ValueError, match="TOOL_UNAVAILABLE"):
        plan_trajectory(
            product,
            tool,
            source,
            target,
            tool_state=ToolState(active_tool_id=None, rack_tool_ids=()),
        )
    with pytest.raises(ValueError, match="TOOL_CHANGER_NOT_READY"):
        plan_trajectory(
            product,
            tool,
            source,
            target,
            tool_state=initial_tool_state().model_copy(update={"changer_state": "FAULTED"}),
        )
    bottle = product_spec("SKU-D")
    with pytest.raises(ValueError, match="INVALID_PRODUCT_TOOL_PAIR"):
        plan_trajectory(
            bottle,
            tool_spec("EE_SUPPORT_FORK"),
            fixture_source_pose(bottle.sku),
            fixture_target_pose(bottle.sku),
        )
    trajectory = plan_trajectory(product, tool, source, target)
    for updates, reason in (({"required_tool_id": "EE_VAC_ARRAY"}, "TRAJECTORY_TOOL_MISMATCH"),):
        with pytest.raises(ValueError, match=reason):
            validate_trajectory(trajectory.model_copy(update=updates), product, tool)
    with pytest.raises(ValueError, match="TRAJECTORY_GRASP_MISMATCH"):
        validate_trajectory(trajectory, product, tool, source_pose=target)
    with pytest.raises(ValueError, match="TRAJECTORY_TARGET_MISMATCH"):
        validate_trajectory(trajectory, product, tool, target_pose=source)
    # Keep contract length valid while replacing a required semantic phase.
    changed = tuple(
        point.model_copy(update={"phase": "NEXT_SAFE_POSE"}) if point.phase == "GRASP" else point
        for point in trajectory.waypoints
    )
    with pytest.raises(ValueError, match="MISSING_REQUIRED_TRAJECTORY_PHASE"):
        validate_trajectory(trajectory.model_copy(update={"waypoints": changed}), product, tool)
    altered_workspace = WorkspaceProfile(safe_transfer_z_m=1.1)
    with pytest.raises(ValueError, match="TRANSFER_BELOW_SAFE_PLANE"):
        validate_trajectory(trajectory, product, tool, workspace=altered_workspace)


def test_hkm_planning_modules_do_not_import_or_read_world_truth():
    for name in ("selector.py", "trajectory.py"):
        tree = ast.parse((Path("robotops/robotics") / name).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                assert node.id not in {"WorldState", "SyntheticRuntime", "BlenderRuntime", "bpy"}
            if isinstance(node, ast.Attribute):
                assert node.attr != "world"
