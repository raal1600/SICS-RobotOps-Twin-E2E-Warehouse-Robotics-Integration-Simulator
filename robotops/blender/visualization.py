"""Read-only illustration contracts. Never input to planning or verification."""

from math import isclose
from typing import ClassVar, Literal, Self

from pydantic import AwareDatetime, Field, FiniteFloat, model_validator

from robotops.domain.base import V2Contract, VersionedContract
from robotops.domain.models import AuditEvent, CellMode, Contract, Identifier, JobState
from robotops.robotics.models import ToolId

Vector3 = tuple[FiniteFloat, FiniteFloat, FiniteFloat]


class VisualObject(VersionedContract):
    extension_fields: ClassVar[frozenset[str]] = frozenset(
        {
            "primitive",
            "quaternion_xyzw",
            "scale",
            "visible",
            "opacity",
            "parent_name",
            "material_role",
            "semantic_tags",
            "label",
            "tool_id",
        }
    )
    name: str = Field(min_length=1, max_length=200)
    position: Vector3
    size: Vector3
    color: Vector3
    product_id: Identifier | None = None
    location_id: Identifier | None = None
    primitive: Literal["box", "cylinder"] | None = None
    quaternion_xyzw: tuple[FiniteFloat, FiniteFloat, FiniteFloat, FiniteFloat] | None = None
    scale: Vector3 | None = None
    visible: bool | None = None
    opacity: float | None = Field(default=None, ge=0, le=1)
    parent_name: str | None = None
    material_role: str | None = None
    semantic_tags: tuple[str, ...] | None = None
    label: str | None = None
    tool_id: ToolId | None = None

    @model_validator(mode="after")
    def geometric_shape(self) -> Self:
        if any(value <= 0 for value in self.size):
            raise ValueError("INVALID_VISUAL_DIMENSIONS")
        if self.schema_version == "2.0":
            if self.primitive is None or self.quaternion_xyzw is None or self.scale is None:
                raise ValueError("ARTICULATED_GEOMETRY_REQUIRED")
            if not isclose(sum(v * v for v in self.quaternion_xyzw), 1, abs_tol=1e-6):
                raise ValueError("INVALID_VISUAL_QUATERNION")
            if any(value <= 0 for value in self.scale):
                raise ValueError("INVALID_VISUAL_SCALE")
        return self


class VisualTransform(V2Contract):
    position: Vector3
    quaternion_xyzw: tuple[FiniteFloat, FiniteFloat, FiniteFloat, FiniteFloat]
    scale: Vector3 = (1, 1, 1)
    visible: bool = True

    @model_validator(mode="after")
    def normalized(self) -> Self:
        if not isclose(sum(v * v for v in self.quaternion_xyzw), 1, abs_tol=1e-6):
            raise ValueError("INVALID_VISUAL_QUATERNION")
        if any(value <= 0 for value in self.scale):
            raise ValueError("INVALID_VISUAL_SCALE")
        return self


class VisualFrame(VersionedContract):
    extension_fields: ClassVar[frozenset[str]] = frozenset(
        {
            "transforms",
            "sim_time_s",
            "active_tool_id",
            "rack_tool_ids",
            "attached_product_id",
        }
    )
    frame: int = Field(ge=1, le=720)
    phase: Literal[
        "APPROACH",
        "ATTACH",
        "LIFT",
        "TRANSFER",
        "DETACH",
        "RETRACT",
        "HOME",
        "TOOL_CHANGE_REQUESTED",
        "MOVE_TO_SAFE_POSE",
        "MOVE_TO_TOOL_DOCK",
        "RELEASE_CURRENT_TOOL",
        "VERIFY_FLANGE_EMPTY",
        "ENGAGE_REQUESTED_TOOL",
        "VERIFY_TOOL_ID",
        "RETREAT_FROM_TOOL_RACK",
        "TOOL_CHANGE_COMPLETED",
        "TOOL_CHANGE_NOT_REQUIRED",
        "PRE_GRASP",
        "GRASP",
        "GRASP_CONFIRM",
        "SAFE_TRANSFER",
        "PRE_PLACE",
        "PLACE",
        "RELEASE",
        "RELEASE_CONFIRM",
        "NEXT_SAFE_POSE",
    ]
    positions: dict[str, Vector3]
    transforms: dict[str, VisualTransform] | None = None
    sim_time_s: float | None = Field(default=None, ge=0)
    active_tool_id: ToolId | None = None
    rack_tool_ids: tuple[ToolId, ...] | None = None
    attached_product_id: Identifier | None = None

    @model_validator(mode="after")
    def versioned_frame(self) -> Self:
        if self.schema_version == "1.0":
            if self.frame > 100 or self.phase not in {
                "APPROACH",
                "ATTACH",
                "LIFT",
                "TRANSFER",
                "DETACH",
                "RETRACT",
            }:
                raise ValueError("INVALID_LEGACY_FRAME")
        else:
            if self.transforms is None or self.sim_time_s is None or self.rack_tool_ids is None:
                raise ValueError("ARTICULATED_TRANSFORMS_REQUIRED")
            if (
                len(set(self.rack_tool_ids)) != len(self.rack_tool_ids)
                or self.active_tool_id in self.rack_tool_ids
            ):
                raise ValueError("INVALID_RECORDED_TOOL_OCCUPANCY")
        return self


class MotionRecording(VersionedContract):
    extension_fields: ClassVar[frozenset[str]] = frozenset(
        {
            "robot_profile_version",
            "kinematics_version",
            "calibration_version",
            "frame_tree_version",
            "simulated_duration_s",
        }
    )
    source: Literal["BLENDER_EVALUATED_SCENE"] = "BLENDER_EVALUATED_SCENE"
    command_id: Identifier
    job_id: Identifier
    scene_epoch: Identifier
    product_id: Identifier
    frame_id: Identifier
    unit: Literal["m"] = "m"
    fps: Literal[24] = 24
    total_frames: int = Field(default=100, ge=1, le=720)
    complete: bool
    objects: list[VisualObject] = Field(min_length=1, max_length=512)
    frames: list[VisualFrame] = Field(min_length=1, max_length=720)
    robot_profile_version: Literal["hkm_inspired_v1"] | None = None
    kinematics_version: Literal["HKM_INSPIRED_VISUAL_KINEMATICS_V1"] | None = None
    calibration_version: Identifier | None = None
    frame_tree_version: Identifier | None = None
    simulated_duration_s: float | None = Field(default=None, gt=0, le=30)

    @model_validator(mode="after")
    def valid_frames(self) -> Self:
        names = {item.name for item in self.objects}
        if len(names) != len(self.objects):
            raise ValueError("DUPLICATE_VISUAL_OBJECT")
        if [item.frame for item in self.frames] != list(range(1, len(self.frames) + 1)):
            raise ValueError("NONCONTIGUOUS_VISUAL_FRAMES")
        if any(not set(frame.positions) <= names for frame in self.frames):
            raise ValueError("UNKNOWN_VISUAL_OBJECT")
        if any(not set(frame.transforms or {}) <= names for frame in self.frames):
            raise ValueError("UNKNOWN_VISUAL_TRANSFORM")
        if any(
            item.schema_version != self.schema_version for item in [*self.objects, *self.frames]
        ):
            raise ValueError("MIXED_RECORDING_VERSIONS")
        if self.schema_version == "1.0":
            if self.total_frames != 100 or len(self.objects) > 100 or len(self.frames) > 100:
                raise ValueError("INVALID_LEGACY_RECORDING_BOUNDS")
        elif any(getattr(self, name) is None for name in self.extension_fields):
            raise ValueError("ARTICULATED_RECORDING_METADATA_REQUIRED")
        if self.schema_version == "2.0":
            if (
                self.frame_id != "cell_world"
                or self.calibration_version != "hkm-cal-1"
                or self.frame_tree_version != "hkm-frame-tree-1"
            ):
                raise ValueError("RECORDING_SPATIAL_METADATA_MISMATCH")
            times = [frame.sim_time_s for frame in self.frames if frame.sim_time_s is not None]
            if (
                len(times) != len(self.frames)
                or times != sorted(times)
                or times[0] != 0
                or (self.complete and times[-1] != self.simulated_duration_s)
            ):
                raise ValueError("RECORDING_TIME_DOMAIN_MISMATCH")
        if self.complete and len(self.frames) != self.total_frames:
            raise ValueError("INCOMPLETE_VISUAL_RECORDING")
        if len(self.frames) > self.total_frames:
            raise ValueError("FRAME_COUNT_EXCEEDS_RECORDING")
        return self


class VisualScene(VersionedContract):
    extension_fields: ClassVar[frozenset[str]] = frozenset({"robot_profile_version", "cameras"})
    source: Literal["SAVED_START_SCENE", "CURRENT_WORLD_REFERENCE"]
    scene_epoch: Identifier
    timestamp: AwareDatetime
    cell_mode: CellMode
    objects: list[VisualObject] = Field(min_length=1, max_length=512)
    robot_profile_version: Literal["hkm_inspired_v1"] | None = None
    cameras: list["VisualCamera"] | None = None

    @model_validator(mode="after")
    def scene_profile(self) -> Self:
        if len({obj.name for obj in self.objects}) != len(self.objects) or any(
            obj.schema_version != self.schema_version for obj in self.objects
        ):
            raise ValueError("INVALID_SCENE_OBJECT_IDENTITY_OR_VERSION")
        if self.schema_version == "1.0":
            if len(self.objects) > 100:
                raise ValueError("INVALID_LEGACY_SCENE_BOUNDS")
        elif self.robot_profile_version is None or self.cameras is None or len(self.cameras) != 3:
            raise ValueError("HKM_SCENE_CAMERAS_REQUIRED")
        return self


class VisualCamera(V2Contract):
    name: str
    position: Vector3
    target: Vector3
    role: Literal["PRESENTATION", "SYNTHETIC_SENSOR"]
    sensor_id: Identifier | None = None
    frame_id: Identifier
    calibration_version: Identifier
    camera_model_version: Identifier


class ExecutionScenario(Contract):
    """Recorded test configuration, not proof of an injection or physical outcome."""

    source: Literal["GUIDED_SESSION"] = "GUIDED_SESSION"
    session_id: Identifier
    fault: str | None


class JobPlayback(Contract):
    job_id: Identifier
    command_id: Identifier | None
    job_state: JobState
    status: Literal["WAITING", "RECORDING", "RECORDED", "PARTIAL", "UNAVAILABLE"]
    reason: str
    can_import: bool = False
    recording: MotionRecording | None = None
    scene: VisualScene
    product_id: Identifier
    events: list[AuditEvent] = Field(default_factory=list)
    execution_scenario: ExecutionScenario | None = None


class DeliveryExecution(Contract):
    job_id: Identifier
    order_id: Identifier
    product_id: Identifier
    state: JobState


class DeliverySummary(Contract):
    delivery_id: Identifier
    started_at: AwareDatetime
    current: bool
    executions: list[DeliveryExecution] = Field(default_factory=list)


class DeliveryPlayback(Contract):
    delivery_id: Identifier
    scene: VisualScene
    jobs: list[JobPlayback] = Field(default_factory=list)
    reason: str = (
        "Original executions in this scene, in durable execution order. Replay sends no commands."
    )

    @model_validator(mode="after")
    def original_identities(self) -> Self:
        if len({job.job_id for job in self.jobs}) != len(self.jobs):
            raise ValueError("DUPLICATE_DELIVERY_EXECUTION")
        for job in self.jobs:
            if (
                job.scene.source == "SAVED_START_SCENE"
                and job.scene.scene_epoch != self.delivery_id
            ) or (job.recording and job.recording.scene_epoch != self.delivery_id):
                raise ValueError("DELIVERY_SCENE_MISMATCH")
        return self


VISUAL_SCHEMAS = (
    VisualObject,
    VisualTransform,
    VisualCamera,
    VisualFrame,
    MotionRecording,
    VisualScene,
    ExecutionScenario,
    JobPlayback,
    DeliveryExecution,
    DeliverySummary,
    DeliveryPlayback,
)
