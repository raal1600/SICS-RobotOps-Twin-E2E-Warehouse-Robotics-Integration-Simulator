"""Durable workflow; uncertainty always reconciles the original intent before resolution."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from time import monotonic

from pydantic import ValidationError

from robotops.brain.deterministic import DeterministicBrain
from robotops.brain.validation import ActionValidator
from robotops.config import Settings
from robotops.domain.models import (
    ActionPlan,
    CommandReceipt,
    FailureInjection,
    Fault,
    JobEvidence,
    JobState,
    PickJob,
    PresentationSnapshot,
    ReconciliationEvidence,
    RobotCommand,
    Verdict,
    VerificationResult,
    WorldObservation,
    new_id,
    stable_id,
)
from robotops.domain.ports import Brain, Observer, Runtime
from robotops.faults.injection import OBSERVATION_FAULTS, RUNTIME_FAULTS
from robotops.observation.model import ObservationModel
from robotops.robot_gateway.gateway import RobotGateway
from robotops.verification.verifier import Verifier
from robotops.workflow.states import RECONCILABLE, UNCERTAIN
from robotops.workflow.store import Claim, Conflict, NotFound, Store, metadata


class Engine:
    def __init__(
        self,
        store: Store,
        runtime: Runtime,
        settings: Settings | None = None,
        brain: Brain | None = None,
        observer: Observer | None = None,
    ):
        self.store = store
        self.runtime = runtime
        self.settings: Settings = settings or getattr(runtime, "settings", None) or Settings()
        self.brain = brain or DeterministicBrain(self.settings)
        self.observer = observer or ObservationModel(self.settings)
        self.validator = ActionValidator(self.settings)
        self.verifier = Verifier(self.settings)
        self.gateway = RobotGateway(runtime, store)

    def _observe(self, job: PickJob, fault: Fault | None = None) -> WorldObservation:
        observation = self.observer.observe(self.runtime.world(), fault)
        # Correlate sensor evidence to the request without changing its capture data.
        observation = observation.model_copy(
            update={
                "run_id": job.run_id,
                "correlation_id": job.correlation_id,
                "causation_id": job.command_id or job.job_id,
            }
        )
        self.store.save(observation.observation_id, observation)
        self.store.emit(
            job,
            "observation",
            "OBSERVATION_CAPTURED",
            fault.value if fault else "FRESH_SENSOR_MODEL",
            evidence_ids=(observation.observation_id,),
        )
        return observation

    def _inject(self, job: PickJob, fault: Fault | None) -> None:
        if fault is not None:
            injection = FailureInjection(
                **metadata(job), injection_id=new_id(), fault=fault, job_id=job.job_id
            )
            self.store.save(injection.injection_id, injection)
            self.store.emit(
                job, "faults", "FAULT_INJECTED", fault.value, evidence_ids=(injection.injection_id,)
            )

    def stage_intake(self, job: PickJob, claim: Claim) -> PickJob:
        """Validate an already durably received job; no planning or actuation."""
        try:
            self.store.load(PresentationSnapshot, job.job_id)
        except NotFound:
            self.store.save(
                job.job_id,
                PresentationSnapshot(
                    **metadata(job), job_id=job.job_id, world=self.runtime.world()
                ),
            )
        if job.state == JobState.RECEIVED:
            return self.store.transition(
                job.job_id, JobState.VALIDATED, "ORDER_SCHEMA_VALID", claim=claim
            )
        return job

    def stage_observe(self, job: PickJob, claim: Claim) -> WorldObservation:
        if job.state == JobState.VALIDATED:
            job = self.store.transition(
                job.job_id, JobState.PLANNING, "BRAIN_REQUESTED", claim=claim
            )
        return self._observe(job)

    def stage_plan(
        self, job: PickJob, observation: WorldObservation, fault: Fault | None = None
    ) -> ActionPlan:
        destination = next(
            loc for loc in self.settings.locations if loc.location_id == job.line.destination_id
        )
        if fault == Fault.BRAIN_TIMEOUT:
            raise TimeoutError("BRAIN_TIMEOUT")
        if fault == Fault.BRAIN_INVALID_OUTPUT:
            ActionPlan.model_validate_json('{"code":"arbitrary code rejected"}')
        # The planner only receives immutable inputs and has no actuator capability.
        pool = ThreadPoolExecutor(max_workers=1)
        future = pool.submit(self.brain.plan, job, observation, destination)
        try:
            plan = future.result(timeout=self.settings.brain_timeout_seconds)
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
        self.store.save(plan.action_plan_id, plan)
        return plan

    def stage_validate(
        self, job: PickJob, observation: WorldObservation, plan: ActionPlan
    ) -> ActionPlan:
        destination = next(
            loc for loc in self.settings.locations if loc.location_id == job.line.destination_id
        )
        plan = self.validator.validate(
            plan, job, observation, self.runtime.world().cell, destination
        )
        self.store.emit(
            job,
            "validator",
            "PLAN_VALIDATED",
            "SEMANTIC_CHECKS_PASSED",
            evidence_ids=(plan.action_plan_id,),
        )
        return plan

    def stage_command(self, job: PickJob, plan: ActionPlan, claim: Claim) -> PickJob:
        command = RobotCommand(
            **plan.model_dump(),
            command_id=stable_id(job.job_id, "pick-attempt-1"),
            **({"required_tool_id": plan.selected_tool_id} if plan.schema_version == "2.0" else {}),
        )
        job = self.store.prepare(claim, plan, command)
        if plan.tool_selection is not None:
            self.store.emit(
                job,
                "brain",
                "GRASP_SELECTION_EVALUATED",
                "DETERMINISTIC_COMPATIBILITY_SCORE",
                evidence_ids=(plan.action_plan_id,),
            )
            self.store.emit(
                job,
                "planner",
                "TRAJECTORY_PLANNED",
                "CONSERVATIVE_SYNTHETIC_COLLISION_PREFLIGHT",
                evidence_ids=(plan.action_plan_id,),
            )
        return self.store.transition(
            job.job_id, JobState.READY_TO_EXECUTE, "PLAN_PERSISTED", claim=claim
        )

    def stage_dispatch(
        self,
        job: PickJob,
        claim: Claim,
        fault: Fault | None = None,
        sender: Callable[[RobotCommand, Fault | None], CommandReceipt] | None = None,
    ) -> CommandReceipt | None:
        if job.command_id is None:
            raise Conflict("MISSING_DURABLE_COMMAND")
        command = self.store.load(RobotCommand, job.command_id)
        self.store.transition(job.job_id, JobState.EXECUTING, "DISPATCH_INTENT", claim=claim)
        try:
            return (sender or self.gateway.send)(
                command, fault if fault in RUNTIME_FAULTS else None
            )
        except (TimeoutError, OSError):
            self.store.transition(
                job.job_id, JobState.UNKNOWN_OUTCOME, "COMMUNICATION_UNCERTAIN", claim=claim
            )
            return None

    def stage_result(self, job: PickJob, claim: Claim) -> PickJob:
        if job.state == JobState.EXECUTING:
            return self.store.transition(
                job.job_id, JobState.VERIFYING, "CONTROLLER_RESPONSE", claim=claim
            )
        return job

    def stage_verify(
        self,
        job: PickJob,
        command: RobotCommand,
        observation: WorldObservation,
        receipt: CommandReceipt | None,
        claim: Claim,
    ) -> VerificationResult:
        result = self.verifier.verify(command, observation, receipt)
        if result.verdict == Verdict.INCONCLUSIVE:
            self.store.save(result.verification_id, result)
            if job.state != JobState.UNKNOWN_OUTCOME:
                self.store.transition(
                    job.job_id, JobState.UNKNOWN_OUTCOME, result.reason, claim=claim
                )
        else:
            target = (
                JobState.COMPLETED
                if result.verdict == Verdict.VERIFIED_SUCCESS
                else JobState.FAILED
            )
            self.store.transition(job.job_id, target, result.reason, claim=claim, evidence=result)
        return result

    def is_guided(self, job_id: str) -> bool:
        with self.store.connect() as db:
            return (
                db.execute("SELECT 1 FROM meta WHERE key=?", ("guided:" + job_id,)).fetchone()
                is not None
            )

    def run(self, job_id: str, fault: Fault | None = None, *, owner: str | None = None) -> PickJob:
        if self.is_guided(job_id):
            raise Conflict("GUIDED_JOB_REQUIRES_STAGE_AUTHORIZATION")
        claim = self.store.claim(job_id, owner or new_id(), self.settings.lease_seconds)
        if claim is None:
            return self.store.job(job_id)
        start = monotonic()
        try:
            job = self.stage_intake(self.store.job(job_id), claim)
            self._inject(job, fault)
            if job.state in {JobState.VALIDATED, JobState.PLANNING}:
                try:
                    observation = self.stage_observe(job, claim)
                    job = self.store.job(job_id)
                    plan = self.stage_plan(job, observation, fault)
                    plan = self.stage_validate(job, observation, plan)
                    job = self.stage_command(job, plan, claim)
                except (
                    ValueError,
                    ValidationError,
                    TimeoutError,
                    StopIteration,
                    AttributeError,
                ) as exc:
                    return self.store.transition(
                        job_id, JobState.FAILED, "PLANNING_REJECTED:" + str(exc), claim=claim
                    )
            if job.state == JobState.READY_TO_EXECUTE:
                receipt = self.stage_dispatch(job, claim, fault)
                if receipt is None:
                    return self.store.job(job_id)
                job = self.stage_result(self.store.job(job_id), claim)
                observation = self._observe(job, fault if fault in OBSERVATION_FAULTS else None)
                if job.command_id is None:
                    raise Conflict("MISSING_DURABLE_COMMAND")
                command = self.store.load(RobotCommand, job.command_id)
                self.stage_verify(job, command, observation, receipt, claim)
            return self.store.job(job_id)
        finally:
            self.store.emit(
                self.store.job(job_id),
                "workflow",
                "PIPELINE_LATENCY",
                "RUN_FINISHED",
                duration_ms=(monotonic() - start) * 1000,
            )
            self.store.release(claim)

    def reconcile(self, job_id: str, fault: Fault | None = None) -> PickJob:
        job = self.store.job(job_id)
        if job.state not in RECONCILABLE:
            raise Conflict("JOB_NOT_UNCERTAIN")
        claim = self.store.claim(job_id, new_id(), self.settings.lease_seconds, reconcile=True)
        if claim is None:
            raise Conflict("JOB_OWNED_OR_CELL_QUARANTINED")
        try:
            job = self.store.job(job_id)
            self._inject(job, fault)
            if job.state in {JobState.EXECUTING, JobState.VERIFYING}:
                job = self.store.transition(
                    job_id, JobState.UNKNOWN_OUTCOME, "RESTART_UNCERTAIN_DISPATCH", claim=claim
                )
            return self._reconcile(job, claim, fault)
        finally:
            self.store.release(claim)

    def _reconcile(self, job: PickJob, claim: Claim, fault: Fault | None) -> PickJob:
        if job.command_id is None:
            raise Conflict("UNKNOWN_JOB_MISSING_COMMAND")
        command = self.store.load(RobotCommand, job.command_id)
        # Query first, then a fresh observation. Never dispatch here.
        receipt = self.gateway.query(command)
        observation = self._observe(job, fault if fault in OBSERVATION_FAULTS else None)
        result = self.verifier.verify(command, observation, receipt)
        evidence = ReconciliationEvidence(
            **metadata(job, observation.observation_id),
            evidence_id=new_id(),
            job_id=job.job_id,
            command=command,
            receipt=receipt,
            observation=observation,
            verification=result,
        )
        if job.state in {JobState.UNKNOWN_OUTCOME, JobState.REQUIRES_INTERVENTION}:
            job = self.store.transition(
                job.job_id,
                JobState.RECONCILING,
                "OPERATOR_REOBSERVATION"
                if job.state == JobState.REQUIRES_INTERVENTION
                else "EVIDENCE_COLLECTED",
                claim=claim,
                evidence=evidence,
            )
        target = {
            Verdict.VERIFIED_SUCCESS: JobState.COMPLETED,
            Verdict.VERIFIED_FAILURE: JobState.FAILED,
            Verdict.INCONCLUSIVE: JobState.REQUIRES_INTERVENTION,
        }[result.verdict]
        job = self.store.transition(
            job.job_id, target, result.reason, claim=claim, evidence=evidence
        )
        self.store.emit(
            job,
            "reconciliation",
            "RECONCILIATION_RESULT",
            result.verdict,
            evidence_ids=(evidence.evidence_id,),
        )
        return job

    def start_fresh_scene(self) -> None:
        epoch = self.store.begin_scene_reset()
        self.runtime.reset(scene_epoch=epoch)
        self.gateway.sync_events()
        self.store.finish_scene_reset(epoch)

    def recover(self) -> list[PickJob]:
        if self.store.pending_scene_reset():
            self.start_fresh_scene()
        recovered = []
        for job in self.store.recoverable():
            if self.is_guided(job.job_id):
                recovered.append(job)
                continue
            if job.state in UNCERTAIN:
                try:
                    recovered.append(self.reconcile(job.job_id))
                except Conflict:
                    # An unexpired live owner or another quarantined job is not overridden.
                    recovered.append(self.store.job(job.job_id))
            else:
                recovered.append(self.run(job.job_id))
        return recovered

    def evidence(self, job_id: str) -> JobEvidence:
        job = self.store.job(job_id)
        observations = tuple(
            self.store.load(WorldObservation, event.evidence_ids[0])
            for event in self.store.timeline(job.order_id)
            if event.job_id == job_id and event.event_type == "OBSERVATION_CAPTURED"
        )
        reconciliations = self.store.records_for_job(ReconciliationEvidence, job_id)
        results = {
            item.verification_id: item
            for item in self.store.records_for_job(VerificationResult, job_id)
        }
        results.update(
            {item.verification.verification_id: item.verification for item in reconciliations}
        )
        command = self.store.load(RobotCommand, job.command_id) if job.command_id else None
        return JobEvidence(
            job=job,
            command=command,
            journal=self.runtime.recorded_journal(job.command_id) if job.command_id else None,
            observations=observations,
            verifications=tuple(results.values()),
            reconciliations=reconciliations,
        )
