from typing import Any, ClassVar, Literal, Self

from pydantic import Field, model_validator

from robotops.domain.models import Contract, Identifier, InventoryLocation, Pose, Product
from robotops.robotics.catalogue import fixture_target_pose, load_catalogue, product_spec


class Settings(Contract):
    schema_version: Literal["1.0", "2.0"] = "1.0"
    extension_fields: ClassVar[frozenset[str]] = frozenset(
        {"robot_profile_version", "product_sources"}
    )
    robot_profile_version: Literal["hkm_inspired_v1"] | None = None
    product_sources: dict[str, str] | None = None
    seed: int = 7
    pose_noise_m: float = Field(default=0, ge=0, allow_inf_nan=False)
    pose_tolerance_m: float = Field(default=0.005, ge=0, allow_inf_nan=False)
    min_confidence: float = Field(default=0.9, ge=0, le=1)
    freshness_seconds: float = Field(default=5, gt=0)
    max_uncertainty_m: float = Field(default=0.02, ge=0)
    workspace_min: tuple[float, float, float] = (-2, -2, 0)
    workspace_max: tuple[float, float, float] = (2, 2, 2)
    frame_id: Identifier = "cell_world"
    calibration_version: Identifier = "cal-1"
    lease_seconds: float = Field(default=120, gt=0)
    brain_timeout_seconds: float = Field(default=2, gt=0)
    runtime_timeout_seconds: float = Field(default=60, gt=0)
    visual_frame_seconds: float = Field(default=0, ge=0, le=0.1, allow_inf_nan=False)
    retry_policy: str = "manual_after_proven_no_effect"
    products: tuple[Product, ...] = (
        Product(product_id="product-red", sku="RED"),
        Product(product_id="product-blue", sku="BLUE"),
        Product(product_id="product-green", sku="GREEN"),
    )
    locations: tuple[InventoryLocation, ...] = (
        InventoryLocation(location_id="source", pose=Pose(position=(-0.6, 0, 0.2))),
        InventoryLocation(location_id="destination", pose=Pose(position=(0.6, 0, 0.2))),
    )

    @property
    def is_hkm(self) -> bool:
        return self.robot_profile_version == "hkm_inspired_v1"

    @classmethod
    def hkm(cls, **overrides: Any) -> Self:
        catalogue = load_catalogue()
        products = tuple(
            Product(product_id=f"product-{item.sku}-01", sku=item.sku)
            for item in catalogue.products
        )
        values = dict(
            schema_version="2.0",
            robot_profile_version=catalogue.profile_version,
            frame_id=catalogue.workspace.frame_id,
            calibration_version=catalogue.workspace.calibration_version,
            products=products,
            locations=tuple(
                InventoryLocation(location_id=source.location_id, pose=source.pose)
                for source in [*catalogue.layout.sources.values(), catalogue.layout.destination]
            ),
            product_sources={
                p.product_id: catalogue.layout.sources[product_spec(p.sku).sku].location_id
                for p in products
            },
        )
        return cls.model_validate({**values, **overrides})

    def source_for(self, product_id: str) -> str:
        if self.product_sources is not None:
            return self.product_sources[product_id]
        return self.locations[0].location_id

    @property
    def destination_id(self) -> str:
        return (
            load_catalogue().layout.destination.location_id
            if self.is_hkm
            else self.locations[1].location_id
        )

    def target_pose(self, product_id: str, destination: InventoryLocation) -> Pose:
        if not self.is_hkm:
            return destination.pose
        product = next(p for p in self.products if p.product_id == product_id)
        if destination.location_id != self.destination_id:
            raise ValueError("DESTINATION_MISMATCH")
        return fixture_target_pose(product.sku)

    @model_validator(mode="after")
    def supported_profile(self) -> Self:
        if self.schema_version == "2.0":
            if not self.is_hkm or self.product_sources is None:
                raise ValueError("HKM_SETTINGS_REQUIRED")
            if self.calibration_version != "hkm-cal-1" or self.frame_id != "cell_world":
                raise ValueError("UNKNOWN_CALIBRATION_OR_FRAME")
            if len(self.products) != 6 or {p.sku for p in self.products} != {
                p.sku for p in load_catalogue().products
            }:
                raise ValueError("SIX_CATALOGUED_PRODUCTS_REQUIRED")
            locations = {loc.location_id for loc in self.locations}
            if len(locations) != len(self.locations) or len(
                {p.product_id for p in self.products}
            ) != len(self.products):
                raise ValueError("DUPLICATE_FIXTURE_IDENTITY")
            if (
                set(self.product_sources) != {p.product_id for p in self.products}
                or not set(self.product_sources.values()) <= locations
            ):
                raise ValueError("PRODUCT_SOURCE_MAP_MISMATCH")
            catalogue = load_catalogue()
            if any(
                self.product_sources[p.product_id]
                != catalogue.layout.sources[product_spec(p.sku).sku].location_id
                for p in self.products
            ):
                raise ValueError("PRODUCT_SOURCE_MAP_MISMATCH")
        return self
