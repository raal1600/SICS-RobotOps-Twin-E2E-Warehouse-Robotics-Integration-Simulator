"""Read-only, non-authorizing explanations computed from saved sensor evidence."""

import base64
from typing import Literal

import cv2
import numpy as np

from robotops.calibration.artifacts import SensorArtifacts
from robotops.calibration.contracts import (
    CalibrationArtifact,
    Capture,
    Limits,
    PointFailure,
    PointMeasurement,
    Record,
    Vec2,
)
from robotops.calibration.depth import reconstruct
from robotops.calibration.errors import CalibrationError
from robotops.calibration.perception import red_cube_top, reference_center
from robotops.calibration.registration import align_native_depth
from robotops.calibration.visualization import axes, segment


class DepthDisplay(Record):
    scope: str = "Display only; raw sensor units, not calibrated distances or a validity decision"
    low_raw: float | None
    high_raw: float | None
    valid_pixels: int
    invalid_pixels: int
    quantiles: tuple[float, float] = (0.01, 0.99)
    quantile_method: Literal["linear"] = "linear"
    colors: str = "Turbo: dark blue to red; values outside the display range are clipped; magenta is nonfinite or nonpositive"


def depth_display(raw: np.ndarray) -> DepthDisplay:
    valid = np.isfinite(raw) & (raw > 0)
    low, high = (
        np.quantile(raw[valid], [0.01, 0.99], method="linear") if valid.any() else (None, None)
    )
    return DepthDisplay(
        low_raw=float(low) if low is not None else None,
        high_raw=float(high) if high is not None else None,
        valid_pixels=int(valid.sum()),
        invalid_pixels=int(raw.size - valid.sum()),
    )


def depth_preview(raw: np.ndarray) -> np.ndarray:
    """Same display scale for saved-capture and pixel-inspection previews; never alters raw data."""
    display = depth_display(raw)
    valid = np.isfinite(raw) & (raw > 0)
    preview = np.zeros(raw.shape, dtype=np.uint8)
    if display.low_raw is not None and display.high_raw is not None:
        preview[valid] = np.clip(
            (raw[valid] - display.low_raw) / max(display.high_raw - display.low_raw, 1) * 255,
            0,
            255,
        ).astype(np.uint8)
    colored = cv2.applyColorMap(preview, cv2.COLORMAP_TURBO)
    colored[~valid] = (255, 0, 255)
    return colored


def inspect_pixel(
    capture: Capture,
    artifact: CalibrationArtifact,
    limits: Limits,
    files: SensorArtifacts,
    pixel: Vec2,
    mode: Literal["native", "aligned"],
) -> dict[str, object]:
    """No active lifecycle or physical-world input: this explanation cannot authorize a target.

    Historical inspection deliberately names the selected artifact, independently of
    today's approval. All raw bytes remain hash-checked and configurations must match.
    """
    camera = artifact.candidate.camera
    if (
        capture.camera_id != camera.camera_id
        or capture.configuration_fingerprint != camera.fingerprint()
    ):
        raise CalibrationError("CAPTURE_ARTIFACT_CONFIGURATION_MISMATCH")
    if artifact.candidate.limits_fingerprint != limits.fingerprint():
        raise CalibrationError("LIMITS_CHANGED")
    if not capture.admitted:
        raise CalibrationError("CAPTURE_NOT_ADMITTED", ", ".join(capture.rejection_codes))
    raw = files.read_depth(capture.depth)
    rgb_source = files.read_rgb(capture.rgb)
    mask = None
    # Same declared visual codes as the runtime. Never infer a surface from depth
    # alone to make an ambiguous association pass.
    for identify in (red_cube_top, reference_center):
        try:
            _, found = identify(rgb_source)
            px, py = (int(round(value)) for value in pixel)
            if 0 <= px < camera.rgb.width and 0 <= py < camera.rgb.height and found[py, px]:
                mask = found
                break
        except CalibrationError:
            continue
    alignment = align_native_depth(raw, camera, capture.capture_id) if mode == "aligned" else None
    result: PointMeasurement | PointFailure
    try:
        result = reconstruct(
            pixel,
            raw,
            camera,
            artifact.candidate.x,
            limits,
            alignment=alignment,
            rgb_surface_mask=mask,
        )
    except CalibrationError as error:
        result = PointFailure(
            code=error.code,
            detail=error.detail,
            camera_id=camera.camera_id,
            selected_rgb_pixel=pixel,
        )
    matrix = np.array(artifact.candidate.x.matrix)
    overlay = axes("Inspection/estimated-camera-c", matrix)
    if isinstance(result, PointMeasurement):
        depth_origin = (matrix @ np.array(camera.t_c_d.matrix))[:3, 3]
        point = np.array(result.point)
        overlay.append(
            segment("Inspection/native-depth-ray", depth_origin, point, (1, 0.8, 0.22), 0.004)
        )
        overlay += axes(
            "Inspection/reconstructed-point-b",
            np.array([[1, 0, 0, point[0]], [0, 1, 0, point[1]], [0, 0, 1, point[2]], [0, 0, 0, 1]]),
            0.025,
        )
    rgb = cv2.cvtColor(rgb_source, cv2.COLOR_RGB2BGR)
    if 0 <= pixel[0] < camera.rgb.width and 0 <= pixel[1] < camera.rgb.height:
        cv2.drawMarker(
            rgb, tuple(int(round(value)) for value in pixel), (0, 230, 255), cv2.MARKER_CROSS, 22, 2
        )
    depth = depth_preview(raw)
    if isinstance(result, PointMeasurement):
        cv2.drawMarker(depth, result.native_depth_pixel, (0, 230, 255), cv2.MARKER_CROSS, 18, 2)

    def encoded(image: np.ndarray) -> str:
        ok, data = cv2.imencode(".png", image)
        if not ok:
            raise CalibrationError("EVIDENCE_PREVIEW_ENCODING_FAILED")
        return "data:image/png;base64," + base64.b64encode(data).decode("ascii")

    return {
        "scope": "READ_ONLY_RECOMPUTATION; saved image + explicitly selected artifact; no grasp or execution authorization",
        "capture_id": capture.capture_id,
        "camera_id": camera.camera_id,
        "artifact_id": artifact.artifact_id,
        "configuration_fingerprint": camera.fingerprint(),
        "mode": mode,
        "result": result.model_dump(mode="json"),
        "alignment": alignment.metadata.model_dump(mode="json") if alignment else None,
        "rgb_preview": encoded(rgb),
        "depth_preview": encoded(depth),
        "depth_display": depth_display(raw).model_dump(mode="json"),
        "overlay_scope": "Estimated camera frame and reconstructed ray from the selected saved evidence; physical sensors are unchanged",
        "overlay": [obj.model_dump(mode="json") for obj in overlay],
    }
