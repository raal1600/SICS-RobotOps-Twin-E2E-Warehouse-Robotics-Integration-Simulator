from datetime import timedelta
from hashlib import sha256

from robotops.config import Settings
from robotops.domain.models import (
    Fault,
    ObservedMachineState,
    ObservedObject,
    WorldObservation,
    WorldState,
    new_id,
    utc_now,
)
from robotops.robotics.catalogue import load_catalogue
from robotops.workflow.store import metadata


class ObservationModel:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def observe(self, world: WorldState, fault: Fault | None = None) -> WorldObservation:
        now = utc_now()
        captured = now
        objects = []
        hkm = world.schema_version == "2.0"
        sensors = (
            tuple(sensor for sensor in load_catalogue().cameras if not sensor.presentation_only)
            if hkm
            else ()
        )
        for obj in world.objects:
            uncertainty = self.settings.pose_noise_m
            if fault == Fault.POSE_UNCERTAINTY:
                uncertainty = max(uncertainty, self.settings.max_uncertainty_m + 0.1)
            sign = (
                1
                if sha256((str(self.settings.seed) + obj.product.product_id).encode()).digest()[0]
                % 2
                else -1
            )
            pose = obj.pose.model_copy(
                update={
                    "position": (
                        obj.pose.position[0] + sign * uncertainty,
                        obj.pose.position[1],
                        obj.pose.position[2],
                    )
                }
            )
            objects.append(
                ObservedObject(
                    **(
                        dict(
                            schema_version="2.0",
                            sensor_id=sensors[0].sensor_id,
                            evidence_source="SYNTHETIC_OBSERVATION_MODEL",
                        )
                        if hkm
                        else {}
                    ),
                    product_id=obj.product.product_id,
                    location_id="gripper" if obj.attached else obj.location_id,
                    pose=pose,
                    confidence=0.3 if fault == Fault.LOW_CONFIDENCE_OBSERVATION else 1,
                    uncertainty_m=uncertainty,
                )
            )
        covered = tuple(loc.location_id for loc in world.locations)
        if fault == Fault.MISSING_OBSERVATION:
            objects = []
            covered = ()
        if fault == Fault.CONTRADICTORY_OBSERVATION:
            objects += [
                obj.model_copy(
                    update={
                        "location_id": next(loc for loc in covered if loc != obj.location_id),
                        **({"sensor_id": sensors[1].sensor_id} if hkm else {}),
                    }
                )
                for obj in objects
            ]
        if fault == Fault.STALE_OBSERVATION:
            captured -= timedelta(seconds=self.settings.freshness_seconds * 2)
        extensions = {}
        if hkm:
            if world.tool_state is None or world.robot_state is None:
                raise ValueError("HKM_OBSERVATION_METADATA_REQUIRED")
            extensions = dict(
                schema_version="2.0",
                model_version="synthetic-observer-2",
                robot_profile_version=world.robot_profile_version,
                frame_tree_version=world.frame_tree_version,
                sensors=sensors,
                machine_telemetry=ObservedMachineState(
                    tool_state=world.tool_state,
                    tcp_pose=world.robot_state.tcp_pose,
                    captured_at=captured,
                    cell_generation=world.cell.generation,
                ),
            )
        return WorldObservation(
            **metadata(world, world.causation_id, now),
            **extensions,
            observation_id=new_id(),
            scene_epoch=world.scene_epoch,
            step=world.step,
            captured_at=captured,
            calibration_version=self.settings.calibration_version,
            objects=tuple(objects),
            covered_locations=covered,
            cell_generation=world.cell.generation,
        )
