"""The same guided stages across real PostgreSQL, AMQP and OPC UA services."""

import socket
import threading
import time
from uuid import uuid4

import httpx
import pytest
import uvicorn
from fastapi.testclient import TestClient

from robotops.lab.api import create_app
from robotops.lab.business import create_app as business_app
from robotops.lab.transport import EdgeAdapter

pytestmark = pytest.mark.lab_integration


@pytest.mark.parametrize(
    "fault", [None, "DROP_ACK_AFTER_EFFECT", "DUPLICATE_DELIVERY", "PLC_RESTART", "WMS_UNAVAILABLE"]
)
def test_guided_network_stack_recovers_without_repeating_motion(
    lab_config, tmp_path, monkeypatch, fault
):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        business_port = listener.getsockname()[1]
    business_server = uvicorn.Server(
        uvicorn.Config(
            business_app(lab_config), host="127.0.0.1", port=business_port, log_level="error"
        )
    )
    business_thread = threading.Thread(target=business_server.run, daemon=True)
    business_thread.start()
    deadline = time.monotonic() + 10
    while not business_server.started and time.monotonic() < deadline:
        time.sleep(0.01)
    assert business_server.started
    for name, value in {
        "ROBOTOPS_POSTGRES_DSN": lab_config.postgres_dsn,
        "ROBOTOPS_AMQP_URL": lab_config.amqp_url,
        "ROBOTOPS_OPCUA_URL": lab_config.opcua_url,
        "ROBOTOPS_EDGE_URL": lab_config.edge_url,
        "ROBOTOPS_AMQP_QUEUE": lab_config.queue,
        "ROBOTOPS_AMQP_ROUTING_KEY": lab_config.routing_key,
        "ROBOTOPS_LAB_DATA": str(tmp_path / "lab-runtime"),
        "ROBOTOPS_LAB_RUNTIME": "synthetic",
        "ROBOTOPS_WMS_URL": f"http://127.0.0.1:{business_port}",
    }.items():
        monkeypatch.setenv(name, value)
    edge = EdgeAdapter(lab_config)
    stopped = threading.Event()
    errors = []

    def consume():
        try:
            while not stopped.is_set():
                edge.consume_one()
                stopped.wait(0.05)
        except BaseException as error:
            errors.append(error)

    worker = threading.Thread(target=consume, daemon=True)
    worker.start()
    app = create_app()
    workflow = app.state.workflow
    try:
        with TestClient(app) as client:
            assert client.get("/health").json()["capabilities"]["test_lifecycle"] is False
            request = {
                "request_id": uuid4().hex,
                "fault": fault,
                "request": {
                    "order_id": uuid4().hex,
                    "lines": [
                        {
                            "order_line_id": "line-1",
                            "product_id": "product-SKU-A-01",
                            "source_id": workflow.settings.source_for("product-SKU-A-01"),
                            "destination_id": workflow.settings.destination_id,
                        }
                    ],
                },
            }
            bypass = client.post(
                "/orders", json=request["request"], headers={"Idempotency-Key": uuid4().hex}
            )
            assert bypass.status_code == 409
            assert bypass.json()["reason"] == "LAB_REQUIRES_VERSIONED_WMS_INTAKE"
            bypass = client.post("/jobs/uncreated-job/run", json={})
            assert bypass.status_code == 409
            assert bypass.json()["reason"] == "LAB_REQUIRES_BOUNDED_INTEGRATION_STAGES"
            assert workflow.store.orders() == []
            assert workflow.runtime.world().step == 0
            response = client.post("/v1/wms/tasks", json=request)
            assert response.status_code == 202, response.text
            session = response.json()
            path = "/integration/sessions/" + session["session_id"]
            resumed = False
            recovered = False
            retry_seen = False
            for _ in range(40):
                if session["status"] == "COMPLETED":
                    break
                if session["current_stage"] < 16:
                    assert workflow.runtime.world().step == 0
                if session["current_stage"] == 15 and not resumed:
                    with TestClient(create_app()) as reload_client:
                        assert reload_client.get(path).json()["revision"] == session["revision"]
                        with reload_client.websocket_connect(path + "/stream") as stream:
                            assert stream.receive_json()["revision"] == session["revision"]
                    resumed = True
                if session["status"] == "UNKNOWN_OUTCOME":
                    assert workflow.runtime.world().step == 1
                    response = client.post(
                        path + "/reconcile",
                        json={
                            "request_id": uuid4().hex,
                            "expected_revision": session["revision"],
                        },
                    )
                    recovered = True
                else:
                    retry_seen |= session["status"] == "RETRYABLE_FAILURE"
                    authorization = {
                        "request_id": uuid4().hex,
                        "expected_revision": session["revision"],
                        "stage": session["current_stage"],
                    }
                    response = client.post(path + "/authorize", json=authorization)
                    if session["current_stage"] == 16:
                        duplicate = client.post(path + "/authorize", json=authorization)
                        assert duplicate.status_code == 200
                        assert duplicate.json()["revision"] == response.json()["revision"]
                assert response.status_code == 200, response.text
                session = response.json()
            assert session["status"] == "COMPLETED", session
            assert resumed
            assert recovered == (fault == "DROP_ACK_AFTER_EFFECT")
            assert retry_seen == (fault == "WMS_UNAVAILABLE")
            if fault == "WMS_UNAVAILABLE":
                business_steps = [step for step in session["steps"] if step["stage"] == 20]
                assert [step["status"] for step in business_steps] == ["FAILED", "COMPLETED"]
                failed = business_steps[0]
                assert failed["protocol"] == "REST"
                assert failed["classification"] == "REAL PROTOCOL"
                assert failed["source"]["symbol"] == "LabBridge.reconcile_business"
                assert failed["wire"]["protocol_evidence_confirmed"] is True
                assert failed["wire"]["http_response"] == {
                    "method": "POST",
                    "path": "/v1/wms/acknowledgements",
                    "status_code": 503,
                }
                assert failed["wire"]["wms_acknowledged"] is False
                assert failed["wire"]["physical_retry"] is False
            receipt = workflow.runtime.recorded_journal(session["command_id"])
            assert receipt.effect_count == 1
            assert workflow.runtime.world().step == 1
            assert workflow.store.order(session["order_id"]).status == "COMPLETED"
            assert workflow.lab.status(session["command_id"])["result"]["effect_count"] == 1
            business_payload = {
                "command_id": session["command_id"],
                "job_id": session["job_id"],
                "verified_outcome": "COMPLETED",
                "wms_acknowledged": True,
                "physical_retry": False,
            }
            repeated = httpx.post(
                f"http://127.0.0.1:{business_port}/v1/wms/acknowledgements",
                json={"outcome": business_payload},
            )
            assert repeated.status_code == 200
            assert repeated.json()["acknowledgement_id"] == "wms:" + session["command_id"]
            conflict = httpx.post(
                f"http://127.0.0.1:{business_port}/v1/wms/acknowledgements",
                json={"outcome": {**business_payload, "verified_outcome": "FAILED"}},
            )
            assert conflict.status_code == 409
            assert workflow.runtime.world().step == 1
            assert all(step["source"]["excerpt"] for step in session["steps"])
            assert all(
                step["classification"] == "REAL PROTOCOL"
                for step in session["steps"]
                if step["stage"] in {10, 11, 12, 13, 14, 17}
            )
            if fault == "DUPLICATE_DELIVERY":
                assert workflow.lab.store.inbox(session["command_id"])["deliveries"] >= 2
            assert not errors
    finally:
        stopped.set()
        worker.join(15)
        assert not worker.is_alive()
        business_server.should_exit = True
        business_thread.join(10)
        assert not business_thread.is_alive()
