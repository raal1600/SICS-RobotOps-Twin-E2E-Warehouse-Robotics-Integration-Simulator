# CODEX_GOAL_CHECKLIST.md

Operational checklist only. `PROJECT_PLAN.md` and `SUCCESS_CRITERIA.md` remain normative.

## Start
- [ ] Read HANDOFF -> PROJECT_PLAN -> SUCCESS_CRITERIA -> this checklist -> README/research/publication docs.
- [ ] Inspect current code/tests/contracts/ADRs and GOAL_PROGRESS.
- [ ] Establish current PASS/FAIL/unknown status for every MUST.
- [ ] Check documentation drift before changing code.

## Contracts
- [ ] Versioned typed domain schemas.
- [ ] Stable IDs, correlation/causation IDs, UTC timestamps.
- [ ] Units/coordinate frames/calibration metadata where relevant.
- [ ] OpenAPI/event contracts validate.
- [ ] Order and command idempotency semantics implemented.

## Workflow
- [ ] Central job transition guard.
- [ ] Durable audit events.
- [ ] Safe job claim/concurrency.
- [ ] Timeout != failure.
- [ ] UNKNOWN_OUTCOME + RECONCILING implemented.
- [ ] Restart never blindly replays uncertain side effects.

## Brain / action validation
- [ ] Deterministic local Brain is mandatory path.
- [ ] Strict schema validation.
- [ ] Invalid/timeout Brain cannot reach effect.
- [ ] Optional model adapter cannot block CI.
- [ ] No arbitrary model-generated execution code.

## Cell / robot gateway
- [ ] Cell states and logical interlocks.
- [ ] Controller command journal.
- [ ] Duplicate command suppression.
- [ ] Same command ID + changed payload rejected.
- [ ] Required deterministic fault injections.

## Blender
- [ ] Stable scene/object identities.
- [ ] Bounded runtime adapter.
- [ ] Deterministic reset/query/pick.
- [ ] DROP_ACK_AFTER_EFFECT supported.
- [ ] Screenshot/artifact available.
- [ ] Runtime does not require unrestricted MCP.
- [ ] Docs preserve synthetic/non-safety boundary.

## Observation / verification
- [ ] Ground truth separated from observation.
- [ ] Degradation fixtures implemented.
- [ ] VERIFIED_SUCCESS / VERIFIED_FAILURE / INCONCLUSIVE.
- [ ] Low confidence/contradiction never fabricates success.

## Reconciliation
- [ ] Lost ack after effect -> UNKNOWN_OUTCOME.
- [ ] Query original command identity.
- [ ] Fresh observation.
- [ ] Proven existing effect -> COMPLETED.
- [ ] Exactly one pick effect.
- [ ] Ambiguous -> intervention/unknown.
- [ ] Restart version of critical scenario passes.

## Observability
- [ ] Structured causal event logs.
- [ ] Order/job/command correlation.
- [ ] State transitions visible.
- [ ] Latency + outcome/reconciliation/duplicate/fault metrics.
- [ ] UI timeline explains demo.

## Tests/gates
- [ ] Unit.
- [ ] Contract.
- [ ] Integration.
- [ ] E2E fixtures from SUCCESS_CRITERIA.
- [ ] Full deterministic suite one command.
- [ ] Full suite passes twice cleanly.
- [ ] Lint/format.
- [ ] Typecheck.
- [ ] Dependency/security gate.
- [ ] No mandatory external LLM/API/GPU.

## Knowledge-base synchronization
- [ ] Identify implementation/source/status changes that invalidate docs.
- [ ] Update all affected normative/operational/public source files together.
- [ ] Preserve provenance categories.
- [ ] Update diagrams for architecture/state/recovery/trust changes.
- [ ] README has current commands, paths, status and no stale counts.
- [ ] Validate links, referenced paths, criterion IDs and contract references.
- [ ] Build publication from source; never edit generated Pages/PDF manually.
- [ ] Record drift and synchronization in GOAL_PROGRESS.

## Final acceptance
- [ ] Generate ACCEPTANCE_REPORT.md.
- [ ] Every MUST has inspectable PASS evidence.
- [ ] SHOULD failures documented.
- [ ] Documentation-drift section completed.
- [ ] README/reports/diagrams/contracts aligned.
- [ ] Publication workflow green.
- [ ] Public Pages verified.
- [ ] Final SHA recorded.
- [ ] If any MUST fails: status remains NOT DONE.
