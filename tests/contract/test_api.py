import json
from pathlib import Path

from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from apps.api.app import create_app
from robotops.workflow.store import Store


def test_openapi_is_current_and_schemas_validate(tmp_path):
    app = create_app(Store(tmp_path / "api.db"))
    spec = json.loads(Path("contracts/openapi.json").read_text())
    assert app.openapi() == spec
    assert spec["openapi"].startswith("3.1.")
    for schema in spec["components"]["schemas"].values():
        Draft202012Validator.check_schema(schema)


def test_http_intake_idempotency_conflict_and_timeline(tmp_path, order_request):
    client = TestClient(create_app(Store(tmp_path / "api.db")))
    payload = order_request.model_dump(mode="json")
    first = client.post("/orders", json=payload, headers={"Idempotency-Key": "key"})
    assert first.status_code == 201
    second = client.post("/orders", json=payload, headers={"Idempotency-Key": "key"})
    assert first.json() == second.json()
    assert (
        client.post(
            "/orders", json={**payload, "order_id": "changed"}, headers={"Idempotency-Key": "key"}
        ).status_code
        == 409
    )
    assert client.post("/orders", json=payload).status_code == 422
    assert client.get("/orders/missing").status_code == 404
    result = client.get("/orders/order-1/timeline").json()
    assert len(result) == 2
    assert result[1]["causation_id"] == result[0]["event_id"]
    assert client.get("/jobs/" + first.json()["job_ids"][0]).json()["state"] == "RECEIVED"
    assert client.get("/health").status_code == 200
