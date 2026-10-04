# Bounded Blender runtime

The selected tested runtime is Blender 5.2.1 LTS. `BLENDER_EXECUTABLE` can select
its executable; missing Blender fails the real-runtime tests explicitly. It never
substitutes the headless adapter. CPU rendering is enforced, with no model API,
GPU, MCP, plugin or proprietary robot code. The fixed checked-in script is invoked
with `--background --factory-startup --disable-autoexec --python-exit-code 2`.
The schema-1 compatibility path accepts reset/query/capture/pick; schema 2 accepts
reset/capture/pick. World and journal queries use the durable local checkpoint.
Neither version offers a code/eval/exec endpoint.

Each bounded exchange writes request.json, scene.blend, capture.png, runtime.log
and an atomically renamed response.json. The scene has stable product identities.
Pick exchanges also record evaluated animation poses in atomic motion.json
snapshots for [live illustration and replay](playback.md). This separate display
path never supplies verification evidence.
The actual Blender object follows a baked gripper-relative carrying pose between
attach and detach; its final Blender coordinates become the WorldState checkpoint.
Schema-2 `.blend` files retain articulated link rotations, TCP-driven wrist/tool
poses, tool exchange, product attachment/release and every sampled transform.
The original procedural HKM1800-inspired hybrid-kinematic manipulator has six
source boxes, six varied product families, six interchangeable tools and three
camera viewpoints. The API and Blender consume the same semantic primitives;
the canonical catalogue supplies dimensions, tool constraints and fixture poses.
These are synthetic visual kinematics, not validated robot dynamics, certified
safety or an exact Cognibotics/HKM1800 simulation. Historical schema-1 scenes keep
their original Cartesian gantry and positional recording interpretation.

`HKM_INSPIRED_VISUAL_KINEMATICS_V1` maps TCP pose to an original parallel-link
configuration. Smooth segmented presentation motion is baked into actual Blender
objects. The runtime exports evaluated matrices, not a second invented browser
trajectory. Fixed semantic parents and parent-space residual correction keep
tool-dock and carrying transforms within the tested 1e-6 m numeric tolerance;
this tolerance describes numerical agreement, not real-world accuracy.
Tool changes preserve command identity and never increment the product-transfer
effect count. During a normal pick one tool is mounted and five remain in the
rack; the empty-flange phase briefly places all six in their docks.

The original synthetic tote layout has open access lips: 0.03 m at the front,
0.05 m at the right, full configured height at the left/back. Products remain
visible and accessible. Collision preflight uses these same procedural bounds.
This is our fixture design, not an industrial customer layout or safety barrier.

Before launching Blender, the adapter commits RUNNING and reserves the cell.
Duplicate deliveries never re-launch it. A complete response and matching .blend
hash allow the controller journal and world checkpoint to commit together. If the
adapter dies after Blender finishes, querying the original journal can finalize
that same checkpoint; no motion is rerun. Missing/corrupt checkpoints remain
STATUS_UNKNOWN and quarantine the runtime even after a logical cell reset.
Evidence views instead use recorded_journal, a pure saved-receipt read. They never
finish a pending checkpoint, including when viewing an archived test (ADR 0007).
Fresh observation is still required for business completion. Neither a receipt
nor a screenshot alone is accepted by Verifier.

Schema-2 subprocess validation independently rechecks the durable payload hash,
scene/cell identity, finite workspace poses, product source, available compatible
tool, trajectory structure and conservative geometry preflight before animation.
The host then checks the entire returned checkpoint and artifact hashes before
committing the effect. Unknown or corrupt outcomes stay uncertain.

`world()` reads the durable checkpoint exported from the bounded Blender process;
there is no continuously running external Blender scene or live artist session.
Capture reconstructs that checkpoint in a fresh process. This batch adapter is
documented in ADR 0001. Existing user Blender sessions are never touched.
Interactive execution paces frame export for the live illustration. Older saved
scenes support a fixed `--record-existing` export mode after hash validation;
it never replays the pick or modifies the original scene/checkpoint.

`tests/blender/test_hkm_runtime.py` invokes actual Blender for the six-tool
showcase, transform/attachment/rack assertions, lost-ack/restart/ambiguity,
hash-corrupt checkpoints and malformed requests that must produce no effect.
A fixed test-only probe inspects the actual saved hierarchy, labels and camera
sensor/frame/calibration/model properties. Presentation cameras and rendered
pixels never become verifier input. Scoped development evidence is recorded in
GOAL_PROGRESS.md. The accepted HKM source `ca779879` is preserved in
[the lifecycle baseline archive](../evidence/test-lifecycle-baseline/README.md);
ACCEPTANCE_REPORT.md records the current revision separately. Explicit test-data
deletion may remove a selected test's Blender artifacts after confirmation; it
never invokes the runtime to execute, recover or resolve that deleted world.

Run:

```
uv run --locked python -m tools.dev demo --runtime blender
uv run --locked python -m tools.dev demo --runtime blender --scenario lost_ack_after_effect
uv run --locked python -m tools.dev test tests/blender
```

The complete `make test`/portable test command includes tests/blender. A separate
fast development run can name tests/unit tests/contract tests/integration tests/e2e;
that subset is not full acceptance. No mandatory test uses skip or xfail.

CI pins the Linux archive to SHA-256
`a31f524fa99a527d3d52b7f5aaa68c34e1a19d5a1c9473f79c5cc610fd5b10e9`, read from the
[official release checksums](https://download.blender.org/release/Blender5.2/blender-5.2.1.sha256).
The version choice and protocol are SIMULATOR_DESIGN. The upstream checksum is
release provenance, not evidence of physical performance.
