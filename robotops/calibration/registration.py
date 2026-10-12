"""Documented alignment adapter retaining native depth meaning and provenance.

RGB-grid values are copied native Z or native radial range, never relabelled RGB Z.
Native data and a per-pixel native index map are retained for conservative visibility
and neighbourhood checks. Hole filling/interpolation is deliberately unsupported.
"""

import hashlib
from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from robotops.calibration.contracts import Camera, Id, Record, Vec2
from robotops.calibration.depth import deproject
from robotops.calibration.errors import CalibrationError
from robotops.calibration.geometry import points, project


class AlignmentMetadata(Record):
    capture_id: Id
    camera_configuration_fingerprint: str
    algorithm: Literal["native-z-buffer-with-index-map-1"] = "native-z-buffer-with-index-map-1"
    value_semantics: Literal["native_optical_z", "native_radial_range"]
    native_sha256: str
    aligned_sha256: str
    native_index_map_sha256: str
    hole_policy: Literal["NaN; never filled or used as a target"] = (
        "NaN; never filled or used as a target"
    )


@dataclass(frozen=True)
class RegisteredDepth:
    metadata: AlignmentMetadata
    values: NDArray[np.float32]
    native_pixels: NDArray[np.int32]


def array_hash(array: np.ndarray) -> str:
    header = f"{array.dtype.str}:{array.shape}:".encode()
    return hashlib.sha256(header + np.ascontiguousarray(array).tobytes()).hexdigest()


def align_native_depth(
    native_raw: NDArray[np.float32], camera: Camera, capture_id: str
) -> RegisteredDepth:
    """Project every valid native return, retain the closest RGB-z surface and index.

    Z-buffer selection is registration, not permission to grasp an ambiguous edge.
    Reconstruction still uses the complete original native data and rejects ambiguity.
    """
    expected = "native_" + camera.depth_semantics
    if camera.registration == "aligned_documented" and camera.aligned_semantics != expected:
        raise CalibrationError(
            "UNSUPPORTED_ALIGNED_DEPTH_SEMANTICS",
            "This adapter preserves native Z/range and requires its native index map",
        )
    if native_raw.dtype != np.float32 or native_raw.shape != (
        camera.depth.height,
        camera.depth.width,
    ):
        raise CalibrationError("NATIVE_DEPTH_PROFILE_MISMATCH")
    v, u = np.indices(native_raw.shape)
    pixels = np.column_stack((u.ravel(), v.ravel()))
    depth = native_raw.astype(np.float64).ravel() * camera.depth_scale_m
    indices = np.flatnonzero(
        np.isfinite(depth) & (depth >= camera.min_depth_m) & (depth <= camera.max_depth_m)
    )
    pc = (
        points(
            camera.t_c_d.matrix,
            deproject(pixels[indices].astype(np.float64), depth[indices], camera),
        )
        if len(indices)
        else np.empty((0, 3))
    )
    forward = pc[:, 2] > 0
    pc, indices = pc[forward], indices[forward]
    projected = (
        project(
            pc,
            np.asarray(camera.rgb.k),
            np.asarray(camera.rgb.coefficients),
            camera.rgb.distortion_model,
        )
        if len(pc)
        else np.empty((0, 2))
    )
    rounded = np.rint(projected).astype(np.int64)
    inside = (
        (rounded[:, 0] >= 0)
        & (rounded[:, 0] < camera.rgb.width)
        & (rounded[:, 1] >= 0)
        & (rounded[:, 1] < camera.rgb.height)
    )
    indices, pc, projected, rounded = (
        indices[inside],
        pc[inside],
        projected[inside],
        rounded[inside],
    )
    flat_rgb = rounded[:, 1] * camera.rgb.width + rounded[:, 0]
    # Deterministic tie order: RGB index, nearest RGB Z, centre distance, native index.
    order = np.lexsort((indices, np.linalg.norm(projected - rounded, axis=1), pc[:, 2], flat_rgb))
    ordered = flat_rgb[order]
    first = np.r_[True, ordered[1:] != ordered[:-1]] if len(order) else np.zeros(0, dtype=bool)
    chosen = order[first]
    values = np.full((camera.rgb.height, camera.rgb.width), np.nan, dtype=np.float32)
    mapping = np.full((*values.shape, 2), -1, dtype=np.int32)
    values.ravel()[flat_rgb[chosen]] = native_raw.ravel()[indices[chosen]]
    mapping.reshape(-1, 2)[flat_rgb[chosen]] = pixels[indices[chosen]]
    metadata = AlignmentMetadata(
        capture_id=capture_id,
        camera_configuration_fingerprint=camera.fingerprint(),
        value_semantics="native_optical_z"
        if camera.depth_semantics == "optical_z"
        else "native_radial_range",
        native_sha256=array_hash(native_raw),
        aligned_sha256=array_hash(values),
        native_index_map_sha256=array_hash(mapping),
    )
    values.setflags(write=False)
    mapping.setflags(write=False)
    return RegisteredDepth(metadata, values, mapping)


def validate_alignment(
    selected_rgb: Vec2, native_raw: NDArray[np.float32], camera: Camera, aligned: RegisteredDepth
) -> tuple[int, int]:
    """Validate the actual arrays, profile, declared meaning and selected correspondence."""
    if (
        aligned.metadata.camera_configuration_fingerprint != camera.fingerprint()
        or (
            camera.registration == "aligned_documented"
            and aligned.metadata.value_semantics != camera.aligned_semantics
        )
        or aligned.metadata.value_semantics != "native_" + camera.depth_semantics
    ):
        raise CalibrationError("ALIGNED_CONFIGURATION_MISMATCH")
    expected_shape = (camera.rgb.height, camera.rgb.width)
    if (
        aligned.values.shape != expected_shape
        or aligned.values.dtype != np.float32
        or aligned.native_pixels.shape != (*expected_shape, 2)
        or aligned.native_pixels.dtype != np.int32
    ):
        raise CalibrationError("ALIGNED_ARRAY_CONTRACT_MISMATCH")
    if (
        array_hash(native_raw) != aligned.metadata.native_sha256
        or array_hash(aligned.values) != aligned.metadata.aligned_sha256
        or array_hash(aligned.native_pixels) != aligned.metadata.native_index_map_sha256
    ):
        raise CalibrationError("ALIGNED_ARRAY_HASH_MISMATCH")
    x, y = np.rint(selected_rgb).astype(int)
    if not (0 <= x < camera.rgb.width and 0 <= y < camera.rgb.height):
        raise CalibrationError("RGB_PIXEL_OUT_OF_BOUNDS")
    raw = float(aligned.values[y, x])
    nx, ny = (int(value) for value in aligned.native_pixels[y, x])
    if not np.isfinite(raw) or raw <= 0 or nx < 0 or ny < 0:
        raise CalibrationError("ALIGNED_DEPTH_HOLE")
    if nx >= camera.depth.width or ny >= camera.depth.height or raw != float(native_raw[ny, nx]):
        raise CalibrationError("ALIGNED_NATIVE_VALUE_MISMATCH")
    return nx, ny
