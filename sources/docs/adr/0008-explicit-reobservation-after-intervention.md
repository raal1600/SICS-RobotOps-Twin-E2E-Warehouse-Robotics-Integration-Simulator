# ADR 0008: Continue an intervention with explicit fresh evidence

Accepted locally 2026-10-03. Classification: SIMULATOR_DESIGN.

The user needs to keep investigating the same test after a bad observation.
Previously REQUIRES_INTERVENTION was permanently terminal: the cell remained
quarantined and the UI offered only inspection or a separate test. A degraded
observation should pause physical work without prohibiting further observation.

Extend the centrally guarded job graph with
`REQUIRES_INTERVENTION -> RECONCILING`, exclusively on an explicit reconciliation
request. The existing endpoint queries the original controller journal and
captures a new WorldObservation. Identity-matched ReconciliationEvidence is
required to enter RECONCILING; the unchanged verifier determines COMPLETED,
proven-no-effect FAILED, or another REQUIRES_INTERVENTION. Repetition is supported
for every configured observation degradation, including repeated inconclusive
attempts. No command dispatch, new command identity or fixture reset occurs.

COMPLETED and FAILED remain terminal. Intervention is excluded from automatic
startup recovery and normal execution claims; only explicit reconciliation may
claim it. Fenced cell leases serialize new evidence collection against other
workers. The cell blocks new picks and fixture restock until the original outcome
is resolved. A later successful reassessment enables the next explicit order;
it never automatically retries the original pick. Archived tests remain read-only.

Every attempt retains its immutable evidence, observation and causal transitions.
Evidence arrays follow durable insertion order rather than UUID ordering so the
UI shows the latest assessment while preserving earlier inconclusive results.
The delivery identity and recorded Blender motion remain unchanged; replay adds
the new investigation events without adding a second motion clip.

This is an operator-requested extension of the normative graph, not a relaxation
of SC-STATE-003/004 or SC-REC-005. Bad evidence still cannot produce success.
New sufficient evidence may resolve the outcome. No acceptance threshold, sensor
boundary, or exactly-one-effect requirement changes. No schema migration or
rewriting of existing user jobs is needed. ADR 0007's independent tests remain
available but are no longer the only way to continue after intervention.
