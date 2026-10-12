"""Read-only explanations of persisted evidence, never execution decisions.

Every proof points to an ExecutionStep and an exact output field. A completed
handler, session position, or animation alone cannot establish a boundary.
"""

from typing import Any, cast

from robotops.integration.models import ExecutionSession, ExecutionStep
from robotops.integration.store import sanitize

ACTIONS = (
    "Create business demand",
    "Create warehouse task",
    "Accept task through API",
    "Commit order and job",
    "Capture fresh observation",
    "Create action plan",
    "Validate action plan",
    "Save original robot command",
    "Inspect durable outbox",
    "Publish command",
    "Process edge delivery",
    "Connect to controller",
    "Submit command to PLC",
    "Check controller preconditions",
    "AUTHORIZE ROBOT EXECUTION",
    "Execute authorized original command",
    "Read controller result",
    "Capture post-action observation",
    "Verify observed result",
    "Send WMS acknowledgement",
    "Complete ERP business record",
    "Save final correlated trace",
)

# Meaning and limitation are separate: these describe the recorded operation,
# not an assertion that its intended outcome succeeded.
STAGE_MEANING = (
    ("Business demand was saved.", "API acceptance, robot work or business completion."),
    ("A warehouse task was saved for the order.", "Durable workflow intake or robot execution."),
    ("The API validated the task request.", "A committed workflow or a physical result."),
    (
        "The order and its jobs were committed to the workflow database.",
        "Message publication or robot execution.",
    ),
    (
        "The observation model captured a view of the cell for planning.",
        "Physical ground truth or a completed pick.",
    ),
    (
        "The planner produced an action plan from the observation.",
        "Plan validity or permission to execute.",
    ),
    ("The plan passed the recorded validation checks.", "Certified safety or physical execution."),
    (
        "The original robot command and outbox intent were saved.",
        "Delivery, controller acceptance or execution.",
    ),
    (
        "The command's durable outbox entry was inspected or created.",
        "Broker publication or consumer processing.",
    ),
    (
        "The publication operation returned the recorded transport result.",
        "Edge processing, controller acceptance or execution.",
    ),
    (
        "The edge delivery operation recorded its inbox and acknowledgement result.",
        "Controller acceptance or robot execution.",
    ),
    (
        "The controller connection operation returned its recorded result.",
        "Command acceptance, robot readiness or execution.",
    ),
    (
        "The original command was submitted to the controller.",
        "Robot execution, observation or verification.",
    ),
    (
        "The application checked controller preconditions.",
        "Certified safety or permission to execute without consent.",
    ),
    (
        "Explicit permission for the original command was saved.",
        "Execution success or a certified safety function.",
    ),
    (
        "The authorized execution attempt returned its recorded result.",
        "A verified physical outcome or WMS acknowledgement.",
    ),
    (
        "The original command journal was queried for a controller result.",
        "Fresh observation, verification or business completion.",
    ),
    (
        "The observation model captured a post-action cell report.",
        "Freshness, sufficient confidence or success until assessed by verification.",
    ),
    (
        "The verifier recorded its assessment of the original command and observation.",
        "WMS acknowledgement or ERP completion.",
    ),
    (
        "The WMS acknowledgement operation returned its recorded result.",
        "ERP completion or that a failed pick succeeded.",
    ),
    (
        "The ERP business outcome was saved after checking every job's acknowledgement.",
        "Production hardware validation or certified safety.",
    ),
    (
        "The final correlation summary was saved.",
        "Any missing boundary evidence; a complete trace is not proof of success.",
    ),
)

PERSISTENCE = {
    1: "integration_effects: ERP_DEMAND",
    2: "integration_effects: WMS_TASK",
    3: "integration_effects: API_VALIDATION",
    4: "orders, jobs and workflow events",
    5: "records: WorldObservation",
    6: "records: ActionPlan",
    8: "records: RobotCommand and its immutable outbox intent",
    9: "integration_outbox; lab_outbox when the lab adapter is used",
    10: "outbox state and the recorded publication result",
    11: "durable inbox and delivery count",
    15: "integration_effects: PHYSICAL_AUTHORIZATION",
    16: "dispatch intent and available controller receipt; runtime journal is separate",
    17: "recorded query of the original controller journal",
    18: "records: WorldObservation",
    19: "records: VerificationResult; reconciliation evidence when this is a recovery attempt",
    20: "integration_effects: WMS_ACKNOWLEDGEMENT on successful acknowledgement",
    21: "integration_effects: ERP_BUSINESS_STATUS and order business marker",
    22: "integration_effects: TRACE_SUMMARY",
}


def _recovery(step: ExecutionStep) -> str:
    if step.output.get("next_action"):
        return str(step.output["next_action"])
    if step.stage == 20:
        return "Retry only the WMS acknowledgement when permitted. No robot command is sent."
    if 15 <= step.stage <= 19:
        return "If the outcome is uncertain, reconcile the original command. Do not retry the pick."
    if step.stage == 21:
        return "Check every job's verification and saved WMS acknowledgement before business completion."
    if step.stage in {5, 6, 7}:
        return (
            "Resolve the planning or observation issue. Follow the backend's permitted next action."
        )
    return "Inspect this boundary's recorded result and use only the action permitted by Execution now."


def explain(step: ExecutionStep) -> dict[str, Any]:
    meaning, limitation = STAGE_MEANING[step.stage - 1]
    result = step.output
    if step.status == "FAILED":
        meaning = "This attempt did not complete: " + str(result.get("error", step.summary))
    elif step.component == "reconciliation":
        meaning = "The original command was reconciled without sending a replacement command."
    elif step.status == "RECOVERED_NO_DISPATCH":
        meaning = (
            "Recovery found no committed dispatch intent; fresh physical permission is required."
        )
    verdict = result.get("verification", result).get("verdict")
    if verdict:
        meaning += " " + {
            "VERIFIED_SUCCESS": "Verification established success.",
            "VERIFIED_FAILURE": "Verification established failure.",
            "INCONCLUSIVE": "The physical outcome remains unproven.",
        }.get(verdict, "The recorded verdict is " + str(verdict) + ".")
        if step.state_after in {"UNKNOWN_OUTCOME", "REQUIRES_INTERVENTION"}:
            meaning = "The verifier saved an assessment, but original-command recovery has not resolved the workflow outcome."
    receipt = result.get("receipt")
    if step.stage in {16, 17}:
        meaning += (
            " Controller result: "
            + (receipt.get("status", "unavailable") if receipt else "unavailable")
            + "."
        )
    claims = []
    for key, label, stages, _ in BOUNDARIES:
        if step.stage not in stages or (
            step.stage == 19 and key != "verification" and step.component != "reconciliation"
        ):
            continue
        state, fact, field = _result(key, step)
        claims.append(f"{label}: {fact} [{state}; {field}]")
    return {
        "what": meaning,
        "changed": f"{step.state_before} → {step.state_after}"
        if step.state_before != step.state_after
        else f"No workflow state change ({step.state_after}).",
        "saved": "records: ExecutionStep; execution_sessions: persisted history. "
        + (
            "This failed attempt does not prove the intended persistence effect."
            if step.status == "FAILED"
            else "Operation evidence: "
            + PERSISTENCE.get(step.stage, "the recorded controller or validation result")
            + "."
        ),
        "proves": "\n".join(claims)
        if claims
        else "The saved operation result below, scoped to this attempt. COMPLETED means the handler finished; it does not establish later outcomes.",
        "does_not_prove": limitation,
        "recovery": _recovery(step),
    }


BOUNDARIES = (
    ("intent", "Business intent", (1,), "Durable workflow intake or robot work."),
    ("durable", "Durable workflow", (4,), "Broker publication or robot execution."),
    ("broker", "Broker publication", (10,), "Consumer processing or controller acceptance."),
    ("edge", "Edge processing", (11,), "Controller acceptance or execution."),
    ("controller", "Controller acceptance", (13,), "Execution, observation or verification."),
    (
        "execution",
        "Execution result",
        (16, 17, 19),
        "Sensor verification or business acknowledgement.",
    ),
    (
        "observation",
        "Post-action observation",
        (18, 19),
        "Freshness, confidence or success until assessed by verification.",
    ),
    ("verification", "Verification", (19,), "WMS acknowledgement or ERP completion."),
    (
        "wms",
        "WMS acknowledgement",
        (20,),
        "ERP completion or that a failed physical result succeeded.",
    ),
    ("erp", "ERP completion", (21,), "Production hardware validation or certified safety."),
)


def _result(key: str, step: ExecutionStep) -> tuple[str, str, str]:
    """Return evidence state, explanatory fact, and exact field path."""
    data = step.output
    if step.status == "FAILED":
        if key == "execution":
            return (
                "unproven",
                "The execution request failed to establish an outcome. Do not retry the pick. "
                + str(data.get("error", step.summary)),
                "output.error",
            )
        return "failed", str(data.get("error", step.summary)), "output.error"
    if key == "intent" and data.get("demand_id") and data.get("status") == "DEMAND_CREATED":
        return "established", "Business demand saved.", "output.demand_id"
    if key == "durable" and data.get("transaction_committed") is True:
        return "established", "Order and jobs committed.", "output.transaction_committed"
    if key == "broker":
        if data.get("publisher_confirm") is True:
            return (
                "established",
                "Broker publisher confirmation recorded.",
                "output.publisher_confirm",
            )
        if data.get("amqp_used") is False:
            return (
                "simulated",
                "In-process handoff only; no broker confirmation.",
                "output.amqp_used",
            )
    if key == "edge" and (
        data.get("durable_inbox_committed") is True or data.get("durable_inbox") is True
    ):
        return (
            "established",
            "Durable edge inbox recorded; acknowledgement details remain in Protocol.",
            "output",
        )
    if key == "controller" and (data.get("accepted") is True or data.get("state") == "ACCEPTED"):
        return "established", "Original command accepted; no execution implied.", "output"
    if key == "execution":
        receipt = data.get("receipt") or {}
        if receipt.get("command_id") == step.command_id and receipt.get("status") in {
            "SUCCEEDED",
            "FAILED",
            "REJECTED",
        }:
            success = receipt["status"] == "SUCCEEDED"
            return (
                "established" if success else "failed",
                "Controller result: " + receipt["status"],
                "output.receipt",
            )
    if key == "observation":
        observation = data.get("observation", data)
        if observation.get("observation_id") and observation.get("captured_at"):
            return (
                "established",
                "Observation captured; see Verification for its assessment.",
                "output.observation" if "observation" in data else "output",
            )
    if key == "verification":
        verification = data.get("verification", data)
        if verification.get("command_id") == step.command_id and verification.get(
            "verification_id"
        ):
            verdict = verification.get("verdict")
            if verdict in {"VERIFIED_SUCCESS", "VERIFIED_FAILURE", "INCONCLUSIVE"}:
                if step.state_after in {"UNKNOWN_OUTCOME", "REQUIRES_INTERVENTION"}:
                    return (
                        "unproven",
                        f"Recorded assessment: {verdict}. Original-command recovery has not resolved the workflow outcome.",
                        "output.verification" if "verification" in data else "output",
                    )
                state = {
                    "VERIFIED_SUCCESS": "established",
                    "VERIFIED_FAILURE": "failed",
                    "INCONCLUSIVE": "unproven",
                }[verdict]
                return (
                    state,
                    f"{verdict}: {verification.get('reason', '')}",
                    "output.verification" if "verification" in data else "output",
                )
    if (
        key == "wms"
        and data.get("wms_acknowledged") is True
        and data.get("command_id") == step.command_id
    ):
        return (
            "established",
            "WMS acknowledged the verified outcome: " + str(data.get("verified_outcome")),
            "output.wms_acknowledged",
        )
    if (
        key == "erp"
        and data.get("business_status") in {"COMPLETED", "FAILED"}
        and data.get("wms_acknowledgement_ids")
    ):
        success = data["business_status"] == "COMPLETED"
        return (
            "established" if success else "failed",
            "ERP business result: " + data["business_status"],
            "output.business_status",
        )
    return "unproven", "The saved result does not establish this boundary.", "output"


def project(session: ExecutionSession) -> dict[str, Any]:
    proofs = []
    for key, label, stages, limitation in BOUNDARIES:
        candidates = [
            s
            for s in session.steps
            if s.stage in stages
            and (key in {"intent", "durable", "erp"} or s.job_id == session.job_id)
            and (s.stage != 19 or key == "verification" or s.component == "reconciliation")
        ]
        step = candidates[-1] if candidates else None
        state, fact, field = (
            _result(key, step) if step else ("unproven", "No supporting result recorded yet.", "")
        )
        proofs.append(
            {
                "key": key,
                "label": label,
                "state": state,
                "fact": fact,
                "does_not_prove": limitation,
                "step_id": step.step_id if step else None,
                "field": field,
                "evidence_ids": list(step.evidence_ids) if step else [],
                "classification": step.classification if step else "UNAVAILABLE",
            }
        )
    status = {
        "WAITING_AUTHORIZATION": "Waiting for your approval",
        "EXECUTING_STAGE": "Stage in progress or awaiting recovery",
        "UNKNOWN_OUTCOME": "Robot outcome not yet proven",
        "REQUIRES_INTERVENTION": "Robot outcome not yet proven",
        "RETRYABLE_FAILURE": "This boundary needs another attempt",
        "FAILED": "Execution stopped",
        "COMPLETED": "Journey finished — review the recorded outcomes",
    }.get(session.status, session.status)
    if session.current_stage == 15 and session.pending_authorization:
        status = "Waiting for robot authorization"
    if session.current_stage == 20 and session.status == "RETRYABLE_FAILURE":
        status = "Business acknowledgement failed"
    return cast(
        dict[str, Any],
        sanitize(
            {
                "version": 1,
                "status": status,
                "proof_scope_job_id": session.job_id,
                "proofs": proofs,
                "stages": {s.step_id: explain(s) for s in session.steps},
            }
        ),
    )
