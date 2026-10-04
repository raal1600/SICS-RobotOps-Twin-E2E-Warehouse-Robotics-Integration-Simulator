from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api.__main__ import main
from apps.api.app import create_app
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.robotics.catalogue import load_catalogue
from robotops.workflow.store import Store


def order_payload(fixture, index=0, order_id="hkm-api-order"):
    product = fixture["products"][index]["product_id"]
    return {
        "order_id": order_id,
        "lines": [
            {
                "order_line_id": "line",
                "product_id": product,
                "source_id": fixture["product_sources"][product],
                "destination_id": fixture["destination_id"],
            }
        ],
    }


def test_fresh_api_fixture_and_six_product_orders_use_catalogued_sources_and_tools(tmp_path):
    app = create_app(Store(tmp_path / "workflow.db"))
    client = TestClient(app)
    fixture = client.get("/fixtures").json()
    catalogue = load_catalogue()
    assert fixture["robot_profile_version"] == catalogue.profile_version
    assert fixture["catalogue"] == catalogue.model_dump(mode="json")
    assert len(fixture["products"]) == len(fixture["product_sources"]) == 6
    assert len(set(fixture["product_sources"].values())) == 6
    assert fixture["destination_id"] == catalogue.layout.destination.location_id
    assert fixture["destination_id"] not in fixture["product_sources"].values()
    assert fixture["source_id"] == fixture["product_sources"][fixture["products"][0]["product_id"]]
    engine = app.state.test_registry.original
    for index, spec in enumerate(catalogue.products):
        payload = order_payload(fixture, index, f"order-{spec.sku}")
        response = client.post("/orders", json=payload, headers={"Idempotency-Key": spec.sku})
        assert response.status_code == 201, response.text
        job_id = response.json()["job_ids"][0]
        response = client.post(f"/jobs/{job_id}/run", json={})
        assert response.status_code == 200, response.text
        job = response.json()
        assert job["state"] == "COMPLETED", job
        receipt = engine.runtime.journal(job["command_id"])
        assert receipt.effect_count == 1
        assert receipt.active_tool_id == spec.preferred_tool_id
    assert sum(event.event_type == "PICK_EFFECT" for event in engine.runtime.events()) == 6


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("product_id", "unknown", "PRODUCT_NOT_IN_FIXTURE"),
        ("source_id", "SRC_B", "PRODUCT_SOURCE_MISMATCH"),
        ("destination_id", "SRC_B", "DESTINATION_MISMATCH"),
    ],
)
def test_new_api_order_rejects_invalid_fixture_before_creating_job(tmp_path, field, value, reason):
    app = create_app(Store(tmp_path / "workflow.db"))
    client = TestClient(app)
    payload = order_payload(client.get("/fixtures").json())
    payload["lines"][0][field] = value
    response = client.post("/orders", json=payload, headers={"Idempotency-Key": "invalid"})
    assert response.status_code == 422
    assert response.json()["detail"] == reason
    engine = app.state.test_registry.original
    assert engine.store.orders() == []
    assert engine.store.timeline() == []
    assert engine.runtime.events() == []


def test_api_fixture_validation_preserves_duplicate_and_conflict_semantics(tmp_path):
    app = create_app(Store(tmp_path / "workflow.db"))
    client = TestClient(app)
    payload = order_payload(client.get("/fixtures").json())
    first = client.post("/orders", json=payload, headers={"Idempotency-Key": "same"})
    assert first.status_code == 201
    assert (
        client.post("/orders", json=payload, headers={"Idempotency-Key": "same"}).json()
        == first.json()
    )
    payload["lines"][0]["source_id"] = "wrong"
    # Existing identity conflicts remain conflicts even if changed input also
    # fails fixture validation. No second job or command is created.
    for key in ("same", "different"):
        response = client.post("/orders", json=payload, headers={"Idempotency-Key": key})
        assert response.status_code == 409
    engine = app.state.test_registry.original
    assert len(engine.store.orders()) == 1
    assert len(engine.store.order(payload["order_id"]).job_ids) == 1
    assert engine.runtime.events() == []


def test_new_hkm_test_preserves_legacy_world_and_each_profile_after_restart(tmp_path):
    runtime = SyntheticRuntime(tmp_path / "runtime.db", Settings())
    before = runtime.world().model_dump_json()
    path = tmp_path / "workflow.db"
    client = TestClient(create_app(Store(path)))
    legacy = client.get("/fixtures").json()
    assert legacy["catalogue"] is None
    assert legacy["robot_profile_version"] is None
    assert set(legacy["product_sources"].values()) == {"source"}
    assert len(legacy["products"]) == 3
    response = client.post("/simulation-tests", json={"request_id": str(uuid4())})
    assert response.status_code == 201
    prefix = "/simulation-tests/" + response.json()["test_id"]
    fresh = client.get(prefix + "/fixtures").json()
    assert fresh["robot_profile_version"] == "hkm_inspired_v1"
    assert len(fresh["products"]) == 6
    assert fresh["scene_epoch"] != legacy["scene_epoch"]
    restarted = TestClient(create_app(Store(path), recover=True))
    assert restarted.get("/fixtures").json() == legacy
    assert restarted.get(prefix + "/fixtures").json() == fresh
    assert runtime.world().model_dump_json() == before


def test_archived_nonoriginal_legacy_test_uses_its_own_saved_settings(tmp_path):
    store = Store(tmp_path / "workflow.db")
    app = create_app(store)
    registry = app.state.test_registry
    legacy_id = uuid4()
    directory = registry.root / str(legacy_id)
    legacy_runtime = SyntheticRuntime(directory / "runtime.db", Settings())
    legacy_world = legacy_runtime.world().model_dump_json()
    # Reconstruct a catalogued test created by the previous release.
    with registry.exclusive() as db:
        db.execute(
            "INSERT INTO tests(id,created) VALUES (?,?)",
            (str(legacy_id), legacy_runtime.world().timestamp.isoformat()),
        )
        db.execute("UPDATE active SET test_id=? WHERE id=1", (str(legacy_id),))
    client = TestClient(app)
    legacy_prefix = f"/simulation-tests/{legacy_id}"
    legacy = client.get(legacy_prefix + "/fixtures").json()
    assert legacy["catalogue"] is None
    assert len(legacy["products"]) == 3
    response = client.post("/simulation-tests", json={"request_id": str(uuid4())})
    assert response.status_code == 201
    restarted = TestClient(create_app(Store(store.path), recover=True))
    assert restarted.get(legacy_prefix + "/fixtures").json() == legacy
    assert legacy_runtime.world().model_dump_json() == legacy_world


@pytest.mark.parametrize("persisted", [None, "legacy", "hkm"])
def test_cli_default_profile_and_saved_profile_are_resolved_by_runtime(
    tmp_path, monkeypatch, persisted
):
    if persisted:
        saved = Settings() if persisted == "legacy" else Settings.hkm()
        SyntheticRuntime(tmp_path / "runtime.db", saved)
    arguments = ["robotops-api", "--data-dir", str(tmp_path), "--port", "8765"]
    if persisted == "hkm":
        # Explicit old settings cannot silently downgrade persisted HKM state.
        config = tmp_path / "legacy.json"
        config.write_text(Settings().model_dump_json())
        arguments += ["--settings", str(config)]
    captured = []
    monkeypatch.setattr("sys.argv", arguments)
    monkeypatch.setattr("apps.api.__main__.uvicorn.run", lambda app, **kwargs: captured.append(app))
    main()
    fixture = TestClient(captured[0]).get("/fixtures").json()
    assert fixture["robot_profile_version"] == (
        None if persisted == "legacy" else "hkm_inspired_v1"
    )
    assert len(fixture["products"]) == (3 if persisted == "legacy" else 6)
