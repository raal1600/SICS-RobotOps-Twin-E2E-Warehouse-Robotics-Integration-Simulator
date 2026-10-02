# ADR 0003: Recorded Blender motion as a read-only illustration

Accepted 2026-10-02. Classification: SIMULATOR_DESIGN.

The user requested a live illustration and replay instead of only a static final
render. Keep the bounded batch Blender runtime. Export its evaluated object poses
at each of the existing 100 animation frames, at 24 simulated frames per second.
Do not animate an independently invented successful pick in the browser.

Blender atomically replaces a bounded `motion.json` as frames arrive. The local
dashboard polls the selected job's presentation endpoint and draws the exported
boxes and positions in a dependency-free Canvas illustration. Playback interpolates
between received poses, never beyond the last received frame. Pause, replay,
scrubbing, speed and camera rotation affect only the view. The job status remains
visible independently, including UNKNOWN_OUTCOME and REQUIRES_INTERVENTION.

This presentation path may expose simulator truth to a human for explanation. It
is explicitly not sensor evidence and is never consumed by Brain or Verifier.
Partial recordings do not prove a committed effect. Full recordings do not prove
a verified business outcome. Original journal plus fresh WorldObservation still
govern reconciliation. No normative acceptance rule or state machine changes.

The interactive hosts pace export at 1/24 second per frame; batch demos/tests
default to unpaced export with the same scene frames. Simulated playback time is
not robot cycle-time evidence. CPU final renders remain available per job.

Older orders can export the keyed animation from their original saved `.blend`.
An explicit import action verifies the saved scene hash, disables auto-executed
scripts and calls a fixed export-only mode. It never invokes `apply`, checkpoints
the world, changes workflow state or overwrites the original scene/response/log.
Only derived motion data and a separate replay log are written. Missing/corrupt
recordings show an unavailable state rather than manufactured motion.

This is a lightweight geometric illustration of the Blender scene, not streamed
photorealistic frames, validated dynamics or a continuously running artist session.
