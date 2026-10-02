# Local operations and observability

On Windows, the [desktop app](desktop.md) starts this same dashboard in its own
window and stops its owned backend/Blender processes when closed. Desktop data is
persistent under `%LOCALAPPDATA%\RobotOpsTwin\data`; it uses an OS-selected port.
The following command remains the independently managed browser/server mode.

Start the loopback-only dashboard:

```
uv run --locked python -m apps.api --runtime blender --port 8000 --data-dir runs/my-demo
```

Open http://127.0.0.1:8000. Use a new data directory for a fresh physical fixture;
reusing a directory preserves orders, world, journal and evidence. Startup recovers
unfinished work without replaying uncertain commands. This local demo has no
production authentication/authorization boundary and binds to loopback only.

Choose a product and fault, then Create and run order. Lost acknowledgement after
effect displays UNKNOWN_OUTCOME even though Blender has moved the product. Use
Reconcile selected job with a normal fresh observation to complete it. Selecting
contradictory/missing/low-confidence/stale evidence instead yields intervention.
Cell reset preserves uncertain jobs and does not restore products to the source.

The dashboard exposes ERP order, job and logical cell status separately, plus
original command identity, journal status, verifier reason, causal timeline,
observation/reconciliation JSON, live motion and the selected order's Blender
artifact. [Replay controls](playback.md) read evaluated Blender frames, preserve
uncertainty and never send another pick. Neither images nor animation establish
business success. Fault controls are synthetic local fixtures.

`GET /metrics` derives counters from persisted events. Received/completed/failed/
unknown/intervention totals count entries into those states; current-state gauges
reflect present status. Reconciliation is labelled by verdict. Commands count
durable intents, duplicates count journal suppression, injected failures count
explicit workflow injections once (not their mirrored controller event).
Pipeline latency is wall duration measured monotonically for each run attempt,
reported as histogram/count/sum in seconds; it is not physical cycle-time evidence.

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
