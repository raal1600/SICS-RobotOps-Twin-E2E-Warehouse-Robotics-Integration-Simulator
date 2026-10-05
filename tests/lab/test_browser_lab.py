"""Real Chromium over separate API/edge/PLC/WMS processes and real PG/RabbitMQ."""

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright

from tools.lab_stack import LabStack

pytestmark = pytest.mark.lab_integration


def read_journal(stack, command_id):
    uri = (stack.directory / "runtime.db").as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as db:
        row = db.execute(
            "SELECT receipt FROM controller_journal WHERE id=?", (command_id,)
        ).fetchone()
        world = json.loads(db.execute("SELECT body FROM runtime_world WHERE id=1").fetchone()[0])
    return (json.loads(row[0]) if row else None), world["step"]


def state(page, origin):
    identity = page.locator("#integration-history").input_value()
    response = page.request.get(f"{origin}/integration/sessions/{identity}")
    assert response.ok, response.text()
    return response.json()


def advance(page, origin):
    current = state(page, origin)
    expect(page.locator("#integration-advance")).to_be_enabled(timeout=30_000)
    with page.expect_response(
        lambda response: response.request.method == "POST" and response.url.endswith("/authorize"),
        timeout=180_000,
    ) as response:
        page.locator("#integration-advance").click()
    assert response.value.ok, response.value.text()
    page.wait_for_function("() => !integration.busy", timeout=180_000)
    expect(page.locator("#integration-error")).to_be_empty()
    updated = state(page, origin)
    assert updated["revision"] > current["revision"]
    return updated


@pytest.mark.parametrize(
    "scenario", ["", "DROP_ACK_AFTER_EFFECT", "DUPLICATE_DELIVERY", "WMS_UNAVAILABLE"]
)
def test_full_lab_browser_authorization_recovery_and_business_completion(
    lab_config, tmp_path, scenario
):
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
    evidence = Path("artifacts/lab-browser") / stamp / (scenario or "happy")
    evidence.mkdir(parents=True)
    sources = [
        *Path("robotops/lab").glob("*.py"),
        *Path("robotops/integration").glob("*.py"),
        *Path("apps/api").glob("*.py"),
        *Path("apps/erp_ui").glob("*.js"),
        Path("tools/lab_stack.py"),
        Path(__file__),
    ]
    hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
    (evidence / "source-hashes.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    stack = LabStack(lab_config, tmp_path / "process-stack").start()
    (evidence / "stack.json").write_text(json.dumps(stack.report(), indent=2), encoding="utf-8")
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True, args=["--enable-unsafe-swiftshader"]
            )
            context = browser.new_context(viewport={"width": 1440, "height": 1100})
            context.tracing.start(screenshots=True, snapshots=True, sources=False)
            page = context.new_page()
            page.set_default_timeout(30_000)
            errors, console_errors, requests = [], [], []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on(
                "console",
                lambda message: (
                    console_errors.append(message.text) if message.type == "error" else None
                ),
            )
            page.on(
                "request",
                lambda request: requests.append(
                    {
                        "method": request.method,
                        "url": request.url,
                        "body": request.post_data_json if request.method == "POST" else None,
                    }
                ),
            )
            try:
                page.goto(stack.origin)
                expect(page.locator("#create")).to_be_enabled(timeout=30_000)
                expect(page.locator("#motion-state")).to_have_text("3D cell ready", timeout=30_000)
                expect(page.locator("#new-test")).to_be_hidden()
                page.locator("#scenario").select_option(scenario)
                with page.expect_response(
                    lambda response: response.url.endswith("/v1/wms/tasks")
                ) as created:
                    page.locator("#create").click()
                assert created.value.status == 202
                expect(page.locator("#integration-console")).to_be_visible(timeout=30_000)
                current = state(page, stack.origin)
                assert current["current_stage"] == 1
                reloaded = unknown_seen = business_retry_seen = False
                physical_request = None
                for _ in range(35):
                    current = state(page, stack.origin)
                    if current["status"] == "COMPLETED":
                        break
                    if current["command_id"] and current["current_stage"] <= 15:
                        receipt, effects = read_journal(stack, current["command_id"])
                        assert receipt is None and effects == 0
                    if current["current_stage"] == 10 and not reloaded:
                        page.reload()
                        expect(page.locator("#integration-console")).to_be_visible(timeout=30_000)
                        resumed = state(page, stack.origin)
                        assert resumed["session_id"] == current["session_id"]
                        assert resumed["revision"] == current["revision"]
                        expect(page.locator("#integration-stream")).to_contain_text(
                            "read-only WebSocket"
                        )
                        reloaded = True
                    if current["current_stage"] == 15:
                        expect(page.locator("#integration-advance")).to_have_text(
                            "AUTHORIZE ROBOT EXECUTION"
                        )
                        page.screenshot(path=str(evidence / "physical-gate.png"), full_page=True)
                        executed = advance(page, stack.origin)
                        assert executed["current_stage"] == 17
                        receipt, effects = read_journal(stack, executed["command_id"])
                        assert receipt["effect_count"] == effects == 1
                        expect(page.locator("#integration-live")).to_be_visible()
                        expect(page.locator("#motion-play")).to_be_enabled()
                        live = page.request.get(
                            f"{stack.origin}/integration/sessions/{executed['session_id']}/live"
                        ).json()
                        assert live["read_only"] is True
                        assert any(event["value"] == "EXECUTING" for event in live["events"])
                        expect(page.locator("#integration-protocol-live")).to_contain_text("OPC UA")
                        physical_request = next(
                            item
                            for item in reversed(requests)
                            if item["body"] and item["body"].get("stage") == 16
                        )
                        replay = page.request.post(
                            physical_request["url"], data=physical_request["body"]
                        )
                        assert replay.ok
                        assert replay.json()["revision"] == executed["revision"]
                        assert read_journal(stack, executed["command_id"])[1] == 1
                        continue
                    if current["status"] == "UNKNOWN_OUTCOME":
                        unknown_seen = True
                        expect(page.locator("#integration-reconcile")).to_be_visible()
                        expect(page.locator("#integration-advance")).to_be_disabled()
                        page.screenshot(path=str(evidence / "unknown-outcome.png"), full_page=True)
                        with page.expect_response(
                            lambda response: response.url.endswith("/reconcile")
                        ) as reconciled:
                            page.locator("#integration-reconcile").click()
                        assert reconciled.value.ok
                        page.wait_for_function("() => !integration.busy")
                        assert read_journal(stack, current["command_id"])[1] == 1
                        continue
                    if current["status"] == "RETRYABLE_FAILURE":
                        if current["current_stage"] == 5:
                            assert current["steps"][-1]["summary"] == "STALE_OR_FUTURE_OBSERVATION"
                            assert read_journal(stack, current["command_id"])[1] == 0
                        else:
                            assert current["current_stage"] == 20
                            assert read_journal(stack, current["command_id"])[1] == 1
                            business_retry_seen = True
                    advance(page, stack.origin)
                final = state(page, stack.origin)
                assert final["status"] == "COMPLETED", final
                assert reloaded and physical_request
                assert unknown_seen == (scenario == "DROP_ACK_AFTER_EFFECT")
                assert business_retry_seen == (scenario == "WMS_UNAVAILABLE")
                assert final["context"]["wms_ack"] is True
                opc = next(step["output"] for step in final["steps"] if step["stage"] == 12)
                assert opc["opcua_client_component"] == "edge-adapter"
                assert opc["edge_process_id"] == stack.service_process_ids["edge"]
                assert opc["edge_process_id"] != stack.service_process_ids["api"]
                assert read_journal(stack, final["command_id"])[0]["effect_count"] == 1
                assert read_journal(stack, final["command_id"])[1] == 1
                assert all(
                    step["classification"] == "REAL PROTOCOL"
                    for step in final["steps"]
                    if step["stage"] in {10, 11, 12, 13, 14, 17, 20}
                )
                assert not any(
                    item["method"] == "POST" and item["url"].endswith("/run") for item in requests
                )
                encoded = json.dumps(final, indent=2)
                for secret in ["demo-only", "local-demo-only", "guest:guest", "postgresql://"]:
                    assert secret not in encoded
                assert not errors and not console_errors
                (evidence / "session.json").write_text(encoded, encoding="utf-8")
                page.screenshot(path=str(evidence / "completed.png"), full_page=True)
            finally:
                if page.locator("#integration-history").input_value():
                    (evidence / "last-session.json").write_text(
                        json.dumps(state(page, stack.origin), indent=2), encoding="utf-8"
                    )
                page.screenshot(path=str(evidence / "last-state.png"), full_page=True)
                (evidence / "browser.json").write_text(
                    json.dumps(
                        {"errors": errors, "console_errors": console_errors, "requests": requests},
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                context.tracing.stop(path=str(evidence / "trace.zip"))
                browser.close()
    finally:
        stack.stop()
        for path in stack.directory.glob("*.log"):
            content = path.read_text(encoding="utf-8", errors="replace")
            assert "demo-only" not in content and "guest:guest" not in content
            (evidence / path.name).write_text(content, encoding="utf-8")
