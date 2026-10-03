"""Read-only illustration contracts. Never input to planning or verification."""

from typing import Literal, Self

from pydantic import AwareDatetime, Field, FiniteFloat, model_validator

from robotops.domain.models import AuditEvent, CellMode, Contract, Identifier, JobState

Vector3 = tuple[FiniteFloat, FiniteFloat, FiniteFloat]


class VisualObject(Contract):
    name: str = Field(min_length=1, max_length=200)
    position: Vector3
    size: Vector3
    color: Vector3
    product_id: Identifier | None = None
    location_id: Identifier | None = None


class VisualFrame(Contract):
    frame: int = Field(ge=1, le=100)
    phase: Literal["APPROACH", "ATTACH", "LIFT", "TRANSFER", "DETACH", "RETRACT"]
    positions: dict[str, Vector3]


class MotionRecording(Contract):
    source: Literal["BLENDER_EVALUATED_SCENE"] = "BLENDER_EVALUATED_SCENE"
    command_id: Identifier
    job_id: Identifier
    scene_epoch: Identifier
    product_id: Identifier
    frame_id: Identifier
    unit: Literal["m"] = "m"
    fps: Literal[24] = 24
    total_frames: Literal[100] = 100
    complete: bool
    objects: list[VisualObject] = Field(min_length=1, max_length=100)
    frames: list[VisualFrame] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def valid_frames(self) -> Self:
        names = {item.name for item in self.objects}
        if len(names) != len(self.objects):
            raise ValueError("DUPLICATE_VISUAL_OBJECT")
        if [item.frame for item in self.frames] != list(range(1, len(self.frames) + 1)):
            raise ValueError("NONCONTIGUOUS_VISUAL_FRAMES")
        if any(not set(frame.positions) <= names for frame in self.frames):
            raise ValueError("UNKNOWN_VISUAL_OBJECT")
        if self.complete and len(self.frames) != self.total_frames:
            raise ValueError("INCOMPLETE_VISUAL_RECORDING")
        return self


class VisualScene(Contract):
    source: Literal["SAVED_START_SCENE", "CURRENT_WORLD_REFERENCE"]
    scene_epoch: Identifier
    timestamp: AwareDatetime
    cell_mode: CellMode
    objects: list[VisualObject] = Field(min_length=1, max_length=100)


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


VISUAL_SCHEMAS = (VisualObject, VisualFrame, MotionRecording, VisualScene, JobPlayback)
