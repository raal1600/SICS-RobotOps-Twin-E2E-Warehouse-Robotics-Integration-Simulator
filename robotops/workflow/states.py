from robotops.domain.models import (
    JobState,
    PickJob,
    ReconciliationEvidence,
    Verdict,
    VerificationResult,
)


class TransitionError(ValueError):
    pass


TERMINAL = {JobState.COMPLETED, JobState.FAILED}
# Recovery may retry uncertain evidence collection automatically. Intervention
# requires an explicit operator request; neither path is allowed to dispatch.
UNCERTAIN = {JobState.EXECUTING, JobState.VERIFYING, JobState.UNKNOWN_OUTCOME, JobState.RECONCILING}
RECONCILABLE = UNCERTAIN | {JobState.REQUIRES_INTERVENTION}
ALLOWED: dict[JobState, set[JobState]] = {
    JobState.RECEIVED: {JobState.VALIDATED, JobState.FAILED},
    JobState.VALIDATED: {JobState.PLANNING, JobState.FAILED},
    JobState.PLANNING: {JobState.READY_TO_EXECUTE, JobState.FAILED},
    JobState.READY_TO_EXECUTE: {JobState.EXECUTING, JobState.FAILED},
    JobState.EXECUTING: {JobState.VERIFYING, JobState.UNKNOWN_OUTCOME},
    JobState.VERIFYING: {JobState.COMPLETED, JobState.FAILED, JobState.UNKNOWN_OUTCOME},
    JobState.UNKNOWN_OUTCOME: {JobState.RECONCILING},
    JobState.RECONCILING: {JobState.COMPLETED, JobState.FAILED, JobState.REQUIRES_INTERVENTION},
    JobState.COMPLETED: set(),
    JobState.FAILED: set(),
    JobState.REQUIRES_INTERVENTION: {JobState.RECONCILING},
}


def guard(
    job: PickJob,
    target: JobState,
    evidence: VerificationResult | ReconciliationEvidence | None = None,
) -> None:
    if target not in ALLOWED[job.state]:
        raise TransitionError(f"FORBIDDEN_TRANSITION:{job.state}->{target}")
    if job.state in {
        JobState.UNKNOWN_OUTCOME,
        JobState.RECONCILING,
        JobState.REQUIRES_INTERVENTION,
    }:
        if not isinstance(evidence, ReconciliationEvidence):
            raise TransitionError("RECONCILIATION_EVIDENCE_REQUIRED")
        if evidence.job_id != job.job_id or evidence.command.command_id != job.command_id:
            raise TransitionError("RECONCILIATION_IDENTITY_MISMATCH")
    verdict = evidence.verification if isinstance(evidence, ReconciliationEvidence) else evidence
    if verdict is not None:
        if verdict.job_id != job.job_id or verdict.command_id != job.command_id:
            raise TransitionError("VERIFICATION_IDENTITY_MISMATCH")
    if target == JobState.COMPLETED:
        if verdict is None or verdict.verdict != Verdict.VERIFIED_SUCCESS:
            raise TransitionError("SUCCESS_EVIDENCE_REQUIRED")
    if target == JobState.FAILED and job.state in UNCERTAIN:
        if verdict is None or verdict.verdict != Verdict.VERIFIED_FAILURE:
            raise TransitionError("FAILURE_EVIDENCE_REQUIRED")
