# Goal Progress
Last updated: 2026-10-03 UTC
Implementation base: `bcc8a4ee856879a1287fc781910264e9b30055bb`.

## Current phase
P5/P7 user-requested extension: full 3D scene and all-scenario replay implemented.
The environment, machine and products stay visible before orders and when a
scenario has no effect. Recorded machine/product poses and saved events replay
without commands. Final clean acceptance and exact-SHA remote checks remain.

## MUST status
Baseline: all 85 MUSTs passed before this extension. Current development suite:
254 tests PASS, 87.35% coverage, no skips or xfails. Scenario matrix, persistence,
legacy import, uncertainty and all-frame carrying-offset checks pass. Lint,
strict types and Python/npm security checks pass. All eight real-Blender native
checks pass after aligning drain deadlines with the existing runtime budget.
No MUST, coverage threshold or state transition was weakened. The extension is
not yet declared accepted.

## Evidence
- artifacts/3d-regression-awake-tests.xml and coverage JSON: complete suite.
- tests/blender/test_playback.py: every execution scenario, evaluated poses,
  exactly one effect, no-effect stationary scenes, read-only replay/import.
- tests/unit/test_visualization.py and tests/ui/playback.test.cjs: scene history,
  offline asset integrity, event replay, partial clips and bounded file retry.
- docs/evidence/3d-scenarios.json and 3d-{webgl,software,mobile}.png: real browser
  checks and persisted one-effect/intervention evidence.
- docs/evidence/3d-desktop.json: actual native window/process lifecycle, normal
  close during a real pick and forced close ownership, with source hashes.
- A broader test exposed a Windows reader/rename race; bounded presentation-only
  retry fixes it. Another run experienced an eleven-hour host interruption and
  failed existing timeout/lease checks. Its results were rejected and rerun;
  timeouts and assertions were retained unchanged.

## Decisions / ADRs
ADR 0004 extends ADR 0003: immutable PresentationSnapshot before execution,
shared cell geometry, offline Three.js and software perspective rendering,
read-only event/pose timeline, explicit legacy reference provenance. Cartesian
machine illustration is synthetic, not validated kinematics. No renderer data
enters Brain, ObservationModel or Verifier. Cell reset never erases history.

## Knowledge-base synchronization
Drift: prior motion-only/Canvas-only descriptions, absent no-motion history,
stale persistence future tense and damaged Swedish report characters.
Synchronized README, PROJECT_PLAN, PUBLICATION, report 01, registry S22,
architecture source, OpenAPI and schemas, playback/Blender/desktop/operations/
persistence/dependency/contract guides, ADRs 0003/0004 and acceptance mapping.
Publication regenerated with 181 validated PDF internal destinations. Existing
company claims and provenance classifications remain unchanged.

## Next milestone
Complete native launcher and clean acceptance; commit coherent implementation,
verify CI and publication at that SHA, retain acceptance evidence, then verify
the final evidence successor. Installed launcher uses this checkout: reopening
loads the update without reinstalling or clearing the user's data.
