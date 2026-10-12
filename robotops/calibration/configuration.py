"""Public, measurable configuration for the synthetic calibration rig (no extrinsic truth)."""

from typing import cast

import cv2
import numpy as np

from robotops.calibration.contracts import Board, Camera, Frame, Matrix4, Stream, Transform
from robotops.calibration.geometry import Array, rigid


def framed(matrix: Array, source: Frame, destination: Frame) -> Transform:
    value = rigid(matrix)
    return Transform(
        source=source,
        destination=destination,
        matrix=cast(Matrix4, tuple(tuple(float(v) for v in row) for row in value)),
    )


def default_board() -> Board:
    return Board(
        corner_ids=tuple(range(24)),
        corners_m=tuple(
            ((x + 1) * 0.045, (y + 1) * 0.045, 0.0) for y in range(4) for x in range(6)
        ),
    )


def charuco_board(board: Board, marker_ids: tuple[int, ...] = ()) -> cv2.aruco.CharucoBoard:
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
    return cv2.aruco.CharucoBoard(
        (board.squares_x, board.squares_y),
        board.square_length_m,
        board.marker_length_m,
        dictionary,
        np.asarray(marker_ids, dtype=np.int32) if marker_ids else None,
    )


def default_camera(camera_id: str) -> Camera:
    rgb = Stream(
        width=960,
        height=720,
        k=((950, 0, 479.5), (0, 950, 359.5), (0, 0, 1)),
        verification="SIMULATION_ONLY_FACTORY_MODEL",
    )
    depth = Stream(
        width=640,
        height=480,
        k=((635, 0, 319.5), (0, 635, 239.5), (0, 0, 1)),
        verification="SIMULATION_ONLY_FACTORY_MODEL",
    )
    registration = np.eye(4)
    registration[0, 3] = 0.055
    return Camera(
        camera_id=camera_id,
        profile_id="rgb960-depth640-native-1",
        configuration_revision="configuration-1",
        rgb=rgb,
        depth=depth,
        depth_scale_m=0.001,
        depth_semantics="optical_z",
        t_c_d=framed(registration, "d", "c"),
    )
