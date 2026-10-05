# Run a pick, notice the result, inspect its evidence

The cell moves one product from its source box to the output tote. A normal pick
also receives a reply and verifies a reliable sensor report before completing.

1. In **Run a pick**, choose a product and **Execution scenario**. Read the short
   description and **Watch for** line, then **Create and run order**.
2. Watch the cell and its result badge. **UNKNOWN_OUTCOME** means the app cannot
   confirm the result; it is different from a failed pick. An amber guide and
   highlighted **Investigate this pick** button identify work needing attention.
3. Open **Investigate this pick**. **What happened** separates the symptom,
   confirmed record contents, their limits and possible explanations. The replay
   pauses at its current frame; the robot workflow is not paused by this view.
4. Choose **Inspect the supporting evidence** for the original command/journal
   and exact sensor report used in the latest decision. Verification history,
   tool-selection reasons, exact IDs and full JSON remain expandable. The
   **Event timeline** is collapsed and bounded; select an event reason for its
   full record, including available correlation/causation IDs.
5. **Manual inspection** offers PowerShell GET requests for this test/job,
   **Download evidence & events (JSON)**, recorded execution-fault guidance and
   the actual source and local file locations. These are investigation entry
   points, not a claim that a root cause has been proved.
6. **Back to simulation** retains your replay selection and frame. Press Play to
   resume it. Reopening the same investigation retains its tab. Choosing another
   test closes the old panel and cannot display its delayed responses as new data.

For the lost-reply example, the robot log may record one movement while the app
has no verified result. In **What happened**, choose **Sensor report for the next
check** and click the named **Reconcile** or **Observe again** action. This
collects another observation and checks the original command; it never picks
again. A normal fresh report may resolve the result when it agrees with the
journal. Missing, stale, low-confidence or contradictory evidence can remain
unresolved. **REQUIRES_INTERVENTION** keeps this investigation available; it does
not invent success or failure. Observation choices change evidence quality, not
product positions. [Definitions and comparisons](scenarios.md) explain each mode.

The guide prioritizes an unresolved pick even when you replay an earlier one.
Its review action opens the blocking pick's evidence without changing that replay.
The inspector header and exact command ID identify what is being investigated.
Explicit reconciliation is a separate state-changing action, scoped to the
original uncertain command. Saved tests expose the same evidence read-only.
**Start new test** creates an independent world; **Manage test data** contains
explicit confirmed deletion. Neither is an implicit recovery step.

Actual HTTP/service problems appear as **App request problem**, separately from
the persisted simulation result. The workflow guide reports execution state;
Play/Pause controls only recorded presentation. The static Blender image remains
an optional collapsed technical checkpoint. Neither that image nor the 3D scene
is the sensor report used by the verifier.

## Technical boundary and reproducible browser checks

`apps/erp_ui/workflow-guide.js` derives descriptions from typed evidence and
job/order-scoped events. `app.js` pins inspector context, builds scoped read-only
requests and renders the exact assessed observation. `playback.js` owns the
presentation cursor. No new robot/API wire schema or workflow transition is added.
The exported JSON wrapper identifies format `robotops-investigation-1`, test ID,
JobEvidence and **order_events** (the full order timeline, possibly several jobs).
The on-screen timeline filters to the inspected job and shared order events.

After installing the locked environment and Chromium, run:

```sh
uv run --locked python -m pytest tests/browser/test_investigation.py -q
```

The suite starts disposable loopback servers with real SQLite and runs both
synthetic and actual Blender paths at desktop and compact viewports. It performs
normal execution, lost reply, evidence/manual inspection/download, return,
contradictory and normal re-observation, and saved-history review. It checks exact
command ownership, one effect, no navigation writes, no browser errors, bounded
timeline/dialog geometry and keyboard tabs. A separate intentional 503 checks
error presentation without relabelling a job as a simulated failure.

Screenshots, a Playwright `trace.zip`, browser request/error records, downloads and
semantic results are saved under `artifacts/investigation-browser/<run>/<case>/`.
Each acceptance run also keeps its own JUnit and source attribution. Use
`uv run --locked python -m playwright show-trace <trace.zip>` for detailed review.
These functional checks do not replace first-time user testing or validate real
hardware. The narrow viewport verifies layout/access, not a touch-device or
screen-reader usability study. [ADR 0012](../adr/0012-evidence-driven-investigation.md)
records the design decision and preserved boundaries.
