"""Actual process outage/restart, same-request recovery and historical mutation denial.

No endpoint response is mocked. The test owns and stops only its local API process.
"""

import json
import os
import socket
import subprocess
import sys
import time

import httpx
import pytest
import test_calibration_console as calibration
from playwright.sync_api import expect
from test_client_rebuild import assert_accessible
from test_investigation import get

browser_page = calibration.browser_page


class LocalAPI:
    def __init__(self, directory):
        self.directory = directory
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            self.port = listener.getsockname()[1]
        self.origin = f"http://127.0.0.1:{self.port}"
        self.process = None
        self.log = None
        self.pids = []

    def start(self):
        self.log = (self.directory / f"process-{len(self.pids)}.log").open("wb")
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "apps.api",
                "--runtime",
                "headless",
                "--data-dir",
                str(self.directory / "worlds"),
                "--port",
                str(self.port),
            ],
            stdin=subprocess.DEVNULL,
            stdout=self.log,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        self.pids.append(self.process.pid)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            assert self.process.poll() is None, "Local API exited; inspect process log"
            try:
                if httpx.get(self.origin + "/health", timeout=0.5).status_code == 200:
                    return
            except httpx.TransportError:
                pass
            time.sleep(0.05)
        raise AssertionError("Local API did not become healthy")

    def stop(self):
        if self.process is None:
            return
        # Windows venv launchers can have a child interpreter. Target only this
        # test-owned PID tree; never kill Python processes by name or by port.
        if self.process.poll() is None:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(self.process.pid), "/T", "/F"],
                    check=True,
                    capture_output=True,
                )
            else:
                self.process.terminate()
            self.process.wait(timeout=15)
        self.log.close()
        self.process = None


@pytest.fixture
def process_server(tmp_path):
    api = LocalAPI(tmp_path)
    try:
        api.start()
        yield api
    finally:
        api.stop()


def test_real_outage_same_capture_retry_process_restart_and_readonly_history(
    process_server,
    browser_page,
):
    api = process_server
    page, artifacts, errors, console_errors, requests = browser_page
    prefix = calibration.new_measured_test(page, api.origin, 97)
    test_id = page.locator("#test-history").input_value()
    configured = calibration.action(page, "Configure camera", "/configure")
    api.stop()
    # The API is genuinely unavailable; this request cannot have committed.
    page.locator("#calibration-action").click()
    expect(page.locator("#calibration-error")).to_contain_text("Check the saved request")
    expect(page.locator("#calibration-action")).to_be_disabled()
    pending = page.evaluate("calibration.pending")
    assert pending["body"]["expected_revision"] == configured["state"]["revision"]
    page.screenshot(path=str(artifacts / "offline-pending.png"), full_page=True)
    api.start()
    page.reload()
    expect(page.locator("#calibration-check")).to_have_text("Check saved request")
    assert page.evaluate("calibration.pending") == pending
    assert get(page, prefix + "/calibration")["states"][0] == configured["state"]
    page.locator("#calibration-check").click()
    expect(page.locator("#calibration-check")).to_have_text("Retry the saved request")
    assert_accessible(page, artifacts, "retry-saved-request")
    with page.expect_response(
        lambda response: (
            response.request.method == "POST" and response.url.endswith("/acquisitions")
        ),
        timeout=180_000,
    ) as response:
        page.locator("#calibration-check").evaluate(
            "element => {element.click(); element.click();}"
        )
    assert response.value.ok, response.value.text()
    captured = response.value.json()
    page.wait_for_function("() => !calibration.busy && !busy")
    assert page.evaluate("calibration.pending") is None
    accepted_requests = [
        item
        for item in requests
        if item["method"] == "POST" and item["url"].endswith("/acquisitions")
    ]
    assert len(accepted_requests) == 2  # Offline attempt and one explicit retry.
    assert accepted_requests[0]["body"] == accepted_requests[1]["body"] == pending["body"]
    records = get(page, prefix + "/calibration/records")
    captures = [item for item in records if item["kind"] == "capture"]
    assert len(captures) == 18
    repeated = page.request.post(
        prefix + pending["route"], data=pending["body"], headers={"X-Test-Revision": "1"}
    )
    assert repeated.ok and repeated.json() == captured
    assert [
        item for item in get(page, prefix + "/calibration/records") if item["kind"] == "capture"
    ] == captures
    candidate = calibration.action(page, "Estimate calibration", "/candidates")
    validated = calibration.action(page, "Validate independently", "/validations")
    assert validated["state"]["active_artifact_id"] is None
    candidate_id = candidate["state"]["candidate_id"]
    page.locator("#calibration-inspect").click()
    page.locator("#calibration-record").select_option("candidate/" + candidate_id)
    api.stop()
    api.start()
    page.reload()
    expect(page.locator("#calibration-record")).to_have_value("candidate/" + candidate_id)
    assert get(page, prefix + "/calibration")["states"][0] == validated["state"]
    page.get_by_role("link", name="Run & watch", exact=True).click()
    expect(page.locator("#calibration-action")).to_have_text("Approve for this simulation")
    assert page.locator("#create").is_disabled()
    page.locator("#calibration-actor").fill("Simulated restart acceptance operator")
    approved = calibration.action(page, "Approve for this simulation", "/approvals")
    artifact_id = approved["state"]["active_artifact_id"]
    original = get(page, prefix + "/calibration/records/artifact/" + artifact_id)
    api.stop()
    api.start()
    page.reload()
    expect(page.locator("#calibration-action")).to_have_text("Calibrate the other camera")
    assert get(page, prefix + "/calibration/records/artifact/" + artifact_id) == original
    assert get(page, prefix + "/calibration")["states"][0] == approved["state"]
    # A new isolated world makes this original world historical and read-only.
    calibration.new_measured_test(page, api.origin, 37)
    page.locator("#test-history").select_option(test_id)
    expect(page.locator("#calibration-state")).to_contain_text("Saved, read-only")
    expect(page.locator("#calibration-action")).to_be_disabled()
    rejected = page.request.post(
        prefix + "/calibration/cameras/camera-west/invalidation",
        data={
            "request_id": "denied-historical-change",
            "expected_revision": approved["state"]["revision"],
            "reason": "MUST_NOT_APPLY",
        },
        headers={"X-Test-Revision": "1"},
    )
    assert rejected.status == 409 and "READ_ONLY" in rejected.json()["reason"]
    assert get(page, prefix + "/calibration/records/artifact/" + artifact_id) == original
    assert get(page, prefix + "/calibration")["states"][0] == approved["state"]
    page.locator("#calibration-inspect").click()
    page.locator("#calibration-record").select_option("artifact/" + artifact_id)
    expect(page.locator("#calibration-summary")).to_contain_text(
        "Simulated restart acceptance operator"
    )
    assert_accessible(page, artifacts, "historical-approval")
    page.screenshot(path=str(artifacts / "historical-approval.png"), full_page=True)
    assert len(set(api.pids)) == 4
    assert not errors
    assert all(
        any(code in message for code in ("ERR_CONNECTION_REFUSED", "404", "409"))
        for message in console_errors
    ), console_errors
    (artifacts / "restart-evidence.json").write_text(
        json.dumps(
            {
                "process_ids": api.pids,
                "request": pending,
                "capture_count": len(captures),
                "candidate": candidate,
                "validation": validated,
                "approval": approved,
                "denied_mutation": rejected.json(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
