# ADR 0004: Persisted scenes and full 3D scenario replay

Accepted 2026-10-03. Classification: SIMULATOR_DESIGN. Extends ADR 0003;
supersedes its dependency-free isometric renderer choice only.

The user needs to see the environment, machine and products even when an order
cannot move anything. A motion file alone cannot represent planning failures or
controller rejections. Before a newly claimed job advances from RECEIVED, save
an immutable PresentationSnapshot in the workflow record store. It contains the
starting WorldState solely for human presentation, never planning/verification.
Later orders and restart do not replace it. Jobs without a historic snapshot use
an explicitly labelled current reference; existing Blender clips retain their
original geometry and poses.

GET /cell/scene supplies the idle view. JobPlayback supplies the scene, product,
original audit events and optional recording. The viewer replays significant
events at half-second presentation intervals and inserts evaluated Blender motion
after the dispatch-intent event. The original timestamps remain in the causal
timeline. Incomplete motion stops at the last received pose. A missing recording
never implies no effect; controller rejections and business outcomes are distinct.

Blender and the starting view share a standard-library mesh builder. The machine
is a stylized Cartesian gantry with baked moving carriage, arm, spindle and gripper
parts. The product preserves its carrying offset at every exported frame. This
is an explanatory synthetic model, not industrial kinematics or a real robot.

Three.js 0.180.0 and OrbitControls are served offline with their upstream MIT
license, pinned archive integrity, file digests and npm audit lock. Perspective
meshes, lighting and camera orbit/pan/zoom make the cell inspectable. A software
perspective renderer consumes the same data when WebGL is unavailable or lost.
No GPU, cloud, model or Node process is required by the running application.

Windows readers can briefly hold a sharing lock during atomic motion-file
replacement. Retry only that rename, at most 50 attempts with 10 ms intervals.
Keep the last intact recording on persistent failure. Never retry physical
execution. Original journaling, quarantine and reconciliation semantics remain.

Native testing exposed a shutdown-budget mismatch: a valid paced pick plus its
CPU checkpoint took about 18 seconds, exceeding the old 15-second server drain.
Align shutdown with the existing 60-second runtime deadline: 65 seconds for the
server (planning/persistence margin), 70 for the native owner and 75 for the test
to observe process exit. Runtime deadlines, completion assertions and exactly-one
effect requirements are unchanged. This allows accepted operations to finish;
forced/crash cleanup remains bounded. The renderer redraws only changed poses,
camera or size, conserving CPU when idle. Versioned native installs avoid
overwriting files loaded by an open older app and preserve all saved data.

Validation: the real Blender scenario matrix, all-frame carrying-offset checks,
immutable history after later orders/restart, corruption/legacy import tests,
bounded-sharing-lock tests, browser event/partial-frame controls, offline asset
hashes and camera fallback checks. No normative MUST or threshold was weakened.
