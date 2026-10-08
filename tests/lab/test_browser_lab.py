"""Real Chromium over separate API/edge/PLC/WMS processes and real PG/RabbitMQ."""

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright

from tools.lab_stack import LabStack

pytestmark = pytest.mark.lab_integration


def read_journal(stack, command_id):
    uri = (stack.directory / "runtime.db").as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as db:
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


def assert_waiting_without_playback(page):
    page.wait_for_function("() => player.executionGated === true")
    for identity in (
        "motion-play",
        "motion-replay",
        "motion-scrub",
        "motion-speed",
        "motion-step-back",
        "motion-step-forward",
    ):
        expect(page.locator(f"#{identity}")).to_be_disabled()
    before = page.evaluate(
        """() => ({playing: player.playing, recording: player.recording,
          motions: player.track.filter(step => step.kind === 'motion').length,
          pose: player.pose()})"""
    )
    assert before["playing"] is False
    assert before["recording"] is None and before["motions"] == 0
    after = page.evaluate(
        """async () => {
          await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
          return {playing: player.playing, pose: player.pose()};
        }"""
    )
    assert after["playing"] is False and after["pose"] == before["pose"]


def prove_blender_playback(page, command_id, evidence):
    page.wait_for_function(
        """() => player.recording?.complete && player.recording.frames.length > 1
          && player.track.some(step => step.kind === 'motion')""",
        timeout=30_000,
    )
    recording = page.evaluate(
        """() => {
          const rec = player.recording, robot = 'Robot/ToolFlange';
          const product = rec.objects.find(object => object.product_id === player.data.product_id);
          const motions = player.track.filter(step => step.kind === 'motion');
          const position = frame => frame.transforms[robot].position;
          const moving = rec.frames.findIndex((frame, i) => i < rec.frames.length - 1
            && position(frame).some((value, axis) =>
              Math.abs(value - position(rec.frames[i + 1])[axis]) > 1e-5));
          return {source: rec.source, complete: rec.complete, command_id: rec.command_id,
            frames: rec.frames.length, total_frames: rec.total_frames, motion_steps: motions.length,
            robot_poses: new Set(rec.frames.map(frame => JSON.stringify(position(frame)))).size,
            product_name: product.name,
            product_start: rec.frames[0].transforms[product.name].position,
            product_finish: rec.frames.at(-1).transforms[product.name].position,
            moving_cursor: player.track.findIndex(step => step.kind === 'motion'
              && step.frame === moving)};
        }"""
    )
    assert recording["source"] == "BLENDER_EVALUATED_SCENE"
    assert recording["complete"] is True and recording["command_id"] == command_id
    assert recording["frames"] == recording["total_frames"] == recording["motion_steps"]
    assert recording["frames"] > 1 and recording["robot_poses"] > 1
    assert recording["product_start"] != recording["product_finish"]
    assert recording["moving_cursor"] >= 0
    assert page.evaluate("() => player.executionGated") is False
    page.locator("#motion-scrub").fill(str(recording["moving_cursor"]))
    before = page.evaluate(
        """() => ({cursor: player.cursor, pose: player.pose().transforms['Robot/ToolFlange'],
          rendered: player.view.meshes.get('Robot/ToolFlange').position.toArray()})"""
    )
    expect(page.locator("#motion-play")).to_have_text("Play")
    page.locator("#motion-play").click()
    page.wait_for_function(
        """before => player.playing && player.cursor > before.cursor
          && JSON.stringify(player.pose().transforms['Robot/ToolFlange']) !== JSON.stringify(before.pose)
          && JSON.stringify(player.view.meshes.get('Robot/ToolFlange').position.toArray())
            !== JSON.stringify(before.rendered)""",
        arg=before,
        timeout=30_000,
    )
    after = page.evaluate(
        """() => ({cursor: player.cursor, playing: player.playing,
          pose: player.pose().transforms['Robot/ToolFlange'],
          rendered: player.view.meshes.get('Robot/ToolFlange').position.toArray()})"""
    )
    page.locator("#motion-play").click()
    expect(page.locator("#motion-play")).to_have_text("Play")
    (evidence / "blender-motion.json").write_text(
        json.dumps({"recording": recording, "before": before, "after": after}, indent=2),
        encoding="utf-8",
    )
    page.screenshot(path=str(evidence / "blender-motion.png"), full_page=True)
    page.get_by_role("link", name="Inspect evidence", exact=True).click()


@pytest.mark.parametrize(
    "scenario",
    [
        pytest.param("", marks=pytest.mark.blender),
        "DROP_ACK_AFTER_EFFECT",
        "DUPLICATE_DELIVERY",
        "WMS_UNAVAILABLE",
    ],
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
        *Path("robotops/blender").glob("*.py"),
        *Path("blender/scripts").glob("*.py"),
        *Path("apps/api").glob("*.py"),
        *Path("apps/erp_ui").glob("*.js"),
        Path("tools/lab_stack.py"),
        Path(__file__),
    ]
    hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
    (evidence / "source-hashes.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    runtime = "synthetic" if scenario else "blender"
    stack = LabStack(lab_config, tmp_path / "process-stack", runtime=runtime).start()
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
                health = page.request.get(f"{stack.origin}/health")
                assert health.ok and health.json()["runtime"] == runtime
                expect(page.locator("#create")).to_be_enabled(timeout=30_000)
                expect(page.locator("#execution-profile")).to_contain_text("Integration lab")
                expect(page.locator("#execution-profile")).to_contain_text("real AMQP / OPC UA")
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
                    if current["current_stage"] <= 15:
                        assert_waiting_without_playback(page)
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
                        assert_waiting_without_playback(page)
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
                        if runtime == "blender":
                            prove_blender_playback(page, executed["command_id"], evidence)
                        live = page.request.get(
                            f"{stack.origin}/integration/sessions/{executed['session_id']}/live"
                        ).json()
                        assert live["read_only"] is True
                        assert any(event["value"] == "EXECUTING" for event in live["events"])
                        expect(page.locator("#integration-protocol-live")).to_contain_text("OPC UA")
                        expect(page.locator("#integration-protocol-live")).to_contain_text(
                            executed["command_id"]
                        )
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
                        expect(page.locator("#integration-pending-title")).to_have_text(
                            "Robot outcome not yet proven"
                        )
                        expect(page.locator("#integration-pending-detail")).to_contain_text(
                            "Do not retry the pick"
                        )
                        expect(page.locator("#integration-command")).to_contain_text(
                            current["command_id"]
                        )
                        expect(page.locator('[data-proof="verification"]')).to_have_attribute(
                            "data-state", "unproven"
                        )
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
                            expect(page.locator("#integration-pending-title")).to_have_text(
                                "Business acknowledgement failed"
                            )
                            expect(page.locator("#integration-advance")).to_have_text(
                                "Retry WMS acknowledgement"
                            )
                            expect(page.locator('[data-proof="verification"]')).to_have_attribute(
                                "data-state", "established"
                            )
                            expect(page.locator('[data-proof="wms"]')).to_have_attribute(
                                "data-state", "failed"
                            )
                            assert (
                                current["steps"][-1]["output"]["http_response"]["status_code"]
                                == 503
                            )
                            page.screenshot(path=str(evidence / "wms-failed.png"), full_page=True)
                    advance(page, stack.origin)
                final = state(page, stack.origin)
                assert final["status"] == "COMPLETED", final
                expected_scenario = {
                    "": "Happy path (no injected scenario)",
                    "DROP_ACK_AFTER_EFFECT": "Lose acknowledgement after effect",
                    "DUPLICATE_DELIVERY": "Duplicate command delivery",
                    "WMS_UNAVAILABLE": "WMS unavailable after verified pick",
                }[scenario]
                expect(page.locator("#motion-scenario")).to_contain_text(expected_scenario)
                page.get_by_role("link", name="Run & watch", exact=True).click()
                page.locator("#scenario").select_option("BRAIN_TIMEOUT")
                expect(page.locator("#motion-scenario")).to_contain_text(expected_scenario)
                saved_playback = page.request.get(
                    f"{stack.origin}/jobs/{final['job_id']}/playback"
                ).json()
                assert saved_playback["execution_scenario"]["fault"] == (scenario or None)
                assert saved_playback["execution_scenario"]["session_id"] == final["session_id"]
                assert reloaded and physical_request
                assert unknown_seen == (scenario == "DROP_ACK_AFTER_EFFECT")
                assert business_retry_seen == (scenario == "WMS_UNAVAILABLE")
                if scenario == "DUPLICATE_DELIVERY":
                    delivery = next(
                        step["output"] for step in final["steps"] if step["stage"] == 11
                    )
                    duplicate = delivery.get("redelivery", delivery)
                    assert duplicate["deliveries"] == 2
                    attempt = page.locator(
                        '#integration-events [data-stage="11"] .integration-attempt'
                    )
                    expect(attempt).to_contain_text("Deliveries 2 · original command identity")
                    assert ("broker redelivery" in attempt.inner_text()) == (
                        duplicate.get("redelivered") is True
                    )
                assert final["context"]["wms_ack"] is True
                assert all(
                    proof["state"] == "established" for proof in final["workbench"]["proofs"]
                )
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
                # Close pages/sockets gracefully before the browser's force-close.
                try:
                    context.close()
                finally:
                    browser.close()
    finally:
        stack.stop()
        for path in stack.directory.glob("*.log"):
            content = path.read_text(encoding="utf-8", errors="replace")
            assert "demo-only" not in content and "guest:guest" not in content
            (evidence / path.name).write_text(content, encoding="utf-8")
