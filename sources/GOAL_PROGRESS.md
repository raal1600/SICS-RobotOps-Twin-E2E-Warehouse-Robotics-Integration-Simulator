# Goal Progress
Last updated: 2026-10-02 UTC
Extension base: `62628444448a0440af7e47f586efef6ce8c75f4f`.

## Current phase
P5/P7 user-requested extension: live Blender motion illustration and per-order
replay implemented. Final clean acceptance and exact-SHA remote checks are next.
The installed desktop launcher uses this checkout; reopening loads the new UI/API.
Existing saved orders can import their original keyed animation without a pick.

## MUST status
All 85 core MUSTs have audited base evidence in ACCEPTANCE_REPORT.md. Extension
verification: 239 tests pass, 86.57% coverage (unchanged 85% threshold), lint,
strict types and security checks pass. Native desktop tests with real Blender
pass, including close during motion and recovery with exactly one pick.
The final extension revision is not yet attested by remote CI/publication.
SHOULD SC-BRAIN-005 (optional model failure/fallback) remains non-blocking.

## Evidence added
- docs/evidence/replay-extension.json and replay-desktop.png: browser playback,
  uncertainty/intervention and exactly one effect; native process lifecycle.
- tests/blender/test_playback.py: live frame progression, actual evaluated poses,
  restart, read-only legacy import, no fabricated success, corrupt/partial data,
  path confinement and commands with no recorded effect.
- tests/unit/test_visualization.py and tests/ui/playback.test.cjs: strict schemas,
  no Node/CDN dependency at runtime, pause/scrub/replay and stale-selection guards.
- Regenerated PDF architecture visually checked; 180 combined PDF destinations
  and source links validated by the publication build.

## Decisions / ADRs
ADR 0003 separates presentation from observation/verification. Fixed Blender
script exports evaluated frames; browser only illustrates received poses.
Atomic recordings retain command/job/epoch identities and an export digest.
Older scenes use hash-checked export-only mode, leaving original evidence intact.
Interactive hosts pace at 24 simulated fps; batch acceptance need not wait.
No state machine, effect-idempotency or reconciliation criterion changed.

## Knowledge-base synchronization
Drift detected: static-only dashboard descriptions; missing replay API/contracts;
older contract guide still described completed phases in future tense.
Synchronized README, PROJECT_PLAN, Blender/contracts/operations/desktop/dependency
and playback guides, ADR 0003, design report, architecture diagram, OpenAPI and
four presentation schemas, acceptance map/generator, reviewed subprocess scope
and this progress record. Generated publication is rebuilt, never hand-edited.
No external source claim or provenance class changed.

## Next milestone
Commit coherent extension, run clean acceptance twice plus demos, refresh exact-SHA
CI/publication evidence and current acceptance report, verify deployed sources.
