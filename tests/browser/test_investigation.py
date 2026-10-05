"""Actual Chromium journeys against real HTTP, persistence and both cell runtimes.

Only the application-error case intercepts a response. Normal/fault/review journeys
use the checked-in API and runtime; navigation must not change durable evidence.
"""

import hashlib
import json
import re
import socket
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest
import uvicorn
from playwright.sync_api import expect, sync_playwright

from apps.api.app import create_workspace_app
from robotops.blender.adapter import BlenderRuntime
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings


@pytest.fixture
def server(tmp_path, request):
    runtime_type = getattr(request, "param", SyntheticRuntime)
    app = create_workspace_app(
        tmp_path / "worlds", runtime_type=runtime_type, settings=Settings.hkm()
    )
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        service = uvicorn.Server(uvicorn.Config(app, log_level="warning", access_log=False))
        thread = threading.Thread(target=service.run, kwargs={"sockets": [listener]}, daemon=True)
        thread.start()
        deadline = time.monotonic() + 20
        while not service.started and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert service.started, "Local browser-test API failed to start"
        try:
            yield f"http://127.0.0.1:{listener.getsockname()[1]}", app.state.test_registry
        finally:
            service.should_exit = True
            thread.join(timeout=20)
            assert not thread.is_alive(), "Browser-test API did not shut down"


@pytest.fixture
def browser_page(request):
    directory = (
        Path("artifacts/investigation-browser")
        / datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
        / request.node.name
    )
    directory.mkdir(parents=True)
    ui_sources = [
        *Path("apps/erp_ui").glob("*.js"),
        Path("apps/erp_ui/index.html"),
        Path("apps/erp_ui/theme.css"),
        Path(__file__),
    ]
    source_hashes = {
        path.as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in ui_sources
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=["--enable-unsafe-swiftshader"])
        context = browser.new_context()
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        page.set_default_timeout(20_000)
        errors, console_errors, requests = [], [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda message: (
                console_errors.append(message.text) if message.type == "error" else None
            ),
        )
        page.on("request", lambda req: requests.append({"method": req.method, "url": req.url}))
        try:
            yield page, directory, errors, console_errors, requests
        finally:
            page.screenshot(path=str(directory / "last-state.png"), full_page=True)
            (directory / "browser.json").write_text(
                json.dumps(
                    {
                        "page_errors": errors,
                        "console_errors": console_errors,
                        "requests": requests,
                        "source_sha256_at_start": source_hashes,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            context.tracing.stop(path=str(directory / "trace.zip"))
            browser.close()


def get(page, url):
    response = page.request.get(url)
    assert response.ok, response.text()
    return response.json()


def open_ready(page, origin, viewport):
    page.set_viewport_size(viewport)
    page.goto(origin)
    expect(page.locator("#create")).to_be_enabled()
    expect(page.locator("#motion-state")).to_have_text("3D cell ready")
    expect(page.locator("#motion-renderer")).to_contain_text("3D")
    expect(page.locator("#scenario-brief")).to_contain_text("Normal pick")
    expect(page.locator("#scenario-watch")).to_contain_text("output tote")
    assert not page.locator("#timeline-panel").is_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def choose_pick(page, fault=""):
    if not page.locator("#setup-panel").evaluate("element => element.open"):
        page.locator("#setup-panel > summary").click()
    page.locator("#scenario").select_option(fault)
    with page.expect_response(
        lambda response: response.request.method == "POST" and response.url.endswith("/run"),
        timeout=180_000,
    ) as run:
        page.locator("#create").click()
    assert run.value.ok, run.value.text()
    job = run.value.json()
    expect(page.locator("#selected-result")).to_contain_text(job["state"], timeout=30_000)
    return job


def inspect(page):
    if not page.locator("#investigation-dialog").is_visible():
        page.locator("#inspect-selected").click()
    expect(page.locator("#investigation-dialog")).to_be_visible()


def screenshot(page, directory, name):
    page.screenshot(
        path=str(directory / f"{name}.png"),
        full_page=not page.locator("#investigation-dialog").is_visible(),
    )


def panel_bounds(page):
    rect = page.locator("#investigation-dialog").bounding_box()
    assert rect is not None
    viewport = page.viewport_size
    assert rect["x"] >= 0 and rect["y"] >= 0
    assert rect["x"] + rect["width"] <= viewport["width"] + 1
    assert rect["y"] + rect["height"] <= viewport["height"] + 1
    assert page.locator(".inspection-body").evaluate("el => el.scrollWidth <= el.clientWidth + 1")


@pytest.mark.parametrize(
    "viewport",
    [{"width": 1440, "height": 1000}, {"width": 390, "height": 844}],
    ids=["desktop", "compact"],
)
@pytest.mark.parametrize(
    "server",
    [SyntheticRuntime, pytest.param(BlenderRuntime, marks=pytest.mark.blender)],
    indirect=True,
    ids=["synthetic", "blender"],
)
def test_run_notice_investigate_and_return(server, browser_page, viewport):
    origin, registry = server
    page, directory, errors, console_errors, requests = browser_page
    open_ready(page, origin, viewport)
    screenshot(page, directory, "01-ready")
    happy = choose_pick(page)
    assert happy["state"] == "COMPLETED"
    expect(page.locator("#motion-play")).to_be_enabled()
    page.locator("#motion-scrub").fill("3")
    assert page.locator("#motion-play").inner_text() == "Play"
    selected = page.locator("#orders").input_value()
    cursor = page.locator("#motion-scrub").input_value()
    inspect(page)
    expect(page.locator("#inspection-finding")).to_contain_text("destination")
    page.locator("#return-simulation").click()
    expect(page.locator("#orders")).to_have_value(selected)
    expect(page.locator("#motion-scrub")).to_have_value(cursor)
    screenshot(page, directory, "02-normal-completed")

    unusual = choose_pick(page, "DROP_ACK_AFTER_EFFECT")
    assert unusual["state"] == "UNKNOWN_OUTCOME"
    expect(page.locator("#guide-title")).to_contain_text("outcome uncertain")
    expect(page.locator("#investigation-dialog")).not_to_be_visible()
    expect(page.locator("#inspect-selected")).to_have_attribute("data-attention", "true")
    screenshot(page, directory, "03-notice-uncertainty")
    inspect(page)
    expect(page.locator("#inspection-symptom")).to_contain_text("no confirmed result")
    expect(page.locator("#inspection-finding")).to_contain_text("1 product move")
    expect(page.locator("#inspection-limit")).to_contain_text("does not prove")
    panel_bounds(page)
    screenshot(page, directory, "03-unusual-result")
    job_id = unusual["job_id"]
    command_id = unusual["command_id"]
    before = get(page, f"{origin}/jobs/{job_id}/evidence")
    assert before["journal"]["effect_count"] == 1
    posts = [request for request in requests if request["method"] == "POST"]

    page.locator("#view-evidence").click()
    assert not page.locator("#timeline-panel").evaluate("element => element.open")
    assert (
        json.loads(page.locator("#journal-record").inner_text())["command"]["command_id"]
        == command_id
    )
    expect(page.locator("#observation-record")).to_contain_text("No assessed observation")
    screenshot(page, directory, "04-evidence")
    page.locator("#journal-details > summary").click()
    page.locator("#observation-details > summary").click()
    page.locator("#timeline-panel > summary").click()
    page.locator("#timeline-filter").select_option("all")
    assert page.locator(".timeline-scroll").bounding_box()["height"] <= 261
    page.locator("#timeline button").first.click()
    event = json.loads(page.locator("#event-record").inner_text())
    assert event.get("job_id") in (None, job_id)
    page.locator("#tab-manual").click()
    expect(page.locator("#manual-reproduce")).to_contain_text("DROP_ACK_AFTER_EFFECT")
    expect(page.locator("#manual-sources")).to_contain_text("robotops/verification/verifier.py")
    urls = re.findall(r"Invoke-RestMethod '([^']+)'", page.locator("#manual-requests").inner_text())
    assert len(urls) == 2
    assert get(page, urls[0])["job"]["job_id"] == job_id
    assert all(event.get("order_id") == unusual["order_id"] for event in get(page, urls[1]))
    with page.expect_download() as download:
        page.locator("#download-evidence").click()
    download.value.save_as(directory / "investigation.json")
    bundle = json.loads((directory / "investigation.json").read_text(encoding="utf-8"))
    assert bundle["evidence"] == before
    assert bundle["test_id"] == "original"
    assert bundle["order_events"]
    assert [request for request in requests if request["method"] == "POST"] == posts
    assert get(page, f"{origin}/jobs/{job_id}/evidence") == before
    screenshot(page, directory, "05-manual-inspection")
    page.locator("#return-simulation").click()
    expect(page.locator("#orders")).to_have_value(job_id)
    page.locator(".viewer-details > summary").click()
    page.locator(".replay-options > summary").click()
    page.locator("#orders").select_option(happy["job_id"])
    page.locator("#guide-action").click()
    expect(page.locator("#orders")).to_have_value(happy["job_id"])
    expect(page.locator("#inspection-context")).to_contain_text(job_id)
    page.locator("#tab-evidence").click()
    page.locator("#technical-status > summary").click()
    expect(page.locator("#status-command")).to_have_text(command_id)
    expect(page.locator("#job-state")).to_have_text("UNKNOWN_OUTCOME")
    expect(page.locator("#command")).to_contain_text(command_id)
    assert [request for request in requests if request["method"] == "POST"] == posts

    page.locator("#tab-findings").click()
    page.locator("#observation").select_option("CONTRADICTORY_OBSERVATION")
    with page.expect_response(
        lambda response: response.url.endswith("/reconcile") and response.request.method == "POST"
    ) as review:
        page.locator("#resolve-blocker").click()
    assert review.value.json()["state"] == "REQUIRES_INTERVENTION"
    expect(page.locator("#inspection-context")).to_contain_text("REQUIRES_INTERVENTION")
    expect(page.locator("#inspection-symptom")).to_contain_text("could not establish")
    page.locator("#tab-evidence").click()
    if not page.locator("#observation-details").evaluate("element => element.open"):
        page.locator("#observation-details > summary").click()
    observation = json.loads(page.locator("#observation-record").inner_text())
    assessed = get(page, f"{origin}/jobs/{job_id}/evidence")
    assert assessed["verifications"][-1]["observation_id"] == observation["observation_id"]
    assert assessed["verifications"][-1]["verdict"] == "INCONCLUSIVE"
    assert assessed["command"]["command_id"] == command_id
    assert assessed["journal"]["effect_count"] == 1
    screenshot(page, directory, "06-conflicting-sensor-report")
    page.locator("#tab-findings").click()
    page.locator("#use-normal").click()
    with page.expect_response(
        lambda response: response.url.endswith("/reconcile") and response.request.method == "POST"
    ) as resolved:
        page.locator("#resolve-blocker").click()
    assert resolved.value.json()["state"] == "COMPLETED"
    expect(page.locator("#investigation-title")).to_contain_text("Pick confirmed")
    expect(page.locator("#observation-controls")).not_to_be_visible()
    after = get(page, f"{origin}/jobs/{job_id}/evidence")
    assert after["command"]["command_id"] == command_id
    assert len(after["reconciliations"]) == 2
    assert after["journal"]["effect_count"] == 1
    effects = registry.original.runtime.events(command_id)
    assert sum(event.event_type == "PICK_EFFECT" for event in effects) == 1
    assert (
        len(
            [
                request
                for request in requests
                if request["method"] == "POST" and request["url"].endswith("/run")
            ]
        )
        == 2
    )
    screenshot(page, directory, "07-resolved-original-pick")
    page.locator("#return-simulation").click()
    page.locator("#new-test").click()
    expect(page.locator("#cell-profile")).to_have_value("hkm_inspired_v1")
    page.locator("#create-test").click()
    expect(page.locator("#new-test-dialog")).not_to_be_visible()
    new_test_id = page.locator("#test-history").input_value()
    assert new_test_id != "original"
    fresh = choose_pick(page)
    assert fresh["state"] == "COMPLETED"
    inspect(page)
    page.locator("#tab-manual").click()
    scoped_urls = re.findall(
        r"Invoke-RestMethod '([^']+)'", page.locator("#manual-requests").inner_text()
    )
    assert len(scoped_urls) == 2
    assert all(f"/simulation-tests/{new_test_id}/" in url for url in scoped_urls)
    assert get(page, scoped_urls[0])["job"]["job_id"] == fresh["job_id"]
    assert fresh["job_id"] != job_id
    screenshot(page, directory, "08-independent-test-inspection")
    page.locator("#return-simulation").click()
    page.locator("#test-history").select_option("original")
    expect(page.locator("#test-status")).to_contain_text("read-only")
    if not page.locator(".viewer-details").evaluate("el => el.open"):
        page.locator(".viewer-details > summary").click()
    if not page.locator(".replay-options").evaluate("el => el.open"):
        page.locator(".replay-options > summary").click()
    page.locator("#orders").select_option(job_id)
    inspect(page)
    expect(page.locator("#review-label")).to_contain_text("read-only")
    expect(page.locator("#observation-controls")).not_to_be_visible()
    page.locator("#tab-evidence").focus()
    page.keyboard.press("ArrowRight")
    expect(page.locator("#tab-manual")).to_be_focused()
    expect(page.locator("#manual-identity")).to_contain_text(command_id)
    panel_bounds(page)
    assert not errors, errors
    assert not console_errors, console_errors
    (directory / "result.json").write_text(
        json.dumps(
            {
                "runtime": registry.runtime_type.__name__,
                "viewport": viewport,
                "job_id": job_id,
                "command_id": command_id,
                "effect_count": 1,
                "review_states": ["UNKNOWN_OUTCOME", "REQUIRES_INTERVENTION", "COMPLETED"],
                "evidence": after,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_app_request_failure_does_not_become_simulated_outcome(server, browser_page):
    origin, _ = server
    page, directory, errors, console_errors, _ = browser_page
    open_ready(page, origin, {"width": 1440, "height": 1000})
    page.route(
        "**/jobs/*/run",
        lambda route: route.fulfill(
            status=503,
            content_type="application/json",
            body='{"reason":"BROWSER_TEST_SERVICE_UNAVAILABLE"}',
        ),
    )
    page.locator("#create").click()
    expect(page.locator("#message")).to_have_attribute("data-kind", "error")
    expect(page.locator("#message")).to_contain_text(
        "separate from the recorded simulation outcome"
    )
    orders = get(page, origin + "/orders")
    assert len(orders) == 1
    evidence = get(page, origin + f"/jobs/{orders[0]['job_ids'][0]}/evidence")
    assert evidence["job"]["state"] == "RECEIVED"
    assert evidence["command"] is None
    assert evidence["journal"] is None
    assert not errors
    assert console_errors and all("503" in error for error in console_errors)
    screenshot(page, directory, "app-error-separate-from-simulation")
