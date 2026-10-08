"""Client rebuild regressions against isolated real HTTP/persistence fixtures.

Failure injection tests explicitly intercept only the named read request. Mutating
journeys use the actual backend and verify the original command remains unchanged.
"""

import json
from pathlib import Path

import pytest
import test_guided_console as guided
from playwright.sync_api import expect

from robotops.cell.runtime import SyntheticRuntime

server = guided.server
browser_page = guided.browser_page

AXE = Path(__file__).parent / "node_modules/axe-core/axe.min.js"


def inspect_workspace(page):
    page.get_by_role("link", name="Inspect evidence", exact=True).click()
    expect(page.locator("#evidence-workspace")).to_be_visible()


def assert_accessible(page, directory, name):
    assert AXE.exists(), "Run npm ci --ignore-scripts from tests/browser first"
    page.add_script_tag(path=str(AXE))
    result = page.evaluate(
        """async () => await axe.run(document, {runOnly: {type: 'tag',
        values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']}})"""
    )
    (directory / f"axe-{name}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    assert not result["violations"], [
        (item["id"], [node["target"] for node in item["nodes"]]) for item in result["violations"]
    ]


@pytest.mark.parametrize("server", [SyntheticRuntime], indirect=True)
def test_real_completion_duplicate_guard_and_reduced_motion(server, browser_page):
    origin, registry = server
    page, directory, errors, console_errors, requests = browser_page
    page.emulate_media(reduced_motion="reduce")
    guided.start_guided(page, origin)
    before = sum(item["method"] == "POST" for item in requests)
    # Two immediate activations exercise the real client guard and backend response.
    with page.expect_response(lambda response: response.url.endswith("/authorize")):
        page.locator("#integration-advance").evaluate("el => {el.click(); el.click();}")
    page.wait_for_function("() => !busy && !integration.busy")
    assert sum(item["method"] == "POST" for item in requests) == before + 1
    final = guided.finish(page, origin)
    assert final["status"] == "COMPLETED" and final["context"]["wms_ack"] is True
    journal = registry.engine("original").runtime.recorded_journal(final["command_id"])
    assert journal.effect_count == 1
    expect(page.locator("#motion-play")).to_be_enabled()
    assert page.evaluate("player.reducedMotion && !player.playing")
    previous = page.locator("#motion-scrub").input_value()
    page.locator("#motion-step-forward").click()
    assert page.locator("#motion-scrub").input_value() != previous
    assert page.locator("#motion-phase").inner_text()
    assert_accessible(page, directory, "completed-run")
    assert not errors and not console_errors


@pytest.mark.parametrize("server", [SyntheticRuntime], indirect=True)
def test_saved_context_keyboard_source_and_browser_navigation(server, browser_page):
    origin, _ = server
    page, directory, errors, console_errors, requests = browser_page
    guided.start_guided(page, origin)
    saved = guided.until_stage(page, origin, 15)
    before = sum(item["method"] == "POST" for item in requests)
    inspect_workspace(page)
    row = page.locator('#integration-events button[data-stage="8"]')
    row.focus()
    row.press("Enter")
    expect(row).to_be_focused()
    expect(page.locator('#integration-events button[tabindex="0"]')).to_have_count(1)
    row.press("ArrowDown")
    expect(page.locator('#integration-events button[data-stage="9"]')).to_be_focused()
    page.keyboard.press("ArrowUp")
    expect(row).to_be_focused()
    tabs = page.locator("#integration-tabs")
    tabs.get_by_role("tab", name="Data", exact=True).focus()
    page.keyboard.press("ArrowRight")
    expect(tabs.get_by_role("tab", name="State", exact=True)).to_be_focused()
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowRight")
    expect(tabs.get_by_role("tab", name="Source", exact=True)).to_be_focused()
    expect(tabs.locator('[tabindex="0"]')).to_have_count(1)
    full_file = page.locator("#integration-source-full")
    # Hold the real read in the browser; verify focus survives its loading render.
    pending_reads = []
    page.route("**/steps/*/source", lambda route: pending_reads.append(route))
    full_file.focus()
    full_file.press("Enter")
    expect(full_file).to_have_attribute("aria-busy", "true")
    expect(full_file).to_be_focused()
    assert len(pending_reads) == 1
    pending_reads[0].continue_()
    page.unroute("**/steps/*/source")
    selector = page.locator("#integration-source-select")
    expect(selector).to_be_enabled()
    selector.focus()
    selector.select_option("validator")
    expect(page.locator("#integration-inspector .source-related-line").first).to_contain_text(
        "def validate("
    )
    expect(selector).to_be_focused()
    expect(page.locator("#integration-source button")).to_have_count(2)
    assert "session=" in page.url and "step=" in page.url and "#inspect" in page.url
    page.reload()
    page.wait_for_function("() => !robotWorkspace.restoring")
    expect(page.locator("#integration-inspector-title")).to_contain_text("Step 8")
    expect(tabs.get_by_role("tab", name="Source", exact=True)).to_have_attribute(
        "aria-selected", "true"
    )
    expect(selector).to_have_value("validator")
    expect(full_file).to_have_attribute("aria-pressed", "true")
    expect(page.locator("#integration-inspector .source-related-line").first).to_contain_text(
        "def validate("
    )
    page.get_by_role("link", name="Run & watch", exact=True).click()
    expect(page.locator("#run-workspace")).to_be_visible()
    page.go_back()
    expect(page.locator("#evidence-workspace")).to_be_visible()
    expect(page.locator("#integration-inspector-title")).to_contain_text("Step 8")
    opener = page.locator("#integration-investigate")
    opener.click()
    expect(page.locator("#investigation-dialog")).to_be_visible()
    assert_accessible(page, directory, "investigation-dialog")
    page.keyboard.press("Escape")
    expect(opener).to_be_focused()
    assert guided.session(page, origin)["revision"] == saved["revision"]
    assert before == sum(item["method"] == "POST" for item in requests)
    assert_accessible(page, directory, "source")
    assert not errors and not console_errors


@pytest.mark.parametrize("server", [SyntheticRuntime], indirect=True)
def test_responsive_empty_search_and_source_failure_recovery(server, browser_page):
    origin, _ = server
    page, directory, errors, console_errors, requests = browser_page
    guided.start_guided(page, origin)
    saved = guided.until_stage(page, origin, 6)
    before = sum(item["method"] == "POST" for item in requests)
    inspect_workspace(page)
    page.locator("#integration-search").fill("no-such-record-" * 20)
    expect(page.locator("#integration-trace-count")).to_contain_text("No matches")
    page.locator("#integration-reset-filters").click()
    expect(page.locator("#integration-events button").first).to_be_visible()
    page.locator("#integration-tabs").get_by_role("tab", name="Source", exact=True).click()
    # Mocked read failure only. The run and saved excerpt remain genuine backend data.
    page.route(
        "**/steps/*/source",
        lambda route: route.fulfill(status=503, json={"detail": "Source service unavailable"}),
    )
    page.locator("#integration-source-full").click()
    expect(page.locator("#integration-inspector")).to_contain_text("Full Python file unavailable")
    page.locator("#integration-source-excerpt").click()
    expect(page.locator("#integration-inspector")).to_have_text(
        saved["steps"][-1]["source"]["excerpt"]
    )
    page.unroute("**/steps/*/source")
    page.locator("#integration-source-full").click()
    expect(page.locator("#integration-inspector")).to_contain_text("class Engine:")
    for width, height in [(1440, 1000), (1280, 720), (390, 844), (320, 800)]:
        page.set_viewport_size({"width": width, "height": height})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(directory / f"source-{width}.png"), full_page=True)
    page.emulate_media(reduced_motion="reduce")
    page.add_style_tag(content="html {font-size: 200% !important}")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert guided.session(page, origin)["revision"] == saved["revision"]
    assert before == sum(item["method"] == "POST" for item in requests)
    assert_accessible(page, directory, "enlarged-source")
    # A 1280x720 desktop at 200% zoom has a 640x360 CSS viewport. Exercise
    # that reflow/device-pixel geometry explicitly; this is not an OS magnifier test.
    zoom_context = page.context.browser.new_context(
        viewport={"width": 640, "height": 360}, device_scale_factor=2
    )
    try:
        zoom_page = zoom_context.new_page()
        zoom_page.goto(page.url)
        zoom_page.wait_for_function("() => !robotWorkspace.restoring")
        assert zoom_page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        expect(zoom_page.locator("#integration-source-select")).to_be_enabled()
        zoom_page.screenshot(
            path=str(directory / "source-200-percent-zoom-reflow.png"), full_page=True
        )
        assert_accessible(zoom_page, directory, "zoom-reflow")
    finally:
        zoom_context.close()
    assert not errors
    # Chromium reports the deliberately injected 503 as a console network error.
    assert all("503" in item for item in console_errors)


@pytest.mark.parametrize("server", [SyntheticRuntime], indirect=True)
@pytest.mark.parametrize("reads_unavailable", [False, True], ids=["read-recovers", "offline"])
def test_empty_backend_validation_and_lost_response_recovery(
    server, browser_page, reads_unavailable
):
    origin, _ = server
    page, directory, errors, console_errors, requests = browser_page
    guided.open_ready(page, origin, {"width": 1280, "height": 720})
    page.locator("#new-test").click()
    expect(page.locator("#new-test-dialog")).to_be_visible()
    assert_accessible(page, directory, "new-test-dialog")
    page.keyboard.press("Escape")
    expect(page.locator("#new-test")).to_be_focused()
    page.locator(".manage-data > summary").click()
    page.locator("#delete-test").click()
    expect(page.locator("#delete-test-dialog")).to_be_visible()
    assert_accessible(page, directory, "delete-test-dialog")
    page.keyboard.press("Escape")
    expect(page.locator("#delete-test")).to_be_focused()
    inspect_workspace(page)
    expect(page.locator("#evidence-empty")).to_contain_text("No saved run yet")
    assert_accessible(page, directory, "empty-evidence")
    page.get_by_role("link", name="Run & watch", exact=True).click()
    page.locator("#scenario").select_option("BROKER_TRANSIENT")
    product = page.locator("#product").input_value()

    # Invalid values cannot be selected through the UI. Corrupt this request to
    # exercise an actual backend validation rejection, not a mocked response.
    def invalid_request(route):
        payload = route.request.post_data_json
        payload["fault"] = "UNKNOWN_SCENARIO"
        route.continue_(post_data=json.dumps(payload))

    page.route("**/v1/wms/tasks", invalid_request)
    with page.expect_response(lambda response: response.url.endswith("/v1/wms/tasks")) as rejected:
        page.locator("#create").click()
    assert rejected.value.status == 409
    assert rejected.value.json() == {"reason": "UNKNOWN_FAILURE_SCENARIO"}
    page.wait_for_function("() => !busy && !integration.busy")
    expect(page.locator("#message")).to_have_attribute("data-kind", "error")
    expect(page.locator("#scenario")).to_have_value("BROKER_TRANSIENT")
    expect(page.locator("#product")).to_have_value(product)
    assert guided.get(page, origin + "/integration/sessions") == []
    assert_accessible(page, directory, "validation-error")
    page.unroute("**/v1/wms/tasks")

    # The backend really creates the run; only its response is lost. Refreshing
    # authoritative state must recover that same run and prevent a second intake.
    created = []

    def lose_response(route):
        response = route.fetch()
        assert response.status == 202
        created.append(response.json())
        route.abort("failed")

    page.route("**/v1/wms/tasks", lose_response)
    if reads_unavailable:
        page.route("**/integration/sessions", lambda route: route.abort("failed"))
    page.locator("#create").click()
    page.wait_for_function("() => !busy && !integration.busy")
    assert len(created) == 1
    records = guided.get(page, origin + "/integration/sessions")
    assert len(records) == 1 and records[0]["session_id"] == created[0]["session_id"]
    expect(page.locator("#create")).to_be_disabled()
    if reads_unavailable:
        expect(page.locator("#message")).to_contain_text("Reload this page to check saved runs")
        expect(page.locator("#create")).to_contain_text("Request unconfirmed")
        assert_accessible(page, directory, "unconfirmed-request")
        page.unroute("**/integration/sessions")
    else:
        expect(page.locator("#integration-history")).to_have_value(created[0]["session_id"])
        expect(page.locator("#integration-advance")).to_be_enabled()
    assert created[0]["current_stage"] == 1
    page.reload()
    page.wait_for_function("() => !robotWorkspace.restoring")
    assert guided.session(page, origin)["session_id"] == created[0]["session_id"]
    assert sum(item["method"] == "POST" for item in requests) == 2
    assert not errors
    assert all("409" in item or "ERR_FAILED" in item for item in console_errors)


@pytest.mark.parametrize("server", [SyntheticRuntime], indirect=True)
def test_real_six_product_history_and_export(server, browser_page):
    origin, registry = server
    page, directory, errors, console_errors, requests = browser_page
    guided.open_ready(page, origin, {"width": 1440, "height": 1000})
    page.get_by_text("More about this scenario & test controls", exact=True).click()
    page.locator("#tool-showcase").click()
    page.wait_for_function("() => !busy && !integration.busy")
    for _ in range(150):
        saved = guided.session(page, origin)
        if saved["status"] == "COMPLETED":
            break
        guided.advance(page, origin)
    assert saved["status"] == "COMPLETED"
    commands = {step["command_id"] for step in saved["steps"] if step["stage"] == 16}
    assert len(commands) == 6
    assert all(
        registry.engine("original").runtime.recorded_journal(command).effect_count == 1
        for command in commands
    )
    before = sum(item["method"] == "POST" for item in requests)
    inspect_workspace(page)
    expect(page.locator("#integration-events button")).to_have_count(len(saved["steps"]))
    assert len(saved["steps"]) > 100
    first = page.locator("#integration-events button").first
    first.focus()
    first.press("End")
    expect(page.locator("#integration-events button").last).to_be_focused()
    with (
        page.expect_download() as download,
        page.expect_response(
            lambda response: response.url.endswith("/export")
        ) as exported_response,
    ):
        page.locator("#integration-export").click()
    destination = directory / "six-product-export.json"
    download.value.save_as(destination)
    exported = json.loads(destination.read_text(encoding="utf-8"))
    assert exported["session"]["session_id"] == saved["session_id"]
    assert exported == exported_response.value.json()
    # Export intentionally redacts authorization fields. Verify every durable
    # stage identity/outcome while comparing the downloaded file to the real API.
    fields = ("step_id", "stage", "sequence", "status", "command_id", "evidence_ids")
    assert [tuple(step[key] for key in fields) for step in exported["session"]["steps"]] == [
        tuple(step[key] for key in fields) for step in saved["steps"]
    ]
    assert before == sum(item["method"] == "POST" for item in requests)
    page.screenshot(path=str(directory / "six-product-trace.png"), full_page=True)
    assert not errors and not console_errors
