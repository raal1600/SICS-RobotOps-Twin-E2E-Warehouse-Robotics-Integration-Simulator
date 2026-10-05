"""One authorization performs one persisted bounded integration operation.

Local mode is deliberately an in-process transport model. No trace claims an AMQP
or OPC UA wire operation unless the configured LabBridge actually performs one.
"""

from pathlib import Path
from time import monotonic
from typing import Any

from robotops.cell.runtime import SyntheticRuntime
from robotops.domain.models import (
    ActionPlan,
    CommandReceipt,
    Fault,
    JobState,
    OrderRequest,
    RobotCommand,
    VerificationResult,
    WorldObservation,
    new_id,
    stable_id,
    utc_now,
)
from robotops.faults.injection import OBSERVATION_FAULTS
from robotops.integration.models import (
    AuthorizeStage,
    CreateSession,
    ExecutionSession,
    ExecutionStep,
    PendingAuthorization,
    ProtocolTrace,
    SourceReference,
)
from robotops.integration.store import IntegrationStore, sanitize
from robotops.workflow.engine import Engine
from robotops.workflow.store import Claim, Conflict, digest

# title, component, protocol, classification, source path, source symbol, invariant
STAGES = (
    (
        "ERP demand created",
        "erp",
        "SQL",
        "SIMULATED SYSTEM",
        "robotops/integration/engine.py",
        "GuidedEngine._execute",
        "Business intent does not authorize a robot.",
    ),
    (
        "WMS task created",
        "wms",
        "SQL",
        "SIMULATED SYSTEM",
        "robotops/integration/engine.py",
        "GuidedEngine._execute",
        "SKU/source/destination must identify one material flow.",
    ),
    (
        "API intake",
        "api",
        "REST",
        "REAL CODE",
        "robotops/integration/engine.py",
        "GuidedEngine._validate",
        "Versioned Pydantic input and idempotency precede durable intake.",
    ),
    (
        "Durable intake",
        "database",
        "SQL",
        "REAL CODE",
        "robotops/workflow/store.py",
        "Store.intake",
        "Database commit is not physical execution.",
    ),
    (
        "Fresh observation",
        "sensor",
        "sensor",
        "SYNTHETIC SENSOR",
        "robotops/workflow/engine.py",
        "Engine.stage_observe",
        "WorldObservation is measured evidence, distinct from WorldState.",
    ),
    (
        "Planning",
        "planner",
        "Python",
        "REAL CODE",
        "robotops/workflow/engine.py",
        "Engine.stage_plan",
        "Planner has no actuator capability.",
    ),
    (
        "Plan validation",
        "validator",
        "Python",
        "REAL CODE",
        "robotops/workflow/engine.py",
        "Engine.stage_validate",
        "Planner output is not trusted without semantic validation.",
    ),
    (
        "Immutable RobotCommand persisted",
        "database",
        "SQL",
        "REAL CODE",
        "robotops/workflow/store.py",
        "Store.prepare",
        "Stable command identity and payload hash precede dispatch.",
    ),
    (
        "Transactional outbox",
        "database",
        "SQL",
        "REAL CODE",
        "robotops/integration/store.py",
        "IntegrationStore.enqueue",
        "Command and outbox commit atomically before network side effects.",
    ),
    (
        "Dispatch publication",
        "broker",
        "LOCAL",
        "SIMULATED SYSTEM",
        "robotops/integration/store.py",
        "IntegrationStore.publish_local",
        "Publisher confirmation is distinct from consumer acknowledgement.",
    ),
    (
        "Edge delivery",
        "edge",
        "LOCAL",
        "SIMULATED SYSTEM",
        "robotops/integration/store.py",
        "IntegrationStore.deliver_local",
        "Persist inbox identity before acknowledging delivery.",
    ),
    (
        "Controller session",
        "opcua",
        "LOCAL",
        "SIMULATED SYSTEM",
        "robotops/integration/engine.py",
        "GuidedEngine._execute",
        "Local mode performs no OPC UA network operation.",
    ),
    (
        "PLC SubmitJob",
        "plc",
        "LOCAL",
        "SIMULATED SYSTEM",
        "robotops/integration/engine.py",
        "GuidedEngine._execute",
        "Acceptance is not execution; command identity is immutable.",
    ),
    (
        "PLC operational preconditions",
        "plc",
        "controller",
        "SIMULATED SYSTEM",
        "robotops/integration/engine.py",
        "GuidedEngine._execute",
        "Operational checks are not safety-rated functions.",
    ),
    (
        "READY FOR PHYSICAL EXECUTION",
        "operator",
        "REST",
        "REAL CODE",
        "robotops/integration/engine.py",
        "GuidedEngine._execute",
        "Explicit authorization must precede irreversible simulated physical effect.",
    ),
    (
        "Physical execution",
        "robot",
        "controller",
        "SIMULATED ROBOT",
        "robotops/workflow/engine.py",
        "Engine.stage_dispatch",
        "Lost acknowledgement never permits a blind physical retry.",
    ),
    (
        "Controller result",
        "controller",
        "controller",
        "SIMULATED SYSTEM",
        "robotops/robot_gateway/gateway.py",
        "RobotGateway.query",
        "Controller success is not sensor verification or WMS acknowledgement.",
    ),
    (
        "Fresh post-execution observation",
        "sensor",
        "sensor",
        "SYNTHETIC SENSOR",
        "robotops/workflow/engine.py",
        "Engine._observe",
        "Verification uses fresh evidence, not the presentation replay.",
    ),
    (
        "Verification",
        "verifier",
        "Python",
        "REAL CODE",
        "robotops/verification/verifier.py",
        "Verifier.verify",
        "Inconclusive evidence must never produce business success.",
    ),
    (
        "WMS reconciliation",
        "wms",
        "SQL",
        "SIMULATED SYSTEM",
        "robotops/integration/engine.py",
        "GuidedEngine._execute",
        "WMS retries never execute robot motion.",
    ),
    (
        "ERP business completion",
        "erp",
        "SQL",
        "SIMULATED SYSTEM",
        "robotops/integration/store.py",
        "IntegrationStore.complete_business",
        "Business completion requires acknowledgement of verified outcome.",
    ),
    (
        "Final correlated trace",
        "trace",
        "SQL",
        "REAL CODE",
        "robotops/integration/engine.py",
        "GuidedEngine._execute",
        "Each evidence ID refers to persisted backend work.",
    ),
)
GATES = {3, 10, 13, 15}
FAULTS = {item.value for item in Fault} | {
    "DUPLICATE_DELIVERY",
    "BROKER_TRANSIENT",
    "EDGE_TRANSIENT",
    "OPC_UA_DISCONNECT",
    "PLC_RESTART",
    "WMS_UNAVAILABLE",
}


class GuidedEngine:
    def __init__(self, workflow: Engine):
        self.workflow = workflow
        self.store = IntegrationStore(workflow.store)
        self.lab: Any = getattr(workflow, "lab", None)

    def present(self, session: ExecutionSession) -> ExecutionSession:
        pending = None
        if session.status in {"WAITING_AUTHORIZATION", "RETRYABLE_FAILURE"}:
            stage = session.current_stage
            pending = PendingAuthorization(
                stage=stage,
                title=STAGES[stage - 1][0],
                label="AUTHORIZE ROBOT EXECUTION"
                if stage == 15
                else "Authorize boundary"
                if stage in GATES
                else "Continue",
                expected_revision=session.revision,
                mandatory=stage in GATES,
            )
        return session.model_copy(update={"pending_authorization": pending})

    def get(self, session_id: str) -> ExecutionSession:
        return self.present(self.store.get(session_id))

    def create(self, request: CreateSession) -> ExecutionSession:
        if request.fault is not None and request.fault not in FAULTS:
            raise Conflict("UNKNOWN_FAILURE_SCENARIO")
        session = self.store.create(request)
        return self.present(session)

    def _validate(self, request: OrderRequest) -> None:
        OrderRequest.model_validate(request.model_dump())
        products = {p.product_id for p in self.workflow.settings.products}
        for line in request.lines:
            if line.product_id not in products:
                raise ValueError("PRODUCT_NOT_IN_FIXTURE")
            if line.source_id != self.workflow.settings.source_for(line.product_id):
                raise ValueError("PRODUCT_SOURCE_MISMATCH")
            if line.destination_id != self.workflow.settings.destination_id:
                raise ValueError("DESTINATION_MISMATCH")

    def _claim(self, session: ExecutionSession) -> Claim:
        if session.job_id is None:
            raise Conflict("SESSION_JOB_REQUIRED")
        lease_seconds = self.workflow.settings.lease_seconds
        if session.current_stage == 16:
            network_budget = float(self.lab.config.timeout) * 2 if self.lab else 0
            lease_seconds = max(
                lease_seconds, self.workflow.settings.runtime_timeout_seconds + network_budget + 15
            )
        claim = self.workflow.store.claim(session.job_id, new_id(), lease_seconds, reconcile=True)
        if claim is None:
            raise Conflict("JOB_OWNED_OR_CELL_QUARANTINED")
        return claim

    def _execute(self, session: ExecutionSession, context: dict[str, Any]) -> dict[str, Any]:
        stage = session.current_stage
        ws = self.workflow.store
        fault = Fault(session.fault) if session.fault in {item.value for item in Fault} else None
        ident = stable_id(session.session_id, f"stage:{stage}:{session.job_id}")
        if stage == 1:
            return self.store.effect(
                ident,
                "ERP_DEMAND",
                {
                    "order_id": session.order_id,
                    "demand_id": ident,
                    "lines": [x.model_dump(mode="json") for x in session.request.lines],
                    "status": "DEMAND_CREATED",
                    "system": "synthetic ERP",
                },
            )
        if stage == 2:
            return self.store.effect(
                ident,
                "WMS_TASK",
                {
                    "task_id": ident,
                    "order_id": session.order_id,
                    "request": session.request.model_dump(mode="json"),
                    "status": "TASK_CREATED",
                    "system": "synthetic WMS",
                },
            )
        if stage == 3:
            self._validate(session.request)
            return self.store.effect(
                ident,
                "API_VALIDATION",
                {
                    "schema_version": "1.0",
                    "idempotency_key": session.request_id,
                    "payload_hash": digest(session.request),
                    "accepted": True,
                    "method": "POST",
                    "path": "/v1/wms/tasks",
                },
            )
        if stage == 4:
            # Install execution-authority guard before any recoverable job exists.
            with ws.transaction() as db:
                for line in session.request.lines:
                    job_id = stable_id(session.order_id, line.order_line_id)
                    db.execute(
                        "INSERT OR IGNORE INTO meta VALUES (?,?)",
                        ("guided:" + job_id, session.session_id),
                    )
            order = ws.intake(
                session.request, "guided:" + session.request_id, validate=self._validate
            )
            context["job_ids"] = list(order.job_ids)
            context["job_index"] = 0
            job = ws.job(order.job_ids[0])
            temporary = session.model_copy(update={"job_id": job.job_id})
            claim = self._claim(temporary)
            try:
                job = self.workflow.stage_intake(job, claim)
                self.workflow._inject(job, fault)
            finally:
                ws.release(claim)
            return {
                "order": order.model_dump(mode="json"),
                "job": job.model_dump(mode="json"),
                "database": "PostgreSQL" if self.lab else "SQLite",
                "transaction_committed": True,
            }
        if session.job_id is None:
            raise Conflict("SESSION_JOB_REQUIRED")
        job = ws.job(session.job_id)
        command = ws.load(RobotCommand, job.command_id) if job.command_id else None
        if stage == 5:
            claim = self._claim(session)
            try:
                job = self.workflow.stage_intake(job, claim)
                observation = self.workflow.stage_observe(job, claim)
            finally:
                ws.release(claim)
            context["pre_observation_id"] = observation.observation_id
            return observation.model_dump(mode="json")
        if stage == 6:
            observation = ws.load(WorldObservation, context["pre_observation_id"])
            plan = self.workflow.stage_plan(job, observation, fault)
            context["plan_id"] = plan.action_plan_id
            return plan.model_dump(mode="json")
        if stage == 7:
            plan = self.workflow.stage_validate(
                job,
                ws.load(WorldObservation, context["pre_observation_id"]),
                ws.load(ActionPlan, context["plan_id"]),
            )
            context["validated"] = True
            return {"action_plan_id": plan.action_plan_id, "valid": True}
        if stage == 8:
            if not context.get("validated"):
                raise Conflict("PLAN_NOT_VALIDATED")
            recovering_command = job.command_id is not None
            claim = self._claim(session)
            try:
                # A command commit can precede a process crash/session checkpoint.
                # Recover that immutable intent; never replace it with a new plan.
                if job.command_id is not None:
                    if job.action_plan_id != context["plan_id"]:
                        raise Conflict("RECOVERED_COMMAND_PLAN_MISMATCH")
                    if job.state == JobState.PLANNING:
                        job = ws.transition(
                            job.job_id,
                            JobState.READY_TO_EXECUTE,
                            "COMMAND_COMMIT_RECOVERED",
                            claim=claim,
                        )
                else:
                    job = self.workflow.stage_command(
                        job, ws.load(ActionPlan, context["plan_id"]), claim
                    )
            finally:
                ws.release(claim)
            if job.command_id is None:
                raise Conflict("MISSING_DURABLE_COMMAND")
            command = ws.load(RobotCommand, job.command_id)
            return {
                "command": command.model_dump(mode="json"),
                "payload_hash": digest(command),
                "outbox_atomic_with_command": True,
                "recovered_existing_command": recovering_command,
            }
        if command is None:
            raise Conflict("MISSING_DURABLE_COMMAND")
        if stage == 9:
            result = self.store.enqueue(command.model_dump(mode="json"))
            if self.lab:
                result["lab_outbox"] = self.lab.enqueue(command.model_dump(mode="json"))
            return result
        if stage in {10, 11, 12}:
            fault_for_stage = {
                10: "BROKER_TRANSIENT",
                11: "EDGE_TRANSIENT",
                12: "OPC_UA_DISCONNECT",
            }
            key = f"fault_once_{stage}"
            if session.fault == fault_for_stage[stage] and not context.get(key):
                context[key] = True
                raise OSError(
                    fault_for_stage[stage] + ": bounded operation unavailable; safe retry"
                )
            if stage == 10:
                return (
                    dict(self.lab.publish(command.command_id))
                    if self.lab
                    else self.store.publish_local(command.command_id)
                )
            if stage == 11:
                result = (
                    dict(self.lab.edge_deliver(command.command_id))
                    if self.lab
                    else self.store.deliver_local(command.command_id)
                )
                if session.fault == "DUPLICATE_DELIVERY":
                    result["redelivery"] = (
                        self.lab.redeliver(command.command_id)
                        if self.lab
                        else self.store.deliver_local(command.command_id)
                    )
                return result
            if stage == 12:
                return (
                    dict(self.lab.opc_connect())
                    if self.lab
                    else self.store.effect(
                        ident,
                        "LOCAL_CONTROLLER_SESSION",
                        {
                            "connection": "in-process",
                            "opc_ua_network_used": False,
                            "classification": "SIMULATED SYSTEM",
                            "boot_id": self.workflow.runtime.world().scene_epoch,
                        },
                    )
                )
        if stage == 13:
            if self.lab:
                return dict(self.lab.submit(command.model_dump(mode="json")))
            return self.store.effect(
                stable_id(command.command_id, "accepted"),
                "PLC_ACCEPTANCE",
                {
                    "command_id": command.command_id,
                    "payload_hash": digest(command),
                    "accepted": True,
                    "state": "ACCEPTED",
                    "physical_effect": False,
                },
            )
        if stage == 14:
            world = self.workflow.runtime.world()
            rejection = SyntheticRuntime.rejection_reason(world, command, None)
            if rejection:
                raise Conflict(rejection)
            if self.lab:
                return dict(self.lab.preconditions(command.command_id))
            return self.store.effect(
                ident,
                "OPERATIONAL_PRECONDITIONS",
                {
                    "scene_epoch": world.scene_epoch,
                    "generation": world.cell.generation,
                    "cell_mode": world.cell.mode.value,
                    "payload_hash": digest(command),
                    "tool": command.required_tool_id,
                    "safety_rated": False,
                },
            )
        if stage == 15:
            context["physical_authorized"] = True
            return self.store.effect(
                ident,
                "PHYSICAL_AUTHORIZATION",
                {
                    "command_id": command.command_id,
                    "payload_hash": digest(command),
                    "authorized": True,
                    "safety_function": False,
                    "meaning": "Permission for irreversible simulated robot effect; not certified safety.",
                },
            )
        if stage == 16:
            if not context.get("physical_authorized"):
                raise Conflict("EXPLICIT_PHYSICAL_AUTHORIZATION_REQUIRED")
            claim = self._claim(session)
            try:

                def send_lab(intent: RobotCommand, runtime_fault: Fault | None) -> CommandReceipt:
                    def execute() -> dict[str, Any]:
                        return dict(
                            self.workflow.gateway.send(intent, runtime_fault).model_dump(
                                mode="json"
                            )
                        )

                    wire = self.lab.authorize_execute(intent.command_id, execute)
                    context["execution_wire"] = wire
                    return CommandReceipt.model_validate(wire)

                receipt = self.workflow.stage_dispatch(
                    job, claim, fault, sender=send_lab if self.lab else None
                )
            finally:
                ws.release(claim)
            context["receipt"] = receipt.model_dump(mode="json") if receipt else None
            context["dispatch_uncertain"] = receipt is None
            return {
                "command_id": command.command_id,
                "receipt": context["receipt"],
                "status": "UNKNOWN_OUTCOME" if receipt is None else receipt.status.value,
                "interface": "simulated controller interface",
                "playback_url": f"/jobs/{job.job_id}/playback",
            }
        if stage == 17:
            if session.fault == "PLC_RESTART":
                if not self.lab:
                    runtime = self.workflow.runtime
                    if not isinstance(runtime, SyntheticRuntime):
                        raise Conflict("LOCAL_RUNTIME_RESTART_UNSUPPORTED")
                    # Recreate the controller adapter from durable storage, without reset/apply.
                    replacement = type(runtime)(runtime.db.path, runtime.settings)
                    self.workflow.runtime = replacement
                    self.workflow.gateway.runtime = replacement
                context["controller_restart"] = (
                    self.lab.restart()
                    if self.lab
                    else self.store.effect(
                        ident,
                        "SIMULATED_CONTROLLER_RECONNECTION",
                        {
                            "classification": "SIMULATED SYSTEM",
                            "journal_retained": True,
                            "restart_model": "controller adapter reconstructed from durable journal; no operating-system process restart",
                            "scene_epoch": self.workflow.runtime.world().scene_epoch,
                        },
                    )
                )
            receipt = self.workflow.gateway.query(command)
            if self.lab:
                context["controller_wire"] = self.lab.status(command.command_id)
            context["receipt"] = receipt.model_dump(mode="json") if receipt else None
            if job.state == JobState.EXECUTING:
                claim = self._claim(session)
                try:
                    self.workflow.stage_result(job, claim)
                finally:
                    ws.release(claim)
            return {
                "command_id": command.command_id,
                "receipt": context["receipt"],
                "journal_query_only": True,
                "wire": context.get("controller_wire", {}),
                "restart": context.get("controller_restart"),
            }
        if stage == 18:
            observation = self.workflow._observe(
                job, fault if fault in OBSERVATION_FAULTS else None
            )
            context["post_observation_id"] = observation.observation_id
            return observation.model_dump(mode="json")
        if stage == 19:
            observation = ws.load(WorldObservation, context["post_observation_id"])
            receipt = (
                CommandReceipt.model_validate(context["receipt"])
                if context.get("receipt")
                else None
            )
            if job.state in {JobState.COMPLETED, JobState.FAILED}:
                # Verification and its terminal transition committed before the
                # interrupted session checkpoint. Reuse the actual saved verdict.
                results = ws.records_for_job(VerificationResult, job.job_id)
                if not results:
                    raise Conflict("TERMINAL_JOB_MISSING_VERIFICATION")
                verification = results[-1]
            elif job.state == JobState.UNKNOWN_OUTCOME:
                verification = self.workflow.verifier.verify(command, observation, receipt)
                ws.save(verification.verification_id, verification)
            else:
                claim = self._claim(session)
                try:
                    verification = self.workflow.stage_verify(
                        job, command, observation, receipt, claim
                    )
                finally:
                    ws.release(claim)
            context["verification"] = verification.model_dump(mode="json")
            return {
                **verification.model_dump(mode="json"),
                "workflow_state": ws.job(job.job_id).state.value,
                "reconciliation_required": ws.job(job.job_id).state == JobState.UNKNOWN_OUTCOME,
                "recovered_verification": job.state in {JobState.COMPLETED, JobState.FAILED},
            }
        if stage == 20:
            if job.state not in {JobState.COMPLETED, JobState.FAILED}:
                raise Conflict("VERIFIED_OUTCOME_REQUIRED_FOR_WMS")
            if not self.lab and session.fault == "WMS_UNAVAILABLE" and not context.get("wms_retry"):
                context["wms_retry"] = 1
                raise OSError(
                    "WMS_UNAVAILABLE: physical work retained; retry business acknowledgement only"
                )
            acknowledgement = {
                "command_id": command.command_id,
                "job_id": job.job_id,
                "verified_outcome": job.state.value,
                "wms_acknowledged": True,
                "physical_retry": False,
            }
            if self.lab:
                acknowledgement["wire"] = self.lab.reconcile_business(
                    acknowledgement, fail_once=session.fault == "WMS_UNAVAILABLE"
                )
            result = self.store.effect(
                ident,
                "WMS_ACKNOWLEDGEMENT",
                acknowledgement,
            )
            context["wms_ack"] = True
            return result
        if stage == 21:
            if not context.get("wms_ack"):
                raise Conflict("WMS_ACKNOWLEDGEMENT_REQUIRED")
            return self.store.complete_business(session, ident)
        if stage == 22:
            return self.store.effect(
                ident,
                "TRACE_SUMMARY",
                {
                    "session_id": session.session_id,
                    "order_id": session.order_id,
                    "job_ids": session.job_ids,
                    "correlation_id": session.correlation_id,
                    "stage_count": len(session.steps) + 1,
                    "event_count": len(ws.timeline(session.order_id)),
                    "acknowledgement_semantics": "HTTP accepted != DB commit != publisher confirm != consumer ACK != PLC acceptance != controller success != verification != WMS ACK != ERP completion",
                },
            )
        raise Conflict("UNKNOWN_GUIDED_STAGE")

    def authorize(self, session_id: str, request: AuthorizeStage) -> ExecutionSession:
        session, fresh = self.store.reserve(session_id, request)
        if not fresh:
            return self.present(session)
        return self._advance_reserved(session, request)

    def _advance_reserved(
        self, session: ExecutionSession, request: AuthorizeStage
    ) -> ExecutionSession:
        """Run exactly one admitted stage, including a safe interrupted-stage resume."""
        session_id = session.session_id
        start = monotonic()
        context = dict(session.context)
        before = (
            self.workflow.store.job(session.job_id).state.value if session.job_id else "NOT_INTAKEN"
        )
        stage = session.current_stage
        if stage == 21:
            before = self.workflow.store.order(session.order_id).status.value
        status = "WAITING_AUTHORIZATION"
        step_status = "COMPLETED"
        result: dict[str, Any]
        try:
            result = self._execute(session, context)
        except (ValueError, OSError, TimeoutError, StopIteration) as exc:
            # Failed pre-effect/business stages can be explicitly retried; physical intent cannot.
            physical_started = session.job_id is not None and self.workflow.store.job(
                session.job_id
            ).state in {JobState.EXECUTING, JobState.VERIFYING, JobState.UNKNOWN_OUTCOME}
            status = "UNKNOWN_OUTCOME" if stage == 16 and physical_started else "RETRYABLE_FAILURE"
            step_status = "FAILED"
            result = {"error": str(exc), "retry_permitted": stage != 16}
            injected_before_wire = (
                stage in {10, 11, 12}
                and context.get(f"fault_once_{stage}")
                and not session.context.get(f"fault_once_{stage}")
            )
            if injected_before_wire:
                result.update({"injected_failure": True, "network_attempted": False})
            if stage in {6, 7} and str(exc) != "STALE_OR_FUTURE_OBSERVATION":
                # Preserve the original engine's terminal planning rejection.
                claim = self._claim(session)
                try:
                    if session.job_id is None:
                        raise Conflict("SESSION_JOB_REQUIRED")
                    self.workflow.store.transition(
                        session.job_id,
                        JobState.FAILED,
                        "PLANNING_REJECTED:" + str(exc),
                        claim=claim,
                    )
                finally:
                    self.workflow.store.release(claim)
                status = "FAILED"
                result["retry_permitted"] = False
        job_ids = tuple(context.get("job_ids", session.job_ids))
        job_id = job_ids[int(context.get("job_index", 0))] if job_ids else None
        job = self.workflow.store.job(job_id) if job_id else None
        after = job.state.value if job else "NOT_INTAKEN"
        if stage == 21:
            after = self.workflow.store.order(session.order_id).status.value
        if stage == 19 and after in {"UNKNOWN_OUTCOME", "REQUIRES_INTERVENTION"}:
            status = "UNKNOWN_OUTCOME"
        next_stage = stage + 1 if step_status == "COMPLETED" else stage
        if stage in {6, 7} and result.get("error") == "STALE_OR_FUTURE_OBSERVATION":
            # A human may spend longer than the sensor freshness window reviewing
            # a proposal. Require a new observed/planned/validated sequence.
            next_stage = 5
            for key in ("pre_observation_id", "plan_id", "validated"):
                context.pop(key, None)
            result["next_action"] = "Capture a fresh observation, then plan and validate again."
        if (
            stage == 20
            and step_status == "COMPLETED"
            and int(context["job_index"]) + 1 < len(job_ids)
        ):
            context = {"job_ids": list(job_ids), "job_index": int(context["job_index"]) + 1}
            job_id = job_ids[context["job_index"]]
            next_stage = 5
        if next_stage == 23:
            status = "COMPLETED"
        title, component, protocol, classification, path, symbol, invariant = STAGES[stage - 1]
        if self.lab and stage in {10, 11, 12, 13, 14, 17, 20}:
            protocol = "AMQP" if stage in {10, 11} else "REST" if stage == 20 else "OPC UA"
            classification = "REAL PROTOCOL"
            path = "robotops/lab/transport.py"
            symbol = (
                "LabBridge."
                + {
                    10: "publish",
                    11: "edge_deliver",
                    12: "opc_connect",
                    13: "submit",
                    14: "preconditions",
                    17: "status",
                    20: "reconcile_business",
                }[stage]
            )
        if stage == 8 and result.get("recovered_existing_command"):
            path = "robotops/integration/engine.py"
            symbol = "GuidedEngine._execute"
        if stage == 19 and result.get("recovered_verification"):
            path = "robotops/workflow/store.py"
            symbol = "Store.records_for_job"
        if step_status == "FAILED":
            # A guard may reject before the intended adapter is ever called.
            # Report only the handler that certainly executed, without claiming
            # confirmed protocol evidence for a failed operation.
            path = "robotops/integration/engine.py"
            symbol = "GuidedEngine._execute"
            if self.lab:
                classification = "REAL CODE"
                result["protocol_evidence_confirmed"] = False
        if result.get("injected_failure"):
            protocol = "in-process fault injection"
            classification = "SIMULATED SYSTEM"
            path = "robotops/integration/engine.py"
            symbol = "GuidedEngine._execute"
        source_path = Path(__file__).parents[2] / path
        excerpt = ""
        if source_path.exists():
            lines = source_path.read_text(encoding="utf-8").splitlines()
            method = symbol.split(".")[-1]
            match = next((i for i, line in enumerate(lines) if f"def {method}(" in line), None)
            if method == "_execute":
                match = next(
                    (i for i, line in enumerate(lines) if line.strip() == f"if stage == {stage}:"),
                    match,
                )
                if result.get("injected_failure"):
                    match = next(
                        (
                            i
                            for i, line in enumerate(lines)
                            if "if session.fault == fault_for_stage[stage]" in line
                        ),
                        match,
                    )
            if match is not None:
                excerpt = "\n".join(lines[match : match + 8])
        step = ExecutionStep(
            step_id=stable_id(session_id, f"step:{session.revision}"),
            session_id=session_id,
            execution_session_id=session_id,
            order_id=session.order_id,
            job_id=session.job_id or job_id,
            command_id=job.command_id if job else None,
            correlation_id=session.correlation_id,
            stage=stage,
            sequence=len(session.steps) + 1,
            revision=session.revision,
            title=title,
            summary=str(sanitize(result.get("error") or result.get("status") or title)),
            status=step_status,
            component=component,
            protocol=protocol,
            classification=classification,
            input=sanitize(
                {
                    "stage": stage,
                    "request_id": request.request_id,
                    "command_id": job.command_id if job else None,
                }
            ),
            output=sanitize(result),
            state_before=before,
            state_after=after,
            persistence_effect="Authorization and bounded operation evidence committed; no transaction held while waiting.",
            wire=sanitize(result),
            source=SourceReference(path=path, symbol=symbol, excerpt=excerpt),
            invariant=invariant,
            failure_semantics="Query original command after uncertain effect; never blindly resend. Pre-effect and business failures require explicit retry.",
            duration_ms=(monotonic() - start) * 1000,
            evidence_ids=tuple(
                str(result[key])
                for key in (
                    "observation_id",
                    "verification_id",
                    "action_plan_id",
                    "command_id",
                    "task_id",
                    "demand_id",
                )
                if result.get(key)
            ),
            authorization_required=stage in GATES,
        )
        trace = ProtocolTrace(
            trace_id=stable_id(step.step_id, "protocol"),
            protocol=protocol,
            classification=classification,
            wire=sanitize(result),
        )
        self.workflow.store.save(trace.trace_id, trace)
        step = step.model_copy(update={"evidence_ids": (*step.evidence_ids, trace.trace_id)})
        if job:
            self.workflow.store.emit(
                job,
                component,
                "GUIDED_STAGE",
                f"{stage}:{step_status}",
                evidence_ids=(step.step_id,),
                duration_ms=step.duration_ms,
            )
        self.workflow.store.save(step.step_id, step)
        updated = session.model_copy(
            update={
                "revision": session.revision + 1,
                "status": status,
                "current_stage": min(next_stage, 22),
                "steps": (*session.steps, step),
                "context": sanitize(context),
                "job_ids": job_ids,
                "job_id": job_id,
                "command_id": self.workflow.store.job(job_id).command_id if job_id else None,
                "profile": "lab" if self.lab else "local",
                "updated_at": utc_now(),
            }
        )
        return self.present(self.store.finish(updated, session.revision))

    def _recover_unstarted_dispatch(self, session: ExecutionSession) -> ExecutionSession:
        """Prove no dispatch intent committed, then require renewed physical consent."""
        if session.job_id is None or session.command_id is None:
            raise Conflict("RECOVERY_COMMAND_IDENTITY_REQUIRED")
        receipt = self.workflow.runtime.recorded_journal(session.command_id)
        if receipt is not None:
            raise Conflict("DISPATCH_STATE_JOURNAL_CONFLICT_REQUIRES_INTERVENTION")
        context = {**session.context, "physical_authorized": False}
        result = {
            "command_id": session.command_id,
            "dispatch_intent_committed": False,
            "recorded_controller_result": None,
            "physical_resend": False,
            "next_action": "Renew explicit physical authorization before any dispatch.",
        }
        step = ExecutionStep(
            step_id=stable_id(session.session_id, f"recovery:{session.revision}"),
            session_id=session.session_id,
            execution_session_id=session.session_id,
            order_id=session.order_id,
            job_id=session.job_id,
            command_id=session.command_id,
            correlation_id=session.correlation_id,
            stage=16,
            sequence=len(session.steps) + 1,
            revision=session.revision,
            title="Interrupted execution recovered before dispatch",
            summary="No dispatch intent or controller result; renewed physical authorization required.",
            status="RECOVERED_NO_DISPATCH",
            component="recovery",
            protocol="SQL + controller journal",
            classification="REAL CODE",
            output=result,
            wire=result,
            state_before=JobState.READY_TO_EXECUTE,
            state_after=JobState.READY_TO_EXECUTE,
            persistence_effect="Session returned to the mandatory physical gate; no command sent.",
            source=SourceReference(
                path="robotops/integration/engine.py",
                symbol="GuidedEngine._recover_unstarted_dispatch",
                excerpt="receipt = self.workflow.runtime.recorded_journal(session.command_id)",
            ),
            invariant="A possibly completed physical operation is never resent by recovery.",
            failure_semantics="Any committed dispatch intent instead requires original-command reconciliation.",
            evidence_ids=(session.command_id,),
            authorization_required=True,
        )
        self.workflow.store.save(step.step_id, step)
        self.workflow.store.emit(
            self.workflow.store.job(session.job_id),
            "recovery",
            "GUIDED_RECOVERY",
            "NO_DISPATCH_INTENT_RENEW_PHYSICAL_AUTHORIZATION",
            evidence_ids=(step.step_id,),
        )
        updated = session.model_copy(
            update={
                "revision": session.revision + 1,
                "status": "WAITING_AUTHORIZATION",
                "current_stage": 15,
                "context": context,
                "steps": (*session.steps, step),
                "updated_at": utc_now(),
            }
        )
        return self.present(self.store.finish(updated, session.revision))

    def reconcile(
        self, session_id: str, request: AuthorizeStage, fault: Fault | None = None
    ) -> ExecutionSession:
        original = self.store.get(session_id)
        if original.status == "EXECUTING_STAGE":
            age = (utc_now() - original.updated_at).total_seconds()
            if age < max(
                self.workflow.settings.lease_seconds,
                self.workflow.settings.runtime_timeout_seconds
                + (float(self.lab.config.timeout) * 2 if self.lab else 0)
                + 60,
                self.workflow.settings.brain_timeout_seconds + 60,
            ):
                raise Conflict("BOUNDED_OPERATION_STILL_IN_PROGRESS")
        # Persist a new authorized recovery operation; never replay physical stage 16.
        session, fresh = self.store.reserve(
            session_id, request, recovery=True, recovery_fault=fault.value if fault else None
        )
        if not fresh:
            return self.present(session)
        if original.status == "EXECUTING_STAGE" and session.current_stage != 16:
            # Every other stage is a bounded idempotent persistence, protocol,
            # planning, observation, result or business operation. Stage 16 is
            # never passed to this automatic resume branch.
            return self._advance_reserved(session, request)
        if session.job_id is None:
            raise Conflict("NO_JOB_TO_RECONCILE")
        if self.workflow.store.job(session.job_id).state == JobState.READY_TO_EXECUTE:
            return self._recover_unstarted_dispatch(session)
        started = monotonic()
        before = self.workflow.store.job(session.job_id).state.value
        job = self.workflow.reconcile(session.job_id, fault)
        if self.lab and job.command_id:
            receipt = self.workflow.runtime.recorded_journal(job.command_id)
            if receipt:
                self.lab.record_result(job.command_id, receipt.model_dump(mode="json"))
        context = dict(session.context)
        context["reconciliation"] = {
            "job_id": job.job_id,
            "command_id": job.command_id,
            "status": job.state.value,
            "original_identity_queried": True,
            "physical_resend": False,
        }
        evidence = self.workflow.evidence(job.job_id).reconciliations[-1]
        step = ExecutionStep(
            step_id=stable_id(session_id, f"reconciliation:{session.revision}"),
            session_id=session_id,
            execution_session_id=session_id,
            order_id=session.order_id,
            job_id=job.job_id,
            command_id=job.command_id,
            correlation_id=session.correlation_id,
            stage=19,
            sequence=len(session.steps) + 1,
            revision=session.revision,
            title="Original command reconciliation",
            summary=evidence.verification.reason,
            status="COMPLETED",
            component="reconciliation",
            protocol="controller + sensor",
            classification="REAL CODE",
            input={
                "command_id": job.command_id,
                "observation_fault": fault.value if fault else None,
            },
            output=sanitize(evidence.model_dump(mode="json")),
            state_before=before,
            state_after=job.state.value,
            persistence_effect="Original journal, fresh observation and verification evidence committed.",
            wire=context["reconciliation"],
            source=SourceReference(
                path="robotops/workflow/engine.py",
                symbol="Engine._reconcile",
                excerpt="receipt = self.gateway.query(command)\nobservation = self._observe(job, fault if fault in OBSERVATION_FAULTS else None)\nresult = self.verifier.verify(command, observation, receipt)",
            ),
            invariant="Reconciliation queries original command identity; it has no send operation.",
            failure_semantics="Inconclusive evidence pauses for intervention; no physical retry.",
            duration_ms=(monotonic() - started) * 1000,
            evidence_ids=(evidence.evidence_id,),
            authorization_required=True,
        )
        self.workflow.store.save(step.step_id, step)
        updated = session.model_copy(
            update={
                "revision": session.revision + 1,
                "current_stage": 20,
                "status": "WAITING_AUTHORIZATION"
                if job.state in {JobState.COMPLETED, JobState.FAILED}
                else "UNKNOWN_OUTCOME",
                "context": context,
                "steps": (*session.steps, step),
                "updated_at": utc_now(),
            }
        )
        return self.present(self.store.finish(updated, session.revision))
