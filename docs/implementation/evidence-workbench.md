# Evidence-centered E2E engineering workbench

The guided console now follows one persisted order through execution, investigation
and recovery without requiring raw JSON as the starting point. **Execution now**
stays attached to the backend's current stage and permitted action. **Inspecting**
can remain on an older result while execution advances. **Follow current** returns
to the latest saved result and clears navigation filters.

This is a locally implemented and verified enhancement to research baseline
`26d7aac9774d4f014e70da872dd4045d94428748`, on `feat/integration-lab`. These changes
have not been committed, pushed or deployed. Historical release/CI acceptance in
the repository does not attest this worktree. The [review pack](../evidence/workbench-20261007/README.md)
contains screenshots, scenario snapshots, validation records and source hashes.

The subsequent [Source-view correction](../evidence/source-view-20261007/README.md)
adds readable saved Python and a read-only full-current-file view. It has its own
test results and source hashes; the original workbench pack below remains evidence
for the earlier review snapshot.

## Product behavior

The eight-phase journey filters the chronological trace. Search, component,
protocol, status and engineering-perspective filters all operate on the same saved
run. Trace entries show attempt numbers and available delivery/redelivery evidence;
execution and inspection have separate markers. Filtering does not hide the
persistent execution context or change the backend workflow.

The inspector presents meaning, responsibility and classification, important input
identities, state changes, persistence, supporting records, proof limits, invariants
and recovery before the technical record. Data, State, Protocol, Source, Recovery
and Raw JSON preserve the technical depth. Protocol records are explicitly
structured adapter request/results, not packet captures. Stage/job links open the
existing investigation dialog and its evidence, timeline and manual-inspection
export instead of introducing another inspection system.

The proof ladder separates business intent, durable workflow, broker publication,
edge processing, controller acceptance, execution result, post-action observation,
verification, WMS acknowledgement and ERP completion. Every established or failed
claim links to a saved step and output field. Missing records remain unproven;
in-process publication is explicitly simulated. Completing a stage or the whole
journey does not turn an unsuccessful outcome into a success.

The existing 3D viewer is docked beside the investigation on wide screens and below
it on smaller screens. Its current command, recording availability and read-only
replay status remain explicit. Changing execution stages no longer scrolls the
page to and from a separate robot section. Background refresh retains the selected
run's original job and rejects stale replay responses. Desktop execution context
is sticky; at 390px, a compact sticky strip retains order, both cursors, original
command and Follow current.

Physical authorization states that approving immediately requests the original
command once. It remains an application control, not a certified safety function.
Uncertain outcomes show known/not-yet-proven evidence, **Do not retry the pick**, and
**Reconcile original command**. WMS failure retains physical proof and offers only
the business acknowledgement retry. Both recovery explanations say what the action
will do before it is invoked.

## Files and contracts

| Component | Changed files | Purpose |
| --- | --- | --- |
| Console and presentation | `apps/erp_ui/integration-console.js`, `index.html`, `theme.css` | Two cursors, meaningful inspector, proof ladder, phase/filter navigation, recovery, robot dock, responsive context and download |
| Existing app integration | `apps/erp_ui/app.js` | Reuse investigation; retain original-job replay through history/refresh; avoid duplicate guidance and automatic page hopping |
| Backend presentation | `robotops/integration/presentation.py` (new) | Sanitized, deterministic explanations and proof predicates derived from saved steps |
| Engine and session model | `robotops/integration/engine.py`, `models.py` | Bounded action labels and read-only `workbench` projection on presented sessions |
| Read API | `apps/api/guided.py` | Saved-run JSON download |
| Generated contracts | `contracts/openapi.json`, `contracts/schemas/ExecutionSession.json` | Additive API/schema documentation |
| Tests | `tests/integration/test_workbench.py`, `tests/browser/test_workbench_console.py` (new); `tests/ui/integration-console.test.cjs`, `tests/ui/dashboard.test.cjs`, `tests/browser/test_guided_console.py`, `tests/lab/test_browser_lab.py` | Proof, cursor, recovery, replay, sanitization and browser regressions |
| Documentation/evidence | This report, `docs/implementation/investigation.md`, `docs/evidence/workbench-20261007/` | Current guide, requirement audit and reviewable evidence |

`ExecutionSession.workbench` is an optional object with a default empty value for
older sessions. Presentation version 1 supplies `status`, `proof_scope_job_id`,
`proofs` and a `stages` map keyed by saved step ID. A proof includes `key`, `label`,
`state`, `fact`, `does_not_prove`, `step_id`, `field`, `evidence_ids` and
`classification`. States are `established`, `failed`, `simulated` or `unproven`.
The engine rebuilds this projection on reads; it grants no execution authority.
No database migration or dispatch/reconciliation algorithm change is required.

`GET /integration/sessions/{session_id}/export` returns `format`, `scope` and
`session`. Format `robotops-guided-run-v1` contains a sanitized persisted-session
snapshot with stage records and evidence references. It does not embed separate
job records or motion files. It is read-only, including through existing test-scoped
routes. The existing job evidence/events export remains available in investigation.

No new protocol instrumentation was needed for Phase 1. The only backend additions
are a presentation projection, action wording and this read endpoint. No inferred
frontend field stands in for unavailable backend evidence.

## Phase 1 acceptance audit

| Priority | Implemented behavior | Authoritative evidence |
| --- | --- | --- |
| 1. Two cursors | Persistent execution context and separately pinned saved stage | Browser `test_two_cursors_actions_filters_export_and_existing_investigation`; manual A step 8 while execution moves 15 to 17 |
| 2. Follow current | Unpins, clears filters and selects latest saved result without work | UI WebSocket/pinning test; same browser test; mobile manual C |
| 3. Plain status | Human-readable status precedes internal state/revision | Backend projection and A/B/C screenshots |
| 4. Meaning before JSON | Ten overview fields precede collapsed technical record | `explain`, `inspect`; history/replay screenshot |
| 5. Proof and limits | Supporting IDs/field paths and separate limits | Backend proof tests; all stage overviews; proof item navigation |
| 6. Proof ladder | Ten independent, evidence-derived boundaries | `test_proof_ladder_does_not_infer_later_boundaries_or_real_broker`; A gate/robot/completion snapshots |
| 7. Named actions | 22 bounded labels, explicit robot gate, WMS-only retry | `ACTIONS`; physical-gate screenshot; WMS tests |
| 8. Phase navigation | Eight read-only phase filters, current/inspected/failed/uncertain markers | UI phase-navigation test; real browser navigation without POSTs |
| 9. Search/filter | Search plus status/component/protocol/perspective/attempt filters | UI filter tests; browser empty search preserves execution context |
| 10. Attempts/redelivery | Per-job/stage/component attempt counting and recorded delivery facts | UI repeated-stage test; local browser retry test; distributed duplicate-delivery case |
| 11. State changes | Before/after or explicit no-change statement; deeper State view | Backend `explain`; manual recorded-robot and mobile verification screens |
| 12. Known/unknown | Dedicated uncertainty and business-failure panels | Manual B/C snapshots and screens; backend recovery proof tests |
| 13. Robot context | Existing viewer docked with command and recording identity | Manual A recorded/replay screens; missing/mismatched replay tests; final history read check |
| 14. Reuse investigation | Selected stage's job opens existing evidence/timeline/manual views | Real browser test opens/closes the existing dialog without mutation; historical-job link unit test |
| 15. Export | Visible sanitized saved-run download and existing job export | Backend export test; actual manual `happy-export.json`; browser download/no-POST check |

## Other requirements and invariants

| Requirement | Verification and boundary |
| --- | --- |
| Compact run identity with expandable IDs | Order/scenario header, status/revision, details block, persistent original command; desktop and 390px screenshots |
| Execution action targets current backend position | UI test asserts posted current stage/revision while step 8 is pinned; browser advances to 17 with step 8 still selected |
| Explicit physical consent; inspection/replay never dispatch | Existing guided authorization/idempotency tests, no-POST browser assertions, three manual stage-16 requests for three original commands |
| Late asynchronous results cannot switch runs or authorize another run | Generation/session guards in authorization/reconciliation; late-authorization regression; stale replay response guard and history refresh regression |
| Persisted restoration and read-only stream | Existing guided read-only/stream tests, browser reload at the gate, manual reload, UI rejects old revisions while preserving pinned history |
| Interrupted physical execution | Existing recovery tests cover before/after dispatch intent and committed dispatch without result; recovery queries or renews consent, never blindly resends |
| Unknown outcome remains uncertain | Manual B has a controller success and favorable assessment but verification stays unproven until original-command reconciliation is committed |
| Physical failure is not business success | Existing business tests retain verified failures and require per-job WMS acknowledgement before ERP finalization; proof projection retains failed verdict/business result |
| WMS retry cannot execute robot work | Manual C's retry request is only stage 20; original journal effect count remains 1; backend and distributed tests cover this |
| Real/simulated/synthetic/unavailable remain distinct | Saved classifications, local simulated-publication predicate, missing-replay message, explicit synthetic observation and simulated replay labels |
| Secrets stay redacted | Existing trace sanitizer tests; added malicious-credential export test; UI text uses `textContent`; curated JSON scanning |
| Default E2E and optional perspectives | Perspectives only filter saved trace; persistent execution card remains unchanged; no alternate workflow or backend endpoint |
| Existing investigation and history are retained | Shared dialog/export links, playback selection test and manual historical-run review |
| Responsive inspection | Browser cases at 1440 and 390px; 390px manual image, no horizontal overflow, sticky independent cursors |
| Manual UX validation | A/B/C exercised through Chromium against native distributed lab with Blender; important screens reviewed, not inferred from test status |
| Engineering approach | HEAD remains the researched baseline; diffs preserve bounded engine operations, store, transport, viewer and investigation; presentation logic is isolated in a backend module |

The explicit UX criteria are supported by these behaviors and checks. This is an
implementation/manual review, not a usability study with independent engineers.

## Validation results

| Scope | Result | Saved evidence |
| --- | --- | --- |
| All UI unit tests | 167 passed; no failures or skips | `validation/ui-tests.txt` |
| Guided integration, recovery, business, read-only, playback and new workbench tests | 83 passed | `validation/backend-and-initial-contract.xml` (83 integration passes; subsequent stale-contract failure retained) |
| API/schema contract tests after regeneration | 68 passed | `validation/contracts.xml` |
| Local browser guided/workbench suite | 7 passed, 2 Blender cases deselected | `validation/browser.xml`; Blender covered separately below |
| Native distributed browser lab | 4 passed: happy, lost reply, duplicate delivery, WMS outage | `lab/*/session.json`, `browser.json`, source hashes and scenario-check summary |
| Manual distributed lab | A/B/C completed with Blender, one effect each, no browser errors | `manual-checks.json`, scenario snapshots, screenshots |
| Static checks | Ruff lint/format, mypy, JavaScript syntax and diff whitespace | `validation/static-checks.txt` |

The combined backend/contract run stopped after its first contract assertion:
the committed OpenAPI snapshot lacked the new read route and session field. The
83 preceding integration cases passed. Regenerating contracts fixed the mismatch;
all 68 API/schema cases then passed. Both raw result files are retained so the
initial failure is not presented as a green run.

The distributed suite used real PostgreSQL, RabbitMQ, OPC UA and REST, with separate
API, edge, PLC and WMS processes. Its happy case used Blender; its three fault cases
used the synthetic runtime. The separate manual A/B/C review used Blender for all
three. WMS failure was an actual HTTP 503 from the simulated WMS service.

Some final UI polish and the historical replay-selection fix followed the
distributed suite. The 167-test UI run includes that regression, and the final
manual history read check confirms the chosen session, selected job, playback job
and recording command agree after reload. The full repository's prior release
suite and remote CI were not rerun for this enhancement; results here cover the
changed workbench and the listed adjacent behaviors.

## Manual acceptance scenarios

| Scenario | What was inspected and confirmed | Original command |
| --- | --- | --- |
| A: Successful order | Step 8 stays selected at gate 15 and while execution advances to 17. Recorded motion exists before verification. All ten proof boundaries established only by final completion. Reload and history review retain identity. | `89dae376-6f2c-5164-919a-7c7817a538b5` |
| B: Lost acknowledgement after effect | Dedicated UNKNOWN_OUTCOME state; known controller success separated from unresolved workflow verification. Original-command reconciliation, then business completion. Journal effect count 1 before and after. | `426ebcae-977c-5b45-b601-4a850700a00d` |
| C: WMS failure after verified work | Controller/observation/verification established; WMS failed with HTTP 503; ERP unproven. Retry posts only stage 20. Identity and effect count 1 retained through completion. | `32c07717-8200-585b-94f3-0b8827a05910` |

All three acceptance scenarios completed successfully. The manual request log
contains three physical-stage requests total, one for each original command.
Mobile historical inspection and Follow current sent no mutation. The final
history/reload review likewise sent no POST and reported no browser errors.

## Reproduce the focused checks

Use the repository's locked environment and installed Chromium. On Windows,
PowerShell does not expand Node test globs, so enumerate them explicitly:

```powershell
$uiTests = @(Get-ChildItem -LiteralPath tests/ui -Filter '*.test.cjs' | ForEach-Object { $_.FullName })
node --test --test-reporter=spec @uiTests

$workbenchTemp = 'artifacts/workbench-check-' + [guid]::NewGuid().ToString('N')
.venv\Scripts\python.exe -m pytest tests/integration/test_guided.py tests/integration/test_guided_recovery.py tests/integration/test_guided_business.py tests/integration/test_guided_readonly.py tests/integration/test_guided_playback.py tests/integration/test_workbench.py tests/contract/test_api.py tests/contract/test_schemas.py -p no:cacheprovider --basetemp $workbenchTemp

$workbenchBrowserTemp = 'artifacts/workbench-browser-' + [guid]::NewGuid().ToString('N')
.venv\Scripts\python.exe -m pytest tests/browser/test_guided_console.py tests/browser/test_workbench_console.py -m 'not blender' -p no:cacheprovider --basetemp $workbenchBrowserTemp
```

The separate distributed browser suite is `tests/lab/test_browser_lab.py`. It
requires the documented local PostgreSQL/RabbitMQ services and Blender for its
Blender case. Follow [native lab setup](../../README.md) instead of substituting
mock transports. Omit `-m 'not blender'` above to include the local Blender cases.

To review manually, choose a product and scenario, then **Create and run order**.
Use named stage actions up to the physical gate. Inspect step 8, authorize once,
check that the inspector remains pinned, then Follow current. Continue to
verification and business completion. Repeat with lost acknowledgement and WMS
unavailable, using only the displayed recovery action. Inspect/download the saved
evidence and compare the original command's journal effect count before/after.

## Limits and deferred work

- The run JSON is a referenced snapshot, not an offline bundle of every job record,
  motion file, dependency and source revision. Existing job export provides a
  complementary evidence/events view.
- The proof ladder summarizes the current job and order-level boundaries. It does
  not aggregate every earlier job into one physical proof state. Earlier stages
  remain available in the trace.
- Observations are synthetic. Their capture and verification are separate facts.
  Recorded Blender motion is replay, not sensor proof or hardware validation.
- Protocol views are structured operation records, not packet captures. Local
  publication cannot establish a real broker boundary.
- Follow current selects the latest saved result; pending operations have no result.
  Inspection/filter state is not an immutable run manifest and is not restored as
  a personal workspace after reload.
- Explicit causal relationships, immutable runtime/build manifests, richer
  persistence/protocol schemas and a complete review-package export are deferred
  contract enhancements. None was needed to support the implemented Phase 1 claims.
- Cross-run semantic diff/search, causal graphs, reliability analysis, saved expert
  workspaces and synchronized physical timelines remain later capabilities.
- This local worktree has no new remote release/CI attestation, and the UI has not
  yet been evaluated in a formal study with independent systems engineers.
