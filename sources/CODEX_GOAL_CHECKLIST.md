# CODEX_GOAL_CHECKLIST.md

Operational checklist only. `PROJECT_PLAN.md` and `SUCCESS_CRITERIA.md` remain normative.

## Start
- [x] Read HANDOFF -> PROJECT_PLAN -> SUCCESS_CRITERIA -> this checklist -> README/research/publication docs.
- [x] Inspect current code/tests/contracts/ADRs and GOAL_PROGRESS.
- [x] Establish current PASS/FAIL/unknown status for every MUST.
- [x] Check documentation drift before changing code.

## Contracts
- [x] Versioned typed domain schemas.
- [x] Stable IDs, correlation/causation IDs, UTC timestamps.
- [x] Units/coordinate frames/calibration metadata where relevant.
- [x] OpenAPI/event contracts validate.
- [x] Order and command idempotency semantics implemented.

## Workflow
- [x] Central job transition guard.
- [x] Durable audit events.
- [x] Safe job claim/concurrency.
- [x] Timeout != failure.
- [x] UNKNOWN_OUTCOME + RECONCILING implemented.
- [x] Restart never blindly replays uncertain side effects.

## Brain / action validation
- [x] Deterministic local Brain is mandatory path.
- [x] Strict schema validation.
- [x] Invalid/timeout Brain cannot reach effect.
- [x] Optional model adapter cannot block CI.
- [x] No arbitrary model-generated execution code.

## Cell / robot gateway
- [x] Cell states and logical interlocks.
- [x] Controller command journal.
- [x] Duplicate command suppression.
- [x] Same command ID + changed payload rejected.
- [x] Required deterministic fault injections.

## Blender
- [x] Stable scene/object identities.
- [x] Bounded runtime adapter.
- [x] Deterministic reset/query/pick.
- [x] DROP_ACK_AFTER_EFFECT supported.
- [x] Screenshot/artifact available.
- [x] Runtime does not require unrestricted MCP.
- [x] Docs preserve synthetic/non-safety boundary.

## Observation / verification
- [x] Ground truth separated from observation.
- [x] Degradation fixtures implemented.
- [x] VERIFIED_SUCCESS / VERIFIED_FAILURE / INCONCLUSIVE.
- [x] Low confidence/contradiction never fabricates success.

## Reconciliation
- [x] Lost ack after effect -> UNKNOWN_OUTCOME.
- [x] Query original command identity.
- [x] Fresh observation.
- [x] Proven existing effect -> COMPLETED.
- [x] Exactly one pick effect.
- [x] Ambiguous -> intervention/unknown.
- [x] Restart version of critical scenario passes.
- [x] Explicit re-observation after intervention retains every assessment and the original command; no new pick (ADR 0008).

## Observability
- [x] Structured causal event logs.
- [x] Order/job/command correlation.
- [x] State transitions visible.
- [x] Latency + outcome/reconciliation/duplicate/fault metrics.
- [x] UI timeline explains demo.

## Tests/gates
- [x] Unit.
- [x] Contract.
- [x] Integration.
- [x] E2E fixtures from SUCCESS_CRITERIA.
- [x] Full deterministic suite one command.
- [x] Full suite passes twice cleanly.
- [x] Lint/format.
- [x] Typecheck.
- [x] Dependency/security gate.
- [x] No mandatory external LLM/API/GPU.

## Knowledge-base synchronization
- [x] Identify implementation/source/status changes that invalidate docs.
- [x] Update all affected normative/operational/public source files together.
- [x] Preserve provenance categories.
- [x] Update diagrams for architecture/state/recovery/trust changes.
- [x] README has current commands, paths, status and no stale counts.
- [x] Validate links, referenced paths, criterion IDs and contract references.
- [x] Build publication from source; never edit generated Pages/PDF manually.
- [x] Record drift and synchronization in GOAL_PROGRESS.

## Final acceptance
- [x] Generate ACCEPTANCE_REPORT.md.
- [ ] Every MUST has inspectable PASS evidence for the current release; exact-commit remote gates are pending.
- [x] SHOULD failures documented.
- [x] Documentation-drift section completed.
- [x] README/reports/diagrams/contracts aligned.
- [ ] Publication workflow green for the current local extension (earlier release evidence is retained).
- [ ] Public Pages verified for the current release (publication now authorized; final-SHA checks pending).
- [ ] Final release SHA verified by CI and public build.json (prior audited SHAs remain recorded).
- [x] If any MUST fails: status remains NOT DONE.

Local and remote evidence is indexed by ACCEPTANCE_REPORT.md. Final source/evidence successors are rechecked by CI and publication as documented in ADR 0002. This checklist is not proof by itself.

## Local guided workflow milestone (ADR 0009)
- [x] Dark theme and state-derived Prepare / Run / Review / Continue guidance.
- [x] Direct attention to original-job review; evidence and observation controls together.
- [x] UI action, no-ground-truth assessment and confined asset contract regressions.
- [x] Final isolated browser/native checks, unchanged user history and local acceptance: 389 tests twice, 99 UI checks, all local gates pass.
- [ ] Remote CI/Pages verification for these changes (publication now authorized; checks pending).

## Local selector explanations
- [x] Define every execution scenario and observation mode, its stage and key difference.
- [x] Compare options in the same window; distinguish new-order faults from review captures.
- [x] Verify selectors/comparisons do not execute work or resolve uncertainty (101 UI checks).
- [x] Complete affected-suite/browser evidence (170 Python tests, all 15 real-browser choices) and regenerate local publication.
