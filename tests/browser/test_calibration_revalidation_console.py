"""Real browser recovery tests for unchanged saved estimates and rejected rollback."""

import json

import test_calibration_console as calibration
from playwright.sync_api import expect
from test_client_rebuild import assert_accessible
from test_investigation import continue_guided, get

server = calibration.server
browser_page = calibration.browser_page


def reuse(page, artifact_id):
    page.locator("#calibration-reuse-artifact").select_option(artifact_id)
    page.locator("#calibration-reuse").focus()
    return calibration.auxiliary(page, "#calibration-reuse", "/reuse-estimate")


def test_saved_estimate_is_inactive_until_new_validation_and_moved_camera_reuse_fails(
    server, browser_page
):
    origin, registry = server
    page, artifacts, errors, console_errors, requests = browser_page
    prefix = calibration.new_measured_test(page, origin, 83)
    original = calibration.approve_camera(page)
    original_id = original["state"]["active_artifact_id"]
    calibration.apply_sensor_or_tool_fault(page, "depth_scale")
    calibration.apply_sensor_or_tool_fault(page, "restore_sensor")
    page.get_by_text("Revalidate a saved estimate", exact=True).click()
    before = get(page, prefix + "/calibration/records")
    candidate = reuse(page, original_id)
    assert candidate["state"]["workflow_state"] == "CANDIDATE"
    assert candidate["state"]["active_validity"] == "SUSPECT_INVALID"
    assert candidate["state"]["active_artifact_id"] == original_id
    after = get(page, prefix + "/calibration/records")
    assert [row for row in before if row["kind"] == "capture"] == [
        row for row in after if row["kind"] == "capture"
    ]
    expect(page.locator("#create")).to_be_disabled()
    expect(page.locator("#calibration-action")).to_have_text("Validate independently")
    page.reload()
    expect(page.locator("#calibration-action")).to_have_text("Validate independently")
    calibration.action(page, "Validate independently", "/validations")
    expect(page.locator("#create")).to_be_disabled()
    page.locator("#calibration-actor").fill("New simulated approval after independent recheck")
    renewed = calibration.action(page, "Approve for this simulation", "/approvals")
    assert renewed["state"]["active_artifact_id"] != original_id
    page.locator("#calibration-action").click()
    calibration.approve_camera(page)
    calibration.action(page, "Remove board and check tool", "/tool-check")
    with page.expect_response(lambda response: response.url.endswith("/v1/wms/tasks")) as started:
        page.locator("#calibration-action").click()
    assert started.value.ok
    completed = continue_guided(page, prefix, started.value.json()["session_id"])
    assert completed["status"] == "COMPLETED", completed
    page.locator("#calibration-camera").select_option("camera-west")
    page.locator("#calibration-checks > summary").click()
    page.get_by_text("Introduce a simulated camera fault", exact=True).click()
    calibration.auxiliary(page, "#calibration-move-camera", "/move-camera")
    page.get_by_text("Revalidate a saved estimate", exact=True).click()
    reuse(page, original_id)
    checked = calibration.action(page, "Validate independently", "/validations")
    report = get(page, prefix + "/calibration/records/validation/" + checked["record_ids"][0])
    assert not report["passed"] and report["reference_max_mm"] > 5
    expect(page.locator("#calibration-action")).to_have_text("Start new measurements")
    expect(page.locator("#create")).to_be_disabled()
    expect(page.locator("#calibration-state")).to_contain_text("SUSPECT_INVALID")
    page.locator("#calibration-inspect").click()
    page.locator("#calibration-record").select_option("validation/" + report["report_id"])
    expect(page.locator("#calibration-summary")).to_contain_text("REJECTED")
    expect(page.locator("#calibration-summary")).to_contain_text("Independent reference error")
    expect(page.locator("#calibration-summary")).not_to_contain_text(
        report["references"][0]["reference_id"]
    )
    page.get_by_text("Records and run info · full saved JSON", exact=True).click()
    expect(page.locator("#calibration-record-json")).to_contain_text(report["failures"][0])
    page.get_by_text("Records and run info · full saved JSON", exact=True).click()
    assert_accessible(page, artifacts, "rejected-saved-estimate")
    page.screenshot(path=str(artifacts / "rejected-saved-estimate.png"), full_page=True)
    (artifacts / "revalidation-result.json").write_text(
        json.dumps(
            {"original": original, "renewed": renewed, "rejected": report, "pick": completed},
            indent=2,
        ),
        encoding="utf-8",
    )
    assert not errors and not console_errors
