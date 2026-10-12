"""A board-ID fault is acquired image evidence, with measured recovery through the client."""

import json

import test_calibration_console as calibration
from playwright.sync_api import expect
from test_client_rebuild import assert_accessible
from test_investigation import get

server = calibration.server
browser_page = calibration.browser_page


def test_wrong_printed_board_ids_remain_inspectable_after_restoration_and_new_approval(
    server, browser_page
):
    origin, registry = server
    page, artifacts, errors, console_errors, requests = browser_page
    prefix = calibration.new_measured_test(page, origin, 83)
    calibration.action(page, "Configure camera", "/configure")
    calibration.apply_sensor_or_tool_fault(page, "board_marker_ids")
    calibration.action(page, "Start new measurements", "/begin-measurements")
    captured = calibration.action(page, "Acquire board images", "/acquisitions")
    expect(page.locator("#calibration-action")).to_have_text("Improve measurements")
    expect(page.locator("#create")).to_be_disabled()
    capture_id = captured["record_ids"][0]
    saved = get(page, prefix + "/calibration/records/capture/" + capture_id)
    rejection = get(page, prefix + "/calibration/records/rejection/" + capture_id)
    assert rejection["reason"] == "MARKER_IDS_DO_NOT_MATCH_BOARD"
    page.locator("#calibration-inspect").click()
    page.locator("#calibration-record").select_option("rejection/" + capture_id)
    expect(page.locator("#calibration-summary")).to_contain_text("Unexpected detected marker IDs")
    page.locator("#calibration-source > summary").click()
    expect(page.locator("#calibration-source-content")).to_contain_text(
        "MARKER_IDS_DO_NOT_MATCH_BOARD"
    )
    assert (
        page.evaluate("calibration.savedTrace.source.loaded_function_verification")
        == "MATCHED_PYTHON_CODE"
    )
    assert_accessible(page, artifacts, "wrong-printed-ids")
    page.get_by_role("link", name="Run & watch", exact=True).click()
    page.locator("#calibration-capture").select_option(capture_id)
    with page.expect_response(lambda response: "/calibration/geometry?" in response.url) as shown:
        page.locator("#calibration-geometry-mode").select_option("capture")
    assert shown.value.ok
    marker_names = [
        obj["name"]
        for obj in shown.value.json()["scene"]["objects"]
        if obj["name"].startswith("Board/marker-")
    ]
    assert {int(name.split("-")[1]) for name in marker_names} == set(range(17, 34))
    page.screenshot(path=str(artifacts / "wrong-print-capture.png"), full_page=True)
    page.locator("#calibration-geometry-mode").select_option("cell")
    calibration.apply_sensor_or_tool_fault(page, "restore_board_print")
    assert get(page, prefix + "/calibration/records/capture/" + capture_id) == saved
    calibration.action(page, "Start new measurements", "/begin-measurements")
    calibration.action(page, "Acquire board images", "/acquisitions")
    calibration.action(page, "Estimate calibration", "/candidates")
    validated = calibration.action(page, "Validate independently", "/validations")
    assert validated["state"]["active_validity"] == "SUSPECT_INVALID"
    page.locator("#calibration-actor").fill("Simulated approval after restoring board print")
    approved = calibration.action(page, "Approve for this simulation", "/approvals")
    assert approved["state"]["active_validity"] == "VERIFIED"
    (artifacts / "printed-id-result.json").write_text(
        json.dumps({"capture": saved, "rejection": rejection, "approval": approved}, indent=2),
        encoding="utf-8",
    )
    assert not errors and not console_errors
