"""One canonical, typed catalogue of original simulator assets and constraints."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, model_validator

from robotops.domain.base import Identifier, Pose, V2Contract
from robotops.robotics.catalogue_data import raw_catalogue
from robotops.robotics.models import (
    SKU,
    Dimensions,
    EndEffectorSpec,
    Nonnegative,
    Positive,
    ProductSpec,
    SensorSpec,
    ToolId,
    ToolState,
    Vector3,
    WorkspaceProfile,
)


class PublicReference(V2Contract):
    classification: Literal["COMPANY_REPORTED_CLAIM"]
    nominal_radial_reach_m: Positive
    approximate_z_stroke_m: Positive


class MotionTiming(V2Contract):
    classification: Literal["SIMULATOR_PRESENTATION_TIMING"]
    approach_s: Positive
    grasp_dwell_s: Positive
    lift_s: Positive
    transfer_speed_m_s: Positive
    transfer_min_s: Positive
    transfer_max_s: Positive
    place_s: Positive
    release_dwell_s: Positive
    retract_s: Positive
    tool_change_s: Positive


class ContainerFixture(V2Contract):
    location_id: Identifier
    pose: Pose
    interior_m: tuple[Positive, Positive]
    wall_height_m: Positive
    product_support_offset_m: Nonnegative = 0


class CellLayout(V2Contract):
    floor_width_m: Positive
    floor_depth_m: Positive
    home_tcp_pose: Pose
    sources: dict[SKU, ContainerFixture]
    destination: ContainerFixture
    destination_slots: dict[SKU, Vector3]
    tool_docks: dict[ToolId, Pose]

    @model_validator(mode="after")
    def complete_layout(self) -> Self:
        if len(self.sources) != 6 or set(self.sources) != set(self.destination_slots):
            raise ValueError("SIX_SOURCE_AND_DESTINATION_SLOTS_REQUIRED")
        if len(self.tool_docks) != 6:
            raise ValueError("SIX_TOOL_DOCKS_REQUIRED")
        poses = (
            self.home_tcp_pose,
            self.destination.pose,
            *(source.pose for source in self.sources.values()),
            *self.tool_docks.values(),
        )
        if any(
            pose.frame_id != "cell_world" or pose.calibration_version != "hkm-cal-1"
            for pose in poses
        ):
            raise ValueError("LAYOUT_SPATIAL_METADATA_MISMATCH")
        return self


class RoboticsCatalogue(V2Contract):
    classification: Literal["SIMULATOR_DESIGN"]
    profile_version: Literal["hkm_inspired_v1"]
    robot_profile_version: Literal["hkm_inspired_v1"]
    product_catalog_version: Literal["synthetic-products-1"]
    tool_catalog_version: Literal["synthetic-tools-1"]
    frame_tree_version: Literal["hkm-frame-tree-1"]
    public_reference: PublicReference
    workspace: WorkspaceProfile
    visual_motion: MotionTiming
    empty_flange_collision_envelope_m: Dimensions
    empty_flange_collision_offset_m: Vector3
    products: tuple[ProductSpec, ...] = Field(min_length=6, max_length=6)
    tools: tuple[EndEffectorSpec, ...] = Field(min_length=6, max_length=6)
    layout: CellLayout
    cameras: tuple[SensorSpec, ...] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def unique_catalogue(self) -> Self:
        if len({item.sku for item in self.products}) != 6:
            raise ValueError("SIX_UNIQUE_PRODUCTS_REQUIRED")
        if len({item.tool_id for item in self.tools}) != 6:
            raise ValueError("SIX_UNIQUE_TOOLS_REQUIRED")
        if len({item.sensor_id for item in self.cameras}) != 3:
            raise ValueError("THREE_UNIQUE_CAMERAS_REQUIRED")
        if self.visual_motion.transfer_min_s > self.visual_motion.transfer_max_s:
            raise ValueError("INVALID_TRANSFER_TIMING")
        return self


@lru_cache(maxsize=1)
def _canonical_catalogue() -> RoboticsCatalogue:
    return RoboticsCatalogue.model_validate(raw_catalogue())


def load_catalogue() -> RoboticsCatalogue:
    # Pydantic's frozen setting does not make nested dictionaries immutable.
    # Give callers independent maps so one experiment cannot change another.
    return _canonical_catalogue().model_copy(deep=True)


def product_spec(sku: str) -> ProductSpec:
    for item in load_catalogue().products:
        if item.sku == sku:
            return item
    raise ValueError("UNKNOWN_SKU")


def tool_spec(tool_id: str) -> EndEffectorSpec:
    for item in load_catalogue().tools:
        if item.tool_id == tool_id:
            return item
    raise ValueError("UNKNOWN_TOOL")


def preferred_tool(sku: str) -> ToolId:
    return product_spec(sku).preferred_tool_id


def fixture_source_pose(sku: str) -> Pose:
    product = product_spec(sku)
    fixture = load_catalogue().layout.sources[product.sku]
    anchor = fixture.pose
    x, y, z = anchor.position
    return anchor.model_copy(
        update={
            "position": (x, y, z + fixture.product_support_offset_m + product.dimensions_m[2] / 2)
        }
    )


def fixture_target_pose(sku: str) -> Pose:
    product = product_spec(sku)
    layout = load_catalogue().layout
    x, y, z = layout.destination.pose.position
    dx, dy, dz = layout.destination_slots[product.sku]
    return layout.destination.pose.model_copy(
        update={
            "position": (x + dx, y + dy, z + dz + product.dimensions_m[2] / 2),
        }
    )


def initial_tool_state() -> ToolState:
    tools = load_catalogue().tools
    return ToolState(
        active_tool_id=tools[0].tool_id, rack_tool_ids=tuple(tool.tool_id for tool in tools[1:])
    )


CATALOGUE_SCHEMAS = (PublicReference, MotionTiming, ContainerFixture, CellLayout, RoboticsCatalogue)
