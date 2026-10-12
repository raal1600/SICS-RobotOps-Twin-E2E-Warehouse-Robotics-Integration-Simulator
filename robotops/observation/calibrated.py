"""Operational observation from sensor arrays and approved artifacts only.

The observer is deliberately not given WorldState, hidden camera extrinsics, board
mounts or object poses. It cannot fall back to the legacy synthetic observer.
"""

from datetime import UTC, datetime
from functools import partial
from math import dist
from typing import Protocol

from robotops.calibration.agreement import compare_cameras
from robotops.calibration.artifacts import SensorArtifacts
from robotops.calibration.contracts import PointFailure
from robotops.calibration.depth import pixel_to_base
from robotops.calibration.errors import CalibrationError
from robotops.calibration.lifecycle import CalibrationStore
from robotops.calibration.measurement_quality import assess_measurement
from robotops.calibration.perception import identify_surface, visible_fixture_codes
from robotops.calibration.runtime_contracts import (
    ArtifactBinding,
    CalibratedObject,
    CalibratedObservation,
    SensorSnapshot,
)
from robotops.calibration.trace import recorded_call
from robotops.config import Settings
from robotops.domain.models import Fault, ObservedObject, Pose, WorldObservation, new_id


class FreshSensor(Protocol):
    def fresh(self, camera_ids: tuple[str, ...], capture_prefix: str) -> SensorSnapshot: ...


class CalibratedObserver:
    def __init__(
        self,
        settings: Settings,
        sensor: FreshSensor,
        store: CalibrationStore,
        artifacts: SensorArtifacts,
        camera_id: str = "camera-west",
    ):
        self.settings, self.sensor, self.store, self.artifacts = settings, sensor, store, artifacts
        self.camera_id = camera_id

    def fresh(self, fault: Fault | None = None, *, identity: str | None = None) -> WorldObservation:
        if fault is not None:
            raise CalibrationError(
                "USE_MEASURED_SENSOR_FAULTS",
                "Legacy copied-pose faults are not image sensor faults",
            )
        camera_ids = (
            self.camera_id,
            "camera-east" if self.camera_id == "camera-west" else "camera-west",
        )
        artifacts = {camera_id: self.store.active(camera_id) for camera_id in camera_ids}
        states = {camera_id: self.store.state(camera_id) for camera_id in camera_ids}
        identity = identity or new_id()
        method = self.sensor.fresh
        snapshot = recorded_call(
            self.store,
            self.camera_id,
            identity,
            method.__module__.replace(".", "/") + ".py",
            method.__qualname__,
            {"camera_ids": list(camera_ids), "capture_prefix": identity},
            partial(method, camera_ids, identity),
        )
        with self.store.store.transaction() as db:
            self.store._put(db, "runtime-acquisition", identity, snapshot)
            for capture in snapshot.captures:
                self.store._put(db, "capture", capture.capture_id, capture)
        if tuple(capture.camera_id for capture in snapshot.captures) != camera_ids:
            raise CalibrationError("SENSOR_CAMERA_SET_MISMATCH")
        bindings, measurements, coverage, detections = [], [], [], []
        for capture in snapshot.captures:
            artifact, state = artifacts[capture.camera_id], states[capture.camera_id]
            if capture.configuration_fingerprint != artifact.candidate.camera.fingerprint():
                raise CalibrationError("FRESH_SENSOR_CONFIGURATION_CHANGED")
            if capture.board_fingerprint != artifact.candidate.board.fingerprint():
                raise CalibrationError("FRESH_BOARD_CONFIGURATION_CHANGED")
            rgb = self.artifacts.read_rgb(capture.rgb)
            detection = recorded_call(
                self.store,
                capture.camera_id,
                identity,
                "robotops/calibration/perception.py",
                "identify_surface",
                {
                    "capture_id": capture.capture_id,
                    "camera_id": capture.camera_id,
                    "rgb": capture.rgb.model_dump(mode="json"),
                    "method": "red_cube_top",
                },
                partial(
                    identify_surface,
                    capture.capture_id,
                    capture.camera_id,
                    rgb,
                    "red_cube_top",
                    self.artifacts,
                ),
            )
            with self.store.store.transaction() as db:
                self.store._put(db, "surface-detection", capture.capture_id, detection)
            detections.append(detection)
            pixel, mask = detection.selected_rgb_pixel, self.artifacts.read_mask(detection.mask)
            result = recorded_call(
                self.store,
                capture.camera_id,
                identity,
                "robotops/calibration/depth.py",
                "pixel_to_base",
                {
                    "selected_rgb_pixel": pixel,
                    "depth_artifact": capture.depth.model_dump(mode="json"),
                    "capture_id": capture.capture_id,
                    "camera": state.camera.model_dump(mode="json"),
                    "artifact_id": artifact.artifact_id,
                    "artifact_sha256": artifact.fingerprint(),
                    "limits": state.limits.model_dump(mode="json"),
                    "rgb_mask_source": "red_cube_top(actual saved RGB)",
                    "rgb_surface_mask": detection.mask.model_dump(mode="json"),
                },
                partial(
                    pixel_to_base,
                    pixel,
                    self.artifacts.read_depth(capture.depth),
                    state.camera,
                    artifact,
                    state.limits,
                    active_valid=True,
                    rgb_surface_mask=mask,
                ),
            )
            with self.store.store.transaction() as db:
                self.store._put(
                    db,
                    "runtime-point-error" if isinstance(result, PointFailure) else "runtime-point",
                    capture.capture_id,
                    result,
                )
            if isinstance(result, PointFailure):
                raise CalibrationError(result.code, result.detail)
            measurements.append(result)
            coverage.append(visible_fixture_codes(rgb))
            bindings.append(
                ArtifactBinding(
                    camera_id=capture.camera_id,
                    artifact_id=artifact.artifact_id,
                    artifact_fingerprint=artifact.fingerprint(),
                    camera_configuration_fingerprint=state.camera.fingerprint(),
                    capture_id=capture.capture_id,
                )
            )
        agreement = recorded_call(
            self.store,
            self.camera_id,
            identity,
            "robotops/calibration/agreement.py",
            "compare_cameras",
            {
                "primary": measurements[0].model_dump(mode="json"),
                "secondary": measurements[1].model_dump(mode="json"),
                "first_artifact_id": artifacts[camera_ids[0]].artifact_id,
                "second_artifact_id": artifacts[camera_ids[1]].artifact_id,
                "first_limits": states[camera_ids[0]].limits.model_dump(mode="json"),
                "second_limits": states[camera_ids[1]].limits.model_dump(mode="json"),
            },
            partial(
                compare_cameras,
                identity,
                measurements[0],
                measurements[1],
                artifacts[camera_ids[0]],
                artifacts[camera_ids[1]],
                states[camera_ids[0]].limits,
                states[camera_ids[1]].limits,
            ),
        )
        with self.store.store.transaction() as db:
            self.store._put(db, "camera-agreement", identity, agreement)
        if not agreement.passed:
            raise CalibrationError("CAMERA_AGREEMENT_FAILED", ", ".join(agreement.failures))
        # All supporting artifacts are rechecked after processing and again at dispatch.
        for camera_id in camera_ids:
            if self.store.active(camera_id).fingerprint() != artifacts[camera_id].fingerprint():
                raise CalibrationError("CALIBRATION_CHANGED_DURING_OBSERVATION")
        result = measurements[0]
        capture = snapshot.captures[0]
        covered = tuple(location for location in coverage[0] if location in coverage[1])
        # The known cube's top-to-center offset is configured geometry, explicitly
        # separate from the camera's measured surface point and the grasp orientation.
        center = (result.point[0], result.point[1], result.point[2] - 0.04)
        nearby = [
            location
            for location in self.settings.locations
            if dist(center, location.pose.position) < 0.06
        ]
        if len(nearby) != 1 or nearby[0].location_id not in covered:
            raise CalibrationError("OBSERVED_PRODUCT_LOCATION_AMBIGUOUS")
        checks = recorded_call(
            self.store,
            self.camera_id,
            identity,
            "robotops/calibration/measurement_quality.py",
            "assess_measurement",
            {
                "point": result.model_dump(mode="json"),
                "detection": detections[0].model_dump(mode="json"),
                "agreement": agreement.model_dump(mode="json"),
                "artifact_id": artifacts[self.camera_id].artifact_id,
                "limits": states[self.camera_id].limits.model_dump(mode="json"),
            },
            partial(
                assess_measurement,
                result,
                detections[0],
                agreement,
                artifacts[self.camera_id],
                states[self.camera_id].limits,
            ),
        )
        with self.store.store.transaction() as db:
            self.store._put(db, "measurement-quality", checks.quality_id, checks)
        if not checks.passed:
            raise CalibrationError("MEASUREMENT_QUALITY_FAILED", ", ".join(checks.failures))
        measured = CalibratedObject(
            binding=bindings[0], surface_point=result, measurement_quality=checks
        )
        timestamp = datetime.fromtimestamp(capture.rgb_timestamp_s, UTC)
        observation = WorldObservation(
            schema_version="3.0",
            run_id=self.store.store.run_id,
            correlation_id=identity,
            causation_id=identity,
            timestamp=timestamp,
            observation_id=identity,
            scene_epoch=snapshot.scene_epoch,
            step=snapshot.step,
            captured_at=timestamp,
            model_version="measured-rgbd-observer-2",
            calibration_version=self.settings.calibration_version,
            cell_generation=snapshot.cell_generation,
            covered_locations=covered,
            objects=(
                ObservedObject(
                    schema_version="3.0",
                    product_id=self.settings.products[0].product_id,
                    location_id=nearby[0].location_id,
                    confidence=None,
                    uncertainty_m=None,
                    pose=Pose(
                        position=center,
                        frame_id=self.settings.frame_id,
                        calibration_version=self.settings.calibration_version,
                    ),
                    calibrated_object=measured,
                ),
            ),
            calibrated_observation=CalibratedObservation(
                machine=snapshot.machine, bindings=tuple(bindings)
            ),
        )
        return observation
