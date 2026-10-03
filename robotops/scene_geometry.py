"""Shared synthetic cell meshes for Blender and read-only 3D presentation.

Standard library only: the fixed Blender script imports this same geometry.
This is a stylized Cartesian machine, not validated robot kinematics.
"""

from typing import Any


def cell_meshes(world: dict[str, Any]) -> list[dict[str, Any]]:
    meshes: list[dict[str, Any]] = []

    def box(name: str, position: Any, size: Any, color: Any, **labels: str) -> None:
        meshes.append(dict(name=name, position=position, size=size, color=color, **labels))

    steel = (0.18, 0.5, 0.62)
    light = (0.3, 0.65, 0.72)
    gold = (0.85, 0.65, 0.17)
    box("RobotOpsTwin/Cell", (0, 0, -0.05), (2.7, 1.8, 0.1), (0.12, 0.18, 0.23))
    box("Robot", (-1.15, 0.5, 0.65), (0.14, 0.18, 1.3), steel)
    box("RobotSupport", (1.15, 0.5, 0.65), (0.14, 0.18, 1.3), steel)
    box("RobotCrossrail", (0, 0.5, 1.3), (2.45, 0.18, 0.16), steel)
    box("RobotCarriage", (0, 0.5, 1.3), (0.24, 0.24, 0.24), light)
    box("RobotArm", (0, 0.2, 1.18), (0.14, 0.85, 0.12), steel)
    box("RobotSpindle", (0, 0, 1.325), (0.06, 0.06, 1.05), light)
    box("Gripper", (0, 0, 0.8), (0.2, 0.15, 0.09), gold)
    box("GripperLeft", (-0.095, 0, 0.74), (0.025, 0.13, 0.14), gold)
    box("GripperRight", (0.095, 0, 0.74), (0.025, 0.13, 0.14), gold)
    box("ControlCabinet", (-1.1, -0.58, 0.23), (0.25, 0.26, 0.46), steel)
    for i, loc in enumerate(world["locations"]):
        x, y, _ = loc["pose"]["position"]
        name = "SourceTote" if i == 0 else "DestinationTote"
        box(
            name,
            (x, y, 0.04),
            (0.55, 0.65, 0.08),
            (0.2, 0.32, 0.38),
            location_id=loc["location_id"],
        )
        for j, (dx, dy, sx, sy) in enumerate(
            [
                (-0.28, 0, 0.025, 0.65),
                (0.28, 0, 0.025, 0.65),
                (0, -0.33, 0.56, 0.025),
                (0, 0.33, 0.56, 0.025),
            ]
        ):
            box(name + f"Wall{j}", (x + dx, y + dy, 0.11), (sx, sy, 0.15), (0.3, 0.45, 0.52))
    colors = [(0.76, 0.19, 0.15), (0.15, 0.38, 0.72), (0.22, 0.62, 0.3)]
    for i, item in enumerate(world["objects"]):
        ident = item["product"]["product_id"]
        box(
            "Products/" + ident,
            item["pose"]["position"],
            (0.13, 0.13, 0.13),
            colors[i % 3],
            product_id=ident,
            location_id=item["location_id"],
        )
    return meshes
