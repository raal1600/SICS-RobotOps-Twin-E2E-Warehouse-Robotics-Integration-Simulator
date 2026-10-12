"""The browser follows actual reference acquisition, identification and Python reconstruction."""

import json

import test_calibration_console as calibration
from playwright.sync_api import expect
from test_client_rebuild import assert_accessible
from test_investigation import get

server = calibration.server
browser_page = calibration.browser_page


def test_reference_measurements_expose_real_source_masks_operands_and_readonly_replay(
    server, browser_page
):
    origin, registry = server
    page, artifacts, errors, console_errors, requests = browser_page
    prefix = calibration.new_measured_test(page, origin, 83)
    calibration.approve_camera(page)
    page.locator("#calibration-checks").evaluate("element => {element.open=true;}")
    checked = calibration.auxiliary(page, "#calibration-routine", "/routine-check")
    report = get(page, prefix + "/calibration/records/routine-check/" + checked["record_ids"][0])
    assert report["passed"] and report["reference_count"] == 24
    capture_id = report["references"][0]["reference_id"]
    before = get(page, prefix + "/calibration")
    cell = get(page, prefix + "/cell")
    page.locator("#calibration-capture").select_option(capture_id)
    expect(page.locator("#calibration-depth-display")).to_contain_text("raw sensor units")
    page.locator("#calibration-inspect").click()
    page.locator("#calibration-source > summary").click()
    evidence = {}
    for kind, symbol in (
        ("capture", "ControllerSensor.reference_batch"),
        ("surface-detection", "identify_surface"),
        ("reference", "reconstruct"),
    ):
        page.locator("#calibration-record").select_option(kind + "/" + capture_id)
        rows = get(page, prefix + "/calibration/records")
        row = next(item for item in rows if item["kind"] == kind and item["id"] == capture_id)
        trace = get(
            page, prefix + "/calibration/records/calculation-trace/" + row["source_trace_id"]
        )
        assert trace["symbol"] == symbol and not trace["error"]
        assert trace["classification"] == "IN_PROCESS_PYTHON"
        assert trace["source"]["loaded_function_verification"] == "MATCHED_PYTHON_CODE"
        expect(page.locator("#calibration-source-content")).to_contain_text(
            "def " + symbol.split(".")[-1]
        )
        if kind == "surface-detection":
            expect(page.locator("#calibration-summary")).to_contain_text(
                "One declared purple survey patch"
            )
            assert trace["output"]["mask"]["shape"] == [720, 960]
        if kind == "reference":
            expect(page.locator("#calibration-summary")).to_contain_text("Surveyed base point")
            expect(page.locator("#calibration-summary")).to_contain_text("Reconstructed base point")
            assert (
                trace["inputs"]["x"]["source"] == "c" and trace["inputs"]["x"]["destination"] == "b"
            )
            assert trace["output"]["calculation"]["inputs"]
        evidence[kind] = trace
    page.locator("#calibration-protocol").evaluate(
        "element => {element.closest('details').open=true;}"
    )
    expect(page.locator("#calibration-protocol")).to_contain_text(
        "independent_surveyed_base_point_m"
    )
    page.screenshot(path=str(artifacts / "reference-reconstruction-source.png"), full_page=True)
    assert_accessible(page, artifacts, "reference-inspection")
    page.reload()
    expect(page.locator("#calibration-record")).to_have_value("reference/" + capture_id)
    assert get(page, prefix + "/cell") == cell
    after = get(page, prefix + "/calibration")
    assert after["states"] == before["states"]
    (artifacts / "reference-trace-evidence.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )
    assert not errors and not console_errors
