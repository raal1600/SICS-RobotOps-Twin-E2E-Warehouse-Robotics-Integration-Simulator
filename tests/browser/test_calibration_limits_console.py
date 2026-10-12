"""A real missing tolerance cannot be replaced by a UI default or historic approval."""

import test_calibration_console as calibration
from playwright.sync_api import expect
from test_client_rebuild import assert_accessible
from test_investigation import get

server = calibration.server
browser_page = calibration.browser_page


def test_missing_limit_is_visible_and_restoration_requires_new_approval(server, browser_page):
    origin, registry = server
    page, artifacts, errors, console_errors, requests = browser_page
    prefix = calibration.new_measured_test(page, origin, 37)
    approved = calibration.approve_camera(page)
    original_id = approved["state"]["active_artifact_id"]
    removed = calibration.apply_sensor_or_tool_fault(page, "missing_reference_limit")
    assert removed["state"]["limits"]["max_reference_error_mm"] is None
    expect(page.locator("#calibration-action")).to_have_text("Restore documented limits")
    expect(page.locator("#calibration-next")).to_contain_text("tolerance is missing")
    expect(page.locator("#create")).to_be_disabled()
    page.reload()
    expect(page.locator("#calibration-action")).to_have_text("Restore documented limits")
    page.locator("#calibration-inspect").click()
    page.locator("#calibration-record").select_option(
        "simulation-fault/" + removed["record_ids"][0]
    )
    expect(page.locator("#calibration-summary")).to_contain_text(
        "Remove required reference tolerance"
    )
    expect(page.locator("#calibration-summary")).to_contain_text("not a diagnosis")
    page.locator("#calibration-source > summary").click()
    expect(page.locator("#calibration-source-content")).to_contain_text("def fault_notice")
    assert_accessible(page, artifacts, "missing-limits-evidence")
    page.screenshot(path=str(artifacts / "missing-limit-evidence.png"), full_page=True)
    page.get_by_role("link", name="Run & watch", exact=True).click()
    restored = calibration.action(page, "Restore documented limits", "/faults")
    assert restored["state"]["limits"]["max_reference_error_mm"] == 5
    assert restored["state"]["active_validity"] == "SUSPECT_INVALID"
    assert restored["state"]["active_artifact_id"] == original_id
    page.locator("#calibration-checks").evaluate("element => {element.open=true;}")
    page.get_by_text("Revalidate a saved estimate", exact=True).click()
    page.locator("#calibration-reuse-artifact").select_option(original_id)
    calibration.auxiliary(page, "#calibration-reuse", "/reuse-estimate")
    calibration.action(page, "Validate independently", "/validations")
    expect(page.locator("#create")).to_be_disabled()
    page.locator("#calibration-actor").fill("New simulated limits approval")
    renewed = calibration.action(page, "Approve for this simulation", "/approvals")
    assert renewed["state"]["active_artifact_id"] != original_id
    current = get(page, prefix + "/calibration")
    assert current["states"][0]["limits"]["max_reference_error_mm"] == 5
    assert not errors and not console_errors
