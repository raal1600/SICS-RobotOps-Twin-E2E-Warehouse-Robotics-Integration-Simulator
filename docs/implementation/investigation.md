# Run a pick, notice the result, inspect its evidence

The Guided Integration Console follows one order from synthetic enterprise intent
through persisted command delivery, simulated robot motion, verified evidence and
business acknowledgement. **Create and run order** creates a saved session at
stage 1. It does not start the robot or secretly execute the workflow.

1. Choose a product and **Execution scenario**, then **Create and run order**.
   The console shows the session/correlation IDs and a pending bounded stage.
   The named action in **Execution now** executes that stage and persists its
   evidence. The eight-phase journey is read-only navigation: selecting a phase
   filters its saved attempts without executing anything. Timestamps and durations
   are backend values. **Inspecting** identifies the selected historical stage;
   **Follow current** clears filters and follows the latest saved result. A pending
   stage has no result until it runs. The execution action always targets the
   backend's current stage, even while an older step is selected.
2. Review ERP/WMS intent, versioned REST validation, durable intake, fresh sensor
   observation, planning and independent plan validation. Database commit is not
   execution. The immutable command and transactional outbox exist before dispatch.
3. Authorize distributed dispatch and PLC submission at their named gates. Local
   mode labels its transport **SIMULATED SYSTEM**; the lab profile records actual
   AMQP and OPC UA operations as **REAL PROTOCOL**. Neither publisher confirmation,
   consumer acknowledgement nor PLC acceptance proves a physical effect.
4. At **READY FOR PHYSICAL EXECUTION**, review the command and explicitly click
   **AUTHORIZE ROBOT EXECUTION**. The browser then requests the separate physical
   stage. The docked robot context shows the existing recorded runtime and read-only
   protocol status alongside the trace and inspector. The controller interface and
   robot are simulated; the button is not a
   certified safety function. There is no approval per animation keyframe.
5. Continue in the same workspace for controller result, fresh post-execution observation
   and verification. Continue through WMS acknowledgement and ERP status to the
   final correlated trace. Verified physical work alone does not complete these
   business stages. A WMS outage retries acknowledgement, without robot motion.
6. Select a persisted stage to read its meaning, responsibility, important input,
   state change, storage, supporting records, proof limits and recovery. Expand
   **Data / State / Protocol / Source / Recovery / Raw JSON** for deeper inspection.
   These retain the concepts previously exposed by **What / Wire / Code / State /
   Why / Failure semantics**. Search and filters narrow the trace by status,
   component, protocol, perspective or repeated/failed attempts. Payloads, state
   changes, exact source path/symbol/excerpt and evidence IDs come from the backend.
   Reload resumes persisted execution; viewing or reconnecting the read-only trace
   stream never authorizes work. Historical selection is a browser view, not a
   persisted execution cursor.
7. From a selected stage, open **Investigate this job · evidence & timeline**, or
   use **Investigate this pick** in the robot viewer. Both reuse the existing
   investigation dialog. **What happened** separates
   the symptom, confirmed record contents, their limits and possible explanations.
   **Evidence** retains the original command/journal, exact assessed sensor report,
   verification history, tool selection and expandable JSON. Its bounded timeline
   lets you select the complete event record.
8. **Manual inspection** offers test/job-scoped PowerShell GET requests and
   **Download evidence & events (JSON)**. **Back to simulation** retains the replay
   selection and frame. Play resumes that presentation; it does not execute a pick.

The **proof ladder** links each major boundary to its supporting saved step. A
completed handler or attractive replay cannot establish a later outcome. Local
in-process publication remains a simulated boundary, not a broker confirmation.
The ladder covers the current job's robot boundaries and the order's business
intent, durable intake and ERP completion; inspect earlier jobs through the trace.
An observation being captured does not by itself prove its freshness or quality.
The separate verification record supplies that assessment.

**Source** displays the saved Python excerpt with its real indentation and line
breaks, plus the file path and function name. **Full Python file** reads the current
application file and scrolls to the matching excerpt when present. This current
file is reference material, not a source snapshot from the older run; its label,
line count and displayed-content SHA-256 make that distinction explicit. **Saved
excerpt** returns to the recorded code. The read endpoint only serves known stage
source files, redacts sensitive values and never executes Python or changes the
run. [Source-view follow-up evidence](../evidence/source-view-20261007/README.md).

**Download saved run (JSON)** exports the sanitized session and its stage records,
including evidence references and the read-only workbench projection. The format
is `robotops-guided-run-v1`. Referenced job records and motion files are not embedded;
use the existing job investigation export for job evidence and events. Neither
download changes the session revision or authorizes work.

The uncertainty panel separates known facts from outcomes not yet proven. A WMS
failure has a distinct business-recovery state and **Retry WMS acknowledgement**
action. A saved successful physical result is retained while the business update
is retried. [Workbench implementation and acceptance evidence](evidence-workbench.md)
describe the current local enhancement separately from historical release audits.

The six-tool showcase creates one guided order with six lines. Each line reaches
its own explicit physical gate and WMS acknowledgement before the order's final
ERP stage. It does not bypass the integration console.

For the lost-reply example, the robot log may record one movement while the job
remains **UNKNOWN_OUTCOME**. The guided post-execution stages can already contain
a fresh observation and assessment; explicit reconciliation still resolves the
original uncertain dispatch before business acknowledgement. In **What happened**, choose **Sensor report for the next
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
the persisted simulation result. The integration console reports the authoritative session and business stage;
Play/Pause controls only recorded presentation. The static Blender image remains
an optional collapsed technical checkpoint. Neither that image nor the 3D scene
is the sensor report used by the verifier.

## Technical boundary and reproducible browser checks

`apps/erp_ui/integration-console.js` renders persisted execution sessions and
requests individual REST authorizations. `robotops/integration/engine.py` uses
the same bounded core handlers as automatic `Engine.run`; SQL transactions close
before human waiting. `apps/erp_ui/workflow-guide.js` derives descriptions from typed evidence and
job/order-scoped events. `app.js` pins inspector context, builds scoped read-only
requests and renders the exact assessed observation. `playback.js` owns the
presentation cursor. Guided session/step/authorization/trace contracts extend the
API while preserving the existing robot command and evidence contracts.
The exported JSON wrapper identifies format `robotops-investigation-1`, test ID,
JobEvidence and **order_events** (the full order timeline, possibly several jobs).
The on-screen timeline filters to the inspected job and shared order events.

After installing the locked environment and Chromium, run:

```sh
uv run --locked python -m pytest tests/browser/test_investigation.py tests/browser/test_guided_console.py tests/browser/test_workbench_console.py -q
```

The suite starts disposable loopback servers with real SQLite and runs both
synthetic and actual Blender paths at desktop and compact viewports. It performs
explicit guided authorization, the physical gate, normal execution, lost reply,
evidence/manual inspection/download, return,
contradictory and normal re-observation, and saved-history review. It checks exact
command ownership, one effect, no navigation writes, no browser errors, bounded
timeline/dialog geometry and keyboard tabs. A separate intentional 503 checks
error presentation without relabelling a job as a simulated failure.
An active read-only WebSocket regression clears and deletes its watched test,
checks the stream closes, and verifies that reading cannot recreate deleted world files.

Screenshots, a Playwright `trace.zip`, browser request/error records, downloads and
semantic results are saved under `artifacts/investigation-browser/<run>/<case>/`.
Each acceptance run also keeps its own JUnit and source attribution. Use
`uv run --locked python -m playwright show-trace <trace.zip>` for detailed review.
These functional checks do not replace first-time user testing or validate real
hardware. The narrow viewport verifies layout/access, not a touch-device or
screen-reader usability study. [ADR 0012](../adr/0012-evidence-driven-investigation.md)
records the design decision and preserved boundaries.

[Historical source-specific results and screenshots](../evidence/investigation-ui-final/README.md)
cover clean `7b9f0a6` on Windows and Linux. Its 118 MUSTs and five browser cases
apply only to that historical source, not to the current integration-lab goal. The evidence keeps the earlier
failed label assertion and its correction, rather than hiding it. The visual
assessment remains an implementer review; independent novice, touch-device and
screen-reader studies have not been performed.

For another attempt with the same test, choose **Manage test data → Clear test and
retry**. Confirmation discards that test's old evidence, restores products and
keeps its number/cell and your scenario choices. **Delete selected test** removes
the test entirely. Reused display numbers are labels; technical test/job/command
UUIDs still distinguish independent evidence. Clearing invalidates old inspection
and replay context before loading the restored world (ADR 0013).

The historical df45c93 revision added four clear/retry/delete/create browser
cases. Those nine cases now drive explicit guided authorization, with a tenth
active-watch lifecycle regression; current
acceptance must be run again against the changed source. The
[historical evidence](../evidence/test-reset-final/README.md) preserves source hashes,
restored-world assertions and exactly one effect from each explicit retry.
