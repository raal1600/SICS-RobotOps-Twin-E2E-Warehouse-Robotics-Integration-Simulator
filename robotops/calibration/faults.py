"""Explicit, reproducible sensor-output faults at the synthetic hardware boundary.

These functions alter actual measured arrays, never a fitted transform or a target.
The catalogue describes the injected cause for a presenter. Diagnostics receive the
resulting measurements and must not treat this instructor label as measured proof.
"""

import hashlib
from typing import Literal

import cv2
import numpy as np
from numpy.typing import NDArray

from robotops.calibration.contracts import Camera, Id, Record
from robotops.calibration.geometry import undistort

FaultKind = Literal[
    "depth_scale",
    "range_as_z",
    "depth_registration",
    "depth_zero",
    "depth_nonfinite",
    "depth_mixed",
    "depth_occluded",
    "units_1000",
    "rgb_crop",
    "sensor_noise",
    "rgb_corner_warp",
    "tool_translation",
    "tool_rotation",
    "restore_sensor",
    "restore_tool",
    "model_focal",
    "model_profile",
    "model_crop",
    "model_resize",
    "model_distortion",
    "restore_model",
    "board_remount",
    "board_dimensions",
    "restore_board_dimensions",
    "board_marker_ids",
    "restore_board_print",
    "missing_reference_limit",
    "restore_limits",
]


class FaultDefinition(Record):
    kind: FaultKind
    label: str
    description: str
    affected: Literal["sensor", "tool", "configuration", "board", "limits"]
    next_action: str


class FaultRecord(Record):
    fault_id: Id
    camera_id: Id
    definition: FaultDefinition
    scope: Literal["ISOLATED_SIMULATION_FAULT"] = "ISOLATED_SIMULATION_FAULT"


def catalogue() -> tuple[FaultDefinition, ...]:
    sensor_rows: tuple[tuple[FaultKind, str, str], ...] = (
        (
            "depth_scale",
            "Depth scale +8%",
            "Multiply native depth returns by 1.08 while leaving the declared scale unchanged.",
        ),
        (
            "range_as_z",
            "Radial range reported as axial depth",
            "Report ray length where the camera configuration still declares optical-axis Z.",
        ),
        (
            "depth_registration",
            "RGB/depth registration shifted",
            "Shift native depth returns 14 columns; vacated columns are missing, not wrapped.",
        ),
        (
            "depth_zero",
            "Missing depth: zero returns",
            "Replace all native depth returns with zero. No valid point may be substituted.",
        ),
        (
            "depth_nonfinite",
            "Missing depth: non-finite returns",
            "Replace all native depth returns with NaN. Raw NPY preserves the missing values.",
        ),
        (
            "depth_mixed",
            "Mixed foreground/background returns",
            "Alternate native returns and a surface 80 mm farther away in adjacent pixels.",
        ),
        (
            "depth_occluded",
            "Depth sensor obscured",
            "A simulated cover produces a near surface at 250 mm in the depth stream; RGB remains unobscured.",
        ),
        (
            "units_1000",
            "Meters/millimeters confusion",
            "Multiply native returns by 1000 without changing the declared measurement units.",
        ),
        (
            "rgb_crop",
            "Undeclared RGB crop and resize",
            "Crop 32 pixels from every RGB edge and resize back; keep the old K to demonstrate its inapplicability.",
        ),
        (
            "sensor_noise",
            "Increased measurement noise",
            "Add seeded 12 mm depth noise and 8-level RGB noise, exceeding the nominal measurement budget.",
        ),
        (
            "rgb_corner_warp",
            "Distort board corner readings",
            "Warp RGB column readout near the image center by up to 12 pixels with a 22-pixel Gaussian spread. Actual image features move; the physical board, depth and declared optics stay unchanged. Inspect rejected or excluded measured corners.",
        ),
        (
            "restore_sensor",
            "Restore nominal sensor output",
            "Remove the selected camera's output fault. Existing suspect approval stays blocked.",
        ),
    )
    result = [
        FaultDefinition(
            kind=kind,
            label=label,
            description=description,
            affected="sensor",
            next_action="Measure routine references and inspect the images. Restore the sensor, then collect new calibration and unused validation measurements.",
        )
        for kind, label, description in sensor_rows
    ]
    tool_rows: tuple[tuple[FaultKind, str, str], ...] = (
        (
            "tool_translation",
            "Tool tip moved 15 mm",
            "Change the physical tool tip along flange z; leave its configured TCP unchanged.",
        ),
        (
            "tool_rotation",
            "Tool axes rotated",
            "Rotate the physical tool by 0.04 radians about flange x; leave the configured tool axes unchanged.",
        ),
        (
            "restore_tool",
            "Restore the indexed tool",
            "Restore the original synthetic tool geometry; independent tool verification is still required.",
        ),
    )
    for kind, label, description in tool_rows:
        result.append(
            FaultDefinition(
                kind=kind,
                label=label,
                description=description,
                affected="tool",
                next_action="Run independent tool verification. A tool fault does not change or recalibrate the camera transform.",
            )
        )
    model_rows: tuple[tuple[FaultKind, str, str], ...] = (
        (
            "model_focal",
            "Wrong configured focal length",
            "Increase the declared RGB focal lengths by 10%; physical optics and generated pixels stay unchanged.",
        ),
        (
            "model_profile",
            "Wrong configured stream profile",
            "Declare an unsupported profile identity while the physical streams keep their original profile.",
        ),
        (
            "model_crop",
            "Wrong configured RGB crop",
            "Declare a 32-pixel crop without a matching physical stream profile.",
        ),
        (
            "model_resize",
            "Wrong configured depth resize",
            "Declare half-size depth resizing without a matching active physical profile.",
        ),
        (
            "model_distortion",
            "Wrong distortion model",
            "Declare fisheye RGB optics for this physical pinhole camera.",
        ),
        (
            "restore_model",
            "Restore nominal camera configuration",
            "Restore the declared factory camera configuration; retain blocked old approval for audit.",
        ),
    )
    for kind, label, description in model_rows:
        result.append(
            FaultDefinition(
                kind=kind,
                label=label,
                description=description,
                affected="configuration",
                next_action="Record the changed model and inspect its optical verification. Restore an applicable model before new installation measurements and approval.",
            )
        )
    board_rows: tuple[tuple[FaultKind, str, str], ...] = (
        (
            "board_marker_ids",
            "Print the wrong board marker IDs",
            "Replace the physical marker patterns with dictionary IDs 17 through 33. The declared board still expects IDs 0 through 16. Dimensions, camera placement and board mounting stay fixed.",
        ),
        (
            "restore_board_print",
            "Restore the documented board print",
            "Restore the actual marker patterns to the declared board. This changes images and saved presentation geometry, but cannot restore approval.",
        ),
        (
            "board_remount",
            "Remount the calibration board",
            "Move the physical board mounting 8 mm and rotate it 0.02 radians. Record a new mounting identity for both cameras; the physical cameras stay fixed.",
        ),
        (
            "board_dimensions",
            "Wrong declared board dimensions",
            "Increase declared board dimensions by 8% while keeping the physical printed board unchanged. Image residual alone cannot establish metric scale.",
        ),
        (
            "restore_board_dimensions",
            "Restore measured board dimensions",
            "Restore the original metric board specification while retaining the current mounting identity. Old approval stays blocked.",
        ),
    )
    for kind, label, description in board_rows:
        result.append(
            FaultDefinition(
                kind=kind,
                label=label,
                description=description,
                affected="board",
                next_action="Both cameras share this board. Record its changed specification, collect new images, validate independently and explicitly approve each new candidate. A board change is not proof of camera movement.",
            )
        )
    for kind, label, description in (
        (
            "missing_reference_limit",
            "Remove required reference tolerance",
            "Remove the selected camera's maximum reference-error limit. Existing approval is blocked; no acceptance threshold may be guessed from the measurements.",
        ),
        (
            "restore_limits",
            "Restore documented simulation limits",
            "Restore the original frozen simulation-only error budget. This does not restore approval: independent validation and explicit approval are still required.",
        ),
    ):
        result.append(
            FaultDefinition(
                kind=kind,
                label=label,
                description=description,
                affected="limits",
                next_action="Restore the documented simulation limits, then measure or revalidate a compatible saved estimate. Do not tune limits against failed validation data.",
            )
        )
    return tuple(result)


def definition(kind: FaultKind) -> FaultDefinition:
    return next(item for item in catalogue() if item.kind == kind)


def sensor_output(
    fault: FaultRecord | None,
    camera: Camera,
    rgb: NDArray[np.uint8],
    depth: NDArray[np.float32],
    capture_id: str,
) -> tuple[NDArray[np.uint8], NDArray[np.float32]]:
    if fault is None or fault.definition.kind == "restore_sensor":
        return rgb, depth
    kind = fault.definition.kind
    depth, rgb = depth.copy(), rgb.copy()
    if kind == "depth_scale":
        depth *= 1.08
    elif kind == "units_1000":
        depth *= 1000
    elif kind == "range_as_z":
        v, u = np.indices(depth.shape)
        q = undistort(
            np.column_stack((u.ravel(), v.ravel())).astype(float),
            np.asarray(camera.depth.k),
            np.asarray(camera.depth.coefficients),
            camera.depth.distortion_model,
        )
        norm = np.sqrt(np.sum(q**2, axis=1) + 1).reshape(depth.shape)
        depth *= (
            norm.astype(np.float32)
            if camera.depth_semantics == "optical_z"
            else (1 / norm).astype(np.float32)
        )
    elif kind == "depth_registration":
        depth[:, 14:] = depth[:, :-14].copy()
        depth[:, :14] = np.nan
    elif kind == "depth_zero":
        depth.fill(0)
    elif kind == "depth_nonfinite":
        depth.fill(np.nan)
    elif kind == "depth_mixed":
        v, u = np.indices(depth.shape)
        depth[(u + v) % 2 == 0] += 0.08 / camera.depth_scale_m
    elif kind == "depth_occluded":
        depth.fill(0.25 / camera.depth_scale_m)
    elif kind == "rgb_crop":
        rgb = np.asarray(
            cv2.resize(rgb[32:-32, 32:-32], (camera.rgb.width, camera.rgb.height)), dtype=np.uint8
        )
    elif kind == "sensor_noise":
        seed = int.from_bytes(
            hashlib.sha256(f"{fault.fault_id}/{capture_id}".encode()).digest()[:8], "little"
        )
        rng = np.random.default_rng(seed)
        depth += rng.normal(0, 0.012 / camera.depth_scale_m, depth.shape).astype(np.float32)
        rgb = np.clip(rgb.astype(float) + rng.normal(0, 8, rgb.shape), 0, 255).astype(np.uint8)
    elif kind == "rgb_corner_warp":
        warp_grid = np.indices(rgb.shape[:2], dtype=np.float32)
        row_map = np.asarray(warp_grid[0], dtype=np.float32)
        column_map = np.asarray(warp_grid[1], dtype=np.float32)
        displacement = 12 * np.exp(
            -((column_map - camera.rgb.width / 2) ** 2 + (row_map - camera.rgb.height / 2) ** 2)
            / (2 * 22**2)
        )
        rgb = np.asarray(
            cv2.remap(rgb, column_map + displacement, row_map, cv2.INTER_LINEAR), dtype=np.uint8
        )
    return rgb, depth
