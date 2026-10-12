"""Presentation-only metric geometry. Never imported by estimation/planning/verification.

Both browser renderers use z-up base coordinates directly. Optical right/down/forward
axes are transformed explicitly by supplied matrices. No fitting moves the physical
camera geometry; estimates and instructor/world references remain separate layers.
"""

from functools import lru_cache
from typing import cast

import cv2
import numpy as np
from scipy.spatial.transform import Rotation

from robotops.blender.visualization import VisualCamera, VisualObject
from robotops.calibration.configuration import charuco_board
from robotops.calibration.contracts import Board, Camera
from robotops.calibration.geometry import Array, from_xyzw, undistort
from robotops.domain.models import WorldState


def _box(
    name: str,
    position: Array,
    size: tuple[float, float, float],
    color: tuple[float, float, float],
    rotation: Array | None = None,
    **metadata: object,
) -> VisualObject:
    return VisualObject.model_validate(
        {
            "schema_version": "3.0",
            "name": name,
            "position": position.tolist(),
            "size": size,
            "color": color,
            "primitive": "box",
            "quaternion_xyzw": Rotation.from_matrix(rotation).as_quat().tolist()
            if rotation is not None
            else [0, 0, 0, 1],
            "scale": [1, 1, 1],
            "visible": True,
            "opacity": 1,
            **metadata,
        }
    )


def segment(
    name: str, start: Array, end: Array, color: tuple[float, float, float], radius: float = 0.003
) -> VisualObject:
    delta = end - start
    length = float(np.linalg.norm(delta))
    direction = delta / length
    z = np.array([0.0, 0.0, 1.0])
    cross = np.cross(z, direction)
    if np.linalg.norm(cross) < 1e-10:
        rotation = np.eye(3) if direction[2] > 0 else np.diag([1, -1, -1])
    else:
        rotation = Rotation.from_rotvec(
            cross / np.linalg.norm(cross) * np.arccos(np.clip(z @ direction, -1, 1))
        ).as_matrix()
    return _box(name, (start + end) / 2, (radius, radius, length), color, rotation)


def axes(name: str, matrix: Array, length: float = 0.10) -> list[VisualObject]:
    origin = matrix[:3, 3]
    result = [_box(f"{name}/origin", origin, (0.008, 0.008, 0.008), (0.9, 0.9, 0.9))]
    for index, (letter, color) in enumerate(
        (("x", (0.9, 0.3, 0.2)), ("y", (0.3, 0.85, 0.4)), ("z", (0.3, 0.55, 1.0)))
    ):
        result.append(
            segment(f"{name}/{letter}", origin, origin + matrix[:3, index] * length, color)
        )
    return result


@lru_cache(maxsize=8)
def printed_markers(
    board_json: str,
    marker_ids: tuple[int, ...] = (),
) -> tuple[tuple[str, tuple[float, float, float], tuple[float, float, float]], ...]:
    """Exact dictionary bits/metric marker positions used by the RGB board renderer.

    Merge horizontal black runs to keep geometry bounded. These are printed marks,
    not detected image corners or evidence of successful calibration.
    """
    board = Board.model_validate_json(board_json)
    definition = charuco_board(board, marker_ids)
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
    output = []
    cell = board.marker_length_m / 6
    for identity, corners in zip(definition.getIds(), definition.getObjPoints(), strict=True):
        bitmap = cv2.aruco.generateImageMarker(dictionary, int(identity), 6)
        origin = corners[0]
        for row in range(6):
            column = 0
            while column < 6:
                if bitmap[row, column] != 0:
                    column += 1
                    continue
                start = column
                while column < 6 and bitmap[row, column] == 0:
                    column += 1
                output.append(
                    (
                        f"Board/marker-{int(identity)}-{row}-{start}",
                        (
                            float(origin[0] + (start + column) * cell / 2),
                            float(origin[1] + (row + 0.5) * cell),
                            -0.0012,
                        ),
                        ((column - start) * cell, cell, 0.0002),
                    )
                )
    return tuple(output)


def cell_geometry(
    world: WorldState,
    board: Board,
    physical_cameras: dict[str, Array],
    physical_mount: Array,
    cameras: dict[str, Camera],
    marker_ids: tuple[int, ...] = (),
) -> tuple[list[VisualObject], list[VisualCamera]]:
    machine = world.calibration_machine
    if machine is None:
        raise ValueError("CALIBRATION_MACHINE_REQUIRED")
    objects = [
        _box("Gantry/base", np.array([0, 0.32, 0.05]), (0.9, 0.15, 0.1), (0.28, 0.35, 0.40)),
        _box("Gantry/beam", np.array([0, 0.32, 1.05]), (0.9, 0.09, 0.09), (0.4, 0.48, 0.53)),
        _box(
            "Gantry/left-column", np.array([-0.4, 0.32, 0.55]), (0.07, 0.07, 1), (0.28, 0.35, 0.40)
        ),
        _box(
            "Gantry/right-column", np.array([0.4, 0.32, 0.55]), (0.07, 0.07, 1), (0.28, 0.35, 0.40)
        ),
    ]
    flange = np.asarray(machine.flange.matrix)
    tcp = np.asarray(machine.tcp.matrix)
    objects += [
        segment(
            "Gantry/z-slide",
            np.array([flange[0, 3], flange[1, 3], 1.05]),
            flange[:3, 3],
            (0.5, 0.58, 0.64),
            0.025,
        ),
        _box(
            "Robot/ToolChanger",
            flange[:3, 3],
            (0.055, 0.055, 0.03),
            (0.8, 0.82, 0.84),
            flange[:3, :3],
        ),
        segment("Robot/tool-shaft", flange[:3, 3], tcp[:3, 3], (0.35, 0.4, 0.44), 0.018),
        _box(
            "Robot/ActiveTool",
            tcp[:3, 3],
            (0.045, 0.045, 0.008),
            (0.18, 0.8, 0.67),
            tcp[:3, :3],
            label="TCP",
        ),
    ]
    objects += axes("Base b", np.eye(4)) + axes("Flange f", flange, 0.06) + axes("TCP", tcp, 0.06)
    for location, color in zip(
        world.locations, ((0.16, 0.78, 0.27), (0.16, 0.78, 0.78)), strict=True
    ):
        position = np.array([*location.pose.position[:2], 0.155])
        objects.append(
            _box(
                f"Fixture/{location.location_id}",
                position,
                (0.16, 0.16, 0.31),
                color,
                location_id=location.location_id,
                label=location.location_id,
            )
        )
    for obj in world.objects:
        matrix = from_xyzw(obj.pose.position, obj.pose.quaternion_xyzw)
        objects.append(
            _box(
                f"Product/{obj.product.product_id}",
                matrix[:3, 3],
                (0.08, 0.08, 0.08),
                (0.88, 0.16, 0.14),
                matrix[:3, :3],
                product_id=obj.product.product_id,
                location_id=obj.location_id,
                label="Cube",
            )
        )
    if machine.board_mounted:
        board_pose = flange @ physical_mount
        for row in range(board.squares_y):
            for column in range(board.squares_x):
                center = board_pose @ np.array(
                    [
                        (column + 0.5) * board.square_length_m,
                        (row + 0.5) * board.square_length_m,
                        0,
                        1,
                    ]
                )
                shade = 0.95 if (row + column) % 2 else 0.06
                objects.append(
                    _box(
                        f"Board/square-{row}-{column}",
                        center[:3],
                        (board.square_length_m, board.square_length_m, 0.002),
                        (shade, shade, shade),
                        board_pose[:3, :3],
                    )
                )
        for name, local, size in printed_markers(board.model_dump_json(), marker_ids):
            center = board_pose @ np.array([*local, 1])
            objects.append(_box(name, center[:3], size, (0.015, 0.015, 0.015), board_pose[:3, :3]))
        objects += axes("Removable board t", board_pose, 0.08)
    viewpoints = [
        VisualCamera(
            name="Camera/OperatorOverview",
            position=(1.55, -2.5, 1.7),
            target=(0, -0.15, 0.8),
            role="PRESENTATION",
            frame_id="b",
            calibration_version="presentation-only",
            camera_model_version="operator-orbit",
        )
    ]
    for index, (identity, physical) in enumerate(physical_cameras.items()):
        camera = cameras[identity]
        objects.append(
            _box(
                f"Sensor/{identity}",
                physical[:3, 3],
                (0.11, 0.045, 0.045),
                (0.45, 0.5, 0.56),
                physical[:3, :3],
                label=identity.removeprefix("camera-").capitalize(),
            )
        )
        objects += axes(f"{identity}/c · optical", physical, 0.12)
        pixels = np.array(
            [
                [0, 0],
                [camera.rgb.width - 1, 0],
                [camera.rgb.width - 1, camera.rgb.height - 1],
                [0, camera.rgb.height - 1],
            ],
            dtype=float,
        )
        normalized = undistort(
            pixels,
            np.asarray(camera.rgb.k),
            np.asarray(camera.rgb.coefficients),
            camera.rgb.distortion_model,
        )
        end_points = np.column_stack((normalized, np.ones(4))) * 0.38
        end_points = end_points @ physical[:3, :3].T + physical[:3, 3]
        for j, endpoint in enumerate(end_points):
            objects.append(
                segment(f"Sensor/{identity}/ray-{j}", physical[:3, 3], endpoint, (0.2, 0.65, 0.7))
            )
            objects.append(
                segment(
                    f"Sensor/{identity}/image-edge-{j}",
                    endpoint,
                    end_points[(j + 1) % 4],
                    (0.2, 0.65, 0.7),
                )
            )
        viewpoints.append(
            VisualCamera(
                name="Camera/" + ("OverheadObservation" if index == 0 else "SideInspection"),
                position=cast(tuple[float, float, float], tuple(physical[:3, 3].tolist())),
                target=cast(
                    tuple[float, float, float], tuple((physical[:3, 3] + physical[:3, 2]).tolist())
                ),
                role="SYNTHETIC_SENSOR",
                sensor_id=identity,
                frame_id=f"{identity}:c",
                calibration_version="physical-simulator-placement",
                camera_model_version=camera.profile_id,
            )
        )
    return objects, viewpoints
