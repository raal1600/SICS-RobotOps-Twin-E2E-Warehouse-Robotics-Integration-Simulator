"""Strict wire contracts. WorldState is deliberately distinct from WorldObservation."""

from datetime import UTC, datetime
from enum import StrEnum
from math import isclose
from typing import Annotated, Literal, Self
from uuid import NAMESPACE_URL, uuid4, uuid5

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    FiniteFloat,
    StringConstraints,
    field_validator,
    model_validator,
)

Identifier = Annotated[str, StringConstraints(min_length=1, max_length=160, pattern=r"^[\w.:-]+$")]


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return str(uuid4())


def stable_id(namespace: str, value: str) -> str:
    return str(uuid5(NAMESPACE_URL, namespace + ":" + value))


class Contract(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, validate_default=True, allow_inf_nan=False
    )
    schema_version: Literal["1.0"] = "1.0"


class Record(Contract):
    run_id: Identifier
    correlation_id: Identifier
    causation_id: Identifier
    timestamp: AwareDatetime

    @field_validator("timestamp")
    @classmethod
    def utc(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)


class Pose(Contract):
    position: tuple[FiniteFloat, FiniteFloat, FiniteFloat]
    quaternion_xyzw: tuple[FiniteFloat, FiniteFloat, FiniteFloat, FiniteFloat] = (0, 0, 0, 1)
    unit: Literal["m"] = "m"
    frame_id: Identifier = "cell_world"
    calibration_version: Identifier = "cal-1"

    @model_validator(mode="after")
    def normalized(self) -> Self:
        if not isclose(sum(x * x for x in self.quaternion_xyzw), 1.0, abs_tol=1e-6):
            raise ValueError("quaternion must have unit norm within 1e-6")
        return self


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


class WorldState(Record):
    scene_epoch: Identifier
    step: int = Field(ge=0)
    objects: tuple[WorldObject, ...]
    locations: tuple[InventoryLocation, ...]
    cell: CellState


class ObservedObject(Contract):
    product_id: Identifier
    location_id: Identifier
    pose: Pose
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)
    uncertainty_m: float = Field(default=0, ge=0, allow_inf_nan=False)


class WorldObservation(Record):
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


class ActionPlan(Record):
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
    brain_version: Literal["deterministic-1", "structured-1"] = "deterministic-1"


class RobotCommand(ActionPlan):
    command_id: Identifier


class CommandStatus(StrEnum):
    CREATED = "CREATED"
    DISPATCHED = "DISPATCHED"
    ACCEPTED = "ACCEPTED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    STATUS_UNKNOWN = "STATUS_UNKNOWN"


class CommandReceipt(Record):
    command_id: Identifier
    job_id: Identifier
    scene_epoch: Identifier
    status: CommandStatus
    reason: str
    effect_count: int = Field(ge=0, le=1)
    payload_hash: str
    journal_durable: bool = True


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
