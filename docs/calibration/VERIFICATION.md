# Measured calibration verification log

Final result: **PASS** for all SC01-SC20 simulation criteria. The scoped final
ACCEPTANCE_REPORT.md records exact results and remaining manual/hardware limitations.
The chronological iteration notes below retain earlier failures and then-current status;
their old pending statements do not supersede the final campaign.
Historical evidence is not relabeled as measured calibration evidence.

## GitHub review handoff (2026-10-13)

The user authorized committing and pushing the current implementation on
`feat/measured-calibration`. This branch includes the client rebuild, measured
calibration runtime/client/contracts/tests, and the desktop portability changes.
It does not merge `main` or publish/deploy the documentation site.

Fresh checks: **575 Python tests passed** (366 unit, 208 contract, one real-browser
seed37 journey), **199 Node tests passed**, lint/format, strict typing, reviewed
static findings, Python/npm dependency audits, vendored hashes and Git diff check.
The real browser journey covers generated captures, both-camera estimation and
approval, a guided pick, read-only inspection, moved-camera blocking and recovery.
The approved desktop screenshot was opened and inspected. One existing Starlette
TestClient/httpx deprecation warning remains; it is not a failing test.

[Machine-readable results](evidence/github-sync-20261013/verification.json),
[JUnit](evidence/github-sync-20261013/pytest.xml),
[rendered client](evidence/github-sync-20261013/approved-desktop.png),
[security](evidence/github-sync-20261013/security.json), and
[source comparison](evidence/github-sync-20261013/source-comparison.json) are committed
for remote review. Full fresh logs/fixtures are local under
`artifacts/calibration/github-sync-20261013/`. Use the commands in verification.json
from a locked environment and choose unused output directories.

The complete 1080-test campaign below remains **October 9 evidence**, not a fresh
full campaign for this push. Rechecking all 420 accepted source files found only
three differences: `apps/desktop/RobotOpsLauncher.cs`, `tools/build-desktop.ps1`,
and `tools/test-desktop.ps1`. These support explicit executable/data/output paths,
keep WebView2 data with the chosen data root, and place startup diagnostics beside
the executable. [Eight actual native/Blender relocation checks](evidence/github-sync-20261013/desktop-relocation.json)
passed against those files; their before/after hashes are in the source comparison.
[Accepted source](evidence/github-sync-20261013/accepted-source-20261009.json),
[current worktree source](evidence/github-sync-20261013/current-source.json), and
[historical full-suite summary](evidence/github-sync-20261013/accepted-regression-20261009.json)
retain their identities. These are Windows worktree byte hashes; Git-normalized
source blobs are recorded separately when staged for publication.

The canonical local repository is now `D:/RobotOps-Twin/project`; external raw
calibration evidence moved from `D:/RobotOpsTwin-Calibration-Evidence/` to
`D:/RobotOps-Twin/evidence/calibration/`. Historical reports keep their original
paths and dates. `D:/RobotOps-Twin/cleanup/path-map.json` records the relocation.
Large image arrays, worlds, videos, browser profiles, virtual environments and
machine-specific launcher configuration are excluded from the Git upload.
GitHub CI status is separate from these local checks; no new screen-reader,
human usability or hardware commissioning result is claimed.

## 2026-10-09 source-frozen campaign

`final-regression-01` passed **1080 tests, zero failures/skips**, across all `tests/`
with no marker exclusion, in 3325.94 seconds. Combined coverage is **91.18%**.
It includes real Chromium, Blender and isolated live PostgreSQL/RabbitMQ/OPC UA.
No skipped lane counts as a pass. The unchanged combined coverage requirement is 85%.
Source SHA-256: `a5c19e6eaa327582788b10d8834d5de24efd2b8ea5e2ea64275e287a1eeca044`.
`artifacts/calibration/final-source-01.json` records all 420 included file hashes,
dependency versions, starting commit and uncommitted state; its ZIP preserves those
exact runtime/client/tool/test/contract sources. It is not a remote release identity.

Large fixtures and new browser evidence use
`D:/RobotOpsTwin-Calibration-Evidence/20261009/{final-regression-01,final-browser-01}`.
Logs, JUnit, coverage, manifests and selected review captures remain in the repository.
The optional `ROBOTOPS_BROWSER_ARTIFACT_ROOT` test-harness environment variable changes
only where new browser evidence is written; its default remains the established
`artifacts/investigation-browser`. No previous evidence was moved or overwritten.

Static delivered HTML/CSS/JS increased from 239,664 to 309,472 bytes (estimated
per-file gzip: 67,240 to 86,119 bytes), excluding unchanged vendor files. This includes
the acquired-image/calculation/calibration workflow and geometry inspection. See
`final-static-size-01.json`; it is a byte comparison, not a loading-time claim.

Reproduce the complete local test lane after the documented lab services are running:

```powershell
uv sync --locked --all-groups
uv run --locked python -m playwright install chromium --only-shell
# Set ROBOTOPS_POSTGRES_DSN and ROBOTOPS_AMQP_URL for your isolated local lab.
# Optional: use a spacious directory for new browser evidence and a NEW --basetemp.
$env:ROBOTOPS_BROWSER_ARTIFACT_ROOT = 'artifacts/calibration/my-fresh-browser-evidence'
uv run --locked python -m pytest tests -q --cov=robotops --cov=apps --cov-report=term
uv run --locked python -m tools.dev lint
uv run --locked python -m mypy robotops apps/api tools/calibration.py
uv run --locked python -m tools.dev security
$testFiles = @(Get-ChildItem -LiteralPath tests/ui -Filter '*.test.cjs' | ForEach-Object { $_.FullName })
node --test $testFiles
```

The hardware-free presenter demo does not require the distributed lab. From a clean
locked environment, create a new run directory (never reuse a saved demonstration):

```powershell
uv run --locked python -m tools.calibration --run-dir runs/measured-demo-new --seed 37 --command-mode flange demonstrate --actor 'Simulated presenter' --approve-simulation --authorize-simulated-execution
uv run --locked python -m tools.calibration --run-dir runs/measured-demo-new export --output artifacts/calibration/measured-demo-new-export
uv run --locked python -m tools.calibration reproduce --bundle artifacts/calibration/measured-demo-new-export
```

Use `--command-mode tcp` for a fresh TCP-command world. Existing runs retain their
saved controller mode. Browser actions and Swedish explanations are in PRESENTER.md.
Both final clean-environment demonstrations and reproductions now pass; see
`final-cli-summary-01.json` and ACCEPTANCE_REPORT.md. Commands alone are not evidence.

## Final handoffs and clean environment

- The finish reviewer scored all five listed UI fixes resolved, scoped disposition
  `ship`: `artifacts/calibration/finish-review-02.md`. The original review and failed
  viewport iterations are retained. This verdict is not whole-surface acceptance.
- The fresh documenter compared the extension to the incumbent Operate design and
  preserved DESIGN.md: `design-documentation-review-01.md`. It records pre-existing
  documentation-format and small-copy drift without claiming a new design system.
- `uv sync --locked --all-groups --offline` created a separate environment at
  `D:/RobotOpsTwin-Calibration-Evidence/20261009/clean-env-01`: **PASS**, 99 packages.
  `final-clean-install-01.log` and `final-clean-environment-01.json` retain exact
  packages, Python/lock/source identity and smoke results. CLI `--help` also passed.
  A one-off smoke probe initially named a nonexistent Board.points_m attribute;
  correcting it to the published Board.corners_m field passed without changing code.
  The two fresh full demonstrations and export reproductions passed; each produced
  one verified pick and 300 verified hashed artifacts, with no changed trace sources.
- `final-performance-01.json` retains seed97's completed final guided run and prior
  serial observations: fresh observation 1330.30 ms, post-observation 1482.69 ms.
  Earlier serial snapshots were 2133.71-2238.55 ms and 2886.15-2937.43 ms respectively.
  This is one saved run per iteration, not a controlled benchmark or causal speedup
  claim; command mode and machine load differ. The five-second freshness gate remains.
- A read-only progress query encountered one automatic permission-review timeout;
  the explicitly permitted retry succeeded. No test, code or security-policy change.

## Baseline (cacc5fb39ddd36ea10303b167fd209e149e14bf5)

- Python: `pytest tests/unit tests/integration tests/e2e -q -m 'not blender and not lab_integration'`
  **624 passed, 7 deselected**. The seven deselections are not passes. Existing cache
  directory access warnings occurred; no test failure. This was not the full browser,
  Blender or distributed-lab campaign.
- Node: `node --test tests/ui/*.test.cjs` (PowerShell expanded files explicitly):
  **174 passed**.
- Browser: actual loopback server on port 8091, desktop 1440x1000 and narrow 390x844.
  No page errors in this baseline read-only inspection. This is not task E2E evidence.
- Files: `artifacts/calibration/baseline/{python.log,python.xml,javascript.log,
  desktop.png,narrow.png,browser.json}`. Four PDF source-page renders are in `brief/`.

## Measured core iterations

Latest bounded campaigns (2026-10-09):

- `operational-boundaries-01`: **1 PASS, 33.93 s**. Both cameras are calibrated
  from fresh RGB/depth. A test-oracle-only physical displacement of `[18,12,0]` mm
  produces new image measurements and a target displacement within 4 mm of that
  independently specified change. Planning produces no physical effect. Camera
  disagreement, incompatible transform/profile identity, same-camera substitution,
  absent limits, shared-Y conflict and affected-camera invalidation are exercised;
  inputs are never averaged. Different board mounts do not share a Y constraint.
- `lint-final-candidate-01`: **PASS**, 343 files already formatted.
  `types-final-candidate-01`: **PASS**, 108 strictly checked source files.
- `security-final-01`: **PASS**. Static findings match reviewed exact exceptions;
  Python and npm dependency audits exit 0 and vendored content hashes match.
  Raw prior outputs were retained under `security-before-final-01`; the new
  Bandit/audit/review JSON files have the `final-01-` prefix.
- `browser-finish-review-01`: **3 PASS, 1 FAIL, 4 deselected, 235.87 s**.
  The new 1280x720 assertion found the recovery button at y=722.58, height=45,
  below the viewport. `browser-finish-review-02` retained that failure (83.58 s).
  Context was reorganized rather than weakening the viewport assertion.
  `browser-finish-review-03`: **4 PASS, 4 deselected, 262.20 s**, including both
  world seeds, the missed pick and four real API launches/restarts. A final compact
  trace-connection status and profile-binding guard are under current recapture.

- `browser-finish-review-04`: **3 PASS, 1 FAIL, 4 deselected, 236.59 s**.
  Restoring the visible connection status left the recovery button at y=676.58,
  height=45: 1.58 px below the 720 px viewport. Reducing toolbar padding corrected
  this without removing status or weakening the assertion. The final full campaign
  produced the same 1280x720 recovery capture after passing that assertion; the
  independent reviewer scored the layout fix resolved. The full campaign now passes with the viewport assertion unchanged.
- `node-final-01`: **199 PASS, 0 skipped, 2948.10 ms**, on the frozen final client.

- `command-mode-runtime-01`: **2 PASS, 2 FAIL, 2 deselected, 192.44 s**.
  Both TCP-mode headless/Blender journeys passed. Both flange journeys completed
  physical picks and correctly rejected a double offset; the new assertion expected
  only the error code rather than its returned explanation. Corrected the assertion,
  preserving the guard. `command-mode-runtime-02`: **2 PASS, 4 deselected, 119.15 s**
  for the flange headless/Blender cases. All four modes now have bounded passing evidence.
- `node-finish-review-01`: **198 PASS, 1 FAIL**. The legacy boundary-copy test
  expected the text to be static HTML. It now checks rendered profile-specific copy.
  `node-finish-review-02`: **199 PASS, 2.99 s**. Source/protocol clearing and source-mode
  retention have a focused asynchronous selection test; existing replay expectations
  explicitly identify recorded jobs and saved deliveries.
- Independent Impeccable heuristic review: `artifacts/calibration/finish-review-01.md`.
  Five material UI findings, no numerical or full-accessibility certification. The
  profile disclosure, current/saved wording, compact completed-journey context,
  visible source-mode selection and scenario stripe are corrected; browser recapture
  and reviewer verdict are pending. No second detector or new design system was added.

- `browser-restart-01`: **1 PASS, 34.45 s**. Four actual API process launches over
  the same isolated data. Offline acquisition intent survives reload; receipt lookup
  returns real 404; an explicit same-ID retry creates exactly 18 captures. A second
  POST returns the same receipt and capture records. Candidate/validation remain
  inactive across restart; recorded approval survives another restart. Historical
  mutation is denied by the backend, with unchanged artifact/state. Axe and manual
  screenshot review pass; evidence under `artifacts/investigation-browser/20261009T024333291481/`.
- `command-mode-contract-01`: **216 PASS, 11.99 s**. New measured-cell TCP/flange
  selection is persisted, survives clear/restart and rejects changed idempotency
  payloads, invalid modes and legacy-profile use. Archived wire compatibility and
  regenerated strict schemas pass. No mode is added to older settings' serialized bytes.
- `browser-command-mode-01`: **2 PASS, 4 deselected, 204.51 s**. Fresh seed37 uses
  flange commands; seed97 uses TCP commands. Both complete actual guided picks and
  verify command operands and the independently expected 180 mm flange/TCP difference.
  Existing image/pixel/source/export, responsive/axe and moved-camera recovery checks
  remain enabled. Controller/Blender results are recorded above.
- New large test fixtures use `D:/RobotOpsTwin-Calibration-Evidence/20261009/` because
  the repository drive is low on space. Code, logs, XML, browser screenshots and
  reports remain in the repository; prior evidence is unchanged. Mapping is recorded
  in `artifacts/calibration/fixture-storage-20261009.json`.

- `browser-missed-pick-01`: **1 PASS, 55.88 s**. Real HTTP/backend, both cameras,
  failed grip, 121 controller samples, fresh image verification, keyboard investigation,
  axe, reload and exactly one order submission. Manually reviewed
  `artifacts/investigation-browser/20261009T023601215727/`: finished journey is separate
  from FAILED transfer; cause remains unresolved; neither approval nor X changes.
- `missed-blender-01`: **3 PASS, 122.07 s**. Headless and real Blender failed-grip
  journeys, all 121 evaluated flange/TCP poses and unmoved-object positions, restart,
  one original attempt, immutable receipt and export reproduction. Blender now presents
  explicitly recorded motion without transfer as well as successful transfers.
- `unit-contract-missed-01`: **572 PASS, 1 FAIL, 40.04 s**. Failure was the UI test's
  fixed scenario list missing the new scenario. `missed-ui-catalogue-01` still failed
  because the test tried selecting the measured-only scenario on its legacy fixture.
  The corrected test explicitly verifies that unsupported selection is disabled,
  hidden and resets without dispatch, while its comparison remains explanatory.
  `missed-ui-catalogue-02`: **11 PASS, 4.54 s**, including all 179 embedded Node checks.
- `node-restart-recovery-01`: **19 PASS**. Missing receipt allows an explicit same-ID
  retry; unavailable receipt service and historical state do not permit retry.
  Real process-outage/restart verification passes in `browser-restart-01` above.
- `depth-compression-01`: reversible NTFS compression of existing NPY evidence,
  exit 0; 17,561,883,776 logical bytes stored in 15,083,247,744 bytes (14,616 files
  compressed). No files deleted. All 16 representative hashes and lengths are unchanged
  in `depth-compression-before.json` / `depth-compression-after.json`. This is storage
  maintenance, not a calibration acceptance result.

- `missed-pick-01`: **8 PASS, 1 FAIL, 39.16 s**. Physical/controller/verification
  and investigation assertions passed; the new test incorrectly treated the
  existing Boolean `context.wms_ack` as the acknowledgement payload. It now checks
  the actual persisted stage-20 output. No production behavior was changed for this fix.
- `missed-pick-02`: **2 PASS, 57.94 s**. Both cameras calibrated from new images,
  explicit guided execution, 121 recorded motion samples with no attachment, zero
  transfer, fresh image-derived observation at source, VERIFIED_FAILURE, failed WMS
  outcome, idempotent original-command replay, unchanged approvals, UNKNOWN_CAUSE
  investigation and source-bound export/reproduction. The scenario is denied for
  legacy profiles. Existing receipt guards remain; the new explicitly tagged failed
  transfer may report six executed waypoints with zero product effects. Old receipt
  serialization omits the new optional field. Browser verification remains pending.
- `node-missed-pick-01`: **32 PASS**. Ruff/format: **340 files PASS**. Strict mypy:
  **108 source files PASS**.

- `browser-limits-01`: **1 PASS, 38.59 s**. Missing tolerance, reload, actual source
  inspection, keyboard-accessible controls, axe, explicit restore, inactive reuse,
  unused validation and new approval. Screenshot manually inspected under
  `artifacts/investigation-browser/20261009T014843076075/`; it clearly distinguishes
  an instructor fault configuration from a measured diagnosis.
- `investigation-01`: **18 PASS, 98.48 s**. Independent analytical signatures for
  edge/center residuals, low PnP/high chain, orientation/distance correlations,
  approximately 1000-fold units, scale versus rigid hypotheses, timing, diversity,
  mixed depth and sudden deterioration. Collapsed geometry remains unresolved,
  without NaN scale. Real sensor/tool faults produce persisted investigations;
  idempotency, unchanged authority and full export/recomputation pass. These numerical
  signature fixtures are labelled analytical, not substituted for image acceptance.
- `investigation-schema-02`: **142 PASS, 2.44 s**. Typed schemas and affected
  diagnostic unit tests. Ruff and strict mypy **107 source files PASS**.
- `browser-investigation-01`: **1 PASS, 5 deselected, 114.40 s**. Real calibration,
  separate tool and depth faults, keyboard-triggered investigations, restored focus,
  actual saved Python source, axe, guarded recovery and completed guided pick.
  Investigations never restore a suspect camera or rewrite X/tool/limits. The
  actual ambiguous missed-pick case and complete final regression campaign remain due.

- `contracts-measured-01`: **201 PASS, 28.28 s**. Regenerated OpenAPI and typed
  schemas; validation/serialization shapes agree. Original archived wire bytes and
  command digests, including uncertain-command restart recovery, pass unchanged.
  One existing Starlette/httpx deprecation warning remains. Calibration wrappers
  follow the existing domain serializer convention, so their return annotations no
  longer erase typed published fields. No data shape or hash was rewritten.
- `limits-01`: **1 PASS, 28.74 s**. Real images/approval, missing required tolerance,
  idempotent retry, fresh service instance, blocked old approval, explicit restore,
  inactive saved-estimate reuse, unused independent validation and new approval.
  Neither fault alters physical/controller state or X. Strict mypy: **105 files PASS**.

- `browser-quality-ambiguity-01`: **1 PASS, 1 FAIL, 5 deselected**. Real near-frontal
  RGB exposed two positive-depth IPPE/LM solutions and correctly rejected the pose;
  new varied measurements produced an inactive candidate. The full pick completed,
  but its quality-record inspection failed because the client record index was stale
  and the test still selected the east camera for a west-camera measurement.
- `browser-quality-refresh-01`: **1 PASS, 5 deselected, 70.74 s**. The inspector now
  refreshes read-only state/records; completed/failed guided runs refresh calibration
  evidence too. The test explicitly selects the measurement's camera. No page reload
  is used to discover new quality evidence. Existing pixel/native-aligned, source,
  replay, export and accessibility assertions also passed. `node-quality-refresh-01`:
  **17 PASS**, including read-only refresh/focus/selection and stale-response checks.
- Manual screenshot review: `artifacts/investigation-browser/20261009T013405266628/`
  shows actual near-frontal RGB, explicit depth display units/limits, rejected pose
  status and bounded numerical operands. No selected pose or approval is invented.
  Updated quality screenshot/replay/export evidence is under
  `artifacts/investigation-browser/20261009T014033912271/`.

These are focused passes, not the final SC01–SC20 acceptance campaign. Failed
campaign artifacts remain unchanged. No human screen-reader test was performed.

1. `core-01`: **16 passed**. Independent analytical X/Y direction and Park-Martin
   mapping; rigid transforms/point-count RMS; real RGB detection/PnP/fitting in two
   cameras and seeds 17/53. Inactive candidates only, no approval claim.
2. `depth-tcp-01`: **13 passed**. Off-axis axial/radial measurements, scale/registration,
   invalid and mixed data, no-approval result, independent pivot + indexed orientation
   metrology, TCP/flange conversion and changed-tool rejection.
3. `image-holdout-01`: **4 failed**. Test incorrectly assumed every planned board
   view was detectable. Visual inspection confirmed severe foreshortening. Admission
   rejection now remains in the report with raw captures. Required admitted sample
   count and acceptance thresholds were not lowered.
4. `image-holdout-02`: **4 failed**. Native baseline permits background returns hidden
   behind the RGB foreground. Added explicit front-surface support/z-buffer handling
   only inside a uniquely identified opaque RGB surface. Edge/uncertain cases reject.
5. `image-holdout-03`: **3 passed, 1 failed**. Seed 53/east exceeded the 6 mm chain
   translation gate on one view. Failure retained. Separate seed-17 **fit** images
   demonstrated biased interpolated corners (roughly 0.7–0.8 px oracle errors);
   image-based checker-intersection refinement reduced those development errors.
   Added a fixed 3 px `cornerSubPix` step before PnP. No X/Y or threshold was tuned to
   the failed holdout, and seeds 17/53 are development data from this point onward.
6. `image-holdout-04`: **4 passed** using new worlds, seeds **29/83**, both cameras.
   Actual RGB/native-depth arrays, real corner detection, inactive unknown-Y fit,
   unused board holdout plus 24 separately located reference disks over x/y/height.
   Reference centers are detected from RGB; points reconstructed from native depth.
   PnP and chain residuals are separate; every final reference uses the frozen X.
7. `lifecycle-01`: the **3 substantive lifecycle tests passed** (a fourth redundant
   annotation-only assertion was subsequently removed). Actual images through fit,
   reserved holdout, separate explicit simulated approval, restart, immutable export,
   invalidation, duplicate requests, concurrent revision guards and rejected captures.
   Removing the redundant assertion does not replace rerunning the final suite.

Each iteration has its own log/XML and retained temporary data under
`artifacts/calibration/`. Failures are not overwritten. These intermediate runs do
not certify subsequent source edits; a source-bound complete campaign is still due.

## Reproduction during development

From the repository, with `uv sync --locked` completed:

```powershell
uv run --locked python -m pytest tests/unit/test_measured_calibration.py tests/unit/test_calibration_depth_tcp.py tests/integration/test_calibration_images.py tests/integration/test_calibration_lifecycle.py -q
uv run --locked mypy robotops/calibration
uv run --locked ruff check robotops/calibration tools/calibration.py
```

CLI operations share the application service and require revision + idempotency IDs:

```powershell
uv run --locked python -m tools.calibration --run-dir runs/calibration-example --seed 29 --request-id setup --expected-revision 0 configure
uv run --locked python -m tools.calibration --run-dir runs/calibration-example --seed 29 --request-id measure --expected-revision 1 capture --dataset fit-1
uv run --locked python -m tools.calibration --run-dir runs/calibration-example --seed 29 --request-id estimate --expected-revision 2 fit --dataset fit-1 --candidate candidate-1
uv run --locked python -m tools.calibration --run-dir runs/calibration-example --seed 29 --request-id final --expected-revision 3 validate --candidate candidate-1 --dataset unused-final-1
uv run --locked python -m tools.calibration --run-dir runs/calibration-example --seed 29 status
```

`approve` is a separate explicit command requiring actor, candidate, report and current
revision; `export --output NEW_DIRECTORY` never replaces an existing evidence folder.
The initial CLI demonstrated the measured core only. The later integrated iteration
below adds an actual guided ERP/WMS pick; earlier evidence is not relabelled.

## Unperformed checks / remaining work

- New UI/browser journeys, accessibility/keyboard, 3D/controller agreement.
- Integration into actual order execution; profile-specific motion/contact interlocks.
- Full required fault, overlap, investigation/recovery, rollback and command-integrity campaign.
- Documented aligned-depth adapter; current native path rejects unprovided alignment mapping.
- Full source/transport instrumentation and reproducible export replay.
- Fresh complete regression campaign including Blender and applicable distributed lab.
- Human usability and real screen-reader testing have not been performed.

## Integrated client/runtime iteration (2026-10-08)

These results supersede the earlier *implementation status*, not the saved evidence.
The listed campaigns used their own fresh worlds; no failed evidence was overwritten.
The full goal remains incomplete.

| Campaign | Result | Evidence / meaning |
|---|---|---|
| `actual-pick-04` | 1 PASS | Real Engine observation -> approved target -> command -> contact -> fresh verification; original command replay after invalidation has no second effect |
| `wire-compat-02` | 42 PASS | Existing legacy/HKM contract and catalogue checks after measured v3 extension |
| `core-03` | 32 PASS | Numerical/depth/TCP/contract/lifecycle checks including pose-conditioning change |
| `browser-01` | FAIL | Test asserted image load before the asynchronous image response; replaced with waiting for actual decoded dimensions |
| `browser-02` | FAIL | East camera holdout had a weak 8-corner PnP view with 18 mm chain error. Approval stayed blocked. Failed holdout retained |
| `browser-03` | 1 PASS | Real two-camera acquisition, fit, validation, named approval, tool check, 22-stage guided pick, refreshed history/source/narrow inspection |
| `browser-04` | 2 PASS | Same real browser journey in fresh worlds, seeds 37 and 97, now with cross-camera agreement and both artifacts bound into the command |
| `overlap-core-01` | 3 PASS, 1 FAIL | Analytical diagnostic cases pass; reused request ID across cameras exposed a global validation-reservation collision |
| `overlap-core-02` | 1 PASS | Reservation ID now hashes camera + request; same-request-ID two-camera integration succeeds |
| `node-03` | 174 PASS | Existing JavaScript regression tests. `node-02` was a Windows wildcard invocation error, not a test result |
| `browser-05` | 2 PASS | Axe, enlarged text, raw export, camera move, failed routine references and replacement approval; export RPC was unnecessarily slow |
| `browser-06` | 2 PASS | Uses a real browser download; adds resumed pick after restocking while preserving the verified tool |
| `browser-07` | 2 PASS | Above journeys plus 121-frame controller replay and saved camera geometry unchanged after physical movement |
| `controller-replay-01` | 5 PASS | Initial controller motion / contract checks |
| `image-quality-01` | FAIL (4) | Old tests assumed every rendered view was accepted. The new pre-fit image-conditioning check correctly rejects weak views |
| `controller-replay-02` | 5 PASS | Every rejection is retained; unchanged minimum sample/coverage and 5 mm / 0.4 degree golden-transform checks pass. Controller/product replay and physical contact offsets match |
| `cli-demo-01` | FAIL | Real pick completed, but Windows cp1252 stdout rejected a Unicode arrow. Evidence retained; output now uses standard JSON ASCII escaping |
| `cli-restart-01` | PASS | Same CLI pick request loads the original completed guided session |
| `cli-demo-02` | PASS | Fresh seed 163: both cameras, image fitting, unused validation, named approval, tool metrology, full guided pick |
| `cli-export-02`, `cli-reproduce-02` | PASS | 248 image/depth artifacts hash-verified; actual RGB detection/PnP/refit reproduces both X/Y exactly with matching recorded source fingerprints |
| `measured-blender-01` | 1 PASS | Real Blender 5.2.1: evaluated flange/TCP/product samples match controller reports, saved-scene reimport is read-only, duplicate dispatch does not create another effect or presentation |
| `measured-blender-02` | 12 PASS | Headless and real Blender picks, saved-scene reimport and existing adapter timeout/QoS tests. Rendered screenshot reviewed after fixing cropped sensor framing |
| `aligned-depth-01` | 16 PASS | Original depth/TCP tests plus documented aligned-native semantics, map/hash/profile checks, holes, mixed surfaces and radial range |
| `aligned-depth-02` | 18 PASS, 2 ERROR | Windows denied pytest's default temp directory; no product failure in these two unrun tests |
| `aligned-depth-03` | 20 PASS | Reran with a new repository-local basetemp/cache, including legacy wire and oracle-import boundary checks |
| `browser-08` | 2 FAIL | Test incorrectly required dense aligned depth at an arbitrary RGB pixel. RGB is 960x720; depth is 640x480. Correct implementation returned `ALIGNED_DEPTH_HOLE`; no point fallback |
| `browser-09` | 2 PASS | Keeps hole rejection, then explicitly selects a projected measured return; keyboard native/aligned inspection, Python ray overlay, axe and unchanged approval/execution records. Screenshot review led to smaller image boxes and full-sized pixel inputs in the next iteration |
| `node-04` | 174 PASS | Existing JS suite with controller/Blender playback labels and the initial pixel inspector |
| `uncertain-recovery-01` | 1 PASS | Real camera movement after physical effect blocks fresh observation; restart/reconciliation keep original command unresolved. New measurement/validation/approval permits fresh verification of that same command with one physical effect |
| `regression-01` | 664 PASS, 3 FAIL, 8 DESELECTED | Failures: incomplete Blender manifest fixture / new closure file; stale hardcoded reconciliation excerpt; old test expected only one selectable profile. Baseline had none of these failures. Fixes retain the old HKM default and legacy history; broad rerun required |
| `regression-fixes-01` | 7 PASS | Blender closure manifest now includes the new renderer; test supplies initialized settings. Reconciliation excerpt is extracted from the actual current function after adding failed-observation handling |
| `uncertain-guided-01` | 1 PASS | Full guided stages, post-effect camera notice, failed stage 18, two unresolved reconciliation attempts across restart, explicit new calibration approval, original-command verification and WMS/ERP completion with exactly one effect |
| `browser-10` | 2 PASS | Same two-world journeys after image aspect-ratio, 44 px pixel inputs and camera framing fixes; rendered pixel-inspection screenshot reviewed |
| `legacy-blender-01` | 33 PASS | Complete existing `tests/blender` lane with actual Blender; fresh timestamped evidence preserves prior artifacts |
| `metrology-01` | 21 PASS, 1 DESELECTED | Raw pivot/probe measurements survive concurrency/restart; changed cell blocks application; replay cannot re-enable a later changed tool. Includes real measured picks and uncertain-outcome recovery; Blender variant intentionally excluded from this focused run |
| `lab-regression-01` | 28 PASS, 2 FAIL | Actual loopback PostgreSQL 17.11 / RabbitMQ 4.3.6 plus HTTP/OPC UA. Browser static-preview load raced a no-motion assertion; measured-cell error handling unintentionally changed the legacy lab job state |
| `lab-fixes-02` | 7 PASS | Complete existing lab browser scenarios (including Blender) and boot-recovery cases. Waits for initial static geometry before unchanged no-motion assertions; special measured-cell state transition scoped to that profile |
| `faults-01` | 8 PASS | Real images/depth and independent references: scale-compatible clue, no target for invalid returns, restoration leaves approval suspect, independent tool translation/orientation failures, fault persistence and reproducible raw artifacts |
| `browser-faults-01` | 1 FAIL | New test used a nonexistent workspace selector; implementation reached tool failure evidence successfully. Corrected test to use the existing named navigation link |
| `browser-faults-02` | 1 PASS | Real browser tool fault/check/restoration, depth-scale investigation, non-finite depth rejection, failed approval applicability, restored sensor still blocked, new measurements/validation/explicit approval, other camera approval, full guided pick; axe on tool evidence and missing depth |
| `node-05` | 180 PASS | Existing JS coverage plus late pixel/world responses, selection changes, clearing outstanding rays and explicit depth errors |
| `reproduction-03` | 1 FAIL, 1 DESELECTED | All numerical stages matched, but editing two source files during the test correctly failed exact-source comparison. Failure retained; not counted as a pass. Actual target construction ran twice for the same observation during revalidation, so the test now checks one immutable target identity and one physical command/effect while retaining both call traces |
| `reproduction-04` | 2 PASS | Fresh headless and Blender-backed image calibration/pick: 252 raw artifacts, both fits, independent reports and rejected views, all runtime points, pivot/probe checks, target calls, command hash/receipt and 121 controller samples reproduced/audited. Export and reproduction preserve suspect state and physical world |
| `robust-fit-01` | 20 PASS, 1 DESELECTED | Known/unknown Y with independently corrupted robot reports, excessive inconsistent populations rejected, all four image/holdout cases, headless real pick and expanded reproduction. Training consensus never uses holdout; limits unchanged |
| `node-06` | 180 PASS | JavaScript regressions after blocked-artifact evidence wording and pixel-selection fixes |
| `optics-lifecycle-01` | 3 PASS | Existing durable lifecycle checks with explicit camera-model verification |
| `optics-01` | 9 PASS, 1 FAIL | Fisheye projection rejected integer distortion coefficients; the shared projection boundary now canonicalizes K/D as float64 |
| `optics-02` | 31 PASS, 1 DESELECTED | Independent pinhole/fisheye optical fixtures, depth/TCP, lifecycle and a real headless calibrated pick with expanded reproduction |
| `optics-03` | 19 PASS | Camera-model/contract tests including proof that changing declared K, dimensions, depth scale or registration does not change the physical sensor's generated arrays |
| `optics-config-04` | 20 PASS | Durable focal-length/profile/crop/resize/distortion faults; failed camera-model verification prevents candidate creation, and configuration survives restart |
| `correspondences-01` | 6 PASS | Independent pinhole corner fixtures: duplicate/negative/unknown IDs rejected before PnP, gross outliers and swapped IDs explicitly excluded, actual IPPE/LM leaves a distant nearly frontal view unresolved |
| `browser-optics-01` | 3 PASS, 1 FAIL | Camera-model faults, tool/depth recovery and seed97 completed. Seed37 completed its pick/inspection, then an old test selector matched both newly available fault disclosures; fixed to target the named camera-movement disclosure |
| `acquisition-01` | 11 PASS, 2 FAIL | Repeated/single-axis development plans also produced too many weak individual images to isolate diversity. Limits and assertions retained; fixed horizontal-board plan chosen using separate development captures |
| `acquisition-02` | 13 PASS | Repeated/single-axis usable images still fail coverage; timing/unsettled captures are retained and rejected; explicit recovery uses new images; exported rejected datasets reproduce all decisions; lifecycle and corner regression checks pass |
| `node-acquisition-01` | 180 PASS | Existing JavaScript tests after measurement controls and idle-state wording |
| `node-acquisition-02` | 181 PASS | Adds idle calibration-gate labels while preserving saved command outcomes and legacy reset behavior |
| `acquisition-pick-01` | 2 PASS, 2 DESELECTED | Fresh headless and real Blender measured picks, scientific reproduction and controller-frame audit; uncertain-outcome tests outside this focused selection |
| `browser-acquisition-01` | 4 PASS, 1 FAIL | Capture quality, model faults and both seed37/97 happy/recovery journeys passed. Tool/depth recovery reached UNKNOWN_OUTCOME after a post-action observation expired during concurrent Blender load |
| `browser-recovery-03` | 1 PASS, 4 DESELECTED | Isolated rerun of that tool/depth journey passed; unchanged 5-second freshness limit and assertions |
| `format-02` | PASS | All 313 files satisfy repository formatting; lint and strict typing (102 files) pass |
| `optimized-guards-01` | 5 PASS | Explicit motion/export guards still reject invalid context under Python `-O` |
| `security-02` | PASS | Static review has no unreviewed findings after explicit guard fixes and exact-AST review of the fixed Blender version command |
| `trace-guards-01` | 13 PASS | Actual controller capture and PnP traces are distinct; routine results are recomputed from immutable references; acquisition/export/lifecycle/fault regressions pass |
| `browser-trace-01` | 1 PASS, 4 DESELECTED | Real acquisition-quality/recovery journey checks distinct saved sensor/PnP excerpts for records sharing a capture ID |
| `board-01` | 3 PASS, 2 FAIL | Remount/reapproval and wrong-size rejection ran; new test used the legacy observer and a guessed rejection code. Test mistakes corrected without changing limits or acceptance requirements |
| `board-02` | 4 PASS, 1 FAIL | Both-camera remount, persistence, unchanged physical cameras, recovered mounting, invalid rollback and stale-revision checks pass. Capture retry uncovered numeric 0/0.0 hashing mismatch |
| `board-units-01` | 67 PASS, 276 DESELECTED | Applicable measured/calibration unit checks; FastAPI test-client deprecation warning retained |
| `node-board-01` | 181 PASS | Existing UI regressions with board fault choices and recovery wording |
| `board-03` | 1 PASS, 1 DESELECTED | Wrong metric board has low PnP residual but no reliable rigid-chain fit; immutable capture retry rejects changed board; restoration uses fresh images and passes independent validation/approval |
| `browser-board-01` | 1 PASS, 5 DESELECTED | Actual client: wrong metric dimensions rejected, restoration, approval of both cameras, shared remount, refresh, inactive replacements, independent validation/approval, tool check and completed guided pick; axe checks pass |
| `presentation-01` | COLLECTION ERROR | Two new test files had the same import basename; renamed the integration file without changing assertions |
| `node-presentation-01` | 186 PASS, 1 FAIL | New saved-scene inspection exposed a null replay-record access; fixed draw to exclude replay frames while static evidence is selected |
| `presentation-02` | 3 PASS | Printed marker runs agree with actual OpenCV dictionary and metric image; independent error vectors are unscaled; saved capture matches reported flange, survives later camera movement, exports and reproduces without mutation |
| `node-presentation-02` | 187 PASS | Adds saved-scene replay isolation and stale geometry-response checks for world/camera/capture/record changes |
| `presentation-03` | 3 PASS | Reproduction additionally audits every saved capture presentation against its bound capture and reported flange |
| `node-presentation-03` | 187 PASS | Geometry and pixel inspection contexts do not mix; prior UI regressions pass |
| `browser-presentation-01` | 2 PASS, 4 DESELECTED | Actual capture/plan/sample-chain inspection plus seed97 complete guided pick, reference errors, exact saved target, raw export, responsive/text/axe and no JS errors |
| `node-presentation-04` | 188 PASS | Adds an assertion that coordinate overlays cannot borrow current physical camera/board geometry |
| `browser-presentation-02` | 2 PASS, 4 DESELECTED | Repeats those journeys after shorter captions and historical scene binding; before/after source hashes match during each journey |
| `regression-02` | 716 PASS, 8 DESELECTED; **FAIL coverage** | 1505.07 s; 79.08% against unchanged 85%. Separate browser/Blender/lab code is included in the denominator but those lanes were not executed here. XML, log, coverage data and source identity retained; not a passing engineering gate |
| `revalidation-01` | 2 PASS | Reuse retains original X/Y and fit provenance, remains inactive/suspect, rejects old holdout/report, needs new approval, survives restart; moved camera fails independent validation, board remount forbids old-Y reuse |
| `revalidation-02` | 4 PASS | Adds export/reproduction of reused-estimate lineage and the original fit; numerical presentation tests preserve unscaled errors with close presentation-only framing |
| `node-revalidation-01` | 189 PASS | Adds continuous close-evidence zoom with unchanged supplied geometry; existing UI regression tests pass |
| `browser-revalidation-01` | 2 PASS, 5 DESELECTED | Real UI: reused estimate remains blocked through reload, fresh validation/new approval, actual guided pick, moved-camera reuse rejects; second fresh world seed97 verifies close reference framing, exact target, images, export, narrow/text/axe checks; source unchanged during each journey |
| `node-revalidation-02` | 190 PASS | Groups repeated validation failures by limit for the visible summary without changing or removing exact saved codes/sample IDs |
| `browser-revalidation-02` | 1 PASS | Repeats the real reuse/pick/moved-camera rejection journey; grouped failure summary is readable, exact saved codes remain accessible, axe and source-stability checks pass |
| `loaded-source-01` | 10 PASS | Loaded direct/partial function and bound-method code matches compiled local source; changed code and wrong callables reject before execution with a durable error; raw CRLF bytes differ from normalized display hash; existing source/boundary tests pass |
| `loaded-source-optimized-01` | 5 PASS | The same explicit source checks run under Python -O; pytest notes that assertions in non-test modules are disabled, while implementation guards use explicit errors |
| `loaded-source-runtime-01` | 5 PASS, 3 DESELECTED | Real rejected/varied acquisition plus approved image-driven application pick and export reproduction run with loaded-function verification enabled |
| `printed-ids-01` | 3 PASS | Physical RGB and saved 3D markers change to IDs 17-33 while declared board/X/Y remain fixed; real detection rejects unknown IDs, both cameras block, restoration/new independent approval succeeds, and export reproduces both rejection and recovery |
| `browser-printed-ids-01` | 2 PASS, 5 DESELECTED | Actual client wrong-print rejection/raw image/saved 3D/source/restore/new approval plus timing/settling/diversity recovery; matched loaded-function evidence asserted for sensor/PnP calls, axe/source-stability checks pass |
| `corner-warp-01` | 7 PASS | Actual local RGB readout warp produces detected corner exclusions and pose-quality rejections; numerical correspondence tests also pass |
| `corner-warp-02` | 7 PASS | Excluded pixel coordinates remain paired with their IDs; reproduction compares them against raw-image detection and rejects a copied, rehashed but falsified pixel record |
| `browser-corner-warp-01` | 1 PASS | Real RGB warp, saved excluded pixels/overlay, restoration, unused validation and explicit approval; axe and saved source checks pass (51.60 s) |
| `depth-display-01` | 2 PASS | Raw-unit quantile endpoints, clipped color mapping, preserved invalid data and no invented all-missing range |
| `node-depth-display-01` | 16 PASS | Inspector unit checks, including stale world/camera/capture responses and all-missing depth caption |
| `reference-trace-01` | 3 PASS, 1 FAIL | Journal concurrency/restart/moved-camera identity passed; interrupted validation and complete reproduction passed before a final test assertion incorrectly assumed chronological export ordering. Corrected to select the failed check by ID; rerun pending |
| `node-reference-trace-01` | 194 PASS | Complete current UI unit suite, including late-response guards and native evidence-view zoom |
| `reference-trace-02` | 7 PASS, 1 DESELECTED | Atomic reference retries, restart after interrupted validation, raw masks/operands, missing-depth routine rejection/export reproduction, headless actual pick and both original-command recovery modes (238.11 s); Blender deselected, not passed |
| `browser-reference-trace-01` | 2 PASS | Reference capture -> real image-only detection/mask -> reconstruction operands/source; read-only reload/state preservation, numeric depth display and corner-fault recovery (63.55 s). Axe and source-stability checks pass |
| `measured-quality-01` | 28 PASS | Measured gates without invented probability/uncertainty, bad bindings and missing operands, truthful historical wire shape, v1/v2 numeric requirements, existing action/verifier and source boundaries |
| `node-measured-quality-01` | 31 PASS | Quality labels distinguish actual measured gates, unestimated statistics and legacy scores; inspector response guards pass |
| `measured-quality-runtime-01` | 2 PASS, 5 DESELECTED | Actual headless pick, post-observation and complete export recomputation use recorded gates and explicit unknown statistics; missing/stale quality bindings reject, and lifecycle/84 depth+mask export files pass (84.28 s) |
| `image-ambiguity-01` | 1 PASS | Actual generated near-frontal RGB produces unresolved positive-depth planar poses; saved rejection and raw-image reproduction pass |
| `image-ambiguity-02` | 11 PASS | Rejections now retain actual corners, normalized operands, both T_c_t candidates/residuals and RMS gap; raw-image reproduction compares the rejected calculation. Analytical PnP and measured-quality checks also pass |

The near-frontal development probe used only training images from seed173 and
public fixed flange poses; it read no hidden X/Y, fitted candidate or holdout.
`artifacts/calibration/near-frontal-training-01/{results.json,runtime.db,images/}`
retains source identity and captures. At flange z=0.65 m and xyz rotation
(0.82,-0.54,0) rad, actual IPPE/LM found distinct positive-depth solutions with
0.209146 and 0.213420 px point RMS. Existing 0.08 px ambiguity and conditioning
limits were unchanged. The resulting client experiment does not force that outcome;
each generated image still goes through the real solver and gates.

Rendered screenshots reviewed for the reference and depth-display slice:
`artifacts/investigation-browser/20261009T011454934353/`
`test_reference_measurements_expose_real_source_masks_operands_and_readonly_replay/reference-reconstruction-source.png`
and `artifacts/investigation-browser/20261009T011529228623/`
`test_rgb_readout_fault_shows_excluded_corner_pixels_and_recovers_with_new_images/excluded-corner-overlay.png`.
They show separate survey/reconstruction coordinates, recorded Python source and
explicit raw-unit display endpoints. No full accessibility conformance is claimed.

Rendered review of `artifacts/investigation-browser/20261009T004952154534/`
`test_rgb_readout_fault_shows_excluded_corner_pixels_and_recovers_with_new_images/`
`excluded-corner-overlay.png` confirms the actual annotated capture, native depth,
blocked camera state and measurement recovery remain visible. The depth preview
uses a per-image color range; a numerical range will make this display more useful.

`rgb-warp-training-01/results.json` records a development experiment using only
training poses (seed113). It compared 8/12/16-pixel sensor-readout faults to obtain a
visible outlier demonstration. The selected 12-pixel fault and 22-pixel Gaussian
spread change RGB arrays, not detector outputs, K, X/Y, limits or solver settings.
No holdout was used. Accepted and rejected observations remain stored; the browser
overlay draws recorded excluded pixels as labelled amber crosses.

The printing fault uses OpenCV's explicit marker-ID constructor, verified against the
installed 4.13 stubs and the [official CharucoBoard API](https://docs.opencv.org/4.13.0/d0/d3c/classcv_1_1aruco_1_1CharucoBoard.html).
Expected board corner IDs and metric correspondences remain the declared configuration.
Neither detection nor fitting branches on the instructor fault label.

Manual screenshot review of browser-revalidation-01 found that rejection details
dominated the evidence page. The summary now reports grouped limit failures; full
codes and sample identities remain under Records and run info. The affected browser
journey passed again and its rendered summary was reviewed. The reference-error view's new framing visibly resolves
the distributed points while preserving 1:1 vector lengths; it is presentation-only.

Rendered review of geometry-capture.png found repeated technical captions. The
follow-up uses a shorter capture title and static-view banner, retaining full scope
and numbers below the selector. Sample overlays use their saved capture scene;
targets use the saved pre-command scene when available. Other coordinate overlays
draw their own data without substituting the current cell. The second browser
campaign passed with no page or console errors. A one-line import-order lint issue
was corrected after the browser freeze; repository formatting reports 317 files pass.
The broader Python regression completed with all collected tests passing but a
coverage-gate failure. The final complete campaign must measure the separate lanes
and exercise remaining uncovered behavior; the threshold remains 85%.

The board-02 retry failure was corrected by normalizing timestamp skew to float
before hashing; it was not weakened to accept arbitrary conflicts. Focused board-03
passed; browser recovery verification passed in browser-board-01. Physical collision checks now use
the physical board corners, including its current remount, rather than a hardcoded
upright extent. Shared board notices invalidate both camera revisions atomically
before the physical change; historical artifacts remain immutable.

The browser-acquisition-01 failure is retained, not relabelled successful. Command
`4c84d526-4a8a-5d49-85dc-8019bb7eec2b` had one committed PICK_APPLIED effect.
The subsequent observation took 4246.792 ms to acquire/process and was expired at
the later verification stage (`STALE_OR_FUTURE_OBSERVATION`). No console error or
second pick occurred. The isolated rerun supports a load-related explanation but
does not prove all performance issues resolved. Heavy Blender rendering and browser
happy-path freshness checks must be run separately under comparable conditions.

The acquisition development comparison used only synthetic training captures, no
final holdout or candidate error. A horizontal board gave 18 accepted images for
each camera in the fixed seed83 development world. It makes the repeated/one-axis
demonstration isolate diversity; it does not bypass conditioning or guarantee
acceptance for arbitrary worlds. Raw development images/log are retained under
`acquisition-development-02`.

`format-audit-01` found 63 files requiring the repository formatter (since corrected
and rechecked in format-02). `security-01` found eight new assertion findings
and an outdated exact-AST review for the Blender manifest function. These are
corrected/reviewed in security-02, not waived. Its Python dependency vulnerability audit
completed with exit0 (99 dependencies, zero findings). NPM audit also exited0 with
zero vulnerabilities; every vendored asset matches its manifest hash. Full combined
security acceptance remains pending at final source freeze.

Rendered manual review of the new one-axis report confirmed a concise explanation:
18 accepted images, adequate position spans, one nonzero rotational diversity
direction, no approval and an explicit new-measurement recovery path. Evidence:
`artifacts/investigation-browser/20261008T223007788955/test_capture_quality_failures_are_explained_and_recover_with_new_images/capture-single_axis.png`.

The optics-config-04 source passed `ruff check .` and strict
`mypy robotops apps/api tools/calibration.py` (101 source files). A complete current
calibration browser rerun (`browser-acquisition-01`) finished with the results above.

Optical verification uses a separate, explicitly synthetic camera-local factory
metrology fixture: 105 independently defined points per RGB/depth optical frame,
with seeded 0.08-pixel readout noise. It does not use installed X/Y or a candidate,
and does not verify depth scale, registration, TCP or mechanics. It is not a real
factory certificate or working-cell RGB-D acquisition. The declared model and
physical sensor specification are separate. This supports the report's distinction
between factory optics and installation calibration without claiming that the
working-cell board poses provide well-conditioned intrinsic estimation.

`ruff check .` and strict `mypy robotops apps/api tools/calibration.py` passed after
the robust-fit slice (100 checked source files). One automatic permission review of
the read-only check command timed out; its permitted single retry succeeded. This
was not a code/test failure or an unresolved permission blocker.

The lab fixtures for this campaign are isolated under `artifacts/calibration/lab-services-01`,
with PostgreSQL port 5433 and RabbitMQ port 5673. No Windows service, system policy,
production endpoint or global PATH was changed. The `.ps1` launcher was blocked by
the existing execution policy; reviewed native executable startup commands were used
without changing that policy. The complete lab lane must be repeated at source freeze.

Image conditioning fix: before looking at X/chain/reference errors, propagate a fixed
0.2-pixel noise floor (or larger observed image residual) through the numerical image
Jacobian. Reject when three-sigma local pose sensitivity exceeds the existing 6 mm /
1 degree chain budgets. Limits were **not relaxed**. Training capture diagnostics,
not the failed holdout, informed this measurement-quality change. The covariance is a
local sensitivity estimate, not a real-world accuracy guarantee. Accepted samples save
the estimate; rejected views save the reason. Fresh independent sets follow the change.

Browser traces/screenshots/source hashes are under
`artifacts/investigation-browser/<timestamp>/test_calibration_*`; logs/XML/data for
each named campaign are under `artifacts/calibration/`. This is agent-based testing,
not human user research. Full-source-bound final acceptance remains due.

Reproduction:

```powershell
uv run --locked python -m pytest tests/browser/test_calibration_console.py -q
uv run --locked python -m pytest tests/unit/test_calibration_diagnostics.py tests/e2e/test_measured_pick.py -q
$testFiles = @(Get-ChildItem -LiteralPath tests/ui -Filter '*.test.cjs' | ForEach-Object { $_.FullName })
node --test $testFiles
```

Manual rendered review found oversized/overlapping labels in the initial gantry
scene. The new profile now uses fewer short labels with a smaller presentation scale,
plus numerical flange/tool/TCP text. The physical camera geometry remains independent
from its estimated transform. Further 3D overlay/replay and Blender checks remain due.

Vercel review consulted the fresh upstream
[Web Interface Guidelines](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md).
Applied findings: explicit image dimensions, native labelled controls, status/error
announcements, preserved focus after asynchronous actions, bounded code scrolling,
and a real download link. This does not establish complete WCAG conformance.
