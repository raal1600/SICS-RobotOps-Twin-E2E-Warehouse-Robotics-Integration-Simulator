"""Measured calibration browser acceptance: real images, API, approval and robot effect."""

import json
from zipfile import ZipFile

import numpy as np
import pytest
import test_investigation as journeys
from playwright.sync_api import expect
from test_client_rebuild import assert_accessible
from test_investigation import continue_guided, get

server = journeys.server
browser_page = journeys.browser_page


def new_measured_test(page, origin, seed=37, command_mode="flange"):
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.goto(origin)
    expect(page.locator("#new-test")).to_be_enabled()
    page.locator("#new-test").click()
    page.locator("#cell-profile").select_option("synthetic_calibration_gantry_v1")
    page.locator("#calibration-seed").fill(str(seed))
    page.locator("#calibration-command-mode").select_option(command_mode)
    page.locator("#create-test").click()
    expect(page.locator("#new-test-dialog")).not_to_be_visible()
    expect(page.locator("#calibration-action")).to_have_text("Configure camera")
    return origin + "/simulation-tests/" + page.locator("#test-history").input_value()


def action(page, label, endpoint):
    button = page.locator("#calibration-action")
    expect(button).to_have_text(label)
    expect(button).to_be_enabled()
    with page.expect_response(
        lambda response: response.request.method == "POST" and response.url.endswith(endpoint),
        timeout=180_000,
    ) as response:
        button.click()
    assert response.value.ok, response.value.text()
    page.wait_for_function("() => !calibration.busy && !busy", timeout=180_000)
    expect(page.locator("#calibration-error")).to_be_empty()
    return response.value.json()


def approve_camera(page):
    action(page, "Configure camera", "/configure")
    action(page, "Acquire board images", "/acquisitions")
    expect(page.locator("#calibration-rgb")).to_be_visible()
    page.wait_for_function(
        "() => {const image=document.getElementById('calibration-rgb'); return image.complete && image.naturalWidth === 960;}"
    )
    candidate = action(page, "Estimate calibration", "/candidates")
    assert candidate["state"]["active_artifact_id"] is None
    validated = action(page, "Validate independently", "/validations")
    assert validated["state"]["active_artifact_id"] is None
    page.locator("#calibration-actor").fill("Simulated browser acceptance operator")
    return action(page, "Approve for this simulation", "/approvals")


def auxiliary(page, button, endpoint):
    with page.expect_response(
        lambda response: response.request.method == "POST" and response.url.endswith(endpoint),
        timeout=180_000,
    ) as response:
        page.locator(button).click()
    assert response.value.ok, response.value.text()
    page.wait_for_function("() => !calibration.busy && !busy", timeout=180_000)
    return response.value.json()


def apply_sensor_or_tool_fault(page, kind):
    page.locator("#calibration-checks").evaluate("element => {element.open=true;}")
    page.locator("#calibration-faults").evaluate("element => {element.open=true;}")
    page.locator("#calibration-fault-kind").select_option(kind)
    return auxiliary(page, "#calibration-fault-apply", "/faults")


def investigate_selected(page, prefix, expected_clue):
    button = page.locator("#calibration-investigate")
    expect(button).to_be_enabled()
    button.focus()
    with page.expect_response(lambda response: response.url.endswith("/investigate")) as response:
        button.press("Enter")
    assert response.value.ok, response.value.text()
    receipt = response.value.json()
    page.wait_for_function("() => !calibration.busy && !busy")
    expect(page.locator("#calibration-record")).to_have_value(
        "investigation/" + receipt["record_ids"][0]
    )
    expect(page.locator("#calibration-summary")).to_contain_text(expected_clue)
    expect(page.locator("#calibration-summary")).to_contain_text(
        "INSUFFICIENT_EVIDENCE / UNKNOWN_CAUSE"
    )
    expect(page.locator("#calibration-operation-status")).to_be_focused()
    saved = get(page, prefix + "/calibration/records/investigation/" + receipt["record_ids"][0])
    assert expected_clue in {item["code"] for item in saved["clues"]}
    return receipt


def test_capture_quality_failures_are_explained_and_recover_with_new_images(server, browser_page):
    origin, registry = server
    page, artifacts, errors, console_errors, requests = browser_page
    prefix = new_measured_test(page, origin, 83)
    action(page, "Configure camera", "/configure")
    for scenario in ("repeated", "single_axis", "timestamp_skew", "unsettled"):
        page.locator("#calibration-measurement-options").evaluate("element => {element.open=true;}")
        page.locator("#calibration-capture-scenario").select_option(scenario)
        captured = action(page, "Acquire board images", "/acquisitions")
        expect(page.locator("#calibration-action")).to_have_text("Improve measurements")
        expect(page.locator("#motion-outcome")).to_have_text("Calibration check required")
        overview = get(page, prefix + "/calibration")
        report_id = overview["next_steps"]["camera-west"]["measurement_report_id"]
        report = get(page, prefix + "/calibration/records/acquisition-report/" + report_id)
        assert not report["ready_to_fit"] and report["capture_count"] == 18
        assert captured["state"]["active_artifact_id"] is None
        rejected = page.request.post(
            prefix + "/calibration/cameras/camera-west/candidates",
            data={
                "dataset_id": report["dataset_id"],
                "candidate_id": "no-candidate-" + scenario,
                "request_id": "denied-fit-" + scenario,
                "expected_revision": captured["state"]["revision"],
            },
        )
        assert rejected.status == 409 and "INSUFFICIENT_MEASUREMENT" in rejected.json()["reason"]
        page.locator("#calibration-inspect").click()
        page.locator("#calibration-record").select_option("acquisition-report/" + report_id)
        expect(page.locator("#calibration-summary")).to_contain_text(
            "More informative measurements required"
        )
        if scenario in {"repeated", "single_axis"}:
            expect(page.locator("#calibration-summary")).to_contain_text(
                "INSUFFICIENT_ROTATION_DIVERSITY"
            )
        else:
            expect(page.locator("#calibration-summary")).to_contain_text("0 accepted of 18")
        assert_accessible(page, artifacts, "capture-" + scenario)
        page.screenshot(path=str(artifacts / ("capture-" + scenario + ".png")), full_page=True)
        page.get_by_role("link", name="Run & watch", exact=True).click()
        action(page, "Improve measurements", "/begin-measurements")
    page.locator("#calibration-capture-scenario").focus()
    page.locator("#calibration-capture-scenario").press("Home")
    expect(page.locator("#calibration-capture-scenario")).to_have_value("varied")
    action(page, "Acquire board images", "/acquisitions")
    candidate = action(page, "Estimate calibration", "/candidates")
    assert candidate["state"]["active_artifact_id"] is None
    records = get(page, prefix + "/calibration/records")
    sample_id = next(item["id"] for item in reversed(records) if item["kind"] == "sample")
    page.locator("#calibration-inspect").click()
    page.locator("#calibration-source > summary").click()
    page.locator("#calibration-record").select_option("capture/" + sample_id)
    expect(page.locator("#calibration-source-content")).to_contain_text("calibration_captures")
    assert (
        page.evaluate("calibration.savedTrace.source.loaded_function_verification")
        == "MATCHED_PYTHON_CODE"
    )
    page.locator("#calibration-record").select_option("sample/" + sample_id)
    expect(page.locator("#calibration-source-content")).to_contain_text("CharucoDetector")
    assert (
        page.evaluate("calibration.savedTrace.source.loaded_function_verification")
        == "MATCHED_PYTHON_CODE"
    )
    # Selection drives saved geometry, never a new acquisition or current-scene replacement.
    page.get_by_role("link", name="Run & watch", exact=True).click()
    page.locator("#calibration-capture").select_option(sample_id)
    cell = get(page, prefix + "/cell")
    geometry_evidence = []
    for mode in ("capture", "poses", "record"):
        with page.expect_response(
            lambda response: "/calibration/geometry?" in response.url
        ) as shown:
            page.locator("#calibration-geometry-mode").select_option(mode)
        assert shown.value.ok, shown.value.text()
        geometry = shown.value.json()
        geometry_evidence.append(geometry)
        expect(page.locator("#calibration-geometry-status")).to_contain_text(geometry["title"])
        expect(page.locator("#motion-outcome")).to_have_text("Read-only evidence")
        expect(page.locator("#motion-play")).to_be_disabled()
        assert page.evaluate("player.evidence.numbers !== undefined")
        assert_accessible(page, artifacts, "geometry-" + mode)
        page.screenshot(path=str(artifacts / ("geometry-" + mode + ".png")), full_page=True)
    assert get(page, prefix + "/cell") == cell
    (artifacts / "geometry-evidence.json").write_text(
        json.dumps(geometry_evidence, indent=2), encoding="utf-8"
    )
    page.locator("#calibration-geometry-mode").select_option("cell")
    expect(page.locator("#motion-outcome")).to_have_text("Calibration check required")
    assert not errors and all("409" in message for message in console_errors)


def test_wrong_camera_models_are_inspectable_and_cannot_create_calibration_candidates(
    server, browser_page
):
    origin, registry = server
    page, artifacts, errors, console_errors, requests = browser_page
    prefix = new_measured_test(page, origin, 83)
    initial = action(page, "Configure camera", "/configure")
    camera = "camera-west"
    first_report = get(
        page,
        f"{prefix}/calibration/records/camera-model-report/{initial['state']['camera_model_report_id']}",
    )
    assert first_report["passed"] and len(first_report["streams"]) == 2
    for kind in ("model_focal", "model_profile", "model_crop", "model_resize", "model_distortion"):
        apply_sensor_or_tool_fault(page, kind)
        recorded = action(page, "Record changed camera model", "/configure")
        identity = recorded["state"]["camera_model_report_id"]
        report = get(page, f"{prefix}/calibration/records/camera-model-report/{identity}")
        assert not report["passed"] and report["failures"]
        expect(page.locator("#calibration-action")).to_have_text("Inspect camera model")
        assert page.locator("#create").is_disabled()
        rejected = page.request.post(
            f"{prefix}/calibration/cameras/{camera}/candidates",
            data={
                "dataset_id": "not-measured",
                "candidate_id": "must-not-exist",
                "request_id": f"denied-{kind}",
                "expected_revision": recorded["state"]["revision"],
            },
        )
        assert rejected.status == 409 and rejected.json()["reason"] == "CAMERA_MODEL_NOT_VERIFIED"
        page.locator("#calibration-inspect").click()
        page.locator("#calibration-record").select_option(f"camera-model-report/{identity}")
        expect(page.locator("#calibration-summary")).to_contain_text(
            "Optical model verification: FAILED"
        )
        expect(page.locator("#calibration-summary")).to_contain_text(
            "does not determine camera-to-robot X"
        )
        page.get_by_role("link", name="Run & watch", exact=True).click()
    page.screenshot(path=str(artifacts / "wrong-model-blocked.png"), full_page=True)
    assert_accessible(page, artifacts, "wrong-camera-model")
    apply_sensor_or_tool_fault(page, "restore_model")
    restored = action(page, "Record changed camera model", "/configure")
    assert restored["state"]["active_artifact_id"] is None
    assert get(
        page,
        f"{prefix}/calibration/records/camera-model-report/{restored['state']['camera_model_report_id']}",
    )["passed"]
    action(page, "Acquire board images", "/acquisitions")
    candidate = action(page, "Estimate calibration", "/candidates")
    assert candidate["state"]["active_artifact_id"] is None
    assert not errors
    # Explicit negative endpoint checks are expected 409 network entries, not JS failures.
    assert all("409" in message for message in console_errors)


def test_shared_board_dimensions_and_remount_have_measured_recovery(server, browser_page):
    origin, registry = server
    page, artifacts, errors, console_errors, requests = browser_page
    prefix = new_measured_test(page, origin, 83)
    action(page, "Configure camera", "/configure")
    apply_sensor_or_tool_fault(page, "board_dimensions")
    action(page, "Record changed board", "/configure")
    action(page, "Acquire board images", "/acquisitions")
    with page.expect_response(lambda response: response.url.endswith("/candidates")) as response:
        page.locator("#calibration-action").click()
    assert response.value.status == 409
    assert response.value.json()["reason"] == "NO_RELIABLE_TRAINING_CONSENSUS"
    page.wait_for_function("() => !calibration.busy && !busy")
    expect(page.locator("#calibration-error")).to_contain_text("new measurements")
    assert page.locator("#create").is_disabled()
    page.screenshot(path=str(artifacts / "wrong-board-metric-chain-rejected.png"), full_page=True)
    assert_accessible(page, artifacts, "wrong-board-dimensions")
    apply_sensor_or_tool_fault(page, "restore_board_dimensions")
    action(page, "Record changed board", "/configure")
    action(page, "Acquire board images", "/acquisitions")
    action(page, "Estimate calibration", "/candidates")
    action(page, "Validate independently", "/validations")
    page.locator("#calibration-actor").fill("Simulated board acceptance operator")
    west = action(page, "Approve for this simulation", "/approvals")
    page.locator("#calibration-action").click()
    east = approve_camera(page)
    original = {item["camera_id"]: item["state"]["active_artifact_id"] for item in (west, east)}
    changed = apply_sensor_or_tool_fault(page, "board_remount")
    overview = get(page, prefix + "/calibration")
    mount_id = overview["board"]["mounting_id"]
    assert mount_id != "flange-mount-1"
    assert all(state["active_validity"] == "SUSPECT_INVALID" for state in overview["states"])
    expect(page.locator("#calibration-action")).to_have_text("Record changed board")
    assert page.locator("#create").is_disabled()
    page.reload()
    expect(page.locator("#calibration-action")).to_have_text("Record changed board")
    page.screenshot(path=str(artifacts / "shared-board-both-cameras-blocked.png"), full_page=True)
    for camera in ("camera-west", "camera-east"):
        page.locator("#calibration-camera").select_option(camera)
        action(page, "Record changed board", "/configure")
        action(page, "Acquire board images", "/acquisitions")
        candidate = action(page, "Estimate calibration", "/candidates")
        assert candidate["state"]["active_artifact_id"] == original[camera]
        assert candidate["state"]["active_validity"] == "SUSPECT_INVALID"
        action(page, "Validate independently", "/validations")
        page.locator("#calibration-actor").fill("Simulated remount recovery operator")
        current = action(page, "Approve for this simulation", "/approvals")
        assert current["state"]["active_artifact_id"] != original[camera]
        assert current["state"]["board"]["mounting_id"] == mount_id
    action(page, "Remove board and check tool", "/tool-check")
    with page.expect_response(lambda response: response.url.endswith("/v1/wms/tasks")) as response:
        page.locator("#calibration-action").click()
    assert response.value.status == 202
    completed = continue_guided(page, prefix, response.value.json()["session_id"])
    assert completed["status"] == "COMPLETED"
    (artifacts / "board-recovery.json").write_text(
        json.dumps(
            {
                "fault": changed,
                "old_artifacts": original,
                "mounting_id": mount_id,
                "completed": completed,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    assert_accessible(page, artifacts, "board-recovery-complete")
    assert not errors and all("409" in message for message in console_errors)


def test_tool_and_depth_faults_have_separate_evidence_and_guarded_recovery(server, browser_page):
    origin, registry = server
    page, artifacts, errors, console_errors, requests = browser_page
    prefix = new_measured_test(page, origin, 37)
    approved = approve_camera(page)
    original = approved["state"]["active_artifact_id"]
    apply_sensor_or_tool_fault(page, "tool_translation")
    tool = auxiliary(page, "#calibration-tool-recheck", "/tool-check")
    report = get(page, f"{prefix}/calibration/records/tool-verification/{tool['record_ids'][0]}")
    assert not report["passed"] and "TCP_TRANSLATION_CHECK_FAILED" in report["failures"]
    overview = get(page, f"{prefix}/calibration")
    assert overview["states"][0]["active_artifact_id"] == original
    assert overview["states"][0]["active_validity"] == "VERIFIED"
    assert overview["machine"]["tool_verification_id"] is None
    page.locator("#calibration-inspect").click()
    page.locator("#calibration-record").select_option(
        f"tool-verification/{report['verification_id']}"
    )
    expect(page.locator("#calibration-summary")).to_contain_text("TCP_TRANSLATION_CHECK_FAILED")
    investigated_tool = investigate_selected(page, prefix, "INDEPENDENT_TOOL_CHECK_FAILED")
    assert investigated_tool["state"]["active_artifact_id"] == original
    assert investigated_tool["state"]["active_validity"] == "VERIFIED"
    page.screenshot(path=str(artifacts / "changed-tool-independent-check.png"), full_page=True)
    assert_accessible(page, artifacts, "tool-fault-evidence")
    page.get_by_role("link", name="Run & watch", exact=True).click()
    apply_sensor_or_tool_fault(page, "restore_tool")
    restored_tool = auxiliary(page, "#calibration-tool-recheck", "/tool-check")
    assert get(
        page, f"{prefix}/calibration/records/tool-verification/{restored_tool['record_ids'][0]}"
    )["passed"]

    apply_sensor_or_tool_fault(page, "depth_scale")
    expect(page.locator("#calibration-state")).to_contain_text("SUSPECT_INVALID")
    routine = auxiliary(page, "#calibration-routine", "/routine-check")
    scale = get(page, f"{prefix}/calibration/records/routine-check/{routine['record_ids'][0]}")
    assert not scale["passed"] and "SCALE_ERROR_COMPATIBLE" in scale["diagnostic"]["clues"]
    page.locator("#calibration-inspect").click()
    page.locator("#calibration-record").select_option(f"routine-check/{scale['check_id']}")
    expect(page.locator("#calibration-summary")).to_contain_text(
        "INSUFFICIENT_EVIDENCE / UNKNOWN_CAUSE"
    )
    investigated_scale = investigate_selected(page, prefix, "SCALE_ERROR_COMPATIBLE")
    assert investigated_scale["state"]["active_artifact_id"] == original
    assert investigated_scale["state"]["active_validity"] == "SUSPECT_INVALID"
    page.locator("#calibration-source > summary").click()
    expect(page.locator("#calibration-source-content")).to_contain_text("def investigate(")
    page.locator("#calibration-source > summary").click()
    assert_accessible(page, artifacts, "scale-investigation")
    page.screenshot(path=str(artifacts / "depth-scale-diagnostic.png"), full_page=True)
    page.get_by_role("link", name="Run & watch", exact=True).click()
    apply_sensor_or_tool_fault(page, "depth_nonfinite")
    routine = auxiliary(page, "#calibration-routine", "/routine-check")
    missing = get(page, f"{prefix}/calibration/records/routine-check/{routine['record_ids'][0]}")
    assert not missing["passed"] and missing["reference_count"] == 0
    capture = missing["failed_capture_ids"][0]
    page.locator("#calibration-capture").select_option(capture)
    page.locator("#calibration-pixel-panel").evaluate("element => {element.open=true;}")
    page.locator("#calibration-pixel-u").fill("480")
    page.locator("#calibration-pixel-v").fill("360")
    page.locator("#calibration-pixel-inspect").click()
    expect(page.locator("#calibration-pixel-status")).to_contain_text("NO_VALID_DEPTH")
    page.screenshot(path=str(artifacts / "missing-depth-no-target.png"), full_page=True)
    assert_accessible(page, artifacts, "missing-depth")
    apply_sensor_or_tool_fault(page, "restore_sensor")
    routine = auxiliary(page, "#calibration-routine", "/routine-check")
    assert get(page, f"{prefix}/calibration/records/routine-check/{routine['record_ids'][0]}")[
        "passed"
    ]
    assert routine["state"]["active_validity"] == "SUSPECT_INVALID"
    assert page.locator("#create").is_disabled()
    action(page, "Start new measurements", "/begin-measurements")
    action(page, "Acquire board images", "/acquisitions")
    action(page, "Estimate calibration", "/candidates")
    action(page, "Validate independently", "/validations")
    page.locator("#calibration-actor").fill("Simulated recovery operator")
    recovered = action(page, "Approve for this simulation", "/approvals")
    assert recovered["state"]["active_artifact_id"] != original
    page.locator("#calibration-action").click()
    approve_camera(page)
    action(page, "Remove board and check tool", "/tool-check")
    with page.expect_response(lambda response: response.url.endswith("/v1/wms/tasks")) as response:
        page.locator("#calibration-action").click()
    assert response.value.status == 202
    completed = continue_guided(page, prefix, response.value.json()["session_id"])
    assert completed["status"] == "COMPLETED"
    (artifacts / "fault-recovery.json").write_text(
        json.dumps(
            {
                "tool": report,
                "scale": scale,
                "missing": missing,
                "recovered": recovered,
                "session": completed,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    assert not errors and not console_errors


@pytest.mark.parametrize("seed", [37, 97])
def test_calibration_images_approval_guided_pick_and_readonly_inspection(
    server, browser_page, seed
):
    origin, registry = server
    page, artifacts, errors, console_errors, requests = browser_page
    command_mode = "tcp" if seed == 97 else "flange"
    prefix = new_measured_test(page, origin, seed, command_mode)
    page.locator("#simulation-boundaries > summary").click()
    expect(page.locator("#simulation-profile-boundary")).to_contain_text("Ideal synthetic gantry")
    expect(page.locator("#simulation-sensor-boundary")).to_contain_text("OpenCV detects")
    expect(page.locator("#simulation-boundaries")).not_to_contain_text("images are not analyzed")
    page.screenshot(path=str(artifacts / "measured-simulation-boundaries.png"), full_page=True)
    page.locator("#simulation-boundaries > summary").click()
    page.screenshot(path=str(artifacts / "configure-desktop.png"), full_page=True)
    assert_accessible(page, artifacts, "configure")
    assert page.locator("#create").is_disabled()
    west = approve_camera(page)
    expect(page.locator("#calibration-action")).to_have_text("Calibrate the other camera")
    page.locator("#calibration-action").click()
    expect(page.locator("#calibration-camera")).to_have_value("camera-east")
    east = approve_camera(page)
    action(page, "Remove board and check tool", "/tool-check")
    page.screenshot(path=str(artifacts / "approved-desktop.png"), full_page=True)
    with page.expect_response(lambda response: response.url.endswith("/v1/wms/tasks")) as response:
        page.locator("#calibration-action").click()
    assert response.value.status == 202, response.value.text()
    created = response.value.json()
    completed = continue_guided(page, prefix, created["session_id"])
    assert completed["status"] == "COMPLETED", completed
    evidence = get(page, f"{prefix}/jobs/{completed['job_id']}/evidence")
    assert evidence["job"]["state"] == "COMPLETED"
    command = evidence["command"]
    assert command["schema_version"] == "3.0"
    target = command["calibrated_plan"]["target"]
    assert target["mode"] == command_mode
    assert (
        target["command_target"]
        == target["tcp_target" if command_mode == "tcp" else "flange_target"]
    )
    np.testing.assert_allclose(
        np.array(target["flange_target"]["matrix"])[:3, 3]
        - np.array(target["tcp_target"]["matrix"])[:3, 3],
        [0, 0, 0.18],
        atol=1e-12,
    )
    assert (
        command["calibrated_plan"]["observed_object"]["binding"]["artifact_id"]
        == west["state"]["active_artifact_id"]
    )
    assert (
        command["calibrated_plan"]["supporting_bindings"][0]["artifact_id"]
        == east["state"]["active_artifact_id"]
    )
    playback = get(page, f"{prefix}/jobs/{completed['job_id']}/playback")
    assert playback["recording"]["source"] == "SYNTHETIC_CONTROLLER_REPORTS"
    assert len(playback["recording"]["frames"]) == 121
    saved_scene = playback["scene"]
    cell = get(page, prefix + "/cell")
    records = get(page, prefix + "/calibration/records")
    assert any(record["kind"] == "http-trace" for record in records)
    assert any(record["kind"] == "calculation-trace" for record in records)
    assert any(record["kind"] == "camera-agreement" for record in records)
    quality_record = next(record for record in records if record["kind"] == "measurement-quality")
    assert quality_record["source_trace_id"]
    for observation in evidence["observations"]:
        assert observation["objects"][0]["confidence"] is None
        assert observation["objects"][0]["uncertainty_m"] is None
        assert observation["objects"][0]["calibrated_object"]["measurement_quality"]["passed"]
    page.locator("#calibration-camera").select_option(quality_record["camera_id"])
    with page.expect_response(
        lambda response: response.url.endswith("/calibration/records")
    ) as refreshed_records:
        page.locator("#calibration-inspect").click()
    assert refreshed_records.value.ok
    page.locator("#calibration-record").select_option("measurement-quality/" + quality_record["id"])
    expect(page.locator("#calibration-summary")).to_contain_text(
        "statistical confidence and point uncertainty are not estimated"
    )
    expect(page.locator("#calibration-summary")).to_contain_text("RGB/depth correspondence")
    page.screenshot(
        path=str(artifacts / "measured-quality-no-invented-confidence.png"), full_page=True
    )
    assert_accessible(page, artifacts, "measured-quality")
    page.get_by_role("link", name="Run & watch", exact=True).click()
    page.reload()
    expect(page.locator("#calibration-action")).to_have_text("Run a guided pick")
    page.locator("#calibration-camera").select_option("camera-west")
    observed = command["calibrated_plan"]["observed_object"]
    page.locator("#calibration-capture").select_option(observed["binding"]["capture_id"])
    page.locator("#calibration-pixel-panel > summary").click()
    u, v = (round(value) for value in observed["surface_point"]["selected_rgb_pixel"])
    page.locator("#calibration-pixel-u").fill(str(u))
    page.locator("#calibration-pixel-v").fill(str(v))
    pixel_results = []
    for mode in ("native", "aligned"):
        page.locator("#calibration-pixel-mode").select_option(mode)
        page.locator("#calibration-pixel-inspect").focus()
        with page.expect_response(
            lambda response: "/calibration/inspect-pixel?" in response.url
        ) as inspected:
            page.locator("#calibration-pixel-inspect").press("Enter")
        assert inspected.value.ok, inspected.value.text()
        result = inspected.value.json()
        if mode == "aligned" and result["result"].get("code") == "ALIGNED_DEPTH_HOLE":
            # RGB has more pixels than depth. A dense registered image is not
            # promised: preserve holes, then explicitly select a measured return.
            assert "point" not in result["result"]
            expect(page.locator("#calibration-pixel-status")).to_contain_text("no depth sample")
            ru, rv = (
                round(value)
                for value in pixel_results[0]["result"]["calculation"]["outputs"][
                    "projected_rgb_pixel"
                ]
            )
            page.locator("#calibration-pixel-u").fill(str(ru))
            page.locator("#calibration-pixel-v").fill(str(rv))
            with page.expect_response(
                lambda response: "/calibration/inspect-pixel?" in response.url
            ) as inspected:
                page.locator("#calibration-pixel-inspect").press("Enter")
            assert inspected.value.ok, inspected.value.text()
            result = inspected.value.json()
        assert "point" in result["result"], result["result"]
        assert "READ_ONLY_RECOMPUTATION" in result["scope"]
        assert (
            np.linalg.norm(np.array(result["result"]["point"]) - observed["surface_point"]["point"])
            < 0.005
        )
        pixel_results.append(result)
        expect(page.locator("#calibration-pixel-status")).to_contain_text("Base point")
        assert page.evaluate("player.overlay.some(item=>item.name==='Inspection/native-depth-ray')")
    assert pixel_results[1]["alignment"]["value_semantics"] == "native_optical_z"
    (artifacts / "pixel-recomputation.json").write_text(
        json.dumps(
            [
                {
                    key: value
                    for key, value in result.items()
                    if key not in {"rgb_preview", "depth_preview"}
                }
                for result in pixel_results
            ],
            indent=2,
        ),
        encoding="utf-8",
    )
    assert_accessible(page, artifacts, "pixel-inspection")
    page.screenshot(path=str(artifacts / "pixel-depth-ray.png"), full_page=True)
    page.locator("#calibration-camera").select_option("camera-east")
    assert page.evaluate("player.overlay.length===0")
    assert get(page, prefix + "/cell") == cell
    assert len(get(page, prefix + "/calibration/records")) == len(records)
    page.locator("#calibration-inspect").click()
    page.locator("#calibration-record").select_option("validation/" + east["state"]["report_id"])
    expect(page.locator("#calibration-summary")).to_contain_text("PASS")
    expect(page.locator("#calibration-summary")).not_to_contain_text("approval is still required")
    page.get_by_role("link", name="Run & watch", exact=True).click()
    with page.expect_response(lambda response: "/calibration/geometry?" in response.url) as shown:
        page.locator("#calibration-geometry-mode").select_option("record")
    assert shown.value.ok
    assert len(shown.value.json()["numbers"]["references"]) == 24
    expect(page.locator("#calibration-geometry-status")).to_contain_text(
        "Independent reference errors"
    )
    page.screenshot(path=str(artifacts / "reference-error-geometry.png"), full_page=True)
    page.locator("#calibration-geometry-mode").select_option("cell")
    page.locator("#calibration-camera").select_option("camera-west")
    page.locator("#calibration-inspect").click()
    target_record = next(item["id"] for item in records if item["kind"] == "runtime-target")
    page.locator("#calibration-record").select_option("runtime-target/" + target_record)
    page.get_by_role("link", name="Run & watch", exact=True).click()
    with page.expect_response(lambda response: "/calibration/geometry?" in response.url) as shown:
        page.locator("#calibration-geometry-mode").select_option("record")
    assert shown.value.ok, shown.value.text()
    assert (
        shown.value.json()["numbers"]["command_target"]
        == command["calibrated_plan"]["target"]["command_target"]
    )
    expect(page.locator("#calibration-geometry-status")).to_contain_text(
        "Saved grasp, approach and command target"
    )
    page.screenshot(path=str(artifacts / "target-approach-geometry.png"), full_page=True)
    page.locator("#calibration-geometry-mode").select_option("cell")
    page.locator("#calibration-camera").select_option("camera-east")
    page.locator("#calibration-inspect").click()
    page.locator("#calibration-record").select_option("validation/" + east["state"]["report_id"])
    page.locator("#calibration-source > summary").click()
    expect(page.locator("#calibration-source-scope")).to_contain_text("Saved source")
    page.locator("#calibration-full").click()
    expect(page.locator("#calibration-component")).to_be_visible()
    expect(page.locator("#calibration-source-scope")).to_contain_text("Current reference source")
    assert page.locator("#calibration-full").evaluate(
        "el => getComputedStyle(el).backgroundColor"
    ) != page.locator("#calibration-excerpt").evaluate("el => getComputedStyle(el).backgroundColor")
    page.screenshot(path=str(artifacts / "evidence-desktop.png"), full_page=True)
    assert_accessible(page, artifacts, "expanded-evidence")
    assert get(page, prefix + "/cell") == cell
    assert len(get(page, prefix + "/calibration/records")) == len(records)
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.screenshot(path=str(artifacts / "evidence-narrow.png"), full_page=True)
    assert_accessible(page, artifacts, "narrow-evidence")
    page.emulate_media(reduced_motion="reduce")
    page.evaluate("document.documentElement.style.fontSize='200%'")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.screenshot(path=str(artifacts / "enlarged-text.png"), full_page=True)
    page.evaluate("document.documentElement.style.fontSize=''")
    with page.expect_download(timeout=120_000) as downloaded:
        page.locator("#calibration-export").click()
    export_path = artifacts / "calibration-evidence.zip"
    downloaded.value.save_as(export_path)
    with ZipFile(export_path) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["seed"] == seed
        assert any(record["kind"] == "RobotCommand" for record in manifest["application_records"])
        for record in manifest["records"]:
            if record["kind"] == "capture":
                assert "images/" + record["body"]["rgb"]["path"] in archive.namelist()
    assert len(get(page, prefix + "/calibration/records")) == len(records)
    if seed == 37:
        page.set_viewport_size({"width": 1280, "height": 900})
        page.get_by_role("link", name="Run & watch", exact=True).click()
        page.locator("#calibration-checks > summary").click()
        # Keyboard reaches and invokes a real routine-reference acquisition.
        page.locator("#calibration-routine").focus()
        assert page.locator("#calibration-routine").evaluate("el => el === document.activeElement")
        auxiliary(page, "#calibration-routine", "/routine-check")
        page.get_by_text("Introduce a simulated camera fault", exact=True).click()
        moved = auxiliary(page, "#calibration-move-camera", "/move-camera")
        assert moved["state"]["active_validity"] == "SUSPECT_INVALID"
        assert get(page, f"{prefix}/jobs/{completed['job_id']}/playback")["scene"] == saved_scene
        expect(page.locator("#create")).to_be_disabled()
        checked = auxiliary(page, "#calibration-routine", "/routine-check")
        report = get(
            page, prefix + "/calibration/records/routine-check/" + checked["record_ids"][0]
        )
        assert not report["passed"]
        assert report["maximum_error_mm"] > 5
        expect(page.locator("#cell-summary")).to_contain_text("Controller: READY")
        expect(page.locator("#cell-summary")).to_contain_text("calibration checked separately")
        expect(page.locator("#motion-outcome")).to_contain_text("Recorded job:")
        page.evaluate("window.scrollTo(0,0)")
        page.screenshot(path=str(artifacts / "moved-camera-blocked.png"), full_page=True)
        page.set_viewport_size({"width": 1280, "height": 720})
        page.evaluate("window.scrollTo(0,0)")
        primary = page.locator("#calibration-action").bounding_box()
        scene = page.locator(".scene-stage").bounding_box()
        assert primary and primary["y"] + primary["height"] <= 720, primary
        assert scene and scene["y"] + 140 <= 720, scene
        page.screenshot(path=str(artifacts / "moved-camera-laptop-720.png"), full_page=True)
        assert_accessible(page, artifacts, "blocked-laptop")
        page.set_viewport_size({"width": 1280, "height": 900})
        action(page, "Start new measurements", "/begin-measurements")
        action(page, "Acquire board images", "/acquisitions")
        action(page, "Estimate calibration", "/candidates")
        action(page, "Validate independently", "/validations")
        page.locator("#calibration-actor").fill("Simulated recovery approval")
        renewed = action(page, "Approve for this simulation", "/approvals")
        assert renewed["state"]["active_artifact_id"] != east["state"]["active_artifact_id"]
        action(page, "Remove board and check tool", "/tool-check")
        expect(page.locator("#create")).to_be_enabled()
        page.screenshot(path=str(artifacts / "recovery-approved.png"), full_page=True)
        with page.expect_response(
            lambda response: response.url.endswith("/v1/wms/tasks")
        ) as response:
            page.locator("#calibration-action").click()
        assert response.value.ok, response.value.text()
        resumed = continue_guided(page, prefix, response.value.json()["session_id"])
        assert resumed["status"] == "COMPLETED", resumed
        resumed_evidence = get(page, prefix + "/jobs/" + resumed["job_id"] + "/evidence")
        assert (
            resumed_evidence["command"]["calibrated_plan"]["supporting_bindings"][0]["artifact_id"]
            == renewed["state"]["active_artifact_id"]
        )
        assert resumed_evidence["command"]["command_id"] != command["command_id"]
    (artifacts / "calibration-result.json").write_text(
        json.dumps({"west": west, "east": east, "evidence": evidence, "cell": cell}, indent=2),
        encoding="utf-8",
    )
    assert not errors
    assert not console_errors
