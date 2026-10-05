# Test deletion / same-test clearing development evidence

Baseline: `4da22d75bded35452f4bca1db03c57da5e9eb957`. The byte-preserved prior
acceptance report is `baseline-acceptance.txt`; it retains its original audited
revision and does not certify this change. `provenance.json` records file hashes
and the development source hashes. Clean-source acceptance follows separately.

The user explicitly changed deletion/numbering semantics; ADR 0013 documents the
corresponding replacement of the old monotonic-number and permanent-tombstone
expectations. Robot assertions, runtime deadlines and coverage thresholds remain.

- Original lifecycle baseline: 32 passing tests (`test-reset-baseline.xml`).
- Final targeted integration: 49 passing tests (`test-reset-integration-3.xml`).
- Final JavaScript suites: 139 passing checks (`test-reset-node.tap`).
- Final desktop/compact Chromium lifecycle matrix: four passing cases with real
  HTTP and both runtimes (`test-reset-browser-6.xml`, `browser/`).
- Documentation drift and publication build: passing logs retained alongside.

Earlier failures are retained, not erased by later passes. Browser runs 2 and 3
timed out in Blender (60 seconds) while rendering; the controller conservatively
remained uncertain. Their runtime logs are `timeout-1.log` and `timeout-2.log`.
The same disposable request alone profiled at about 12 seconds including startup
(`reset-render-profile-1.log`). Process sampling during the browser matrix showed
CPU WebGL rendering consuming about ten CPU cores alongside Blender. Replay now
bounds automatic drawing at 24 fps while preserving elapsed-time cursor speed;
the new JavaScript regression checks both 60 and 144 Hz presentation clocks.
Blender quality, recording frames and timeout interpretation were not changed.

Browser run 5 completed the picks but caught four stale HTTP 404 requests after
deletion. Periodic world reads now pause through data management, and pending view
versions are invalidated. A delayed-response regression verifies polling resumes
after the returned selection is applied. Run 6 passes without console/page errors.

The screenshots were visually inspected: confirmation names the retained test and
discarded data; the cleared compact view shows Test 1, restored products and kept
scenario choice; the replacement test is empty and numbered 1. These are UI checks,
not usability-study results or physical/vision verification evidence. All fixtures
are disposable; the owner's application data was not modified.

## Windows checkout correction

The first implementation commit `2eddd8a` failed Windows checkout before building:
the expanded repository prefix plus descriptive browser-case directory exceeded
Windows' path limit. `windows-checkout.log` and `windows-jobs.json` preserve the
failure. The four directories now use short viewport/runtime names. Their bytes
are unchanged; `path-relocations.json` maps the paths in the original provenance
manifest to their new locations, and every recorded hash was verified after moving.

The local acceptance run `20261005T113217` started at clean `2eddd8a` before this
documentation-only relocation. Its recorded source identity is the start snapshot;
the archive relocation occurred during that run. Do not treat it as a clean-source
acceptance attestation for the corrected commit. Exact-source CI reruns all gates
on the corrected tree, including Windows checkout and the desktop lifecycle.
