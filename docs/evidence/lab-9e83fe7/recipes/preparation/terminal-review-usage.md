# Terminal local acceptance review preparation

Status: **PREPARED, SYNTAX CHECKED ONLY; NOT EXECUTED; NO CURRENT PASS ASSERTION.**

Pinned source: 9e83fe7d41a52a63ba65b77730e392dafca8fffe.
Pinned source fingerprint: 136641a25c5fbd7d45c016582ec2c5c5197362f44f0a894ee95a69c652e3eafd.
Pinned campaign: docs/evidence/acceptance/20261006T024719.
Pinned terminal: artifacts/acceptance-response-sync-exit.json.

After the exact wrapper has terminated, root may run from the repository root:

~~~powershell
& .venv\Scripts\python.exe artifacts/final-evidence-pack/9e83fe7/prepare-terminal-review.py --review-terminal
if ($LASTEXITCODE -ne 0) { throw 'Terminal review refused; no new PASS may be inferred' }
~~~

This is an offline evidence reader. It imports only the Python standard library, reads the exact saved campaign, and invokes only read-only git commands to recompute source identity. It starts no tests, services, browser, DB connections, renders, scans or network requests. It never edits the acceptance manifest. Current execution is **not authorized by this preparation receipt**.

The sole possible review output is artifacts/final-evidence-pack/9e83fe7/local-acceptance-review.json. It is created exclusively after all checks succeed. An existing output causes refusal and is preserved; a refusal never refreshes or validates an old output. Check the command exit code and inspect the newly created, parseable JSON and its hash. Do not reuse an old result after a refusal.

Required checks:

- Exact terminal source and exit 0; terminal interval contains the exact manifest start; manifest records the exact clean-start source; current commit and recomputed source fingerprint match.
- Exactly 20 local gates passed, executable gates exit 0, each saved log belongs to this campaign. All three remote gates remain explicitly not run.
- Both full-suite commands bind separate pass fixture basenames and exact JUnit/coverage paths with no extra test-selection options.
- Independently parse every actual testcase: positive count, consistent declared counts, no errors/failures/skips anywhere, no duplicate identities, identical full testcase sets and outcomes across passes. No expected total test count is hardcoded.
- Require eight selected exact browser cases per pass: four real network lab cases, two Blender investigation views, and two Blender guided cases. Lab happy uses Blender; lab fault cases use synthetic runtime. JUnit success does not substitute for saved-DOM/secret/manual review.
- Both coverages recompute from line totals and must be at least 85%; saved repeatability must exactly equal the independent JUnit maps.
- Recompute every criterion from current source specification, mapping, actual JUnits and gates; compare every result with manifest criteria. Require 169 MUST with 163 local passes and exactly six remote-dependent pending criteria, plus all 51 LAB-MUST local passes. Four SHOULD outcomes remain separate and nonblocking.
- Inspect all eight Blender-selected CLI scenarios in this exact run. Require each campaign result to be byte-identical to its run result, original identities, durable receipts/payload hashes, matching created/effect event counts, no duplicate effects, original-command reconciliation, expected scenario-specific outcomes and fresh timestamps. Positive effects require Blender intent, bounded process dispatch and Blender receipts; three zero-effect fault paths must retain their expected rejection/failure semantics. The tool showcase requires six distinct tools/SKUs/original commands.
- Inspect saved security review and matching lock hash, drift and source-bound publication metadata. Reviewed Bandit findings are not misrepresented as a zero-exit scan.
- Hash every consumed artifact and recheck all bytes plus source identity before writing.

Successful output contains direct schema fields:

~~~json
{
  "local_acceptance_passed": true,
  "source": {
    "commit": "9e83fe7d41a52a63ba65b77730e392dafca8fffe",
    "source_sha256": "136641a25c5fbd7d45c016582ec2c5c5197362f44f0a894ee95a69c652e3eafd"
  },
  "goal_status": "NOT_ACHIEVED"
}
~~~

This document is a schema example, **not an acceptance result**. That output shape is intended for the separately prepared exact-source audit guard; its own readiness requirements still apply. The guard still requires fresh saved cases, completed manual/CLI proofs, process-stop evidence and an actual populated/hash-bound inventory.

The eight demo scenarios concern the Blender-selected local workflow/runtime. They do not independently attest separate-process AMQP/OPC UA. This review reads no trace ZIPs, saved DOM or pixels and makes no fresh manual, caption/dropdown, secret-scan, PDF visual, CI, Pages or remote-publication PASS claim. Those scopes remain explicit pending work.

Preparation validation: built-in compile(source, filename, "exec") only; the review module was neither imported nor executed. The prior source A terminal reviewer and saved demo schemas informed preparation only; there is no historical source/path fallback in the executable.

