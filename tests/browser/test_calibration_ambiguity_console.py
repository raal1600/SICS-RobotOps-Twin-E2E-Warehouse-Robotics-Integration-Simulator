"""Actual ambiguous RGB reaches the client without selecting a convenient board pose."""

import json

import test_calibration_console as calibration
from playwright.sync_api import expect
from test_client_rebuild import assert_accessible
from test_investigation import get

server = calibration.server
browser_page = calibration.browser_page


def test_ambiguous_planar_images_show_competing_python_poses_and_allow_new_measurements(
    server, browser_page
):
    origin, registry = server
    page, artifacts, errors, console_errors, requests = browser_page
    prefix = calibration.new_measured_test(page, origin, 173)
    calibration.action(page, "Configure camera", "/configure")
    page.locator("#calibration-measurement-options").evaluate("element => {element.open=true;}")
    page.locator("#calibration-capture-scenario").select_option("near_frontal")
    calibration.action(page, "Acquire board images", "/acquisitions")
    expect(page.locator("#calibration-action")).to_have_text("Improve measurements")
    overview = get(page, prefix + "/calibration")
    report_id = overview["next_steps"]["camera-west"]["measurement_report_id"]
    report = get(page, prefix + "/calibration/records/acquisition-report/" + report_id)
    rejection = next(
        item
        for item in report["rejections"]
        if item["reason"] == "UNRESOLVED_PLANAR_POSE_AMBIGUITY"
    )
    choices = rejection["calculation"]["outputs"]["positive_depth_candidates"]
    assert len(choices) == 2 and choices[0]["t_c_t"] != choices[1]["t_c_t"]
    assert not report["ready_to_fit"]
    page.locator("#calibration-capture").select_option(rejection["capture_id"])
    page.wait_for_function(
        "document.getElementById('calibration-rgb').complete && document.getElementById('calibration-rgb').naturalWidth===960"
    )
    page.screenshot(path=str(artifacts / "ambiguous-real-rgb.png"), full_page=True)
    page.locator("#calibration-inspect").click()
    page.locator("#calibration-record").select_option("rejection/" + rejection["capture_id"])
    expect(page.locator("#calibration-summary")).to_contain_text("UNRESOLVED_PLANAR_POSE_AMBIGUITY")
    page.locator("#calibration-calculations > summary").click()
    expect(page.locator("#calibration-calculation")).to_contain_text("positive_depth_candidates")
    expect(page.locator("#calibration-calculation")).to_contain_text("no pose selected")
    assert_accessible(page, artifacts, "ambiguous-pose-evidence")
    page.screenshot(path=str(artifacts / "competing-poses-calculation.png"), full_page=True)
    page.get_by_role("link", name="Run & watch", exact=True).click()
    calibration.action(page, "Improve measurements", "/begin-measurements")
    page.locator("#calibration-capture-scenario").select_option("varied")
    calibration.action(page, "Acquire board images", "/acquisitions")
    candidate = calibration.action(page, "Estimate calibration", "/candidates")
    assert candidate["state"]["active_artifact_id"] is None
    (artifacts / "ambiguity-and-recovery.json").write_text(
        json.dumps({"rejection": rejection, "new_candidate": candidate}, indent=2), encoding="utf-8"
    )
    assert not errors and not console_errors
