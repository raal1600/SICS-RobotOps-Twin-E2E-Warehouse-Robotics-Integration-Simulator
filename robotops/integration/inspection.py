"""Read-only engineering views over saved evidence and explicitly current references."""

import json
from typing import Any

from robotops.domain.models import utc_now
from robotops.integration.models import ExecutionSession, ExecutionStep
from robotops.integration.store import sanitize
from robotops.workflow.engine import Engine

# These are implementation relationships, never a claim that a function executed.
# Keys, files, and symbols are controlled by the application, not request paths.
COMPONENTS = {
    "workflow": (
        "Workflow",
        "robotops/workflow/engine.py",
        "Engine",
        "Coordinates observation, planning, execution and verification.",
    ),
    "storage": (
        "Workflow database",
        "robotops/workflow/store.py",
        "Store.prepare",
        "Saves command intent and the workflow transaction.",
    ),
    "guided-storage": (
        "Guided records",
        "robotops/integration/store.py",
        "IntegrationStore",
        "Stores authorizations, stage effects, inbox and outbox.",
    ),
    "planner": (
        "Planner",
        "robotops/brain/deterministic.py",
        "DeterministicBrain.plan",
        "Builds an action plan from the observation and requested destination.",
    ),
    "validator": (
        "Plan checks",
        "robotops/brain/validation.py",
        "ActionValidator.validate",
        "Checks whether the proposed plan can be accepted.",
    ),
    "tools": (
        "Tool selection",
        "robotops/robotics/selector.py",
        "select_tool",
        "Compares tool candidates for robot profiles that use tool selection.",
    ),
    "trajectory": (
        "Path checks",
        "robotops/robotics/trajectory.py",
        "validate_trajectory",
        "Checks planned motion for profiles that include a trajectory.",
    ),
    "observation": (
        "Observation model",
        "robotops/observation/model.py",
        "ObservationModel.observe",
        "Produces the simulated observation used by the workflow.",
    ),
    "quality": (
        "Observation quality",
        "robotops/observation/quality.py",
        "quality",
        "Checks freshness, confidence and position uncertainty.",
    ),
    "gateway": (
        "Robot gateway",
        "robotops/robot_gateway/gateway.py",
        "RobotGateway",
        "Sends a command or queries the retained result.",
    ),
    "synthetic": (
        "Synthetic cell",
        "robotops/cell/runtime.py",
        "SyntheticRuntime.apply",
        "Reference implementation for synthetic robot execution.",
    ),
    "blender": (
        "Blender cell",
        "robotops/blender/adapter.py",
        "BlenderRuntime.apply",
        "Reference implementation for recorded Blender execution.",
    ),
    "cell-checks": (
        "Robot execution checks",
        "robotops/cell/hkm_execution.py",
        "validate_execution",
        "Rechecks the robot profile at the effect boundary.",
    ),
    "verification": (
        "Result verification",
        "robotops/verification/verifier.py",
        "Verifier.verify",
        "Compares the retained receipt with a fresh observation.",
    ),
    "transport": (
        "Lab protocol bridge",
        "robotops/lab/transport.py",
        "LabBridge",
        "Connects the guided workflow to lab services.",
    ),
    "delivery": (
        "Broker delivery",
        "robotops/lab/transport.py",
        "EdgeAdapter.consume_one",
        "Commits the durable inbox before acknowledging delivery.",
    ),
    "edge-rpc": (
        "Edge HTTP client",
        "robotops/lab/edge_rpc.py",
        "EdgeRPC.call",
        "Calls the separate edge process over HTTP.",
    ),
    "edge": (
        "Edge process",
        "robotops/lab/edge.py",
        "EdgeControl.call",
        "Owns the OPC UA client and checks the durable inbox.",
    ),
    "opc-client": (
        "OPC UA client",
        "robotops/lab/opcua.py",
        "OPCClient._call",
        "Browses, subscribes and invokes controller methods.",
    ),
    "plc": (
        "Virtual PLC server",
        "robotops/lab/opcua.py",
        "VirtualPLC.start",
        "Defines the Python controller's OPC UA variables and methods.",
    ),
    "plc-journal": (
        "PLC command journal",
        "robotops/lab/journal.py",
        "PLCJournal",
        "Retains command identity, execution claims, results and acknowledgements.",
    ),
    "postgres": (
        "PostgreSQL transactions",
        "robotops/lab/postgres.py",
        "PostgreSQLStore",
        "Implements workflow storage with PostgreSQL transactions.",
    ),
    "wms": (
        "WMS service",
        "robotops/lab/business.py",
        "create_app",
        "Handles the simulated business acknowledgement over real HTTP.",
    ),
}


def code_catalog(session: ExecutionSession, step: ExecutionStep) -> list[dict[str, str]]:
    keys = ["workflow", "guided-storage"]
    stage = step.stage
    if stage >= 4:
        keys += ["storage"]
    if stage in {5, 6, 7, 18, 19}:
        keys += ["observation", "quality"]
    if stage in {6, 7, 8, 14, 16}:
        keys += ["planner", "validator", "tools", "trajectory"]
    if stage in {12, 13, 14, 15, 16, 17, 18, 19}:
        keys += ["gateway", "synthetic", "blender", "cell-checks"]
    if stage in {17, 18, 19, 20, 21}:
        keys += ["verification"]
    if session.profile == "lab":
        keys += ["postgres"]
        if stage in {9, 10, 11}:
            keys += ["transport", "delivery"]
        if 12 <= stage <= 17:
            keys += ["transport", "edge-rpc", "edge", "opc-client", "plc", "plc-journal"]
        if stage in {20, 21}:
            keys += ["transport", "wms"]
    return [
        {
            "key": "entry",
            "label": "Saved stage entry point",
            "path": step.source.path,
            "symbol": step.source.symbol,
            "role": "The source reference saved with this stage.",
        },
        *[
            {
                "key": key,
                "label": COMPONENTS[key][0],
                "path": COMPONENTS[key][1],
                "symbol": COMPONENTS[key][2],
                "role": COMPONENTS[key][3],
            }
            for key in dict.fromkeys(keys)
        ],
    ]


def facts(value: Any, path: str = "output") -> list[dict[str, Any]]:
    """Keep exact field paths; never turn absence, false, or an empty array into success."""
    if isinstance(value, dict):
        return [fact for key, item in value.items() for fact in facts(item, f"{path}.{key}")]
    if isinstance(value, list) and any(isinstance(item, (list, dict)) for item in value):
        return [
            fact for index, item in enumerate(value) for fact in facts(item, f"{path}[{index}]")
        ]
    return [{"field": path, "value": value}]


def _ids(value: Any) -> set[str]:
    if isinstance(value, dict):
        direct = {v for k, v in value.items() if k.endswith("_id") and isinstance(v, str)}
        return direct | set().union(*(_ids(v) for v in value.values()))
    if isinstance(value, (list, tuple)):
        return set().union(*(_ids(v) for v in value))
    return set()


def stored_records(
    engine: Engine, session: ExecutionSession, step: ExecutionStep
) -> dict[str, Any]:
    """Only resolve IDs owned by this saved session/job. Never contact a controller."""
    job_steps = [s for s in session.steps if s.job_id == step.job_id]
    refs = set(step.evidence_ids)
    for item in job_steps:
        refs.update(item.evidence_ids)
        refs.update(_ids(item.output))
        refs.update(_ids(item.input))
    records: list[dict[str, Any]] = []
    resolved: set[str] = set()

    def add(table: str, identity: str, body: Any, scope: str, kind: str = "") -> None:
        records.append(
            {
                "table": table,
                "id": identity,
                "kind": kind,
                "scope": scope,
                "body": body,
                "selected_step_reference": identity in step.evidence_ids,
            }
        )

    with engine.store.readonly_connect() as db:
        # Domain records are immutable. Resolve references as well as job-owned records
        # because observations do not carry job_id in all contract versions.
        for ident in sorted(refs):
            for row in db.execute("SELECT kind,id,body FROM records WHERE id=?", (ident,)):
                resolved.add(row[1])
                add("records", row[1], json.loads(row[2]), "Saved immutable record", row[0])
            effect = db.execute(
                "SELECT kind,body FROM integration_effects WHERE id=?", (ident,)
            ).fetchone()
            if effect:
                resolved.add(ident)
                add(
                    "integration_effects",
                    ident,
                    json.loads(effect[1]),
                    "Saved stage effect",
                    effect[0],
                )
        if step.job_id:
            for row in db.execute(
                "SELECT kind,id,body FROM records WHERE json_extract(body,'$.job_id')=?",
                (step.job_id,),
            ):
                if row[1] not in resolved:
                    resolved.add(row[1])
                    add("records", row[1], json.loads(row[2]), "Saved immutable record", row[0])
            row = db.execute("SELECT body FROM jobs WHERE id=?", (step.job_id,)).fetchone()
            if row:
                add("jobs", step.job_id, json.loads(row[0]), "Current row, read now")
        row = db.execute("SELECT body FROM orders WHERE id=?", (session.order_id,)).fetchone()
        if row:
            add("orders", session.order_id, json.loads(row[0]), "Current row, read now")
        for row in db.execute(
            "SELECT id,body FROM authorization_decisions WHERE session_id=? ORDER BY id",
            (session.session_id,),
        ):
            body = json.loads(row[1])
            if body.get("expected_revision") == step.revision - 1 or (
                body.get("stage") == step.stage
                and body.get("expected_revision", step.revision) < step.revision
            ):
                add(
                    "authorization_decisions",
                    row[0],
                    body,
                    "Saved authorization (check revision and timestamp)",
                )
        command = step.command_id
        if command:
            transport_queries = {
                "integration_outbox": "SELECT id,payload_hash,body,state FROM integration_outbox WHERE id=?",
                "integration_inbox": "SELECT id,payload_hash,body,deliveries FROM integration_inbox WHERE id=?",
                "lab_outbox": "SELECT command_id,payload_hash,payload,state,attempts,confirmed_at FROM lab_outbox WHERE command_id=?",
                "lab_inbox": "SELECT command_id,payload_hash,payload,deliveries,redelivered,ack_sent,received_at FROM lab_inbox WHERE command_id=?",
            }
            for table, columns in [
                ("integration_outbox", ("id", "payload_hash", "body", "state")),
                ("integration_inbox", ("id", "payload_hash", "body", "deliveries")),
            ]:
                row = db.execute(transport_queries[table], (command,)).fetchone()
                if row:
                    body = {name: row[i] for i, name in enumerate(columns)}
                    body["body"] = json.loads(body["body"])
                    add(table, command, body, "Current row, read now")
            if session.profile == "lab":
                for table, lab_columns in [
                    (
                        "lab_outbox",
                        (
                            "command_id",
                            "payload_hash",
                            "payload",
                            "state",
                            "attempts",
                            "confirmed_at",
                        ),
                    ),
                    (
                        "lab_inbox",
                        (
                            "command_id",
                            "payload_hash",
                            "payload",
                            "deliveries",
                            "redelivered",
                            "ack_sent",
                            "received_at",
                        ),
                    ),
                ]:
                    row = db.execute(transport_queries[table], (command,)).fetchone()
                    if row:
                        body = {name: row[i] for i, name in enumerate(lab_columns)}
                        body["payload"] = json.loads(body["payload"])
                        add(table, command, body, "Current row, read now")
                events = db.execute(
                    "SELECT sequence,body FROM lab_protocol_events WHERE command_id=? ORDER BY sequence LIMIT 301",
                    (command,),
                ).fetchall()
                for row in events[:300]:
                    add(
                        "lab_protocol_events",
                        str(row[0]),
                        json.loads(row[1]),
                        "Saved protocol notification; may be later than selected step",
                    )
            else:
                events = []
        else:
            events = []
    return {
        "items": records,
        "unresolved_selected_ids": sorted(set(step.evidence_ids) - resolved),
        "protocol_events_truncated": len(events) > 300,
        "scope": "Linked records for the selected job, including records saved after this step. Current rows are labelled separately. PLC database files and motion files are not copied; saved controller responses remain in Protocol and Raw JSON.",
    }


def inspect_step(engine: Engine, session: ExecutionSession, step: ExecutionStep) -> dict[str, Any]:
    output_facts = facts(step.output)
    decision_names = {
        "valid",
        "checks",
        "reason",
        "verdict",
        "state",
        "workflow_state",
        "effect_permitted",
        "reconciliation_required",
        "selected_tool_id",
        "safety_rated",
        "ordinary_operational_checks",
        "rechecked_by_runtime_at_effect",
    }
    versions = [
        f
        for f in facts(step.model_dump(mode="json"), "step")
        if f["field"].endswith(
            (
                "_version",
                ".schema_version",
                ".seed",
                ".scene_epoch",
                ".cell_generation",
                ".payload_hash",
            )
        )
    ]
    related = [
        {
            "step_id": other.step_id,
            "stage": other.stage,
            "title": other.title,
            "status": other.status,
            "timestamp": other.timestamp.isoformat(),
            "relation": "Same command"
            if step.command_id and other.command_id == step.command_id
            else "Same job",
        }
        for other in session.steps
        if other.step_id != step.step_id
        and (
            (step.command_id and other.command_id == step.command_id)
            or (step.job_id and other.job_id == step.job_id)
        )
    ]
    return dict(
        sanitize(
            {
                "format": "robotops-step-inspection-v1",
                "session_id": session.session_id,
                "step_id": step.step_id,
                "job_id": step.job_id,
                "command_id": step.command_id,
                "session_revision": session.revision,
                "read_at": utc_now().isoformat(),
                "source_catalog": code_catalog(session, step),
                "source_scope": "Related current implementation, not a recorded call trace. Profile-specific alternatives may not have run. The PLC is a Python simulation; no vendor ladder or Structured Text program is supplied.",
                "protocol": {
                    "classification": step.classification,
                    "protocol": step.protocol,
                    "scope": "Saved structured adapter evidence, not a packet capture. Fields absent from this record (such as exact request arguments or node IDs) are unavailable.",
                    "facts": facts(step.wire, "wire"),
                    "input": step.input,
                },
                "records": stored_records(engine, session, step),
                "decisions": {
                    "scope": "Recorded results and inputs only. A list of check names is not an individual pass/fail report. Current code and settings do not establish which historical branches ran.",
                    "rule": step.invariant,
                    "recovery": step.failure_semantics,
                    "facts": [
                        f
                        for f in output_facts
                        if f["field"].rsplit(".", 1)[-1] in decision_names
                        or ".tool_selection." in f["field"]
                    ],
                    "input": step.input,
                    "proofs": [
                        p
                        for p in session.workbench.get("proofs", [])
                        if p.get("step_id") == step.step_id
                    ],
                },
                "run": {
                    "recorded": {
                        "session_id": session.session_id,
                        "request_id": session.request_id,
                        "order_id": session.order_id,
                        "job_id": step.job_id,
                        "command_id": step.command_id,
                        "correlation_id": step.correlation_id,
                        "profile": session.profile,
                        "fault": session.fault,
                        "step_timestamp": step.timestamp.isoformat(),
                        "step_revision": step.revision,
                    },
                    "recorded_versions": versions,
                    "current_reference": {
                        "scope": "Current application settings, not a saved configuration snapshot for this run.",
                        "runtime": type(engine.runtime).__name__,
                        "settings": engine.settings.model_dump(mode="json"),
                    },
                    "missing": [
                        "An immutable full source/build snapshot for this run.",
                        "A complete execution-time configuration snapshot.",
                        "Physical hardware and safety certification evidence; this is a simulated cell.",
                    ],
                },
                "related_steps": related,
            }
        )
    )
