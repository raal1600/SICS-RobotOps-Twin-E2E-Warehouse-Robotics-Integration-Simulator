# Test management development evidence

Isolated local review on 2026-10-04, based on
`ae6d5d85c813e47aea042aea2a87236b5a8bc204` with the lifecycle change uncommitted.
These are scoped development results, not final-source acceptance.
The final twice-run acceptance manifest records its own exact source identity.

- `ui.log`: 119 Node UI checks, including cancellation, cell selection, deletion,
  empty workspace, stale history and lost-response retry identities.
- `docs.xml`: 71 governance, robotics documentation and schema checks.
- `backend.xml`: 146 targeted backend cases, including all 32 new lifecycle
  checks; five Blender cases were deselected only for this targeted run and
  remain in the mandatory full acceptance suite. `backend-smoke.xml` contains
  six final empty-workspace/path/startup checks.
- `api-desktop-replay.xml`: 137 affected API, desktop, replay, fresh-scene and
  contract regressions, all passed with zero skips.
- `desktop-lifecycle.json` and `desktop-clear-reopen.json`: actual Windows EXE
  lifecycle and clear-all/reopen checks in separate owned data roots. Hidden
  native-window text inspection was unavailable and is not claimed; the browser
  screenshots cover the rendered empty-workspace panel.
- `independent-review.json`: corrected lifecycle review with per-file hashes.
  The two `initial-*-finding.json` files preserve the earlier startup-contention
  and orphan-profile defects; they were fixed and gained regression tests.
- `security-review.json`: dependency audit and reviewed bounded subprocess checks.
- `publication-build.json`: source documentation/PDF build with 110 MUST criteria,
  30 references and 11 diagrams. Its Git SHA identifies the base of this dirty
  development build, not a clean acceptance of the changed sources.

Browser review used only `runs/test-management-review` at localhost port 8017.
The existing desktop data directory was not changed. The new-test dialog offered
the HKM-inspired cell and created six fresh product families. A happy-path pick
reached COMPLETED; deletion then identified that test and its one order. After
confirmation, the saved original test remained read-only and no active test was
selected. Clearing the remaining original removed its workflow/runtime files.
Restart returned an empty history and healthy API without recreating those files;
the empty-state button created Test 3 with the HKM cell and six products.

The screenshots show the cell selector, deletion scope, empty restart and fresh
cell after restart. `mobile-new-test.png` was checked at 390×844 with no horizontal
page overflow; the dialog stayed within the viewport. Browser error collection
was empty. One early automation attempt waited for a hidden dialog as though it
were visible and timed out; subsequent checks used awaited DOM handlers and
inspected persisted application results. That automation failure is not counted
as a passing application test.
