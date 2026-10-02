# Live cell illustration and replay

The Windows EXE and browser dashboard share **Live cell & replay**. New Blender
orders show motion as evaluated frames arrive. The selected order owns the clip;
choosing an older order never substitutes the most recent order's image or motion.

- **Pause / Play** stops or resumes the view.
- **Replay** starts the same recording from frame 1. It sends no robot command.
- **Recorded frame** scrubs to a received frame; keyboard arrows also work.
- **Speed** selects 0.25x, 0.5x, 1x or 2x simulated playback time.
- **Rotate view** changes the illustration's viewing angle.
- **Load saved animation** appears for older runs with a saved Blender scene but
  no recording. It reads that original animation without executing another pick.

Try lost acknowledgement after effect: the product visibly moves but the job
becomes UNKNOWN_OUTCOME. Replay it repeatedly, then reconcile. Contradictory
evidence still requires intervention even though the illustration shows a move.
Missing/pre-dispatch/rejected commands have no invented movement. A headless run
explicitly reports that it has no Blender recording.

The geometric view uses recorded Blender box dimensions/colors and evaluated
world positions. Its simplified shading differs from the CPU-rendered checkpoint.
The phase and current frame are also exposed as text. Illustration data is
simulator truth for the human viewer, not input to verification or sensor output.

## Protocol and persistence

`GET /jobs/{job_id}/playback` returns the versioned JobPlayback contract with the
original command ID, current job state, recording status and optional motion.
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

[Design decision](../adr/0003-recorded-motion-illustration.md).
