from pydantic import Field

from robotops.domain.models import Contract, Identifier, InventoryLocation, Pose, Product


class Settings(Contract):
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
