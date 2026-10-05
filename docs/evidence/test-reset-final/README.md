# Accepted test deletion and reusable clearing

Audited implementation: `df45c93247551e042f043216ab94d74a0ba34ff3`.
Baseline: `4da22d75bded35452f4bca1db03c57da5e9eb957`.

[The refreshed acceptance manifest](../acceptance/20261005T113952/manifest.json)
derives every MUST result from executed gates. Both complete suites contain 688
passing tests, no failures/errors/skips and 91.66% coverage. The nine real-browser
cases run twice, with source hashes checked against this exact commit. All eight
actual Blender demos pass, including one effect after lost acknowledgement and
restart, no replacement command, and intervention on ambiguous evidence.

The byte-verified CI artifact is identified in `ci-artifact.json`; `ci-audit.json`
records its digest, clean source, identical collected test sets and gate results.
`browser/browser-verification.json` verifies both repetitions, including eight
clear/retry/delete/create journeys and the two deliberately injected HTTP errors.
Short case folders retain screenshots and original request/result files.
`semantics.json` independently checks command identities, effect events, fresh
observations, verification verdicts and the six-tool showcase.

`native-evidence.json` and its checksum-attributed artifact verify actual window
startup, ownership, closure and conservative restart on Windows. `workflows.json`
records successful CI, desktop and publication runs for the same SHA.
`publication.json` compares public source documents with Git and checks seven
HTML pages, 374 internal links, PDF hashes/destinations and the canonical matrix.
That publication correctly still described verification as pending when checked;
it is preserved unchanged. `publication-visual.json` scopes the selected-page
layout review. A status/evidence successor must get its own CI and deployed SHA
verification, as required by [ADR 0002](../../adr/0002-acceptance-attestations.md).

The acceptance index initially retained the former monotonic-number test name,
even though the owner-authorized replacement had already passed in both suites.
The original CI manifest is preserved as `local-manifest.json` in the acceptance
directory. `before-mapping-fix.json` and its report preserve the first refreshed
FAIL. `mapping-erratum.json` records the corrected selector and four additional
clear regressions now required by that mapping. No test, MUST, threshold or
assertion was removed or weakened. The final report was regenerated from the
actual JUnit evidence using that corrected index.

[Development evidence](../test-reset-development/README.md) retains the earlier
renderer timeout, stale polling and Windows checkout failures and their fixes.
The local acceptance attempt `20261005T113217` was interrupted when the source
changed for the path correction; it has no completed-suite claim. Exact-source CI
supplies the complete repeated acceptance above. Research provenance is unchanged.
The status sources, lifecycle/API guides, reports, diagram caption and citation
version are synchronized; publication is generated through the normal builder.

`archive-manifest.json` hashes the imported evidence; audit programs are retained
as `.py.txt` attachments. They were executed from the repository's `artifacts/`
directory. The only outstanding SHOULD is the explicitly optional model-provider
fallback; the mandatory implementation remains deterministic and model-free.
