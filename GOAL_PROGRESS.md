# Goal Progress
Last updated: 2026-10-02 UTC
Audited extension source: `899678f0e11044b4104d5c93467de776dce916c6`.

## Current phase
P5/P7 user-requested extension: live Blender motion illustration and per-order
replay implemented and accepted. All 85 MUST criteria pass with clean local and
remote evidence. Native Windows and publication workflows are also green.
The installed desktop launcher uses this checkout; reopening loads the new UI/API.
Existing saved orders can import their original keyed animation without a pick.

## MUST status
ACCEPTANCE_REPORT.md attests all 85 MUSTs for the audited extension source.
Both clean suite runs pass all 239 tests, with 86.57% coverage (unchanged 85%
threshold). Setup, seven real Blender demos, lint,
strict types and security checks pass. Native desktop tests with real Blender
pass, including close during motion and recovery with exactly one pick.
Exact-SHA CI, publication and public Pages are verified in the report manifest.
SHOULD SC-BRAIN-005 (optional model failure/fallback) remains non-blocking.

## Evidence added
- docs/evidence/acceptance/20261002T211230: clean source, two suites, all gates
  and live remote attestation. CI runs 37065407198 (core), 37065407209 (Windows),
  and 37065407211 (publication) all succeeded for the audited SHA.
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

## Release evidence
The committed report identifies its audited source rather than claiming its own
future commit hash (ADR 0002). The evidence successor receives fresh exact-SHA
CI artifacts and public build.json; final delivery verifies all three workflows.
Optional model/hardware work remains non-blocking. Reopen the existing desktop
app to load this checkout; no data reset or reinstallation is needed.
