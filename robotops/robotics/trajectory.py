"""Conservative synthetic AABB preflight, not certified robot motion planning.

Trajectories express TCP poses and presentation timing, never real HKM joints.
Every segment is sampled deterministically for workspace checks and tested with
an exact slab intersection against inflated AABBs, so thin walls cannot be skipped.
"""

import hashlib
import json
from collections.abc import Mapping, Sequence
from math import ceil, dist, hypot
from typing import cast

from robotops.domain.base import Pose
from robotops.hkm_geometry import static_obstacle_bounds
from robotops.robotics.catalogue import (
    initial_tool_state,
    load_catalogue,
)
from robotops.robotics.models import (
    CollisionObstacle,
    EndEffectorSpec,
    ProductSpec,
    ToolId,
    ToolState,
    TrajectoryIntent,
    TrajectoryPhase,
    TrajectoryWaypoint,
    Vector3,
    WorkspaceProfile,
)
from robotops.robotics.selector import geometry_reason

REQUIRED_PICK_PHASES: tuple[TrajectoryPhase, ...] = (
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


def smoothstep(value: float) -> float:
    """Cubic presentation interpolation with zero endpoint velocity."""
    bounded = max(0.0, min(1.0, value))
    return bounded * bounded * (3 - 2 * bounded)


def translated(pose: Pose, offset: Vector3) -> Pose:
    return pose.model_copy(
        update={"position": tuple(a + b for a, b in zip(pose.position, offset, strict=True))}
    )


def at_height(pose: Pose, height: float) -> Pose:
    return pose.model_copy(update={"position": (pose.position[0], pose.position[1], height)})


def grasp_pose(product_pose: Pose, product: ProductSpec, tool: EndEffectorSpec) -> Pose:
    offset = product.dimensions_m[2] / 2
    if tool.family == "fork":
        offset = -offset
    elif tool.family in {"pinch", "soft"}:
        offset = 0
    return translated(product_pose, (0, 0, offset))


def validate_workspace(pose: Pose, workspace: WorkspaceProfile | None = None) -> None:
    envelope = workspace or load_catalogue().workspace
    pose = Pose.model_validate(pose.model_dump())
    if (
        pose.frame_id != envelope.frame_id
        or pose.calibration_version != envelope.calibration_version
    ):
        raise ValueError("SPATIAL_METADATA_MISMATCH")
    x, y, z = pose.position
    if hypot(x, y) > envelope.radial_limit_m + 1e-9:
        raise ValueError("WORKSPACE_RADIAL_LIMIT")
    if not envelope.min_z_m - 1e-9 <= z <= envelope.max_z_m + 1e-9:
        raise ValueError("WORKSPACE_HEIGHT_LIMIT")
    if abs(pose.quaternion_xyzw[0]) > 1e-9 or abs(pose.quaternion_xyzw[1]) > 1e-9:
        raise ValueError("SYNTHETIC_PROFILE_REQUIRES_UPRIGHT_TOOL")


def segment_samples(start: Vector3, end: Vector3, spacing_m: float = 0.025) -> tuple[Vector3, ...]:
    if spacing_m <= 0:
        raise ValueError("INVALID_SEGMENT_SPACING")
    count = max(1, ceil(dist(start, end) / spacing_m))
    return tuple(
        (
            start[0] + (end[0] - start[0]) * i / count,
            start[1] + (end[1] - start[1]) * i / count,
            start[2] + (end[2] - start[2]) * i / count,
        )
        for i in range(count + 1)
    )


def segment_intersects_aabb(
    start: Vector3, end: Vector3, minimum: Vector3, maximum: Vector3
) -> bool:
    entering, leaving = 0.0, 1.0
    for a, b, low, high in zip(start, end, minimum, maximum, strict=True):
        direction = b - a
        if abs(direction) < 1e-12:
            if a < low or a > high:
                return False
            continue
        one, two = (low - a) / direction, (high - a) / direction
        entering = max(entering, min(one, two))
        leaving = min(leaving, max(one, two))
        if entering > leaving:
            return False
    return True


def _bounds(
    product: ProductSpec,
    tool: EndEffectorSpec | None,
    attached: bool,
    offset: Vector3,
    pose: Pose,
    empty_flange: tuple[Vector3, Vector3],
) -> tuple[Vector3, Vector3]:
    """Axis-wise conservative bounds preserve long-carton clearance in its tote.

    Tool body occupies TCP..flange; carried object uses the explicit attachment
    offset. Upright yaw is accounted for by the absolute rotation matrix.
    """
    qz, qw = pose.quaternion_xyzw[2:]
    cosine, sine = abs(1 - 2 * qz * qz), abs(2 * qz * qw)
    if tool is None:
        dimensions, centre = empty_flange
    else:
        dimensions, centre = tool.collision_envelope_m, tool.collision_offset_m
    tx, ty, tz = dimensions
    x, y = (cosine * tx + sine * ty) / 2, (sine * tx + cosine * ty) / 2
    cx, cy, cz = centre
    signed_cosine, signed_sine = 1 - 2 * qz * qz, 2 * qz * qw
    cx, cy = signed_cosine * cx - signed_sine * cy, signed_sine * cx + signed_cosine * cy
    low, high = [cx - x, cy - y, cz - tz / 2], [cx + x, cy + y, cz + tz / 2]
    if attached:
        px, py, pz = product.dimensions_m
        half = ((cosine * px + sine * py) / 2, (sine * px + cosine * py) / 2, pz / 2)
        for axis in range(3):
            low[axis] = min(low[axis], offset[axis] - half[axis])
            high[axis] = max(high[axis], offset[axis] + half[axis])
    margin = 0.002
    return (low[0] - margin, low[1] - margin, low[2] - margin), (
        high[0] + margin,
        high[1] + margin,
        high[2] + margin,
    )


def collision_free(
    trajectory: TrajectoryIntent,
    product: ProductSpec,
    tool: EndEffectorSpec,
    obstacles: Sequence[CollisionObstacle],
    *,
    tool_state: ToolState | None = None,
    tool_docks: Mapping[ToolId, Pose] | None = None,
) -> bool:
    # One isolated catalogue per preflight. Fixed rack geometry can be reused;
    # occupancy and intentional contact are still evaluated for every segment.
    catalogue = load_catalogue()
    specifications = {item.tool_id: item for item in catalogue.tools}
    empty_flange = (
        catalogue.empty_flange_collision_envelope_m,
        catalogue.empty_flange_collision_offset_m,
    )
    cached_rack_bounds: dict[ToolId, CollisionObstacle] = {}
    docks = tool_docks if tool_docks is not None else catalogue.layout.tool_docks
    initial_tool = trajectory.waypoints[0].active_tool_id
    state = tool_state or ToolState(
        active_tool_id=initial_tool,
        rack_tool_ids=tuple(
            item.tool_id for item in catalogue.tools if item.tool_id != initial_tool
        ),
    )
    if state.active_tool_id != initial_tool:
        return False
    occupied = set(state.rack_tool_ids)
    released: ToolId | None = None
    for start, end in zip(trajectory.waypoints, trajectory.waypoints[1:], strict=False):
        # Use both endpoint envelopes if tool identity or attachment changes.
        endpoint_bounds = [
            _bounds(
                product,
                specifications[point.active_tool_id] if point.active_tool_id else None,
                point.attached,
                trajectory.product_attachment_offset_m,
                point.pose,
                empty_flange,
            )
            for point in (start, end)
        ]
        low = tuple(min(bounds[0][axis] for bounds in endpoint_bounds) for axis in range(3))
        high = tuple(max(bounds[1][axis] for bounds in endpoint_bounds) for axis in range(3))
        quaternion_dot = sum(
            a * b for a, b in zip(start.pose.quaternion_xyzw, end.pose.quaternion_xyzw, strict=True)
        )
        if abs(quaternion_dot) < 1 - 1e-12:
            # A rotating long tool can sweep beyond BOTH endpoint AABBs. This
            # upright profile uses its full planar circumscribed radius for
            # changing yaw, conservatively bounding every intermediate angle.
            radius = hypot(max(abs(low[0]), abs(high[0])), max(abs(low[1]), abs(high[1])))
            low, high = (-radius, -radius, low[2]), (radius, radius, high[2])
        rack_obstacles = []
        for tool_id in sorted(occupied):
            dock = docks[tool_id]
            if _intentional_dock_contact(start, end, tool_id, dock, released):
                continue
            if tool_id not in cached_rack_bounds:
                rack_low, rack_high = _bounds(
                    product, specifications[tool_id], False, (0, 0, 0), dock, empty_flange
                )
                cached_rack_bounds[tool_id] = CollisionObstacle(
                    obstacle_id="racked-" + tool_id,
                    minimum=tuple(a + b for a, b in zip(dock.position, rack_low, strict=True)),
                    maximum=tuple(a + b for a, b in zip(dock.position, rack_high, strict=True)),
                )
            rack_obstacles.append(cached_rack_bounds[tool_id])
        for obstacle in (*obstacles, *rack_obstacles):
            minimum = cast(Vector3, tuple(obstacle.minimum[axis] - high[axis] for axis in range(3)))
            maximum = cast(Vector3, tuple(obstacle.maximum[axis] - low[axis] for axis in range(3)))
            if segment_intersects_aabb(start.pose.position, end.pose.position, minimum, maximum):
                return False
        if start.active_tool_id != end.active_tool_id:
            if (
                start.active_tool_id is not None
                and end.active_tool_id is None
                and end.phase == "RELEASE_CURRENT_TOOL"
                and end.pose == docks[start.active_tool_id]
            ):
                released = start.active_tool_id
                occupied.add(released)
            elif (
                start.active_tool_id is None
                and end.active_tool_id in occupied
                and end.phase == "ENGAGE_REQUESTED_TOOL"
                and end.pose == docks[end.active_tool_id]
            ):
                occupied.remove(end.active_tool_id)
                released = None
            else:
                return False
    return True


def _intentional_dock_contact(
    start: TrajectoryWaypoint,
    end: TrajectoryWaypoint,
    tool_id: ToolId,
    dock: Pose,
    released: ToolId | None,
) -> bool:
    """Allow only vertical engage/uncouple at the matching registered tool dock."""
    if any(
        point.pose.position[:2] != dock.position[:2]
        or point.pose.position[2] < dock.position[2] - 1e-9
        or point.pose.quaternion_xyzw != dock.quaternion_xyzw
        for point in (start, end)
    ):
        return False
    engaging = (
        start.phase == "MOVE_TO_TOOL_DOCK"
        and start.active_tool_id is None
        and end.phase == "ENGAGE_REQUESTED_TOOL"
        and end.active_tool_id == tool_id
        and end.pose == dock
    )
    uncoupling = (
        tool_id == released
        and start.active_tool_id is None
        and end.active_tool_id is None
        and start.pose == dock
        and (start.phase, end.phase)
        in {
            ("RELEASE_CURRENT_TOOL", "VERIFY_FLANGE_EMPTY"),
            ("VERIFY_FLANGE_EMPTY", "MOVE_TO_SAFE_POSE"),
        }
    )
    return engaging or uncoupling


def default_obstacles() -> tuple[CollisionObstacle, ...]:
    """Use AABBs of the SAME procedural static meshes shown in Blender/replay.

    Explicit tote-floor/product-support and registered docking contact surfaces
    are excluded by the geometry contract, not arbitrary obstacle-name filters.
    """
    return tuple(CollisionObstacle.model_validate(item) for item in static_obstacle_bounds())


def product_obstacles(
    products: Sequence[tuple[str, ProductSpec, Pose]],
    *,
    exclude_product_id: str | None = None,
) -> tuple[CollisionObstacle, ...]:
    result = []
    for identity, spec, pose in products:
        if identity == exclude_product_id:
            continue
        # Other observed products may be tilted even though this profile only
        # grasps upright products. Bound all three observed rotation axes.
        qx, qy, qz, qw = pose.quaternion_xyzw
        rotation = (
            (1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)),
            (2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)),
            (2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)),
        )
        half = tuple(
            sum(
                abs(value) * dimension / 2
                for value, dimension in zip(row, spec.dimensions_m, strict=True)
            )
            for row in rotation
        )
        result.append(
            CollisionObstacle(
                obstacle_id="product-" + identity,
                product_id=identity,
                kind="PRODUCT",
                minimum=tuple(pose.position[i] - half[i] for i in range(3)),
                maximum=tuple(pose.position[i] + half[i] for i in range(3)),
            )
        )
    return tuple(result)


def _routes(source: Pose, target: Pose) -> tuple[tuple[Pose, ...], ...]:
    a, b = source.position, target.position
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = hypot(dx, dy)
    nx, ny = (-dy / length, dx / length) if length > 1e-9 else (1.0, 0.0)
    routes: list[tuple[Pose, ...]] = [(source, target)]
    for offset in (0.35, -0.35, 0.65, -0.65):
        middle = source.model_copy(
            update={
                "position": ((a[0] + b[0]) / 2 + nx * offset, (a[1] + b[1]) / 2 + ny * offset, a[2])
            }
        )
        routes.append((source, middle, target))
    for corner in ((a[0], b[1], a[2]), (b[0], a[1], a[2])):
        routes.append((source, source.model_copy(update={"position": corner}), target))
    return tuple(routes)


def _build(
    product: ProductSpec,
    tool: EndEffectorSpec,
    source_pose: Pose,
    target_pose: Pose,
    initial_tcp: Pose,
    workspace: WorkspaceProfile,
    tool_state: ToolState,
    tool_docks: Mapping[ToolId, Pose],
    route: tuple[Pose, ...],
    route_index: int,
) -> TrajectoryIntent:
    timing = load_catalogue().visual_motion
    source_tcp = grasp_pose(source_pose, product, tool)
    target_tcp = grasp_pose(target_pose, product, tool)
    offset: Vector3 = (
        source_pose.position[0] - source_tcp.position[0],
        source_pose.position[1] - source_tcp.position[1],
        source_pose.position[2] - source_tcp.position[2],
    )
    points: list[TrajectoryWaypoint] = []
    clock = 0.0

    def add(
        phase: TrajectoryPhase,
        pose: Pose,
        duration: float,
        attached: bool = False,
        active: ToolId | None = tool.tool_id,
    ) -> None:
        nonlocal clock
        clock = round(clock + duration, 9)
        points.append(
            TrajectoryWaypoint(
                phase=phase, pose=pose, sim_time_s=clock, attached=attached, active_tool_id=active
            )
        )

    add("HOME", initial_tcp, 0, active=tool_state.active_tool_id)
    if tool_state.active_tool_id == tool.tool_id:
        add("TOOL_CHANGE_NOT_REQUIRED", initial_tcp, 0.05)
    else:
        current = tool_state.active_tool_id
        dock = (
            tool_docks[current] if current else at_height(initial_tcp, workspace.safe_transfer_z_m)
        )
        requested = tool_docks[tool.tool_id]
        step = timing.tool_change_s / 12
        add("TOOL_CHANGE_REQUESTED", initial_tcp, step, active=current)
        add(
            "MOVE_TO_SAFE_POSE",
            at_height(initial_tcp, workspace.safe_transfer_z_m),
            step,
            active=current,
        )
        add("MOVE_TO_TOOL_DOCK", at_height(dock, workspace.safe_transfer_z_m), step, active=current)
        add("MOVE_TO_TOOL_DOCK", dock, step, active=current)
        add("RELEASE_CURRENT_TOOL", dock, step, active=None)
        add("VERIFY_FLANGE_EMPTY", dock, step, active=None)
        add("MOVE_TO_SAFE_POSE", at_height(dock, workspace.safe_transfer_z_m), step, active=None)
        add(
            "MOVE_TO_TOOL_DOCK",
            at_height(requested, workspace.safe_transfer_z_m),
            step,
            active=None,
        )
        add("ENGAGE_REQUESTED_TOOL", requested, step)
        add("VERIFY_TOOL_ID", requested, step)
        add("RETREAT_FROM_TOOL_RACK", at_height(requested, workspace.safe_transfer_z_m), step)
        add("TOOL_CHANGE_COMPLETED", at_height(requested, workspace.safe_transfer_z_m), step)
    add("PRE_GRASP", route[0], timing.approach_s)
    add("APPROACH", source_tcp, timing.approach_s)
    add("GRASP", source_tcp, timing.grasp_dwell_s, True)
    add("GRASP_CONFIRM", source_tcp, 0.1, True)
    add("LIFT", route[0], timing.lift_s, True)
    for a, b in zip(route, route[1:], strict=False):
        duration = max(
            timing.transfer_min_s,
            min(timing.transfer_max_s, dist(a.position, b.position) / timing.transfer_speed_m_s),
        )
        add("SAFE_TRANSFER", b, duration, True)
    add("PRE_PLACE", route[-1], 0.1, True)
    add("PLACE", target_tcp, timing.place_s, True)
    add("RELEASE", target_tcp, timing.release_dwell_s)
    add("RELEASE_CONFIRM", target_tcp, 0.1)
    add("RETRACT", route[-1], timing.retract_s)
    add("HOME", at_height(initial_tcp, workspace.safe_transfer_z_m), timing.approach_s)
    raw = {
        "product": product.sku,
        "tool": tool.tool_id,
        "waypoints": [point.model_dump(mode="json") for point in points],
    }
    identifier = hashlib.sha256(
        json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return TrajectoryIntent(
        trajectory_id="trajectory-" + identifier,
        required_tool_id=tool.tool_id,
        grasp_pose=source_tcp,
        target_tcp_pose=target_tcp,
        product_attachment_offset_m=offset,
        waypoints=tuple(points),
        estimated_sim_duration_s=clock,
        route_index=route_index,
    )


def validate_trajectory(
    trajectory: TrajectoryIntent,
    product: ProductSpec,
    tool: EndEffectorSpec,
    *,
    workspace: WorkspaceProfile | None = None,
    obstacles: Sequence[CollisionObstacle] = (),
    source_pose: Pose | None = None,
    target_pose: Pose | None = None,
    tool_state: ToolState | None = None,
    tool_docks: Mapping[ToolId, Pose] | None = None,
) -> None:
    trajectory = TrajectoryIntent.model_validate(trajectory.model_dump())
    envelope = workspace or load_catalogue().workspace
    if trajectory.required_tool_id != tool.tool_id:
        raise ValueError("TRAJECTORY_TOOL_MISMATCH")
    if (
        product.compatibility[tool.tool_id] == "N"
        or geometry_reason(product, tool)
        or product.mass_max_kg > tool.max_simulated_mass_kg
    ):
        raise ValueError("INVALID_PRODUCT_TOOL_PAIR")
    if source_pose is not None and trajectory.grasp_pose != grasp_pose(source_pose, product, tool):
        raise ValueError("TRAJECTORY_GRASP_MISMATCH")
    if target_pose is not None and trajectory.target_tcp_pose != grasp_pose(
        target_pose, product, tool
    ):
        raise ValueError("TRAJECTORY_TARGET_MISMATCH")
    expected = iter(REQUIRED_PICK_PHASES)
    phase: TrajectoryPhase | None = next(expected)
    for point in trajectory.waypoints:
        validate_workspace(point.pose, envelope)
        if point.phase == phase:
            phase = next(expected, None)
    if phase is not None:
        raise ValueError("MISSING_REQUIRED_TRAJECTORY_PHASE")
    if any(
        point.phase == "SAFE_TRANSFER"
        and point.pose.position[2] < envelope.safe_transfer_z_m - 1e-9
        for point in trajectory.waypoints
    ):
        raise ValueError("TRANSFER_BELOW_SAFE_PLANE")
    phases = [point.phase for point in trajectory.waypoints]
    if phases[0] != "HOME" or phases[-1] != "HOME":
        raise ValueError("TRAJECTORY_HOME_BOUNDARY_REQUIRED")
    for required in REQUIRED_PICK_PHASES:
        if required not in {"HOME", "SAFE_TRANSFER"} and phases.count(required) != 1:
            raise ValueError("DUPLICATE_PICK_PHASE")
    grasp_index, release_index = phases.index("GRASP"), phases.index("RELEASE")
    pick_start = phases.index("PRE_GRASP")
    for index, point in enumerate(trajectory.waypoints):
        if point.attached != (grasp_index <= index < release_index):
            raise ValueError("TRAJECTORY_ATTACHMENT_SEQUENCE_INVALID")
        if index >= pick_start and point.active_tool_id != tool.tool_id:
            raise ValueError("TRAJECTORY_ACTIVE_TOOL_MISMATCH")
        expected_pose = None
        if point.phase in {"APPROACH", "GRASP", "GRASP_CONFIRM"}:
            expected_pose = trajectory.grasp_pose
        elif point.phase in {"PLACE", "RELEASE", "RELEASE_CONFIRM"}:
            expected_pose = trajectory.target_tcp_pose
        elif point.phase in {"PRE_GRASP", "LIFT"}:
            expected_pose = at_height(trajectory.grasp_pose, envelope.safe_transfer_z_m)
        elif point.phase in {"PRE_PLACE", "RETRACT"}:
            expected_pose = at_height(trajectory.target_tcp_pose, envelope.safe_transfer_z_m)
        if expected_pose is not None and point.pose != expected_pose:
            raise ValueError("TRAJECTORY_PHASE_POSE_MISMATCH")
    if source_pose is not None:
        attached_position = tuple(
            a + b
            for a, b in zip(
                trajectory.grasp_pose.position, trajectory.product_attachment_offset_m, strict=True
            )
        )
        if any(
            abs(a - b) > 1e-9 for a, b in zip(source_pose.position, attached_position, strict=True)
        ):
            raise ValueError("TRAJECTORY_ATTACHMENT_OFFSET_MISMATCH")
    if target_pose is not None:
        released_position = tuple(
            a + b
            for a, b in zip(
                trajectory.target_tcp_pose.position,
                trajectory.product_attachment_offset_m,
                strict=True,
            )
        )
        if any(
            abs(a - b) > 1e-9 for a, b in zip(target_pose.position, released_position, strict=True)
        ):
            raise ValueError("TRAJECTORY_ATTACHMENT_OFFSET_MISMATCH")
    for start, end in zip(trajectory.waypoints, trajectory.waypoints[1:], strict=False):
        for sample in segment_samples(start.pose.position, end.pose.position):
            validate_workspace(start.pose.model_copy(update={"position": sample}), envelope)
        if (
            end.phase == "SAFE_TRANSFER"
            and min(start.pose.position[2], end.pose.position[2])
            < envelope.safe_transfer_z_m - 1e-9
        ):
            raise ValueError("TRANSFER_BELOW_SAFE_PLANE")
    if not collision_free(
        trajectory, product, tool, obstacles, tool_state=tool_state, tool_docks=tool_docks
    ):
        raise ValueError("NO_COLLISION_FREE_SYNTHETIC_TRAJECTORY")


def plan_trajectory(
    product: ProductSpec,
    tool: EndEffectorSpec,
    source_pose: Pose,
    target_pose: Pose,
    *,
    initial_tcp: Pose | None = None,
    workspace: WorkspaceProfile | None = None,
    obstacles: Sequence[CollisionObstacle] | None = None,
    tool_state: ToolState | None = None,
    tool_docks: Mapping[ToolId, Pose] | None = None,
) -> TrajectoryIntent:
    catalogue = load_catalogue()
    envelope = workspace or catalogue.workspace
    initial = initial_tcp or catalogue.layout.home_tcp_pose
    observed_tools = tool_state or initial_tool_state()
    docks = tool_docks if tool_docks is not None else catalogue.layout.tool_docks
    barriers = default_obstacles() if obstacles is None else obstacles
    if observed_tools.changer_state != "READY":
        raise ValueError("TOOL_CHANGER_NOT_READY")
    if (
        tool.tool_id != observed_tools.active_tool_id
        and tool.tool_id not in observed_tools.rack_tool_ids
    ):
        raise ValueError("TOOL_UNAVAILABLE")
    for pose in (
        initial,
        grasp_pose(source_pose, product, tool),
        grasp_pose(target_pose, product, tool),
    ):
        validate_workspace(pose, envelope)
    if (
        product.compatibility[tool.tool_id] == "N"
        or geometry_reason(product, tool)
        or product.mass_max_kg > tool.max_simulated_mass_kg
    ):
        raise ValueError("INVALID_PRODUCT_TOOL_PAIR")
    source_safe, target_safe = (
        at_height(source_pose, envelope.safe_transfer_z_m),
        at_height(target_pose, envelope.safe_transfer_z_m),
    )
    for index, route in enumerate(_routes(source_safe, target_safe)):
        candidate = _build(
            product,
            tool,
            source_pose,
            target_pose,
            initial,
            envelope,
            observed_tools,
            docks,
            route,
            index,
        )
        try:
            validate_trajectory(
                candidate,
                product,
                tool,
                workspace=envelope,
                obstacles=barriers,
                source_pose=source_pose,
                target_pose=target_pose,
                tool_state=observed_tools,
                tool_docks=docks,
            )
        except ValueError as exc:
            if str(exc) not in {"WORKSPACE_RADIAL_LIMIT", "NO_COLLISION_FREE_SYNTHETIC_TRAJECTORY"}:
                raise
        else:
            return candidate
    raise ValueError("NO_COLLISION_FREE_SYNTHETIC_TRAJECTORY")
