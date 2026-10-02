# Observation, verification and reconciliation

DeterministicBrain is a local pure proposal function for a fixed job, observation
and destination. A strict schema plus ActionValidator checks job/order/line/run
ownership, source/destination, version, epoch, cell generation, freshness,
confidence, coordinate metadata and workspace. A bounded wait discards a late
proposal; Brain has no runtime capability. The optional structured-output parser
has no provider dependency, command execution or arbitrary code evaluation.

WorldState crosses into ObservationModel, which returns a separate WorldObservation.
Deterministic degradation supports missing coverage/detections, low confidence,
stale capture time, conflicting detections and seeded configurable pose uncertainty.
Verifier accepts only WorldObservation and original command/receipt contracts;
dependency and runtime type tests prohibit truth substitution.

| Journal + fresh observed target | Verdict | Reconciliation outcome |
|---|---|---|
| Original durable SUCCEEDED/one effect; source covered, target only at destination | VERIFIED_SUCCESS | COMPLETED |
| Original durable REJECTED/FAILED/zero effects; target at source | VERIFIED_FAILURE | FAILED |
| Missing/non-durable/mismatched journal, stale/missing/low-confidence/conflicting observation | INCONCLUSIVE | REQUIRES_INTERVENTION |
| Any other contradiction or incomplete result | INCONCLUSIVE | REQUIRES_INTERVENTION |

Before acknowledgement loss is reconciled, the job remains UNKNOWN_OUTCOME.
Reconciliation queries the original command, then captures a new observation.
Evidence and transitions are persisted together. No code path in reconciliation
dispatches a command. The explicit retry policy is manual_after_proven_no_effect;
even proven no-effect is reported as FAILED, with no automatic replacement pick.

A restarted orchestrator respects live leases. Once an expired lease is reclaimed,
EXECUTING/VERIFYING work becomes UNKNOWN_OUTCOME and reconciles. A process-death
test exits after the controller commits a pick but before the caller receives it;
recovery completes with one effect and no duplicate dispatch. Cell reset changes
the generation and preserves unknown jobs; re-observation is still required.

Run `uv run --locked python -m tools.dev demo` for happy path; add
`--scenario lost_ack_after_effect`, `ambiguous`, or `restart`. Each fresh run writes
its timeline, original command identity, controller events and a clearly labelled
test-oracle world to a new directory under runs/. No model account is needed.
