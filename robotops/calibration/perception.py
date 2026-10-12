"""Explicitly limited image segmentation, not universal object recognition.

The default synthetic reference fixture has one purple circular patch per image.
This function receives pixels only. Runtime object identification will use an equally
declared visual code; no API here accepts world poses or camera extrinsics.
"""

from typing import Literal

import cv2
import numpy as np
from numpy.typing import NDArray

from robotops.calibration.artifacts import SensorArtifacts
from robotops.calibration.contracts import SurfaceDetection, Vec2
from robotops.calibration.errors import CalibrationError


def identify_surface(
    capture_id: str,
    camera_id: str,
    rgb: NDArray[np.uint8],
    method: Literal["reference_center", "red_cube_top"],
    files: SensorArtifacts,
) -> SurfaceDetection:
    """Persist the exact image-only mask used by correspondence; arrays remain hash-referenced."""
    identify = {"reference_center": reference_center, "red_cube_top": red_cube_top}.get(method)
    if identify is None:
        raise CalibrationError("UNSUPPORTED_SURFACE_DETECTOR")
    pixel, mask = identify(rgb)
    return SurfaceDetection(
        capture_id=capture_id,
        camera_id=camera_id,
        method=method,
        selected_rgb_pixel=pixel,
        mask=files.mask(mask),
        selected_pixel_count=int(mask.sum()),
    )


def reference_center(rgb: NDArray[np.uint8]) -> tuple[Vec2, NDArray[np.bool_]]:
    if rgb.ndim != 3 or rgb.shape[2] != 3 or rgb.dtype != np.uint8:
        raise CalibrationError("INVALID_RGB_ARRAY")
    mask = (rgb[:, :, 0] > 180) & (rgb[:, :, 1] < 70) & (rgb[:, :, 2] > 150)
    count, _, statistics, centers = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
    components = [index for index in range(1, count) if statistics[index, cv2.CC_STAT_AREA] >= 20]
    if len(components) != 1:
        raise CalibrationError("REFERENCE_NOT_UNIQUELY_IDENTIFIED")
    center = centers[components[0]]
    return (float(center[0]), float(center[1])), mask


def red_cube_top(rgb: NDArray[np.uint8]) -> tuple[Vec2, NDArray[np.bool_]]:
    """One declared red top patch. Sides have a different intensity; no world lookup."""
    mask = (rgb[:, :, 0] > 180) & (rgb[:, :, 1] < 80) & (rgb[:, :, 2] < 80)
    count, _, statistics, centers = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
    candidates = [index for index in range(1, count) if statistics[index, cv2.CC_STAT_AREA] >= 40]
    if len(candidates) != 1:
        raise CalibrationError(
            "PRODUCT_NOT_UNIQUELY_IDENTIFIED", "Expected one declared red cube top patch"
        )
    center = centers[candidates[0]]
    return (float(center[0]), float(center[1])), mask


def visible_fixture_codes(rgb: NDArray[np.uint8]) -> tuple[str, ...]:
    """Recognize the declared source/destination top codes from actual visible pixels."""
    green = (rgb[:, :, 0] < 80) & (rgb[:, :, 1] > 170)
    source = green & (rgb[:, :, 2] < 100)
    destination = green & (rgb[:, :, 2] > 170)
    return tuple(
        name
        for name, mask in (("source", source), ("destination", destination))
        if np.count_nonzero(mask) >= 50
    )
