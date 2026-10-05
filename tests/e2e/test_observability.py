from html.parser import HTMLParser

from fastapi.testclient import TestClient

from apps.api.app import create_app
from robotops.cell.runtime import SyntheticRuntime
from robotops.domain.models import Fault, RobotCommand
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


def test_metrics_timeline_and_dashboard_survive_restart(tmp_path, order_request):
    store = Store(tmp_path / "workflow.db")
    runtime = SyntheticRuntime(tmp_path / "runtime.db")
    engine = Engine(store, runtime)
    client = TestClient(create_app(store, engine))
    job_id = store.intake(order_request, "key").job_ids[0]
    uncertain = engine.run(job_id, Fault.DROP_ACK_AFTER_EFFECT)
    assert "robotops_jobs_unknown_total 1" in client.get("/metrics").text
    engine.reconcile(job_id)
    engine.gateway.send(store.load(RobotCommand, uncertain.command_id))
    metrics = client.get("/metrics").text
    for required in [
        "robotops_jobs_received_total 1",
        "robotops_jobs_completed_total 1",
        "robotops_jobs_failed_total 0",
        "robotops_jobs_intervention_total 0",
        "robotops_commands_total 1",
        "robotops_duplicate_commands_suppressed_total 1",
        "robotops_injected_failures_total 1",
        'robotops_reconciliation_total{outcome="VERIFIED_SUCCESS"} 1',
        "robotops_pipeline_latency_seconds_count 1",
    ]:
        assert required in metrics
    latency = next(
        line
        for line in metrics.splitlines()
        if line.startswith("robotops_pipeline_latency_seconds_sum ")
    )
    assert float(latency.split()[-1]) > 0
    restarted = TestClient(
        create_app(Store(store.path), Engine(Store(store.path), SyntheticRuntime(runtime.db.path)))
    )
    assert restarted.get("/metrics").text == metrics
    evidence = restarted.get(f"/jobs/{job_id}/evidence").json()
    assert evidence["journal"]["effect_count"] == 1
    assert evidence["verifications"][-1]["verdict"] == "VERIFIED_SUCCESS"
    assert len(evidence["observations"]) == 2
    assert evidence["reconciliations"][0]["command"]["command_id"] == uncertain.command_id
    page = restarted.get("/")
    assert page.status_code == 200
    assert all(
        label in page.text
        for label in ["Event timeline", "Reconcile selected job", "Saved Blender snapshot"]
    )

    class SnapshotDisclosure(HTMLParser):
        panel = None

        def __init__(self):
            super().__init__()
            self.controls = {}

        def handle_starttag(self, tag, attrs):
            attributes = dict(attrs)
            if ident := attributes.get("id"):
                self.controls[ident] = tag, attributes
            if attributes.get("id") == "visual-panel":
                self.panel = tag, attributes

    disclosure = SnapshotDisclosure()
    disclosure.feed(page.text)
    assert disclosure.panel is not None
    tag, attributes = disclosure.panel
    assert tag == "details" and "open" not in attributes
    timeline_tag, timeline_attributes = disclosure.controls["timeline-panel"]
    assert timeline_tag == "details" and "open" not in timeline_attributes
    assert disclosure.controls["investigation-dialog"][0] == "dialog"
    for tab, pane in (("tab-evidence", "pane-evidence"), ("tab-manual", "pane-manual")):
        assert disclosure.controls[tab][1]["aria-controls"] == pane
        assert disclosure.controls[pane][1]["role"] == "tabpanel"
    assert disclosure.controls["reconcile"][0] == "button"
    assert restarted.get("/ui/app.js").status_code == 200
    assert restarted.get("/fixtures").json()["runtime"] == "headless"
    assert restarted.get("/artifacts/latest.png").status_code == 404
