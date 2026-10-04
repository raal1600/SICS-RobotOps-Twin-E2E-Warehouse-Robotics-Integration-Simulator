# CODEX_GOAL_CHECKLIST.md

Operational checklist only. `PROJECT_PLAN.md` and `SUCCESS_CRITERIA.md` remain normative.

## Active HKM-inspired revision — NOT DONE

The completed items below this section describe the previous audited release,
not acceptance of the new scene/tool revision. All 85 original MUSTs remain;
25 additional HKM MUSTs require new evidence. Checked implementation items below
have targeted evidence; they do not imply full-revision acceptance. The final
clean repeated suite, visual review and exact-SHA remote gates remain open.

- [x] Record actual clean baseline HEAD eaf35b499e80a5ce31b2ea3a24fbfa010bc67c98.
- [x] Archive exact previous and baseline reports with hashes; preserve historical release evidence.
- [x] Execute setup/security/full suite twice/lint/types/seven Blender demos/drift/publication baseline.
- [x] Record repeated baseline failure honestly: obsolete snapshot label, 388/389 passed each run, 89.11% coverage; 101 UI checks passed.
- [x] Publish enhancement-in-progress status and 25 stable new criterion IDs; retain unchanged old85.
- [x] Correct obsolete label assertion with collapsed-details behavior coverage.
- [x] HKM-P0: original procedural links/cell/cameras, shared quaternion transforms and explicit legacy playback compatibility.
- [x] HKM-P1: six products/tools, canonical matrix, persisted selection/occupancy and visible journaled tool changes.
- [x] Validate workspace, calibration and conservative collision preflight with negative tests.
- [x] Run the six-tool showcase in actual Blender and inspect product attachment/release.
- [x] Add HKM-P2 deterministic/negative contracts/scenarios and targeted uncertainty/idempotency/race/restart evidence.
- [ ] Re-run every original and new mandatory test twice on the final revision.
- [x] Prove original-command journal plus fresh observation resolves one transfer; contradictory evidence remains intervention.
- [x] Prove verifier/reconciliation cannot read hidden WorldState and replay cannot mutate runtime.
- [x] Implement HKM-P3 status/tool reasoning/evidence/camera controls and simulation boundaries.
- [ ] Complete final actual-browser review of the implemented HKM workflow.
- [ ] Synchronize implemented schemas, diagrams, generated catalogue docs, research sources and README.
- [ ] Run final clean suites twice, quality/security gates and all Blender demos including showcase.
- [ ] Regenerate acceptance, Pages and PDFs; obtain all110 MUST PASS with exact-SHA remote/public-link evidence.

Baseline and implemented revision are recorded in [GOAL_PROGRESS.md](GOAL_PROGRESS.md),
[ADR 0010](docs/adr/0010-hkm-inspired-versioned-cell.md) and
[archive provenance](docs/evidence/hkm-baseline-eaf35b4/provenance.json).

## Historical implementation checklist

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
- [x] Every MUST has inspectable PASS evidence for audited source 59ace31; evidence successors receive independent exact-SHA checks.
- [x] SHOULD failures documented.
- [x] Documentation-drift section completed.
- [x] README/reports/diagrams/contracts aligned.
- [x] Publication workflow green for audited source 59ace31; its evidence is retained.
- [x] Public Pages verified for audited source 59ace31, including 18 HTML/PDF/diagram responses.
- [x] Audited release SHA recorded and verified; the final evidence successor is attested by its own CI artifact and public build.json (ADR 0002).
- [x] If any MUST fails: status remains NOT DONE.

Local and remote evidence is indexed by ACCEPTANCE_REPORT.md. Final source/evidence successors are rechecked by CI and publication as documented in ADR 0002. This checklist is not proof by itself.

## Local guided workflow milestone (ADR 0009)
- [x] Dark theme and state-derived Prepare / Run / Review / Continue guidance.
- [x] Direct attention to original-job review; evidence and observation controls together.
- [x] UI action, no-ground-truth assessment and confined asset contract regressions.
- [x] Final isolated browser/native checks, unchanged user history and local acceptance: 389 tests twice, 99 UI checks, all local gates pass.
- [x] Remote CI/Pages verification for audited source 59ace31; final evidence successor checks remain mandatory.

## Local selector explanations
- [x] Define every execution scenario and observation mode, its stage and key difference.
- [x] Compare options in the same window; distinguish new-order faults from review captures.
- [x] Verify selectors/comparisons do not execute work or resolve uncertainty (101 UI checks).
- [x] Complete affected-suite/browser evidence (170 Python tests, all 15 real-browser choices) and regenerate local publication.
