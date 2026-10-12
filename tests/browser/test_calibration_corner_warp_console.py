"""Inspect real corner exclusions caused by a synthetic RGB readout fault."""

import json

import test_calibration_console as calibration
from playwright.sync_api import expect
from test_client_rebuild import assert_accessible
from test_investigation import get

server = calibration.server
browser_page = calibration.browser_page


def test_rgb_readout_fault_shows_excluded_corner_pixels_and_recovers_with_new_images(
    server, browser_page
):
    origin, registry = server
    page, artifacts, errors, console_errors, requests = browser_page
    prefix = calibration.new_measured_test(page, origin, 113)
    calibration.action(page, "Configure camera", "/configure")
    calibration.apply_sensor_or_tool_fault(page, "rgb_corner_warp")
    calibration.action(page, "Start new measurements", "/begin-measurements")
    calibration.action(page, "Acquire board images", "/acquisitions")
    records = get(page, prefix + "/calibration/records")
    samples = [
        get(page, prefix + "/calibration/records/sample/" + row["id"])
        for row in records
        if row["kind"] == "sample"
    ]
    sample = next(item for item in samples if item["excluded_corner_ids"])
    assert len(sample["excluded_image_points_px"]) == len(sample["excluded_corner_ids"])
    page.locator("#calibration-capture").select_option(sample["capture_id"])
    expect(page.locator("#calibration-capture-note")).to_contain_text("crosses marked X")
    expect(page.locator("#calibration-depth-display")).to_contain_text("raw sensor units")
    display = get(page, prefix + "/calibration/captures/" + sample["capture_id"] + "/depth-display")
    assert display["low_raw"] > 0 and display["high_raw"] > display["low_raw"]
    assert display["valid_pixels"] + display["invalid_pixels"] == 640 * 480
    page.wait_for_function(
        "document.getElementById('calibration-rgb').complete && document.getElementById('calibration-rgb').naturalWidth===960"
    )
    page.screenshot(path=str(artifacts / "excluded-corner-overlay.png"), full_page=True)
    page.locator("#calibration-inspect").click()
    page.locator("#calibration-record").select_option("sample/" + sample["capture_id"])
    expect(page.locator("#calibration-summary")).to_contain_text("Excluded corners")
    page.locator("#calibration-calculations > summary").click()
    expect(page.locator("#calibration-calculation")).to_contain_text("excluded_image_points_px")
    assert_accessible(page, artifacts, "excluded-corner-evidence")
    page.get_by_role("link", name="Run & watch", exact=True).click()
    calibration.apply_sensor_or_tool_fault(page, "restore_sensor")
    expect(page.locator("#create")).to_be_disabled()
    calibration.action(page, "Start new measurements", "/begin-measurements")
    calibration.action(page, "Acquire board images", "/acquisitions")
    calibration.action(page, "Estimate calibration", "/candidates")
    calibration.action(page, "Validate independently", "/validations")
    page.locator("#calibration-actor").fill("Simulated RGB readout recovery approval")
    approved = calibration.action(page, "Approve for this simulation", "/approvals")
    assert approved["state"]["active_validity"] == "VERIFIED"
    assert get(page, prefix + "/calibration/records/sample/" + sample["capture_id"]) == sample
    (artifacts / "corner-outlier-result.json").write_text(
        json.dumps({"sample": sample, "approval": approved}, indent=2), encoding="utf-8"
    )
    assert not errors and not console_errors
