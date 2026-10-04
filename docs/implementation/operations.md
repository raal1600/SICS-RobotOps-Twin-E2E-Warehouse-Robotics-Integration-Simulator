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
it retains scenario/observation selections and creates an independent world with
six catalogued products, each at its own source box in the HKM-inspired cell.
Fresh API data directories also use this profile. Existing saved worlds keep
their own profile; opening a historical three-product test does not upgrade it.
The previous test remains unchanged in **Test history**,
including uncertain/intervention outcomes. Review its evidence and full replay
in the same window; **Return to current test** resumes the active world.
Startup recovers only that active world, without replaying uncertain commands.
Archives remain read-only. This local demo has no
production authentication/authorization boundary and binds to loopback only.

The dark workspace has a persistent Next step card and Prepare / Run / Review /
Continue indicator. Each execution/observation choice shows its stage, definition,
key difference and expected behavior. Expand Compare all execution scenarios or
Compare all observation modes to read them together. The execution selector
applies to a new order and its first post-pick check; the observation selector
applies only to the next explicit reconciliation capture. See the
[definitions and comparisons](scenarios.md) for similar-looking outcomes.
Run it, then follow the resulting guide. An uncertain/intervention job automatically
opens and focuses Review evidence once; regular polling and repeated observations
do not move keyboard focus. The panel names the original product/job, summarizes
the journal, exact assessed observation, latest verifier reason and saved attempts.
A pre-pick planning capture is never shown as an assessed post-pick observation.
Inspect full evidence & timeline navigates to that same original job, even if an
older replay was selected. Neither navigation nor viewing evidence submits work.
Use normal observation only changes the selector and focuses the explicit review
action. Its helper text does not promise success. Any supported observation mode
can be repeated in this same test. The guide prioritizes unresolved work, then
cell reset, then next-pick setup or a new test for an exhausted delivery. Cell &
diagnostics and advanced replay selection are expandable. See ADR 0009.

Choose a product and fault, then Create and run order. Lost acknowledgement after
effect displays UNKNOWN_OUTCOME even though Blender has moved the product. Use
the named Reconcile [product] action in **Review evidence** (or Reconcile selected job)
with a normal fresh observation to complete it. An uncertain pick pauses the
whole cell, so choosing another product cannot bypass this step. Each pick in
the lost-ack scenario requires reconciliation before the next explicit order. Selecting
contradictory/missing/low-confidence/stale evidence instead yields intervention.
To continue that same test, choose an observation mode and click **Observe
again and reconcile** (or **Observe again: [product]** in **Review evidence**). The new capture
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

The status strip adds the observed tool and observation confidence/model/calibration.
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

Local guided-workspace captures: [dark desktop view](../evidence/guided-workflow-dark.png)
and [mobile intervention review](../evidence/guided-workflow-mobile.png).
The [validation record](../evidence/guided-workflow-local.json) distinguishes
isolated test writes from read-only inspection of the user's open session.
