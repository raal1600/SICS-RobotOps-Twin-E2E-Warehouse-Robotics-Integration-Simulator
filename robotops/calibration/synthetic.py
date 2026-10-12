"""Sensor-generation and test-oracle boundary. Never imported by estimation or target code.

This analytic Python renderer intersects camera rays with metric board/floor surfaces.
It produces images, not precomputed detections. Pixel centers, distortion and native
depth baselines use the declared per-stream models. Physical extrinsics remain here.
The gantry/gimbal rig is synthetic; these poses do not assert HKM inverse kinematics.
"""

import hashlib
from dataclasses import dataclass
from typing import Literal

import cv2
import numpy as np
from numpy.typing import NDArray
from scipy.spatial.transform import Rotation

from robotops.calibration.artifacts import SensorArtifacts
from robotops.calibration.configuration import charuco_board, default_board, default_camera, framed
from robotops.calibration.contracts import (
    Camera,
    Capture,
    Limits,
    ReferenceBatch,
    ReferenceCapture,
    Stream,
    Transform,
)
from robotops.calibration.errors import CalibrationError
from robotops.calibration.geometry import Array, inverse, points, transform, undistort
from robotops.calibration.geometry import project as optical_project
from robotops.calibration.optics import OpticalReference


@dataclass(frozen=True)
class SensorNoise:
    intensity_sigma: float = 0.4
    depth_sigma_m: float = 0.0003
    robot_translation_sigma_m: float = 0.00005
    robot_rotation_sigma_rad: float = 0.00005


@dataclass(frozen=True)
class PhysicalBox:
    """Private renderer input. Never returned in sensor observations."""

    t_b_object: Array
    size_m: tuple[float, float, float]
    top_rgb: tuple[int, int, int]


def _look_at(position: Array, target: Array) -> Array:
    forward = target - position
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, [0, 0, 1])
    right /= np.linalg.norm(right)
    down = np.cross(forward, right)
    return transform(np.column_stack((right, down, forward)), position)


def _rays(stream: Stream) -> Array:
    v, u = np.indices((stream.height, stream.width))
    pixels = np.column_stack((u.ravel(), v.ravel())).astype(np.float64)
    normalized = undistort(
        pixels, np.asarray(stream.k), np.asarray(stream.coefficients), stream.distortion_model
    )
    return np.column_stack((normalized, np.ones(len(normalized))))


class SyntheticSensorWorld:
    """Owns hidden geometry. Public output is capture/configuration, never B_i or truth X/Y."""

    def __init__(self, seed: int, artifacts: SensorArtifacts, noise: SensorNoise | None = None):
        self.seed = seed
        self.artifacts = artifacts
        self.noise = noise or SensorNoise()
        self.board = default_board()
        self._physical_board = self.board
        self.cameras = {key: default_camera(key) for key in ("camera-west", "camera-east")}
        # Physical optics stay independent of the application's declared model.
        # These public intrinsic specifications are not the hidden installation X/Y.
        self._factory_models = dict(self.cameras)
        rng = np.random.default_rng(seed)
        self._physical_cameras = {
            "camera-west": _look_at(
                np.array([-0.55, -0.75, 1.6]) + rng.normal(0, 0.03, 3), np.array([0.0, 0.0, 0.48])
            ),
            "camera-east": _look_at(
                np.array([0.62, -0.65, 1.52]) + rng.normal(0, 0.03, 3), np.array([0.0, 0.0, 0.48])
            ),
        }
        w, h = self._physical_board.measured_dimensions_m
        self._physical_mount = transform(
            Rotation.from_euler("x", np.pi).as_matrix(), [-w / 2, h / 2, 0.035]
        )
        self._texture = charuco_board(self._physical_board).generateImage(
            (1400, 1000), marginSize=0
        )
        self._printing_marker_ids: tuple[int, ...] = ()
        self._ray_cache: dict[str, Array] = {}

    def planned_poses(self, partition: str, count: int = 18) -> tuple[Transform, ...]:
        """Reproducible bounded gantry/gimbal poses, not random reward exploration.

        Distinct deterministic sequences for fit/final validation/routine checks.
        Rig bounds: x/y +/-0.3 m, z 0.3..0.8 m, tilt <=30 degrees per axis.
        These are commanded flange inputs, not calibration answers.
        """
        if partition not in ("fit", "validation", "routine") or count < 1 or count > 100:
            raise CalibrationError("INVALID_CAPTURE_PLAN")
        offset = {"fit": 0, "validation": 113, "routine": 227}[partition]
        result = []
        for i in range(count):
            phase = float(i + offset)
            position = [
                0.17 * np.sin(phase * 2.399),
                0.16 * np.cos(phase * 1.618),
                0.5 + 0.13 * np.sin(phase * 1.37),
            ]
            rotation = Rotation.from_euler(
                "xyz",
                [
                    0.36 * np.sin(phase * 1.17 + 0.3),
                    0.36 * np.cos(phase * 1.79),
                    0.40 * np.sin(phase * 2.11),
                ],
            ).as_matrix()
            result.append(framed(transform(rotation, position), "f", "b"))
        return tuple(result)

    def sensor_output(
        self, camera: Camera, rgb: NDArray[np.uint8], depth: NDArray[np.float32], capture_id: str
    ) -> tuple[NDArray[np.uint8], NDArray[np.float32]]:
        return rgb, depth

    def sensor_fault_ids(self, camera_id: str) -> tuple[str, ...]:
        return ()

    def optical_references(self, camera_id: str) -> tuple[OpticalReference, ...]:
        """A separate synthetic factory fixture, not installation-board PnP answers.

        Independently surveyed target points are camera-local factory metrology inputs.
        Actual pixel measurements are generated by the physical optics model, with
        deterministic readout noise. This fixture never reads the installed X or Y.
        """
        physical = self._factory_models[camera_id]
        points_m = np.array(
            [
                (x * z, y * z, z)
                for z in (0.7, 1.1, 1.5)
                for y in np.linspace(-0.32, 0.32, 5)
                for x in np.linspace(-0.44, 0.44, 7)
            ]
        )
        result = []
        for name, stream, frame in (("rgb", physical.rgb, "c"), ("depth", physical.depth, "d")):
            identity = f"optical-{self.seed}-{camera_id}-{name}"
            seed = int.from_bytes(hashlib.sha256(identity.encode()).digest()[:8], "little")
            measured = optical_project(
                points_m,
                np.asarray(stream.k),
                np.asarray(stream.coefficients),
                stream.distortion_model,
            )
            measured += np.random.default_rng(seed).normal(0, 0.08, measured.shape)
            result.append(
                OpticalReference.model_validate(
                    {
                        "measurement_id": identity,
                        "camera_id": camera_id,
                        "profile_id": physical.profile_id,
                        "stream": name,
                        "optical_frame": frame,
                        "width": stream.width,
                        "height": stream.height,
                        "crop_xy": stream.crop_xy,
                        "resize_xy": stream.resize_xy,
                        "optical_points_m": points_m.tolist(),
                        "measured_pixels_px": measured.tolist(),
                    }
                )
            )
        return tuple(result)

    def _stream_rays(self, stream: Stream) -> Array:
        key = stream.fingerprint()
        if key not in self._ray_cache:
            self._ray_cache[key] = _rays(stream)
        return self._ray_cache[key]

    def _surfaces(
        self, stream: Stream, t_b_sensor: Array, t_b_board: Array
    ) -> tuple[Array, Array, NDArray[np.bool_]]:
        rays = self._stream_rays(stream)
        t_sensor_board = inverse(t_b_sensor) @ t_b_board
        normal = t_sensor_board[:3, 2]
        denom = rays @ normal
        scale = np.divide(
            normal @ t_sensor_board[:3, 3],
            denom,
            out=np.full(len(rays), np.inf),
            where=np.abs(denom) > 1e-10,
        )
        board_points = points(
            inverse(t_sensor_board), rays * np.where(np.isfinite(scale), scale, 0)[:, None]
        )
        w, h = self._physical_board.measured_dimensions_m
        visible = (
            (scale > 0)
            & np.isfinite(scale)
            & (board_points[:, 0] >= 0)
            & (board_points[:, 0] <= w)
            & (board_points[:, 1] >= 0)
            & (board_points[:, 1] <= h)
        )
        # Base floor z=0 is a genuinely different, farther surface.
        world_rays = rays @ t_b_sensor[:3, :3].T
        floor_scale = np.divide(
            -t_b_sensor[2, 3],
            world_rays[:, 2],
            out=np.full(len(rays), np.nan),
            where=world_rays[:, 2] < -1e-10,
        )
        visible &= (scale < floor_scale) | ~np.isfinite(floor_scale)
        distances = np.where(visible, scale, floor_scale)
        return distances, board_points, visible

    def _render(
        self, camera: Camera, flange: Array, rng: np.random.Generator
    ) -> tuple[NDArray[np.uint8], NDArray[np.float32]]:
        camera = self._factory_models[camera.camera_id]
        physical = self._physical_cameras[camera.camera_id]
        board_pose = flange @ self._physical_mount
        _, local, visible = self._surfaces(camera.rgb, physical, board_pose)
        w, h = self._physical_board.measured_dimensions_m
        map_x = (local[:, 0] / w * self._texture.shape[1] - 0.5).astype(np.float32)
        map_y = (local[:, 1] / h * self._texture.shape[0] - 0.5).astype(np.float32)
        image_shape = (camera.rgb.height, camera.rgb.width)
        texture = cv2.remap(
            self._texture,
            map_x.reshape(image_shape),
            map_y.reshape(image_shape),
            cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=255,
        )
        rgb = np.full((*image_shape, 3), (70, 80, 90), dtype=np.uint8)
        rgb[visible.reshape(image_shape)] = texture[visible.reshape(image_shape), None]
        rgb = np.clip(
            rgb.astype(np.float64) + rng.normal(0, self.noise.intensity_sigma, rgb.shape), 0, 255
        ).astype(np.uint8)
        z, _, _ = self._surfaces(
            camera.depth, physical @ np.asarray(camera.t_c_d.matrix), board_pose
        )
        if camera.depth_semantics == "radial_range":
            z *= np.linalg.norm(self._stream_rays(camera.depth), axis=1)
        z += rng.normal(0, self.noise.depth_sigma_m, z.shape)
        depth = (
            (z / camera.depth_scale_m)
            .reshape(camera.depth.height, camera.depth.width)
            .astype(np.float32)
        )
        return rgb, depth

    def acquire(
        self,
        camera_id: str,
        flange: Transform,
        dataset_id: str,
        index: int,
        partition: Literal["fit", "validation", "routine"],
        limits: Limits,
        *,
        settled: bool = True,
        timestamp_skew_s: float = 0,
    ) -> Capture:
        if (flange.source, flange.destination) != ("f", "b"):
            raise CalibrationError("FLANGE_FRAME_DIRECTION")
        camera = self.cameras[camera_id]
        # Seed is a function of immutable capture identity; retries reproduce the same bytes.
        capture_id = f"{dataset_id}-{camera_id}-{index:03d}"
        seed_bytes = hashlib.sha256(f"{self.seed}/{capture_id}".encode()).digest()
        rng = np.random.default_rng(int.from_bytes(seed_bytes[:8], "little"))
        physical_flange = np.asarray(flange.matrix)
        rgb, depth = self._render(camera, physical_flange, rng)
        rgb, depth = self.sensor_output(self._factory_models[camera_id], rgb, depth, capture_id)
        report_error = transform(
            Rotation.from_rotvec(rng.normal(0, self.noise.robot_rotation_sigma_rad, 3)).as_matrix(),
            rng.normal(0, self.noise.robot_translation_sigma_m, 3),
        )
        reported = framed(physical_flange @ report_error, "f", "b")
        rejection = []
        if not settled:
            rejection.append("ROBOT_NOT_SETTLED")
        if abs(timestamp_skew_s) > limits.max_timestamp_skew_s:
            rejection.append("TIMESTAMP_MISMATCH")
        timestamp = 1_800_000_000.0 + index
        return Capture(
            capture_id=capture_id,
            dataset_id=dataset_id,
            camera_id=camera_id,
            profile_id=camera.profile_id,
            configuration_fingerprint=camera.fingerprint(),
            board_fingerprint=self.board.fingerprint(),
            rgb=self.artifacts.rgb(rgb),
            depth=self.artifacts.depth(depth),
            rgb_timestamp_s=timestamp,
            depth_timestamp_s=timestamp + timestamp_skew_s,
            robot_timestamp_s=timestamp,
            settled=settled,
            moving=not settled,
            t_b_f=reported,
            admitted=not rejection,
            rejection_codes=tuple(rejection),
            partition=partition,
            sensor_fault_ids=self.sensor_fault_ids(camera_id),
        )

    def reference_captures(self, camera_id: str, dataset_id: str) -> tuple[ReferenceCapture, ...]:
        return self.reference_batch(camera_id, dataset_id, "validation").captures

    def reference_batch(
        self, camera_id: str, dataset_id: str, partition: Literal["validation", "routine"]
    ) -> ReferenceBatch:
        identity = hashlib.sha256(f"{camera_id}/{dataset_id}/{partition}".encode()).hexdigest()
        return ReferenceBatch(
            batch_id=identity,
            camera_id=camera_id,
            dataset_id=dataset_id,
            partition=partition,
            captures=self._render_reference_captures(camera_id, dataset_id, partition),
        )

    def _render_reference_captures(
        self, camera_id: str, dataset_id: str, partition: Literal["validation", "routine"]
    ) -> tuple[ReferenceCapture, ...]:
        """24 separately defined survey targets over x/y/height, rendered one at a time.

        The purple 50 mm disks are simplified, identifiable reference fixtures. Their
        base coordinates are set before and without reading any candidate calibration.
        Runtime/reference services must detect them from RGB and reconstruct native depth.
        """
        references = [
            (x, y, z)
            for z in (0.3, 0.45, 0.6, 0.75)
            for y in (-0.12, 0.12)
            for x in (-0.18, 0.0, 0.18)
        ]
        declared = self.cameras[camera_id]
        camera = self._factory_models[camera_id]
        physical = self._physical_cameras[camera_id]
        captures = []
        for index, reference in enumerate(references):
            seed = hashlib.sha256(
                f"{self.seed}/{dataset_id}/{camera_id}/reference/{index}".encode()
            ).digest()
            rng = np.random.default_rng(int.from_bytes(seed[:8], "little"))
            arrays = []
            masks = []
            for stream, camera_pose in (
                (camera.rgb, physical),
                (camera.depth, physical @ np.asarray(camera.t_c_d.matrix)),
            ):
                rays = self._stream_rays(stream)
                world_rays = rays @ camera_pose[:3, :3].T
                z_scale = (reference[2] - camera_pose[2, 3]) / world_rays[:, 2]
                world_points = camera_pose[:3, 3] + z_scale[:, None] * world_rays
                inside = (
                    np.linalg.norm(world_points[:, :2] - np.array(reference[:2]), axis=1) <= 0.025
                ) & (z_scale > 0)
                floor_scale = -camera_pose[2, 3] / world_rays[:, 2]
                axial = np.where(inside, z_scale, floor_scale)
                arrays.append(axial)
                masks.append(inside)
            flat_rgb = np.full(
                (camera.rgb.height * camera.rgb.width, 3), (70, 80, 90), dtype=np.uint8
            )
            flat_rgb[masks[0]] = (225, 35, 190)
            rgb = flat_rgb.reshape(camera.rgb.height, camera.rgb.width, 3)
            rgb = np.clip(
                rgb.astype(float) + rng.normal(0, self.noise.intensity_sigma, rgb.shape), 0, 255
            ).astype(np.uint8)
            measurement = arrays[1]
            if camera.depth_semantics == "radial_range":
                measurement *= np.linalg.norm(self._stream_rays(camera.depth), axis=1)
            measurement += rng.normal(0, self.noise.depth_sigma_m, measurement.shape)
            depth = (
                (measurement / camera.depth_scale_m)
                .reshape(camera.depth.height, camera.depth.width)
                .astype(np.float32)
            )
            reference_id = f"{dataset_id}-{camera_id}-reference-{index:02d}"
            rgb, depth = self.sensor_output(camera, rgb, depth, reference_id)
            timestamp = 1_800_010_000.0 + index
            capture = Capture(
                capture_id=reference_id,
                dataset_id=dataset_id,
                camera_id=camera_id,
                profile_id=declared.profile_id,
                configuration_fingerprint=declared.fingerprint(),
                board_fingerprint=self.board.fingerprint(),
                rgb=self.artifacts.rgb(rgb),
                depth=self.artifacts.depth(depth),
                rgb_timestamp_s=timestamp,
                depth_timestamp_s=timestamp,
                robot_timestamp_s=timestamp,
                settled=True,
                moving=False,
                t_b_f=framed(np.eye(4), "f", "b"),
                admitted=True,
                partition=partition,
                sensor_fault_ids=self.sensor_fault_ids(camera_id),
            )
            captures.append(
                ReferenceCapture(reference_id=reference_id, base_point_m=reference, capture=capture)
            )
        return tuple(captures)

    def capture_objects(
        self,
        camera_id: str,
        objects: tuple[PhysicalBox, ...],
        flange: Transform,
        capture_id: str,
        timestamp_s: float,
    ) -> Capture:
        """Ray-cast the physical boxes; the result contains RGB/depth, never object poses."""
        declared = self.cameras[camera_id]
        camera = self._factory_models[camera_id]
        physical = self._physical_cameras[camera_id]
        seed = hashlib.sha256(f"{self.seed}/runtime/{capture_id}".encode()).digest()
        rng = np.random.default_rng(int.from_bytes(seed[:8], "little"))
        depths, rgb_values = [], None
        for stream, camera_pose in (
            (camera.rgb, physical),
            (camera.depth, physical @ np.asarray(camera.t_c_d.matrix)),
        ):
            rays = self._stream_rays(stream)
            world_rays = rays @ camera_pose[:3, :3].T
            nearest = -camera_pose[2, 3] / world_rays[:, 2]
            colors = np.full((len(rays), 3), (70, 80, 90), dtype=np.uint8)
            for obj in objects:
                t_object_camera = inverse(obj.t_b_object) @ camera_pose
                local_origin = t_object_camera[:3, 3]
                local_directions = rays @ t_object_camera[:3, :3].T
                half = np.asarray(obj.size_m) / 2
                with np.errstate(divide="ignore", invalid="ignore"):
                    first = (-half - local_origin) / local_directions
                    second = (half - local_origin) / local_directions
                entry = np.max(np.minimum(first, second), axis=1)
                leave = np.min(np.maximum(first, second), axis=1)
                hit = (entry > 0) & (leave >= entry) & (entry < nearest)
                local_hit = local_origin + entry[:, None] * local_directions
                top = hit & (np.abs(local_hit[:, 2] - half[2]) < 1e-7)
                colors[hit] = (130, 45, 40)
                colors[top] = obj.top_rgb
                nearest[hit] = entry[hit]
            depths.append(nearest)
            if stream is camera.rgb:
                rgb_values = colors.reshape(stream.height, stream.width, 3)
        if rgb_values is None:
            raise CalibrationError("RGB_RENDER_FAILED")
        rgb = np.clip(
            rgb_values.astype(float) + rng.normal(0, self.noise.intensity_sigma, rgb_values.shape),
            0,
            255,
        ).astype(np.uint8)
        measurement = depths[1]
        if camera.depth_semantics == "radial_range":
            measurement *= np.linalg.norm(self._stream_rays(camera.depth), axis=1)
        measurement += rng.normal(0, self.noise.depth_sigma_m, measurement.shape)
        depth = (
            (measurement / camera.depth_scale_m)
            .reshape(camera.depth.height, camera.depth.width)
            .astype(np.float32)
        )
        rgb, depth = self.sensor_output(camera, rgb, depth, capture_id)
        return Capture(
            capture_id=capture_id,
            dataset_id=f"runtime-{camera_id}",
            camera_id=camera_id,
            profile_id=declared.profile_id,
            configuration_fingerprint=declared.fingerprint(),
            board_fingerprint=self.board.fingerprint(),
            rgb=self.artifacts.rgb(rgb),
            depth=self.artifacts.depth(depth),
            rgb_timestamp_s=timestamp_s,
            depth_timestamp_s=timestamp_s,
            robot_timestamp_s=timestamp_s,
            settled=True,
            moving=False,
            t_b_f=flange,
            admitted=True,
            partition="runtime",
            sensor_fault_ids=self.sensor_fault_ids(camera_id),
        )


def instructor_reference(world: SyntheticSensorWorld, camera_id: str) -> tuple[Array, Array]:
    """Explicit test/instructor oracle. Forbidden in estimator and operational target services."""
    return world._physical_cameras[camera_id].copy(), world._physical_mount.copy()
