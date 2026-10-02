from datetime import timedelta
from hashlib import sha256

from robotops.config import Settings
from robotops.domain.models import (
    Fault,
    ObservedObject,
    WorldObservation,
    WorldState,
    new_id,
    utc_now,
)
from robotops.workflow.store import metadata


class ObservationModel:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def observe(self, world: WorldState, fault: Fault | None = None) -> WorldObservation:
        now = utc_now()
        captured = now
        objects = []
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
                    update={"location_id": next(loc for loc in covered if loc != obj.location_id)}
                )
                for obj in objects
            ]
        if fault == Fault.STALE_OBSERVATION:
            captured -= timedelta(seconds=self.settings.freshness_seconds * 2)
        return WorldObservation(
            **metadata(world, world.causation_id, now),
            observation_id=new_id(),
            scene_epoch=world.scene_epoch,
            step=world.step,
            captured_at=captured,
            calibration_version=self.settings.calibration_version,
            objects=tuple(objects),
            covered_locations=covered,
            cell_generation=world.cell.generation,
        )
