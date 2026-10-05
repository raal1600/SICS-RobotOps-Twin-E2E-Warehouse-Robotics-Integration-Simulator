# Full 3D cell and scenario replay

The Windows EXE and browser dashboard always show the environment, machine and
products, before orders and for every scenario. The interactive perspective view
uses offline Three.js, with a software 3D fallback when WebGL is unavailable.
Fresh worlds use the original procedural HKM1800-inspired hybrid-kinematic
manipulator, six product families, six tools and a bounded synthetic workspace.
This is visual kinematics, not the real HKM mechanism or validated dynamics.
Blender and the browser consume the same named primitive geometry. Saved
schema-1 worlds retain the historical Cartesian gantry and positional recordings.

The product selector shows current fixture availability. **Start new test** is
always present and creates an independent world while keeping scenario and
observation selections. **Test history** opens previous evidence and full-delivery
replay read-only in the same window, even for unresolved outcomes. New test
creation never resolves or replays the previous command. A running operation
must finish first. Changing **Execution scenario** only configures the next order. After
all products are picked, **Start new delivery and run order** explicitly prepares
another scene before running the chosen product. **Start fresh scene** also
remains available. Fresh scenes are blocked by active or unresolved jobs.
**Reset logical cell state** clears a logical stop/fault but does not move products.

**Delivery replay** selects a current or saved scene. **Full delivery (all products)**
is the default scope: Replay and the scrubber span every product execution in
the original execution order. **Selected product execution** replays just the
chosen item in **Product execution details**. Six picks therefore appear as
one delivery with six segments; each retains its own command and outcome.
Earlier delivered products use their saved positions in later clips. Preparing
a fresh scene preserves the earlier delivery; starting a new test retains that
world's deliveries under Test history. Explicit **Delete selected test** or
**Delete all tests** removes that evidence after confirmation. **Clear test and
retry** instead retains the test number/cell but removes its old recordings and
restores a fresh scene. Revision changes invalidate old replay/inspection context
(ADR 0013).
Those catalog actions are separate from playback; replay, camera selection,
scrubbing and opening history remain read-only. Deleting the active test leaves
no active world and clears its displayed replay instead of promoting an archive.

The display-refresh loop draws at up to 24 fps, matching the recording and
independent of display refresh rate. The playback cursor still uses elapsed presentation time and the
selected speed. This bounds CPU-renderer contention with Blender during a live
pick; it does not change recording frames, render quality, execution deadlines or
the conservative outcome of a real timeout. Incoming evidence and explicit
scrub/step actions redraw immediately. Before confirmed test management,
background polling pauses and outstanding JSON/snapshot response bodies finish.
The snapshot is fetched before displaying a local blob URL so its file response
participates in the same drain. A five-second stalled-view wait sends no management
request and offers explicit retry. Polling and controls resume after the returned
test/revision and its final refresh are applied. Other clients' active reads,
downloads and running work still block destructive backend operations.

The Blender authoring path avoids resetting unchanged visibility flags, while
retaining all animation keyframes. Its Windows child process uses Blender's
`--qos high` scheduling option; saved-scene export uses the same bounded invocation.
These runtime performance choices preserve replay data and render quality.

An uncertain pick pauses the entire cell, including picks of different products.
The Run button says **Next pick paused — reconcile first**, with a named-product
explanation and **Reconcile [product]** action beside it. This action targets the
blocking job even when historical details are selected, and uses the selected
observation mode. It sends only reconciliation, never a replacement pick
or the next order. If evidence is inconclusive, **Observe again: [product]**
collects another selected fresh observation for the same command. The guard stays
in force until sufficient evidence resolves it. Every assessment joins the replay
as investigation events; the original motion appears only once. Evidence inspection
remains available independently, and never changes the result (ADR 0008).

- Drag to orbit, scroll to zoom, right-drag or Shift-drag to pan. The Rotate,
  zoom buttons and Reset camera also work with a keyboard.
- Pause / Play stops or resumes the view. Replay restarts the same scenario;
  it never sends a command. The slider scrubs received motion and saved events.
- Previous/Next frame steps through the received track and pauses presentation.
- Operator, Overhead, Side inspection and Follow TCP change presentation only;
  switching views never captures sensor evidence or changes calibration.
  Browser overhead/side presets use an 84-degree vertical field of view to frame
  the full cell; Operator, Follow TCP and Reset use 42 degrees. WebGL and software
  projection share this framing. These are presentation settings, not changes to
  the canonical synthetic camera model or observation evidence.
- Speed selects 0.25x, 0.5x, 1x, 2x or 4x playback time. Event steps use a readable
  half-second pace, while motion labels show Blender frames and simulation time.
  Original event timestamps remain available in the causal timeline.
- Load saved animation reads an older order's original keyed Blender scene
  without a new pick. It does not replace that scene with today's model.

| Execution scenario | Machine and product | Business result before reconciliation |
|---|---|---|
| Happy path | Recorded pick and place | COMPLETED |
| Lost acknowledgement after effect | Recorded pick and place | UNKNOWN_OUTCOME |
| Lost acknowledgement before effect | Stationary starting scene; controller rejection event | UNKNOWN_OUTCOME |
| Contradictory / low-confidence / stale observation | Recorded pick and place; observation problem in event replay | UNKNOWN_OUTCOME |
| Logical E-stop / cell fault | Stationary scene; blocked/rejected event | FAILED with fresh no-effect evidence |
| Invalid Brain output / Brain timeout | Stationary scene; planning rejection | FAILED, no dispatch |

Missing observations, pose uncertainty and robot-command failure are also
supported by the API and scenario tests. Missing/corrupt/partial recordings are
explicitly labelled. A stationary reference alone never proves no effect.

New orders save their starting layout before planning; later orders and restart
cannot change that historical view. Legacy orders with neither a starting snapshot
nor recorded poses show a labelled current cell reference, not invented history.
Headless runs show scene and events but explicitly have no Blender motion trace.

Try lost acknowledgement after effect: the product moves, but the job remains
UNKNOWN_OUTCOME. Replay repeatedly, then reconcile with contradictory evidence:
it still requires intervention. Scene/motion data is simulator truth for human
explanation, not WorldObservation or input to Brain/Verifier.

## Protocol and persistence

`GET /jobs/{job_id}/playback` returns the versioned JobPlayback contract with the
original command ID, current job state, recording status, starting VisualScene,
product identity, audit events and optional motion. GET /cell/scene supplies the
current initial environment. PresentationSnapshot stores each new job's immutable
starting WorldState in the workflow database, exclusively for human replay.
`GET /deliveries` returns DeliverySummary/DeliveryExecution records grouped by
saved scene identity. `GET /deliveries/{delivery_id}/playback` returns the original
JobPlayback records in durable execution order through DeliveryPlayback. These
are presentation groups, not new ERP orders. Old attempts with no saved scene
identity remain available individually. No replay endpoint dispatches or resets.
Statuses are WAITING, RECORDING, RECORDED, PARTIAL or UNAVAILABLE. An interrupted
recording retains its last frame and is not extrapolated to the destination.
If an abruptly killed job still holds its lease, RECORDING may remain visible;
the frame counter stops, and existing conservative recovery rules apply.

`POST /jobs/{job_id}/playback/import` creates only a derived recording from the
original hash-checked scene. `GET /jobs/{job_id}/artifact.png` retrieves that job's
render. The old `/artifacts/latest.png` endpoint remains compatible.
The dashboard keeps this static image under **Technical details**, collapsed by
default and labelled **Saved Blender snapshot**. Opening it does not execute or
reconcile anything; the full 3D cell and replay remain the primary visualization.

MotionRecording includes command/job/product/epoch IDs, frame ID, metre units,
24 fps and object geometry. Schema 1 retains 100 frames and its 2 MB bound.
Schema 2 records up to 720 contiguous frames within a 32 MB bound, with actual
evaluated world position/quaternion/scale/visibility transforms for a fixed union
of animated objects. Static geometry is shared by every frame. Tool/rack state,
attachment identity, phase and synthetic time remain explicit. Quaternion
interpolation uses the shortest rotation; discrete visibility is not blended.
Interrupted clips keep their last received pose. Completed recordings are not
re-fetched until delivery state changes or an explicit review requests them.
The Blender
process writes atomic snapshots to its original command exchange's `motion.json`.
Windows sharing-lock conflicts retry only the atomic file rename, bounded to
50 attempts with 10 ms intervals; no physical command is retried.
Its final response includes the recording SHA-256. Reads validate schema,
identity, size, frame continuity, path confinement and the digest when present.
Older exports remain associated with the original hash-checked `.blend`.

Playback GETs are read-only. Import is serialized across hosts by the test catalog
and is unavailable for archived tests. New test paths prefix these routes with
`/simulation-tests/<UUID>`; original test routes remain compatible.
Restart reads the same persisted data. No playback endpoint reconciles a job or
dispatches a command. The runtime's original effect and journal protocol remains
authoritative, including if recording/rendering is interrupted.

Interactive API/desktop hosts use `visual_frame_seconds=1/24`. A settings file
can set this to 0 for unpaced export or up to 0.1 for slower illustration. Batch
demos default to 0; the recorded poses and simulated times are identical.
Neither pacing nor playback speed represents industrial performance.

## Verification

`uv run --locked python -m tools.dev test` includes real Blender streaming,
restart, older scene import, corruption/partial-recording and no-effect tests,
plus Node's built-in tests for playback controls. Install Node 20.17.0 for these
development tests; the application itself requires no Node runtime or CDN.
See tests/blender/test_playback.py, tests/unit/test_visualization.py and
tests/ui/playback.test.cjs, plus tests/blender/test_hkm_runtime.py for articulated
tools and all six product families. The test that imports an older scene verifies that
world, journal, events, workflow history and the `.blend` hash do not change.

[Pose provenance](../adr/0003-recorded-motion-illustration.md) and
[3D scenario design](../adr/0004-full-3d-scenario-replay.md).

The dark guided workspace keeps the full-delivery 3D view as default. Expand
Choose delivery or product replay to inspect another recording. The Next step
card uses persisted workflow/evidence and points to the active unresolved job even
while an older recording is selected. It never uses the visible scene or replay
poses as verification. Attention highlights an explicit investigation action;
the cell is not automatically covered. Opening the bounded inspector pauses only
replay and preserves its frame/selection on return. Play resumes explicitly.
Scene, journal and sensor-observation provenance remain separate (ADR 0012).

The Evidence tab's expandable status details identify the inspected order, job, original command, product,
cell, observed tool and observation confidence/version/calibration. The replay
phase/tool label describes the viewed frame, which may be an earlier product in
the full delivery. **Why this tool?** reads the persisted selection candidates,
scores, conservative assessed mass and constraint reasons from the command.
**Run six-tool showcase (happy path)** explicitly runs all six catalogue products,
verifying each before the next. It prepares a new delivery if the resolved
current one has already consumed products; it cannot bypass an uncertain job.
The Simulation boundaries panel explains synthetic observations and collision
preflight; the optional static checkpoint stays collapsed in Technical details.
