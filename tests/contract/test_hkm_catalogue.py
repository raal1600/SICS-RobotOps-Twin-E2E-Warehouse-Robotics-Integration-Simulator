import copy

import jsonschema
import pytest
from pydantic import ValidationError

from robotops.domain.base import Pose
from robotops.robotics.catalogue import (
    CATALOGUE_SCHEMAS,
    RoboticsCatalogue,
    fixture_source_pose,
    fixture_target_pose,
    initial_tool_state,
    load_catalogue,
    product_spec,
    tool_spec,
)
from robotops.robotics.catalogue_data import raw_catalogue
from robotops.robotics.models import (
    ROBOTICS_SCHEMAS,
    ProductSpec,
    RobotState,
    SensorSpec,
    ToolState,
    WorkspaceProfile,
)


def test_hkm_catalogue_has_exact_six_specs_and_canonical_compatibility_matrix():
    catalogue = load_catalogue()
    assert len(catalogue.products) == len(catalogue.tools) == 6
    expected = ["PCCCCC", "CPNCCC", "CNCNPC", "NNPCCN", "CCCP CN".replace(" ", ""), "NCNCNP"]
    assert [
        "".join(product.compatibility[tool.tool_id] for tool in catalogue.tools)
        for product in catalogue.products
    ] == expected
    dimensions = [
        (0.120, 0.080, 0.045),
        (0.240, 0.160, 0.100),
        (0.180, 0.120, 0.040),
        (0.075, 0.075, 0.230),
        (0.090, 0.090, 0.120),
        (0.420, 0.090, 0.060),
    ]
    masses = [(0.15, 0.4), (0.5, 1.2), (0.08, 0.35), (0.25, 0.75), (0.3, 0.8), (0.6, 1.8)]
    assert [product.dimensions_m for product in catalogue.products] == dimensions
    assert [(product.mass_min_kg, product.mass_max_kg) for product in catalogue.products] == masses
    assert max(product.mass_max_kg for product in catalogue.products) < 2
    assert catalogue.classification == "SIMULATOR_DESIGN"
    assert catalogue.public_reference.classification == "COMPANY_REPORTED_CLAIM"
    assert catalogue.workspace.radial_limit_m < catalogue.public_reference.nominal_radial_reach_m
    assert sum(camera.presentation_only for camera in catalogue.cameras) == 1


def test_hkm_fixture_locations_and_slots_have_distinct_nonoverlapping_footprints():
    catalogue = load_catalogue()
    assert len(set(source.location_id for source in catalogue.layout.sources.values())) == 6
    for product in catalogue.products:
        source = fixture_source_pose(product.sku)
        target = fixture_target_pose(product.sku)
        clearance = {"SKU-C": 0.02, "SKU-F": 0.04}.get(product.sku, 0)
        assert source.position[2] == pytest.approx(0.18 + clearance + product.dimensions_m[2] / 2)
        assert target.position[2] == source.position[2]
        assert source.calibration_version == target.calibration_version == "hkm-cal-1"
        for other in catalogue.products:
            if product.sku == other.sku:
                continue
            other_target = fixture_target_pose(other.sku)
            assert any(
                abs(target.position[axis] - other_target.position[axis])
                > (product.dimensions_m[axis] + other.dimensions_m[axis]) / 2
                for axis in (0, 1)
            )


@pytest.mark.parametrize("model", ROBOTICS_SCHEMAS + CATALOGUE_SCHEMAS)
def test_hkm_contracts_have_strict_versioned_json_schemas(model):
    schema = model.model_json_schema()
    jsonschema.Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    assert schema["properties"]["schema_version"]["const"] == "2.0"


@pytest.mark.parametrize(
    "update",
    [
        {"surprise": "not permitted"},
        {"sku": "SKU-Z"},
        {"mass_max_kg": -1},
        {"dimensions_m": (0, 1, 1)},
        {"dimensions_m": (float("inf"), 1, 1)},
        {"mass_min_kg": 2, "mass_max_kg": 1},
    ],
)
def test_hkm_product_contract_rejects_unknown_invalid_or_nonfinite_data(update):
    with pytest.raises(ValidationError):
        ProductSpec.model_validate({**product_spec("SKU-A").model_dump(), **update})


def test_hkm_catalogue_rejects_unknown_tools_duplicate_ids_and_incomplete_layout():
    for mutate in (
        lambda data: data["tools"][0].update(tool_id="UNKNOWN_TOOL"),
        lambda data: data["products"][0].update(compatibility={"EE_VAC_SINGLE": "P"}),
        lambda data: data["products"][0]["compatibility"].update(EE_VAC_ARRAY="P"),
        lambda data: data["tools"][0]["tcp_transform"].update(calibration_version="old-cal"),
        lambda data: data["tools"][0]["tcp_transform"].update(frame_id="unknown_frame"),
        lambda data: data["tools"][0]["tcp_transform"].update(quaternion_xyzw=[0, 0, 0, 0]),
        lambda data: data["layout"]["sources"].pop("SKU-A"),
        lambda data: data["layout"]["tool_docks"].pop("EE_VAC_SINGLE"),
        lambda data: data["layout"]["home_tcp_pose"].update(calibration_version="old-cal"),
        lambda data: data["products"].__setitem__(1, copy.deepcopy(data["products"][0])),
        lambda data: data["tools"].__setitem__(1, copy.deepcopy(data["tools"][0])),
        lambda data: data["cameras"].__setitem__(1, copy.deepcopy(data["cameras"][0])),
        lambda data: data["visual_motion"].update(transfer_min_s=10),
        lambda data: data["tools"][0]["constraints"].update(minimum_flat_top_m=[0, 0]),
        lambda data: data["tools"][2]["constraints"].update(minimum_width_m=0),
    ):
        data = raw_catalogue()
        mutate(data)
        with pytest.raises(ValidationError):
            RoboticsCatalogue.model_validate(data)


def test_hkm_mounted_tool_and_rack_occupancy_are_explicit_and_unique():
    state = initial_tool_state()
    assert state.active_tool_id == "EE_VAC_SINGLE"
    assert len(state.rack_tool_ids) == 5
    for rack in ((state.active_tool_id,), ("EE_VAC_ARRAY", "EE_VAC_ARRAY")):
        with pytest.raises(ValidationError):
            ToolState(active_tool_id=state.active_tool_id, rack_tool_ids=rack)
    with pytest.raises(ValidationError):
        ToolState(active_tool_id="UNKNOWN", rack_tool_ids=())
    with pytest.raises(ValueError, match="UNKNOWN_SKU"):
        product_spec("invalid")
    with pytest.raises(ValueError, match="UNKNOWN_TOOL"):
        tool_spec("invalid")


def test_hkm_spatial_contracts_require_known_calibration_and_frames():
    with pytest.raises(ValidationError):
        WorkspaceProfile(min_z_m=1.1)
    with pytest.raises(ValidationError):
        RobotState(tcp_pose=Pose(position=(0, 0, 0.5)), active_tool_id=None)
    sensor = load_catalogue().cameras[1].model_dump()
    sensor["pose"]["frame_id"] = "unknown_frame"
    with pytest.raises(ValidationError):
        SensorSpec.model_validate(sensor)


def test_hkm_catalogue_mutation_cannot_change_another_experiment():
    first = load_catalogue()
    first.products[0].compatibility["EE_VAC_SINGLE"] = "N"
    assert load_catalogue().products[0].preferred_tool_id == "EE_VAC_SINGLE"
    raw = raw_catalogue()
    raw["products"][0]["sku"] = "BROKEN"
    assert raw_catalogue()["products"][0]["sku"] == "SKU-A"


def test_hkm_individual_spec_lookups_preserve_nested_mutation_isolation():
    first = product_spec("SKU-A")
    first.compatibility["EE_VAC_SINGLE"] = "N"
    fresh = product_spec("SKU-A")
    assert fresh.compatibility["EE_VAC_SINGLE"] == "P"
    assert load_catalogue().products[0].compatibility["EE_VAC_SINGLE"] == "P"
    first_tool = tool_spec("EE_VAC_SINGLE")
    fresh_tool = tool_spec("EE_VAC_SINGLE")
    assert first_tool == fresh_tool and first_tool is not fresh_tool
    assert first_tool.constraints is not fresh_tool.constraints
    assert first_tool.tcp_transform is not fresh_tool.tcp_transform


def test_hkm_individual_spec_lookup_does_not_clone_unrelated_catalogue(monkeypatch):
    def unrelated_copy(*args, **kwargs):
        raise AssertionError("Single-spec lookups must not clone all six tools and the cell")

    monkeypatch.setattr(RoboticsCatalogue, "model_copy", unrelated_copy)
    assert product_spec("SKU-A").preferred_tool_id == "EE_VAC_SINGLE"
    assert tool_spec("EE_SUPPORT_FORK").tool_id == "EE_SUPPORT_FORK"
