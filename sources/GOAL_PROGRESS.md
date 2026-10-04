# Goal Progress
Last updated: 2026-10-04 UTC
Previously released audited implementation: `488db3efc124901ad57b20f7aaa4e472c7314b9f`.

## Current phase: HKM-P2/P3 final verification and knowledge-base synchronization

Enhancement base/current HEAD:
`eaf35b499e80a5ce31b2ea3a24fbfa010bc67c98` (clean before baseline execution;
current enhancement worktree is uncommitted).
The HKM-inspired six-tool/six-SKU adaptation is **NOT DONE**. It is a new
implementation/acceptance revision, not a reinterpretation of the prior release.

Implemented: canonical typed six-product/tool catalogue, deterministic selection
with persisted candidate reasons, segmented workspace/collision preflight,
original articulated shared geometry, schema-2 world/tool/observation/plan/command
and quaternion recording contracts, persisted profile settings, and explicit
schema-1 compatibility. The bounded Blender runtime executes tool preparation,
product attachment, transfer and release. Browser replay consumes evaluated
transforms and retains read-only historical delivery playback. Status/tool/evidence
inspectors, camera controls and the six-tool showcase are implemented. The static
snapshot remains inside collapsed Technical details.

Targeted evidence includes 12 actual Blender tests passing together, with all six
preferred tools, six transfers, exact-one-effect lost-ack/restart recovery,
contradictory/fresh reconciliation, corruption defenses and immutable saved-scene
re-export. See [scoped Blender/native evidence](docs/evidence/hkm-blender-local/result.json)
and its preserved failure/fix provenance. These checks do not attest later source
changes. The affected robotics/Brain/contract/E2E regression run passed 112 tests
(`artifacts/hkm-baseline-eaf35b4/robotics-brain-regressions.xml`); 22 targeted
contract/governance/documentation/Brain checks also passed. The Node UI suite now
has 105 passing checks (`artifacts/hkm-ui-tests.log` retains the follow-up run).
Full repeated acceptance is still required.

Final pre-commit checks: 112 schema, legacy-hash, boundary and timeout-diagnostic
tests passed; lint/strict types/security passed. The final camera-framing suite
has 107 passing UI checks (`artifacts/hkm-ui-camera-final.log`). Actual browser
execution completed a six-product delivery, then a separate lost-ack pick moved
through UNKNOWN_OUTCOME, contradictory intervention and fresh-observation
completion without another command. Independent SQLite audits and screenshots
are retained under `docs/evidence/hkm-browser-local/`. A coordinated request/response
tampering regression preserves durable inventory and imports zero effects.
The publication preflight built all reports, diagrams and PDFs successfully.
These remain scoped development checks; the next milestone is a clean-commit
full acceptance run twice, eight Blender demos, then exact-SHA CI/Pages evidence.

The security gate passed with zero dependency advisories and valid vendored
asset hashes; its five existing low-severity subprocess scopes remain explicitly
reviewed. Only the changed demo function's AST fingerprint was refreshed; no new
exception class or reduced threshold was introduced. The formal MUST verdicts,
full-suite count/coverage and final source SHA remain the acceptance runner's
responsibility. Current-SHA CI, publication, public links and final visual review
are still pending.

New decisions: schema-1 serialization omits all absent schema-2 extensions so
original durable payload hashes remain unchanged; fresh worlds persist their
execution settings, while archived worlds retain their original profile. API
serialization schemas must remain typed and reject unknown fields. Tool geometry
and static-obstacle bounds share the same procedural definition; fork/pouch
fixtures use visible support skids where the tool needs clearance. These are
original simulator-design choices, not manufacturer geometry or capabilities.

Baseline `uv run --locked python -m tools.dev acceptance --local` ran the mandatory
suite twice without modifying source: 389 tests each, 388 passed and one failed
in each run, zero skips; coverage 89.11000552791597%. The failure is the obsolete
`Latest Blender artifact` label assertion in
`test_metrics_timeline_and_dashboard_survive_restart`, after the approved compact
snapshot presentation changed that label. The current revision corrects that assertion with meaningful collapsed-details
coverage while preserving the journal/metrics/restart assertions. The original
failed baseline evidence remains archived unchanged.
All 101 Node UI checks, setup, lint, typecheck, security, seven actual Blender
demos, drift and both local publication builds passed. Lost-ack/restart demos
each retained one transfer; contradictory reconciliation remained intervention.
Environment: Python 3.13.15, Blender 5.2.1 LTS, Node 20.17.0, uv 0.12.13.

Baseline MUST PASS: SC-TEST-004, SC-TEST-005, SC-TEST-006, SC-KB-009,
SC-ACC-005, SC-DOC-003, SC-DOC-004 and SC-DOC-005. Other baseline criteria
fail their shared full-suite/repeatability gates or lack current-SHA remote
evidence; this does not mean 77 distinct behavior failures. The original 85 MUSTs
remain unchanged. HKM-VIS-MUST-001 through HKM-VIS-MUST-025 are in progress,
with FAIL/pending acceptance until their implementation and inspectable evidence
exist. Optional provider fallback remains the documented SC-BRAIN-005 SHOULD gap.

Evidence: [clean baseline manifest](docs/evidence/acceptance/20261004T000708/manifest.json),
[summary](docs/evidence/hkm-baseline-eaf35b4/baseline-result.json) and
[immutable report/provenance archive](docs/evidence/hkm-baseline-eaf35b4/provenance.json).
Old acceptance files were not overwritten; exact before/baseline reports are
retained as text archives with hashes. No saved user test or active app was touched.

Decisions: extend the bounded adapter and shared procedural scene; make the
TCP-driven visual kinematics explicit; persist tool preparation under the original
pick identity; retain product-transfer effect counts and observation-only
verification. Version new recordings/contracts explicitly and preserve old scene,
payload/journal and replay interpretations. No imported HKM CAD or guessed true
robot/controller geometry. [ADR 0010](docs/adr/0010-hkm-inspired-versioned-cell.md)
records the accepted design; [implementation scope](docs/implementation/hkm-inspired.md)
describes implemented runtime features with scoped evidence while retaining
pending final acceptance.

Drift detected: unconditional DONE referred to the previous audited release, and
the UI follow-up left an old wording assertion. Synchronized plan, success criteria,
handoff, checklist, README, report status blocks, publication status/policy,
acceptance map/report, new ADR/design guide and criterion/status tooling. New
criterion IDs are included in drift and completion checks; status dates now use
UTC rather than a fixed past date. Research provenance and generated catalogue/
diagram synchronization remain part of the implementation milestones. Generated
Pages/PDFs must be rebuilt after the coherent source milestone, never hand-edited.

Governance follow-up: nine targeted tests, scoped Ruff lint/format and strict
drift pass; all 85 original MUST definitions are byte-equivalent as text to the
base definitions. Negative tests reject unknown/missing HKM criteria and prevent
DONE with even one new criterion failing. [Scoped evidence](docs/evidence/hkm-governance/result.json)
does not attest runtime enhancement completion. Pending test names in the
acceptance map must be replaced/refined against implemented tests and artifacts.

Next milestone: complete final browser review, run the complete clean mandatory suite twice and
all eight Blender demos, then regenerate acceptance and publication. Verify the
exact final commit in CI/Pages; do not promote scoped results to final acceptance.

Final source synchronization replaces stale planned-feature descriptions with
implemented HKM geometry, six-tool selection/preparation, schema-2 contracts and
read-only replay, without changing generated status blocks or formal acceptance
verdicts. Updated README, plan, handoff, checklist, runtime/contracts/persistence/
operations/acceptance documentation and design/scope reports. Historical baseline
and failure evidence remain unchanged. The host and fixed Blender source-contact
checks now share the 5 mm simulator centering bound; the coordinated 1 mm noise
probe completed in actual Blender and targeted runtime checks passed. That bound
is separate from verifier pose tolerance and is not real gripper accuracy.

API/default-profile follow-up: fresh API/desktop worlds and Start new test now use
the six-SKU HKM profile; reopened originals and archives keep their own saved
settings. Fixture metadata supplies every product's source and the actual
destination plus the canonical catalogue. New intake rejects invalid fixture
identities before creating jobs while retaining replay/conflict semantics.
Targeted checks passed: 11 API/profile regressions and 102 scenario/history/desktop
backend checks, scoped Ruff/mypy and strict drift. Six HTTP orders selected all
six preferred tools with one transfer each. Legacy and fresh desktop backends
both preserved original command identity and one effect after close/reopen.
[Scoped evidence](docs/evidence/hkm-api/result.json) records commands and exclusions;
these checks do not replace actual Blender/native-window/final acceptance checks.
Synchronized README, plan, handoff and contracts/operations/desktop/adaptation
guides. The desktop smoke script now derives SKU/source IDs from the fixture.

Actual Blender follow-up: all 12 tests in `tests/blender/test_hkm_runtime.py`
pass in one run (124.38 s, no skips/xfails). Six SKUs use six preferred tools and
produce six transfers, one per original command. Every sampled carrying/rack
pose is checked within 1e-6; link rotations, tool exchange, attachment/release,
final checkpoint poses, actual camera metadata and A-F labels are inspected.
Lost-ack/restart/contradiction and later reconciliation preserve one command/effect.
Saved-scene re-export preserves transforms and leaves world/journal/timeline and
the original scene hash unchanged. Eight malformed requests fail in actual Blender
before scene/motion/effect creation. An initial floating-point rack residual and
a later strict dock-pose comparison regression were fixed in production; neither
assertion nor tolerance was weakened. Both failures remain archived alongside
the passing suite in [scoped evidence](docs/evidence/hkm-blender-local/result.json).
The native host rebuilt without installation; its isolated Blender lifecycle
smoke passed eight checks, including graceful in-flight close, lost-ack recovery
and forced owned-process-tree cleanup. No active user app/data was touched.
Runtime/adaptation documentation now distinguishes legacy Cartesian evidence from
schema-2 articulated transforms, tools, cameras and original synthetic open totes.
Full repeated acceptance and final source-SHA publication gates remain pending.

## Previous phase: P7 compact snapshot presentation follow-up
Base: `5db9bf973026fd111adc97885cfb1080060a25c5` (published and verified).
The saved Blender snapshot is now under **Technical details**, collapsed by
default. The full 3D cell/replay stays primary. This is a native HTML disclosure;
snapshot generation, API, workflow, verification and saved user data are unchanged.
All 101 existing UI checks pass. An isolated real-Blender happy path confirms the
image loads without opening the disclosure; keyboard expansion/collapse and
390 px layout pass. The order completes with exactly one effect.
[Scoped evidence](docs/evidence/technical-details-local.json) retains the checks
and screenshots. README, operations/playback guides and the acceptance report
describe the new placement. Architecture, contracts, diagrams and research claims
do not change. The release evidence below remains its own audited snapshot.
Documentation checks are recorded with the scoped evidence. Next: user testing of
the compact disclosure; the earlier release gates retain their original scope.

## Previous verified release: P7 guided simulation workspace
Audited source: `59ace317d949cc8e6fbd77db13a10656737d9238`, clean checkout.
The user's publication authorization supersedes the earlier local-only scope.
All 85 MUST criteria PASS with inspectable evidence from GitHub CI and Pages.
389 mandatory tests pass twice without skips/xfails; all 101 UI checks pass in
each suite. Coverage is 89.22%, above the unchanged 85% floor. Setup, security,
lint/format, types, seven real Blender demos, drift and publication pass.
Windows native launch/duplicate launch/close/restart checks also pass.
Lost acknowledgement after effect and restart retain exactly one pick;
ambiguous evidence does not fabricate success.

Evidence: [audited manifest](docs/evidence/acceptance/20261003T220839/manifest.json),
[release provenance](docs/evidence/workspace-release.json) and ACCEPTANCE_REPORT.md.
The original local CI manifest is preserved; remote refresh adds same-source
workflow and public-link evidence without relabelling any test result.
SHOULD SC-BRAIN-005 remains unimplemented (optional model-provider fallback).
The OPTIONAL model/hardware/real-ERP backlog remains non-blocking.

Drift detected: the current status still described unpublished local work.
Synchronized README, reports, publication status/policy, checklist, progress and
acceptance report with verified release evidence. The earlier local-only records
below remain historical. Source provenance, contracts and architecture diagrams
are unchanged by this evidence-only closure. Publication is rebuilt from sources.
Next: push the evidence/status successor and verify its own CI, Windows workflow
and public build.json, as required by ADR 0002. The final successor is attested by
its CI artifact and deployed manifest rather than by changing an earlier report's SHA.

## Previous verified extension: P7 scenario and observation explanations
The local follow-up replaces outcome-only help with definitions, failure stage,
key differences and expandable comparisons for every visible execution scenario
and observation mode. The UI explains new-order injection versus later evidence
collection, including similar-looking no-motion and inconclusive outcomes.
Base: 348c786710a0e22f0dd7de0744eac7057da13ad8; no commit, push or deployment.
Production workflow, faults, contracts and verification rules are unchanged.
SC-DEMO-003 follow-up: all 101 UI checks and 170 affected Python tests pass.
The isolated browser exercised all 10 execution and 5 observation selections,
compared every option and verified the desktop and 390 px layouts. Browsing help
preserved identical UNKNOWN_OUTCOME evidence, one order and one pick effect;
only an explicit normal reconciliation completed the original command.
Lint/format, strict type checks, drift scan and local publication pass. Evidence and all executed commands are
in [the scoped local record](docs/evidence/scenario-help-local.json).
The full acceptance run below remains the prior baseline, not a new whole-system
attestation. Knowledge-base synchronization covers README, report status blocks,
PROJECT_PLAN, publication status, operator/desktop/acceptance guides, the new
scenario guide, ADR 0009, acceptance mapping/report and checklist. Architecture,
diagrams, external source provenance and contracts require no change because
this follow-up only describes the existing behavior.
Next: user testing of the explained choices; remote MUSTs remain deferred under
the local-only scope. No user test data was read or changed in this follow-up.

## Previous verified extension: P7 guided dark workspace
The dark workspace provides a persistent next-step guide, scenario expectations
and readable original-command evidence beside explicit re-observation. Attention
opens and focuses review once; polling and repeat assessments retain focus.
Resolved, stopped-cell, depleted-delivery and archived states have explicit next
actions. ADR 0009 preserves the unchanged verifier, command identity, quarantine
and ground-truth boundaries. No new dependency or domain transition was introduced.
Base: 348c786710a0e22f0dd7de0744eac7057da13ad8; no commit, push or deployment.

Local acceptance: 389 tests PASS twice, zero skips/xfails, 89.33% coverage.
All 99 UI checks, setup, security, lint/format, strict types, seven real Blender
demos, drift and local publication PASS. Evidence:
`docs/evidence/acceptance/20261003T205102` and `ACCEPTANCE_REPORT.md`.
SC-DEMO-003 is explicitly extended with guide, action and confined-asset evidence.
All local MUST gates pass; SC-DATA-005, SC-KB-006/007/008 remain unverified for
these uncommitted changes under local-only scope. SHOULD SC-BRAIN-005 remains
unimplemented; optional backlog is unchanged. This is not a new DONE attestation.

[Browser/native evidence](docs/evidence/guided-workflow-local.json): real Blender
happy path; lost acknowledgement after effect; contradictory/low-confidence
reviews followed by normal evidence on the same command; continued three-product
delivery with one effect and 100 original frames per product; lost acknowledgement
before effect followed by missing/normal evidence (FAILED, zero effects); logical
stop/cell-fault reset; planning timeout/invalid output; stale evidence archived
unchanged and reviewed read-only. Inspecting evidence and choosing normal
observation left the original records identical. Desktop and 390 px layout/focus
were inspected with no horizontal overflow. Native isolated headless lifecycle
checks and all new asset requests pass. The user's open session, all 54 orders,
every assessment, fixture and delivery remain unchanged. Its UNKNOWN_OUTCOME job
was not reconciled or restarted; the new version loads on the next app reopen.

Initial targeted failures were permissions on a pre-existing Windows pytest temp
folder, resolved using a fresh local fixture root. A history-selection regression
was fixed by capturing the selected test before disabling controls. No assertion,
mandatory test or acceptance threshold was weakened.

Drift corrected: scattered-control instructions, stale UI labels and status counts.
Synchronized README, operations, desktop, playback, contracts, reconciliation,
acceptance guide/map/generator/report, PROJECT_PLAN, checklist, PUBLICATION,
report/status sources, architecture caption, generated OpenAPI, ADR 0009 and this
record. Research provenance and domain state diagrams are unchanged. Final
source-document checks/publication and application/test hash equality are recorded
in the linked evidence. Generated pages/PDFs use only the repository builder.
Next: reopen the local app once and follow Next step. Remote CI/Pages verification
remains deferred under the local-only instruction; no Git actions are pending here.

## Previous verified extension: P7 same-test re-observation
An active REQUIRES_INTERVENTION job now accepts an explicit fresh observation
through RECONCILING. It retains the original command, every assessment and the
same delivery. The unchanged verifier either resolves the outcome or pauses it
again. No new pick, fixture reset or automatic restart resolution occurs.
Base: 348c786710a0e22f0dd7de0744eac7057da13ad8; no commit, push or deployment.

Local acceptance: 389 tests PASS twice, zero skips/xfails, 89.31% coverage.
All 77 UI checks, setup, security, lint/format, strict types, seven real Blender
demos, drift and local publication PASS. Evidence:
`docs/evidence/acceptance/20261003T194506` and `ACCEPTANCE_REPORT.md`.
SC-STATE-001/003/004, SC-REC-002/004/005/007 and SC-DEMO-003 are revalidated.
All local MUST gates pass; SC-DATA-005, SC-KB-006, SC-KB-007 and SC-KB-008
remain unverified for these uncommitted changes under the local-only instruction.
This is not a new published DONE attestation. Optional backlog is unchanged.

ADR 0008 records the evidence-only return from intervention. Only COMPLETED and
FAILED remain terminal; intervention requires an explicit reconciliation claim
and stays paused across restart. Fencing and quarantine still prevent concurrent
work or blind retries. Evidence arrays now follow durable insertion order instead
of UUID sorting, preserving a correct latest assessment across repeat attempts.
Tests cover every observation degradation twice, missing journal, both lost-ack
outcomes, restart, archived write rejection, competing claims and continuation of
the same delivery. Gateway dispatch and controller delivery are distinct logged
events for the same single command; assertions check each component once.

[Browser/native evidence](docs/evidence/reobservation-local.json): five degraded
assessments stayed inconclusive, normal fresh evidence completed the original
pick, and blue/green then completed in the same test/delivery. Exactly three
pick effects and three original 100-frame clips remain, one per product.
The native app was gracefully reloaded once. Its current Test 2, all 49 orders,
observations, assessments, fixture and delivery history were verified unchanged.
Its existing intervention now offers Observe again and reconcile; no user job was
reconciled for them. Desktop and 390 px controls, plus diagrams, were inspected.

Knowledge-base drift corrected: intervention as a permanent terminal state,
inspection-only guidance, UUID evidence ordering, stale current-status counts
and the released checklist's remote claims. Synchronized PROJECT_PLAN, checklist,
README, reports/status, PUBLICATION, state/ack-loss diagrams, OpenAPI, contracts,
persistence/reconciliation/operations/desktop/playback guides, ADR 0008, acceptance
mapping/generator/report and this record. External source claims are unchanged.
Publication is rebuilt only through the existing builder. Final documentation-only
checks and application/test hash equality are recorded in the linked evidence.
Next: user continues Test 2 with Fresh observation and Observe again and reconcile.
Local implementation is ready; remote CI/Pages verification awaits authorization.

## Previous verified extension: P7 independent tests in one window
Start new test now provides the same lifecycle for every execution/observation
combination. It retains both choices, creates separate workflow/runtime storage
and archives previous outcomes and replay read-only in the same window. Running
operations finish first. Scenario selection changes configuration only; existing
restock, state-machine, idempotency and observation guards remain intact.
Base: 348c786710a0e22f0dd7de0744eac7057da13ad8; no commit, push or deployment.

Local acceptance: 382 tests PASS twice, zero skips/xfails, 89.14% coverage.
All 69 UI control checks (including 50 combinations), 91 API combinations,
setup, security, lint/format, types, seven Blender demos, drift and publication PASS.
Evidence: docs/evidence/acceptance/20261003T185730, ACCEPTANCE_REPORT.md and
[local browser/desktop evidence](docs/evidence/test-lifecycle-local.json).
All local MUST gates pass. SC-DATA-005, SC-KB-006, SC-KB-007 and SC-KB-008
remain unverified under the
user's local-only instruction; this is not a new published DONE attestation.

ADR 0007 records isolated worlds, durable catalog identity, idempotent creation,
cross-host write serialization, immutable archives and active-only recovery.
Final review caught a recovery-capable journal read in evidence presentation.
Runtime.recorded_journal now reads saved receipts only. Real Blender regressions
prove that viewing a valid pending checkpoint cannot commit it, while explicit
reconciliation still resolves the active test exactly once. The earlier 380-test
attempt predates this correction and was superseded, not used as final evidence.

Browser verification: lost acknowledgement after effect plus contradictory fresh
evidence retained one effect and intervention; before effect retained zero effects
and intervention with the same observation choice. A third test completed all
three products with 300 recorded frames. Earlier evidence/replay stayed identical.
History disabled writes, kept Start new test available and fit a 390 px viewport.
The updated desktop is open in one window. All 49 previous user orders, evidence
and replays were verified unchanged, including the prior separate reconciliation
test copied into history. Its original files remain intact.

Knowledge-base drift corrected: automatic scenario restock, separate-window
workarounds, archive recovery/read semantics and old current-status counts.
Synchronized README, reports/status, PROJECT_PLAN, PUBLICATION, architecture,
API/OpenAPI/schemas, persistence/contracts/runtime/Blender/operations/desktop/
playback/reconciliation guides, ADRs 0006/0007, acceptance mapping/generator/report
and this record. Final status/evidence documentation is rebuilt locally and checked
separately; application and test files remain identical to the two accepted runs.
Next: user review of the permanent Start new test and Test history controls.
No remaining implementation blocker for this local change; remote release awaits
an explicit change to the local-only instruction.

## Previous verified extension: P7 local next-pick guidance
User reported that another product did nothing after a lost acknowledgement.
Read-only inspection found green UNKNOWN_OUTCOME, one durable pick effect and
no second order. The cell quarantine is correct; the UI did not make the next
step prominent. Added a named blocking-product prompt and reconciliation action
beside Run, plus intervention inspection. Existing API/state/verification rules
are unchanged. Local acceptance: 277 tests PASS twice, zero skips/xfails, 87.90% coverage;
18 UI control checks, setup, security, lint/format, type checking, seven Blender
demos, drift and local publication PASS. Evidence is in
`docs/evidence/acceptance/20261003T172709`, `ACCEPTANCE_REPORT.md`, and
`docs/evidence/ack-guidance-local.json`. The same four remote-gate MUSTs remain
unverified because the user requested local changes only.

Actual browser checks with isolated Blender fixtures: green moved once, normal
reconciliation completed its original command without creating another order,
then red ran and entered UNKNOWN_OUTCOME under the same fault. Contradictory
fresh evidence required intervention and kept the next pick blocked. A read-only
check of the user session also showed the named blocking-product prompt.
The user continued testing; no user job was changed or application restarted.
Reopen after the current test to load the updated UI.

Knowledge-base sync: README, reports shared status, operations, desktop, playback,
reconciliation guide, ADR 0006 clarification, acceptance generator/report and
this record. This changes UI guidance only; API, architecture and state-machine
contracts are unchanged. Generated publication rebuilt locally only.
Next: user review. No commit or push requested.

## Previous verified extension: P7 local delivery replay
User confirmed happy path works, then found that changing scenarios left an
exhausted fixture and Replay covered only the last product. Scenario changes now
prepare fresh products through the existing guarded operation. Full delivery is
the default replay scope and includes every original product clip in durable
execution order. Saved deliveries and individual execution details remain
available. Active or uncertain jobs still block preparation and new dispatch.
Base: 348c786710a0e22f0dd7de0744eac7057da13ad8, intentionally uncommitted.

Local acceptance: 277 tests PASS twice, zero skips/xfails, 87.90% coverage.
Setup, security, lint/format, strict typing, all seven Blender demos, drift and
local publication PASS. Evidence: `docs/evidence/acceptance/20261003T132825` and
`ACCEPTANCE_REPORT.md`. The four remote-gate MUSTs remain unverified for this
local change at the user's request; no new published DONE claim is made.

Browser evidence: `docs/evidence/delivery-replay-local.json`. Actual Replay at
2x traversed red, blue and green in the user's saved delivery (300 Blender
frames), and three new UI runs formed another full delivery in an isolated copy.
Changing to logical E-stop restored all three products without creating an
order; running it then produced a rejected command with zero effects. Saved
delivery playback and orders remained unchanged. Fourteen dashboard/playback
control tests also cover exhausted-fixture continuation, legacy individual
selection, partial clips, paused cursors and unresolved-outcome guards.

The actual desktop was gracefully reopened with the new source. All 30 user
orders and the completed scene remain unchanged; the default full replay has
three completed clips. No fixture reset was applied to the user's saved delivery.

ADR 0006 defines scene-epoch grouping as presentation only, with no merged
business orders or new physical commands. Drift corrected: single-product replay
and manual-only scene preparation descriptions. Synchronized README, reports'
shared status, PROJECT_PLAN, architecture caption, API/OpenAPI and schemas,
operations/desktop/playback/contracts guides, acceptance generator/report and
this progress record. Publication is rebuilt locally; public Pages retains the
earlier released source. Final documentation-only checks are recorded in
`docs/evidence/delivery-replay-local.json`.

Next: user review in the open desktop app. No commit or push requested.

## Previous local correction
User requested local changes only: no commit, push or publication. Base remains
348c786710a0e22f0dd7de0744eac7057da13ad8; working source is intentionally dirty.
Reported SOURCE_NOT_OBSERVED reproduced from the user's persisted scene: all
three fixture products were already at destination. Added explicit guarded
fresh-scene preparation, current availability and specific rejection messages.
Source validation and uncertain-outcome rules are unchanged. ADR 0005 records
durable reset identity, exclusive maintenance and crash recovery.

Local verification: 265 tests PASS twice, zero failures/skips/xfails, 87.83%
coverage; setup, lint/format, strict typing, security, all seven Blender demos,
drift and local publication builds PASS. Evidence is in
`docs/evidence/acceptance/20261003T123412` and `ACCEPTANCE_REPORT.md`.
Four MUSTs involving remote gates are unverified for this local change by user request;
this is a verified local correction, not a new published DONE attestation.

Browser evidence: `docs/evidence/happy-path-local.json` and screenshots under
`artifacts/happy-path-fix`. A copy of the depleted user scene completed all three
products through actual UI buttons, streamed approach/lift/transfer/detach poses,
then completed another red pick after fresh-scene preparation. Saved replays,
old-command suppression, restart and reset/intake races have regression coverage.
The actual desktop was gracefully reloaded and prepared with all three products
at source; its 27 previous orders remain byte-for-byte unchanged through the API.

Knowledge-base sync: README, reports' shared status, PROJECT_PLAN, runtime/API,
operations, playback and desktop guides, architecture caption, OpenAPI, ADR 0005,
acceptance generator/report and this record. A stale runtime implementation
future-tense sentence was also corrected. Generated publication was rebuilt
locally only. Public Pages still represents the earlier released source.

Next: user tests Happy path in the open local app. Repeating a picked product
uses Start fresh scene; no Git commit/push until requested.

## Previous released phase
P5/P7 extension complete: full 3D cell, moving machine/product poses and scenario
replay for every execution outcome. All 85 MUSTs pass for the audited clean
source with local and exact-SHA remote evidence. Final evidence/status successors
receive fresh CI artifacts and public build.json attestation (ADR 0002).

## MUST status
Both clean suites: 254 PASS, zero skips/xfails, 87.35% coverage (85% minimum).
Setup, lint/format, strict typing, Python/npm security, seven real Blender demos,
drift scan and publication pass. Exact-source workflows: core 37120767979,
Windows 37120767929 and publication 37120767978 all SUCCESS. Public Pages exposes
the matching source SHA, 22 references and seven synchronized diagrams.
SHOULD SC-BRAIN-005 remains non-blocking; optional model/hardware work is unchanged.

## Evidence
- docs/evidence/acceptance/20261003T114649: clean manifest, two complete suites,
  all gate logs/demos and verified remote status; ACCEPTANCE_REPORT.md maps all
  85 MUSTs to inspectable evidence and names the tested source.
- docs/evidence/3d-scenarios.json and 3d-{webgl,software,mobile}.png: actual browser
  rendering, fixed/no-effect scenes, replay/scrub, mobile layout and exactly-one
  pick despite ambiguous reconciliation.
- docs/evidence/3d-desktop.json: all eight native/real-Blender lifecycle checks,
  including normal close during a pick and termination of owned children on crash.
- Tests cover the complete fault matrix, saved scenes after later orders/restart,
  every carrying-frame offset, partial/corrupt recordings, read-only legacy import,
  no replay dispatch, offline asset integrity and Windows sharing-lock retries.
- One development run exposed a transient Windows reader/rename race (fixed).
  Another encountered an eleven-hour host pause and failed existing deadlines;
  that result was rejected and rerun without weakening runtime timeouts/assertions.

## Decisions / ADRs
ADR 0004 extends ADR 0003: presentation snapshots and audit-event playback,
shared stylized gantry geometry, offline Three.js with software perspective
fallback, and explicit legacy-reference provenance. No presentation data enters
Brain, ObservationModel or Verifier. No state-machine or MUST changes.
Native drain budgets now match the existing 60-second runtime deadline: 65 s
server, 70 s owner, 75 s test observation. Measured valid paced picks exceeded the
old 15-second drain; completion/effect assertions are retained. Idle shutdown is
prompt. Rendering redraws only changed poses/camera/size.
The updated versioned EXE is installed and the desktop shortcut points to it.
An open older app and all user data remain untouched; close/reopen the shortcut.

## Knowledge-base synchronization
Drift found and corrected: motion-only/Canvas-only descriptions, missing static
scenario history, persistence future tense, damaged Swedish characters and the
old native drain/install descriptions. Synchronized README, PROJECT_PLAN,
PUBLICATION, report 01 and the shared status in reports 01-03, registry S22,
architecture, schemas/OpenAPI, all affected
implementation guides, scene README, ADRs 0003/0004, acceptance map/generator and
this record. Publication is generated only from source; 181 PDF destinations
validate. Existing external company claims retain their original provenance.

## Release evidence
The committed report attests its audited source, not its own future commit hash.
The final evidence successor must have all three workflows green and matching
Pages build.json before delivery. Optional model/hardware integration remains
explicitly non-blocking. No unresolved implementation or knowledge-base drift
remains; final exact-SHA CI artifacts are the release attestation.
