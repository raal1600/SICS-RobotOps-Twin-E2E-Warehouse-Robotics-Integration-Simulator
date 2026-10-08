"""Real UI checks for the evidence workbench, including mobile investigation."""

import json

import pytest
import test_guided_console as guided
from playwright.sync_api import expect

from robotops.cell.runtime import SyntheticRuntime

server = guided.server
browser_page = guided.browser_page


@pytest.mark.parametrize("server", [SyntheticRuntime], indirect=True)
def test_engineering_views_records_related_source_and_export_are_read_only(server, browser_page):
    origin, _ = server
    page, directory, errors, console_errors, requests = browser_page
    guided.start_guided(page, origin)
    saved = guided.until_stage(page, origin, 15)
    before = sum(r["method"] == "POST" for r in requests)
    page.get_by_role("link", name="Inspect evidence", exact=True).click()
    tabs = page.locator("#integration-tabs")
    expect(page.locator("#integration-follow")).to_have_text("Latest step selected")
    expect(page.locator("#integration-follow")).to_be_disabled()
    page.locator('#integration-events [data-stage="8"]').click()
    expect(page.locator("#integration-follow")).to_have_text("Follow latest step")
    expect(page.locator("#integration-follow")).to_be_enabled()
    tabs.get_by_role("tab", name="Records", exact=True).click()
    expect(page.locator("#integration-engineering-body")).to_contain_text("RobotCommand")
    expect(page.locator("#integration-engineering-body")).to_contain_text("Current row, read now")
    page.locator("#integration-engineering-search").fill("RobotCommand")
    expect(page.locator("#integration-engineering-body")).not_to_contain_text("WorldObservation")
    page.locator("#integration-engineering-search").fill("")
    tabs.get_by_role("tab", name="Source", exact=True).click()
    # Full-file mode always shows the selector, including when Records cached the catalog.
    expect(page.locator("#integration-source button")).to_have_count(2)
    expect(page.locator("#integration-source-browser")).to_be_hidden()
    page.locator("#integration-source-full").click()
    expect(page.locator("#integration-source-browser")).to_be_visible()
    expect(page.locator("#integration-source-select")).to_be_enabled()
    expect(page.locator("#integration-source-catalog-status")).to_contain_text("Choose one")
    page.locator("#integration-source-excerpt").click()
    expect(page.locator("#integration-source-browser")).to_be_hidden()
    page.locator("#integration-source-full").click()
    expect(page.locator("#integration-source-browser")).to_be_visible()
    page.locator("#integration-source-select").select_option("validator")
    expect(page.locator("#integration-inspector")).to_contain_text("class ActionValidator")
    expect(page.locator("#integration-source-identity")).to_contain_text(
        "robotops/brain/validation.py"
    )
    highlights = page.locator("#integration-inspector .source-related-line")
    expect(highlights.first).to_contain_text("def validate(")
    expect(page.locator("#integration-source-highlight-label")).to_contain_text(
        "ActionValidator.validate"
    )
    source = page.request.get(
        f"{origin}/integration/sessions/{saved['session_id']}/steps/{data_step_id(saved, 8)}/source?component=validator"
    ).json()
    expect(highlights).to_have_count(source["symbol_end_line"] - source["symbol_start_line"] + 1)
    assert page.locator("#integration-inspector").text_content() == source["content"]
    page.locator("#integration-inspector").evaluate("el => el.scrollTop = 0")
    page.locator("#integration-source-full").click()
    expect(highlights.first).to_contain_text("def validate(")
    assert page.locator("#integration-inspector").evaluate("el => el.scrollTop > 0")
    tabs.get_by_role("tab", name="Decisions", exact=True).click()
    expect(page.locator("#integration-engineering-body")).to_contain_text(
        "not an individual pass/fail"
    )
    tabs.get_by_role("tab", name="Run info", exact=True).click()
    expect(page.locator("#integration-engineering-body")).to_contain_text(
        "not a saved configuration snapshot"
    )
    with page.expect_download() as download:
        page.locator("#integration-engineering-export").click()
    data = json.loads(download.value.path().read_text(encoding="utf-8"))
    assert data["step_id"] == next(s["step_id"] for s in saved["steps"] if s["stage"] == 8)
    assert data["records"]["items"]
    tabs.get_by_role("tab", name="Protocol", exact=True).click()
    expect(page.locator("#integration-engineering-body")).to_contain_text("not a packet capture")
    for width in [1440, 390]:
        page.set_viewport_size({"width": width, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(directory / f"engineering-{width}.png"), full_page=True)
    assert guided.session(page, origin)["revision"] == saved["revision"]
    assert before == sum(r["method"] == "POST" for r in requests)
    # On a phone, follow returns inspection to the latest saved result without execution.
    page.locator("#integration-follow-mobile").click()
    expect(page.locator("#integration-inspector-title")).to_contain_text("Step 14")
    expect(page.locator("#integration-follow-mobile")).to_be_disabled()
    assert before == sum(r["method"] == "POST" for r in requests)
    assert not errors and not console_errors


def data_step_id(session, stage):
    return next(step["step_id"] for step in session["steps"] if step["stage"] == stage)


@pytest.mark.parametrize("server", [SyntheticRuntime], indirect=True)
def test_source_shows_readable_saved_python_and_current_full_file(server, browser_page):
    origin, _ = server
    page, directory, errors, console_errors, requests = browser_page
    guided.start_guided(page, origin)
    saved = guided.until_stage(page, origin, 6)
    page.get_by_role("link", name="Inspect evidence", exact=True).click()
    source = saved["steps"][-1]["source"]
    before = sum(r["method"] == "POST" for r in requests)
    page.locator("#integration-tabs").get_by_role("tab", name="Source", exact=True).click()
    expect(page.locator("#integration-inspector")).to_have_text(source["excerpt"])
    expect(page.locator("#integration-source-identity")).to_contain_text("Engine.stage_observe")
    page.locator("#integration-source-full").click()
    expect(page.locator("#integration-source-select")).to_be_visible()
    expect(page.locator("#integration-source-select")).to_be_enabled()
    expect(page.locator("#integration-inspector")).to_contain_text("class Engine:")
    expect(page.locator("#integration-source-note")).to_contain_text("not a snapshot")
    assert page.locator("#integration-inspector").inner_text().count("\n") > 100
    page.screenshot(path=str(directory / "python-source.png"), full_page=True)
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.locator("#integration-source-excerpt").click()
    expect(page.locator("#integration-inspector")).to_have_text(source["excerpt"])
    assert guided.session(page, origin)["revision"] == saved["revision"]
    assert before == sum(r["method"] == "POST" for r in requests)
    assert not errors and not console_errors


@pytest.mark.parametrize("server", [SyntheticRuntime], indirect=True)
def test_two_cursors_actions_filters_export_and_existing_investigation(server, browser_page):
    origin, registry = server
    page, directory, errors, console_errors, requests = browser_page
    guided.start_guided(page, origin)
    at_gate = guided.until_stage(page, origin, 15)
    page.get_by_role("link", name="Inspect evidence", exact=True).click()
    page.locator('#integration-events [data-stage="8"]').click()
    expect(page.locator("#integration-inspector-title")).to_contain_text("Step 8")
    expect(page.locator("#integration-position")).to_contain_text("Step 15")
    expect(page.locator("#integration-current-inspection")).to_contain_text("historical")
    expect(page.locator("#integration-pending-detail")).to_contain_text(
        "immediately requests execution"
    )
    before = sum(r["method"] == "POST" for r in requests)
    page.locator("#integration-search").fill("impossible-match")
    expect(page.locator("#integration-events li")).to_have_count(0)
    expect(page.locator("#integration-position")).to_contain_text("Step 15")
    page.locator("#integration-reset-filters").click()
    page.locator("#integration-investigate").click()
    expect(page.locator("#investigation-dialog")).to_be_visible()
    expect(page.locator("#review-identity")).to_contain_text(at_gate["command_id"])
    page.locator("#return-simulation").click()
    with page.expect_download() as download:
        page.locator("#integration-export").click()
    exported = json.loads(download.value.path().read_text(encoding="utf-8"))
    assert exported["session"]["revision"] == at_gate["revision"]
    assert "not embedded" in exported["scope"]
    assert before == sum(r["method"] == "POST" for r in requests)
    page.screenshot(path=str(directory / "historical-at-physical-gate.png"), full_page=True)
    result = guided.advance(page, origin)
    assert result["current_stage"] == 17
    expect(page.locator("#integration-inspector-title")).to_contain_text("Step 8")
    expect(page.locator("#integration-position")).to_contain_text("Step 17")
    page.locator("#integration-follow-mobile").click()
    expect(page.locator("#integration-inspector-title")).to_contain_text("Step 16")
    expect(page.locator("#integration-replay-evidence")).to_contain_text(
        "No recorded Blender motion"
    )
    expect(page.locator('[data-proof="verification"]')).to_have_attribute("data-state", "unproven")
    assert (
        registry.engine("original").runtime.recorded_journal(at_gate["command_id"]).effect_count
        == 1
    )
    assert not errors and not console_errors


@pytest.mark.parametrize("server", [SyntheticRuntime], indirect=True)
@pytest.mark.parametrize("width", [390, 1440])
def test_wms_recovery_has_verified_physical_evidence_and_business_only_action(
    server, browser_page, width
):
    origin, registry = server
    page, directory, errors, console_errors, requests = browser_page
    guided.start_guided(page, origin, "WMS_UNAVAILABLE")
    page.set_viewport_size({"width": width, "height": 900})
    guided.until_stage(page, origin, 20)
    failed = guided.advance(page, origin)
    assert failed["status"] == "RETRYABLE_FAILURE"
    expect(page.locator("#integration-pending-title")).to_have_text(
        "Business acknowledgement failed"
    )
    expect(page.locator('[data-proof="verification"]')).to_have_attribute(
        "data-state", "established"
    )
    expect(page.locator('[data-proof="wms"]')).to_have_attribute("data-state", "failed")
    expect(page.locator('[data-proof="erp"]')).to_have_attribute("data-state", "unproven")
    expect(page.locator("#integration-advance")).to_have_text("Retry WMS acknowledgement")
    expect(page.locator("#integration-pending-detail")).to_contain_text(
        "No robot command will be sent"
    )
    page.get_by_role("link", name="Inspect evidence", exact=True).click()
    page.locator("#integration-proof-panel > summary").click()
    page.locator('[data-proof="verification"]').click()
    expect(page.locator("#integration-overview")).to_contain_text("VERIFIED_SUCCESS")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if width == 390:
        page.locator("#integration-tabs").scroll_into_view_if_needed()
        # Status no longer overlays the inspector on narrow screens.
        assert (
            page.locator("#integration-cursor-strip").evaluate(
                "el => getComputedStyle(el).position"
            )
            == "static"
        )
        expect(page.locator("#integration-inspector-title")).to_contain_text("Step 19")
    page.screenshot(path=str(directory / f"wms-failed-{width}.png"), full_page=True)
    before = len(requests)
    updated = guided.advance(page, origin)
    assert updated["command_id"] == failed["command_id"]
    posts = [r for r in requests[before:] if r["method"] == "POST"]
    assert len(posts) == 1 and posts[0]["body"]["stage"] == 20
    final = guided.finish(page, origin)
    assert final["status"] == "COMPLETED"
    assert (
        registry.engine("original").runtime.recorded_journal(failed["command_id"]).effect_count == 1
    )
    assert not errors and not console_errors
