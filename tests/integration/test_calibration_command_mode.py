"""Controller reference is configured once per new measured cell and survives restart."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api.app import create_workspace_app


@pytest.mark.parametrize("mode", ["tcp", "flange"])
def test_new_cell_command_reference_is_persisted_scoped_and_idempotent(tmp_path, mode):
    app = create_workspace_app(tmp_path)
    with TestClient(app) as client:
        body = {
            "request_id": str(uuid4()),
            "cell_profile_id": "synthetic_calibration_gantry_v1",
            "seed": 37,
            "command_mode": mode,
        }
        response = client.post("/simulation-tests", json=body)
        assert response.status_code == 201, response.text
        identity = response.json()["test_id"]
        original = app.state.test_registry.engine(identity).runtime.world()
        assert original.calibration_machine.command_mode == mode
        assert client.post("/simulation-tests", json=body).json() == response.json()
        assert (
            client.post(
                "/simulation-tests",
                json={**body, "command_mode": "tcp" if mode == "flange" else "flange"},
            ).status_code
            == 409
        )
        assert app.state.test_registry.engine(identity).runtime.world() == original
        for bad in ("base", "TCP", ""):
            assert (
                client.post(
                    "/simulation-tests",
                    json={**body, "request_id": str(uuid4()), "command_mode": bad},
                ).status_code
                == 422
            )
        rejected = client.post(
            "/simulation-tests",
            json={
                "request_id": str(uuid4()),
                "cell_profile_id": "hkm_inspired_v1",
                "command_mode": mode,
            },
        )
        assert (
            rejected.status_code == 409
            and rejected.json()["reason"] == "COMMAND_MODE_REQUIRES_MEASURED_PROFILE"
        )
    restarted = create_workspace_app(tmp_path)
    with TestClient(restarted) as client:
        engine = restarted.state.test_registry.engine(identity)
        assert engine.runtime.world() == original
        assert engine.settings.calibration_command_mode == mode
        assert client.post("/simulation-tests", json=body).status_code == 201
        cleared = client.post(
            f"/simulation-tests/{identity}/clear",
            json={"request_id": str(uuid4()), "expected_revision": 1},
        )
        assert cleared.status_code == 200, cleared.text
        fresh = restarted.state.test_registry.engine(identity)
        assert fresh.runtime.world().calibration_machine.command_mode == mode
        assert fresh.settings.calibration_command_mode == mode
