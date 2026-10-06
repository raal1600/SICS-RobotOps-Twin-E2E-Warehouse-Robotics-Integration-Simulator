# Goal Progress - Integration Lab

Current objective: root [GOAL.md](GOAL.md), introduced at `814979d`.
Status: **NOT ACHIEVED**. Earlier simulator acceptance remains historical.

Milestones A-D are implemented on `feat/integration-lab`: bounded persisted stages
and revision-guarded authorization, the guided console and shared automatic
handlers, PostgreSQL/outbox durability, RabbitMQ and durable edge inbox, actual
OPC UA traffic and retained PLC command identity, separate WMS HTTP acknowledgement,
conservative recovery, Blender handoff, source/payload inspectors and telemetry.
The requirement registry contains 169 MUSTs, including all 51 root GOAL checkboxes.

## Final-loop evidence and corrections in progress

The complete first acceptance suite on frozen implementation `f78985b` executed
**799 tests: 796 passed, 3 failed, no skips**, with **91.44% coverage**. Setup,
headless browser installation, Blender availability and configured security checks
passed. All four separate-process lab browser cases passed: real Blender happy
path, lost ACK after effect, duplicate delivery and WMS HTTP 503 recovery. Each
retained the original command with one effect; Blender produced 133 evaluated
frames, 118 distinct robot poses and visible rendered motion. These individual
passes do not turn the failed full suite into accepted evidence.

[The retained failure record](docs/evidence/lab-f78985b/summary.json) and
[original acceptance manifest](docs/evidence/acceptance/20261005T195412/manifest.json)
identify the exact source and commands. The second pass was deliberately stopped
after the first failed, so it is explicitly interrupted, not passed. Original
JUnit, coverage and logs remain unchanged.

The synthetic guided browser failure repeatedly encountered observations older
than the unchanged five-second freshness limit before any command existed.
Two Blender investigation failures exposed test observation issues: one asserted
the title before the actual UI action finished loading confirmed evidence; another
read-only test GET received ECONNRESET while the server remained responsive.
Corrections wait for the existing action completion, allow one bounded reset retry
on test GETs only, and close the lab browser helper's SQLite readers. No robot
operation, freshness limit, physical retry rule or outcome assertion is relaxed.
Terminal console wording is also corrected so completed sessions invite review
instead of incorrectly asking for further verification.

Scoped correction verification passed: 109 dashboard tests, all three previously
failing browser journeys (271.94 seconds), repository lint/formatting, strict mypy
for 66 source files, and the 169-MUST documentation drift check.
[Corrective results](docs/evidence/lab-f78985b/corrections/summary.json) identify
the changed source bytes; these checks do not replace full acceptance.

The next clean campaign on `f00ad15` was intentionally interrupted after a saved
Playwright trace confirmed another investigation-test helper error. Its busy-label
check used a literal question mark instead of the UI ellipsis, so it returned
before the action completed; the next five-second enabled assertion expired
after successful WMS reconciliation. The trace then showed the enabled Continue
button. No backend error, extra physical effect, or connection reset was observed.
The correction waits for the actual UI action to become idle within the helper's
existing timeout budget. The incomplete campaign is not a full-suite result;
[its interruption record](docs/evidence/acceptance/20261005T210653/interruption.json)
preserves that distinction. The corrective run then passed all 16 scenario bodies
across both browser files, but exited with one Blender-desktop server teardown
error. Cleanup logged Windows Proactor `ConnectionResetError` before the unchanged
20-second server shutdown assertion failed. A separate 48-case real TCP probe did
not reproduce that exact callback race. The fixtures now explicitly close their
Playwright contexts before closing the browser, following the documented graceful
cleanup order. No event-loop replacement, exception suppression, or shutdown
deadline increase was applied. Both Blender investigation layouts and the actual
separate-process Blender lab happy path then passed: **3 passed, 5 deselected in
381.80 seconds**, with no failures or teardown errors. The selection deliberately
targeted the changed cleanup paths and does not replace the full suite.
[The correction record](docs/evidence/lab-f00ad15/summary.json) preserves source
hashes, failed/interrupted results, the probe limitation and passing rerun.
The clean campaign on `dfb06bc` then passed the complete first suite:
**799 passed, zero failures, errors or skips in 2300.346 seconds**, with
**91.44% coverage**. All four separate-process lab browser cases passed and their
captured runtime/PLC journals retain the original command with one effect.
The acceptance runner subsequently exited during temporary-fixture cleanup with
Windows sharing error 32, before starting the second pass. The ignored evidence
watcher had used SQLite's transaction context without explicitly closing its
connections. An isolated Windows probe reproduced that handle-retention mechanism
and verified that explicit close releases both databases immediately, including
the exception path. The historical locker was not identified at the failure
instant; a later exclusive-read probe already found the file unlocked. This is a
probable watcher cause, not a demonstrated product failure. No production code,
acceptance cleanup rule or test assertion was changed. The watcher is corrected;
a new clean full two-pass campaign is required. [The retained record](docs/evidence/lab-dfb06bc/summary.json)
keeps the successful suite distinct from the incomplete acceptance runner.

The next clean campaign on `4774af5` completed successfully: **799 passed twice,
zero failures, errors or skips**, with coverage **91.3835% / 91.4398%**. Both
case sets match. All 20 local gates passed, including eight actual Blender demos,
security, lint/type checks and publication generation. The three remote gates
remain pending; this proves 163 of 169 MUSTs locally, with six depending on remote
attestation. The optional model SHOULD remains separate. The original results are
in [the complete campaign](docs/evidence/acceptance/20261005T224038/manifest.json).

A fresh native Blender lab then completed the manual browser happy, lost-ACK and
duplicate-delivery journeys, plus both exact README CLI commands. Saved evidence
proves the physical gate precedes the effect, reload preserves the authoritative
session, six inspectors are read-only, and duplicate authorization preserves the
original result. Lost-ACK reconciliation retained the original runtime receipt and
one effect; the PLC legitimately gained its first retained result. Duplicate
publication increased inbox deliveries from one to two with the same command/hash
and one effect; its broker redelivered flags were false. The selected manual
browser diagnostics contained no errors. These are simulator results, not a
guarantee of exactly-once physical execution in an industrial installation.

Manual screenshot inspection also found two presentation defects that prevent
completion: supported distributed scenarios had no short explanation, and their
replay could incorrectly say Happy path when no robot-runtime fault was injected.
The correction supplies persisted per-job scenario metadata for historical replay
and complete scenario summaries. A related source-level race also needs command-
bound live-response guards; the old protocol text at the captured physical gate
was hidden, not a visible false claim. These changes require regression checks
and a new source-bound acceptance campaign. The successful `4774af5` campaign and
manual evidence remain historical proof of their exact source, not proof of the
correction. See [the retained record](docs/evidence/lab-4774af5/summary.json).

The bounded correction now passes **90 targeted Python tests**, with the final
JavaScript wrapper rerunning the same five files as the **160-pass Node check**.
It also passes **10 focused browser/real-protocol cases in 223.25 seconds**; the
Blender happy case was deliberately deselected from that focused lane. The saved
duplicate and WMS screenshots show correct historical captions even after changing
the next-order selector. Full repository typing and the 169-MUST drift check pass.
[Correction evidence](docs/evidence/scenario-label-correction/summary.json) records
the exact code hashes and the distinction from full acceptance. The complete
saved lab trace scan found no credential candidates in its listed scope, while
preserving the historical caption findings. All 64 generated PDF pages were
visually reviewed before the final status rebuild.

The clean corrected-source campaign on `b968586` passed all **811 test bodies**
but failed one compact Blender investigation fixture teardown: the API thread
did not stop within 20 seconds. Its JUnit therefore has **810 clean cases and one
error**, with no test-body failures or skips; coverage is **91.4750%**. All four
distributed browser cases passed, and six saved screenshots show the corrected
captions. The second pass was stopped after the first failure and has no terminal
result. [The failed campaign archive](docs/evidence/lab-b968586/summary.json)
preserves these results without claiming full acceptance.

The saved log contains a Windows Proactor socket-shutdown reset. A deterministic
probe reproduced its cleanup mechanism: the exception skips socket close and
transport detachment, leaving Uvicorn waiting for an accepted connection even
after its request/connection sets are empty. Ordinary loopback resets did not
reproduce the timing-sensitive Chromium trigger. The correction configures the
same explicit Windows HTTP selector loop for native services and their fixtures;
it does not change the global policy, OPC UA loop, Playwright loop or workflow.
Existing shutdown bounds remain strict and fixture failures now include task and
thread diagnostics. [Native loop limits](docs/integration-lab-native.md) document
the 512-socket limit and lack of asyncio subprocess support; Blender continues to
use synchronous worker-thread subprocess calls.

Four real HTTP/WebSocket lifecycle regressions pass, as do the three existing
desktop close/reopen/isolation cases (15.70 seconds), repository lint/formatting
(201 files), strict typing (67 source files), and the 169-MUST drift check. The
four selected Blender browser checks also pass in **223.46 seconds**, with six
synthetic cases deliberately deselected: investigation at desktop and compact
sizes, guided happy/reload, and the separate-service lab happy path. No failures,
errors or skips were recorded, and the frozen source hashes are unchanged.
An independent bounded review found no blocking issue. The
[correction archive](docs/evidence/lab-b968586/http-loop-correction/summary.json)
preserves the probe, exact focused results, source hashes and review receipts.
These focused results do not replace a new clean, two-pass acceptance campaign
or the final manual loop.

Required next evidence: run full acceptance on the clean corrected source,
repeat the final manual checks, finish trace/publication review,
then update the final report and all requirement evidence. Exact-source CI, publication and
Pages verification remain mandatory. Remote publication requires explicit approval
following the earlier automatic approval rejection; no remote action is inferred
from local results. See [the complete checklist](docs/integration-lab-requirements.md).

## Historical pre-lab progress

Last updated: 2026-10-05 UTC
Current revision: delete removes a test completely; clear resets that same test for reuse.
Base: `4da22d75bded35452f4bca1db03c57da5e9eb957` (clean).

## Accepted: complete deletion and same-test retry

Audited implementation: `0d03402776cf7ba63710634c5df2a8047501bdfb`. All 118 MUSTs pass in
[the refreshed acceptance manifest](docs/evidence/acceptance/20261005T141427/manifest.json).
Windows and Linux each pass 693 tests twice, with identical case sets and no
failures, errors or skips. Coverage is 91.72% locally and
91.67% in CI. The suite includes 146 JavaScript checks and nine
actual-browser journeys on each repetition. Eight real Blender demos pass;
independent audits prove the original command moves the product exactly once
after lost acknowledgement and restart, while contradictory evidence remains
inconclusive. The six-product showcase uses all six preferred tools.

[The exact-source archive](docs/evidence/reset-verified/README.md) preserves the
CI artifact digest, both original manifests, browser/source checks, native-host
results and public source/PDF/link verification. Delete removes the catalog row
and owned world files and reuses the lowest free display number; an empty history
starts at Test 1. Clear retains the test identity, number, cell and settings while
restoring products and removing prior execution data. Neither action issues a
pick. Confirmation/cancellation, interrupted cleanup, stale writes, delayed view
responses and fresh Test 1 creation are covered using disposable data only.

Drift resolved: the former pending status is replaced by executed evidence in
README, all three reports, status metadata, handoff, checklist, acceptance guide,
PUBLICATION and this progress record. The earlier plan/runtime/replay descriptions,
source S31 and security review already match the fixed Windows invocation.
Contracts, architecture/state diagrams and the 118 MUST definitions were reviewed
and remain unchanged in this evidence update. No prior failed evidence is rewritten.
SHOULD SC-BRAIN-005 remains the optional external-model fallback, not a mandatory
dependency. No new ADR is needed beyond lifecycle ADR 0013.

Final source synchronization also updates the report generator's drift narrative
and affected-file list. Twelve governance/completion/documentation checks pass,
along with lint, formatting, typing and a rebuilt publication. The first scoped
check encountered an inaccessible shared temporary directory; a fresh disposable
fixture directory passed. Mixed line endings introduced by the text edit were
normalized by Ruff before the final format check. These development checks do not
replace the clean acceptance evidence above.

Next: the evidence/status successor receives its own complete CI, native workflow
and deployed-SHA publication audit under ADR 0002 before final delivery.

## Verification history: view-read draining and Windows Blender scheduling

The final evidence/status successor `317d4a4` exposed a real timing race in CI
run 37308097691: suite 1 passed 688 tests; suite 2 passed 687 and failed the
desktop Blender delete journey. A 541 ms replay response overlapped deletion;
the unchanged backend access barrier correctly returned TEST_OPERATION_IN_PROGRESS.
The [failed evidence](docs/evidence/test-reset-read-drain/README.md) preserves the
artifact digest, original manifests/JUnit, trace finding and earlier accepted report.
That failed revision was NOT DONE; previous acceptance below stays source-scoped.

The UI now drains its own JSON and snapshot response bodies before confirmed
create/clear/delete, keeps polling paused and holds the busy state until its final
refresh completes. A five-second view-read wait expires without sending a
management request, allowing explicit retry. Backend guards, robot deadlines,
command identity, schemas and verification are unchanged. Seven new controlled
network/UI regressions bring the passing JavaScript suite to 146 checks.

All 151 backend lifecycle tests pass. Isolated browser verification also exposed
intermittent Blender deadlines, so concurrent suites were not the whole cause.
The original 60-second deadline and uncertain-outcome behavior remain intact.
[Local failures and profiling](docs/evidence/test-reset-visibility/README.md) are
preserved separately from acceptance. Avoiding redundant visibility assignments
removes unnecessary graph invalidation, and actual hidden/visible keyframes survive
save/reopen; this optimization alone did not resolve the full browser suite.
A two-worker diagnostic also timed out and was not adopted. Blender's documented
Windows hybrid-CPU `--qos high` option passed all nine diagnostic browser journeys.
The production adapter now selects it on Windows and records `cpu_qos` in its
manifest; Linux arguments and system scheduling settings are unchanged. Twelve
production checks pass: all nine browser journeys, saved visibility, exact-one
lost-ack/restart/read-only replay, and the six-tool showcase. Another 170 unit and
contract checks pass. No assertion, render setting, motion frame or deadline is
relaxed. Source S31 records the official CLI documentation; the other provenance
entries are unchanged. Scene and control/state diagrams need no boundary changes.

CI/native/publication all passed for clean read-drain source `def3d51`. The
further Windows correction was committed as `0d03402` and received the separate
complete acceptance recorded above. Final-source evidence is never inferred from
its parent.

## Previous accepted: test deletion, reset and reusable numbering

Audited implementation: `df45c93247551e042f043216ab94d74a0ba34ff3`.
[The current acceptance manifest](docs/evidence/acceptance/20261005T113952/manifest.json)
passes all 118 MUSTs: 688 tests twice, 91.66% coverage, 139 JavaScript checks,
nine actual-browser cases per suite and eight Blender demos. CI, native Windows
lifecycle and publication all pass for that exact source. The
[release archive](docs/evidence/test-reset-final/README.md) retains artifact hashes,
independent effect/browser audits, public-source comparisons and earlier failures.

Final drift findings: the acceptance index retained the old renamed numbering
test, and citation metadata still named publication 1.3. The index now requires
the passing number-reuse test plus four additional clear regressions; original
FAIL evidence is preserved. Citation metadata now matches publication 1.4.
No assertion or MUST was weakened. Optional model fallback remains a documented
SHOULD failure; the mandatory deterministic paths pass. The evidence/status
successor still receives its own full CI and exact deployed-SHA check (ADR 0002).

### Implementation and verification history

The owner's explicit 2026-10-05 correction supersedes ADR 0011's permanent
deleted-test rows and lifetime display numbering. Delete must purge the test's
world, evidence and catalog entry; new tests use the first available number,
starting at 1 when empty. Clear retains the test identity/number/cell and resets
its data for another run. Temporary cleanup intent and anonymous request digests
must still protect interrupted operations and delayed retries without retaining
deleted test records. Robot command/reconciliation semantics are unchanged.

Verification uses disposable roots only; the owner's current tests are untouched.
Catalog migration, digest guards, fresh-world revisions, cached hosts, API and UI
are implemented. Targeted results: 49 lifecycle integration tests and 139 total
JavaScript checks pass. Confirmation/cancel, archive reuse, lost responses,
locked files, interrupted reset, old-catalog migration and stale writes are covered.
All four actual browser lifecycle cases pass in both runtimes/viewports. Browser
verification exposed display-rate CPU rendering contention and stale polls
after deletion; presentation now draws at 24 fps and suspends those polls during
management. No runtime timeout, render quality or robot assertion was relaxed.
Earlier failures, final targeted results and screenshots are retained in
[development evidence](docs/evidence/test-reset-development/README.md).
The publication rebuild, security scan, lint/typecheck and drift check pass.
Those targeted results preceded the complete exact-source acceptance above.

The first implementation commit is `2eddd8a`. Its Windows workflow detected overly
long archived browser-case paths at checkout, before running the launcher tests.
The evidence directories were shortened without changing their bytes; the failure
and path/hash provenance remain archived. Runtime code/tests did not change.
Local acceptance `20261005T113217` started before that documentation-only relocation
and was explicitly interrupted as superseded. It does not claim completed suites.
The corrected commit's full CI and publication supply the exact-source attestation.

ADR 0013 and affected API contracts, plan/handoff, operator/persistence/playback
guides, all three reports and architecture caption are synchronized. Robot wire
schemas and research provenance are unchanged. Prior acceptance below is historical.

## Previous accepted implementation

Audited implementation: `7b9f0a656cdd077106ab4b7ee7ade82335e11f26`.
Implementation baseline: `0db6168b71bc4b500894fe7695ce082384c777b2`.

## Current phase: accepted investigation implementation and final attestation

All 118 MUSTs pass for clean audited source 7b9f0a6. The eight UI-INV criteria are
additive to the original 110; no threshold, physical outcome or evidence boundary
was weakened. [The refreshed acceptance manifest](docs/evidence/acceptance/20261005T014537/manifest.json)
and [exact-source archive](docs/evidence/investigation-ui-final/README.md) provide
inspectable results. This report does not attest an untested later commit.

The workspace follows Set up, Watch, Investigate and Continue. The cell stays
central, with concise scenario purpose and behavior to watch. Attention opens an
explicit bounded inspector for symptoms, recorded findings, limits and possible
explanations. Evidence and manual inspection include the exact assessed observation,
original command/journal, review history, tool decision, scoped GET examples,
real code/config/log paths and downloadable JSON. The timeline is collapsed,
job-filtered and bounded. Test/job selection and paused replay context survive
navigation; sensor re-observation remains an explicit original-command assessment.

No robot/API wire contract, runtime state machine or database migration changed.
The presentation download wrapper is `robotops-investigation-1`. Actual HTTP errors
remain separate from simulated outcomes. All old test lifecycle, cell-selection,
uncertainty, restart, exact-one-effect and read-only replay behavior is retained.

## Current evidence

- Windows: 665 tests twice, identical case identities, zero failures/errors/skips,
  91.71597633136095% coverage in both runs and all 20 local gates passing.
- Linux CI: 665 tests twice, zero failures/errors/skips, 91.6596224288532% coverage
  in both runs and all 20 local gates passing. Exact run 37252672023 succeeded;
  its digest-verified original artifact and local-only remote placeholders are preserved.
- The mandatory suite includes 132 Node checks and five actual Chromium cases:
  synthetic/Blender at desktop/compact viewports, plus an intentional service error.
  Both repeats retain screenshots, requests, source hashes, downloads and traces.
- Eight real Blender demos pass on both platforms. Read-only audits prove one
  original command/transfer after lost reply and restart, conservative ambiguous
  evidence and six products using all six preferred tools. No replay issues a pick.
- Exact-source native workflow 37252672189 passes six actual window/ownership
  checks with the explicit synthetic adapter. Blender coverage is recorded separately.
- Exact-source publication workflow 37252672013 and Pages pass. Public review checks
  51 resources, 374 relative links/fragments, 65 PDF pages, 209 internal PDF
  destinations, 30 sources, 12 diagrams and the canonical 36-cell tool matrix.
  Public Markdown matches Git; byte-identical PDF/diagram comparison preserves the
  original fd47 visual review attribution rather than relabelling it.

The first clean fd47 attempt passed 664 of 665 tests; its older dashboard smoke
test expected the renamed Causal timeline label. [Failure evidence](docs/evidence/acceptance/20261005T012342/README.md)
remains unchanged. The correction kept all metrics, restart and exact-one-effect
assertions and added structural inspector/timeline checks. Complete clean runs
followed at 7b9. Browser-discovered slow-planning selection, premature snapshot
requests and saved-test evidence loading races were fixed and rerun earlier in
this same implementation. No user test data was changed or deleted.

## Decisions and knowledge-base synchronization

ADR 0012 supersedes ADR 0009's automatic review opening with explicit investigation,
while preserving its state-based guide and recovery rules. The visual/functional
review is an implementer assessment, not independent first-time user research.
Compact layout checks are not touch-device or screen-reader studies.
SC-BRAIN-005 remains the documented non-blocking SHOULD for an optional model Brain.

Synchronized: plan, handoff, checklist, MUST registry/mapping, acceptance, README,
operator/scenario/desktop/playback/contracts/reconciliation/dependency guides,
ADRs, source setup/CI instructions, reports, architecture and investigation diagrams,
publication 1.3 metadata and citation. The lifecycle addendum's historical 110-MUST
count now explicitly precedes the eight new criteria. Research provenance and
control dates remain unchanged; this is simulator presentation work, not a new
HKM/SICS performance claim. Generated Pages/PDFs are rebuilt through the publication
workflow and never manually edited.

## Final-source gate and next milestone

The first evidence/status successor `77a8237` failed Windows checkout before its
tests could run because imported browser/native evidence paths were too long.
The original job log is retained in the final archive. Short case/session folders
now preserve all 117 imports byte-for-byte, with original and prior archive paths
in the manifest. This packaging correction changes no application behavior or
test result; the corrected successor must pass all exact-source workflows.

The evidence/status successor must receive its own complete CI and Pages checks
before this goal is closed. Its exact source is recorded by the CI artifact and
public build.json, following ADR 0002's self-reference rule. Earlier source results
never attest a later SHA. After that gate, independent first-time usability research
and an optional model adapter are non-blocking follow-up work; no further mandatory
feature implementation is outstanding.

## Historical accepted phase: test lifecycle and robot-cell selection accepted at audited source

Implementation baseline: `ae6d5d85c813e47aea042aea2a87236b5a8bc204`.
Audited source: `b1c374ae76144309cc4476392dec681292f0e3a7`, clean at the
start of acceptance. All 110 MUSTs pass for this source. The prior acceptance
below remains historical evidence. No user test data has been deleted during
development.

Milestone: introduce a registered robot-cell selector for new tests, explicit
selected-test deletion and clear-all confirmation, durable deletion identity,
safe file cleanup and an empty workspace. Only the implemented HKM-inspired
profile is selectable; legacy recordings preserve their original profile.
Deleting an active test leaves no active test and never promotes an archived
uncertain workflow. Playback and data management dispatch no robot commands.

Implemented: typed cell registry, profile-aware test history, confirmation
dialogs, empty workspace, request-bound retries, committed deletion tombstones,
bounded cleanup and cross-process response-lifetime locks. API and desktop
bootstrap read the catalog before opening any world, so deletion survives
restart. The original test uses its configured database basenames; unrelated
files remain intact. Empty-workspace health and OpenAPI remain available.

Scoped checks: 146 targeted backend checks (including 32 new lifecycle checks),
137 affected API/desktop/replay regressions, 119 UI checks and 71
governance/schema checks pass. Six final backend smoke checks also pass. Lint,
strict typing, security audit, source drift and generated HTML/PDF publication
pass. Actual isolated browser review covered creation, a completed pick,
confirmed deletion, clear-all, empty restart and creation of six fresh HKM
products, including a narrow-screen dialog check. Development artifacts are in
`docs/evidence/test-management-local/`; the independent review retains initial
findings and corrected source hashes. Existing MUST thresholds and
uncertainty/idempotency semantics are unchanged.

Complete Windows acceptance passed 659 tests twice, zero failures/errors/skips,
with identical test identities and 91.57509157509158% coverage. The 119 Node UI
checks pass. All 19 local gates pass, including setup, security, lint, strict
typing, eight actual Blender demos, drift and two publication builds. Exact-source
Linux CI independently passed 659 tests twice with 91.51873767258382% coverage.
CI run 37233307538, Windows desktop run 37233307474 and publication run
37233307475 all succeeded. The [refreshed acceptance manifest](docs/evidence/acceptance/20261004T204452/manifest.json)
records every MUST, command, log and exact-source remote gate; its original local
manifest remains unchanged. [Remote evidence](docs/evidence/test-management-final/README.md)
preserves the verified artifact digest, original CI results and public review.

Lost acknowledgement after effect and restart each produce one original command,
one transfer and no replacement pick, resolving UNKNOWN_OUTCOME through fresh
observation and the original journal. Ambiguous evidence remains
REQUIRES_INTERVENTION with the same one effect. The showcase completes six
transfers with all six preferred tools. Public review checks 49 resources,
360 relative links/fragments, 63 PDF pages, 200 PDF destinations and the
36-cell compatibility matrix against b1c source.

Knowledge-base review: ADR 0011, plan, handoff, checklist, implementation/API
documentation, reports and diagrams are synchronized in this milestone. The
acceptance map adds lifecycle regression evidence to existing persistence and
demo criteria. Prior report bytes remain archived separately.
Publication review also caught obsolete HKM-in-progress wording on PDF covers;
the builder source now refers to the current revision status. Actual Windows
EXE lifecycle and clear-all/reopen checks also pass in isolated data roots;
closing the test window releases its backend and empty restart keeps databases
deleted. Hidden native-window text inspection was unavailable; the separate
browser review verifies the rendered empty panel.
Final synchronization also records this acceptance and closes a SQLite connection
in a migration test fixture; application and robot semantics are unchanged.
The warning and targeted cleanup verification are retained separately from the
frozen b1c results. SHOULD SC-BRAIN-005 (optional external-provider fallback)
remains non-blocking. Optional model/hardware work is unchanged.

Next: commit the evidence/status successor, then independently verify its full
CI, desktop build and published source SHA under ADR 0002. This report identifies
the audited source; the successor's own CI artifacts attest its exact revision.

## Historical milestone: HKM-P3 acceptance complete at audited source

Enhancement baseline: `eaf35b499e80a5ce31b2ea3a24fbfa010bc67c98`.
Audited implementation source: `ca7798798f916c8130e1833cf16b4d4d3f10d546`,
clean at the start of acceptance; source hash
`d52ed73663702ef2acac0be80989a400f53e88714163f30210dc0ea27f582513`.

All **110 MUSTs PASS** (original 85 plus HKM-VIS-MUST-001 through -025).
The [acceptance manifest](docs/evidence/acceptance/20261004T122253/manifest.json)
retains commands, logs, versions, named tests, criterion mappings and exact-source
remote attestations. Both Windows suites passed 622 tests, zero failures/skips,
with identical 91.17558174675129% coverage. The 107 Node UI checks are included.
Linux CI independently passed 622 tests twice with 91.11514052583863% coverage.
Setup, lint, strict typing, dependency/security checks, drift and both publication
builds passed. Eight actual Blender demos passed. Blender is 5.2.1 LTS; Python is
3.13.15 and Node is 20.17.0.

Lost acknowledgement after effect and restart each preserve one original command,
one PICK_EFFECT and one transfer, and resolve through journal plus fresh observation.
Ambiguous evidence remains REQUIRES_INTERVENTION without another pick. The full
showcase completes six jobs, six original commands and six transfers, using
VAC_SINGLE, VAC_ARRAY, ADAPTIVE_SOFT, PINCH_NARROW, PINCH_WIDE and SUPPORT_FORK
for SKU-A through SKU-F respectively. Independent read-only persisted-evidence
checks are retained in `docs/evidence/hkm-final-audit/`. Their first ad-hoc
exact-float comparison and corrected review remain separate; the established
1e-6 Blender transform tolerance and production assertions were not changed.

Actual browser review covered six-product delivery replay, tool/camera controls,
lost-ack uncertainty, contradictory intervention and fresh-observation resolution.
Earlier tests and saved user data remain intact. Reopen the installed launcher
and use Start new test to see the new profile; historical tests retain their
original scenes. The snapshot remains collapsed in Technical details.

Knowledge-base synchronization: README, plan, handoff, checklist, implementation
guides, schemas, canonical catalogue/matrix, 11 diagrams, 30 research sources,
reports and publication status agree with the implemented boundary. Final status
synchronization also corrects the guide's mass wording to conservative catalogue
maximum and the report's publication-version reference. The diagrams describe
implemented behavior; manufacturer claims remain distinct from simulator design.
No material drift remains after the final checks. ADR 0010 records the adaptation;
ADR 0002 governs the separate source and evidence/status commit attestations.

The exact ca77987 CI, Windows desktop and publication workflows passed. Public
HTML/PDF hashes and source SHA were verified, with 360 HTML links/fragments,
200 combined-PDF destinations and 36 compatibility cells checked. The publication
review remains scoped to its recorded source; later Pages builds are verified
again. Source CI artifact evidence is under `docs/evidence/hkm-ci-ca77987/`.

SHOULD gap: SC-BRAIN-005 optional external-provider fallback remains unimplemented
and non-blocking. Optional model APIs, hardware, dynamics and production ERP
integration remain outside the mandatory deterministic implementation.

Next release step: commit these evidence/status sources, rebuild/recheck affected
documentation, and verify that successor's own full CI, Windows desktop and Pages
workflows and exact deployed SHA. Per ADR 0002, this report does not pretend to
contain its own future commit hash. The final successor is independently identified
by its CI artifact and public build.json. No completion claim for an untested
successor is inferred from this source audit.

## Historical milestone: HKM-P2 planning correction before final acceptance

The entries below retain their status at the time recorded; pending statements
in this historical ledger do not replace the accepted current phase above.

Enhancement baseline: `eaf35b499e80a5ce31b2ea3a24fbfa010bc67c98`.
Implemented and pushed milestone/current audited source:
`0d8a8dbf72b063f43f7ca80460a7b67c577172e9` (clean when acceptance started).
The HKM-inspired six-tool/six-SKU adaptation is **NOT DONE**. It is a new
implementation/acceptance revision, not a reinterpretation of the prior release.

Full acceptance attempt `20261004T113942` is **FAIL**: the first mandatory run
completed 619 tests, with 617 passing and two failing; coverage was 91.17%.
The SKU-B repeated-planning test exceeded observation freshness under coverage;
the six-product API test also returned FAILED rather than COMPLETED. Investigation
identified repeated whole-catalogue deep copies inside rack collision preflight.
The unchanged second run was interrupted to fix that production cost. Original
JUnit, coverage, gate log and manifest remain intact; `interrupted.json` records
which gates were not completed. No timeout, freshness or coverage threshold is
being relaxed. The correction must pass a new clean-commit acceptance twice.
Windows desktop and publication workflows passed for `0d8a8db`; these do not
override the local test failure. Public PDFs and 200 internal destinations were
verified against that exact deployed source. A separate evidence-byte audit found
Git line-ending normalization in hashed audit JSON; the original bytes will be
preserved through scoped Git attributes, without rewriting recorded hashes. All
39 archived files match their original bytes; all 15 browser-manifest hashes
match the staged Git blobs.

The production correction now copies only requested catalogue specifications and
reuses fixed rack bounds within one collision preflight. Occupancy and intentional
dock contact are still checked per segment. In the instrumented six-SKU benchmark,
catalogue copies fell from 5,062 to 258; SKU-B planning took 0.150 seconds. Every
selected-tool explanation and full trajectory JSON matches the original run.
The 144 affected regression tests pass, including the previously failing areas;
three new regressions protect copy cost and nested mutation isolation. These are
scoped checks, not a replacement for repeated full acceptance. Evidence is under
`docs/evidence/hkm-planning-performance/`. No deadlines or safety bounds changed.

Implemented: canonical typed six-product/tool catalogue, deterministic selection
with persisted candidate reasons, segmented workspace/collision preflight,
original articulated shared geometry, schema-2 world/tool/observation/plan/command
and quaternion recording contracts, persisted profile settings, and explicit
schema-1 compatibility. The bounded Blender runtime executes tool preparation,
product attachment, transfer and release. Browser replay consumes evaluated
transforms and retains read-only historical delivery playback. Status/tool/evidence
inspectors, camera controls and the six-tool showcase are implemented. The static
snapshot remains inside collapsed Technical details.

Targeted evidence includes 12 actual Blender tests passing together, with all six
preferred tools, six transfers, exact-one-effect lost-ack/restart recovery,
contradictory/fresh reconciliation, corruption defenses and immutable saved-scene
re-export. See [scoped Blender/native evidence](docs/evidence/hkm-blender-local/result.json)
and its preserved failure/fix provenance. These checks do not attest later source
changes. The affected robotics/Brain/contract/E2E regression run passed 112 tests
(`artifacts/hkm-baseline-eaf35b4/robotics-brain-regressions.xml`); 22 targeted
contract/governance/documentation/Brain checks also passed. The Node UI suite now
has 105 passing checks (`artifacts/hkm-ui-tests.log` retains the follow-up run).
Full repeated acceptance is still required.

Final pre-commit checks: 112 schema, legacy-hash, boundary and timeout-diagnostic
tests passed; lint/strict types/security passed. The final camera-framing suite
has 107 passing UI checks (`artifacts/hkm-ui-camera-final.log`). Actual browser
execution completed a six-product delivery, then a separate lost-ack pick moved
through UNKNOWN_OUTCOME, contradictory intervention and fresh-observation
completion without another command. Independent SQLite audits and screenshots
are retained under `docs/evidence/hkm-browser-local/`. A coordinated request/response
tampering regression preserves durable inventory and imports zero effects.
The publication preflight built all reports, diagrams and PDFs successfully.
These remain scoped development checks; the next milestone is a clean-commit
full acceptance run twice, eight Blender demos, then exact-SHA CI/Pages evidence.

The security gate passed with zero dependency advisories and valid vendored
asset hashes; its five existing low-severity subprocess scopes remain explicitly
reviewed. Only the changed demo function's AST fingerprint was refreshed; no new
exception class or reduced threshold was introduced. The formal MUST verdicts,
full-suite count/coverage and final source SHA remain the acceptance runner's
responsibility. Current-SHA CI, publication, public links and final visual review
are still pending.

New decisions: schema-1 serialization omits all absent schema-2 extensions so
original durable payload hashes remain unchanged; fresh worlds persist their
execution settings, while archived worlds retain their original profile. API
serialization schemas must remain typed and reject unknown fields. Tool geometry
and static-obstacle bounds share the same procedural definition; fork/pouch
fixtures use visible support skids where the tool needs clearance. These are
original simulator-design choices, not manufacturer geometry or capabilities.

Baseline `uv run --locked python -m tools.dev acceptance --local` ran the mandatory
suite twice without modifying source: 389 tests each, 388 passed and one failed
in each run, zero skips; coverage 89.11000552791597%. The failure is the obsolete
`Latest Blender artifact` label assertion in
`test_metrics_timeline_and_dashboard_survive_restart`, after the approved compact
snapshot presentation changed that label. The current revision corrects that assertion with meaningful collapsed-details
coverage while preserving the journal/metrics/restart assertions. The original
failed baseline evidence remains archived unchanged.
All 101 Node UI checks, setup, lint, typecheck, security, seven actual Blender
demos, drift and both local publication builds passed. Lost-ack/restart demos
each retained one transfer; contradictory reconciliation remained intervention.
Environment: Python 3.13.15, Blender 5.2.1 LTS, Node 20.17.0, uv 0.12.13.

Baseline MUST PASS: SC-TEST-004, SC-TEST-005, SC-TEST-006, SC-KB-009,
SC-ACC-005, SC-DOC-003, SC-DOC-004 and SC-DOC-005. Other baseline criteria
fail their shared full-suite/repeatability gates or lack current-SHA remote
evidence; this does not mean 77 distinct behavior failures. The original 85 MUSTs
remain unchanged. HKM-VIS-MUST-001 through HKM-VIS-MUST-025 are in progress,
with FAIL/pending acceptance until their implementation and inspectable evidence
exist. Optional provider fallback remains the documented SC-BRAIN-005 SHOULD gap.

Evidence: [clean baseline manifest](docs/evidence/acceptance/20261004T000708/manifest.json),
[summary](docs/evidence/hkm-baseline-eaf35b4/baseline-result.json) and
[immutable report/provenance archive](docs/evidence/hkm-baseline-eaf35b4/provenance.json).
Old acceptance files were not overwritten; exact before/baseline reports are
retained as text archives with hashes. No saved user test or active app was touched.

Decisions: extend the bounded adapter and shared procedural scene; make the
TCP-driven visual kinematics explicit; persist tool preparation under the original
pick identity; retain product-transfer effect counts and observation-only
verification. Version new recordings/contracts explicitly and preserve old scene,
payload/journal and replay interpretations. No imported HKM CAD or guessed true
robot/controller geometry. [ADR 0010](docs/adr/0010-hkm-inspired-versioned-cell.md)
records the accepted design; [implementation scope](docs/implementation/hkm-inspired.md)
describes implemented runtime features with scoped evidence while retaining
pending final acceptance.

Drift detected: unconditional DONE referred to the previous audited release, and
the UI follow-up left an old wording assertion. Synchronized plan, success criteria,
handoff, checklist, README, report status blocks, publication status/policy,
acceptance map/report, new ADR/design guide and criterion/status tooling. New
criterion IDs are included in drift and completion checks; status dates now use
UTC rather than a fixed past date. Research provenance and generated catalogue/
diagram synchronization remain part of the implementation milestones. Generated
Pages/PDFs must be rebuilt after the coherent source milestone, never hand-edited.

Governance follow-up: nine targeted tests, scoped Ruff lint/format and strict
drift pass; all 85 original MUST definitions are byte-equivalent as text to the
base definitions. Negative tests reject unknown/missing HKM criteria and prevent
DONE with even one new criterion failing. [Scoped evidence](docs/evidence/hkm-governance/result.json)
does not attest runtime enhancement completion. Pending test names in the
acceptance map must be replaced/refined against implemented tests and artifacts.

Next milestone: complete final browser review, run the complete clean mandatory suite twice and
all eight Blender demos, then regenerate acceptance and publication. Verify the
exact final commit in CI/Pages; do not promote scoped results to final acceptance.

Final source synchronization replaces stale planned-feature descriptions with
implemented HKM geometry, six-tool selection/preparation, schema-2 contracts and
read-only replay, without changing generated status blocks or formal acceptance
verdicts. Updated README, plan, handoff, checklist, runtime/contracts/persistence/
operations/acceptance documentation and design/scope reports. Historical baseline
and failure evidence remain unchanged. The host and fixed Blender source-contact
checks now share the 5 mm simulator centering bound; the coordinated 1 mm noise
probe completed in actual Blender and targeted runtime checks passed. That bound
is separate from verifier pose tolerance and is not real gripper accuracy.

API/default-profile follow-up: fresh API/desktop worlds and Start new test now use
the six-SKU HKM profile; reopened originals and archives keep their own saved
settings. Fixture metadata supplies every product's source and the actual
destination plus the canonical catalogue. New intake rejects invalid fixture
identities before creating jobs while retaining replay/conflict semantics.
Targeted checks passed: 11 API/profile regressions and 102 scenario/history/desktop
backend checks, scoped Ruff/mypy and strict drift. Six HTTP orders selected all
six preferred tools with one transfer each. Legacy and fresh desktop backends
both preserved original command identity and one effect after close/reopen.
[Scoped evidence](docs/evidence/hkm-api/result.json) records commands and exclusions;
these checks do not replace actual Blender/native-window/final acceptance checks.
Synchronized README, plan, handoff and contracts/operations/desktop/adaptation
guides. The desktop smoke script now derives SKU/source IDs from the fixture.

Actual Blender follow-up: all 12 tests in `tests/blender/test_hkm_runtime.py`
pass in one run (124.38 s, no skips/xfails). Six SKUs use six preferred tools and
produce six transfers, one per original command. Every sampled carrying/rack
pose is checked within 1e-6; link rotations, tool exchange, attachment/release,
final checkpoint poses, actual camera metadata and A-F labels are inspected.
Lost-ack/restart/contradiction and later reconciliation preserve one command/effect.
Saved-scene re-export preserves transforms and leaves world/journal/timeline and
the original scene hash unchanged. Eight malformed requests fail in actual Blender
before scene/motion/effect creation. An initial floating-point rack residual and
a later strict dock-pose comparison regression were fixed in production; neither
assertion nor tolerance was weakened. Both failures remain archived alongside
the passing suite in [scoped evidence](docs/evidence/hkm-blender-local/result.json).
The native host rebuilt without installation; its isolated Blender lifecycle
smoke passed eight checks, including graceful in-flight close, lost-ack recovery
and forced owned-process-tree cleanup. No active user app/data was touched.
Runtime/adaptation documentation now distinguishes legacy Cartesian evidence from
schema-2 articulated transforms, tools, cameras and original synthetic open totes.
Full repeated acceptance and final source-SHA publication gates remain pending.

## Previous phase: P7 compact snapshot presentation follow-up
Base: `5db9bf973026fd111adc97885cfb1080060a25c5` (published and verified).
The saved Blender snapshot is now under **Technical details**, collapsed by
default. The full 3D cell/replay stays primary. This is a native HTML disclosure;
snapshot generation, API, workflow, verification and saved user data are unchanged.
All 101 existing UI checks pass. An isolated real-Blender happy path confirms the
image loads without opening the disclosure; keyboard expansion/collapse and
390 px layout pass. The order completes with exactly one effect.
[Scoped evidence](docs/evidence/technical-details-local.json) retains the checks
and screenshots. README, operations/playback guides and the acceptance report
describe the new placement. Architecture, contracts, diagrams and research claims
do not change. The release evidence below remains its own audited snapshot.
Documentation checks are recorded with the scoped evidence. Next: user testing of
the compact disclosure; the earlier release gates retain their original scope.

## Previous verified release: P7 guided simulation workspace
Audited source: `59ace317d949cc8e6fbd77db13a10656737d9238`, clean checkout.
The user's publication authorization supersedes the earlier local-only scope.
All 85 MUST criteria PASS with inspectable evidence from GitHub CI and Pages.
389 mandatory tests pass twice without skips/xfails; all 101 UI checks pass in
each suite. Coverage is 89.22%, above the unchanged 85% floor. Setup, security,
lint/format, types, seven real Blender demos, drift and publication pass.
Windows native launch/duplicate launch/close/restart checks also pass.
Lost acknowledgement after effect and restart retain exactly one pick;
ambiguous evidence does not fabricate success.

Evidence: [audited manifest](docs/evidence/acceptance/20261003T220839/manifest.json),
[release provenance](docs/evidence/workspace-release.json) and ACCEPTANCE_REPORT.md.
The original local CI manifest is preserved; remote refresh adds same-source
workflow and public-link evidence without relabelling any test result.
SHOULD SC-BRAIN-005 remains unimplemented (optional model-provider fallback).
The OPTIONAL model/hardware/real-ERP backlog remains non-blocking.

Drift detected: the current status still described unpublished local work.
Synchronized README, reports, publication status/policy, checklist, progress and
acceptance report with verified release evidence. The earlier local-only records
below remain historical. Source provenance, contracts and architecture diagrams
are unchanged by this evidence-only closure. Publication is rebuilt from sources.
Next: push the evidence/status successor and verify its own CI, Windows workflow
and public build.json, as required by ADR 0002. The final successor is attested by
its CI artifact and deployed manifest rather than by changing an earlier report's SHA.

## Previous verified extension: P7 scenario and observation explanations
The local follow-up replaces outcome-only help with definitions, failure stage,
key differences and expandable comparisons for every visible execution scenario
and observation mode. The UI explains new-order injection versus later evidence
collection, including similar-looking no-motion and inconclusive outcomes.
Base: 348c786710a0e22f0dd7de0744eac7057da13ad8; no commit, push or deployment.
Production workflow, faults, contracts and verification rules are unchanged.
SC-DEMO-003 follow-up: all 101 UI checks and 170 affected Python tests pass.
The isolated browser exercised all 10 execution and 5 observation selections,
compared every option and verified the desktop and 390 px layouts. Browsing help
preserved identical UNKNOWN_OUTCOME evidence, one order and one pick effect;
only an explicit normal reconciliation completed the original command.
Lint/format, strict type checks, drift scan and local publication pass. Evidence and all executed commands are
in [the scoped local record](docs/evidence/scenario-help-local.json).
The full acceptance run below remains the prior baseline, not a new whole-system
attestation. Knowledge-base synchronization covers README, report status blocks,
PROJECT_PLAN, publication status, operator/desktop/acceptance guides, the new
scenario guide, ADR 0009, acceptance mapping/report and checklist. Architecture,
diagrams, external source provenance and contracts require no change because
this follow-up only describes the existing behavior.
Next: user testing of the explained choices; remote MUSTs remain deferred under
the local-only scope. No user test data was read or changed in this follow-up.

## Previous verified extension: P7 guided dark workspace
The dark workspace provides a persistent next-step guide, scenario expectations
and readable original-command evidence beside explicit re-observation. Attention
opens and focuses review once; polling and repeat assessments retain focus.
Resolved, stopped-cell, depleted-delivery and archived states have explicit next
actions. ADR 0009 preserves the unchanged verifier, command identity, quarantine
and ground-truth boundaries. No new dependency or domain transition was introduced.
Base: 348c786710a0e22f0dd7de0744eac7057da13ad8; no commit, push or deployment.

Local acceptance: 389 tests PASS twice, zero skips/xfails, 89.33% coverage.
All 99 UI checks, setup, security, lint/format, strict types, seven real Blender
demos, drift and local publication PASS. Evidence:
`docs/evidence/acceptance/20261003T205102` and `ACCEPTANCE_REPORT.md`.
SC-DEMO-003 is explicitly extended with guide, action and confined-asset evidence.
All local MUST gates pass; SC-DATA-005, SC-KB-006/007/008 remain unverified for
these uncommitted changes under local-only scope. SHOULD SC-BRAIN-005 remains
unimplemented; optional backlog is unchanged. This is not a new DONE attestation.

[Browser/native evidence](docs/evidence/guided-workflow-local.json): real Blender
happy path; lost acknowledgement after effect; contradictory/low-confidence
reviews followed by normal evidence on the same command; continued three-product
delivery with one effect and 100 original frames per product; lost acknowledgement
before effect followed by missing/normal evidence (FAILED, zero effects); logical
stop/cell-fault reset; planning timeout/invalid output; stale evidence archived
unchanged and reviewed read-only. Inspecting evidence and choosing normal
observation left the original records identical. Desktop and 390 px layout/focus
were inspected with no horizontal overflow. Native isolated headless lifecycle
checks and all new asset requests pass. The user's open session, all 54 orders,
every assessment, fixture and delivery remain unchanged. Its UNKNOWN_OUTCOME job
was not reconciled or restarted; the new version loads on the next app reopen.

Initial targeted failures were permissions on a pre-existing Windows pytest temp
folder, resolved using a fresh local fixture root. A history-selection regression
was fixed by capturing the selected test before disabling controls. No assertion,
mandatory test or acceptance threshold was weakened.

Drift corrected: scattered-control instructions, stale UI labels and status counts.
Synchronized README, operations, desktop, playback, contracts, reconciliation,
acceptance guide/map/generator/report, PROJECT_PLAN, checklist, PUBLICATION,
report/status sources, architecture caption, generated OpenAPI, ADR 0009 and this
record. Research provenance and domain state diagrams are unchanged. Final
source-document checks/publication and application/test hash equality are recorded
in the linked evidence. Generated pages/PDFs use only the repository builder.
Next: reopen the local app once and follow Next step. Remote CI/Pages verification
remains deferred under the local-only instruction; no Git actions are pending here.

## Previous verified extension: P7 same-test re-observation
An active REQUIRES_INTERVENTION job now accepts an explicit fresh observation
through RECONCILING. It retains the original command, every assessment and the
same delivery. The unchanged verifier either resolves the outcome or pauses it
again. No new pick, fixture reset or automatic restart resolution occurs.
Base: 348c786710a0e22f0dd7de0744eac7057da13ad8; no commit, push or deployment.

Local acceptance: 389 tests PASS twice, zero skips/xfails, 89.31% coverage.
All 77 UI checks, setup, security, lint/format, strict types, seven real Blender
demos, drift and local publication PASS. Evidence:
`docs/evidence/acceptance/20261003T194506` and `ACCEPTANCE_REPORT.md`.
SC-STATE-001/003/004, SC-REC-002/004/005/007 and SC-DEMO-003 are revalidated.
All local MUST gates pass; SC-DATA-005, SC-KB-006, SC-KB-007 and SC-KB-008
remain unverified for these uncommitted changes under the local-only instruction.
This is not a new published DONE attestation. Optional backlog is unchanged.

ADR 0008 records the evidence-only return from intervention. Only COMPLETED and
FAILED remain terminal; intervention requires an explicit reconciliation claim
and stays paused across restart. Fencing and quarantine still prevent concurrent
work or blind retries. Evidence arrays now follow durable insertion order instead
of UUID sorting, preserving a correct latest assessment across repeat attempts.
Tests cover every observation degradation twice, missing journal, both lost-ack
outcomes, restart, archived write rejection, competing claims and continuation of
the same delivery. Gateway dispatch and controller delivery are distinct logged
events for the same single command; assertions check each component once.

[Browser/native evidence](docs/evidence/reobservation-local.json): five degraded
assessments stayed inconclusive, normal fresh evidence completed the original
pick, and blue/green then completed in the same test/delivery. Exactly three
pick effects and three original 100-frame clips remain, one per product.
The native app was gracefully reloaded once. Its current Test 2, all 49 orders,
observations, assessments, fixture and delivery history were verified unchanged.
Its existing intervention now offers Observe again and reconcile; no user job was
reconciled for them. Desktop and 390 px controls, plus diagrams, were inspected.

Knowledge-base drift corrected: intervention as a permanent terminal state,
inspection-only guidance, UUID evidence ordering, stale current-status counts
and the released checklist's remote claims. Synchronized PROJECT_PLAN, checklist,
README, reports/status, PUBLICATION, state/ack-loss diagrams, OpenAPI, contracts,
persistence/reconciliation/operations/desktop/playback guides, ADR 0008, acceptance
mapping/generator/report and this record. External source claims are unchanged.
Publication is rebuilt only through the existing builder. Final documentation-only
checks and application/test hash equality are recorded in the linked evidence.
Next: user continues Test 2 with Fresh observation and Observe again and reconcile.
Local implementation is ready; remote CI/Pages verification awaits authorization.

## Previous verified extension: P7 independent tests in one window
Start new test now provides the same lifecycle for every execution/observation
combination. It retains both choices, creates separate workflow/runtime storage
and archives previous outcomes and replay read-only in the same window. Running
operations finish first. Scenario selection changes configuration only; existing
restock, state-machine, idempotency and observation guards remain intact.
Base: 348c786710a0e22f0dd7de0744eac7057da13ad8; no commit, push or deployment.

Local acceptance: 382 tests PASS twice, zero skips/xfails, 89.14% coverage.
All 69 UI control checks (including 50 combinations), 91 API combinations,
setup, security, lint/format, types, seven Blender demos, drift and publication PASS.
Evidence: docs/evidence/acceptance/20261003T185730, ACCEPTANCE_REPORT.md and
[local browser/desktop evidence](docs/evidence/test-lifecycle-local.json).
All local MUST gates pass. SC-DATA-005, SC-KB-006, SC-KB-007 and SC-KB-008
remain unverified under the
user's local-only instruction; this is not a new published DONE attestation.

ADR 0007 records isolated worlds, durable catalog identity, idempotent creation,
cross-host write serialization, immutable archives and active-only recovery.
Final review caught a recovery-capable journal read in evidence presentation.
Runtime.recorded_journal now reads saved receipts only. Real Blender regressions
prove that viewing a valid pending checkpoint cannot commit it, while explicit
reconciliation still resolves the active test exactly once. The earlier 380-test
attempt predates this correction and was superseded, not used as final evidence.

Browser verification: lost acknowledgement after effect plus contradictory fresh
evidence retained one effect and intervention; before effect retained zero effects
and intervention with the same observation choice. A third test completed all
three products with 300 recorded frames. Earlier evidence/replay stayed identical.
History disabled writes, kept Start new test available and fit a 390 px viewport.
The updated desktop is open in one window. All 49 previous user orders, evidence
and replays were verified unchanged, including the prior separate reconciliation
test copied into history. Its original files remain intact.

Knowledge-base drift corrected: automatic scenario restock, separate-window
workarounds, archive recovery/read semantics and old current-status counts.
Synchronized README, reports/status, PROJECT_PLAN, PUBLICATION, architecture,
API/OpenAPI/schemas, persistence/contracts/runtime/Blender/operations/desktop/
playback/reconciliation guides, ADRs 0006/0007, acceptance mapping/generator/report
and this record. Final status/evidence documentation is rebuilt locally and checked
separately; application and test files remain identical to the two accepted runs.
Next: user review of the permanent Start new test and Test history controls.
No remaining implementation blocker for this local change; remote release awaits
an explicit change to the local-only instruction.

## Previous verified extension: P7 local next-pick guidance
User reported that another product did nothing after a lost acknowledgement.
Read-only inspection found green UNKNOWN_OUTCOME, one durable pick effect and
no second order. The cell quarantine is correct; the UI did not make the next
step prominent. Added a named blocking-product prompt and reconciliation action
beside Run, plus intervention inspection. Existing API/state/verification rules
are unchanged. Local acceptance: 277 tests PASS twice, zero skips/xfails, 87.90% coverage;
18 UI control checks, setup, security, lint/format, type checking, seven Blender
demos, drift and local publication PASS. Evidence is in
`docs/evidence/acceptance/20261003T172709`, `ACCEPTANCE_REPORT.md`, and
`docs/evidence/ack-guidance-local.json`. The same four remote-gate MUSTs remain
unverified because the user requested local changes only.

Actual browser checks with isolated Blender fixtures: green moved once, normal
reconciliation completed its original command without creating another order,
then red ran and entered UNKNOWN_OUTCOME under the same fault. Contradictory
fresh evidence required intervention and kept the next pick blocked. A read-only
check of the user session also showed the named blocking-product prompt.
The user continued testing; no user job was changed or application restarted.
Reopen after the current test to load the updated UI.

Knowledge-base sync: README, reports shared status, operations, desktop, playback,
reconciliation guide, ADR 0006 clarification, acceptance generator/report and
this record. This changes UI guidance only; API, architecture and state-machine
contracts are unchanged. Generated publication rebuilt locally only.
Next: user review. No commit or push requested.

## Previous verified extension: P7 local delivery replay
User confirmed happy path works, then found that changing scenarios left an
exhausted fixture and Replay covered only the last product. Scenario changes now
prepare fresh products through the existing guarded operation. Full delivery is
the default replay scope and includes every original product clip in durable
execution order. Saved deliveries and individual execution details remain
available. Active or uncertain jobs still block preparation and new dispatch.
Base: 348c786710a0e22f0dd7de0744eac7057da13ad8, intentionally uncommitted.

Local acceptance: 277 tests PASS twice, zero skips/xfails, 87.90% coverage.
Setup, security, lint/format, strict typing, all seven Blender demos, drift and
local publication PASS. Evidence: `docs/evidence/acceptance/20261003T132825` and
`ACCEPTANCE_REPORT.md`. The four remote-gate MUSTs remain unverified for this
local change at the user's request; no new published DONE claim is made.

Browser evidence: `docs/evidence/delivery-replay-local.json`. Actual Replay at
2x traversed red, blue and green in the user's saved delivery (300 Blender
frames), and three new UI runs formed another full delivery in an isolated copy.
Changing to logical E-stop restored all three products without creating an
order; running it then produced a rejected command with zero effects. Saved
delivery playback and orders remained unchanged. Fourteen dashboard/playback
control tests also cover exhausted-fixture continuation, legacy individual
selection, partial clips, paused cursors and unresolved-outcome guards.

The actual desktop was gracefully reopened with the new source. All 30 user
orders and the completed scene remain unchanged; the default full replay has
three completed clips. No fixture reset was applied to the user's saved delivery.

ADR 0006 defines scene-epoch grouping as presentation only, with no merged
business orders or new physical commands. Drift corrected: single-product replay
and manual-only scene preparation descriptions. Synchronized README, reports'
shared status, PROJECT_PLAN, architecture caption, API/OpenAPI and schemas,
operations/desktop/playback/contracts guides, acceptance generator/report and
this progress record. Publication is rebuilt locally; public Pages retains the
earlier released source. Final documentation-only checks are recorded in
`docs/evidence/delivery-replay-local.json`.

Next: user review in the open desktop app. No commit or push requested.

## Previous local correction
User requested local changes only: no commit, push or publication. Base remains
348c786710a0e22f0dd7de0744eac7057da13ad8; working source is intentionally dirty.
Reported SOURCE_NOT_OBSERVED reproduced from the user's persisted scene: all
three fixture products were already at destination. Added explicit guarded
fresh-scene preparation, current availability and specific rejection messages.
Source validation and uncertain-outcome rules are unchanged. ADR 0005 records
durable reset identity, exclusive maintenance and crash recovery.

Local verification: 265 tests PASS twice, zero failures/skips/xfails, 87.83%
coverage; setup, lint/format, strict typing, security, all seven Blender demos,
drift and local publication builds PASS. Evidence is in
`docs/evidence/acceptance/20261003T123412` and `ACCEPTANCE_REPORT.md`.
Four MUSTs involving remote gates are unverified for this local change by user request;
this is a verified local correction, not a new published DONE attestation.

Browser evidence: `docs/evidence/happy-path-local.json` and screenshots under
`artifacts/happy-path-fix`. A copy of the depleted user scene completed all three
products through actual UI buttons, streamed approach/lift/transfer/detach poses,
then completed another red pick after fresh-scene preparation. Saved replays,
old-command suppression, restart and reset/intake races have regression coverage.
The actual desktop was gracefully reloaded and prepared with all three products
at source; its 27 previous orders remain byte-for-byte unchanged through the API.

Knowledge-base sync: README, reports' shared status, PROJECT_PLAN, runtime/API,
operations, playback and desktop guides, architecture caption, OpenAPI, ADR 0005,
acceptance generator/report and this record. A stale runtime implementation
future-tense sentence was also corrected. Generated publication was rebuilt
locally only. Public Pages still represents the earlier released source.

Next: user tests Happy path in the open local app. Repeating a picked product
uses Start fresh scene; no Git commit/push until requested.

## Previous released phase
P5/P7 extension complete: full 3D cell, moving machine/product poses and scenario
replay for every execution outcome. All 85 MUSTs pass for the audited clean
source with local and exact-SHA remote evidence. Final evidence/status successors
receive fresh CI artifacts and public build.json attestation (ADR 0002).

## MUST status
Both clean suites: 254 PASS, zero skips/xfails, 87.35% coverage (85% minimum).
Setup, lint/format, strict typing, Python/npm security, seven real Blender demos,
drift scan and publication pass. Exact-source workflows: core 37120767979,
Windows 37120767929 and publication 37120767978 all SUCCESS. Public Pages exposes
the matching source SHA, 22 references and seven synchronized diagrams.
SHOULD SC-BRAIN-005 remains non-blocking; optional model/hardware work is unchanged.

## Evidence
- docs/evidence/acceptance/20261003T114649: clean manifest, two complete suites,
  all gate logs/demos and verified remote status; ACCEPTANCE_REPORT.md maps all
  85 MUSTs to inspectable evidence and names the tested source.
- docs/evidence/3d-scenarios.json and 3d-{webgl,software,mobile}.png: actual browser
  rendering, fixed/no-effect scenes, replay/scrub, mobile layout and exactly-one
  pick despite ambiguous reconciliation.
- docs/evidence/3d-desktop.json: all eight native/real-Blender lifecycle checks,
  including normal close during a pick and termination of owned children on crash.
- Tests cover the complete fault matrix, saved scenes after later orders/restart,
  every carrying-frame offset, partial/corrupt recordings, read-only legacy import,
  no replay dispatch, offline asset integrity and Windows sharing-lock retries.
- One development run exposed a transient Windows reader/rename race (fixed).
  Another encountered an eleven-hour host pause and failed existing deadlines;
  that result was rejected and rerun without weakening runtime timeouts/assertions.

## Decisions / ADRs
ADR 0004 extends ADR 0003: presentation snapshots and audit-event playback,
shared stylized gantry geometry, offline Three.js with software perspective
fallback, and explicit legacy-reference provenance. No presentation data enters
Brain, ObservationModel or Verifier. No state-machine or MUST changes.
Native drain budgets now match the existing 60-second runtime deadline: 65 s
server, 70 s owner, 75 s test observation. Measured valid paced picks exceeded the
old 15-second drain; completion/effect assertions are retained. Idle shutdown is
prompt. Rendering redraws only changed poses/camera/size.
The updated versioned EXE is installed and the desktop shortcut points to it.
An open older app and all user data remain untouched; close/reopen the shortcut.

## Knowledge-base synchronization
Drift found and corrected: motion-only/Canvas-only descriptions, missing static
scenario history, persistence future tense, damaged Swedish characters and the
old native drain/install descriptions. Synchronized README, PROJECT_PLAN,
PUBLICATION, report 01 and the shared status in reports 01-03, registry S22,
architecture, schemas/OpenAPI, all affected
implementation guides, scene README, ADRs 0003/0004, acceptance map/generator and
this record. Publication is generated only from source; 181 PDF destinations
validate. Existing external company claims retain their original provenance.

## Release evidence
The committed report attests its audited source, not its own future commit hash.
The final evidence successor must have all three workflows green and matching
Pages build.json before delivery. Optional model/hardware integration remains
explicitly non-blocking. No unresolved implementation or knowledge-base drift
remains; final exact-SHA CI artifacts are the release attestation.
