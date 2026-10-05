# Verified deletion and same-test clearing

Audited implementation: `0d03402776cf7ba63710634c5df2a8047501bdfb`.
Task baseline: `4da22d75bded35452f4bca1db03c57da5e9eb957`.

[The refreshed Windows acceptance manifest](../acceptance/20261005T141427/manifest.json)
passes all 118 MUSTs. Both complete Windows suites pass 693 tests with no failures,
errors or skips and 91.72% coverage. The independently downloaded Linux CI artifact
also passes 693 tests twice, with identical case identities and 91.67% coverage.
Each suite includes 146 JavaScript checks and nine actual Chromium journeys.
All eight Blender demos and all quality/security/publication gates pass.

Delete removes the test's catalog entry and owned world files and releases its
display number. An empty workspace starts again at Test 1. Clear retains the same
test, number, cell and settings while resetting products and execution data for
retry. Tests inspect real catalog/filesystem removal, cancellation, interruption,
revision fencing, delayed-response draining and explicit retry. No owner's test
data was removed during development or verification.

## Inspectable evidence

- [CI audit](ci/audit.json): clean source, original test identities, coverage,
  gate results and verified artifact SHA-256. The ZIP is artifact `11352852960`,
  digest `b50ab7d8308ce8c3397ed754f34b8d43fc715c26bde9aea0ac904e1dec83bcd9`.
  [Original CI manifest](ci/original/manifest.json), JUnit and logs are retained
  byte-for-byte, including remote placeholders from `acceptance --local`.
- [Browser audit](browser/browser-verification.json): 18 recorded journeys from
  the two repetitions, including eight clear/retry/delete/create journeys,
  eight normal/fault investigation journeys and two deliberate HTTP 503 cases.
  Source hashes match the audited commit. Short case folders retain screenshots,
  requests and result files; complete traces remain in the GitHub artifact.
- [Windows demo audit](semantics/windows.json) and [Linux demo audit](semantics/linux.json):
  one original command and one transfer after lost acknowledgement and restart,
  fresh observation and reconciliation, conservative ambiguous outcomes, and
  six products using all six preferred tools. Replay never dispatches a pick.
- [Native launcher evidence](remote/native-evidence.json): six actual Windows
  startup/ownership/closure/recovery checks pass using the explicit headless
  adapter. Real Blender checks are separately recorded in the suites and demos.
- [Successful workflows](remote/runs.json): CI `37323017162`, native desktop
  `37323017158` and publication `37323017461` all match the audited source.
- [Public publication audit](publication/result.json): seven HTML pages, 375
  internal links, 31 sources, 12 diagrams, the 36-cell product/tool matrix and
  210 internal PDF links across 67 combined pages. Deployed source documents match
  Git. The preserved publication still correctly says NOT DONE at that earlier
  observation time; it is not retroactively relabelled as a completed publication.
  [Selected-page visual review](publication/visual-review.json) records its scope.

[The archive index](archive.json) records original paths, byte sizes and SHA-256
digests. Audit programs are preserved as text attachments under `audit-programs/`;
they ran from the repository's ignored `artifacts/` directory. Original Windows
local-only manifest and remote placeholders are preserved beside the refreshed
acceptance manifest. Research provenance is unchanged except for the previously
documented official Blender CLI source S31.

The [read/delete race](../test-reset-read-drain/README.md) and
[Windows Blender diagnostics](../test-reset-visibility/README.md) remain archived
as failures and scoped development checks. Neither assertions nor deadlines were
relaxed. SHOULD SC-BRAIN-005 remains the non-blocking external-model fallback.

The final documentation/status successor receives its own full CI, native and
publication checks under [ADR 0002](../../adr/0002-acceptance-attestations.md).
This archive attests only the source named above. Functional browser automation
is not an independent novice-user study or accessibility certification.
