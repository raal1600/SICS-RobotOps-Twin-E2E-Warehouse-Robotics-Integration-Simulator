"""Strict wire contracts. WorldState is deliberately distinct from WorldObservation."""

from enum import StrEnum
from typing import ClassVar, Literal, Self

from pydantic import AwareDatetime, Field, model_validator

# Public imports remain stable for archived consumers and existing integrations.
from robotops.domain.base import Contract as Contract
from robotops.domain.base import Identifier as Identifier
from robotops.domain.base import Pose as Pose
from robotops.domain.base import Record as Record
from robotops.domain.base import V2Contract, VersionedContract, VersionedRecord
from robotops.domain.base import new_id as new_id
from robotops.domain.base import stable_id as stable_id
from robotops.domain.base import utc_now as utc_now
from robotops.robotics.models import (
    RobotState,
    SensorSpec,
    ToolId,
    ToolSelectionDecision,
    ToolState,
    TrajectoryIntent,
)


class Product(Contract):
    product_id: Identifier
    sku: Identifier


class InventoryLocation(Contract):
    location_id: Identifier
    pose: Pose


class OrderLine(Contract):
    order_line_id: Identifier
    product_id: Identifier
    source_id: Identifier
    destination_id: Identifier
    quantity: Literal[1] = 1

    @model_validator(mode="after")
    def distinct_locations(self) -> Self:
        if self.source_id == self.destination_id:
            raise ValueError("source and destination must differ")
        return self


class OrderRequest(Contract):
    order_id: Identifier
    lines: tuple[OrderLine, ...] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_lines(self) -> Self:
        if len({line.order_line_id for line in self.lines}) != len(self.lines):
            raise ValueError("duplicate order line")
        if len({line.product_id for line in self.lines}) != len(self.lines):
            raise ValueError("one physical product cannot be ordered twice")
        return self


class JobState(StrEnum):
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    PLANNING = "PLANNING"
    READY_TO_EXECUTE = "READY_TO_EXECUTE"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"
    RECONCILING = "RECONCILING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REQUIRES_INTERVENTION = "REQUIRES_INTERVENTION"


class Order(Record):
    order_id: Identifier
    lines: tuple[OrderLine, ...]
    job_ids: tuple[Identifier, ...]
    status: JobState = JobState.RECEIVED


class PickJob(Record):
    job_id: Identifier
    order_id: Identifier
    line: OrderLine
    state: JobState = JobState.RECEIVED
    revision: int = Field(default=0, ge=0)
    command_id: Identifier | None = None
    action_plan_id: Identifier | None = None


class CellMode(StrEnum):
    READY = "READY"
    BUSY = "BUSY"
    FAULTED = "FAULTED"
    ESTOP_LOGICAL = "ESTOP_LOGICAL"
    RESETTING = "RESETTING"
    OFFLINE = "OFFLINE"


class CellState(Record):
    cell_id: Identifier = "cell-1"
    mode: CellMode = CellMode.READY
    generation: int = Field(default=0, ge=0)
    reason: str = "INITIALIZED"


class WorldObject(Contract):
    product: Product
    location_id: Identifier
    pose: Pose
    attached: bool = False


class WorldState(VersionedRecord):
    extension_fields: ClassVar[frozenset[str]] = frozenset(
        {
            "robot_profile_version",
            "product_catalog_version",
            "tool_spec_version",
            "frame_tree_version",
            "robot_state",
            "tool_state",
        }
    )
    scene_epoch: Identifier
    step: int = Field(ge=0)
    objects: tuple[WorldObject, ...]
    locations: tuple[InventoryLocation, ...]
    cell: CellState
    robot_profile_version: Literal["hkm_inspired_v1"] | None = None
    product_catalog_version: Literal["synthetic-products-1"] | None = None
    tool_spec_version: Literal["synthetic-tools-1"] | None = None
    frame_tree_version: Literal["hkm-frame-tree-1"] | None = None
    robot_state: RobotState | None = None
    tool_state: ToolState | None = None

    @model_validator(mode="after")
    def versioned_world(self) -> Self:
        if self.schema_version == "2.0":
            if any(getattr(self, name) is None for name in self.extension_fields):
                raise ValueError("HKM_WORLD_METADATA_REQUIRED")
            if self.robot_state is None or self.tool_state is None:
                raise ValueError("HKM_WORLD_METADATA_REQUIRED")
            if self.robot_state.active_tool_id != self.tool_state.active_tool_id:
                raise ValueError("ROBOT_TOOL_STATE_CONFLICT")
            if len({obj.product.product_id for obj in self.objects}) != len(self.objects) or len(
                {loc.location_id for loc in self.locations}
            ) != len(self.locations):
                raise ValueError("DUPLICATE_WORLD_IDENTITY")
            locations = {loc.location_id for loc in self.locations}
            if any(obj.location_id not in locations for obj in self.objects):
                raise ValueError("UNKNOWN_WORLD_LOCATION")
            if any(
                pose.calibration_version != "hkm-cal-1" or pose.frame_id != "cell_world"
                for pose in [
                    *(obj.pose for obj in self.objects),
                    *(loc.pose for loc in self.locations),
                ]
            ):
                raise ValueError("WORLD_SPATIAL_METADATA_MISMATCH")
            if any(
                obj.product.sku not in {"SKU-A", "SKU-B", "SKU-C", "SKU-D", "SKU-E", "SKU-F"}
                for obj in self.objects
            ):
                raise ValueError("UNKNOWN_SKU")
        return self


class ObservedObject(VersionedContract):
    extension_fields: ClassVar[frozenset[str]] = frozenset({"sensor_id", "evidence_source"})
    product_id: Identifier
    location_id: Identifier
    pose: Pose
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)
    uncertainty_m: float = Field(default=0, ge=0, allow_inf_nan=False)
    sensor_id: Identifier | None = None
    evidence_source: Literal["SYNTHETIC_OBSERVATION_MODEL"] | None = None

    @model_validator(mode="after")
    def sensor_source(self) -> Self:
        if self.schema_version == "2.0" and (
            self.sensor_id is None or self.evidence_source is None
        ):
            raise ValueError("OBSERVATION_SENSOR_REQUIRED")
        return self


class ObservedMachineState(V2Contract):
    source: Literal["SIMULATED_CELL_TELEMETRY"] = "SIMULATED_CELL_TELEMETRY"
    tool_state: ToolState
    tcp_pose: Pose
    captured_at: AwareDatetime
    cell_generation: int = Field(ge=0)

    @model_validator(mode="after")
    def telemetry_frame(self) -> Self:
        if (
            self.tcp_pose.frame_id != "cell_world"
            or self.tcp_pose.calibration_version != "hkm-cal-1"
        ):
            raise ValueError("TELEMETRY_SPATIAL_METADATA_MISMATCH")
        return self


class WorldObservation(VersionedRecord):
    extension_fields: ClassVar[frozenset[str]] = frozenset(
        {
            "robot_profile_version",
            "frame_tree_version",
            "sensors",
            "machine_telemetry",
        }
    )
    observation_id: Identifier
    scene_epoch: Identifier
    step: int = Field(ge=0)
    captured_at: AwareDatetime
    model_version: Identifier = "synthetic-observer-1"
    calibration_version: Identifier = "cal-1"
    objects: tuple[ObservedObject, ...]
    covered_locations: tuple[Identifier, ...]
    # Explicit coverage is needed: absence alone never proves an empty source.
    cell_generation: int = Field(ge=0)
    robot_profile_version: Literal["hkm_inspired_v1"] | None = None
    frame_tree_version: Literal["hkm-frame-tree-1"] | None = None
    sensors: tuple[SensorSpec, ...] | None = None
    machine_telemetry: ObservedMachineState | None = None

    @model_validator(mode="after")
    def observed_versions(self) -> Self:
        if self.schema_version == "2.0":
            if any(getattr(self, name) is None for name in self.extension_fields):
                raise ValueError("HKM_OBSERVATION_METADATA_REQUIRED")
            if self.sensors is None or self.machine_telemetry is None:
                raise ValueError("HKM_OBSERVATION_METADATA_REQUIRED")
            if (
                self.model_version != "synthetic-observer-2"
                or self.calibration_version != "hkm-cal-1"
            ):
                raise ValueError("UNKNOWN_OBSERVATION_VERSION")
            sensors = {sensor.sensor_id for sensor in self.sensors if not sensor.presentation_only}
            if len(sensors) != len(self.sensors) or len(sensors) < 2:
                raise ValueError("SENSING_CAMERA_METADATA_REQUIRED")
            if len({sensor.frame_id for sensor in self.sensors}) != len(self.sensors):
                raise ValueError("DUPLICATE_SENSOR_FRAME")
            if any(
                obj.schema_version != "2.0" or obj.sensor_id not in sensors for obj in self.objects
            ):
                raise ValueError("UNKNOWN_OBSERVATION_SENSOR")
            if self.machine_telemetry.cell_generation != self.cell_generation:
                raise ValueError("TELEMETRY_GENERATION_MISMATCH")
            if self.machine_telemetry.captured_at != self.captured_at:
                raise ValueError("TELEMETRY_CAPTURE_MISMATCH")
        return self


class ActionPlan(VersionedRecord):
    extension_fields: ClassVar[frozenset[str]] = frozenset(
        {
            "selected_tool_id",
            "grasp_pose",
            "trajectory",
            "tool_selection",
            "robot_profile_version",
            "product_catalog_version",
            "tool_spec_version",
            "frame_tree_version",
        }
    )
    action_plan_id: Identifier
    job_id: Identifier
    order_id: Identifier
    order_line_id: Identifier
    kind: Literal["PICK_AND_PLACE"] = "PICK_AND_PLACE"
    product_id: Identifier
    source_id: Identifier
    destination_id: Identifier
    target_pose: Pose
    scene_epoch: Identifier
    observation_id: Identifier
    cell_generation: int = Field(ge=0)
    brain_version: Literal["deterministic-1", "structured-1", "deterministic-hkm-1"] = (
        "deterministic-1"
    )
    selected_tool_id: ToolId | None = None
    grasp_pose: Pose | None = None
    trajectory: TrajectoryIntent | None = None
    tool_selection: ToolSelectionDecision | None = None
    robot_profile_version: Literal["hkm_inspired_v1"] | None = None
    product_catalog_version: Literal["synthetic-products-1"] | None = None
    tool_spec_version: Literal["synthetic-tools-1"] | None = None
    frame_tree_version: Literal["hkm-frame-tree-1"] | None = None

    @model_validator(mode="after")
    def robotics_intent(self) -> Self:
        if self.schema_version == "2.0":
            if any(getattr(self, name) is None for name in ActionPlan.extension_fields):
                raise ValueError("HKM_ACTION_METADATA_REQUIRED")
            if self.tool_selection is None or self.trajectory is None:
                raise ValueError("HKM_ACTION_METADATA_REQUIRED")
            if (
                self.tool_selection.product_id != self.product_id
                or self.tool_selection.selected_tool_id != self.selected_tool_id
                or self.trajectory.required_tool_id != self.selected_tool_id
                or self.trajectory.grasp_pose != self.grasp_pose
                or self.target_pose.calibration_version != "hkm-cal-1"
                or self.target_pose.frame_id != "cell_world"
            ):
                raise ValueError("HKM_ACTION_IDENTITY_MISMATCH")
            if self.brain_version not in {"deterministic-hkm-1", "structured-1"}:
                raise ValueError("HKM_BRAIN_VERSION_MISMATCH")
        elif self.brain_version == "deterministic-hkm-1":
            raise ValueError("HKM_BRAIN_REQUIRES_VERSION_2")
        return self


class RobotCommand(ActionPlan):
    extension_fields: ClassVar[frozenset[str]] = ActionPlan.extension_fields | {"required_tool_id"}
    command_id: Identifier
    required_tool_id: ToolId | None = None

    @model_validator(mode="after")
    def required_tool_matches_plan(self) -> Self:
        if self.schema_version == "2.0" and self.required_tool_id != self.selected_tool_id:
            raise ValueError("COMMAND_TOOL_MISMATCH")
        return self


class CommandStatus(StrEnum):
    CREATED = "CREATED"
    DISPATCHED = "DISPATCHED"
    ACCEPTED = "ACCEPTED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    STATUS_UNKNOWN = "STATUS_UNKNOWN"


class CommandReceipt(VersionedRecord):
    extension_fields: ClassVar[frozenset[str]] = frozenset(
        {
            "active_tool_id",
            "tool_change_performed",
            "trajectory_id",
            "runtime_profile_version",
        }
    )
    command_id: Identifier
    job_id: Identifier
    scene_epoch: Identifier
    status: CommandStatus
    reason: str
    effect_count: int = Field(ge=0, le=1)
    payload_hash: str
    journal_durable: bool = True
    active_tool_id: ToolId | None = None
    tool_change_performed: bool | None = None
    trajectory_id: Identifier | None = None
    runtime_profile_version: Literal["hkm_inspired_v1"] | None = None

    @model_validator(mode="after")
    def robotics_receipt(self) -> Self:
        if self.schema_version == "2.0":
            if (
                self.tool_change_performed is None
                or self.trajectory_id is None
                or self.runtime_profile_version is None
            ):
                raise ValueError("HKM_RECEIPT_METADATA_REQUIRED")
            if (self.status == CommandStatus.SUCCEEDED and self.effect_count != 1) or (
                self.status in {CommandStatus.FAILED, CommandStatus.REJECTED}
                and self.effect_count != 0
            ):
                raise ValueError("RECEIPT_EFFECT_STATUS_CONFLICT")
            if self.tool_change_performed and self.effect_count != 1:
                raise ValueError("UNCOMMITTED_TOOL_CHANGE")
            if len(self.payload_hash) != 64 or any(
                character not in "0123456789abcdef" for character in self.payload_hash
            ):
                raise ValueError("INVALID_PAYLOAD_HASH")
        return self


class Verdict(StrEnum):
    VERIFIED_SUCCESS = "VERIFIED_SUCCESS"
    VERIFIED_FAILURE = "VERIFIED_FAILURE"
    INCONCLUSIVE = "INCONCLUSIVE"


class VerificationResult(Record):
    verification_id: Identifier
    job_id: Identifier
    command_id: Identifier
    observation_id: Identifier
    verdict: Verdict
    reason: str


class Fault(StrEnum):
    DROP_ACK_AFTER_EFFECT = "DROP_ACK_AFTER_EFFECT"
    DROP_ACK_BEFORE_EFFECT = "DROP_ACK_BEFORE_EFFECT"
    ROBOT_COMMAND_FAILURE = "ROBOT_COMMAND_FAILURE"
    CELL_FAULT = "CELL_FAULT"
    LOGICAL_ESTOP = "LOGICAL_ESTOP"
    LOW_CONFIDENCE_OBSERVATION = "LOW_CONFIDENCE_OBSERVATION"
    CONTRADICTORY_OBSERVATION = "CONTRADICTORY_OBSERVATION"
    STALE_OBSERVATION = "STALE_OBSERVATION"
    MISSING_OBSERVATION = "MISSING_OBSERVATION"
    POSE_UNCERTAINTY = "POSE_UNCERTAINTY"
    BRAIN_TIMEOUT = "BRAIN_TIMEOUT"
    BRAIN_INVALID_OUTPUT = "BRAIN_INVALID_OUTPUT"


class FailureInjection(Record):
    injection_id: Identifier
    fault: Fault
    job_id: Identifier | None = None
    enabled: bool = True


class AuditEvent(Record):
    event_id: Identifier
    component: Identifier
    event_type: Identifier
    order_id: Identifier | None = None
    job_id: Identifier | None = None
    command_id: Identifier | None = None
    state_before: str | None = None
    state_after: str | None = None
    reason: str
    duration_ms: float = Field(default=0, ge=0, allow_inf_nan=False)
    evidence_ids: tuple[Identifier, ...] = ()


class RobotEvent(AuditEvent):
    scene_epoch: Identifier
    step: int = Field(ge=0)


class ReconciliationEvidence(Record):
    evidence_id: Identifier
    job_id: Identifier
    command: RobotCommand
    receipt: CommandReceipt | None
    observation: WorldObservation
    verification: VerificationResult


class PresentationSnapshot(Record):
    """Persisted before execution for human replay; never sensor evidence."""

    job_id: Identifier
    world: WorldState


class JobEvidence(Contract):
    job: PickJob
    command: RobotCommand | None
    journal: CommandReceipt | None
    observations: tuple[WorldObservation, ...]
    verifications: tuple[VerificationResult, ...]
    reconciliations: tuple[ReconciliationEvidence, ...]


SCHEMAS: tuple[type[Contract], ...] = (
    ObservedMachineState,
    PresentationSnapshot,
    JobEvidence,
    Product,
    InventoryLocation,
    OrderRequest,
    Order,
    OrderLine,
    PickJob,
    WorldState,
    WorldObservation,
    ActionPlan,
    RobotCommand,
    CommandReceipt,
    RobotEvent,
    VerificationResult,
    CellState,
    FailureInjection,
    AuditEvent,
    ReconciliationEvidence,
)
