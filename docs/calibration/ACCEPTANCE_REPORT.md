# Measured calibration acceptance report

**Result: ACHIEVED for the specified local synthetic calibration simulator.**
Verified 2026-10-09. No remote push, public deployment, paid API or industrial hardware
was used. This does not certify a real cell or proprietary SICS.AI implementation.

## Tested source and source brief

- Repository: `C:/Users/ramis/source/repos/robotops-twin`.
- Branch: `feat/measured-calibration`; base/client-rebuild commit
  `cacc5fb39ddd36ea10303b167fd209e149e14bf5`, based on main
  `26d7aac9774d4f014e70da872dd4045d94428748`. Origin was fetched before branching.
- Implementation remains an uncommitted local worktree. No newer relevant source or
  unrelated local work was discarded. The starting worktree was clean.
- Exact tested source digest:
  `a5c19e6eaa327582788b10d8834d5de24efd2b8ea5e2ea64275e287a1eeca044`.
  `artifacts/calibration/final-source-01.json` lists 420 included files and dependency
  versions; `final-source-01.zip` preserves them. The final regression summary confirms
  no added, removed or changed file in that scope. Documentation has separate provenance.
- The available four-page `SICS_AI_Kalibrering_Rami_Halabi_v2.pdf` was read and visually
  inspected, SHA256 `8b1b371d58824e2bc680ad1d8c0d16406502c5b3ecfee28e7118332c543c0f7f`.
  The exact `(1)` filename was unavailable. The user's restated requirements govern;
  this report does not claim to have inspected that unavailable filename.

## Delivered behavior

Real Python-rendered RGB/native-depth arrays feed actual ChArUco detection, normalized
IPPE/LM, rigid known-Y or Park-Martin unknown-Y estimation, inactive candidates,
independent frozen validation and explicit named simulated approval. Two separately
approved cameras feed depth correspondence, measured base points, separate grasp/TCP
construction and the existing immutable order/command/controller/WMS/ERP path.

The ideal orientable gantry is a separate supported profile. Original HKM upright guards
remain. Physical contact checks and committed controller poses govern simulated effects;
views, replay and exports cannot approve or execute. Failed grip records actual motion
and zero transfer. Uncertain outcomes retain the original command. Tool/depth faults are
investigated separately from X; unsupported conclusions remain UNKNOWN_CAUSE.

Run & watch keeps the next permitted action beside the cell. Inspect evidence exposes
actual captures, residuals, frames, operands, payloads, Python/source identities and
records. Full Python file always offers its component selector; Saved excerpt remains
separate. Historical and current authority/status are explicitly distinguished.

## Current verification

| Check | Result | Evidence under artifacts/calibration |
|---|---|---|
| Complete pytest campaign, no marker exclusions | **1080 PASS, 0 failed, 0 skipped**, 3325.94 s | final-regression-01.log/.xml; final-regression-summary-01.json |
| Coverage, unchanged 85% gate | **91.18%**; 9704/10643 statements | final-coverage-01.json |
| Lanes in complete campaign | 33 Blender; 41 browser; 208 contract; 57 E2E; 345 integration; 30 live lab; 366 unit | JUnit and grouped summary |
| JavaScript regression | **199 PASS**, no skipped/cancelled tests | node-final-01.log |
| Lint and format | PASS; 343 files formatted | lint-final-candidate-01.log |
| Strict typing | PASS; 108 source files | types-final-candidate-01.log |
| Security | PASS: reviewed static findings, Python/npm audit exit0, vendored hashes match | security-final-01.log; final-01-*-audit.json/security-review.json |
| Browser console/source audit | 41 manifests, zero page errors, source unchanged in each | final-browser-summary-01.json |
| Clean installation | PASS, offline lockfile sync into a new environment; 99 packages | final-clean-install-01.log; final-clean-environment-01.json |
| Fresh CLI seed37/flange and seed97/TCP | Both COMPLETED, one effect, VERIFIED_SUCCESS, WMS acknowledged | final-cli-summary-01.json; final-cli-seed*-01.log |
| Export scientific reproduction | Both PASS, 300 verified artifacts each, matching trace sources and 121 controller samples | final-cli-seed*-reproduce-01.log |
| Local existing publication build | PASS: three reports/64 combined pages, SVG/PDF/link checks | final-publication-01.log; final-publication-summary-01.json |
| Final documentation checks | PASS: 7 contract tests, scoped Markdown links resolve; Git diff check exit0 | final-doc-check-01.log/.xml |
| Independent UI review | All five scored fixes resolved; scoped ship | finish-review-01.md; finish-review-02.md; final-review-01/ |
| Design documentation comparison | Complete; incumbent Operate system preserved | design-documentation-review-01.md |

The one pytest warning is a dependency deprecation: Starlette's TestClient reports
that its httpx integration is deprecated in favor of httpx2. It did not fail a test;
no dependency upgrade was made merely to suppress it. Deliberate rejected/offline
browser requests remain in logs. Existing mocked-network UI tests remain labelled;
new measured acceptance journeys use real local backend operations, including actual
stopped-server/restart recovery. Mocked tests are not the integration proof.

## Criterion verdicts

Every row below uses the same current source, complete regression and supplementary
clean-world evidence. TRACEABILITY.md provides implementation symbols, client paths,
individual test mappings and the detailed PDF/goal requirements.

| Criterion | Result | Current verification |
|---|---|---|
| SC01 Latest-code/legacy preservation | PASS | Legacy contract/unit cases, all regression lanes; final-source-01.json and final-regression-summary-01.json |
| SC02 Known X/Y and transform direction | PASS | test_measured_calibration.py analytical known/unknown-Y, independent OpenCV mapping and rigid-mean checks |
| SC03 Image-driven E2E | PASS | test_calibration_images.py; both seed37/97 browser journeys; final-browser-01 and final-cli-summary-01.json |
| SC04 No oracle shortcut | PASS | test_measured_contract_boundaries.py; test_calibration_operational_boundaries.py physical-only displacement changes measured target |
| SC05 Correct depth/correspondence | PASS | test_calibration_depth_tcp.py, test_calibration_faults.py and tool/depth browser journey |
| SC06 Point versus pose/TCP | PASS | TCP/flange golden fixtures; four SyntheticRuntime/BlenderRuntime mode journeys; both clean CLI worlds |
| SC07 Measurement quality | PASS | Actual RGB repeated/single-axis/timing/settling/ambiguity/printed-ID/readout-outlier browser and numerical tests |
| SC08 Independent validation | PASS | Holdout-cannot-fit, reused-holdout/report rejection, immutable reference journal and point-count RMS tests |
| SC09 Approval gates | PASS | Lifecycle, missing-limit, optics/configuration, no-approval and actual backend browser gates |
| SC10 Runtime consumes calibration | PASS | test_measured_pick.py, operational-boundaries displacement, two browser and two clean CLI picks with WMS acknowledgement |
| SC11 Two cameras | PASS | Real two-camera observation, 30mm conflict, wrong camera/profile/artifact, shared-Y and affected-camera invalidation checks |
| SC12 Drift/recovery | PASS | Both main browser seeds: moved camera -> blocked -> independent checks -> replacement -> resumed operation |
| SC13 Conservative diagnosis | PASS | Analytical scale/rigid/spatial signatures plus actual depth/tool/missed-transfer tests, browser inspection and reproduction |
| SC14 Version/command integrity | PASS | Revalidation/restart/concurrency tests; camera change after effect; real stopped-server recovery; legacy/live-lab deduplication |
| SC15 Inspection/export | PASS | Source/trace/allowlist tests; reference/pixel/target browser inspection; both clean exports reproduce with no changed trace sources |
| SC16 Real browser journeys | PASS | 41 tests/browser passes plus lab browser cases; all measured acceptance journeys use real endpoints; final-browser-summary-01.json |
| SC17 3D/runtime agreement | PASS | 33 tests/blender plus measured runtime/Blender E2E, saved-geometry, marker/renderer and replay agreement tests |
| SC18 Usability/accessibility | PASS | Keyboard/focus/axe/reduced-motion/enlarged-text/narrow tests; rendered review; five fixes resolved and documenter comparison |
| SC19 Existing regressions | PASS | 1080 tests with all lanes; 199 Node tests; lint/type/security; isolated local publication build |
| SC20 Reproducibility/evidence | PASS | Fresh seed37 flange and seed97 TCP: verified pick and 300-artifact reproduction each; final-cli-summary-01.json |

## Presenter client at handoff

The tested code is running on `http://127.0.0.1:8092/` in a new isolated, unapproved
measured cell (seed37/flange), ready at Configure camera. Its data is under
`runs/calibration-final-20261009`; startup/API/read-only browser evidence is
`final-presenter-client-01.json`, `final-presenter-browser-01.json` and
`final-presenter-ready-01.png`. The readiness smoke used the clean environment,
verified served client bytes against the tested source and reported no page errors.
The screenshot was opened and checked. This setup performs no approval or pick.
Only our previous outdated server process was replaced; its data and the user's
other server remain intact. The URL lasts while this local process is running.

## Evidence and reproduction

Large immutable raw worlds, captures and browser traces are under
`D:/RobotOpsTwin-Calibration-Evidence/20261009/`:
`final-regression-01/`, `final-browser-01/`, `final-cli-seed37-flange-01/`,
`final-cli-seed97-tcp-01/`, and `final-cli-seed{37,97}-export-01/`.
The export manifest SHA256 values are respectively
`23def291c08845d4cc6a818c6b4955bd2f52c20109f7592d9eea1bea6c402e78` and
`c4916fb62d5d57a6d55a8756d51d4018d66669e59bbd60db4863f0f399fac8af`.
`final-acceptance-index-01.json` records the final source/document/evidence hashes and
criterion verdicts. Repository logs, XML, coverage, source snapshots and selected screenshots remain
under `artifacts/calibration/`. Neither earlier failed evidence nor saved runs was
overwritten. These large files are intentionally ignored by Git.

Run from the repository root; choose unused output directories:

```powershell
uv sync --locked --all-groups
uv run --locked python -m playwright install chromium --only-shell
uv run --locked python -m apps.api --runtime headless --data-dir runs/measured-presenter-new --port 8093
# In another terminal, or after stopping that foreground server:
uv run --locked python -m tools.calibration --run-dir runs/measured-cli-new --seed 37 --command-mode flange demonstrate --actor 'Simulated presenter' --approve-simulation --authorize-simulated-execution
uv run --locked python -m tools.calibration --run-dir runs/measured-cli-new export --output artifacts/calibration/measured-cli-new-export
uv run --locked python -m tools.calibration reproduce --bundle artifacts/calibration/measured-cli-new-export
# Set isolated ROBOTOPS_POSTGRES_DSN and ROBOTOPS_AMQP_URL for the live-lab lane.
uv run --locked python -m pytest tests -q --cov=robotops --cov=apps --cov-report=term
uv run --locked python -m tools.dev lint
uv run --locked python -m mypy robotops apps/api tools/calibration.py
uv run --locked python -m tools.dev security
$testFiles = @(Get-ChildItem -LiteralPath tests/ui -Filter '*.test.cjs' | ForEach-Object { $_.FullName })
node --test $testFiles
```

The hardware-free headless demonstration requires neither Blender nor the distributed
lab. Full acceptance requires the installed Blender executable and isolated live lab;
see the repository lab setup and VERIFICATION.md. The Windows documentation build
uses the existing Pango/Cairo/Fontconfig environment described in PUBLICATION.md and
a new isolated copy. That build is a regression check, not a deployment or certification
of all PDF layouts. Its input manifest predates this final acceptance report.

## User journeys, design guidance and limitations

The real client covers first configuration and missing approval; both-camera calibration,
validation and explicit approval; measured pick and full inspection; moved-camera block
and recovery; invalid depth/tool faults; degenerate/ambiguous/wrong-board images; a missed
transfer with unresolved cause; real outage/restart and historical mutation denial;
controlled saved-estimate revalidation; and read-only replay/export. Representative
rendered evidence includes desktop, narrow, laptop1280x720, enlarged text, failed pick
and history. The complete next recovery action and useful scene now fit together at
1280x720, and selected source mode is visually apparent. No task times or usability
scores are invented.

The installed skills and provenance remain in ../client-rebuild/skills.md and its
manifest. Impeccable guided task hierarchy, the bounded independent finish review and
documentation handoff. Vercel guidelines informed native semantics, keyboard/focus and
honest feedback. UI/UX Pro Max supported readable density and focus without changing
brand/framework. Playwright operates the real application through the existing reusable
pytest suite. No hooks were installed or approved; automatic skill discovery was not
claimed, and skill instructions were read explicitly. TRACEABILITY.md maps all ten
UX principles to behavior and observable checks.

No mandatory simulation acceptance blocker remains. Remaining limits are explicit:
synthetic factory/tool metrology and SIMULATION_ONLY tolerances; ideal gantry rather
than accurate HKM1800 kinematics; known colored-cube perception rather than general
recognition; no real-hardware commissioning or safety certification; no human usability
study or real screen-reader test. Automated axe/keyboard checks and agent render review
do not establish full WCAG conformance. See LIMITATIONS.md for uncertainty, export
snapshot and loaded-source attestation boundaries. The Swedish live demonstration is
in PRESENTER.md. Historical acceptance reports and release claims remain unchanged.
