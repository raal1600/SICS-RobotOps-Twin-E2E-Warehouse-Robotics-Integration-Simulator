# Investigation workflow: exact-source acceptance

The implementation at clean source
`7b9f0a656cdd077106ab4b7ee7ade82335e11f26` passes **all 118 MUST criteria**.
The baseline was `0db6168b71bc4b500894fe7695ce082384c777b2`.
The [refreshed local manifest](../acceptance/20261005T014537/manifest.json)
and root [acceptance report](../../../ACCEPTANCE_REPORT.md) map each criterion to
commands, tests and evidence. This archive does not attest a later commit.

| Verification | Executed result |
|---|---|
| Windows complete suite | 665 passing tests twice; identical case identities; zero failures, errors or skips |
| Windows coverage | 91.71597633136095% in each run; unchanged minimum 85% |
| Linux complete suite | 665 passing tests twice; identical case identities; zero failures, errors or skips |
| Linux coverage | 91.6596224288532% in each run; unchanged minimum 85% |
| Mandatory JavaScript wrapper | All 132 checks pass |
| Actual browser cases | Five per full suite: four normal/fault journeys and one intentional service-error case |
| Local gates | All 20 pass on both platforms, including eight actual Blender demos |
| Runtime versions | Python 3.13.15, Blender 5.2.1 LTS, Playwright 1.63.0 |
| Native host | Actual Windows window/ownership lifecycle, six checks, explicitly using the synthetic adapter |

All exact-source workflows succeeded:

- [Deterministic acceptance, run 37252672023](https://github.com/raal1600/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/actions/runs/37252672023)
- [Windows desktop, run 37252672189](https://github.com/raal1600/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/actions/runs/37252672189)
- [Publication and Pages, run 37252672013](https://github.com/raal1600/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/actions/runs/37252672013)

## What changed and what was exercised

The existing dashboard now follows Run a pick, notice its result and Investigate
this pick. Short scenario guidance leaves the cell central. A bounded inspector
separates symptom, recorded finding, limits and possible explanation. Evidence,
manual GET requests, JSON download and a collapsed job-filtered timeline remain
directly accessible. Navigation pins the test/job and preserves paused replay.
The review selector explains that another sensor check does not move the robot.
No robot/API wire schema, database migration or workflow state was changed.
The new presentation export wrapper is `robotops-investigation-1`.

Actual Chromium journeys use real loopback HTTP and SQLite with both synthetic
and real Blender runtimes at 1440x1000 and 390x844. Each normal/fault journey runs
a happy pick, loses a reply after effect, inspects the original evidence, downloads
it, follows manual URLs, returns without losing context, requests contradictory
then normal observations, creates a new independent test and reviews saved history.
The tests assert exact assessed-observation attribution, command ownership,
read-only navigation, bounded layout, keyboard tabs and no unexpected browser errors.
The separate 503 case deliberately records the expected console error while the
job stays RECEIVED with no command or journal; it is not a simulated pick failure.

- [Linux browser audit and original records](browser/browser-verification.json)
- [Desktop uncertain result](<browser/original/20261005T020824715345/test_run_notice_investigate_and_return[blender-desktop]/03-unusual-result.png>)
- [Compact uncertain result](<browser/original/20261005T021014720115/test_run_notice_investigate_and_return[blender-compact]/03-unusual-result.png>)
- [Desktop evidence](<browser/original/20261005T020824715345/test_run_notice_investigate_and_return[blender-desktop]/04-evidence.png>)
- [Compact manual inspection](<browser/original/20261005T021014720115/test_run_notice_investigate_and_return[blender-compact]/05-manual-inspection.png>)
- [Development comparison and clarity assessment](../investigation-ui-development/README.md)

The complete CI artifact retains both runs' screenshots and Playwright traces.
This compact archive keeps selected images, byte-exact browser request/error
records, downloads and semantic results. The served UI and journey-test hashes
match the exact Git source. The implementer also inspected desktop and compact
Linux captures: the result, evidence action and tabs remain readable, with no
visible clipping. The smaller layout uses internal scrolling and fixed navigation.

This is not an independent first-time usability study. Touch-device and
screen-reader studies were not performed. Dense technical JSON remains available
for download. Automation proves the tested functionality and evidence ownership,
not universal discoverability or physical robot performance.

## Original-command and tool evidence

The [Windows](semantics/windows-demo-audit.json) and
[Linux](semantics/linux-demo-audit.json) audits inspect actual persisted demo
snapshots. Lost acknowledgement after effect and restart each retain one order,
one job, one original command, one PICK_EFFECT and no replacement pick. Their
UNKNOWN_OUTCOME and RECONCILING transitions precede completion with a fresh
observation linked to the verification result. Ambiguous evidence stays
REQUIRES_INTERVENTION with INCONCLUSIVE verification and the same single effect.
Lost reply before effect, logical E-stop and cell fault have zero transfer effects.

The six-product showcase completes six original commands with the catalogue's
preferred tools: SKU-A/VAC_SINGLE, SKU-B/VAC_ARRAY, SKU-C/ADAPTIVE_SOFT,
SKU-D/PINCH_NARROW, SKU-E/PINCH_WIDE and SKU-F/SUPPORT_FORK, all with the `EE_`
prefix. The first tool is already mounted; its NOT_REQUIRED event and the five
subsequent tool-change completions are persisted. Each command has one transfer.
These are synthetic mechanics, tool rules and observations, not real robot validation.

## Independent artifacts and publication

[CI verification](ci/verification.json) validates GitHub artifact `11322490995`,
130,209,261 bytes, against SHA-256
`1fa2a66527f46a265e8358bdcff21d24910854d70c6c1f097d00153f1e1064e9`.
All 831 archive entries were bounded and checked for unsafe paths and symlinks.
Only the exact-source [original acceptance directory](ci/original/20261005T014654/manifest.json)
was selected; historical manifests were excluded. Its original manifest,
JUnit, coverage, logs and demo snapshots remain byte-exact. CI runs `--local`,
so its three remote placeholders and six dependent pending MUSTs remain unchanged.
The refreshed Windows manifest assembles the separate successful remote evidence;
this archive does not rewrite CI's original report to manufacture a pass.

[Native-host verification](desktop/verification.json) checks the downloaded build
digest, eight compiled/package file hashes and source identity. The six checks
cover real window rendering, duplicate launch, graceful close, original-command
recovery, abrupt close and reopening. This job explicitly uses the synthetic
adapter; the mandatory suites and eight demos supply real Blender coverage.

[Public publication review](publication/result.json) verifies 51 resources, seven
HTML pages, 374 relative links/fragments, 65 PDF pages, 209 internal PDF
destinations, 30 sources, 12 diagrams and the 36-cell catalogue matrix. All eleven
published Markdown source documents matched Git after newline normalization.
The three individual PDFs and all diagrams are byte-identical to the fd47 files
already rendered and reviewed. [The equivalence check](publication/visual-equivalence.json)
retains that distinction; the original [visual review](publication/render-basis/visual-review.json)
and contact sheets still identify fd47. No generated document was edited.

The implementation-source publication correctly said NOT DONE while its acceptance
was running. Those archived bytes are historical, not a present-day status claim.
The status successor rebuilds the PDFs and Pages from synchronized source and
receives its own exact-SHA verification. External research URLs were not re-audited;
their existing control dates and claim classifications were preserved.

## Integrity and remaining scope

[The archive manifest](archive-manifest.json) records 117 byte-exact imports,
their original paths, sizes and hashes. README and subsequent review metadata
are new explanatory records. Original paths inside CI files refer to the workflow
repository root; the retained copies live under `ci/original` here.
Full ZIPs and additional renders remain in ignored local artifacts.

The [failed first attempt](../acceptance/20261005T012342/README.md) remains intact.
Its old Causal timeline label assertion was aligned with the intentional Event
timeline UI and strengthened with structural navigation checks. Physical and
persistence assertions, test levels and thresholds were not weakened. Complete
fresh suites followed the correction.

SC-BRAIN-005 is the documented non-blocking SHOULD failure: an optional model
adapter/fallback is not implemented. Mandatory behavior remains deterministic and
requires no model API. The existing HKM-inspired/synthetic observation, dynamics,
collision-preflight and safety limitations continue to apply. See
[the operator guide](../../implementation/investigation.md) and
[ADR 0002](../../adr/0002-acceptance-attestations.md) for exact-source attestation.
