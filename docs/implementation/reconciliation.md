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
The whole cell pauses further picks, including other products. The dashboard
names this blocking product in **Review evidence** and offers Reconcile [product].
With Normal observation selected, this queries that original job even if another
execution is selected for viewing. A resolved job unlocks the next explicit order;
an inconclusive result keeps the cell blocked and offers **Observe again**.
Select another observation mode (Normal observation has no injected
degradation), then explicitly request reconciliation again for the same job.
This adds `REQUIRES_INTERVENTION -> RECONCILING` with identity-matched fresh
evidence. The same decision table applies on every attempt: there is no manual
success override or retry dispatch. Earlier evidence stays immutable and ordered
by durable insertion; the UI displays the latest assessment. Sufficient new
evidence permits the next explicit order in the same delivery. See ADR 0008.
Reconciliation queries the original command, then captures a new observation.
Evidence and transitions are persisted together. No code path in reconciliation
dispatches a command. The explicit retry policy is manual_after_proven_no_effect;
even proven no-effect is reported as FAILED, with no automatic replacement pick.

A restarted orchestrator respects live leases. Once an expired lease is reclaimed,
EXECUTING/VERIFYING work becomes UNKNOWN_OUTCOME and reconciles. A process-death
test exits after the controller commits a pick but before the caller receives it;
recovery completes with one effect and no duplicate dispatch. Cell reset changes
the generation and preserves unknown jobs; re-observation is still required.
Intervention is excluded from automatic startup recovery and normal execution
claims. Only an explicit operator request may reopen it for evidence collection.

The dashboard's Start new test creates an independent synthetic experiment for
any combination. It does not reconcile or reset the previous world. That test's
unknown/intervention states and evidence remain unchanged in read-only history.
Restart recovery applies only to the active world; archived uncertainty never
becomes success through navigation or restart. See ADR 0007.

Run `uv run --locked python -m tools.dev demo` for happy path; add
`--scenario lost_ack_after_effect`, `ambiguous`, or `restart`. Each fresh run writes
its timeline, original command identity, controller events and a clearly labelled
test-oracle world to a new directory under runs/. No model account is needed.
