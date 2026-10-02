import pytest

from robotops.domain.models import JobState, PickJob, utc_now
from robotops.workflow.states import ALLOWED, TransitionError, guard


@pytest.mark.parametrize("before", list(JobState))
@pytest.mark.parametrize("after", list(JobState))
def test_forbidden_transitions_and_evidence_requirements(before, after, order_request):
    job = PickJob(
        run_id="r",
        correlation_id="c",
        causation_id="e",
        timestamp=utc_now(),
        job_id="j",
        order_id="o",
        line=order_request.lines[0],
        state=before,
    )
    permitted_without_evidence = (
        after in ALLOWED[before]
        and before not in {JobState.UNKNOWN_OUTCOME, JobState.RECONCILING}
        and after != JobState.COMPLETED
        and not (before == JobState.VERIFYING and after == JobState.FAILED)
    )
    if permitted_without_evidence:
        guard(job, after)
    else:
        with pytest.raises(TransitionError):
            guard(job, after)
