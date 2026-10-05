# CODEX_GOAL_CHECKLIST.md

Operational checklist only. `PROJECT_PLAN.md` and `SUCCESS_CRITERIA.md` remain normative.

## Investigation workflow revision

- [x] Archive clean baseline `0db6168` and earlier acceptance without relabelling it.
- [x] Inspect real UI, evidence contracts, scenario semantics and browser tooling.
- [x] Implement short run guidance and explicit attention-to-investigation navigation.
- [x] Separate symptom, record findings, limits and hypotheses; preserve exact observation IDs.
- [x] Keep evidence/manual access direct and the event timeline collapsed/bounded.
- [x] Preserve test/job/replay context; fix slow-planning selection and snapshot request races.
- [x] Exercise real browser normal/fault/evidence/download/return/archive journeys in both runtimes and viewports.
- [x] Complete visual clarity assessment and archive screenshots/results with source provenance.
- [x] Pass all 118 MUSTs through repeated clean suites and exact-SHA CI/publication for audited source `7b9f0a6`.
- [x] Finalize that source's acceptance, documentation drift scan and Pages/PDF verification.

[Current acceptance](docs/evidence/acceptance/20261005T014537/manifest.json) and
[independent CI/browser/publication evidence](docs/evidence/investigation-ui-final/README.md)
retain the exact source and original artifacts. The first attempt's stale UI-label
failure remains archived. An evidence/status successor receives its own complete
CI and deployed build attestation under ADR 0002; this checklist does not relabel
the 7b9 results as evidence for a later SHA.

## Accepted cell selection and test-data lifecycle revision

The accepted HKM revision below is historical evidence. ADR 0011 adds UI/API
lifecycle behavior; its verification does not inherit earlier PASS results.
The original 110 MUST criteria remain unchanged.

All 110 MUST criteria pass for clean source
`b1c374ae76144309cc4476392dec681292f0e3a7` in the
[refreshed acceptance manifest](docs/evidence/acceptance/20261004T204452/manifest.json).
[Exact-source CI and publication evidence](docs/evidence/test-management-final/README.md)
preserves the independent remote results. Any evidence/status successor still
requires its own exact-SHA CI and deployed-publication checks under ADR 0002.

- [x] Expose typed cell-profile metadata; only HKM is selectable for new tests.
- [x] Persist the selected profile and keep legacy history readable.
- [x] Confirm selected-test deletion and snapshot-bound clear-all in the UI.
- [x] Preserve retry/tombstone semantics, reject busy work and confine cleanup.
- [x] Verify no-active-test restart and no automatic archival promotion.
- [x] Test cancellation, stale requests and unchanged surviving evidence using disposable data.
- [x] Synchronize contracts, ADR, operator docs, reports and architecture diagram.
- [x] Complete affected tests, full acceptance and source-specific publication gates.

## Historical accepted HKM-inspired revision

The HKM-inspired revision adds 25 MUST criteria to the original 85. All 110
criteria passed for audited source `ca7798798f916c8130e1833cf16b4d4d3f10d546`, including
clean repeated suites, browser review and exact-source remote/public-link evidence.
The historical checklist below retains the prior release's scope; this checklist
is not proof by itself.

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
- [x] Re-run every original and new mandatory test twice on the final revision.
- [x] Prove original-command journal plus fresh observation resolves one transfer; contradictory evidence remains intervention.
- [x] Prove verifier/reconciliation cannot read hidden WorldState and replay cannot mutate runtime.
- [x] Implement HKM-P3 status/tool reasoning/evidence/camera controls and simulation boundaries.
- [x] Complete final actual-browser review of the implemented HKM workflow.
- [x] Synchronize implemented schemas, diagrams, generated catalogue docs, research sources and README.
- [x] Run final clean suites twice, quality/security gates and all Blender demos including showcase.
- [x] Regenerate acceptance, Pages and PDFs; obtain all 110 MUST PASS with exact-SHA remote/public-link evidence.

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
