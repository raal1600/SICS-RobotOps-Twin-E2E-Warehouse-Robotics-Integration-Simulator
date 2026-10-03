# Full 3D cell and scenario replay

The Windows EXE and browser dashboard always show the environment, machine and
products, before orders and for every scenario. The interactive perspective view
uses offline Three.js, with a software 3D fallback when WebGL is unavailable.
The stylized Cartesian gantry is an explanatory synthetic model, not real robot
kinematics. Blender and the initial view share the same cell geometry.

- Drag to orbit, scroll to zoom, right-drag or Shift-drag to pan. The Rotate,
  zoom buttons and Reset camera also work with a keyboard.
- Pause / Play stops or resumes the view. Replay restarts the same scenario;
  it never sends a command. The slider scrubs received motion and saved events.
- Speed selects 0.25x, 0.5x, 1x or 2x playback time. Event steps use a readable
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
Statuses are WAITING, RECORDING, RECORDED, PARTIAL or UNAVAILABLE. An interrupted
recording retains its last frame and is not extrapolated to the destination.
If an abruptly killed job still holds its lease, RECORDING may remain visible;
the frame counter stops, and existing conservative recovery rules apply.

`POST /jobs/{job_id}/playback/import` creates only a derived recording from the
original hash-checked scene. `GET /jobs/{job_id}/artifact.png` retrieves that job's
render. The old `/artifacts/latest.png` endpoint remains compatible.

MotionRecording includes command/job/product/epoch IDs, frame ID, metre units,
24 fps, object geometry and 1..100 contiguous VisualFrame records. The Blender
process writes atomic snapshots to its original command exchange's `motion.json`.
Windows sharing-lock conflicts retry only the atomic file rename, bounded to
50 attempts with 10 ms intervals; no physical command is retried.
Its final response includes the recording SHA-256. Reads validate schema,
identity, size, frame continuity, path confinement and the digest when present.
Older exports remain associated with the original hash-checked `.blend`.

Playback GETs are read-only. Import is serialized within the local API instance.
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
tests/ui/playback.test.cjs. The test that imports an older scene verifies that
world, journal, events, workflow history and the `.blend` hash do not change.

[Pose provenance](../adr/0003-recorded-motion-illustration.md) and
[3D scenario design](../adr/0004-full-3d-scenario-replay.md).
