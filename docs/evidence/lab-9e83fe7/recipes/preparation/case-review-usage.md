# Prepared saved-case reviews

PREPARATION ONLY. Syntax checked without importing or executing the programs. No current case, suite, or acceptance PASS is asserted.

Pinned commit: 9e83fe7d41a52a63ba65b77730e392dafca8fffe. Fingerprint: 136641a25c5fbd7d45c016582ec2c5c5197362f44f0a894ee95a69c652e3eafd. Campaign: docs/evidence/acceptance/20261006T024719, manifest start 2026-10-06T02:47:20.134216+00:00.

Both wrappers use case_review.py. Root may invoke them later, after the selected suite exits successfully and the watcher promotes all four snapshots. Replace the placeholder with the exact basename independently observed in that pass's pytest command; it must also match the terminal gate command and watcher. No guessed suffix or historical fixture is accepted.

~~~powershell
& .venv\Scripts\python.exe artifacts/final-evidence-pack/9e83fe7/prepare-pass1-case-review.py --review-terminal-pass1 --expected-fixture '<OBSERVED_PASS1_BASENAME>'
if ($LASTEXITCODE -ne 0) { throw 'Pass-1 review refused; do not infer PASS' }

& .venv\Scripts\python.exe artifacts/final-evidence-pack/9e83fe7/prepare-pass2-case-review.py --review-terminal-pass2 --expected-fixture '<OBSERVED_PASS2_BASENAME>'
if ($LASTEXITCODE -ne 0) { throw 'Pass-2 review refused; do not infer PASS' }
~~~

Expected basename shapes are robotops-acceptance-1-SUFFIX and robotops-acceptance-2-SUFFIX. Include only the basename, not /fixtures or an absolute path. These examples are not instructions to run during preparation.

Readiness guards run before any copy:

- Exact current commit/recomputed source fingerprint, clean-start manifest identity and start time; exact watcher campaign/source/pass fixture.
- Selected tests_N gate terminal exit 0 and passed true; full unfiltered command has the expected fixture/JUnit/coverage flags.
- Nonempty terminal JUnit, all actual/declarations consistent, no failure/error/skips, no duplicate or unowned testcase identities; all four exact lab cases present. Pass 1 requires its own JUnit. Pass 2 requires both clean JUnits and identical full testcase sets. There is no hardcoded total testcase count.
- Selected coverage bound from its first read, recomputed and at least 85%; four watcher cases formally PASSED, complete, exact source/pass, and inside the expected fixture; only four expected raw JSON input paths accepted per case.
- No pre-existing snapshot directory or review output; changed input bytes cause refusal.

After readiness succeeds, the program writes byte-verified immutable copies of four cases, watcher status, and manifest to passN-finalized-snapshots/, plus copy-receipt.json. A later semantic failure retains these copies for inspection and writes no PASS review. Do not automatically delete/reuse them. The original watcher/status/cases/manifest remain unchanged.

The inherited 164 raw checks verify original command/job/payload identities; matching durable runtime/PLC receipts and one effect; READY preflight and authorization ordering; happy Blender frames/poses/rendered movement; lost-ACK original-command reconciliation with no resend; duplicate publication/deliveries 1 to 2 with actual redelivered flags; WMS503 then200 business-only retry; browser errors; and all35 source hashes. Scoped credential patterns report field paths without matched values. Any issue prevents success output.

Each parse is bound to its exact bytes, SHA256 and byte length. A differing reread is rejected. Mutable bytes are hashed before parsing, compared again before exclusive copies, and copied paths are bound to those original bytes before rereading. Inputs and source identity are checked again before exclusive output creation.

Successful outputs are pass1-case-review-final.json or pass2-case-review-final.json. Key fields: source.commit/source_sha256, acceptance_pass, fixture_basename, formal_test_status=PASSED_FOUR_LAB_CASES, check_count=164, source_files_verified=35, all_source_hashes_match=true, issues=[], secret_review.potential_findings=[], cases, input_binding, inputs. input_binding.same_full_testcase_sets_across_passes is null for pass1 (not evaluated), true only for pass2 after comparison. These are schema expectations, not present results.

Limits: no tests/services/browser/DB connections/network/rendering/ZIP/DOM/pixel scans. File reads, source hashes and read-only git commands only. Pre-gate effect0, authorization replay, original saved execution_scenario and dropdown independence have separate exact-test/JUnit attestation when standalone raw responses/DOM were not saved. A browser request listener excludes page.request API calls; one recorded stage16 POST does not mean one total HTTP request. Only happy has Blender motion; fault cases use synthetic runtime with real protocols. No manual, whole-campaign, global-secret, PDF visual or remote PASS is claimed.

The terminal helper has separate usage in terminal-review-usage.md. It additionally refuses until the exact response-sync wrapper exit record exists with exit0, both suites are clean/equal, all20 local gates pass, eight source-bound Blender demo scenarios pass, and independent criteria match169 MUST with163 local passes and6 remote pending. Local acceptance success never means goal complete.
