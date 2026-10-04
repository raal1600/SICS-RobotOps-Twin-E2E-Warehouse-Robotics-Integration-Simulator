# Exact-source lifecycle CI and publication evidence

This archive records remote verification for implementation source
`b1c374ae76144309cc4476392dec681292f0e3a7`. It does not attest a later
documentation/evidence successor or replace the root acceptance report. The
Windows local acceptance run was still running when these files were packaged.
No historical result, CI manifest or pending remote placeholder was rewritten.

All three exact-source workflows succeeded:

- [Deterministic acceptance, run 37233307538](https://github.com/raal1600/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/actions/runs/37233307538)
- [Windows desktop, run 37233307474](https://github.com/raal1600/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/actions/runs/37233307474)
- [Publication and Pages deployment, run 37233307475](https://github.com/raal1600/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/actions/runs/37233307475)

## CI provenance and results

GitHub artifact `deterministic-evidence`, ID `11315576113`, is 9,803,974 bytes.
Its downloaded ZIP matched the published SHA-256 digest
`044308f69a1b60d7ea925a4d3027d86228e09b87ea01c9a48c6dae14dbf11de7`.
All 659 archive entries were checked for traversal, absolute paths, symlinks
and excessive expanded size before selecting the exact-source evidence.
The ZIP remains in ignored local artifacts; it is not duplicated in Git.

The only selected acceptance manifest was
`docs/evidence/acceptance/20261004T204556/manifest.json`. It records the exact
clean source commit above, and its SHA-256 is
`63861fe8b0b7c43ba5418d2e23033bd5de3ff07321887cdfef4a742414f1cc7f`.
Every file from that selected evidence directory is preserved under
[ci/original/20261004T204556](ci/original/20261004T204556/manifest.json),
including both JUnit and coverage reports, logs, security results, repeatability
evidence and all eight demo snapshots. Older manifests in the ZIP were excluded.

Both JUnit runs contain **659 passing cases**, identical case identities and
zero failures, errors or skips. Both coverage reports record
**91.51873767258382%**. All 19 local gates, including eight Blender demos,
passed on Linux/Python 3.13.15. This is independent of the Windows local run;
platform-specific source-byte hashes and coverage values are recorded separately.

The CI command uses `--local`. Its original manifest therefore still contains
three unrefreshed remote gate placeholders (`ci`, `publication_remote`, `pages`)
and five associated pending MUSTs. It locally passes the other 105 of 110 MUSTs.
The completed workflow and public-publication checks are separate evidence here;
this archive does not rewrite those placeholders or claim that CI alone generated
a fully refreshed 110-MUST report. The root acceptance report is authoritative
for the final assembled acceptance decision.

## Public publication review

The [deployed publication](https://raal1600.github.io/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/)
was downloaded and checked against exact b1c source. Its build manifest matched
the source commit; all 11 downloaded Markdown source documents matched Git blobs
after newline normalization. The review checked 49 resources, seven HTML pages,
360 relative links/fragments, 63 PDF pages, 200 preserved internal PDF destinations,
30 sources, 11 diagrams and all 36 canonical product/tool matrix cells.

All 63 pages received contact-sheet visual review. Detailed review covered
pages 1, 3, 9, 11, 21, 34, 36, 39, 47, 49 and 60. Retained page images show the
generic cover, current revision status, lifecycle explanation, updated architecture
and canonical compatibility matrix. No overflow, caption or internal-link defect
was found. The public combined PDF SHA-256 was
`45ce08cdce5526358a8db79dfd5d87f4033b0e65a3cb84e4e36badf61e3ea581`.
Individual PDF hashes and every downloaded resource hash are in
[publication/result.json](publication/result.json). Full PDFs and contact sheets
remain in ignored local artifacts rather than this compact archive.

The b1c publication correctly said **NOT DONE** while b1c acceptance was running.
That archived status is not a present-day project-status assertion. Public URLs
can later serve a successor build; the retained manifest and content hashes define
this review's scope. The review's `worktree_dirty` flag describes the observer's
local checkout, not the independently downloaded exact-source public build.
External research URLs were not re-audited. Rendering is presentation evidence,
not proof of physical sensing, robot dynamics or safety certification.

## Integrity

[archive-manifest.json](archive-manifest.json) lists every byte-exact imported
file, its original local artifact path, size and SHA-256. No imported JSON,
XML, log, image or manifest was edited. The README and archive manifest are
new explanatory metadata. Original relative paths inside CI logs/manifests refer
to the workflow repository root; their retained files are under `ci/original` here.
The preceding source attribution remains mandatory if this evidence is cited.

## Subsequent status synchronization and test-fixture cleanup

These follow-up files are separate from the 53 immutable remote imports above:
[status checks](status-checks.json), [contract JUnit](status-contracts.xml),
[local publication build](status-publication-build.json) and
[fixture cleanup](fixture-cleanup/manifest.json). They record 119 passing contract
checks, quality/drift/publication checks and 32 passing lifecycle tests with
ResourceWarning promoted to an error. The cleanup closes a migration test's
SQLite connection; assertions and application source are unchanged. The initial
warning audit is retained. The local publication was built from the dirty status
successor, so its base SHA does not make it a clean b1c publication attestation.
The successor's full workflows and deployed source identity are checked separately.
