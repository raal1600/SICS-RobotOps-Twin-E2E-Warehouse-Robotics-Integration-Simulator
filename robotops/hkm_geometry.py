"""Original procedural HKM-inspired presentation geometry, shared with Blender.

HKM_INSPIRED_VISUAL_KINEMATICS_V1 is our synthetic two-link display model,
not Cognibotics geometry, inverse kinematics, dynamics or collision evidence.
Only standard-library dependencies are allowed here and in catalogue_data.
Primitive positions/orientations are WORLD transforms; size is in LOCAL axes.
parent_name records semantic ownership, never an additional transform to apply.
"""

import math
from collections.abc import Mapping, Sequence
from typing import Any, NotRequired, TypedDict

from robotops.robotics.catalogue_data import raw_catalogue

Vector3 = tuple[float, float, float]
Quaternion = tuple[float, float, float, float]
VISUAL_KINEMATICS_VERSION = "HKM_INSPIRED_VISUAL_KINEMATICS_V1"
LINK_LENGTH_M = 0.92
SHOULDER_Z_M = 1.20
LINK_SPACING_M = 0.21
FLANGE_TO_TCP_M = 0.18
IDENTITY: Quaternion = (0.0, 0.0, 0.0, 1.0)
CELL = "RobotOpsTwin/Cell"


class Primitive(TypedDict):
    schema_version: str
    name: str
    primitive: str
    position: Vector3
    quaternion_xyzw: Quaternion
    size: Vector3
    scale: Vector3
    parent_name: str | None
    material_role: str
    color: Vector3
    opacity: float
    semantic_tags: tuple[str, ...]
    label: str | None
    visible: bool
    product_id: NotRequired[str]
    location_id: NotRequired[str]
    tool_id: NotRequired[str]


COLORS: dict[str, Vector3] = {
    "floor": (0.055, 0.074, 0.092),
    "graphite": (0.055, 0.073, 0.085),
    "metal": (0.47, 0.53, 0.58),
    "housing": (0.72, 0.77, 0.80),
    "accent": (0.10, 0.52, 0.58),
    "rubber": (0.045, 0.055, 0.065),
    "tool": (0.70, 0.49, 0.17),
    "soft": (0.20, 0.55, 0.48),
    "tote": (0.19, 0.28, 0.33),
    "carton": (0.55, 0.36, 0.19),
    "label": (0.22, 0.56, 0.75),
    "tape": (0.77, 0.61, 0.35),
    "pouch": (0.23, 0.52, 0.47),
    "bottle": (0.39, 0.58, 0.71),
    "red": (0.79, 0.12, 0.09),
    "amber": (0.92, 0.56, 0.07),
    "green": (0.10, 0.66, 0.37),
    "enclosure": (0.33, 0.56, 0.63),
}


def _v(values: Sequence[float]) -> Vector3:
    if len(values) != 3 or not all(math.isfinite(v) for v in values):
        raise ValueError("INVALID_VISUAL_VECTOR")
    return float(values[0]), float(values[1]), float(values[2])


def _add(a: Sequence[float], b: Sequence[float]) -> Vector3:
    return a[0] + b[0], a[1] + b[1], a[2] + b[2]


def _yaw(angle: float) -> Quaternion:
    if not math.isfinite(angle):
        raise ValueError("INVALID_VISUAL_YAW")
    return 0.0, 0.0, math.sin(angle / 2), math.cos(angle / 2)


def _rotate_z(vector: Sequence[float], angle: float) -> Vector3:
    x, y, z = vector
    c, s = math.cos(angle), math.sin(angle)
    return x * c - y * s, x * s + y * c, z


def rotate_vector(vector: Sequence[float], quaternion: Sequence[float]) -> Vector3:
    """Rotate a local vector by an XYZW unit quaternion."""
    x, y, z, w = _quaternion(quaternion)
    vx, vy, vz = _v(vector)
    return (
        (1 - 2 * (y * y + z * z)) * vx + 2 * (x * y - z * w) * vy + 2 * (x * z + y * w) * vz,
        2 * (x * y + z * w) * vx + (1 - 2 * (x * x + z * z)) * vy + 2 * (y * z - x * w) * vz,
        2 * (x * z - y * w) * vx + 2 * (y * z + x * w) * vy + (1 - 2 * (x * x + y * y)) * vz,
    )


def _quaternion(values: Sequence[float]) -> Quaternion:
    if len(values) != 4 or not all(math.isfinite(v) for v in values):
        raise ValueError("INVALID_VISUAL_QUATERNION")
    norm = math.sqrt(sum(v * v for v in values))
    if not math.isclose(norm, 1.0, abs_tol=1e-6):
        raise ValueError("INVALID_VISUAL_QUATERNION")
    return float(values[0]), float(values[1]), float(values[2]), float(values[3])


def _axis_quaternion(direction: Sequence[float]) -> Quaternion:
    """Shortest rotation taking local +Z onto direction; fixed antipodal choice."""
    x, y, z = direction
    norm = math.sqrt(x * x + y * y + z * z)
    if norm < 1e-10:
        raise ValueError("ZERO_LENGTH_VISUAL_BEAM")
    x, y, z = x / norm, y / norm, z / norm
    if z < -1 + 1e-10:
        return 1.0, 0.0, 0.0, 0.0
    q = (-y, x, 0.0, 1 + z)
    length = math.sqrt(sum(value * value for value in q))
    return q[0] / length, q[1] / length, 0.0, q[3] / length


def _part(
    name: str,
    position: Sequence[float],
    size: Sequence[float],
    material: str,
    *,
    parent: str | None = CELL,
    primitive: str = "box",
    quaternion: Sequence[float] = IDENTITY,
    tags: tuple[str, ...] = (),
    label: str | None = None,
    opacity: float = 1.0,
    visible: bool = True,
) -> Primitive:
    dimensions = _v(size)
    if min(dimensions) <= 0 or primitive not in {"box", "cylinder"}:
        raise ValueError("INVALID_VISUAL_PRIMITIVE")
    return {
        "schema_version": "2.0",
        "name": name,
        "primitive": primitive,
        "position": _v(position),
        "quaternion_xyzw": _quaternion(quaternion),
        "size": dimensions,
        "scale": (1.0, 1.0, 1.0),
        "parent_name": parent,
        "material_role": material,
        "color": COLORS[material],
        "opacity": opacity,
        "semantic_tags": tags,
        "label": label,
        "visible": visible,
    }


def _beam(name: str, start: Vector3, end: Vector3, parent: str) -> Primitive:
    delta = tuple(b - a for a, b in zip(start, end, strict=True))
    length = math.sqrt(sum(v * v for v in delta))
    midpoint = tuple((a + b) / 2 for a, b in zip(start, end, strict=True))
    return _part(
        name,
        midpoint,
        (0.038, 0.055, length),
        "graphite",
        parent=parent,
        quaternion=_axis_quaternion(delta),
        tags=("robot", "link", "dynamic"),
    )


def linkage_points(tcp_position: Sequence[float]) -> dict[str, Vector3]:
    """Return original equal-length planar linkage anchors in world metres.

    The elbow is the upper solution of the intersection of two circles. This
    transparent synthetic construction avoids inferring a real HKM mechanism.
    """
    x, y, z = _v(tcp_position)
    radial = math.hypot(x, y)
    yaw = math.atan2(y, x) if radial > 1e-10 else 0.0
    wrist_z = z + FLANGE_TO_TCP_M
    dz = wrist_z - SHOULDER_Z_M
    distance = math.hypot(radial, dz)
    if distance > 2 * LINK_LENGTH_M + 1e-9:
        raise ValueError("TCP_OUTSIDE_VISUAL_LINKAGE")
    if distance < 1e-10:
        elbow_r, elbow_z = LINK_LENGTH_M, SHOULDER_Z_M
    else:
        height = math.sqrt(max(0.0, LINK_LENGTH_M**2 - (distance / 2) ** 2))
        elbow_r = radial / 2 - dz * height / distance
        elbow_z = SHOULDER_Z_M + dz / 2 + radial * height / distance
    result: dict[str, Vector3] = {}
    for side, lateral in (("Left", -LINK_SPACING_M / 2), ("Right", LINK_SPACING_M / 2)):
        for joint, r, h in (
            ("Shoulder", 0.0, SHOULDER_Z_M),
            ("Elbow", elbow_r, elbow_z),
            ("Wrist", radial, wrist_z),
        ):
            result[side + joint] = _rotate_z((r, lateral, h), yaw)
    return result


def robot_primitives(tcp_position: Sequence[float], tool_yaw: float = 0.0) -> list[Primitive]:
    tcp = _v(tcp_position)
    yaw = math.atan2(tcp[1], tcp[0])
    anchors = linkage_points(tcp)
    flange = _add(tcp, (0, 0, FLANGE_TO_TCP_M))
    parts = [
        _part(
            "Robot/BaseColumn",
            (0, 0, 0.46),
            (0.34, 0.34, 0.92),
            "housing",
            primitive="cylinder",
            tags=("robot", "base"),
        ),
        _part(
            "Robot/BaseFoot",
            (0, 0, 0.055),
            (0.56, 0.56, 0.11),
            "graphite",
            parent="Robot/BaseColumn",
        ),
        _part(
            "Robot/RotaryBase",
            (0, 0, 1.0),
            (0.39, 0.39, 0.19),
            "graphite",
            primitive="cylinder",
            parent="Robot/BaseColumn",
            quaternion=_yaw(yaw),
            tags=("robot", "joint", "dynamic"),
        ),
        _part(
            "Robot/UpperAssembly",
            (0, 0, SHOULDER_Z_M),
            (0.23, 0.33, 0.19),
            "metal",
            parent="Robot/RotaryBase",
            quaternion=_yaw(yaw),
            tags=("robot", "dynamic"),
        ),
        _part(
            "Robot/WristAssembly",
            flange,
            (0.13, 0.29, 0.105),
            "metal",
            parent="Robot/UpperAssembly",
            quaternion=_yaw(yaw),
            tags=("robot", "dynamic"),
        ),
        _part(
            "Robot/ToolFlange",
            _add(flange, (0, 0, -0.042)),
            (0.105, 0.105, 0.045),
            "graphite",
            primitive="cylinder",
            parent="Robot/WristAssembly",
            quaternion=_yaw(tool_yaw),
            tags=("robot", "dynamic"),
        ),
        _part(
            "Robot/ToolChanger",
            _add(flange, (0, 0, -0.07)),
            (0.09, 0.09, 0.026),
            "accent",
            primitive="cylinder",
            parent="Robot/ToolFlange",
            quaternion=_yaw(tool_yaw),
            tags=("robot", "tool_changer", "dynamic"),
        ),
    ]
    joint_quaternion = _axis_quaternion(_rotate_z((0, 1, 0), yaw))
    for side in ("Left", "Right"):
        shoulder, elbow, wrist = (
            anchors[side + suffix] for suffix in ("Shoulder", "Elbow", "Wrist")
        )
        parts.extend(
            [
                _beam(f"Robot/ParallelLink{side}Upper", shoulder, elbow, "Robot/UpperAssembly"),
                _beam(f"Robot/ParallelLink{side}Lower", elbow, wrist, f"Robot/{side}ElbowJoint"),
            ]
        )
        for label, point in (("Shoulder", shoulder), ("Elbow", elbow), ("Wrist", wrist)):
            parts.append(
                _part(
                    f"Robot/{side}{label}Joint",
                    point,
                    (0.105, 0.105, 0.075),
                    "housing",
                    primitive="cylinder",
                    parent="Robot/UpperAssembly",
                    quaternion=joint_quaternion,
                    tags=("robot", "joint", "dynamic"),
                )
            )
    return parts


def primitive_bounds(primitive: Primitive) -> tuple[Vector3, Vector3]:
    """Conservative world AABB, including cylinder bounding boxes and world scale."""
    half_size = tuple(
        size * scale / 2 for size, scale in zip(primitive["size"], primitive["scale"], strict=True)
    )
    corners = [
        _add(
            primitive["position"],
            rotate_vector(
                (sx * half_size[0], sy * half_size[1], sz * half_size[2]),
                primitive["quaternion_xyzw"],
            ),
        )
        for sx in (-1, 1)
        for sy in (-1, 1)
        for sz in (-1, 1)
    ]
    return (
        _v(tuple(min(point[axis] for point in corners) for axis in range(3))),
        _v(tuple(max(point[axis] for point in corners) for axis in range(3))),
    )


def static_obstacle_bounds(catalogue: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """Derive forbidden static volumes from the SAME procedural scene.

    Floors, product-support skids and tool-dock coupling contacts are named
    intentional contact surfaces, not traversable general-purpose obstacles.
    Tool docking still requires the registered docking corridor in validation.
    Moving links are display abstractions, not an articulated collision model.
    """
    data = raw_catalogue() if catalogue is None else catalogue
    world = {"objects": [], "robot_state": {"tcp_pose": data["layout"]["home_tcp_pose"]}}
    result = []
    for part in scene_primitives(world, data):
        name, tags = part["name"], part["semantic_tags"]
        forbidden = (
            "tote_wall" in tags
            or "rack_forbidden" in tags
            or name.startswith(("ControlCabinet", "Conveyor", "Enclosure/"))
            or name.endswith(("/Support", "/Crossbar"))
            or name == "Robot/BaseColumn"
        )
        if not forbidden:
            continue
        minimum, maximum = primitive_bounds(part)
        result.append(
            {"obstacle_id": name.replace("/", ":"), "minimum": minimum, "maximum": maximum}
        )
    return result


def tool_primitives(
    tool_id: str,
    tcp_position: Sequence[float],
    tool_yaw: float = 0.0,
    *,
    parent_name: str = "Robot/ToolChanger",
    grasp_width_m: float | None = None,
    grip_amount: float = 0.0,
) -> list[Primitive]:
    """Original tool meshes; contact geometry is synthetic, not real grip physics."""
    tcp = _v(tcp_position)
    if not math.isfinite(grip_amount) or not 0 <= grip_amount <= 1:
        raise ValueError("INVALID_VISUAL_GRIP")
    if grasp_width_m is not None and (not math.isfinite(grasp_width_m) or grasp_width_m <= 0):
        raise ValueError("INVALID_VISUAL_GRASP_WIDTH")
    root = "Tools/" + tool_id
    parts: list[Primitive] = []

    def piece(
        suffix: str, offset: Vector3, size: Vector3, material: str, primitive: str = "box"
    ) -> None:
        item = _part(
            root + suffix,
            _add(tcp, _rotate_z(offset, tool_yaw)),
            size,
            material,
            primitive=primitive,
            parent=parent_name if not suffix else root,
            quaternion=_yaw(tool_yaw),
            tags=("tool", "dynamic"),
        )
        item["tool_id"] = tool_id
        parts.append(item)

    piece("", (0, 0, 0.095), (0.073, 0.073, 0.03), "tool", "cylinder")
    if tool_id == "EE_VAC_SINGLE":
        piece("/Stem", (0, 0, 0.058), (0.024, 0.024, 0.06), "metal", "cylinder")
        piece("/Cup", (0, 0, 0.016), (0.068, 0.068, 0.032), "rubber", "cylinder")
    elif tool_id == "EE_VAC_ARRAY":
        piece("/Plate", (0, 0, 0.07), (0.18, 0.13, 0.025), "metal")
        for index, (x, y) in enumerate(
            ((-0.057, -0.038), (-0.057, 0.038), (0.057, -0.038), (0.057, 0.038)), 1
        ):
            piece(f"/Stem{index}", (x, y, 0.044), (0.017, 0.017, 0.035), "metal", "cylinder")
            piece(f"/Cup{index}", (x, y, 0.014), (0.043, 0.043, 0.028), "rubber", "cylinder")
    elif tool_id in {"EE_PINCH_NARROW", "EE_PINCH_WIDE"}:
        wide = tool_id == "EE_PINCH_WIDE"
        opening = 0.25 if wide else 0.095
        closed = grasp_width_m if grasp_width_m is not None else (0.09 if wide else 0.075)
        opening += (closed - opening) * grip_amount
        thickness = 0.025 if wide else 0.014
        piece("/Bridge", (0, 0, 0.07), (0.31 if wide else 0.15, 0.06, 0.04), "metal")
        for side, sign in (("Left", -1), ("Right", 1)):
            x = sign * (opening + thickness) / 2
            piece(f"/{side}Jaw", (x, 0, 0.012), (thickness, 0.055, 0.09), "graphite")
            piece(f"/{side}Pad", (x - sign * thickness / 2, 0, 0), (0.006, 0.058, 0.042), "rubber")
    elif tool_id == "EE_ADAPTIVE_SOFT":
        piece("/Palm", (0, 0, 0.065), (0.13, 0.13, 0.028), "metal", "cylinder")
        width = grasp_width_m if grasp_width_m is not None else 0.09
        radius = 0.076 + (width / 2 + 0.011 - 0.076) * grip_amount
        for index in range(3):
            angle = 2 * math.pi * index / 3
            x, y = radius * math.cos(angle), radius * math.sin(angle)
            piece(f"/Finger{index + 1}", (x, y, 0.017), (0.023, 0.028, 0.078), "soft")
            piece(
                f"/FingerTip{index + 1}",
                (x * 0.83, y * 0.83, -0.021),
                (0.026, 0.032, 0.029),
                "soft",
            )
    elif tool_id == "EE_SUPPORT_FORK":
        piece("/Back", (-0.245, 0, 0.035), (0.026, 0.16, 0.14), "metal")
        piece("/Neck", (-0.1215, 0, 0.092), (0.273, 0.05, 0.028), "metal")
        for index, y in enumerate((-0.047, 0.047), 1):
            piece(f"/Tine{index}", (-0.02, y, -0.012), (0.45, 0.026, 0.024), "metal")
    else:
        raise ValueError("UNKNOWN_VISUAL_TOOL")
    return parts


def _tote(
    name: str, x: float, y: float, z: float, interior: Vector3, label: str, location_id: str
) -> list[Primitive]:
    width, depth, height = interior
    wall = 0.02
    parts = [
        _part(
            name,
            (x, y, z - 0.03),
            (width + 2 * wall, depth + 2 * wall, 0.06),
            "tote",
            tags=("location", "tote"),
            label=label,
        )
    ]
    parts[0]["location_id"] = location_id
    for suffix, dx, dy, sx, sy in (
        ("LeftWall", -(width + wall) / 2, 0, wall, depth + 2 * wall),
        ("RightWall", (width + wall) / 2, 0, wall, depth + 2 * wall),
        ("FrontWall", 0, -(depth + wall) / 2, width, wall),
        ("BackWall", 0, (depth + wall) / 2, width, wall),
    ):
        # Original open-front presentation fixture: the shallow access lips
        # keep small products inspectable from the operator side. The visible
        # geometry is also the collision-preflight obstacle source of truth.
        actual_height = (
            min(height, 0.03)
            if suffix == "FrontWall"
            else (min(height, 0.05) if suffix == "RightWall" else height)
        )
        parts.append(
            _part(
                name + "/" + suffix,
                (x + dx, y + dy, z + actual_height / 2),
                (sx, sy, actual_height),
                "tote",
                parent=name,
                tags=("tote_wall",),
            )
        )
    for index, (dx, dy) in enumerate(
        ((-width * 0.35, -depth * 0.32), (width * 0.35, depth * 0.32)), 1
    ):
        parts.append(
            _part(
                name + f"/Support{index}",
                (x + dx, y + dy, (z - 0.06) / 2),
                (0.055, 0.055, max(0.03, z - 0.06)),
                "metal",
                parent=name,
            )
        )
    return parts


def _products(world: Mapping[str, Any], specs: Sequence[Mapping[str, Any]]) -> list[Primitive]:
    by_sku = {spec["sku"]: spec for spec in specs}
    parts: list[Primitive] = []
    for item in world["objects"]:
        sku = item["product"]["sku"]
        spec = by_sku[sku]
        ident = item["product"]["product_id"]
        name = "Products/" + ident
        position = _v(item["pose"]["position"])
        dimensions = _v(spec["dimensions_m"])
        quaternion = _quaternion(item["pose"]["quaternion_xyzw"])
        material = {"SKU-C": "pouch", "SKU-D": "bottle", "SKU-E": "metal"}.get(sku, "carton")
        product = _part(
            name,
            position,
            dimensions,
            material,
            primitive="cylinder" if sku in {"SKU-D", "SKU-E"} else "box",
            quaternion=quaternion,
            tags=("product", spec["visual_variant_id"], "dynamic"),
        )
        product["product_id"], product["location_id"] = ident, item["location_id"]
        parts.append(product)
        # Detail children stay inside the declared product bounding envelope.
        width, depth, height = dimensions

        def detail_position(
            offset: Vector3, origin: Vector3 = position, rotation: Quaternion = quaternion
        ) -> Vector3:
            return _add(origin, rotate_vector(offset, rotation))

        if sku in {"SKU-A", "SKU-B", "SKU-F"}:
            parts.append(
                _part(
                    name + "/TopLabel",
                    detail_position((0, 0, height / 2 - 0.001)),
                    (width * 0.55, depth * 0.6, 0.002),
                    "label" if sku == "SKU-A" else "tape",
                    parent=name,
                    quaternion=quaternion,
                    tags=("product_detail", "dynamic"),
                )
            )
        elif sku == "SKU-D":
            parts.append(
                _part(
                    name + "/Cap",
                    detail_position((0, 0, height / 2 - 0.008)),
                    (width * 0.54, depth * 0.54, 0.016),
                    "graphite",
                    parent=name,
                    primitive="cylinder",
                    quaternion=quaternion,
                    tags=("product_detail", "dynamic"),
                )
            )
        elif sku == "SKU-E":
            parts.append(
                _part(
                    name + "/Rim",
                    detail_position((0, 0, height / 2 - 0.006)),
                    (width, depth, 0.012),
                    "housing",
                    parent=name,
                    primitive="cylinder",
                    quaternion=quaternion,
                    tags=("product_detail", "dynamic"),
                )
            )
        elif sku == "SKU-C":
            parts.append(
                _part(
                    name + "/Seal",
                    detail_position((width * 0.42, 0, 0)),
                    (width * 0.12, depth * 0.94, height * 0.6),
                    "soft",
                    parent=name,
                    quaternion=quaternion,
                    tags=("product_detail", "dynamic"),
                )
            )
    return parts


def camera_views(catalogue: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """Sensor extrinsics come from catalogue; viewing never captures an observation."""
    data = raw_catalogue() if catalogue is None else catalogue
    result = []
    for camera in data["cameras"]:
        name = "Camera/" + (
            "OperatorOverview"
            if camera["presentation_only"]
            else "OverheadObservation"
            if "overhead" in camera["frame_id"]
            else "SideInspection"
        )
        result.append(
            {
                "schema_version": "2.0",
                "name": name,
                "position": camera["pose"]["position"],
                "target": (0, 0, 0.55) if camera["presentation_only"] else (0, 0, 0.18),
                "role": "PRESENTATION" if camera["presentation_only"] else "SYNTHETIC_SENSOR",
                "sensor_id": camera["sensor_id"],
                "frame_id": camera["frame_id"],
                "calibration_version": camera["calibration_version"],
                "camera_model_version": camera["camera_model_version"],
            }
        )
    return result


def camera_quaternion(position: Sequence[float], target: Sequence[float]) -> Quaternion:
    """Camera local -Z looks toward target, with +Y as the image up axis."""
    p, t = _v(position), _v(target)
    backward = _v(tuple(a - b for a, b in zip(p, t, strict=True)))
    length = math.sqrt(sum(v * v for v in backward))
    if length < 1e-9:
        raise ValueError("INVALID_CAMERA_TARGET")
    z = tuple(v / length for v in backward)
    # A top-down camera has image-up along world +Y; otherwise use world +Z.
    up = (0.0, 1.0, 0.0) if abs(z[2]) > 0.999 else (0.0, 0.0, 1.0)
    x = (up[1] * z[2] - up[2] * z[1], up[2] * z[0] - up[0] * z[2], up[0] * z[1] - up[1] * z[0])
    length = math.sqrt(sum(v * v for v in x))
    x = _v(tuple(v / length for v in x))
    y = (z[1] * x[2] - z[2] * x[1], z[2] * x[0] - z[0] * x[2], z[0] * x[1] - z[1] * x[0])
    m = ((x[0], y[0], z[0]), (x[1], y[1], z[1]), (x[2], y[2], z[2]))
    trace = m[0][0] + m[1][1] + m[2][2]
    if trace > 0:
        s = math.sqrt(trace + 1) * 2
        return _quaternion(
            ((m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s, (m[1][0] - m[0][1]) / s, s / 4)
        )
    index = max(range(3), key=lambda i: m[i][i])
    j, k = (index + 1) % 3, (index + 2) % 3
    s = math.sqrt(1 + m[index][index] - m[j][j] - m[k][k]) * 2
    q = [0.0, 0.0, 0.0, 0.0]
    q[index] = s / 4
    q[j] = (m[j][index] + m[index][j]) / s
    q[k] = (m[k][index] + m[index][k]) / s
    q[3] = (m[k][j] - m[j][k]) / s
    return _quaternion(q)


def scene_primitives(
    world: Mapping[str, Any], catalogue: Mapping[str, Any] | None = None
) -> list[Primitive]:
    data = raw_catalogue() if catalogue is None else catalogue
    layout = data["layout"]
    dock_x = [pose["position"][0] for pose in layout["tool_docks"].values()]
    rack_x = (min(dock_x) + max(dock_x)) / 2
    rack_width = max(dock_x) - min(dock_x) + 0.44
    parts = [
        _part(
            CELL,
            (0, 0, -0.06),
            (layout["floor_width_m"], layout["floor_depth_m"], 0.12),
            "floor",
            parent=None,
            tags=("cell", "synthetic_world"),
        )
    ]
    tcp_pose = world.get("robot_state", {}).get("tcp_pose", layout["home_tcp_pose"])
    tcp = _v(tcp_pose["position"])
    q = tcp_pose.get("quaternion_xyzw", IDENTITY)
    tool_yaw = math.atan2(2 * (q[3] * q[2] + q[0] * q[1]), 1 - 2 * (q[1] ** 2 + q[2] ** 2))
    parts.extend(robot_primitives(tcp, tool_yaw))
    for sku, source in layout["sources"].items():
        x, y, z = source["pose"]["position"]
        width, depth = source.get("interior_m", (0.62 if sku == "SKU-F" else 0.50, 0.40))[:2]
        parts.extend(
            _tote(
                "Locations/" + source["location_id"],
                x,
                y,
                z,
                (width, depth, source["wall_height_m"]),
                sku[-1],
                source["location_id"],
            )
        )
    destination = layout["destination"]
    x, y, z = destination["pose"]["position"]
    parts.extend(
        _tote(
            "Locations/" + destination["location_id"],
            x,
            y,
            z,
            (*destination["interior_m"], destination["wall_height_m"]),
            "OUT",
            destination["location_id"],
        )
    )
    parts.extend(
        [
            _part("Conveyor", (0, 1.75, 0.12), (1.10, 0.55, 0.20), "graphite", tags=("conveyor",)),
            _part(
                "ControlCabinet",
                (-1.85, -1.1, 0.5),
                (0.36, 0.46, 1),
                "housing",
                tags=("control_cabinet",),
                label="CONTROL",
            ),
            _part(
                "ControlCabinet/Display",
                (-1.85, -1.334, 0.70),
                (0.27, 0.008, 0.19),
                "graphite",
                parent="ControlCabinet",
            ),
            _part(
                "ControlCabinet/LogicalEstop",
                (-1.74, -1.34, 0.43),
                (0.075, 0.075, 0.025),
                "red",
                parent="ControlCabinet",
                primitive="cylinder",
                quaternion=_axis_quaternion((0, -1, 0)),
                tags=("logical_estop",),
                label="LOGICAL STOP",
            ),
            _part(
                "ToolRack",
                (rack_x, 0, 0.40),
                (rack_width, 0.80, 0.20),
                "metal",
                tags=("tool_rack", "rack_forbidden"),
            ),
        ]
    )
    for index in range(7):
        parts.append(
            _part(
                f"Conveyor/Roller{index + 1:02}",
                (0, 1.50 + index * 0.08, 0.21),
                (0.045, 0.045, 1.06),
                "metal",
                parent="Conveyor",
                primitive="cylinder",
                quaternion=_axis_quaternion((1, 0, 0)),
            )
        )
    mode = str(world.get("cell", {}).get("mode", "READY"))
    for index, color in enumerate(("green", "amber", "red")):
        active = (
            (color == "green" and mode == "READY")
            or (color == "amber" and mode == "BUSY")
            or (color == "red" and mode not in {"READY", "BUSY"})
        )
        light = _part(
            "ControlCabinet/StackLight/" + color,
            (-1.85, -1.1, 1.06 + index * 0.065),
            (0.065, 0.065, 0.055),
            color if active else "graphite",
            parent="ControlCabinet",
            primitive="cylinder",
            tags=("stack_light", "dynamic"),
        )
        parts.append(light)
    for index, x in enumerate(
        (rack_x - rack_width / 2 + 0.025, rack_x + rack_width / 2 - 0.025), 1
    ):
        parts.append(
            _part(
                f"ToolRack/Leg{index}",
                (x, 0, 0.15),
                (0.04, 0.66, 0.30),
                "graphite",
                parent="ToolRack",
                tags=("rack_forbidden",),
            )
        )
    for index, y in enumerate((-0.40, 0.40), 1):
        parts.append(
            _part(
                f"ToolRack/Rail{index}",
                (rack_x, y, 0.735),
                (rack_width, 0.025, 0.035),
                "metal",
                parent="ToolRack",
                tags=("rack_forbidden",),
            )
        )
    tools = data["tools"]
    state = world.get("tool_state", {})
    active_id = state.get("active_tool_id", tools[0]["tool_id"])
    rack_ids = state.get(
        "rack_tool_ids", [tool["tool_id"] for tool in tools if tool["tool_id"] != active_id]
    )
    for index, tool in enumerate(tools, 1):
        ident = tool["tool_id"]
        dock = layout["tool_docks"][ident]
        dock_tcp = _v(dock["position"])
        dock_name = f"ToolRack/Dock{index:02}"
        parts.append(
            _part(
                dock_name,
                _add(dock_tcp, (0, 0, 0.115)),
                (0.10, 0.10, 0.025),
                "accent",
                parent="ToolRack",
                label=str(index),
                tags=("tool_dock", "intentional_contact"),
            )
        )
        parts.append(
            _part(
                dock_name + "/Post",
                _add(dock_tcp, (0, 0.13, -0.0175)),
                (0.025, 0.025, 0.315),
                "graphite",
                parent=dock_name,
                tags=("rack_forbidden",),
            )
        )
        parts.append(
            _part(
                dock_name + "/CouplingArm",
                _add(dock_tcp, (0, 0.065, 0.125)),
                (0.035, 0.13, 0.025),
                "metal",
                parent=dock_name,
                tags=("tool_dock", "intentional_contact"),
            )
        )
        tool_parts = tool_primitives(
            ident,
            tcp if ident == active_id else dock_tcp,
            tool_yaw if ident == active_id else 0.0,
            parent_name="Robot/ToolChanger" if ident == active_id else dock_name,
            grasp_width_m=state.get("grasp_width_m"),
            grip_amount=state.get("grip_amount", 0.0) if ident == active_id else 0,
        )
        for part in tool_parts:
            part["visible"] = ident == active_id or ident in rack_ids
        parts.extend(tool_parts)
    parts.extend(_products(world, data["products"]))
    for spec in data["products"]:
        sku = spec["sku"]
        source = layout["sources"][sku]
        for parent, support, height in (
            (
                "Locations/" + source["location_id"],
                source["pose"]["position"],
                source.get("product_support_offset_m", 0),
            ),
            (
                "Locations/" + destination["location_id"],
                _add(destination["pose"]["position"], (*layout["destination_slots"][sku][:2], 0)),
                layout["destination_slots"][sku][2],
            ),
        ):
            if height <= 0:
                continue
            for index, dx in enumerate((-0.14, 0.14) if sku == "SKU-F" else (0,), 1):
                parts.append(
                    _part(
                        parent + f"/SupportSkid-{sku}-{index}",
                        _add(support, (dx, 0, height / 2)),
                        (0.04, 0.022, height) if sku == "SKU-F" else (0.055, 0.045, height),
                        "rubber",
                        parent=parent,
                        tags=("product_support", "intentional_contact"),
                    )
                )
    # Rear portal leaves an opening for the destination conveyor.
    for index, (x, y) in enumerate(
        (
            (-2.1, -1.85),
            (2.1, -1.85),
            (-2.1, 1.85),
            (2.1, 1.85),
            (-0.70, 1.85),
            (0.70, 1.85),
            (-0.53, -1.85),
            (0.53, -1.85),
        ),
        1,
    ):
        parts.append(
            _part(
                f"Enclosure/Post{index:02}",
                (x, y, 1),
                (0.06, 0.06, 2),
                "metal",
                tags=("enclosure",),
            )
        )
    for name, position, size in (
        ("Left", (-2.1, 0, 1.05), (0.012, 3.64, 1.7)),
        ("Right", (2.1, 0, 1.05), (0.012, 3.64, 1.7)),
        ("RearLeft", (-1.4, 1.85, 1.05), (1.34, 0.012, 1.7)),
        ("RearRight", (1.4, 1.85, 1.05), (1.34, 0.012, 1.7)),
        ("FrontLeft", (-1.315, -1.85, 1.05), (1.51, 0.012, 1.7)),
        ("FrontRight", (1.315, -1.85, 1.05), (1.51, 0.012, 1.7)),
        ("OperatorGate", (0, -1.85, 1.05), (1.0, 0.012, 1.7)),
    ):
        parts.append(
            _part(
                "Enclosure/" + name,
                position,
                size,
                "enclosure",
                opacity=0.12,
                tags=("enclosure", "gate") if name == "OperatorGate" else ("enclosure",),
                label="OPERATOR GATE" if name == "OperatorGate" else None,
            )
        )
    for camera, spec in zip(camera_views(data), data["cameras"], strict=True):
        if camera["role"] == "PRESENTATION":
            continue
        name = camera["name"]
        pose = spec["pose"]
        parts.append(
            _part(
                name + "/Housing",
                pose["position"],
                (0.16, 0.10, 0.085),
                "graphite",
                quaternion=pose["quaternion_xyzw"],
                tags=("synthetic_camera",),
                label=camera["sensor_id"],
            )
        )
        cx, cy, cz = pose["position"]
        if "Overhead" in name:
            parts.append(
                _part(
                    name + "/Crossbar",
                    (-1.075, cy, cz + 0.075),
                    (2.15, 0.045, 0.045),
                    "metal",
                    parent=name + "/Housing",
                )
            )
            cx = -2.15
        parts.append(
            _part(
                name + "/Support",
                (cx, cy, cz / 2),
                (0.035, 0.035, cz),
                "metal",
                parent=name + "/Housing",
            )
        )
    return parts
