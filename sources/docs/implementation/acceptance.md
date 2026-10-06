# Acceptance and evidence

## Current Integration Lab audited-C evidence

Audited candidate C is `76e6abef95155b09484da9a226612d774ceb493d`. The complete Linux, Windows native and publication/Pages results linked here attest C. Original manual/Blender evidence remains source A `9e83fe7d41a52a63ba65b77730e392dafca8fffe`; source P's Windows checkout failure and C's isolated checkout correction remain preserved. This status/evidence successor R must pass its own complete workflows before the final goal declaration. Its independent CI artifact and deployed build.json supply R's identity without a self-hash commit loop. No result is relabeled as R execution.

[Exact C acceptance](../evidence/acceptance/20261006T201300/manifest.json) | [CI review](../evidence/lab-76e6abe/ci/review/linux-artifact-review.json) | [Windows review](../evidence/lab-76e6abe/windows/review.json) | [Publication review](../evidence/lab-76e6abe/publication/review.json) | [Runtime identity](../evidence/lab-76e6abe/source-relation.json) | [Payload review](../evidence/lab-76e6abe/payload-review.json)

All 169 MUSTs and the three coded remote gates pass for C. Windows native verification is reviewed separately; it is not an extra key silently added to the status tool. The original A manual runtime remains byte-identical. R receives its own Linux, Windows and publication/Pages attestation under ADR 0002.

The acceptance procedure and historical releases below retain their original scope.

`uv run --locked python -m tools.dev acceptance` runs setup, the full mandatory
suite twice with separate temporary fixture roots, coverage (minimum 85%), lint,
strict types, security, eight deterministic Blender scenarios, documentation drift
checks and publication. Blender and PDF system libraries are required. Installation
and vulnerability auditing may use the network; runtime tests and demos do not.

The investigation revision adds eight UI-INV MUSTs to the 110 existing criteria.
The full suite includes `tests/browser/test_investigation.py`: real Chromium,
real loopback HTTP/SQLite, both synthetic and Blender runtimes, desktop and compact
journeys, evidence downloads, conservative re-observation and an explicit service
error. Browser setup installs the locked Playwright browser; a missing executable
fails rather than skips. Screenshots/traces/request records and results are saved
under `artifacts/investigation-browser/`, uploaded by CI. The baseline report at
`docs/evidence/investigation-ui-baseline/` remains historical. Browser pass results
are functionality evidence, not proof of first-time usability; that assessment is
recorded separately in the [investigation guide](investigation.md) and final review.

The command writes dated evidence under `docs/evidence/acceptance/` and regenerates
`ACCEPTANCE_REPORT.md`. The explicit mapping is `docs/acceptance-map.json`. A test
requirement passes only if its named test was collected and passed in both runs;
any skipped, failed or missing test makes it fail. Gate exit codes, full command
lines, logs, JUnit, environment versions, lock hash and Git identity are retained.
Source documents and automated drift checks supply inspectable documentation
evidence, not a replacement for runtime tests.

Keep imported evidence paths within 100 characters relative to the repository
root so Windows can check out this repository inside GitHub's nested workspace.
Use short case/session folders and preserve the full original artifact paths and
byte hashes in the archive manifest. Renaming an archived copy must not modify
its content or relabel its audited source. The investigation archive retains the
checkout failure at `77a8237` and its path-only correction as inspectable history.

Each demo starts with a new data directory. Lost acknowledgement checks one effect
and zero duplicates; ambiguous reconciliation checks intervention; restart creates
a separate process. A separate test kills an orchestrator after runtime commit.
The eighth scenario, `tool_showcase`, executes all six preferred tools with six
verified jobs and exactly one transfer per original command. The HKM criterion
mapping adds the new geometry, tool, observation-boundary and compatibility tests
without deleting or weakening any original criterion.

Remote gates query public GitHub Actions and Pages and require the tested commit.
Unavailable, stale or failed remote evidence is FAIL, never presumed green. The
report can therefore show NOT DONE even with every local gate green. Approval to
publish is an external operational requirement, not grounds to weaken a MUST.

A report records the exact source SHA plus a hash of the inspected worktree and
whether it was dirty. For release evidence, run acceptance from a clean checkout.
Committing that report creates a new Git SHA: CI produces an immutable acceptance
artifact for its actual `GITHUB_SHA`. A previously committed report must not be
misrepresented as a run on a later commit. Final remote checks record workflow
URLs and the deployed `build.json` commit. Generated Pages/PDFs are only built by
the repository publication tool/workflow.

After downloading the CI evidence for a completed source commit, use
`uv run --locked python -m tools.dev acceptance --refresh-remote <manifest-path>`.
This preserves `local-manifest.json`, checks live workflows and Pages for the
same SHA, saves `remote.json` and regenerates the criterion table. It does not
rerun tests or change their outcomes. A failed local gate stays failed.
[ADR 0002](../adr/0002-acceptance-attestations.md) explains source snapshots and
the final-SHA attestation carried by CI artifacts and public `build.json`.

The optional external model provider, production ERP delivery and real hardware
integration are not completion gates. Actual OPC UA against the synthetic virtual PLC,
PostgreSQL, RabbitMQ and the separate edge service are mandatory for the Integration Lab.
Missing optional model fallback is recorded
against SHOULD SC-BRAIN-005. Reviewed subprocess exceptions are exact AST hashes;
changes require review again. Dependency vulnerabilities have no exceptions.

The guided workspace (ADR 0009) is exercised by the mandatory Node UI suite
inside test_playback_controls_never_dispatch_and_preserve_partial_recording_limits.
Pure guide tests reject substitution of planning observations or scene truth,
explain degradation reasons and prioritize unresolved original work. Dashboard
tests check navigation, focus preservation, explicit reset, repeated review,
archived histories and all execution/observation combinations. Confined CSS/JS
routes are verified alongside the pinned offline viewer assets. Isolated browser
flows and the preservation snapshot are recorded in
`docs/evidence/guided-workflow-local.json`; these are additional UI evidence, not a
replacement for the twice-run mandatory suite or remote release gates.

The later selector-explanation change is scoped separately in
`docs/evidence/scenario-help-local.json`. The full-system baseline remains
`docs/evidence/acceptance/20261003T205102`; it is not relabelled as a later run.
Affected UI, observation, reconciliation, test-history and contract suites verify
the follow-up. Browser checks cover all choices, comparison tables and narrow
screens; reading help must leave the original uncertain command unchanged.

The cell-selection and explicit deletion revision (ADR 0011) is tested by
`tests/integration/test_test_management.py` and the mandatory dashboard suite.
Coverage includes saved legacy profiles, selected-cell validation, confirmation
and cancellation, deletion without archive activation, empty-workspace restart,
durable cleanup intent, interrupted cleanup, bounded paths, cross-process execution
and download races, and request retries after a lost response. These checks extend
the existing persistence and demonstration evidence mappings without changing any
MUST threshold. The previous HKM acceptance is preserved in
`docs/evidence/test-lifecycle-baseline/`; it does not attest this revision.

Fresh acceptance of clean source `b1c374ae76144309cc4476392dec681292f0e3a7`
passes all 110 MUSTs in
[the refreshed local manifest](../evidence/acceptance/20261004T204452/manifest.json).
Both local suites and both independent CI suites contain 659 passing tests with
zero failures, errors or skips. [The remote evidence archive](../evidence/test-management-final/README.md)
retains the original CI manifest, including its unrefreshed remote placeholders,
alongside successful workflow and public-publication checks. The final status
and evidence successor still needs its own exact-SHA CI and Pages attestation.

## Delete versus clear correction (ADR 0013)

The clean baseline is 4da22d7. Its source-specific acceptance remains preserved.
The owner's correction deliberately replaces the old monotonic-label/permanent-row
expectations: deletion now removes the catalog row and frees its number; clear
retains that same test for a new run. New regressions inspect filesystem/catalog
removal, same-test restoration, revision guards, cached hosts, stale retries,
interrupted reset and legacy receipt migration. Four real browser cases exercise
clear/retry and delete/create Test 1 with both runtimes at desktop/compact sizes.
No physical-effect, uncertainty, verification or coverage assertion is weakened.

The df45c93 implementation is accepted with 688 passing tests in each clean CI
suite, 91.66% coverage and successful native/publication workflows.
[The release archive](../evidence/test-reset-final/README.md) includes the original
failed stale-selector report and its mapping correction against actual passed
JUnit cases. All 118 MUSTs pass in the refreshed report. The interrupted local
attempt is retained without a completed-run claim; the exact-source CI artifact
provides both complete suites. Evidence/status successors are verified separately.

The subsequent full-source run exposed a replay-response/deletion race; local
browser runs also exposed Windows Blender deadlines. Those original failures
remain archived. Response-body draining, unchanged-visibility optimization and
the documented Windows process-local QoS option are accepted at clean source
`0d03402776cf7ba63710634c5df2a8047501bdfb`: all 118 MUSTs pass, with 693 tests
twice on each of Windows and Linux, 146 JavaScript checks, nine browser journeys
per suite and eight Blender demos. [The exact-source archive](../evidence/reset-verified/README.md)
retains independent audits, original CI remote placeholders, publication checks
and links to the failures. Robot deadlines, rendering quality, schema boundaries
and all outcome assertions remain unchanged. The status successor still gets
its own exact-source workflows and deployed build check under ADR 0002.
