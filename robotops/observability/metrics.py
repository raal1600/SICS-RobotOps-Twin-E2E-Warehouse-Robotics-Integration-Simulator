from collections import Counter

from robotops.domain.models import JobState, RobotCommand, Verdict
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
    planning_failures = [
        event.reason for event in events if event.reason.startswith("PLANNING_REJECTED:")
    ]
    counts = {
        "orders_total": len(store.orders()),
        "jobs_unknown_outcome_total": transitions[JobState.UNKNOWN_OUTCOME],
        "command_timeouts_total": sum(
            event.reason == "COMMUNICATION_UNCERTAIN" for event in events
        ),
        "pick_effects_total": types["PICK_EFFECT"],
        "tool_changes_total": types["TOOL_CHANGE_COMPLETED"],
        "tool_selection_failures_total": sum("TOOL" in reason for reason in planning_failures),
        "reconciliations_total": types["RECONCILIATION_RESULT"],
        "reconciliations_success_total": reconciled[Verdict.VERIFIED_SUCCESS],
        "reconciliations_inconclusive_total": reconciled[Verdict.INCONCLUSIVE],
        "observations_total": types["OBSERVATION_CAPTURED"],
        "observations_low_confidence_total": sum(
            event.event_type == "OBSERVATION_CAPTURED"
            and event.reason == "LOW_CONFIDENCE_OBSERVATION"
            for event in events
        ),
        "observations_stale_total": sum(
            event.event_type == "OBSERVATION_CAPTURED" and event.reason == "STALE_OBSERVATION"
            for event in events
        ),
        "observations_contradictory_total": sum(
            event.event_type == "OBSERVATION_CAPTURED"
            and event.reason == "CONTRADICTORY_OBSERVATION"
            for event in events
        ),
        "trajectory_plans_total": types["TRAJECTORY_PLANNED"],
        "trajectory_rejections_total": sum(
            any(word in reason for word in ("TRAJECTORY", "WORKSPACE", "SPATIAL_METADATA"))
            for reason in planning_failures
        ),
        "collision_preflight_failures_total": sum(
            "NO_COLLISION_FREE_SYNTHETIC_TRAJECTORY" in reason for reason in planning_failures
        ),
    }
    for name, count in counts.items():
        lines += [f"# TYPE robotops_{name} counter", f"robotops_{name} {count}"]
    durations = []
    for identity in {
        event.command_id
        for event in events
        if event.event_type == "PICK_EFFECT" and event.command_id
    }:
        command = store.load(RobotCommand, identity)
        if command.trajectory is not None:
            durations.append(command.trajectory.estimated_sim_duration_s)
    lines += [
        "# HELP robotops_simulated_motion_duration_s Synthetic presentation time; not application latency.",
        "# TYPE robotops_simulated_motion_duration_s summary",
        f"robotops_simulated_motion_duration_s_count {len(durations)}",
        f"robotops_simulated_motion_duration_s_sum {sum(durations):.9f}",
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
    lines += [
        "# HELP robotops_pipeline_latency_ms Actual application processing latency in milliseconds.",
        "# TYPE robotops_pipeline_latency_ms summary",
        f"robotops_pipeline_latency_ms_count {len(latencies)}",
        f"robotops_pipeline_latency_ms_sum {sum(latencies) * 1000:.6f}",
    ]
    return "\n".join(lines) + "\n"
