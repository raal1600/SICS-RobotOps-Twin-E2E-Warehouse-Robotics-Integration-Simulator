"""Deterministic geometric planning from measured RGB-D observations; no world access."""

from functools import partial

import numpy as np

from robotops.calibration.configuration import framed
from robotops.calibration.errors import CalibrationError
from robotops.calibration.geometry import inverse
from robotops.calibration.lifecycle import CalibrationStore
from robotops.calibration.runtime_contracts import CalibratedPlan, MachineWaypoint
from robotops.calibration.tcp import GraspSpecification, ToolVerification, construct_target
from robotops.calibration.trace import recorded_call
from robotops.config import Settings
from robotops.domain.models import ActionPlan, InventoryLocation, PickJob, WorldObservation, new_id
from robotops.workflow.store import metadata


class CalibratedBrain:
    def __init__(self, settings: Settings, store: CalibrationStore):
        self.settings, self.store = settings, store

    def plan(
        self, job: PickJob, observation: WorldObservation, destination: InventoryLocation
    ) -> ActionPlan:
        if observation.schema_version != "3.0" or observation.calibrated_observation is None:
            raise CalibrationError("MEASURED_OBSERVATION_REQUIRED")
        seen = next(
            (item for item in observation.objects if item.product_id == job.line.product_id), None
        )
        if seen is None or seen.calibrated_object is None:
            raise CalibrationError("MEASURED_OBJECT_REQUIRED")
        machine = observation.calibrated_observation.machine
        if machine.board_mounted:
            raise CalibrationError("REMOVE_CALIBRATION_BOARD_BEFORE_PICK")
        if machine.tool_verification_id is None:
            raise CalibrationError("CURRENT_TOOL_VERIFICATION_REQUIRED")
        binding = seen.calibrated_object.binding
        for used in observation.calibrated_observation.bindings:
            if self.store.active(used.camera_id).fingerprint() != used.artifact_fingerprint:
                raise CalibrationError("OBSERVATION_CALIBRATION_NO_LONGER_ACTIVE")
        checked = self.store.record(
            "tool-verification", machine.tool_verification_id, ToolVerification
        )
        grasp = GraspSpecification(
            orientation_b_tcp=((1, 0, 0), (0, -1, 0), (0, 0, -1)),
            contact_offset_b_m=(0, 0, 0),
            approach_direction_b=(0, 0, -1),
            approach_distance_m=0.10,
            orientation_source="Configured upright cube/top vacuum grasp; not inferred from depth",
            contact_source="Configured flat cube top; TCP is the vacuum contact plane",
            approach_source="Configured vertical approach above the supporting fixture",
        )
        target = recorded_call(
            self.store,
            binding.camera_id,
            observation.observation_id,
            "robotops/calibration/tcp.py",
            "construct_target",
            {
                "record_id": observation.observation_id,
                "job_id": job.job_id,
                "point": seen.calibrated_object.surface_point.model_dump(mode="json"),
                "grasp": grasp.model_dump(mode="json"),
                "tool": machine.tool.model_dump(mode="json"),
                "verification": checked.model_dump(mode="json"),
                "command_mode": machine.command_mode,
            },
            partial(
                construct_target,
                seen.calibrated_object.surface_point,
                grasp,
                machine.tool,
                checked,
                machine.command_mode,
            ),
        )
        with self.store.store.transaction() as db:
            self.store._put(db, "runtime-target", observation.observation_id, target)
        place = np.array(target.tcp_target.matrix)
        place[:3, 3] = np.asarray(destination.pose.position) + [0, 0, 0.04]
        above_place = place.copy()
        above_place[2, 3] += grasp.approach_distance_m
        tcp_values = [
            np.asarray(target.approach_tcp.matrix),
            np.asarray(target.tcp_target.matrix),
            np.asarray(target.approach_tcp.matrix),
            above_place,
            place,
            above_place,
        ]
        phases = ("PRE_GRASP", "GRASP", "LIFT", "TRANSFER", "PLACE", "RETRACT")
        waypoints = tuple(
            MachineWaypoint.model_validate(
                {
                    "phase": phase,
                    "sim_time_s": float(index),
                    "tcp": framed(tcp, "tcp", "b"),
                    "flange": framed(tcp @ inverse(machine.tool.t_f_tcp.matrix), "f", "b"),
                    "attached": phase in ("GRASP", "LIFT", "TRANSFER"),
                }
            )
            for index, (phase, tcp) in enumerate(zip(phases, tcp_values, strict=True))
        )
        intent = CalibratedPlan(
            observed_object=seen.calibrated_object,
            grasp=grasp,
            target=target,
            tool_verification_id=checked.verification_id,
            waypoints=waypoints,
            supporting_bindings=tuple(
                used
                for used in observation.calibrated_observation.bindings
                if used.camera_id != binding.camera_id
            ),
        )
        return ActionPlan(
            **metadata(job, observation.observation_id),
            schema_version="3.0",
            action_plan_id=new_id(),
            job_id=job.job_id,
            order_id=job.order_id,
            order_line_id=job.line.order_line_id,
            product_id=job.line.product_id,
            source_id=job.line.source_id,
            destination_id=job.line.destination_id,
            target_pose=destination.pose,
            scene_epoch=observation.scene_epoch,
            observation_id=observation.observation_id,
            cell_generation=observation.cell_generation,
            brain_version="measured-geometric-1",
            calibrated_plan=intent,
        )
