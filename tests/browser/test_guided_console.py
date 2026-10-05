"""Browser journeys drive real REST gates, durable records and recorded 3D motion."""

import json

import pytest
import test_investigation as journeys
from playwright.sync_api import expect
from test_investigation import get, open_ready

from robotops.blender.adapter import BlenderRuntime
from robotops.cell.runtime import SyntheticRuntime

server = journeys.server
browser_page = journeys.browser_page


def session(page, origin):
    identity = page.locator("#integration-history").input_value()
    assert identity
    return get(page, f"{origin}/integration/sessions/{identity}")


def start_guided(page, origin, fault=""):
    open_ready(page, origin, {"width": 1440, "height": 1100})
    page.locator("#scenario").select_option(fault)
    with page.expect_response(lambda response: response.url.endswith("/v1/wms/tasks")) as response:
        page.locator("#create").click()
    assert response.value.status == 202, response.value.text()
    expect(page.locator("#integration-console")).to_be_visible()
    state = session(page, origin)
    assert state["current_stage"] == 1
    assert get(page, f"{origin}/orders") == []
    return state


def advance(page, origin):
    state = session(page, origin)
    button = page.locator("#integration-advance")
    expect(button).to_be_enabled()
    with page.expect_response(
        lambda response: response.request.method == "POST" and response.url.endswith("/authorize"),
        timeout=180_000,
    ) as response:
        button.click()
    assert response.value.ok, response.value.text()
    if state["current_stage"] == 15:
        expect(page.locator("#integration-pending-title")).to_have_text(
            "Controller result", timeout=180_000
        )
    else:
        expect(page.locator("#integration-state")).not_to_have_text(
            f"{state['status']} · revision {state['revision']}"
        )
    expect(page.locator("#integration-error")).to_be_empty()
    return session(page, origin)


def until_stage(page, origin, target):
    for _ in range(30):
        state = session(page, origin)
        if state["current_stage"] >= target:
            return state
        advance(page, origin)
    pytest.fail(f"Guided session did not reach stage {target}: {state}")


def finish(page, origin):
    for _ in range(30):
        state = session(page, origin)
        if state["status"] == "COMPLETED":
            return state
        advance(page, origin)
    pytest.fail(f"Guided session did not complete: {state}")


@pytest.mark.parametrize(
    "server",
    [SyntheticRuntime, pytest.param(BlenderRuntime, marks=pytest.mark.blender)],
    indirect=True,
    ids=["synthetic", "blender"],
)
def test_guided_happy_reload_gate_trace_and_business_completion(server, browser_page):
    origin, registry = server
    page, directory, errors, console_errors, requests = browser_page
    initial = start_guided(page, origin)
    before_reload = until_stage(page, origin, 10)
    workflow = registry.engine("original")
    command = before_reload["command_id"]
    assert workflow.runtime.recorded_journal(command) is None
    page.reload()
    expect(page.locator("#integration-console")).to_be_visible()
    resumed = session(page, origin)
    assert resumed["session_id"] == initial["session_id"]
    assert resumed["revision"] == before_reload["revision"]
    gate = until_stage(page, origin, 15)
    expect(page.locator("#integration-advance")).to_have_text("AUTHORIZE ROBOT EXECUTION")
    assert workflow.runtime.recorded_journal(command) is None
    page.screenshot(path=str(directory / "physical-gate.png"), full_page=True)
    after_execution = advance(page, origin)
    assert after_execution["current_stage"] == 17
    assert workflow.runtime.recorded_journal(command).effect_count == 1
    expect(page.locator("#integration-live")).to_be_visible()
    expect(page.locator("#motion-play")).to_be_enabled()
    final = finish(page, origin)
    assert final["status"] == "COMPLETED"
    assert {step["stage"] for step in final["steps"]} == set(range(1, 23))
    assert final["context"]["wms_ack"] is True
    assert workflow.runtime.recorded_journal(command).effect_count == 1
    page.get_by_role("tab", name="Code", exact=True).click()
    expect(page.locator("#integration-inspector")).to_contain_text("robotops/integration/engine.py")
    assert not errors
    assert not console_errors
    assert not any(item["method"] == "POST" and item["url"].endswith("/run") for item in requests)
    (directory / "session.json").write_text(json.dumps(final, indent=2), encoding="utf-8")
    assert gate["context"].get("physical_authorized") is not True


@pytest.mark.parametrize(
    "server",
    [SyntheticRuntime, pytest.param(BlenderRuntime, marks=pytest.mark.blender)],
    indirect=True,
    ids=["synthetic", "blender"],
)
def test_guided_lost_ack_reconciles_original_command_without_second_effect(server, browser_page):
    origin, registry = server
    page, directory, errors, console_errors, _ = browser_page
    start_guided(page, origin, "DROP_ACK_AFTER_EFFECT")
    until_stage(page, origin, 19)
    unknown = advance(page, origin)
    assert unknown["status"] == "UNKNOWN_OUTCOME"
    command = unknown["command_id"]
    runtime = registry.engine("original").runtime
    assert runtime.recorded_journal(command).effect_count == 1
    expect(page.locator("#integration-reconcile")).to_be_visible()
    expect(page.locator("#integration-advance")).to_be_disabled()
    expect(page.locator("#integration-pending-title")).to_contain_text("Outcome unproven")
    expect(page.locator("#integration-pending-detail")).to_contain_text(
        "original command journal and fresh observation"
    )
    expect(page.locator("#integration-pending-detail")).to_contain_text("does not issue a new pick")
    expect(page.locator("#integration-advance")).to_have_text("Awaiting reconciliation")
    expect(page.locator("#integration-history option:checked")).to_contain_text("UNKNOWN_OUTCOME")
    page.screenshot(path=str(directory / "unknown-outcome.png"), full_page=True)
    with page.expect_response(lambda response: response.url.endswith("/reconcile")) as response:
        page.locator("#integration-reconcile").click()
    assert response.value.ok, response.value.text()
    expect(page.locator("#integration-pending-title")).to_have_text("WMS reconciliation")
    final = finish(page, origin)
    assert final["command_id"] == command
    assert runtime.recorded_journal(command).effect_count == 1
    evidence = get(page, f"{origin}/jobs/{final['job_id']}/evidence")
    assert evidence["reconciliations"]
    assert all(item["command"]["command_id"] == command for item in evidence["reconciliations"])
    assert not errors
    assert not console_errors
    (directory / "reconciled-session.json").write_text(
        json.dumps(final, indent=2), encoding="utf-8"
    )
