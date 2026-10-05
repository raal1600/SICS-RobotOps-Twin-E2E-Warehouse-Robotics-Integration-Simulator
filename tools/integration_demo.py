"""Drive the same bounded REST stages automatically with explicit physical consent.

Examples (start either the local API or complete lab stack first)::

    uv run python -m tools.integration_demo --authorize-robot --scenario happy_path
    uv run python -m tools.integration_demo --authorize-robot --scenario lost_ack_after_effect

Without --authorize-robot this script stops at the physical gate. It never calls
the legacy run endpoint. Lost replies reconcile the saved original identity.
"""

import argparse
import json
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

SCENARIOS: dict[str, str | None] = {
    "happy_path": None,
    "lost_ack_after_effect": "DROP_ACK_AFTER_EFFECT",
    "lost_ack_before_effect": "DROP_ACK_BEFORE_EFFECT",
    "duplicate_delivery": "DUPLICATE_DELIVERY",
    "broker_transient": "BROKER_TRANSIENT",
    "opcua_disconnect": "OPC_UA_DISCONNECT",
    "stale_observation": "STALE_OBSERVATION",
    "wms_unavailable": "WMS_UNAVAILABLE",
}


def _json(response: httpx.Response) -> Any:
    response.raise_for_status()
    return response.json()


def drive(
    client: httpx.Client,
    *,
    scenario: str,
    authorize_robot: bool,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Automatic and browser callers authorize exactly the same server handlers."""
    if session_id:
        session = _json(client.get(f"/integration/sessions/{session_id}"))
    else:
        fixture = _json(client.get("/fixtures"))
        sources = fixture.get("product_sources", {})
        product = next(
            (
                item["product_id"]
                for item in fixture["inventory"]
                if item["location_id"] == sources.get(item["product_id"], fixture.get("source_id"))
            ),
            None,
        )
        if product is None:
            raise RuntimeError("No product at source; explicitly prepare a fresh test first")
        identity = "demo-" + uuid4().hex
        session = _json(
            client.post(
                "/v1/wms/tasks",
                json={
                    "request_id": identity,
                    "request": {
                        "order_id": identity,
                        "lines": [
                            {
                                "order_line_id": "line-1",
                                "product_id": product,
                                "source_id": sources.get(product, fixture.get("source_id")),
                                "destination_id": fixture["destination_id"],
                            }
                        ],
                    },
                    "fault": SCENARIOS[scenario],
                    "mode": "guided",
                },
            )
        )
    retries: dict[int, int] = {}
    deadline = time.monotonic() + 300
    for _ in range(100):
        identity = session["session_id"]
        if session["status"] == "COMPLETED":
            break
        if session["status"] == "EXECUTING_STAGE":
            if time.monotonic() >= deadline:
                raise RuntimeError(
                    "Stage remains in progress; inspect original session before recovery"
                )
            time.sleep(0.25)
            session = _json(client.get(f"/integration/sessions/{identity}"))
            continue
        if session["status"] in {"UNKNOWN_OUTCOME", "REQUIRES_INTERVENTION"}:
            session = _json(
                client.post(
                    f"/integration/sessions/{identity}/reconcile",
                    json={
                        "request_id": uuid4().hex,
                        "expected_revision": session["revision"],
                        "fault": None,
                    },
                )
            )
            if session["status"] in {"UNKNOWN_OUTCOME", "REQUIRES_INTERVENTION"}:
                break
            continue
        stage = session["current_stage"]
        if stage in {15, 16} and not authorize_robot:
            break
        if session["status"] == "RETRYABLE_FAILURE":
            retries[stage] = retries.get(stage, 0) + 1
            if retries[stage] > 1:
                raise RuntimeError(f"Stage {stage} remains unavailable; original session retained")
        if not session.get("pending_authorization"):
            break
        session = _json(
            client.post(
                f"/integration/sessions/{identity}/authorize",
                json={
                    "request_id": uuid4().hex,
                    "expected_revision": session["revision"],
                    "stage": stage,
                    "decision": "approve",
                },
            )
        )
    evidence = (
        _json(client.get(f"/jobs/{session['job_id']}/evidence")) if session.get("job_id") else None
    )
    if session["status"] == "COMPLETED":
        assert evidence is not None
        expected = 0 if session["fault"] == "DROP_ACK_BEFORE_EFFECT" else 1
        if evidence["journal"]["effect_count"] != expected:
            raise RuntimeError("Persisted effect count does not match the demonstrated scenario")
        if evidence["command"]["command_id"] != session["command_id"]:
            raise RuntimeError("Reconciliation changed the original command identity")
    return {"session": session, "evidence": evidence, "explicit_physical_consent": authorize_robot}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--scenario", choices=SCENARIOS, default="happy_path")
    parser.add_argument("--authorize-robot", action="store_true")
    parser.add_argument("--session-id", help="Resume this original persisted session")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with httpx.Client(base_url=args.url, timeout=180) as client:
        result = drive(
            client,
            scenario=args.scenario,
            authorize_robot=args.authorize_robot,
            session_id=args.session_id,
        )
    output = (
        args.output or Path("runs/integration-demos") / f"{result['session']['session_id']}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["session"]["status"], "evidence": str(output)}))


if __name__ == "__main__":
    main()
