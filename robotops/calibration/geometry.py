"""Frame-explicit SE(3) and camera geometry shared by API, CLI and sensor adapters.

Matrices map source to destination; lengths are meters and angles radians.
Optical axes are right/down/forward; robot base is right/away/up. Browser/Blender
base coordinates remain right/away/up. A Three.js y-up display uses the proper
rotation (x,y,z)_display=(x,z,-y)_base, never an implicit optical-frame swap.
"""

from collections.abc import Sequence

import cv2
import numpy as np
from numpy.typing import NDArray
from scipy.spatial.transform import Rotation

from robotops.calibration.errors import CalibrationError

Array = NDArray[np.float64]


def rigid(value: Sequence[Sequence[float]] | Array) -> Array:
    matrix = np.asarray(value, dtype=np.float64)
    if matrix.shape != (4, 4) or not np.isfinite(matrix).all():
        raise CalibrationError("INVALID_RIGID_TRANSFORM", "Expected a finite 4x4 matrix")
    rotation = matrix[:3, :3]
    if not np.allclose(matrix[3], [0, 0, 0, 1], atol=1e-8, rtol=0):
        raise CalibrationError("INVALID_HOMOGENEOUS_ROW")
    if not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-7, rtol=0):
        raise CalibrationError("NON_ORTHONORMAL_ROTATION")
    if not np.isclose(np.linalg.det(rotation), 1, atol=1e-7, rtol=0):
        raise CalibrationError("IMPROPER_ROTATION")
    return matrix.copy()


def transform(rotation: Array, translation: Sequence[float] | Array) -> Array:
    matrix = np.eye(4, dtype=np.float64)
    matrix[:3, :3] = rotation
    matrix[:3, 3] = translation
    return rigid(matrix)


def inverse(value: Sequence[Sequence[float]] | Array) -> Array:
    matrix = rigid(value)
    return transform(matrix[:3, :3].T, -matrix[:3, :3].T @ matrix[:3, 3])


def points(value: Sequence[Sequence[float]] | Array, coordinates: Array) -> Array:
    matrix = rigid(value)
    coords = np.asarray(coordinates, dtype=np.float64)
    if coords.ndim != 2 or coords.shape[1] != 3 or not np.isfinite(coords).all():
        raise CalibrationError("INVALID_POINT_ARRAY")
    return coords @ matrix[:3, :3].T + matrix[:3, 3]


def from_xyzw(position: Sequence[float], quaternion_xyzw: Sequence[float]) -> Array:
    q = np.asarray(quaternion_xyzw, dtype=np.float64)
    if q.shape != (4,) or not np.isfinite(q).all() or abs(np.linalg.norm(q) - 1) > 1e-7:
        raise CalibrationError("INVALID_XYZW_QUATERNION")
    return transform(Rotation.from_quat(q).as_matrix(), position)


def residual(left: Array, right: Array) -> tuple[float, float]:
    """Translation norm in meters and relative rotation angle in radians, separately."""
    a, b = rigid(left), rigid(right)
    return (
        float(np.linalg.norm(a[:3, 3] - b[:3, 3])),
        float(Rotation.from_matrix(a[:3, :3].T @ b[:3, :3]).magnitude()),
    )


def rigid_mean(values: Sequence[Array], weights: Sequence[float] | None = None) -> Array:
    """Weighted chordal SO(3) mean projected by SVD, plus weighted translation.

    This is a rigid product-manifold fit, not an elementwise 4x4 matrix average.
    Its objective is sum w*(||R-R_i||_F^2 + ||t-t_i||^2); because the two variables
    decouple, no mixed-unit scalar is used to accept a calibration.
    """
    if not values:
        raise CalibrationError("NO_TRANSFORMS")
    matrices = np.stack([rigid(value) for value in values])
    w = np.ones(len(values)) if weights is None else np.asarray(weights, dtype=np.float64)
    if w.shape != (len(values),) or not np.isfinite(w).all() or (w <= 0).any():
        raise CalibrationError("INVALID_FIT_WEIGHTS")
    w = w / np.sum(w)
    u, _, vt = np.linalg.svd(np.einsum("n,nij->ij", w, matrices[:, :3, :3]))
    correction = np.diag([1.0, 1.0, float(np.linalg.det(u @ vt))])
    return transform(u @ correction @ vt, np.einsum("n,ni->i", w, matrices[:, :3, 3]))


def undistort(pixels: Array, k: Array, coefficients: Array, model: str) -> Array:
    pixels = np.asarray(pixels, dtype=np.float64).reshape(-1, 1, 2)
    k, coefficients = np.asarray(k, dtype=np.float64), np.asarray(coefficients, dtype=np.float64)
    if not np.isfinite(pixels).all():
        raise CalibrationError("INVALID_PIXEL")
    if model == "pinhole":
        result = cv2.undistortPoints(pixels, k, coefficients if coefficients.size else None)
    elif model == "fisheye" and coefficients.size == 4:
        result = cv2.fisheye.undistortPoints(pixels, k, coefficients)
    else:
        raise CalibrationError("UNSUPPORTED_DISTORTION_MODEL")
    return np.asarray(result, dtype=np.float64).reshape(-1, 2)


def project(coordinates: Array, k: Array, coefficients: Array, model: str) -> Array:
    coords = np.asarray(coordinates, dtype=np.float64).reshape(-1, 1, 3)
    k, coefficients = np.asarray(k, dtype=np.float64), np.asarray(coefficients, dtype=np.float64)
    if not np.isfinite(coords).all() or (coords[:, 0, 2] <= 0).any():
        raise CalibrationError("NON_POSITIVE_CAMERA_DEPTH")
    if model == "pinhole":
        projected, _ = cv2.projectPoints(
            coords, np.zeros(3), np.zeros(3), k, coefficients if coefficients.size else None
        )
    elif model == "fisheye" and coefficients.size == 4:
        projected, _ = cv2.fisheye.projectPoints(coords, np.zeros(3), np.zeros(3), k, coefficients)
    else:
        raise CalibrationError("UNSUPPORTED_DISTORTION_MODEL")
    return np.asarray(projected, dtype=np.float64).reshape(-1, 2)


def point_rms(residuals: Array) -> float:
    values = np.asarray(residuals, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != 2 or not len(values) or not np.isfinite(values).all():
        raise CalibrationError("INVALID_PIXEL_RESIDUALS")
    return float(np.sqrt(np.sum(values * values) / len(values)))
