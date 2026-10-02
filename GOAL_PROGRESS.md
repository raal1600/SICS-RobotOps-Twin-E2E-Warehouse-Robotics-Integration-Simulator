# Goal Progress
Last updated: 2026-10-02 UTC
Audited source: `2380bd72b2dbba01467cf90bee82a7f4ea18fede`.

## Current phase
User-requested Windows desktop extension implemented, tested and installed.
The native EXE starts its own API and embedded dashboard, uses real Blender by
default, and stops its owned process tree when its window closes. Persistent
orders, journals and uncertainty retain the existing conservative recovery rules.

## MUST status
All 85 core MUST criteria pass against the audited source, with clean CI evidence
in ACCEPTANCE_REPORT.md. Both mandatory suite runs contain 223 passing tests.
The native Windows workflow exposed a long-path startup issue; the correction is
covered by a real local window test with a data path over 260 characters. Its
successor commit reruns all three workflows before final delivery.
SHOULD SC-BRAIN-005 (optional external model fallback) remains non-blocking.

## Evidence
- docs/evidence/acceptance/20261002T195545: clean Ubuntu acceptance, repeated tests,
  quality/security checks, seven actual Blender demos and publication.
- docs/evidence/desktop-launcher.json: native WebView rendering, duplicate launch,
  normal window close, stopped port, unknown-outcome recovery with one pick,
  abrupt desktop termination and closing during a real Blender operation.
- Long-path regression: native long-path support plus a short per-data-root browser
  profile correct the Windows runner startup failure; same lifecycle assertions.
- Installed copy verified in LocalAppData/RobotOpsTwin/App; desktop shortcut exists.

## Decisions
Native .NET Framework/WebView2 host follows the Asset Director desktop pattern.
Checksum-pinned SDK; existing local Python/Blender installation. OS-selected
loopback port and session-specific files do not change the public API contract.
A private Windows Job Object owns the backend before its suspended process resumes.
Close drains work for up to 20 seconds, then terminates only owned descendants.
No blind replay or fabricated success is introduced by shutdown/reopening.

## Knowledge-base synchronization
README, desktop/operations/dependency docs, acceptance mapping/report, architecture
diagram and this progress record reflect the extension and its evidence. Generated
HTML/SVG/PDF were rebuilt and the affected architecture figure visually checked.
No normative criterion, coverage threshold, runtime schema, or provenance class
changed. The observed CI failure and its corrective evidence are retained.

## Release evidence
The report retains its exact audited source identity. Per ADR 0002, later native
path/evidence changes receive fresh exact-SHA CI artifacts and a public build.json;
final verification checks all three workflows and deployed source identity. The
installer records source hashes and clean/dirty state in windows-build.json.
