"""Supported independent simulator cells; each model has an explicit settings factory."""

from robotops.config import Settings
from robotops.domain.models import Contract, Identifier
from robotops.workflow.store import Conflict


class CellProfile(Contract):
    cell_profile_id: Identifier
    display_name: str
    description: str
    selectable: bool
    product_count: int
    tool_count: int


class CellProfiles(Contract):
    default_cell_profile_id: Identifier = "hkm_inspired_v1"
    profiles: tuple[CellProfile, ...]


HKM = CellProfile(
    cell_profile_id="hkm_inspired_v1",
    display_name="HKM1800-inspired warehouse cell",
    description=(
        "Original synthetic hybrid-kinematic manipulator, six product families and six tools. "
        "Not validated HKM1800 geometry, dynamics or safety."
    ),
    selectable=True,
    product_count=6,
    tool_count=6,
)
LEGACY = CellProfile(
    cell_profile_id="legacy_cartesian_v1",
    display_name="Legacy Cartesian cell",
    description="Historical three-product scene retained with its original saved evidence.",
    selectable=False,
    product_count=3,
    tool_count=1,
)


def cell_profiles() -> CellProfiles:
    return CellProfiles(profiles=(HKM, LEGACY))


def profile_for(settings: Settings) -> CellProfile:
    return HKM if settings.is_hkm else LEGACY


def profile_settings(profile_id: str, *, visual_frame_seconds: float) -> Settings:
    if profile_id != HKM.cell_profile_id:
        raise Conflict("CELL_PROFILE_NOT_AVAILABLE")
    return Settings.hkm(visual_frame_seconds=visual_frame_seconds)


CELL_PROFILE_SCHEMAS = (CellProfile, CellProfiles)
