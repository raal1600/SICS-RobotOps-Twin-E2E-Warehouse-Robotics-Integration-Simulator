import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from apps.api.test_sessions import TEST_SCHEMAS
from robotops.blender.visualization import VISUAL_SCHEMAS
from robotops.domain.base import V2Contract, VersionedContract, VersionedRecord
from robotops.domain.models import SCHEMAS, OrderRequest, Pose, WorldObservation, WorldState
from robotops.robotics.catalogue import CATALOGUE_SCHEMAS
from robotops.robotics.models import ROBOTICS_SCHEMAS


@pytest.mark.parametrize(
    "model", (*SCHEMAS, *VISUAL_SCHEMAS, *TEST_SCHEMAS, *ROBOTICS_SCHEMAS, *CATALOGUE_SCHEMAS)
)
def test_versioned_schema_matches_source(model):
    schema = json.loads(Path(f"contracts/schemas/{model.__name__}.json").read_text())
    Draft202012Validator.check_schema(schema)
    assert schema == model.model_json_schema()
    assert schema["additionalProperties"] is False
    version = schema["properties"]["schema_version"]
    if issubclass(model, (VersionedContract, VersionedRecord)):
        assert version["enum"] == ["1.0", "2.0"]
    else:
        assert version["const"] == ("2.0" if issubclass(model, V2Contract) else "1.0")
    # FastAPI must expose the strict wire contract after legacy serialization.
    assert model.model_json_schema(mode="serialization") == schema


@pytest.mark.parametrize(
    "updates",
    [
        {"unit": "mm"},
        {"position": [float("nan"), 0, 0]},
        {"quaternion_xyzw": [0, 0, 0, 0]},
        {"code": "print('forbidden')"},
        {"schema_version": "2.0"},
    ],
)
def test_spatial_contract_rejects_invalid_values(updates):
    with pytest.raises(ValidationError):
        Pose.model_validate({"position": [0, 0, 0], **updates})


def test_truth_cannot_be_substituted_for_observation():
    assert not issubclass(WorldState, WorldObservation)
    with pytest.raises(ValidationError):
        WorldObservation.model_validate({"objects": [], "step": 0})


def test_order_rejects_duplicate_lines_and_same_locations():
    line = {"order_line_id": "l1", "product_id": "p1", "source_id": "a", "destination_id": "b"}
    with pytest.raises(ValidationError):
        OrderRequest.model_validate({"order_id": "o1", "lines": [line, line]})
    with pytest.raises(ValidationError):
        OrderRequest.model_validate({"order_id": "o1", "lines": [{**line, "destination_id": "a"}]})
