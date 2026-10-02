from collections import Counter

from robotops.domain.models import JobState, Verdict
from robotops.workflow.store import Store


def prometheus(store: Store) -> str:
    events = store.timeline()
    transitions = Counter(
        event.state_after for event in events if event.event_type == "JOB_TRANSITION"
    )
    types = Counter(event.event_type for event in events)
    reconciled = Counter(
        event.reason for event in events if event.event_type == "RECONCILIATION_RESULT"
    )
    current = Counter(
        store.job(job_id).state for order in store.orders() for job_id in order.job_ids
    )
    lines = [
        "# HELP robotops_jobs_received_total Durable accepted jobs.",
        "# TYPE robotops_jobs_received_total counter",
        f"robotops_jobs_received_total {types['JOB_RECEIVED']}",
    ]
    for label, state in [
        ("completed", JobState.COMPLETED),
        ("failed", JobState.FAILED),
        ("unknown", JobState.UNKNOWN_OUTCOME),
        ("intervention", JobState.REQUIRES_INTERVENTION),
    ]:
        lines += [
            f"# TYPE robotops_jobs_{label}_total counter",
            f"robotops_jobs_{label}_total {transitions[state]}",
        ]
    lines.append("# TYPE robotops_jobs_current gauge")
    for state in JobState:
        lines.append(f'robotops_jobs_current{{state="{state.value}"}} {current[state]}')
    for verdict in Verdict:
        lines.append(
            f'robotops_reconciliation_total{{outcome="{verdict.value}"}} {reconciled[verdict]}'
        )
    lines += [
        f"robotops_commands_total {types['COMMAND_INTENT']}",
        f"robotops_duplicate_commands_suppressed_total {types['DUPLICATE_SUPPRESSED']}",
        "robotops_injected_failures_total "
        + str(
            sum(
                event.event_type == "FAULT_INJECTED" and event.component == "faults"
                for event in events
            )
        ),
    ]
    latencies = [
        event.duration_ms / 1000 for event in events if event.event_type == "PIPELINE_LATENCY"
    ]
    lines += [
        "# TYPE robotops_pipeline_latency_seconds histogram",
        f"robotops_pipeline_latency_seconds_count {len(latencies)}",
        f"robotops_pipeline_latency_seconds_sum {sum(latencies):.9f}",
    ]
    for bound in [0.1, 0.5, 1, 5, 30, 120]:
        lines.append(
            f'robotops_pipeline_latency_seconds_bucket{{le="{bound}"}} '
            + str(sum(value <= bound for value in latencies))
        )
    lines.append(f'robotops_pipeline_latency_seconds_bucket{{le="+Inf"}} {len(latencies)}')
    return "\n".join(lines) + "\n"
