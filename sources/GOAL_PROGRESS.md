# Goal Progress
Last updated: 2026-10-02 UTC
Base: `13528bebf6eccce588bc8d8d905d2bad87167904` (completed core acceptance).

## Current phase
User-requested Windows desktop launcher extension. Native EXE and WebView2 window
implemented; starts its owned API and actual Blender runtime, stops them on close.

## MUST status
The base has all 85 MUST PASS with exact-SHA CI/publication evidence. Rechecking
all affected criteria for this extension: SC-DEMO-001/003, SC-PERSIST-002/003/004,
SC-IDEM-001, SC-REC-004, SC-TEST-001/003/004/005/006 and SC-KB/DOC/ACC groups.
No normative criterion or threshold changed. Core external-model fallback SHOULD
SC-BRAIN-005 remains a documented non-blocking gap.

## Evidence added this iteration
- Cross-platform desktop backend process tests: close/reopen, original-command
  reconciliation with exactly one pick, separate ports and independent stop files.
- Actual native EXE with Blender: rendered WebView, duplicate launch, graceful
  window close, stopped port, persisted unknown-outcome recovery, crash cleanup,
  closing during a real pick, terminating the owned Blender tree after a crash.
- Full regression: 223 passed, 85.21% Windows coverage (threshold unchanged).
- Lint/format, strict typing, dependency audit/security, drift and generated
  publication all PASS. Evidence: docs/evidence/desktop-launcher.json.
- App installed under LocalAppData/RobotOpsTwin/App with desktop shortcut.

## Decisions
Native .NET Framework/WebView2 host follows the installed Asset Director pattern.
Checksum-pinned SDK; no standalone Python/Blender bundle. OS-selected loopback
port and session-specific filesystem lifecycle avoid changing the API contract.
A private Windows Job Object receives the backend before its suspended process
is resumed. Close drains work for up to 20 seconds, then terminates only owned
children. Persistent journals retain existing conservative recovery semantics.

## Knowledge-base synchronization
Updated README, operations, desktop/dependency docs and architecture diagram for
window ownership, installation, data locations, closing, recovery and tests.
Generated publication will be rebuilt through its existing workflow. The core
architecture, command/observation contracts and research claims are unchanged.

## Next milestone
Commit the verified implementation/tests/docs, run the new Windows desktop CI
lane and full deterministic acceptance, then retain exact-SHA remote/publication
attestations per ADR 0002. The installed app is ready to use.
