# Local Blender deadline investigation

These are development diagnostics against baseline `def3d51`, not a completed
acceptance run. `archive.json` records original paths and SHA-256 digests. Raw
failures remain failures. Temporary cProfile/statement timers added diagnostic
overhead; they are outside the mandatory runtime and are not completion evidence.

The isolated browser suite passed seven cases and failed two Blender journeys
at the unchanged 60-second process deadline. A CPU-instrumented repetition also
retained two failures and an independent Windows HTTP teardown error. Available
host memory and process affinity were checked; neither established the cause.
No unrelated process data is published and no owner application was stopped.

The profile identifies frame baking and dependency-graph evaluation as substantial
costs. Avoiding repeated assignments of unchanged visibility flags preserves the
same animation. One instrumented clear/pick/delete/recreate journey then passed
in 35.96 seconds, but the subsequent full suite still exposed Blender deadlines.
That isolated pass is not presented as proof that the slowdown was resolved.

The new visibility regression initially named a conceptual `Robot/ActiveTool`
object that is not an actual mesh. Its preserved failure is a test-fixture error;
the corrected test selects the mounted `Tools/<tool_id>` from saved tool state
and retains all hide/show and save/reopen assertions. Existing actual Blender
lost-ack, ambiguous reconciliation, original-command restart and read-only export
checks passed in the targeted run.

A two-worker experiment also timed out and was not adopted. Blender's documented
Windows `--qos high` option passed all nine diagnostic browser journeys in
293.64 seconds. The production adapter then passed twelve checks together in
384.15 seconds: those nine journeys, saved visibility, original-command lost-ack /
ambiguous observation / restart / read-only export, and the six-tool showcase.
Another 170 unit and contract checks pass. This is scoped local evidence; a fresh
complete acceptance run is still required for the source carrying this correction.

The initial new adapter test also caught that `platform.system()` may run an OS
version subprocess. The implementation uses `sys.platform` instead; all ten
adapter tests then pass, including the unchanged timeout cases. The fixed argv
is reviewed in `docs/security-exceptions.json`. Render settings, all recorded
frames, motion semantics and the 60-second deadline remain unchanged. No Windows
policy is changed and no physical-performance validation is claimed.
