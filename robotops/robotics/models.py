"""Strict version-2 synthetic robotics contracts; no runtime/world dependencies."""

from typing import Annotated, Literal, Self

from pydantic import Field, FiniteFloat, model_validator

from robotops.domain.base import Identifier, Pose, V2Contract

ToolId = Literal[
    "EE_VAC_SINGLE",
    "EE_VAC_ARRAY",
    "EE_PINCH_NARROW",
    "EE_PINCH_WIDE",
    "EE_ADAPTIVE_SOFT",
    "EE_SUPPORT_FORK",
]
SKU = Literal["SKU-A", "SKU-B", "SKU-C", "SKU-D", "SKU-E", "SKU-F"]
Positive = Annotated[float, Field(gt=0, allow_inf_nan=False)]
Nonnegative = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Dimensions = tuple[Positive, Positive, Positive]
Vector3 = tuple[FiniteFloat, FiniteFloat, FiniteFloat]
Compatibility = Literal["P", "C", "N"]


class ProductGeometry(V2Contract):
    flat_top_m: tuple[Nonnegative, Nonnegative]
    grasp_width_m: Positive
    soft_envelope_m: Positive
    under_clearance: bool


class ProductSpec(V2Contract):
    catalog_id: Identifier
    sku: SKU
    family: Literal[
        "small_carton", "medium_carton", "soft_pouch", "bottle", "can_jar", "long_carton"
    ]
    dimensions_m: Dimensions
    mass_min_kg: Positive
    mass_max_kg: Positive
    visual_variant_id: Identifier
    compatibility: dict[ToolId, Compatibility]
    geometry: ProductGeometry

    @model_validator(mode="after")
    def valid_specification(self) -> Self:
        if self.mass_min_kg > self.mass_max_kg:
            raise ValueError("INVALID_MASS_RANGE")
        if len(self.compatibility) != 6 or list(self.compatibility.values()).count("P") != 1:
            raise ValueError("SIX_TOOLS_AND_ONE_PREFERENCE_REQUIRED")
        return self

    @property
    def preferred_tool_id(self) -> ToolId:
        return next(tool for tool, rating in self.compatibility.items() if rating == "P")

    @property
    def compatible_tool_ids(self) -> tuple[ToolId, ...]:
        return tuple(tool for tool, rating in self.compatibility.items() if rating != "N")


class ToolConstraints(V2Contract):
    kind: Literal["flat_top", "grasp_width", "soft_envelope", "under_clearance"]
    minimum_flat_top_m: tuple[Nonnegative, Nonnegative] = (0, 0)
    minimum_width_m: Nonnegative = 0
    maximum_width_m: Nonnegative = 0

    @model_validator(mode="after")
    def valid_constraint(self) -> Self:
        if self.kind in {"grasp_width", "soft_envelope"} and not (
            0 < self.minimum_width_m <= self.maximum_width_m
        ):
            raise ValueError("INVALID_GEOMETRIC_RANGE")
        if self.kind == "flat_top" and min(self.minimum_flat_top_m) <= 0:
            raise ValueError("INVALID_SUCTION_SURFACE")
        return self


class EndEffectorSpec(V2Contract):
    tool_id: ToolId
    family: Literal["vacuum", "pinch", "soft", "fork"]
    display_name: str = Field(min_length=1, max_length=80)
    max_simulated_mass_kg: Positive
    tcp_transform: Pose
    collision_envelope_m: Dimensions
    collision_offset_m: Vector3 = (0, 0, 0.09)
    constraints: ToolConstraints
    visual_asset_id: Identifier
    tool_spec_version: Literal["synthetic-tools-1"] = "synthetic-tools-1"

    @model_validator(mode="after")
    def valid_tcp_metadata(self) -> Self:
        if self.tcp_transform.frame_id != "tool_flange":
            raise ValueError("INVALID_TCP_FRAME")
        if self.tcp_transform.calibration_version != "hkm-cal-1":
            raise ValueError("UNKNOWN_CALIBRATION_VERSION")
        return self


class ToolState(V2Contract):
    active_tool_id: ToolId | None
    changer_state: Literal["READY", "CHANGING", "FAULTED"] = "READY"
    rack_tool_ids: tuple[ToolId, ...]
    tool_state_version: Literal["synthetic-tool-state-1"] = "synthetic-tool-state-1"

    @model_validator(mode="after")
    def unique_occupancy(self) -> Self:
        if len(set(self.rack_tool_ids)) != len(self.rack_tool_ids):
            raise ValueError("DUPLICATE_RACK_TOOL")
        if self.active_tool_id in self.rack_tool_ids:
            raise ValueError("MOUNTED_TOOL_CANNOT_OCCUPY_RACK")
        return self


class RobotState(V2Contract):
    tcp_pose: Pose
    active_tool_id: ToolId | None
    motion_phase: Identifier = "HOME"
    robot_profile_version: Literal["hkm_inspired_v1"] = "hkm_inspired_v1"
    kinematic_model_version: Literal["HKM_INSPIRED_VISUAL_KINEMATICS_V1"] = (
        "HKM_INSPIRED_VISUAL_KINEMATICS_V1"
    )

    @model_validator(mode="after")
    def valid_robot_frame(self) -> Self:
        if (
            self.tcp_pose.frame_id != "cell_world"
            or self.tcp_pose.calibration_version != "hkm-cal-1"
        ):
            raise ValueError("ROBOT_SPATIAL_METADATA_MISMATCH")
        return self


class SensorSpec(V2Contract):
    sensor_id: Identifier
    frame_id: Literal["camera_operator", "camera_overhead", "camera_side"]
    calibration_version: Literal["hkm-cal-1"] = "hkm-cal-1"
    camera_model_version: Literal["synthetic-orthographic-1"] = "synthetic-orthographic-1"
    pose: Pose
    presentation_only: bool

    @model_validator(mode="after")
    def valid_sensor_pose(self) -> Self:
        if (
            self.pose.frame_id != "cell_world"
            or self.pose.calibration_version != self.calibration_version
        ):
            raise ValueError("SENSOR_SPATIAL_METADATA_MISMATCH")
        return self


class ToolCandidate(V2Contract):
    tool_id: ToolId
    compatibility: Compatibility
    compatible: bool
    eligible: bool
    score: int | None
    reasons: tuple[Identifier, ...]


class ToolSelectionDecision(V2Contract):
    product_id: Identifier
    sku: SKU
    selected_tool_id: ToolId
    candidate_tools: tuple[ToolCandidate, ...] = Field(min_length=1, max_length=6)
    assessed_mass_kg: Positive
    tool_change_required: bool
    selection_version: Literal["deterministic-tool-selector-1"] = "deterministic-tool-selector-1"
    product_catalog_version: Literal["synthetic-products-1"] = "synthetic-products-1"
    tool_spec_version: Literal["synthetic-tools-1"] = "synthetic-tools-1"

    @model_validator(mode="after")
    def selected_candidate_present(self) -> Self:
        if len({candidate.tool_id for candidate in self.candidate_tools}) != len(
            self.candidate_tools
        ):
            raise ValueError("DUPLICATE_TOOL_CANDIDATE")
        if not any(
            candidate.tool_id == self.selected_tool_id and candidate.eligible
            for candidate in self.candidate_tools
        ):
            raise ValueError("SELECTED_TOOL_NOT_ELIGIBLE")
        return self


class WorkspaceProfile(V2Contract):
    radial_limit_m: Positive = 1.55
    min_z_m: FiniteFloat = 0.16
    max_z_m: FiniteFloat = 1.15
    safe_transfer_z_m: FiniteFloat = 1.02
    frame_id: Literal["cell_world"] = "cell_world"
    calibration_version: Literal["hkm-cal-1"] = "hkm-cal-1"

    @model_validator(mode="after")
    def ordered_height(self) -> Self:
        if not self.min_z_m < self.safe_transfer_z_m <= self.max_z_m:
            raise ValueError("INVALID_WORKSPACE_HEIGHTS")
        return self


class CollisionObstacle(V2Contract):
    obstacle_id: Identifier
    minimum: Vector3
    maximum: Vector3
    kind: Literal["STATIC", "PRODUCT"] = "STATIC"
    product_id: Identifier | None = None

    @model_validator(mode="after")
    def positive_bounds(self) -> Self:
        if any(low >= high for low, high in zip(self.minimum, self.maximum, strict=True)):
            raise ValueError("INVALID_OBSTACLE_BOUNDS")
        return self


TrajectoryPhase = Literal[
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
    "APPROACH",
    "GRASP",
    "GRASP_CONFIRM",
    "LIFT",
    "SAFE_TRANSFER",
    "PRE_PLACE",
    "PLACE",
    "RELEASE",
    "RELEASE_CONFIRM",
    "RETRACT",
    "NEXT_SAFE_POSE",
]


class TrajectoryWaypoint(V2Contract):
    phase: TrajectoryPhase
    pose: Pose
    sim_time_s: Nonnegative
    attached: bool = False
    active_tool_id: ToolId | None


class TrajectoryIntent(V2Contract):
    trajectory_id: Identifier
    profile: Literal["SAFE_PICK_PLACE_V1"] = "SAFE_PICK_PLACE_V1"
    required_tool_id: ToolId
    grasp_pose: Pose
    target_tcp_pose: Pose
    product_attachment_offset_m: Vector3
    waypoints: tuple[TrajectoryWaypoint, ...] = Field(min_length=14, max_length=128)
    estimated_sim_duration_s: Positive
    route_index: int = Field(ge=0, le=6)
    trajectory_planner_version: Literal["synthetic-trajectory-1"] = "synthetic-trajectory-1"
    collision_check_version: Literal["synthetic-aabb-preflight-1"] = "synthetic-aabb-preflight-1"
    timing_classification: Literal["SIMULATOR_PRESENTATION_TIMING"] = (
        "SIMULATOR_PRESENTATION_TIMING"
    )
    calibration_version: Literal["hkm-cal-1"] = "hkm-cal-1"
    frame_tree_version: Literal["hkm-frame-tree-1"] = "hkm-frame-tree-1"

    @model_validator(mode="after")
    def ordered_time(self) -> Self:
        times = [point.sim_time_s for point in self.waypoints]
        if times[0] != 0 or any(b <= a for a, b in zip(times, times[1:], strict=False)):
            raise ValueError("INVALID_TRAJECTORY_TIME")
        if abs(times[-1] - self.estimated_sim_duration_s) > 1e-6:
            raise ValueError("TRAJECTORY_DURATION_MISMATCH")
        for pose in (
            self.grasp_pose,
            self.target_tcp_pose,
            *(point.pose for point in self.waypoints),
        ):
            if (
                pose.frame_id != "cell_world"
                or pose.calibration_version != self.calibration_version
            ):
                raise ValueError("TRAJECTORY_SPATIAL_METADATA_MISMATCH")
        return self


ROBOTICS_SCHEMAS = (
    ProductGeometry,
    ProductSpec,
    ToolConstraints,
    EndEffectorSpec,
    ToolState,
    RobotState,
    SensorSpec,
    ToolCandidate,
    ToolSelectionDecision,
    WorkspaceProfile,
    CollisionObstacle,
    TrajectoryWaypoint,
    TrajectoryIntent,
)
