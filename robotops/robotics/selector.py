"""Deterministic gripper selection from catalogue priors and observed telemetry."""

from math import isfinite

from robotops.robotics.catalogue import load_catalogue
from robotops.robotics.models import (
    EndEffectorSpec,
    ProductSpec,
    ToolCandidate,
    ToolSelectionDecision,
    ToolState,
)


class ToolSelectionError(ValueError):
    def __init__(self, reason: str, candidates: tuple[ToolCandidate, ...]):
        super().__init__(reason)
        self.reason = reason
        self.candidates = candidates


def geometry_reason(product: ProductSpec, tool: EndEffectorSpec) -> str | None:
    rule = tool.constraints
    geometry = product.geometry
    if rule.kind == "flat_top":
        # Upright fixtures permit 90-degree in-plane tool orientation for a
        # planar patch. The comparison is independent of JSON tuple ordering.
        actual = sorted(geometry.flat_top_m)
        required = sorted(rule.minimum_flat_top_m)
        if any(a + 1e-12 < b for a, b in zip(actual, required, strict=True)):
            return "INSUFFICIENT_PLANAR_TOP_SURFACE"
    elif rule.kind in {"grasp_width", "soft_envelope"}:
        width = geometry.grasp_width_m if rule.kind == "grasp_width" else geometry.soft_envelope_m
        if not rule.minimum_width_m - 1e-12 <= width <= rule.maximum_width_m + 1e-12:
            return "GEOMETRY_OUTSIDE_SIMULATED_GRASP_RANGE"
    elif not geometry.under_clearance:
        return "NO_SYNTHETIC_UNDER_CLEARANCE"
    return None


def evaluate_candidate(
    product: ProductSpec,
    tool: EndEffectorSpec,
    observed_tools: ToolState,
    mass_kg: float,
) -> ToolCandidate:
    rating = product.compatibility[tool.tool_id]
    reasons: list[str] = []
    if rating == "N":
        reasons.append("DISALLOWED_PRODUCT_TOOL_PAIR")
    else:
        reasons.append(
            "PREFERRED_FOR_PRODUCT_FAMILY" if rating == "P" else "COMPATIBLE_PRODUCT_FAMILY"
        )
    available = (
        tool.tool_id == observed_tools.active_tool_id
        or tool.tool_id in observed_tools.rack_tool_ids
    )
    if not available:
        reasons.append("TOOL_UNAVAILABLE")
    if observed_tools.changer_state != "READY":
        reasons.append("TOOL_CHANGER_NOT_READY")
    mass_valid = mass_kg <= tool.max_simulated_mass_kg
    reasons.append("MASS_WITHIN_SIMULATED_LIMIT" if mass_valid else "SIMULATED_MASS_LIMIT_EXCEEDED")
    geometric_rejection = geometry_reason(product, tool)
    reasons.append(geometric_rejection or "SYNTHETIC_GEOMETRY_COMPATIBLE")
    eligible = (
        rating != "N"
        and available
        and observed_tools.changer_state == "READY"
        and mass_valid
        and geometric_rejection is None
    )
    score = None
    if eligible:
        # All passing fixture geometries receive the same conservative +10
        # clearance and +10 surface fit. This is not a learned grasp-quality score.
        score = (100 if rating == "P" else 70) + 20
        if tool.tool_id == observed_tools.active_tool_id:
            score += 15
            reasons.append("ALREADY_MOUNTED")
        else:
            score -= 10
            reasons.append("TOOL_CHANGE_REQUIRED")
    return ToolCandidate(
        tool_id=tool.tool_id,
        compatibility=rating,
        compatible=rating != "N",
        eligible=eligible,
        score=score,
        reasons=tuple(reasons),
    )


def select_tool(
    product: ProductSpec,
    observed_tools: ToolState,
    *,
    product_id: str | None = None,
    mass_kg: float | None = None,
    tools: tuple[EndEffectorSpec, ...] | None = None,
) -> ToolSelectionDecision:
    """Use conservative catalogue maximum mass unless typed evidence supplies mass.

    The caller must provide observed cell telemetry; this module cannot read a
    runtime or private WorldState. Catalogue order is the stable tie-breaker.
    """
    assessed_mass = product.mass_max_kg if mass_kg is None else mass_kg
    if not isfinite(assessed_mass) or assessed_mass <= 0:
        raise ToolSelectionError("INVALID_PRODUCT_MASS", ())
    catalogue_tools = tools if tools is not None else load_catalogue().tools
    candidates = tuple(
        evaluate_candidate(product, tool, observed_tools, assessed_mass) for tool in catalogue_tools
    )
    eligible = [
        (candidate, index) for index, candidate in enumerate(candidates) if candidate.eligible
    ]
    if not eligible:
        raise ToolSelectionError("NO_COMPATIBLE_AVAILABLE_TOOL", candidates)
    selected = min(eligible, key=lambda item: (-(item[0].score or 0), item[1], item[0].tool_id))[0]
    return ToolSelectionDecision(
        product_id=product_id or "product-" + product.sku + "-01",
        sku=product.sku,
        selected_tool_id=selected.tool_id,
        candidate_tools=candidates,
        assessed_mass_kg=assessed_mass,
        tool_change_required=selected.tool_id != observed_tools.active_tool_id,
    )
