# Bounded Blender runtime

The selected tested runtime is Blender 5.2.1 LTS. `BLENDER_EXECUTABLE` can select
its executable; missing Blender fails the real-runtime tests explicitly. It never
substitutes the headless adapter. CPU rendering is enforced, with no model API,
GPU, MCP, plugin or proprietary robot code. The fixed checked-in script is invoked
with `--background --factory-startup --disable-autoexec --python-exit-code 2`.
JSON accepts only reset/query/capture/pick operations; no code/eval/exec endpoint.

Each bounded exchange writes request.json, scene.blend, capture.png, runtime.log
and an atomically renamed response.json. The scene has stable product identities.
Pick exchanges also record evaluated animation poses in atomic motion.json
snapshots for [live illustration and replay](playback.md). This separate display
path never supplies verification evidence.
The actual Blender object follows a baked gripper-relative carrying pose between
attach and detach; its final Blender coordinates become the WorldState checkpoint.
The .blend retains product, carriage, arm, spindle and gripper keyframes for a
stylized Cartesian gantry. The API and Blender use the same cell mesh definitions.
Every sampled carrying pose preserves the gripper offset. These are synthetic kinematics, not validated
robot dynamics, safety evidence, or a Cognibotics/HKM1800 simulation.

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

`world()` reads the durable checkpoint exported from the bounded Blender process;
there is no continuously running external Blender scene or live artist session.
Capture reconstructs that checkpoint in a fresh process. This batch adapter is
documented in ADR 0001. Existing user Blender sessions are never touched.
Interactive execution paces frame export for the live illustration. Older saved
scenes support a fixed `--record-existing` export mode after hash validation;
it never replays the pick or modifies the original scene/checkpoint.

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
