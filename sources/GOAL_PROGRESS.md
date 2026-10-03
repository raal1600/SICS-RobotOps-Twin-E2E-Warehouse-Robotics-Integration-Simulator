# Goal Progress
Last updated: 2026-10-03 UTC
Audited implementation: `488db3efc124901ad57b20f7aaa4e472c7314b9f`.

## Current phase
P5/P7 extension complete: full 3D cell, moving machine/product poses and scenario
replay for every execution outcome. All 85 MUSTs pass for the audited clean
source with local and exact-SHA remote evidence. Final evidence/status successors
receive fresh CI artifacts and public build.json attestation (ADR 0002).

## MUST status
Both clean suites: 254 PASS, zero skips/xfails, 87.35% coverage (85% minimum).
Setup, lint/format, strict typing, Python/npm security, seven real Blender demos,
drift scan and publication pass. Exact-source workflows: core 37120767979,
Windows 37120767929 and publication 37120767978 all SUCCESS. Public Pages exposes
the matching source SHA, 22 references and seven synchronized diagrams.
SHOULD SC-BRAIN-005 remains non-blocking; optional model/hardware work is unchanged.

## Evidence
- docs/evidence/acceptance/20261003T114649: clean manifest, two complete suites,
  all gate logs/demos and verified remote status; ACCEPTANCE_REPORT.md maps all
  85 MUSTs to inspectable evidence and names the tested source.
- docs/evidence/3d-scenarios.json and 3d-{webgl,software,mobile}.png: actual browser
  rendering, fixed/no-effect scenes, replay/scrub, mobile layout and exactly-one
  pick despite ambiguous reconciliation.
- docs/evidence/3d-desktop.json: all eight native/real-Blender lifecycle checks,
  including normal close during a pick and termination of owned children on crash.
- Tests cover the complete fault matrix, saved scenes after later orders/restart,
  every carrying-frame offset, partial/corrupt recordings, read-only legacy import,
  no replay dispatch, offline asset integrity and Windows sharing-lock retries.
- One development run exposed a transient Windows reader/rename race (fixed).
  Another encountered an eleven-hour host pause and failed existing deadlines;
  that result was rejected and rerun without weakening runtime timeouts/assertions.

## Decisions / ADRs
ADR 0004 extends ADR 0003: presentation snapshots and audit-event playback,
shared stylized gantry geometry, offline Three.js with software perspective
fallback, and explicit legacy-reference provenance. No presentation data enters
Brain, ObservationModel or Verifier. No state-machine or MUST changes.
Native drain budgets now match the existing 60-second runtime deadline: 65 s
server, 70 s owner, 75 s test observation. Measured valid paced picks exceeded the
old 15-second drain; completion/effect assertions are retained. Idle shutdown is
prompt. Rendering redraws only changed poses/camera/size.
The updated versioned EXE is installed and the desktop shortcut points to it.
An open older app and all user data remain untouched; close/reopen the shortcut.

## Knowledge-base synchronization
Drift found and corrected: motion-only/Canvas-only descriptions, missing static
scenario history, persistence future tense, damaged Swedish characters and the
old native drain/install descriptions. Synchronized README, PROJECT_PLAN,
PUBLICATION, report 01 and the shared status in reports 01-03, registry S22,
architecture, schemas/OpenAPI, all affected
implementation guides, scene README, ADRs 0003/0004, acceptance map/generator and
this record. Publication is generated only from source; 181 PDF destinations
validate. Existing external company claims retain their original provenance.

## Release evidence
The committed report attests its audited source, not its own future commit hash.
The final evidence successor must have all three workflows green and matching
Pages build.json before delivery. Optional model/hardware integration remains
explicitly non-blocking. No unresolved implementation or knowledge-base drift
remains; final exact-SHA CI artifacts are the release attestation.
