import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from robotops.domain.models import SCHEMAS, OrderRequest, Pose, WorldObservation, WorldState


@pytest.mark.parametrize("model", SCHEMAS)
def test_versioned_schema_matches_source(model):
    schema = json.loads(Path(f"contracts/schemas/{model.__name__}.json").read_text())
    Draft202012Validator.check_schema(schema)
    assert schema == model.model_json_schema()
    assert schema["additionalProperties"] is False
    assert schema["properties"]["schema_version"]["const"] == "1.0"


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
