"""Real missed transfer: reported motion, fresh images, original evidence and no automatic re-pick."""

import json

import test_calibration_console as calibration
from playwright.sync_api import expect
from test_client_rebuild import assert_accessible
from test_investigation import continue_guided, get

server = calibration.server
browser_page = calibration.browser_page


def test_missed_transfer_has_recorded_motion_and_unknown_cause_without_recalibration(
    server, browser_page
):
    origin, registry = server
    page, artifacts, errors, console_errors, requests = browser_page
    prefix = calibration.new_measured_test(page, origin, 37)
    west = calibration.approve_camera(page)
    page.locator("#calibration-action").click()
    east = calibration.approve_camera(page)
    calibration.action(page, "Remove board and check tool", "/tool-check")
    page.locator("#setup-panel").evaluate("element => {element.open=true;}")
    page.locator("#scenario").select_option("MISSED_PICK")
    expect(page.locator("#scenario-brief")).to_contain_text("object is not retained")
    with page.expect_response(lambda response: response.url.endswith("/v1/wms/tasks")) as started:
        page.locator("#calibration-action").click()
    assert started.value.ok
    session = continue_guided(page, prefix, started.value.json()["session_id"])
    assert session["status"] == "COMPLETED", session  # Journey complete, physical pick failed.
    evidence = get(page, prefix + "/jobs/" + session["job_id"] + "/evidence")
    assert evidence["job"]["state"] == "FAILED"
    assert evidence["journal"]["effect_count"] == 0
    assert evidence["journal"]["reason"] == "GRASP_NOT_ESTABLISHED"
    playback = get(page, prefix + "/jobs/" + session["job_id"] + "/playback")
    assert playback["recording"]["complete"]
    assert len(playback["recording"]["frames"]) == 121
    assert all(frame["attached_product_id"] is None for frame in playback["recording"]["frames"])
    page.locator("#calibration-camera").select_option("camera-west")
    page.locator("#calibration-inspect").click()
    records = get(page, prefix + "/calibration/records")
    outcome = next(row for row in records if row["kind"] == "pick-outcome")
    page.locator("#calibration-record").select_option("pick-outcome/" + outcome["id"])
    expect(page.locator("#calibration-summary")).to_contain_text("VERIFIED_FAILURE")
    expect(page.locator("#calibration-summary")).to_contain_text("0 product transfers")
    investigated = calibration.investigate_selected(
        page, prefix, "MISSED_TRANSFER_CAUSE_UNRESOLVED"
    )
    assert investigated["state"]["active_artifact_id"] == west["state"]["active_artifact_id"]
    assert investigated["state"]["active_validity"] == "VERIFIED"
    expect(page.locator("#calibration-summary")).to_contain_text("No automatic second pick")
    assert_accessible(page, artifacts, "missed-pick-investigation")
    page.screenshot(path=str(artifacts / "missed-pick-unknown-cause.png"), full_page=True)
    page.reload()
    expect(page.locator("#calibration-record")).to_have_value(
        "investigation/" + investigated["record_ids"][0]
    )
    expect(page.locator("#calibration-summary")).to_contain_text("MISSED_TRANSFER_CAUSE_UNRESOLVED")
    current = get(page, prefix + "/calibration")
    assert {item["active_artifact_id"] for item in current["states"]} == {
        west["state"]["active_artifact_id"],
        east["state"]["active_artifact_id"],
    }
    assert (
        len(
            [
                item
                for item in requests
                if item["method"] == "POST" and item["url"].endswith("/v1/wms/tasks")
            ]
        )
        == 1
    )
    (artifacts / "missed-pick-evidence.json").write_text(
        json.dumps({"session": session, "evidence": evidence, "playback": playback}, indent=2),
        encoding="utf-8",
    )
    assert not errors and not console_errors
