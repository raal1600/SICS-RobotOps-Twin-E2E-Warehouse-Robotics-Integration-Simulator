import json
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import httpx
import pytest

from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings


@contextmanager
def desktop_child(data: Path, session: Path):
    session.mkdir()
    with (session / "process.log").open("w") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "apps.desktop.backend",
                "--runtime",
                "headless",
                "--data-dir",
                str(data),
                "--session-dir",
                str(session),
                "--session-id",
                session.name,
            ],
            stdout=log,
            stderr=log,
        )
        try:
            deadline = time.monotonic() + 15
            while not (session / "ready.json").exists():
                assert process.poll() is None, (session / "process.log").read_text()
                assert time.monotonic() < deadline, "Desktop backend did not become ready"
                time.sleep(0.05)
            ready = json.loads((session / "ready.json").read_text())
            assert ready["session_id"] == session.name
            assert ready["origin"].startswith("http://127.0.0.1:")
            with httpx.Client(base_url=ready["origin"], trust_env=False, timeout=10) as client:
                assert client.get("/health").json()["status"] == "ok"
                yield client, process
        finally:
            (session / "stop").touch()
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
                raise
        assert process.returncode == 0, (session / "process.log").read_text()
        assert (session / "stopped.json").is_file()
        with socket.socket() as probe:
            probe.settimeout(1)
            port = int(ready["origin"].rsplit(":", 1)[1])
            assert probe.connect_ex(("127.0.0.1", port)) != 0, (
                "Owned port still accepts connections"
            )


@pytest.mark.parametrize("legacy", [False, True])
def test_desktop_close_reopen_preserves_uncertain_job_without_duplicate_pick(tmp_path, legacy):
    if legacy:
        SyntheticRuntime(tmp_path / "data" / "runtime.db", Settings())
    with desktop_child(tmp_path / "data", tmp_path / "first") as (client, _):
        fixture = client.get("/fixtures").json()
        assert len(fixture["products"]) == (3 if legacy else 6)
        assert fixture["robot_profile_version"] == (None if legacy else "hkm_inspired_v1")
        product = fixture["products"][0]["product_id"]
        payload = {
            "order_id": "desktop-order",
            "lines": [
                {
                    "order_line_id": "line",
                    "product_id": product,
                    "source_id": fixture["product_sources"][product],
                    "destination_id": fixture["destination_id"],
                }
            ],
        }
        response = client.post("/orders", json=payload, headers={"Idempotency-Key": "desktop"})
        assert response.status_code == 201
        job_id = response.json()["job_ids"][0]
        job = client.post(f"/jobs/{job_id}/run", json={"fault": "DROP_ACK_AFTER_EFFECT"}).json()
        assert job["state"] == "UNKNOWN_OUTCOME"
        command_id = job["command_id"]
    with desktop_child(tmp_path / "data", tmp_path / "second") as (client, _):
        reopened_fixture = client.get("/fixtures").json()
        assert reopened_fixture["products"] == fixture["products"]
        assert reopened_fixture["product_sources"] == fixture["product_sources"]
        assert reopened_fixture["scene_epoch"] == fixture["scene_epoch"]
        job = client.get(f"/jobs/{job_id}").json()
        assert job["state"] == "COMPLETED"
        assert job["command_id"] == command_id
        timeline = client.get("/orders/desktop-order/timeline").json()
        assert sum(event["event_type"] == "PICK_EFFECT" for event in timeline) == 1
        assert (
            sum(
                event["event_type"] == "COMMAND_DISPATCHED" and event["component"] == "gateway"
                for event in timeline
            )
            == 1
        )


def test_desktop_instances_use_distinct_owned_ports_and_independent_stop_files(tmp_path):
    with desktop_child(tmp_path / "data-a", tmp_path / "a") as (first, _):
        with desktop_child(tmp_path / "data-b", tmp_path / "b") as (second, _):
            assert first.base_url != second.base_url
        assert first.get("/health").status_code == 200
