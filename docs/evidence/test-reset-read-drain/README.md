# Test management response-drain correction

CI run [37308097691](https://github.com/raal1600/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/actions/runs/37308097691)
tested exact clean source `317d4a4dac69e2b88846002e3a69d04a2b682011`.
Its first suite passed 688 tests; its second passed 687 and failed the desktop
Blender clear/retry/delete journey. All eight Blender demos, quality gates and
publication passed, but that does not make the failed suite acceptable.

`ci-artifact.json`, `archive.json` and `job-log.txt` preserve artifact identity,
checksum-verified imported bytes and executed gates. The original acceptance
folder is [20261005T121519](../acceptance/20261005T121519/manifest.json).
`failed-report.txt` is the original CI report. `prior-report.txt` preserves the
previous accepted report without changing its source attribution. `browser.json`
and `failure.png` retain the failing browser's requests, source hashes and display.

The trace records a GET of delivery playback beginning at 12:40:35.917 UTC and
taking 540.847 ms. The confirmed Delete POST began at 12:40:36.096 UTC and returned
409 TEST_OPERATION_IN_PROGRESS. A current replay response still held the server's
access barrier. Stopping new polls alone did not drain that response.

The implementation now waits for its outstanding JSON/snapshot bodies before
confirmed management and retains busy controls through final refresh. A stalled
view wait sends no management request; retry remains explicit. Backend protection,
robot deadlines and physical-effect semantics are unchanged. `ui-first.log` retains
an intermediate control-release failure caught by existing assertions; `ui-passed.log`
records 146 passing UI checks after fixing it, including seven new concurrency cases.

Targeted browser/API and new exact-source full acceptance are recorded separately
as they complete. A later passing source never relabels this failed source PASS.
