# Acceptance and evidence

`uv run --locked python -m tools.dev acceptance` runs setup, the full mandatory
suite twice with separate temporary fixture roots, coverage (minimum 85%), lint,
strict types, security, eight deterministic Blender scenarios, documentation drift
checks and publication. Blender and PDF system libraries are required. Installation
and vulnerability auditing may use the network; runtime tests and demos do not.

The command writes dated evidence under `docs/evidence/acceptance/` and regenerates
`ACCEPTANCE_REPORT.md`. The explicit mapping is `docs/acceptance-map.json`. A test
requirement passes only if its named test was collected and passed in both runs;
any skipped, failed or missing test makes it fail. Gate exit codes, full command
lines, logs, JUnit, environment versions, lock hash and Git identity are retained.
Source documents and automated drift checks supply inspectable documentation
evidence, not a replacement for runtime tests.

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

The optional external model provider, real ERP delivery, OPC UA and hardware
integration are not completion gates. Missing optional model fallback is recorded
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
