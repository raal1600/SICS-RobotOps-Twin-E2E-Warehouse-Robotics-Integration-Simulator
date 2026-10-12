"""Native depth correspondence and deprojection. No world/object-pose dependency.

`reconstruct` is a non-authorizing numerical operation used during validation.
Operational `pixel_to_base` additionally requires an approved artifact and a current
applicability decision from the lifecycle service. A rejected result has no point.
"""

from typing import TYPE_CHECKING, cast

import cv2
import numpy as np
from numpy.typing import NDArray

from robotops.calibration.contracts import (
    Calculation,
    CalibrationArtifact,
    Camera,
    Limits,
    PointFailure,
    PointMeasurement,
    Transform,
    Vec2,
    Vec3,
)
from robotops.calibration.errors import CalibrationError
from robotops.calibration.geometry import Array, points, project, undistort

if TYPE_CHECKING:
    from robotops.calibration.registration import RegisteredDepth


def deproject(native_pixels: Array, measured_depth_m: Array, camera: Camera) -> Array:
    normalized = undistort(
        native_pixels,
        np.asarray(camera.depth.k),
        np.asarray(camera.depth.coefficients),
        camera.depth.distortion_model,
    )
    rays = np.column_stack((normalized, np.ones(len(normalized))))
    if camera.depth_semantics == "radial_range":
        rays /= np.linalg.norm(rays, axis=1)[:, None]
    return rays * measured_depth_m[:, None]


def reconstruct(
    selected_rgb_pixel: Vec2,
    depth_raw: NDArray[np.float32],
    camera: Camera,
    x: Transform,
    limits: Limits,
    *,
    rgb_surface_mask: NDArray[np.bool_] | None = None,
    native_pixel: tuple[int, int] | None = None,
    alignment: "RegisteredDepth | None" = None,
) -> PointMeasurement:
    """Conservative native-depth association, including z-buffer and 3x3 surface checks.

    A supplied native pixel is still projected into RGB and checked; identical pixel
    indices never imply a match. An RGB-derived surface mask, when supplied, prevents
    accepting rays across the identified object's boundary. No invalid depth filling.
    Documented aligned input additionally supplies a hashed index map and original
    native values for visibility/support checks. Aligned values are never assumed RGB Z.
    """
    if camera.registration != "native" and alignment is None:
        raise CalibrationError(
            "ALIGNED_NATIVE_MAPPING_REQUIRED",
            "Provide native pixels and their measurement semantics through the registration adapter",
        )
    if (x.source, x.destination) != ("c", "b"):
        raise CalibrationError("CAMERA_EXTRINSIC_FRAME_DIRECTION")
    pixel = np.asarray(selected_rgb_pixel, dtype=np.float64)
    if (
        pixel.shape != (2,)
        or not np.isfinite(pixel).all()
        or (pixel < 0).any()
        or pixel[0] >= camera.rgb.width
        or pixel[1] >= camera.rgb.height
    ):
        raise CalibrationError("RGB_PIXEL_OUT_OF_BOUNDS")
    if depth_raw.shape != (camera.depth.height, camera.depth.width):
        raise CalibrationError("NATIVE_DEPTH_PROFILE_MISMATCH")
    if alignment is not None:
        from robotops.calibration.registration import validate_alignment

        mapped_pixel = validate_alignment(selected_rgb_pixel, depth_raw, camera, alignment)
        if native_pixel is not None and native_pixel != mapped_pixel:
            raise CalibrationError("ALIGNED_NATIVE_INDEX_MISMATCH")
        native_pixel = mapped_pixel
    if rgb_surface_mask is not None:
        if rgb_surface_mask.shape != (camera.rgb.height, camera.rgb.width):
            raise CalibrationError("RGB_SURFACE_MASK_MISMATCH")
        px, py = np.rint(pixel).astype(int)
        if px >= camera.rgb.width or py >= camera.rgb.height or not rgb_surface_mask[py, px]:
            raise CalibrationError("RGB_SURFACE_NOT_IDENTIFIED")
    v, u = np.indices(depth_raw.shape)
    native_pixels = np.column_stack((u.ravel(), v.ravel())).astype(np.float64)
    depths = depth_raw.astype(np.float64).ravel() * camera.depth_scale_m
    valid = np.isfinite(depths) & (depths >= camera.min_depth_m) & (depths <= camera.max_depth_m)
    if native_pixel is not None:
        nx, ny = native_pixel
        if not (0 <= nx < camera.depth.width and 0 <= ny < camera.depth.height):
            raise CalibrationError("NATIVE_PIXEL_OUT_OF_BOUNDS")
        if not valid[ny * camera.depth.width + nx]:
            raise CalibrationError("INVALID_SELECTED_DEPTH", repr(float(depth_raw[ny, nx])))
    if not valid.any():
        raise CalibrationError("NO_VALID_DEPTH")
    indices = np.flatnonzero(valid)
    pd = deproject(native_pixels[valid], depths[valid], camera)
    pc = points(camera.t_c_d.matrix, pd)
    forward = pc[:, 2] > 0
    indices, pd, pc = indices[forward], pd[forward], pc[forward]
    if len(pc) == 0:
        raise CalibrationError("DEPTH_NOT_VISIBLE_IN_RGB")
    projected = project(
        pc,
        np.asarray(camera.rgb.k),
        np.asarray(camera.rgb.coefficients),
        camera.rgb.distortion_model,
    )
    distances = np.linalg.norm(projected - pixel, axis=1)
    nearby = np.flatnonzero(distances <= limits.max_correspondence_error_px)
    if len(nearby) == 0:
        raise CalibrationError("NO_RGB_DEPTH_CORRESPONDENCE")
    occluded_count = 0
    if np.ptp(pc[nearby, 2]) > limits.max_depth_surface_spread_m:
        # RGB can see an opaque foreground patch while the displaced depth sensor
        # sees background rays behind it. Resolve only well inside an identified RGB
        # surface with multiple foreground returns; object edges remain ambiguous.
        if rgb_surface_mask is None:
            raise CalibrationError(
                "OCCLUDED_OR_MIXED_DEPTH", "Multiple surfaces project near the selected RGB pixel"
            )
        interior_distance = cv2.distanceTransform(rgb_surface_mask.astype(np.uint8), cv2.DIST_L2, 3)
        px, py = np.rint(pixel).astype(int)
        if interior_distance[py, px] <= 2 * limits.max_correspondence_error_px:
            raise CalibrationError(
                "OCCLUDED_OR_MIXED_DEPTH", "Selected pixel is too close to a surface boundary"
            )
        front = nearby[pc[nearby, 2] <= np.min(pc[nearby, 2]) + limits.max_depth_surface_spread_m]
        occluded_count = len(nearby) - len(front)
        nearby = front
    if native_pixel is None:
        chosen = int(nearby[np.argmin(distances[nearby])])
    else:
        matches = np.flatnonzero(indices == native_pixel[1] * camera.depth.width + native_pixel[0])
        if len(matches) != 1 or matches[0] not in nearby:
            raise CalibrationError("NATIVE_RGB_CORRESPONDENCE_MISMATCH")
        chosen = int(matches[0])
    # Reject isolated/sparse associations, not just one convenient background return.
    if len(nearby) < 2:
        raise CalibrationError("AMBIGUOUS_DEPTH_ASSOCIATION")
    index = int(indices[chosen])
    nx, ny = int(index % camera.depth.width), int(index // camera.depth.width)
    if nx < 1 or ny < 1 or nx >= camera.depth.width - 1 or ny >= camera.depth.height - 1:
        raise CalibrationError("DEPTH_EDGE_WITHOUT_SUPPORT")
    neighborhood = (
        depth_raw[ny - 1 : ny + 2, nx - 1 : nx + 2].astype(np.float64) * camera.depth_scale_m
    )
    if (
        not np.isfinite(neighborhood).all()
        or (neighborhood < camera.min_depth_m).any()
        or (neighborhood > camera.max_depth_m).any()
    ):
        raise CalibrationError("INVALID_DEPTH_NEIGHBORHOOD")
    if np.ptp(neighborhood) > limits.max_depth_surface_spread_m:
        raise CalibrationError("MIXED_FOREGROUND_BACKGROUND_DEPTH")
    if rgb_surface_mask is not None:
        projected_pixels = np.rint(projected[nearby]).astype(int)
        for rx, ry in projected_pixels:
            if (
                not (0 <= rx < camera.rgb.width and 0 <= ry < camera.rgb.height)
                or not rgb_surface_mask[ry, rx]
            ):
                raise CalibrationError("OBJECT_EDGE_CORRESPONDENCE")
    p_base = points(x.matrix, pc[chosen : chosen + 1])[0]
    normalized = undistort(
        np.array([[nx, ny]], dtype=np.float64),
        np.asarray(camera.depth.k),
        np.asarray(camera.depth.coefficients),
        camera.depth.distortion_model,
    )[0]
    result = cast(Vec3, tuple(float(value) for value in p_base))
    trace = Calculation(
        function="robotops.calibration.depth.reconstruct",
        formula="q=[xn,yn,1]; p_d=Z*q or r*q/||q||; p_c=T_c_d*p_d; p_b=X*p_c",
        inputs={
            "selected_rgb_pixel": selected_rgb_pixel,
            "native_depth_pixel": [nx, ny],
            "raw_depth_value": float(depth_raw[ny, nx]),
            "depth_scale_m": camera.depth_scale_m,
            "depth_semantics": camera.depth_semantics,
            "k_d": camera.depth.k,
            "distortion_model": camera.depth.distortion_model,
            "distortion_coefficients": camera.depth.coefficients,
            **({"alignment": alignment.metadata.model_dump(mode="json")} if alignment else {}),
            "t_c_d": camera.t_c_d.model_dump(mode="json"),
            "x": x.model_dump(mode="json"),
        },
        outputs={
            "normalized_ray": [*normalized.tolist(), 1.0],
            "p_d_m": pd[chosen].tolist(),
            "p_c_m": pc[chosen].tolist(),
            "p_b_m": list(result),
            "projected_rgb_pixel": projected[chosen].tolist(),
            "correspondence_error_px": float(distances[chosen]),
            "support_count": len(nearby),
            "occluded_background_returns": occluded_count,
            "visibility_assumption": "Opaque RGB-identified interior surface"
            if rgb_surface_mask is not None
            else "Single unambiguous surface",
        },
        decision="VALID_POINT_ONLY; no grasp or execution authorization implied",
    )
    return PointMeasurement(
        point=result,
        camera_id=camera.camera_id,
        configuration_fingerprint=camera.fingerprint(),
        transform_fingerprint=x.fingerprint(),
        selected_rgb_pixel=selected_rgb_pixel,
        native_depth_pixel=(nx, ny),
        raw_depth_value=float(depth_raw[ny, nx]),
        calculation=trace,
    )


def pixel_to_base(
    selected_rgb_pixel: Vec2,
    depth_raw: NDArray[np.float32],
    camera: Camera,
    artifact: CalibrationArtifact | None,
    limits: Limits,
    *,
    active_valid: bool,
    rgb_surface_mask: NDArray[np.bool_] | None = None,
    native_pixel: tuple[int, int] | None = None,
    alignment: "RegisteredDepth | None" = None,
) -> PointMeasurement | PointFailure:
    try:
        if artifact is None:
            raise CalibrationError("APPROVED_CALIBRATION_REQUIRED")
        if not active_valid:
            raise CalibrationError("ACTIVE_CALIBRATION_SUSPECT")
        if artifact.candidate.camera.fingerprint() != camera.fingerprint():
            raise CalibrationError("ACTIVE_CONFIGURATION_MISMATCH")
        if artifact.candidate.limits_fingerprint != limits.fingerprint():
            raise CalibrationError("LIMITS_CHANGED")
        return reconstruct(
            selected_rgb_pixel,
            depth_raw,
            camera,
            artifact.candidate.x,
            limits,
            rgb_surface_mask=rgb_surface_mask,
            native_pixel=native_pixel,
            alignment=alignment,
        )
    except CalibrationError as error:
        return PointFailure(
            code=error.code,
            detail=error.detail,
            camera_id=camera.camera_id,
            selected_rgb_pixel=selected_rgb_pixel,
        )
