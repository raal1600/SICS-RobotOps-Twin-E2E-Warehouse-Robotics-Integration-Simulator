# Local operations and observability

On Windows, the [desktop app](desktop.md) starts this same dashboard in its own
window and stops its owned backend/Blender processes when closed. Desktop data is
persistent under `%LOCALAPPDATA%\RobotOpsTwin\data`; it uses an OS-selected port.
The following command remains the independently managed browser/server mode.

Start the loopback-only dashboard:

```
uv run --locked python -m apps.api --runtime blender --port 8000 --data-dir runs/my-demo
```

Open http://127.0.0.1:8000. Use **Start new test** for every new combination:
choose **Robot cell** in **New simulation test**, then **Create test**. It retains
scenario/observation selections and creates an independent world. The registry
currently offers only the HKM-inspired cell, with six catalogued products at
their own source boxes; legacy cell metadata labels history but is not selectable.
Fresh API data directories also use this profile. Existing saved worlds keep
their own profile; opening a historical three-product test does not upgrade it.
The previous test remains unchanged in **Simulation test** history,
including uncertain/intervention outcomes. Review its evidence and full replay
in the same window; **Return to current test** resumes the active world.
Startup recovers only that active world, without replaying uncertain commands.
Retained archives remain read-only during ordinary inspection. Under **Manage test
data**, **Clear test and retry** keeps the selected test's number/cell and your
scenario choices, removes its old orders/evidence and restores products. It makes
that fresh test current, including when you explicitly clear an archive.
**Delete selected test** removes its world and catalog entry completely;
**Delete all tests** removes the confirmed displayed set. Available numbers are
reused, starting at Test 1 when empty, without renumbering retained tests.

Confirmation identifies the discarded data; cancellation changes nothing.
Neither action runs/reconciles a pick. Deletion never promotes an archive.
Busy work blocks these actions. Durable pending intent resumes after interrupted
cleanup/reset; duplicate requests cannot erase later runs. The catalog retains
only anonymous request digests after deletion, not hidden test records. See
[ADR 0013](../adr/0013-reusable-test-lifecycle.md).

This local demo has no
production authentication/authorization boundary and binds to loopback only.

The dark workspace follows **Set up / Watch / Investigate / Continue**. A short
scenario purpose and **Watch for** line explain what to expect before running.
The cell stays central; an amber guide and highlighted **Investigate this pick**
button identify unusual outcomes. The operator opens the bounded panel explicitly;
polling never steals focus or obscures the animation. **What happened** separates
symptom, confirmed record contents, their limits and possible explanation.
**Evidence** exposes the original command/journal, exact assessed observation,
verification/review history, tool decision and full JSON. The event timeline is
collapsed, filtered and height-bounded, with each full record available on demand.

**Manual inspection** offers test/job-scoped GET requests, evidence/event download,
recorded-fault reproduction guidance and actual repository/storage/log locations.
Investigation pins its own context while preserving the replay selection/frame;
opening it pauses only the replay. **Back to simulation** retains that view, and
Play resumes explicitly. The guide can inspect the blocking pick while an older
replay stays selected. New tests invalidate old panel responses. The
[investigation walkthrough](investigation.md) and ADR 0012 explain these boundaries.

Execution choices apply to a new order and its first post-pick check. **Sensor
report for the next check** changes only a later explicit reconciliation capture,
not the product position. Expand the scenario/sensor explanation and comparison
sections for definitions and differences. **Use normal observation** only changes
the selector; the named reconciliation action collects the report. Detailed
[scenario definitions](scenarios.md) describe similar-looking outcomes. Actual
service failures are labelled **App request problem**, separately from simulation
results. Cell & diagnostics, advanced replay selection and test-data management
are progressive disclosures; technical depth remains available.

Choose a product and fault, then Create and run order. Lost acknowledgement after
effect displays UNKNOWN_OUTCOME even though Blender has moved the product. Use
the named Reconcile [product] action in the investigation panel (or Reconcile selected job)
with a normal fresh observation to complete it. An uncertain pick pauses the
whole cell, so choosing another product cannot bypass this step. Each pick in
the lost-ack scenario requires reconciliation before the next explicit order. Selecting
contradictory/missing/low-confidence/stale evidence instead yields intervention.
To continue that same test, choose an observation mode and click **Observe
again and reconcile** (or **Observe again: [product]** in the investigation panel). The new capture
checks the original command without another pick. The unchanged verifier either
resolves the job or pauses it again. Every attempt stays in the causal timeline;
Normal observation cannot establish success if the journal is missing/conflicting.
Restart and reviewing evidence leave intervention paused until this explicit action.
Cell reset preserves uncertain jobs and does not restore products to the source.
Products already at the destination are unavailable for another source pick.
Changing Execution scenario only configures the next order. For another
independent combination, Start new test works regardless of the old outcome;
only an in-flight operation blocks creation. If the scene is depleted, the main action reads
Start new delivery and run order; fixture preparation precedes the new order.
The fresh-scene action creates a new epoch only when all jobs are COMPLETED or
FAILED and no worker owns the cell. It cannot clear uncertain/intervention jobs.
Interrupted fixture preparation resumes the same durable reset identity on startup.
The optional **Restock this test** section exposes this guarded operation;
it is distinct from creating another test (ADR 0007).

The dashboard exposes ERP order, job and logical cell status separately, plus
original command identity, journal status, verifier reason, causal timeline,
observation/reconciliation JSON, an always-visible 3D cell, scenario events, live
machine/product motion. The selected order's saved Blender snapshot is available
under **Technical details**, collapsed by default. The full 3D view and replay
remain the main visualization. [Replay controls](playback.md) read evaluated Blender frames, preserve
uncertainty and never send another pick. Neither images nor animation establish
business success. Fault controls are synthetic local fixtures.
The default Full delivery scope replays all product runs in the selected scene.
Saved deliveries remain selectable after scenario changes. Individual product
details and replay remain available; their business identities are unchanged.

The Evidence tab’s expandable technical details add the observed tool and observation confidence/model/calibration.
The replay phase/tool display identifies the currently viewed frame, which may
belong to an earlier delivery item. **Why this tool?** reads the persisted six
candidate scores and mass/geometry/availability reasons. **Run six-tool showcase
(happy path)** explicitly picks and verifies all six SKUs in order; it cannot
bypass unresolved work. Operator, Overhead, Side inspection and Follow TCP are
presentation cameras, not evidence-capture actions.

`GET /metrics` derives counters from persisted events. Received/completed/failed/
unknown/intervention totals count entries into those states; current-state gauges
reflect present status. Reconciliation is labelled by verdict. Commands count
durable intents, duplicates count journal suppression, injected failures count
explicit workflow injections once (not their mirrored controller event).
Pipeline latency is wall duration measured monotonically for each run attempt,
reported as histogram/count/sum in seconds; it is not physical cycle-time evidence.
Additional counters expose orders, product effects, completed tool changes,
selection failures, trajectory plans/rejections, collision-preflight failures,
observation degradations and reconciliation outcomes. The application also exposes
`robotops_pipeline_latency_ms` and `robotops_simulated_motion_duration_s` separately.
Synthetic duration is summed once for each effect-bearing original command;
duplicate delivery and playback speed do not inflate it.

Structured AuditEvent records carry UTC timestamps, component/type, causal IDs,
order/job/command IDs, transition states, reason, duration and evidence references.
Controller RobotEvents retain epoch and scene step. Imported controller events may
arrive later than their timestamp; causal links and original timestamps are kept.
`GET /jobs/{job_id}/evidence` retrieves typed persisted observations/results.

Configuration: pass `--settings path.json` using Settings schema (thresholds,
freshness, bounds/frame/calibration, timeouts, lease, seed/noise, products/locations,
retry policy). CLI controls database directory, runtime and port. No secret is
required. Retry policy is manual after proven no-effect; arbitrary values do not
enable automatic retries. Optional remote ERP/model/hardware work is non-blocking.

Historical guided-workspace captures and validation remain in
`docs/evidence/guided-workflow-local.json`; they do not depict the current layout.
The current browser suite writes screenshots, traces and results under
`artifacts/investigation-browser/`, with revision-scoped acceptance evidence.
