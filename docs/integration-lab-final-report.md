# Integration Lab completion evidence: audited C 76e6abe

Integration Lab is verified at audited source 76e6abe: two clean 831-case Linux suites, all 169 MUST criteria, Windows native checks and exact-source publication/Pages verification. Five fresh Blender/manual scenarios remain attributed to unchanged runtime source 9e83fe7. This evidence/status revision requires its own exact-SHA CI, Windows and deployed-build attestation under ADR 0002.

Audited candidate C is `76e6abef95155b09484da9a226612d774ceb493d`. The complete Linux, Windows native and publication/Pages results linked here attest C. Original manual/Blender evidence remains source A `9e83fe7d41a52a63ba65b77730e392dafca8fffe`; source P's Windows checkout failure and C's isolated checkout correction remain preserved. This status/evidence successor R must pass its own complete workflows before the final goal declaration. Its independent CI artifact and deployed build.json supply R's identity without a self-hash commit loop. No result is relabeled as R execution.

[Exact C acceptance](evidence/acceptance/20261006T201300/manifest.json) | [CI review](evidence/lab-76e6abe/ci/review/linux-artifact-review.json) | [Windows review](evidence/lab-76e6abe/windows/review.json) | [Publication review](evidence/lab-76e6abe/publication/review.json) | [Runtime identity](evidence/lab-76e6abe/source-relation.json) | [Payload review](evidence/lab-76e6abe/payload-review.json)

C has two clean 831-case suites (1079.192/991.936s JUnit), coverage 91.36194029850746/91.36194029850746%, all 20 local gates and all three remote gates. The Windows review attests native headless ownership/recovery; the fresh Blender manual evidence remains A. Optional SC-BRAIN-005 remains a documented SHOULD limitation. No mandatory requirement is waived.

The detailed local evidence and historical catalogs below preserve source A's original bytes, IDs and counts. Their historical preparation/pending statements describe that freeze; the current C closure above and updated 51/14 ledger govern current status. P was not accepted because Windows checkout failed; C fixed only that workflow environment. R's own checks remain a final release obligation.

## Retained source-A terminal local acceptance

[Independent terminal review](../docs/evidence/lab-9e83fe7/reviews/local-acceptance-independent-review.json): 173 checks, 51 bound inputs, including actual original demo effects and build metadata. [Upstream receipt](../docs/evidence/lab-9e83fe7/reviews/local-acceptance-review.json):20 local gates. These reports preserve original source, environment, command, UTC/exit/duration, fixture/JUnit/coverage and artifact identities. This update reparses both JUnits and exact N77 locators; it does not rerun tests or reproduce the larger payload examination.

| Complete suite | Suite 1 | Suite 2 |
| --- | --- | --- |
| Actual unique cases / passes | 815 / 815 | 815 / 815 |
| Failures / errors / skips | 0 / 0 / 0 | 0 / 0 / 0 |
| JUnit seconds | 1649.757 | 1675.043 |
| Console seconds | 1649.78 | 1675.07 |
| Wrapper seconds | 1651.2559275999956 | 1677.8736543999985 |
| Covered / statements | 4898 / 5360 | 4901 / 5360 |
| Coverage | 91.38059701492537% | 91.43656716417911% |
| JUnit | [tests-1.xml](../docs/evidence/acceptance/20261006T024719/tests-1.xml) | [tests-2.xml](../docs/evidence/acceptance/20261006T024719/tests-2.xml) |
| Coverage | [coverage-1.json](../docs/evidence/acceptance/20261006T024719/coverage-1.json) | [coverage-2.json](../docs/evidence/acceptance/20261006T024719/coverage-2.json) |


| Direct terminal input | SHA256 |
| --- | --- |
| `artifacts/acceptance-response-sync-exit.json` | `9dbc305aaf738927a5a62065c1fd11a3dea549f8b099929f82b1b260743b00b9` |
| `docs/evidence/acceptance/20261006T024719/manifest.json` | `caf31b7306a13007432bf86f63eb8b92b88ef8a738a407e8ec7827cc36ce9bca` |
| `docs/evidence/acceptance/20261006T024719/tests-1.xml` | `7899f43724ec15a2ec4fa7be612fd7eb95c60e690fbeb3af9dbb6ed5e073e5af` |
| `docs/evidence/acceptance/20261006T024719/tests-2.xml` | `51bfac934f503a91efbbe965fcb1e7d4b34bafb853c47a9a87aaf25a86d23213` |
| `docs/evidence/acceptance/20261006T024719/coverage-1.json` | `6ace26dd946895fd16504886d8761ee7ce9a00ce4246a22b870cebf144d6c317` |
| `docs/evidence/acceptance/20261006T024719/coverage-2.json` | `8acbd04c4c4773e4d61a74f46cd6c6c839c0f0ae3db37cf5a1836b468e684b94` |

Both runs have the same 815 identities/outcomes and different owned fixture directories; [repeatability](../docs/evidence/acceptance/20261006T024719/repeatability.json) passes. Each console retains one existing deprecation warning, not a failure/teardown error. Source-A N77 case entries below include exact successful selectors and each run's actual duration; focused overlaps are not added to either 815 total.

| Local gate | Result | Exit | Seconds | Saved evidence |
| --- | --- | --- | --- | --- |
| `setup` | PASS | 0 | 0.04331219999585301 | [setup.log](../docs/evidence/acceptance/20261006T024719/setup.log) |
| `browser_setup` | PASS | 0 | 0.3898464999801945 | [browser_setup.log](../docs/evidence/acceptance/20261006T024719/browser_setup.log) |
| `blender_version` | PASS | 0 | 0.22596929999417625 | [blender_version.log](../docs/evidence/acceptance/20261006T024719/blender_version.log) |
| `security` | PASS | 0 | 19.600753200007603 | [security.log](../docs/evidence/acceptance/20261006T024719/security.log) |
| `tests_1` | PASS | 0 | 1651.2559275999956 | [tests_1.log](../docs/evidence/acceptance/20261006T024719/tests_1.log) |
| `tests_2` | PASS | 0 | 1677.8736543999985 | [tests_2.log](../docs/evidence/acceptance/20261006T024719/tests_2.log) |
| `repeatability` | PASS | derived | not separately timed | [repeatability.json](../docs/evidence/acceptance/20261006T024719/repeatability.json) |
| `lint` | PASS | 0 | 0.9106053000141401 | [lint.log](../docs/evidence/acceptance/20261006T024719/lint.log) |
| `typecheck` | PASS | 0 | 0.613668099977076 | [typecheck.log](../docs/evidence/acceptance/20261006T024719/typecheck.log) |
| `demo_happy_path` | PASS | 0 | 9.805350599985104 | [demo_happy_path.log](../docs/evidence/acceptance/20261006T024719/demo_happy_path.log) |
| `demo_lost_ack_after_effect` | PASS | 0 | 9.895965499978047 | [demo_lost_ack_after_effect.log](../docs/evidence/acceptance/20261006T024719/demo_lost_ack_after_effect.log) |
| `demo_lost_ack_before_effect` | PASS | 0 | 0.9802420999913011 | [demo_lost_ack_before_effect.log](../docs/evidence/acceptance/20261006T024719/demo_lost_ack_before_effect.log) |
| `demo_ambiguous` | PASS | 0 | 9.997796199982986 | [demo_ambiguous.log](../docs/evidence/acceptance/20261006T024719/demo_ambiguous.log) |
| `demo_restart` | PASS | 0 | 10.101201000012225 | [demo_restart.log](../docs/evidence/acceptance/20261006T024719/demo_restart.log) |
| `demo_logical_estop` | PASS | 0 | 0.9016031000064686 | [demo_logical_estop.log](../docs/evidence/acceptance/20261006T024719/demo_logical_estop.log) |
| `demo_cell_fault` | PASS | 0 | 0.8974745000014082 | [demo_cell_fault.log](../docs/evidence/acceptance/20261006T024719/demo_cell_fault.log) |
| `demo_tool_showcase` | PASS | 0 | 61.41089379999903 | [demo_tool_showcase.log](../docs/evidence/acceptance/20261006T024719/demo_tool_showcase.log) |
| `drift` | PASS | 0 | 1.0607374999963213 | [drift.log](../docs/evidence/acceptance/20261006T024719/drift.log) |
| `publication` | PASS | 0 | 9.731846900016535 | [publication.log](../docs/evidence/acceptance/20261006T024719/publication.log) |
| `publication_final` | PASS | 0 | 8.915850899997167 | [publication_final.log](../docs/evidence/acceptance/20261006T024719/publication_final.log) |

Source-A Windows local configured quality: Ruff/lint passed, **204 files** already formatted; strict typing passed **67 source files**. Configured security passed with raw Bandit exit1 and **five explicitly reviewed findings**, pip/npm audit exit0 and vendor integrity true. [Security receipt](../docs/evidence/acceptance/20261006T024719/security-review.json) retains the fingerprint-bound exceptions; raw Bandit did not report zero findings. Current saved trace/log audit is complete below; proposed public Git/history payload review has a distinct scope.

There are **169 MUSTs plus 4 SHOULDs**: **163 MUSTs locally satisfied**, all 51 LAB automated-map entries PASS, three SHOULDs PASS and optional `SC-BRAIN-005` unsatisfied (`optional_model_fallback`). At the A freeze, six unresolved MUSTs depended on the following remote gates in the automated map; audited C has now satisfied them, as linked above:

| Mandatory criterion unresolved at A freeze | Remote evidence later satisfied at C |
| --- | --- |
| `SC-DATA-005` | `ci` |
| `SC-KB-006` | `publication_remote` |
| `SC-KB-007` | `publication_remote` |
| `SC-KB-008` | `pages`, `publication_remote` |
| `HKM-VIS-MUST-025` | `ci`, `publication_remote`, `pages` |
| `UI-INV-MUST-008` | `ci`, `publication_remote`, `pages` |

The independent terminal reviewer verified these **core local Blender CLI demos** against original journals, verifier outcomes and PICK_EFFECT events:

| Core demo | Initial -> final | Commands | Effects | Duplicate physical picks |
| --- | --- | --- | --- | --- |
| `happy_path` | COMPLETED -> COMPLETED | 1 | 1 | 0 |
| `lost_ack_after_effect` | UNKNOWN_OUTCOME -> COMPLETED | 1 | 1 | 0 |
| `lost_ack_before_effect` | UNKNOWN_OUTCOME -> FAILED | 1 | 0 | 0 |
| `ambiguous` | UNKNOWN_OUTCOME -> REQUIRES_INTERVENTION | 1 | 1 | 0 |
| `restart` | UNKNOWN_OUTCOME -> COMPLETED | 1 | 1 | 0 |
| `logical_estop` | FAILED -> FAILED | 1 | 0 | 0 |
| `cell_fault` | FAILED -> FAILED | 1 | 0 | 0 |
| `tool_showcase` | COMPLETED -> COMPLETED | 6 | 6 | 0 |

The showcase uses six original commands/tools with one effect each. These core demos are distinct from the two guided README CLI commands, which are freshly demonstrated below.

Both source-A native-lab formal reviews bind four cases per pass: happy with Blender; lost ACK/duplicate/WMS with synthetic runtime and actual SQL/AMQP/edge REST/OPC UA/WMS services. Each [pass1](../docs/evidence/lab-9e83fe7/reviews/pass1-case-review-final.json) and [pass2](../docs/evidence/lab-9e83fe7/reviews/pass2-case-review-final.json) review has 164 checks and 35 matching source files. Fault replay is not called Blender animation. [Pass1](../docs/evidence/lab-9e83fe7/reviews/pass1-saved-visual-review.json) and [pass2](../docs/evidence/lab-9e83fe7/reviews/pass2-saved-visual-review.json) images were reviewed before formal suite completion; formal passing status comes from terminal JUnits and finalized reviews, not those earlier observations.

## Source-A fresh manual and CLI evidence

The complete native Blender lab started after terminal acceptance with namespace `0167de6e4ed545029461cc08cac14a11`: PostgreSQL schema `lab_run_0167de6e4ed545029461cc08cac14a11`, queue `robotops.run.0167de6e4ed545029461cc08cac14a11` and a fresh data directory. The [lab report](../docs/evidence/lab-9e83fe7/manual/lab-report.json) records actual API/WMS/edge/PLC PIDs21452/16008/5088/34956 separately from Windows wrapper PIDs. Owner 31548 began at `2026-10-06T03:54:35.9132796Z`. Existing PostgreSQL/RabbitMQ dependencies were retained; clean means a new application namespace, not erased dependency services. No Docker run is claimed.

| Fresh scenario | Session ID | Original command ID | Final result | Saved review |
| --- | --- | --- | --- | --- |
| Browser happy, stage 10 reload, original stage 1 authorization replay | `7267ded4-1a30-541a-8366-7e98ebd04ff5` | `fa1a4534-8790-5ab3-a139-3aa9e482dbac` | stage 22/revision 44, COMPLETED, effect 1 | [102 checks](../docs/evidence/lab-9e83fe7/reviews/happy-manual-saved-review.json) |
| Browser lost ACK after effect | `cc7ede23-88b4-50bb-8612-d48ed7702220` | `fca22767-020b-58a9-8a80-276f5d4a28f4` | UNKNOWN stage 20/revision 38 -> completed22/revision 46; effect 1 | [109 checks](../docs/evidence/lab-9e83fe7/reviews/lost-manual-saved-review.json) |
| Browser duplicate publication | `129b71fb-0abf-51ea-a91f-6ced9e026128` | `7a8d4aa1-5453-5724-a4d1-bc16abf0806c` | stage 22/revision 44, two same-hash deliveries, effect 1 | [91 checks](../docs/evidence/lab-9e83fe7/reviews/duplicate-manual-saved-review.json) |
| README CLI happy | `2bc6d1f4-67bc-538a-b3d9-c6c777f6a7f2` | `3b428a56-2075-5deb-ad93-f3d84469e681` | stage 22/revision 44, exit0, effect 1 | [97-check CLI/stop review](../docs/evidence/lab-9e83fe7/reviews/cli-manual-saved-review.json) |
| README CLI lost ACK after effect | `0ed18134-4bf9-569e-9001-ba2161052826` | `1b4dfbd2-4d33-5b26-a785-f79232b668bf` | stage 22/revision 46, exit0, original reconciliation, effect 1 | [CLI/stop review](../docs/evidence/lab-9e83fe7/reviews/cli-manual-saved-review.json) |

Happy reload at stage 10/revision 18 preserves complete API bytes without auto-advance. Gate journal/effect count is0; explicit stage 15 consent precedes the single stage 16 dispatch. The original Blender recording contains 133 frames / 118 distinct positions. Sixteen timestamped browser samples contain 14 distinct rendered positions; all last-submitted poses equal mesh poses. Current-cursor evaluation can differ from the throttled last-drawn frame and is not presented as simultaneous equality. The same session completes fresh observation, VERIFIED_SUCCESS, WMS HTTP200 and ERP completion.

The completed happy session replays its successful original nonphysical stage 1 authorization using the same request ID/body. HTTP200 leaves full API bytes, revision 44, selected runtime/PLC records, recorded database hashes and effect 1 unchanged. This intentional replay is additional to the original driver POST list; the list is not an exhaustive network capture.

Lost-ACK retains original command/hash and runtime receipt through gate0 -> UNKNOWN effect 1 -> completed effect 1. Runtime database hash is unchanged between unknown/completed snapshots. PLC EXECUTING/sequence 0 is later backfilled with the same BLENDER_PICK_APPLIED receipt at sequence 1. One explicit reconcile uses fresh observation and original identity with `physical_resend=false`. An initial verifier can see destination evidence while workflow uncertainty still requires explicit reconciliation; these are distinct facts.

Duplicate publication sends the same command twice; both AMQP deliveries have `redelivered=false`. This proves duplicate publication, while actual broker redelivery is separately N10. The PLC/runtime retain one original receipt/effect. The WMS brief is a future selection, not a fourth manual browser workflow; actual503/business-only retry passes in both source-A suites.

All six inspector tabs were compared with saved fields. Payload collapse/reopen and pinning old stages preserve identity/revision/POST counts; happy history records 50 current-map checks over all eight groups. Original captions persist across future-selector changes. Root actually viewed 13 manual PNGs in [the visual receipt](../docs/evidence/lab-9e83fe7/reviews/manual-visual-root-review.json). Static images alone do not prove every transient frame or continuous motion.

The exact README commands each ran once with explicit consent:

```sh
uv run --locked python -m tools.integration_demo --scenario happy_path --authorize-robot
uv run --locked python -m tools.integration_demo --scenario lost_ack_after_effect --authorize-robot
```

On 2026-10-06, happy CLI ran 04:09:47.5110084Z-04:10:17.6912263Z; lost CLI ran 04:11:05.0901218Z-04:11:36.3769377Z. Each has an exclusive reserved/start/exit ledger, exit0, empty stderr and original output identical to its copied result. The independent review recomputes canonical payload hashes and matches original runtime/API/PLC receipts. The execution records truthfully show `dirty=true` and the unchanged accepted fingerprint; generated evidence is not called a clean working tree.

The browser closed and the recorded 16-process owned tree stopped at `2026-10-06T04:12:59.7509794Z`: 7 explicitly stopped, 9 already exited, remaining empty. No outside parent/dependency PID is in the actions. [Completion](../docs/evidence/lab-9e83fe7/manual/manual-completion.json) claims no lab-launcher exit0 after forced shutdown. Independent verification derives ancestry from saved records, not a new PID/database query.

## Source-A saved trace and log audit

The [final audit](../docs/evidence/lab-9e83fe7/audit/final-saved-audit-review.json) is **PASS for its explicit saved inventory**, with [execution receipt](../docs/evidence/lab-9e83fe7/audit/final-saved-audit-execution-receipt.json). It covers 540 files/98,275,596 input bytes, eight current formal native-lab browser ZIPs, all 470 manual files and six settled nonempty service/launcher logs. All 2,588 ZIP members were read in full, CRC checked and hashed:276,018,990 uncompressed bytes. There are 1,632 complete-text and 1,488 known-binary hash-only dispositions; no prefix truncation, credential candidates, decode/JSON failures, truth mismatches or changed inputs.

The audit checks 292 unique persisted truth/protocol steps and 369 session states. Main-frame DOM decoding covers 5,436 snapshots,5,428 relevant snapshots grouped into 441 states, 80 passing checks and no decode errors. Eight original scenario bindings, five completed manual/CLI cases and eight inspector captures pass. Evidence_pack executed the prepared scanner/finalizer authored by final_audit; it is not a separately implemented second scanner.

Heuristic text/DOM checks do not guarantee absence of all secrets. Binary images were hashed, not OCR-scanned; actual image/PDF views are separately attributed. Public fixture credentials and redaction markers are distinct from private secrets. The eight-current-trace audit does not cover all historical published Git content.

The separate [A public-payload review](evidence/lab-9e83fe7/public-payload/public-payload-A-review.json) covers 2,359 A paths and 220 superseded distinct blobs across 11 new commits, including full 236 ZIP members, four SQLite fixtures and all 63 historical PDF pages; it reports no unresolved/private-credential finding. The separate [frozen evidence extension](evidence/lab-9e83fe7/public-payload/public-payload-B-evidence-review.json) reviews939 archive/campaign files (133,627,634 bytes), reuses the exact eight ZIP proofs after full byte-hash equality, and extracts text from four new PDFs (128 total pages counting combined plus parts). It reports no unresolved private-credential finding. Its original filename calls this B evidence; it is not an attestation of candidate P or R. Proposed status/report/validator/test additions and final normalized Git-tree binding still require a further explicit check. The complete candidate public payload therefore remains pending.

## Historical source-A PDF and HTML review

Preserved source-A builds identify source 9e83fe7 and **NOT DONE**. [Structural review](../docs/evidence/lab-9e83fe7/publication/review/structural-review.json) binds input bytes and confirms35+13+16=64 combined pages with the same text as the three parts. [Root visual review](../docs/evidence/lab-9e83fe7/publication/review/visual-review.json) actually viewed all 64 pages on eight original-detail contact sheets, plus entire index/governance HTML and design top/integration-diagram viewports. No clipping, overlap, missing glyphs, unloaded images or reported browser errors were found in that scope. Other HTML regions were not individually screenshot-reviewed. The named browser/owned preview were closed; no invented process exit0 is claimed.

[Archive readiness](../docs/evidence/lab-9e83fe7/readiness.json) and [link disposition](../docs/evidence/lab-9e83fe7/publication-link-disposition.json) preserve runtime PASS, the two publication defects and remote-pending status. Archive review subsequently found two functional link defects in A `_site/design.html`: `../docs/integration-lab.md` and `../docs/integration-lab-requirements.md` resolve outside the site/project prefix and their `_site/docs` targets are absent. The pixel/structural receipts remain valid for their stated scope; they are not all-link-functional PASS. The local builder failed to reject these references because validate_links accepted existing repository files outside its publication root. Proposed P also adds an explicit publication-root confinement guard; its focused proof remains separate from A local acceptance. Within report body content, proposed P changes only those two hrefs to absolute GitHub blob/main URLs. Its full scope also includes the publication-root validator guard, five new contract regressions and reviewed status/evidence text. A outputs are preserved, not silently rebuilt or repaired. The saved proposed-render and confinement proof is recorded below. Applying the correction, checking the real repository and reviewing its exact-P build and remote publication remain pending at this report freeze.

This is exact local A review, not remote publication or candidate P. The report author reads and attributes those receipts without claiming another rendering or visual inspection. Changed P status/publication bytes require their own review.

## Historical proposed P publication correction

The [proposed correction receipt](evidence/lab-9e83fe7/publication-link-correction/correction-receipt.json) tests the actual validate_links FunctionDef AST, not a mirrored implementation. The same five test bytes against A produce3 passes and2 expected failures (0.400s JUnit): plain and percent-encoded paths escape the site to existing files. Against the proposed two-line confinement guard, all5 pass (0.252s), with0fail/error/skip; Ruff/format pass. Other cases preserve valid local/download/fragment/external links and reject missing targets/fragments. These are five new focused contract cases, not additional passes inside either A815 suite.

The proposed guard rejects both broken links in the frozen seven-page A site; an exactly-two-href corrected copy passes. A saved actual build_report AST render matches original A design output; a corrected proposed-report render passes local validation. That earlier render binds its recorded report-status bytes, while the final durable status wording receives a separate bounded render receipt. The full corrected repository build, committed candidate identity, candidate-wide checks and remote URL reachability are forthcoming; external URLs are not fetched by the local validator. Root owns application and real-repository checks. Original A runtime, source and publication outputs are preserved.

## All 51 GOAL criteria

Requirement texts and order exactly match GOAL.md. Concrete implementation references and source-A N locators are retained from the inspected map; source mapping is not inferred from test names. The original evidence locators retain their source-A scope. The current C closure above supplies complete acceptance and remote proof; row44 is now verified by actual C CI. The source-A report-link defects and their subsequent P correction are preserved above as history; exact-C publication closure is linked at the top. The retained source-A N77 catalog contains 77 selected unique cases inside each 815-case suite. The older a881 A77 and 4774 J61 catalogs remain secondary historical evidence; their letter labels are not candidate identities. C's complete-suite counts come only from the current canonical manifest/JUnits linked above. Named symbols define the implementation; line numbers are navigation hints.

| ID | Requirement | Concrete implementation and evidence / judgment |
| --- | --- | --- |
| LAB-MUST-001 | Create/Run Order starts guided execution rather than secretly running the full robot workflow. | Implementation: `apps/erp_ui/integration-console.js` (IntegrationConsole.start); `apps/api/guided.py:23` (mount_guided_routes). Retained source-A test locators (both 815-case suites): [N01](#n01), [N02](#n02). The fresh happy browser journey starts a persisted guided session and explicitly authorizes bounded stages; its saved driver uses no legacy /run endpoint. [Manual proof](#source-a-fresh-manual-and-cli-evidence). **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-002 | Each displayed stage maps to actual backend work/state/protocol evidence. | Implementation: `robotops/integration/engine.py:310` (GuidedEngine._execute); `robotops/integration/engine.py:716` (GuidedEngine._advance_reserved). Retained source-A test locators (both 815-case suites): [N01](#n01), [N03](#n03). Current source-profiler assertions verify called file/symbol pairs and excerpts. Fresh journeys retain all 22 stages with IDs, state and protocol results; actual inspector views were matched to saved step data. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-003 | Authorization advances only the intended bounded stage. | Implementation: `robotops/integration/engine.py:710` (GuidedEngine.authorize); `robotops/integration/store.py:159` (IntegrationStore.reserve). Retained source-A test locators (both 815-case suites): [N01](#n01). The current22-boundary test checks revision and no pre-gate journal. Fresh browser/CLI traces record one intended stage per authorization and one stage 16 dispatch per original command. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-004 | Authorizations are idempotent/revision-guarded against double click/replay. | Implementation: `robotops/integration/store.py:159` (IntegrationStore.reserve); `robotops/integration/engine.py:1048` (GuidedEngine.reconcile). Retained source-A test locators (both 815-case suites): [N04](#n04), [N05](#n05). Concurrent replay, stale revision and changed payload tests pass. Fresh happy replays its original nonphysical stage 1 request/body after completion without changing full API bytes, revision 44, selected journals or effect 1. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-005 | No DB transaction remains open while waiting for a human. | Implementation: `robotops/integration/store.py:159` (IntegrationStore.reserve); `robotops/integration/store.py:229` (IntegrationStore.finish); `robotops/integration/engine.py:716` (GuidedEngine._advance_reserved). Retained source-A test locators (both 815-case suites): [N01](#n01), [N04](#n04). Inspected reserve/finish control flow commits before returning the human-waiting boundary. Current tests exercise persisted waiting/reload. This is not a separate timing probe of every live transaction. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-006 | Automatic and guided modes use the same stage handlers. | Implementation: `tools/integration_demo.py:38` (drive); `robotops/workflow/engine.py:174` (Engine.stage_dispatch); `robotops/integration/engine.py:310` (GuidedEngine._execute). Retained source-A test locators (both 815-case suites): [N06](#n06). The two exact README commands use tools.integration_demo.drive through the same guided REST handlers as the browser. Both fresh full-lab CLI sessions complete all 22 stages with matching original runtime/PLC receipts. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-007 | Existing correctness invariants and scenarios remain functional. | Implementation: `robotops/workflow/engine.py:233` (Engine.run); `robotops/workflow/engine.py:299` (Engine._reconcile); `robotops/verification/verifier.py:23` (Verifier.verify). Retained source-A test locators (both 815-case suites): [N07](#n07), [N08](#n08). At source A, both complete 815-case suites and eight core Blender demos pass, including before/after-effect loss, ambiguity, restart, interlocks and six-tool showcase. Historical failed campaigns stay failed. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-008 | WMS-style versioned REST task intake exists with idempotency. | Implementation: `apps/api/guided.py:23` (mount_guided_routes); `robotops/integration/store.py:122` (IntegrationStore.create); `robotops/workflow/store.py:241` (Store.intake). Retained source-A test locators (both 815-case suites): [N04](#n04), [N03](#n03). Versioned intake, stable request IDs, replay/conflict semantics and rejection of legacy bypass pass in current suites. Fresh browser/CLI results retain their original request/order identity. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-009 | Integration-lab persistence uses PostgreSQL or a documented equivalent lab profile. | Implementation: `robotops/lab/postgres.py:99` (PostgreSQLStore.transaction); `robotops/lab/api.py:21` (create_app). Retained source-A test locators (both 815-case suites): [N09](#n09), [N03](#n03). Current repository/network tests use actual PostgreSQL. Fresh manual API health and report bind PostgreSQL and a new schema; separate runtime/PLC SQLite journals are not mislabeled as application PostgreSQL. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-010 | Transactional outbox is real, not a log message. | Implementation: `robotops/workflow/store.py:595` (Store.prepare); `robotops/integration/store.py:318` (IntegrationStore.enqueue); `robotops/lab/transport.py:52` (DeliveryStore.enqueue). Retained source-A test locators (both 815-case suites): [N09](#n09). Store.prepare commits immutable command plus integration_outbox intent; DeliveryStore.enqueue persists pending dispatch before publication. Current tests inspect durable pending delivery/conflict; the mapped test is not falsely described as an injected rollback test. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-011 | RabbitMQ/AMQP path is real in lab mode. | Implementation: `robotops/lab/transport.py:212` (LabBridge.publish); `robotops/lab/transport.py:133` (EdgeAdapter.consume_one). Retained source-A test locators (both 815-case suites): [N10](#n10). Current real-AMQP tests exercise confirms and actual lost-consumer-ACK broker redelivery. Fresh duplicate publication records two deliveries of the same hash and effect 1; redelivered=false is disclosed. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-012 | Publisher confirm and consumer ACK are represented distinctly. | Implementation: `robotops/lab/transport.py:212` (LabBridge.publish); `robotops/lab/transport.py:259` (LabBridge.edge_deliver); `robotops/lab/transport.py:87` (DeliveryStore.inbox). Retained source-A test locators (both 815-case suites): [N10](#n10). Current tests distinguish publisher confirm, consumer_ack_sent=false and later true. Persisted outbox confirmed_at and inbox ack_sent and saved Wire views remain separate. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-013 | Edge adapter persists/handles delivery identity robustly. | Implementation: `robotops/lab/transport.py:133` (EdgeAdapter.consume_one); `robotops/lab/transport.py:87` (DeliveryStore.inbox). Retained source-A test locators (both 815-case suites): [N10](#n10). The lost-consumer-ACK case retains inbox identity before ACK and records deliveries=2. Fresh duplicate publication cannot acquire a second PLC execution claim. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-014 | OPC UA client/server communication is real in lab mode. | Implementation: `robotops/lab/edge.py:71` (EdgeControl.begin); `robotops/lab/edge_rpc.py:17` (EdgeRPC.call); `robotops/lab/opcua.py:179` (OPCClient._call). Retained source-A test locators (both 815-case suites): [N11](#n11), [N12](#n12), [N13](#n13), [N14](#n14). Actual browse/subscriptions/method calls, separate edge PID and DataChangeNotifications pass in both suites and appear in fresh manual evidence. Slow/stalled probes preserve one bounded execution claim. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-015 | Virtual PLC has durable-enough command identity/journal semantics for demonstrated recovery. | Implementation: `robotops/lab/journal.py:150` (PLCJournal.begin); `robotops/lab/journal.py:183` (PLCJournal.result); `robotops/lab/journal.py:215` (PLCJournal.acknowledge). Retained source-A test locators (both 815-case suites): [N15](#n15), [N16](#n16). Actual OPC server restart retains identity/claim; the concurrent acknowledgement regression cannot acknowledge an advanced result. Fresh lost-ACK recovery backfills the same original receipt as PLC sequence 1. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-016 | Same command ID + same payload cannot cause a second physical effect. | Implementation: `robotops/lab/journal.py:150` (PLCJournal.begin); `robotops/cell/runtime.py:293` (SyntheticRuntime._execute). Retained source-A test locators (both 815-case suites): [N10](#n10). Current AMQP/OPC tests reject a second execution callback. Fresh duplicate publication and authorization replay retain original command/hash and effect 1. No exactly-once physical hardware guarantee follows. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-017 | Same command ID + different payload is rejected. | Implementation: `robotops/lab/journal.py:65` (PLCJournal.submit); `robotops/lab/journal.py:183` (PLCJournal.result). Retained source-A test locators (both 815-case suites): [N17](#n17). Changed cell_generation under an existing command ID is rejected as PAYLOAD_CONFLICT. Premature result and mismatched acknowledgement sequence checks pass. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-018 | Console shows What/Wire/Code/State/Why/failure semantics. | Implementation: `apps/erp_ui/integration-console.js` (IntegrationConsole.inspect). Retained source-A test locators (both 815-case suites): [N02](#n02), [N18](#n18), [N38](#n38). Fresh happy/lost/duplicate captures compare all six What/Wire/Code/State/Why/Failure tabs to persisted fields. Payload collapse/reopen preserves POST counts, session identity and revision; decoded saved DOM provides additional checkpoint coverage. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-019 | Protocol and real-vs-simulated badges are accurate. | Implementation: `robotops/integration/engine.py:716` (GuidedEngine._advance_reserved); `apps/erp_ui/integration-console.js` (IntegrationConsole.render). Retained source-A test locators (both 815-case suites): [N03](#n03), [N02](#n02), [N38](#n38), [N39](#n39). The current audit checks 292 persisted truth/protocol steps and eight decoded browser traces with zero mismatches. Root viewed 13 manual PNGs. REAL PROTOCOL refers to actual SQL/AMQP/OPC/REST; robot/controller/sensors/replay remain simulated. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-020 | Source references point to code that actually executes. | Implementation: `robotops/integration/engine.py:716` (GuidedEngine._advance_reserved); `robotops/lab/edge_rpc.py:17` (EdgeRPC.call). Retained source-A test locators (both 815-case suites): [N03](#n03), [N19](#n19), [N20](#n20). Current source profilers match actual executed symbols and bounded excerpts, including the lab OPC connection boundary. Fresh inspector Code values match saved source references; no placeholder source is substituted. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-021 | Payloads are derived from actual execution data and secrets are redacted. | Implementation: `robotops/integration/store.py:27` (sanitize); `robotops/integration/engine.py:716` (GuidedEngine._advance_reserved). Retained source-A test locators (both 815-case suites): [N21](#n21). Nested secret/header/URL redaction tests pass. The complete explicit current trace/log inventory has no credential candidates or truth mismatches. This bounded heuristic review is separate from proposed public Git/history payload review. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-022 | Architecture mini-map follows the current stage. | Implementation: `apps/erp_ui/integration-console.js` (IntegrationConsole.render). Retained source-A test locators (both 815-case suites): [N02](#n02). Fresh happy history has 50 current-map observations across all eight groups. Inspector captures pin older stages while the map stays at the session's current stage; current_stage and selected step remain separate. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-023 | In-progress session survives browser reload. | Implementation: `apps/erp_ui/integration-console.js` (IntegrationConsole.load); `robotops/integration/store.py:102` (IntegrationStore.get). Retained source-A test locators (both 815-case suites): [N02](#n02), [N39](#n39). Fresh happy reload at stage 10/revision 18 preserves entire saved API bytes and does not advance. Current synthetic/Blender/native browser tests separately assert reload/resume. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-024 | Final physical gate precedes robot side effect. | Implementation: `robotops/integration/engine.py:310` (GuidedEngine._execute); `robotops/integration/store.py:159` (IntegrationStore.reserve). Retained source-A test locators (both 815-case suites): [N01](#n01), [N02](#n02). All three fresh browser gates have selected journal/effect 0 before explicit stage 15 consent and effect 1 after stage 16. Gate and non-safety wording were visually reviewed; bypass and absent-consent tests pass. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-025 | 3D viewer runs only after that gate and post-execution flow returns to verification/reconciliation. | Implementation: `apps/erp_ui/integration-console.js` (IntegrationConsole.advance); `apps/erp_ui/playback.js`; `robotops/integration/engine.py:310` (GuidedEngine._execute). Retained source-A test locators (both 815-case suites): [N02](#n02), [N22](#n22), [N38](#n38), [N39](#n39). Pre-gate playback is disabled. Fresh happy original Blender recording has133 frames / 118 positions; 16 samples include14 distinct rendered positions. Submitted poses equal mesh poses; current evaluation is not falsely equated with the throttled last-drawn frame. The same session returns to verification/WMS/ERP completion. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-026 | Read-only viewing/streaming cannot mutate robot/workflow state. | Implementation: `apps/api/guided.py:23` (mount_guided_routes); `robotops/workflow/store.py:112` (Store.readonly_connect); `robotops/lab/postgres.py:106` (PostgreSQLStore.readonly_connect). Retained source-A test locators (both 815-case suites): [N23](#n23), [N24](#n24), [N25](#n25), [N18](#n18), [N37](#n37), [N38](#n38), [N39](#n39). Current GET/WebSocket/deleted-file/lifecycle/payload-expansion tests pass. Fresh inspection, replay and caption intervals preserve full API bytes or recorded identity/revision/POST counts. Read-only actions are not consent. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-027 | ACK-before-effect loss scenario is demonstrated. | Implementation: `robotops/cell/runtime.py:293` (SyntheticRuntime._execute); `robotops/integration/engine.py:1048` (GuidedEngine.reconcile). Retained source-A test locators (both 815-case suites): [N10](#n10). The real-protocol before-effect-loss case retains effect 0 without replacement execution. Current core Blender demo goes UNKNOWN_OUTCOME to verified FAILED with zero effects; trace completion is not called physical success. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-028 | ACK-after-effect loss scenario reaches uncertainty/reconciliation without duplicate physical action. | Implementation: `robotops/cell/runtime.py:293` (SyntheticRuntime._execute); `robotops/workflow/engine.py:299` (Engine._reconcile). Retained source-A test locators (both 815-case suites): [N10](#n10), [N22](#n22). Fresh lost browser and exact README CLI retain original command/hash and effect 1 through uncertainty and explicit reconciliation. Browser runtime-journal hash is unchanged; PLC result is recovered without a new pick. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-029 | Duplicate/redelivery scenario proves effect_count remains one. | Implementation: `robotops/lab/transport.py:133` (EdgeAdapter.consume_one); `robotops/lab/journal.py:150` (PLCJournal.begin); `robotops/cell/runtime.py:293` (SyntheticRuntime._execute). Retained source-A test locators (both 815-case suites): [N10](#n10). Current broker-redelivery/OPC duplicate tests assert one callback/effect. Fresh duplicate publication independently records two same-hash deliveries and one receipt/effect, with redelivered=false. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-030 | OPC UA/network interruption has deterministic documented behavior. | Implementation: `robotops/lab/edge.py:71` (EdgeControl.begin); `robotops/lab/journal.py:150` (PLCJournal.begin); `robotops/integration/engine.py:975` (GuidedEngine._recover_unstarted_dispatch). Retained source-A test locators (both 815-case suites): [N26](#n26), [N27](#n27), [N28](#n28), [N29](#n29), [N30](#n30), [N15](#n15), [N16](#n16), [N13](#n13), [N14](#n14). Broker/OPC failure prevents callback; pre-intent boot change requires fresh checks/consent while post-intent uncertainty remains conservative. Real restart, interrupted-dispatch and bounded probe regressions pass with documented behavior. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-031 | Inconclusive observation can prevent false success. | Implementation: `robotops/verification/verifier.py:23` (Verifier.verify); `robotops/workflow/engine.py:56` (Engine._observe); `robotops/integration/engine.py:1048` (GuidedEngine.reconcile). Retained source-A test locators (both 815-case suites): [N31](#n31). Stale/missing/inconclusive observations do not invent success; the current ambiguous Blender demo stays REQUIRES_INTERVENTION. Fresh recovery uses a newer observation matched to the original journal; before-effect loss is verified failure. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-032 | WMS outage after verified execution retries business reconciliation, not robot motion. | Implementation: `robotops/lab/transport.py:328` (LabBridge.reconcile_business); `robotops/integration/store.py:251` (IntegrationStore.complete_business); `robotops/workflow/store.py:335` (Store._order). Retained source-A test locators (both 815-case suites): [N03](#n03), [N32](#n32), [N33](#n33). Both current native WMS cases get actual HTTP503 after effect 1, then retry business acknowledgement without another dispatch. ERP completion waits for WMS. The fresh WMS brief is a future choice, not a fourth manual browser workflow. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-033 | UNKNOWN_OUTCOME is visible and explainable. | Implementation: `apps/erp_ui/integration-console.js` (IntegrationConsole.render); `robotops/integration/engine.py:1048` (GuidedEngine.reconcile). Retained source-A test locators (both 815-case suites): [N22](#n22). Fresh UNKNOWN_OUTCOME image/DOM blocks ordinary advance and explains original-journal/fresh-observation reconciliation without a new pick. Original command identity persists through recovery. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-034 | Reconciliation queries the original command instead of issuing a fresh pick. | Implementation: `robotops/integration/engine.py:1048` (GuidedEngine.reconcile); `robotops/workflow/engine.py:299` (Engine._reconcile). Retained source-A test locators (both 815-case suites): [N22](#n22). Fresh lost browser/CLI records original_identity_queried=true and physical_resend=false; original runtime/API/PLC receipts match, stage 16 occurs once and recovery calls Engine._reconcile. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-035 | Unit tests cover new state/domain logic. | Implementation: `robotops/integration/models.py`; `robotops/integration/store.py:159` (IntegrationStore.reserve); `robotops/integration/engine.py:710` (GuidedEngine.authorize). Retained source-A test locators (both 815-case suites): [N01](#n01), [N04](#n04), [N37](#n37), [N38](#n38), [N39](#n39). Current assertions cover domain transitions, revision CAS, conflicts and read-only state, partly under tests/integration. Correction cases cover scenario metadata, late response identity and actual HTTP/WebSocket cleanup; directory names alone are not proof. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-036 | Integration tests cover DB/outbox/broker/edge/OPC UA/virtual PLC path. | Implementation: `robotops/lab/postgres.py:88` (PostgreSQLStore); `robotops/lab/transport.py:202` (LabBridge); `robotops/lab/edge.py:56` (EdgeControl); `robotops/lab/opcua.py:20` (VirtualPLC). Retained source-A test locators (both 815-case suites): [N10](#n10), [N03](#n03), [N12](#n12). Actual PostgreSQL/AMQP/edge REST/OPC/PLC cases pass, including four independent-process native browser scenarios in each suite. Eight formal case/source/fixture snapshots are separately reviewed from manual runs. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-037 | Browser E2E test drives a complete guided happy path through authorization -> 3D execution -> verification -> reconciliation. | Implementation: `apps/erp_ui/integration-console.js` (IntegrationConsole.advance); `tools/lab_stack.py:163` (LabStack.start). Retained source-A test locators (both 815-case suites): [N02](#n02), [N12](#n12). The current native happy E2E uses Blender with original frames, displacement and evaluated/rendered pose change after consent, then verification/business completion. Fresh happy browser independently fulfills the manual journey. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-038 | Browser/integration E2E test drives at least ACK-after-effect/UNKNOWN_OUTCOME/reconciliation. | Implementation: `apps/erp_ui/integration-console.js` (IntegrationConsole.reconcile); `robotops/integration/engine.py:1048` (GuidedEngine.reconcile). Retained source-A test locators (both 815-case suites): [N22](#n22), [N12](#n12). Current local synthetic/Blender and native lost-ACK browsers reach uncertainty and reconcile the original command at effect 1. Fresh browser/CLI proof supplies the separate final manual obligation. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-039 | Browser reload/resume is tested. | Implementation: `apps/erp_ui/integration-console.js` (IntegrationConsole.load); `robotops/integration/store.py:102` (IntegrationStore.get). Retained source-A test locators (both 815-case suites): [N02](#n02). Both current suites include reload assertions. Fresh stage 10 API before/after bytes are equal; saved per-job scenario survives reload and stays independent of future selections. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-040 | Double authorization/idempotency is tested. | Implementation: `robotops/integration/store.py:159` (IntegrationStore.reserve); `robotops/integration/engine.py:1048` (GuidedEngine.reconcile). Retained source-A test locators (both 815-case suites): [N04](#n04), [N05](#n05). Current tests cover concurrent authorization, exact replay, stale revision and changed authorization/recovery payload. Fresh original stage 1 replay preserves revision 44, original IDs and effect 1. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-041 | Duplicate AMQP/OPC command does not duplicate physical effect and is asserted. | Implementation: `robotops/lab/transport.py:133` (EdgeAdapter.consume_one); `robotops/lab/journal.py:150` (PLCJournal.begin); `robotops/cell/runtime.py:293` (SyntheticRuntime._execute). Retained source-A test locators (both 815-case suites): [N10](#n10). Current actual-AMQP/OPC tests assert broker redelivery, repeated SubmitJob and denied second callback. Fresh duplicate publication separately preserves effect 1 and durable original result. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-042 | Existing test suite passes. | Implementation: `tools/dev.py`; `pyproject.toml`. Retained source-A test locators (both 815-case suites): [N07](#n07). Both source-A 815-case suites pass with 0 fail/error/skip and equal identities/outcomes. JUnit1649.757/1675.043s; coverage91.38059701492537/91.43656716417911%. Focused overlaps are not added to the totals. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-043 | Lint/type checks pass at repository policy level. | Implementation: `tools/dev.py`; `pyproject.toml`. Retained source-A test locators (both 815-case suites): [N34](#n34). Source-A Windows local lint/format (204 files) and strict mypy (67 files) pass; exact-C gate results are linked above. Configured security includes five explicitly reviewed Bandit findings; pip/npm/vendor checks pass. Drift alone is not treated as lint/type proof. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-044 | CI runs the relevant tests or documents any environment-specific Blender limitation with a deterministic headless substitute. | Implementation: .github/workflows/ci.yml. The linked clean exact-C Linux acceptance has two 831-case passing suites with actual lab services and pinned Blender; independent Windows and publication reviews are linked above. **Criterion: PASS at C.** |
| LAB-MUST-045 | Docker/integration-lab startup has a documented smoke test and health checks. | Implementation: `tools/lab_stack.py:163` (LabStack.start); `tools/lab_stack.py:94` (LabStack.healthy); `tools/lab-services.ps1`; `compose.yaml`. Retained source-A test locators (both 815-case suites): [N03](#n03), [N12](#n12). Fresh native Blender stack creates an isolated schema/queue/data identity and health-probes separate API/WMS/edge/PLC over existing actual PostgreSQL/RabbitMQ. Compose/health recipe is documented; no Docker run is claimed. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-046 | README architecture matches implementation. | Implementation: `README.md`; `docs/integration-lab.md`; `robotops/lab/edge_rpc.py:36` (EdgeRPC.execute). Retained source-A test locators (both 815-case suites): [N34](#n34). README and lab/native guides were reread against implemented boundaries and current evidence: durable guided stages, separate edge-owned OPC and simulated callback are accurate. Audited-C completion and the successor's independent attestation are stated separately. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-047 | Clearly label simulated vs real-protocol components. | Implementation: `README.md`; `docs/integration-lab.md`; `robotops/integration/engine.py:716` (GuidedEngine._advance_reserved). Retained source-A test locators (both 815-case suites): [N34](#n34). Docs and current trace/visual reviews distinguish actual protocols from synthetic systems/robot/sensors. Original scenario captions persist across future-selector changes; historical false captions remain archived failures. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-048 | Document local fast mode and full integration-lab mode. | Implementation: `docs/integration-lab.md`; `docs/integration-lab-native.md`; `robotops/lab/api.py:21` (create_app). Retained source-A test locators (both 815-case suites): [N34](#n34). Reread guides document fast SQLite/in-process mode, full actual-service lab, ports/health and synthetic-event replay versus --runtime blender recording. Windows HTTP Selector 512-socket/no-asyncio-subprocess limits are documented; OPC/Playwright loops are unchanged. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-049 | Document all acknowledgement meanings and uncertainty model. | Implementation: `docs/integration-lab.md`; `robotops/integration/engine.py:310` (GuidedEngine._execute); `robotops/lab/journal.py:215` (PLCJournal.acknowledge). Retained source-A test locators (both 815-case suites): [N34](#n34). The lab guide and current stage 22 summary distinguish HTTP acceptance, commit, publisher confirm, consumer ACK, OPC/PLC acceptance, controller result, verification, WMS ACK and ERP completion. No database transaction claims atomic real mechanical effects. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-050 | Include a reproducible demo script for happy path and lost-ACK recovery. | Implementation: `tools/integration_demo.py:38` (drive); `tools/integration_demo.py:144` (main); `README.md`. Retained source-A test locators (both 815-case suites): [N35](#n35). Both exact README commands ran once with explicit --authorize-robot against the fresh Blender lab. Exit0/empty stderr/raw results/all 22 stages/original matching runtime-PLC effect 1 are reviewed; lost case has one original-identity reconciliation. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |
| LAB-MUST-051 | No claim implies proprietary SICS.AI knowledge, exact HKM1800 behavior, or safety certification. | Implementation: `README.md`; `docs/integration-lab.md`; `robotops/domain/ports.py`. Retained source-A test locators (both 815-case suites): [N36](#n36). Reread docs and actual UI explicitly state independent synthetic scope, HKM-inspired mechanics and non-certified checks. The source-A PDF/selected-HTML review retains those limits and its historical NOT DONE status; exact-C publication evidence is linked above. No proprietary SICS.AI, exact hardware or safety guarantee is asserted. **Criterion: PASS; source-A local proof retained, exact-C acceptance above.** |

## Last failed a881 campaign and C5 response/body synchronization

The [immutable campaign summary](../docs/evidence/lab-a881acf/summary.json) and [original manifest](../docs/evidence/acceptance/20261006T012424/manifest.json) preserve the failed campaign: source `a881acfee55bb56e808882f724a150ad77d05eb6`, fingerprint `cc354a6e622b244619e4766280632822781ae974770122ed3850fe136f90150f`, terminal exit 1 at `2026-10-06T02:21:59.7083624Z`. First JUnit: **815 passes, zero failures/errors/skips, 1649.157 s**, coverage **91.41791044776119%** (4900/5360). Second JUnit: **814 passes, one failure, zero errors/skips, 1642.800 s**, coverage **91.38059701492537%** (4898/5360). Both enumerate 815 unique cases. All eight native lab browser cases passed individually; that does not erase the unrelated second-suite failure or failed repeatability.

The exact failure was `tests.browser.test_investigation::test_clear_retries_same_test_and_delete_starts_again_at_one[viewport0-SyntheticRuntime]`. [Bounded saved trace metadata](../docs/evidence/lab-a881acf/failed-case/diagnosis/trace-timing.json) records clear POST HTTP200 in 4913.785 ms (4913.316 ms waiting), sent about 4.3 ms after confirm. The unchanged five-second dialog assertion expired during the subsequent projection refresh. Original backend latency cause remains unproven; three separate native HTTP probes were fast and did not reproduce it. Those probes are diagnostics, not repository test cases. [Independent synchronization assessment](../docs/evidence/lab-a881acf/response-sync-correction/reviews/synchronization-independent-review.json) distinguishes the documented five-second pre-POST read-drain guard from durable-clear/body completion.

C5 changes [the existing lifecycle browser test](../tests/browser/test_investigation.py) and [ADR 0013](../docs/adr/0013-reusable-test-lifecycle.md): exact POST URL/method response and completed-body synchronization for clear/delete/create; status, identity and cleanup checks; then the existing five-second UI assertions. The page fixture's 20-second bound, four parameterizations, mutation count and product code are unchanged by C5. No test retry or timeout increase is hidden. Corrected test SHA256: `1bde15b45d789adb35b0f55cebc667e2cc06d2ab167dc9dad095fb16cae5f5b5`.

[Correction archive](../docs/evidence/lab-a881acf/response-sync-correction/summary.json), [input hashes](../docs/evidence/lab-a881acf/response-sync-correction/inputs.json), [independent correction review](../docs/evidence/lab-a881acf/response-sync-correction/reviews/correction-independent-review.json) and [root archive review](../docs/evidence/lab-a881acf/response-sync-correction/root-review.json) retain the bounded proof. Focused JUnit: **4 passed, zero failure/error/skip, 122.443 s** (console 122.45 s), exit 0. Every row below has classname `tests.browser.test_investigation` in [the saved JUnit](../docs/evidence/lab-a881acf/response-sync-correction/focused/lifecycle-response-sync.xml).

| Exact existing testcase | JUnit seconds |
| --- | --- |
| `test_clear_retries_same_test_and_delete_starts_again_at_one[viewport0-SyntheticRuntime]` | 17.622 |
| `test_clear_retries_same_test_and_delete_starts_again_at_one[viewport0-BlenderRuntime]` | 46.130 |
| `test_clear_retries_same_test_and_delete_starts_again_at_one[viewport1-SyntheticRuntime]` | 16.736 |
| `test_clear_retries_same_test_and_delete_starts_again_at_one[viewport1-BlenderRuntime]` | 41.438 |

The [controlled diagnostic JUnit](../docs/evidence/lab-a881acf/response-sync-correction/delayed-body/test.xml) repeats only `test_clear_retries_same_test_and_delete_starts_again_at_one[viewport0-SyntheticRuntime]`: one pass, zero failure/error/skip, suite **22.777 s** (console 22.79 s). The ignored plugin delays the final successful clear response body exactly once after actual durable clear, leaves headers normal, requests 5.25 s and records **5.265089099993929 s** actual delay. Setup/call/teardown passed; nine source hashes matched. [Root review](../docs/evidence/lab-a881acf/response-sync-correction/reviews/delayed-body-root-review.json) binds those facts. The initial shell execution-policy block happened before any test; the subsequent process-local invocation is not a mutation retry. The passing run retained a PytestCacheWarning, without a test/teardown error or cache-permission change.

Focused lint/format (203 files), strict typing (67 source files) and drift (169 MUSTs) passed as recorded in the correction archive. Those pre-commit checks and the controlled repeat do not replace current clean-source full gates or count as added unique tests. The correction is now part of 9e83fe7; its earlier receipts keep their actual pre-commit boundaries.

## Older retained evidence and implementation boundaries

Historical [4774 archive](../docs/evidence/lab-4774af5/summary.json) records two complete 799-pass suites (1807.596/1648.556 s; 91.38351792753895/91.43983480382954% coverage), all 20 local gates, three saved browser and two README CLI journeys. The historical full saved-trace and secret-candidate review scanned 198,471,933 text bytes, verified 292 persisted truth/protocol labels, and preserved the duplicate/WMS presentation failures. The historical 64-page PDF review and CLI receipts remain historical; those historical reviews do not attest A; current reviews are recorded separately above. The canonical historical archive retains exact paths and scope limits.

C1-C3 scenario fixes persist recorded scenario metadata per job, use all six supported briefs, and reject stale live-response identities. The earlier 90 Python/160 Node/10 focused browser-protocol receipts are in [scenario-label correction evidence](../docs/evidence/scenario-label-correction/summary.json). Exact successful a881 first-pass regression locators remain A38/A39 below; they do not prove current final manual captions.

C4's [HTTP-loop correction](../docs/evidence/lab-b968586/http-loop-correction/summary.json) follows the failed b968 campaign. `robotops.http_server.new_event_loop` and `UVICORN_LOOP` select Windows Selector only for HTTP; non-Windows retains Uvicorn auto selection. `apps/api/__main__.py`, `apps/desktop/backend.py`, `robotops/lab/__main__.py` and `tools/lab_stack.py` apply the factory to native API/desktop/edge/API-WMS services; `tests/conftest.py` shares it with strict shutdown checks. OPC UA and Playwright loop ownership is unchanged. `tests/integration/test_http_server_lifecycle.py::test_http_server_peer_reset_exits_cleanly` covers HTTP/WebSocket resets and the deterministic shutdown-reset boundary, with zero retained transports and clean shutdown. Scoped results: four lifecycle cases (0.955 s), three desktop cases (15.667 s), four Blender browser cases (223.458 s; six deliberately deselected). Diagnostics reproduced the Proactor detach failure, not the exact original Chromium timing. Windows Selector's 512-socket/no-asyncio-subprocess limits and absence of Linux/optional-uvloop execution proof remain explicit. C5 changed the investigation test afterward; this draft does not claim all old frozen hash snapshots still equal the current tree.

## Retained source-A 9e83fe7 exact successful two-suite JUnit catalog

N01-N36 provide 61 mapped cases and N37-N39 add 16 correction cases. All 77 selected unique cases passed in each complete source-A 815-case suite, not an additional count. Each outcome/identity/duration below was resolved from A's two actual JUnits. Both A suites, repeatability and all 20 A local gates pass. Source-A manual and scoped audit/visual proof are recorded separately above. Exact-C publication/remote closure is linked at the top; R's independent attestation remains required.

N02/N18/N22 are automated local browser cases; N12 is the automated native independent-process lab browser. Other protocol cases may use TestClient/fixture listeners. N38 is one pytest wrapper, not an additive Node count. No entry is final manual work, Compose execution, remote CI, full archive/secret or PDF visual proof.

### N01

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided.py::test_guided_authorization_is_bounded_durable_and_physically_gated`; JUnit times `2.422s` / `3.146s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_guided_authorization_is_bounded_durable_and_physically_gated']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_guided_authorization_is_bounded_durable_and_physically_gated']`.

### N02

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/browser/test_guided_console.py::test_guided_happy_reload_gate_trace_and_business_completion[synthetic]`; JUnit times `19.382s` / `11.504s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_happy_reload_gate_trace_and_business_completion[synthetic]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_happy_reload_gate_trace_and_business_completion[synthetic]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/browser/test_guided_console.py::test_guided_happy_reload_gate_trace_and_business_completion[blender]`; JUnit times `25.691s` / `26.064s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_happy_reload_gate_trace_and_business_completion[blender]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_happy_reload_gate_trace_and_business_completion[blender]']`.

### N03

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_guided_lab.py::test_guided_network_stack_recovers_without_repeating_motion[None]`; JUnit times `19.811s` / `19.729s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_lab'][@name='test_guided_network_stack_recovers_without_repeating_motion[None]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_guided_lab'][@name='test_guided_network_stack_recovers_without_repeating_motion[None]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_guided_lab.py::test_guided_network_stack_recovers_without_repeating_motion[DROP_ACK_AFTER_EFFECT]`; JUnit times `22.850s` / `22.831s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_lab'][@name='test_guided_network_stack_recovers_without_repeating_motion[DROP_ACK_AFTER_EFFECT]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_guided_lab'][@name='test_guided_network_stack_recovers_without_repeating_motion[DROP_ACK_AFTER_EFFECT]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_guided_lab.py::test_guided_network_stack_recovers_without_repeating_motion[DUPLICATE_DELIVERY]`; JUnit times `18.766s` / `18.858s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_lab'][@name='test_guided_network_stack_recovers_without_repeating_motion[DUPLICATE_DELIVERY]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_guided_lab'][@name='test_guided_network_stack_recovers_without_repeating_motion[DUPLICATE_DELIVERY]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_guided_lab.py::test_guided_network_stack_recovers_without_repeating_motion[PLC_RESTART]`; JUnit times `19.733s` / `17.793s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_lab'][@name='test_guided_network_stack_recovers_without_repeating_motion[PLC_RESTART]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_guided_lab'][@name='test_guided_network_stack_recovers_without_repeating_motion[PLC_RESTART]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_guided_lab.py::test_guided_network_stack_recovers_without_repeating_motion[WMS_UNAVAILABLE]`; JUnit times `18.903s` / `19.853s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_lab'][@name='test_guided_network_stack_recovers_without_repeating_motion[WMS_UNAVAILABLE]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_guided_lab'][@name='test_guided_network_stack_recovers_without_repeating_motion[WMS_UNAVAILABLE]']`.

### N04

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided.py::test_revision_guard_and_double_click_are_idempotent`; JUnit times `0.235s` / `0.262s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_revision_guard_and_double_click_are_idempotent']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_revision_guard_and_double_click_are_idempotent']`.

### N05

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_recovery.py::test_reconciliation_idempotency_binds_observation_fault[None]`; JUnit times `2.488s` / `2.669s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_recovery'][@name='test_reconciliation_idempotency_binds_observation_fault[None]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_recovery'][@name='test_reconciliation_idempotency_binds_observation_fault[None]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_recovery.py::test_reconciliation_idempotency_binds_observation_fault[STALE_OBSERVATION]`; JUnit times `2.853s` / `2.371s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_recovery'][@name='test_reconciliation_idempotency_binds_observation_fault[STALE_OBSERVATION]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_recovery'][@name='test_reconciliation_idempotency_binds_observation_fault[STALE_OBSERVATION]']`.

### N06

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_demo_driver.py::test_automatic_driver_requires_explicit_physical_consent_and_resumes_original`; JUnit times `3.153s` / `3.588s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_demo_driver'][@name='test_automatic_driver_requires_explicit_physical_consent_and_resumes_original']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_demo_driver'][@name='test_automatic_driver_requires_explicit_physical_consent_and_resumes_original']`.

### N07

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/e2e/test_workflow.py::test_happy_path`; JUnit times `0.615s` / `0.641s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.e2e.test_workflow'][@name='test_happy_path']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.e2e.test_workflow'][@name='test_happy_path']`.

### N08

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/e2e/test_workflow.py::test_lost_ack_before_effect`; JUnit times `0.667s` / `0.683s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.e2e.test_workflow'][@name='test_lost_ack_before_effect']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.e2e.test_workflow'][@name='test_lost_ack_before_effect']`.

### N09

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_distributed.py::test_postgres_full_repository_intake_and_atomic_outbox`; JUnit times `3.720s` / `4.776s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_distributed'][@name='test_postgres_full_repository_intake_and_atomic_outbox']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_distributed'][@name='test_postgres_full_repository_intake_and_atomic_outbox']`.

### N10

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_distributed.py::test_real_pg_rabbit_edge_opc_duplicate_and_lost_ack[DROP_ACK_BEFORE_EFFECT-0]`; JUnit times `4.637s` / `5.677s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_distributed'][@name='test_real_pg_rabbit_edge_opc_duplicate_and_lost_ack[DROP_ACK_BEFORE_EFFECT-0]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_distributed'][@name='test_real_pg_rabbit_edge_opc_duplicate_and_lost_ack[DROP_ACK_BEFORE_EFFECT-0]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_distributed.py::test_real_pg_rabbit_edge_opc_duplicate_and_lost_ack[DROP_ACK_AFTER_EFFECT-1]`; JUnit times `4.684s` / `4.731s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_distributed'][@name='test_real_pg_rabbit_edge_opc_duplicate_and_lost_ack[DROP_ACK_AFTER_EFFECT-1]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_distributed'][@name='test_real_pg_rabbit_edge_opc_duplicate_and_lost_ack[DROP_ACK_AFTER_EFFECT-1]']`.

### N11

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_plc.py::test_real_opcua_browse_subscription_acceptance_gate_and_result`; JUnit times `2.795s` / `3.158s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_plc'][@name='test_real_opcua_browse_subscription_acceptance_gate_and_result']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_plc'][@name='test_real_opcua_browse_subscription_acceptance_gate_and_result']`.

### N12

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_browser_lab.py::test_full_lab_browser_authorization_recovery_and_business_completion[]`; JUnit times `54.177s` / `51.373s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_browser_lab'][@name='test_full_lab_browser_authorization_recovery_and_business_completion[]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_browser_lab'][@name='test_full_lab_browser_authorization_recovery_and_business_completion[]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_browser_lab.py::test_full_lab_browser_authorization_recovery_and_business_completion[DROP_ACK_AFTER_EFFECT]`; JUnit times `41.033s` / `43.411s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_browser_lab'][@name='test_full_lab_browser_authorization_recovery_and_business_completion[DROP_ACK_AFTER_EFFECT]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_browser_lab'][@name='test_full_lab_browser_authorization_recovery_and_business_completion[DROP_ACK_AFTER_EFFECT]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_browser_lab.py::test_full_lab_browser_authorization_recovery_and_business_completion[DUPLICATE_DELIVERY]`; JUnit times `37.049s` / `38.195s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_browser_lab'][@name='test_full_lab_browser_authorization_recovery_and_business_completion[DUPLICATE_DELIVERY]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_browser_lab'][@name='test_full_lab_browser_authorization_recovery_and_business_completion[DUPLICATE_DELIVERY]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_browser_lab.py::test_full_lab_browser_authorization_recovery_and_business_completion[WMS_UNAVAILABLE]`; JUnit times `38.913s` / `38.029s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_browser_lab'][@name='test_full_lab_browser_authorization_recovery_and_business_completion[WMS_UNAVAILABLE]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_browser_lab'][@name='test_full_lab_browser_authorization_recovery_and_business_completion[WMS_UNAVAILABLE]']`.

### N13

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_opc_health_probe.py::test_slow_real_server_state_probe_preserves_original_execution_session`; JUnit times `8.838s` / `9.741s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_opc_health_probe'][@name='test_slow_real_server_state_probe_preserves_original_execution_session']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_opc_health_probe'][@name='test_slow_real_server_state_probe_preserves_original_execution_session']`.

### N14

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_opc_health_probe.py::test_sustained_real_server_state_delay_is_bounded_without_a_second_execution`; JUnit times `12.804s` / `12.991s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_opc_health_probe'][@name='test_sustained_real_server_state_delay_is_bounded_without_a_second_execution']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_opc_health_probe'][@name='test_sustained_real_server_state_delay_is_bounded_without_a_second_execution']`.

### N15

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_plc_process_restart.py::test_opc_server_process_restart_does_not_regrant_effect`; JUnit times `4.686s` / `4.440s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_plc_process_restart'][@name='test_opc_server_process_restart_does_not_regrant_effect']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_plc_process_restart'][@name='test_opc_server_process_restart_does_not_regrant_effect']`.

### N16

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_plc.py::test_acknowledgement_cannot_mark_a_concurrently_advanced_result`; JUnit times `0.672s` / `8.692s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_plc'][@name='test_acknowledgement_cannot_mark_a_concurrently_advanced_result']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_plc'][@name='test_acknowledgement_cannot_mark_a_concurrently_advanced_result']`.

### N17

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_plc.py::test_journal_rejects_payload_and_result_conflicts`; JUnit times `0.649s` / `0.684s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_plc'][@name='test_journal_rejects_payload_and_result_conflicts']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_plc'][@name='test_journal_rejects_payload_and_result_conflicts']`.

### N18

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/browser/test_guided_console.py::test_guided_retry_delivery_indicators_and_expandable_payload_are_persisted_and_readonly[BROKER_TRANSIENT-synthetic]`; JUnit times `6.236s` / `6.148s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_retry_delivery_indicators_and_expandable_payload_are_persisted_and_readonly[BROKER_TRANSIENT-synthetic]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_retry_delivery_indicators_and_expandable_payload_are_persisted_and_readonly[BROKER_TRANSIENT-synthetic]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/browser/test_guided_console.py::test_guided_retry_delivery_indicators_and_expandable_payload_are_persisted_and_readonly[DUPLICATE_DELIVERY-synthetic]`; JUnit times `5.772s` / `5.586s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_retry_delivery_indicators_and_expandable_payload_are_persisted_and_readonly[DUPLICATE_DELIVERY-synthetic]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_retry_delivery_indicators_and_expandable_payload_are_persisted_and_readonly[DUPLICATE_DELIVERY-synthetic]']`.

### N19

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_business.py::test_every_displayed_source_symbol_actually_executed_and_excerpt_matches_file[None]`; JUnit times `5.899s` / `5.557s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_business'][@name='test_every_displayed_source_symbol_actually_executed_and_excerpt_matches_file[None]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_business'][@name='test_every_displayed_source_symbol_actually_executed_and_excerpt_matches_file[None]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_business.py::test_every_displayed_source_symbol_actually_executed_and_excerpt_matches_file[DROP_ACK_AFTER_EFFECT]`; JUnit times `6.316s` / `6.042s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_business'][@name='test_every_displayed_source_symbol_actually_executed_and_excerpt_matches_file[DROP_ACK_AFTER_EFFECT]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_business'][@name='test_every_displayed_source_symbol_actually_executed_and_excerpt_matches_file[DROP_ACK_AFTER_EFFECT]']`.

### N20

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_source_map.py::test_every_lab_stage_source_symbol_executes_and_excerpt_matches`; JUnit times `15.788s` / `14.786s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_source_map'][@name='test_every_lab_stage_source_symbol_executes_and_excerpt_matches']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_source_map'][@name='test_every_lab_stage_source_symbol_executes_and_excerpt_matches']`.

### N21

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided.py::test_trace_sanitizes_exception_text_headers_and_credentials`; JUnit times `0.233s` / `0.231s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_trace_sanitizes_exception_text_headers_and_credentials']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_trace_sanitizes_exception_text_headers_and_credentials']`.

### N22

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/browser/test_guided_console.py::test_guided_lost_ack_reconciles_original_command_without_second_effect[synthetic]`; JUnit times `11.276s` / `11.230s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_lost_ack_reconciles_original_command_without_second_effect[synthetic]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_lost_ack_reconciles_original_command_without_second_effect[synthetic]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/browser/test_guided_console.py::test_guided_lost_ack_reconciles_original_command_without_second_effect[blender]`; JUnit times `25.535s` / `25.884s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_lost_ack_reconciles_original_command_without_second_effect[blender]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_lost_ack_reconciles_original_command_without_second_effect[blender]']`.

### N23

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided.py::test_readonly_routes_and_stream_do_not_advance`; JUnit times `1.631s` / `1.514s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_readonly_routes_and_stream_do_not_advance']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_readonly_routes_and_stream_do_not_advance']`.

### N24

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_readonly.py::test_deleted_guided_store_reads_do_not_recreate_database[False-get]`; JUnit times `0.081s` / `0.080s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[False-get]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[False-get]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_readonly.py::test_deleted_guided_store_reads_do_not_recreate_database[False-list]`; JUnit times `0.080s` / `0.082s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[False-list]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[False-list]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_readonly.py::test_deleted_guided_store_reads_do_not_recreate_database[False-prior_authorization]`; JUnit times `0.082s` / `0.080s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[False-prior_authorization]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[False-prior_authorization]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_readonly.py::test_deleted_guided_store_reads_do_not_recreate_database[True-get]`; JUnit times `0.131s` / `0.133s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[True-get]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[True-get]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_readonly.py::test_deleted_guided_store_reads_do_not_recreate_database[True-list]`; JUnit times `0.147s` / `0.129s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[True-list]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[True-list]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_readonly.py::test_deleted_guided_store_reads_do_not_recreate_database[True-prior_authorization]`; JUnit times `0.131s` / `0.144s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[True-prior_authorization]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[True-prior_authorization]']`.

### N25

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided.py::test_active_stream_closes_when_world_is_cleared_or_deleted[False-clear-4409]`; JUnit times `0.642s` / `0.636s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_active_stream_closes_when_world_is_cleared_or_deleted[False-clear-4409]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_active_stream_closes_when_world_is_cleared_or_deleted[False-clear-4409]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided.py::test_active_stream_closes_when_world_is_cleared_or_deleted[False-delete-4404]`; JUnit times `0.564s` / `0.570s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_active_stream_closes_when_world_is_cleared_or_deleted[False-delete-4404]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_active_stream_closes_when_world_is_cleared_or_deleted[False-delete-4404]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided.py::test_active_stream_closes_when_world_is_cleared_or_deleted[True-clear-4409]`; JUnit times `1.234s` / `0.898s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_active_stream_closes_when_world_is_cleared_or_deleted[True-clear-4409]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_active_stream_closes_when_world_is_cleared_or_deleted[True-clear-4409]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided.py::test_active_stream_closes_when_world_is_cleared_or_deleted[True-delete-4404]`; JUnit times `0.843s` / `1.188s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_active_stream_closes_when_world_is_cleared_or_deleted[True-delete-4404]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_active_stream_closes_when_world_is_cleared_or_deleted[True-delete-4404]']`.

### N26

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_distributed.py::test_broker_failure_retains_outbox_and_opc_disconnect_never_executes`; JUnit times `8.013s` / `8.081s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_distributed'][@name='test_broker_failure_retains_outbox_and_opc_disconnect_never_executes']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_distributed'][@name='test_broker_failure_retains_outbox_and_opc_disconnect_never_executes']`.

### N27

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_guided_boot_recovery.py::test_boot_change_before_dispatch_rechecks_then_requires_renewed_physical_consent`; JUnit times `11.725s` / `12.748s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_boot_recovery'][@name='test_boot_change_before_dispatch_rechecks_then_requires_renewed_physical_consent']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_guided_boot_recovery'][@name='test_boot_change_before_dispatch_rechecks_then_requires_renewed_physical_consent']`.

### N28

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_guided_boot_recovery.py::test_boot_change_after_dispatch_intent_remains_uncertain_without_repeat`; JUnit times `12.763s` / `11.727s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_boot_recovery'][@name='test_boot_change_after_dispatch_intent_remains_uncertain_without_repeat']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_guided_boot_recovery'][@name='test_boot_change_after_dispatch_intent_remains_uncertain_without_repeat']`.

### N29

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_guided_boot_recovery.py::test_interrupted_unstarted_lab_dispatch_returns_to_preconditions`; JUnit times `11.735s` / `10.694s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_boot_recovery'][@name='test_interrupted_unstarted_lab_dispatch_returns_to_preconditions']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_guided_boot_recovery'][@name='test_interrupted_unstarted_lab_dispatch_returns_to_preconditions']`.

### N30

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_plc.py::test_restart_invalidates_readiness_until_fresh_checks[False]`; JUnit times `0.775s` / `0.654s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_plc'][@name='test_restart_invalidates_readiness_until_fresh_checks[False]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_plc'][@name='test_restart_invalidates_readiness_until_fresh_checks[False]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/lab/test_plc.py::test_restart_invalidates_readiness_until_fresh_checks[True]`; JUnit times `0.644s` / `0.685s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_plc'][@name='test_restart_invalidates_readiness_until_fresh_checks[True]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.lab.test_plc'][@name='test_restart_invalidates_readiness_until_fresh_checks[True]']`.

### N31

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided.py::test_uncertain_run_queries_original_identity_and_never_repeats_effect[DROP_ACK_AFTER_EFFECT-1-COMPLETED]`; JUnit times `2.727s` / `2.622s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_uncertain_run_queries_original_identity_and_never_repeats_effect[DROP_ACK_AFTER_EFFECT-1-COMPLETED]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_uncertain_run_queries_original_identity_and_never_repeats_effect[DROP_ACK_AFTER_EFFECT-1-COMPLETED]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided.py::test_uncertain_run_queries_original_identity_and_never_repeats_effect[DROP_ACK_BEFORE_EFFECT-0-FAILED]`; JUnit times `2.360s` / `2.404s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_uncertain_run_queries_original_identity_and_never_repeats_effect[DROP_ACK_BEFORE_EFFECT-0-FAILED]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_uncertain_run_queries_original_identity_and_never_repeats_effect[DROP_ACK_BEFORE_EFFECT-0-FAILED]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided.py::test_uncertain_run_queries_original_identity_and_never_repeats_effect[STALE_OBSERVATION-1-COMPLETED]`; JUnit times `2.548s` / `2.304s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_uncertain_run_queries_original_identity_and_never_repeats_effect[STALE_OBSERVATION-1-COMPLETED]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_uncertain_run_queries_original_identity_and_never_repeats_effect[STALE_OBSERVATION-1-COMPLETED]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided.py::test_uncertain_run_queries_original_identity_and_never_repeats_effect[MISSING_OBSERVATION-1-COMPLETED]`; JUnit times `2.649s` / `2.821s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_uncertain_run_queries_original_identity_and_never_repeats_effect[MISSING_OBSERVATION-1-COMPLETED]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_uncertain_run_queries_original_identity_and_never_repeats_effect[MISSING_OBSERVATION-1-COMPLETED]']`.

### N32

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_business.py::test_wms_outage_cannot_complete_erp_order_before_business_stage`; JUnit times `2.378s` / `2.766s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_business'][@name='test_wms_outage_cannot_complete_erp_order_before_business_stage']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_business'][@name='test_wms_outage_cannot_complete_erp_order_before_business_stage']`.

### N33

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_business.py::test_erp_completion_requires_durable_acknowledgement_for_every_order_line`; JUnit times `4.578s` / `4.588s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_business'][@name='test_erp_completion_requires_durable_acknowledgement_for_every_order_line']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_business'][@name='test_erp_completion_requires_durable_acknowledgement_for_every_order_line']`.

### N34

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/contract/test_governance.py::test_knowledge_base_links_ids_sources_and_status`; JUnit times `1.603s` / `17.077s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.contract.test_governance'][@name='test_knowledge_base_links_ids_sources_and_status']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.contract.test_governance'][@name='test_knowledge_base_links_ids_sources_and_status']`.

### N35

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_demo_driver.py::test_automatic_lost_ack_demo_queries_original_without_another_pick`; JUnit times `3.841s` / `3.681s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_demo_driver'][@name='test_automatic_lost_ack_demo_queries_original_without_another_pick']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_demo_driver'][@name='test_automatic_lost_ack_demo_queries_original_without_another_pick']`.

### N36

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/contract/test_governance.py::test_domain_boundary_has_no_blender_or_network_dependency`; JUnit times `0.025s` / `0.018s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.contract.test_governance'][@name='test_domain_boundary_has_no_blender_or_network_dependency']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.contract.test_governance'][@name='test_domain_boundary_has_no_blender_or_network_dependency']`.

### N37

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_http_server_lifecycle.py::test_http_server_peer_reset_exits_cleanly[peer-reset-http]`; JUnit times `0.219s` / `0.218s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_http_server_lifecycle'][@name='test_http_server_peer_reset_exits_cleanly[peer-reset-http]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_http_server_lifecycle'][@name='test_http_server_peer_reset_exits_cleanly[peer-reset-http]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_http_server_lifecycle.py::test_http_server_peer_reset_exits_cleanly[peer-reset-websocket]`; JUnit times `0.231s` / `0.222s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_http_server_lifecycle'][@name='test_http_server_peer_reset_exits_cleanly[peer-reset-websocket]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_http_server_lifecycle'][@name='test_http_server_peer_reset_exits_cleanly[peer-reset-websocket]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_http_server_lifecycle.py::test_http_server_peer_reset_exits_cleanly[shutdown-reset-http]`; JUnit times `0.218s` / `0.218s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_http_server_lifecycle'][@name='test_http_server_peer_reset_exits_cleanly[shutdown-reset-http]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_http_server_lifecycle'][@name='test_http_server_peer_reset_exits_cleanly[shutdown-reset-http]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_http_server_lifecycle.py::test_http_server_peer_reset_exits_cleanly[shutdown-reset-websocket]`; JUnit times `0.213s` / `0.214s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_http_server_lifecycle'][@name='test_http_server_peer_reset_exits_cleanly[shutdown-reset-websocket]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_http_server_lifecycle'][@name='test_http_server_peer_reset_exits_cleanly[shutdown-reset-websocket]']`.

### N38

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/unit/test_visualization.py::test_playback_controls_never_dispatch_and_preserve_partial_recording_limits`; JUnit times `1.902s` / `1.818s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.unit.test_visualization'][@name='test_playback_controls_never_dispatch_and_preserve_partial_recording_limits']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.unit.test_visualization'][@name='test_playback_controls_never_dispatch_and_preserve_partial_recording_limits']`.

### N39

- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_playback.py::test_playback_scenario_survives_reload_for_every_line_without_read_effects[None]`; JUnit times `0.672s` / `0.621s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[None]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[None]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_playback.py::test_playback_scenario_survives_reload_for_every_line_without_read_effects[DUPLICATE_DELIVERY]`; JUnit times `0.696s` / `0.606s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[DUPLICATE_DELIVERY]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[DUPLICATE_DELIVERY]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_playback.py::test_playback_scenario_survives_reload_for_every_line_without_read_effects[BROKER_TRANSIENT]`; JUnit times `0.665s` / `0.607s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[BROKER_TRANSIENT]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[BROKER_TRANSIENT]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_playback.py::test_playback_scenario_survives_reload_for_every_line_without_read_effects[EDGE_TRANSIENT]`; JUnit times `0.629s` / `0.593s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[EDGE_TRANSIENT]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[EDGE_TRANSIENT]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_playback.py::test_playback_scenario_survives_reload_for_every_line_without_read_effects[OPC_UA_DISCONNECT]`; JUnit times `0.637s` / `0.854s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[OPC_UA_DISCONNECT]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[OPC_UA_DISCONNECT]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_playback.py::test_playback_scenario_survives_reload_for_every_line_without_read_effects[PLC_RESTART]`; JUnit times `0.721s` / `0.599s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[PLC_RESTART]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[PLC_RESTART]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_playback.py::test_playback_scenario_survives_reload_for_every_line_without_read_effects[WMS_UNAVAILABLE]`; JUnit times `0.629s` / `0.689s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[WMS_UNAVAILABLE]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[WMS_UNAVAILABLE]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_playback.py::test_unavailable_saved_scenario_never_becomes_a_baseline[missing]`; JUnit times `0.544s` / `0.525s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_unavailable_saved_scenario_never_becomes_a_baseline[missing]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_unavailable_saved_scenario_never_becomes_a_baseline[missing]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_playback.py::test_unavailable_saved_scenario_never_becomes_a_baseline[invalid]`; JUnit times `0.518s` / `0.503s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_unavailable_saved_scenario_never_becomes_a_baseline[invalid]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_unavailable_saved_scenario_never_becomes_a_baseline[invalid]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_playback.py::test_unavailable_saved_scenario_never_becomes_a_baseline[different_order]`; JUnit times `0.522s` / `0.513s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_unavailable_saved_scenario_never_becomes_a_baseline[different_order]']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_unavailable_saved_scenario_never_becomes_a_baseline[different_order]']`.
- **PASS (current 9e83fe7 suites 1 and 2)**: `tests/integration/test_guided_playback.py::test_legacy_playback_scenario_read_does_not_create_guided_schema`; JUnit times `0.131s` / `0.134s`.
  - Suite 1: `docs/evidence/acceptance/20261006T024719/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_legacy_playback_scenario_read_does_not_create_guided_schema']`.
  - Suite 2: `docs/evidence/acceptance/20261006T024719/tests-2.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_legacy_playback_scenario_read_does_not_create_guided_schema']`.

## Historical a881acf exact successful first-pass JUnit catalog

All P entries resolve to actual successful testcase elements in `docs/evidence/acceptance/20261006T012424/tests-1.xml` (SHA256 `79f35fba604edffb2df903baac419dbbe7ee990f29caf20f37b0272810b9213e`). A01-A36 contain **61 historical a881 cases** corresponding to mapped historical groups, with the previously parsed historical durations. A37-A39 add **16 historical correction cases**. All **77 unique selected cases are included in the 815-case suite**, not added to it. These locators establish first-pass execution only; all final criteria remain PENDING.

A02/A18/A22 are automated local browser cases; A12 is automated native lab browser evidence. Other protocol tests may use TestClient or fixture listeners rather than every application service in separate processes. No P entry is final manual work, Compose execution or remote CI. A38 is one successful pytest wrapper; individual Node cases are not separately enumerated by this JUnit.

### A01

- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided.py::test_guided_authorization_is_bounded_durable_and_physically_gated`; JUnit time `2.483s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_guided_authorization_is_bounded_durable_and_physically_gated']`.

### A02

- **PASS (historical a881acf suite 1 only)**: `tests/browser/test_guided_console.py::test_guided_happy_reload_gate_trace_and_business_completion[synthetic]`; JUnit time `11.734s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_happy_reload_gate_trace_and_business_completion[synthetic]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/browser/test_guided_console.py::test_guided_happy_reload_gate_trace_and_business_completion[blender]`; JUnit time `26.319s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_happy_reload_gate_trace_and_business_completion[blender]']`.

### A03

- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_guided_lab.py::test_guided_network_stack_recovers_without_repeating_motion[None]`; JUnit time `17.796s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_lab'][@name='test_guided_network_stack_recovers_without_repeating_motion[None]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_guided_lab.py::test_guided_network_stack_recovers_without_repeating_motion[DROP_ACK_AFTER_EFFECT]`; JUnit time `20.978s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_lab'][@name='test_guided_network_stack_recovers_without_repeating_motion[DROP_ACK_AFTER_EFFECT]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_guided_lab.py::test_guided_network_stack_recovers_without_repeating_motion[DUPLICATE_DELIVERY]`; JUnit time `16.791s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_lab'][@name='test_guided_network_stack_recovers_without_repeating_motion[DUPLICATE_DELIVERY]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_guided_lab.py::test_guided_network_stack_recovers_without_repeating_motion[PLC_RESTART]`; JUnit time `18.883s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_lab'][@name='test_guided_network_stack_recovers_without_repeating_motion[PLC_RESTART]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_guided_lab.py::test_guided_network_stack_recovers_without_repeating_motion[WMS_UNAVAILABLE]`; JUnit time `18.816s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_lab'][@name='test_guided_network_stack_recovers_without_repeating_motion[WMS_UNAVAILABLE]']`.

### A04

- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided.py::test_revision_guard_and_double_click_are_idempotent`; JUnit time `0.235s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_revision_guard_and_double_click_are_idempotent']`.

### A05

- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_recovery.py::test_reconciliation_idempotency_binds_observation_fault[None]`; JUnit time `2.860s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_recovery'][@name='test_reconciliation_idempotency_binds_observation_fault[None]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_recovery.py::test_reconciliation_idempotency_binds_observation_fault[STALE_OBSERVATION]`; JUnit time `2.434s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_recovery'][@name='test_reconciliation_idempotency_binds_observation_fault[STALE_OBSERVATION]']`.

### A06

- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_demo_driver.py::test_automatic_driver_requires_explicit_physical_consent_and_resumes_original`; JUnit time `3.572s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_demo_driver'][@name='test_automatic_driver_requires_explicit_physical_consent_and_resumes_original']`.

### A07

- **PASS (historical a881acf suite 1 only)**: `tests/e2e/test_workflow.py::test_happy_path`; JUnit time `0.701s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.e2e.test_workflow'][@name='test_happy_path']`.

### A08

- **PASS (historical a881acf suite 1 only)**: `tests/e2e/test_workflow.py::test_lost_ack_before_effect`; JUnit time `0.661s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.e2e.test_workflow'][@name='test_lost_ack_before_effect']`.

### A09

- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_distributed.py::test_postgres_full_repository_intake_and_atomic_outbox`; JUnit time `5.787s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_distributed'][@name='test_postgres_full_repository_intake_and_atomic_outbox']`.

### A10

- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_distributed.py::test_real_pg_rabbit_edge_opc_duplicate_and_lost_ack[DROP_ACK_BEFORE_EFFECT-0]`; JUnit time `4.586s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_distributed'][@name='test_real_pg_rabbit_edge_opc_duplicate_and_lost_ack[DROP_ACK_BEFORE_EFFECT-0]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_distributed.py::test_real_pg_rabbit_edge_opc_duplicate_and_lost_ack[DROP_ACK_AFTER_EFFECT-1]`; JUnit time `4.672s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_distributed'][@name='test_real_pg_rabbit_edge_opc_duplicate_and_lost_ack[DROP_ACK_AFTER_EFFECT-1]']`.

### A11

- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_plc.py::test_real_opcua_browse_subscription_acceptance_gate_and_result`; JUnit time `3.041s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_plc'][@name='test_real_opcua_browse_subscription_acceptance_gate_and_result']`.

### A12

- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_browser_lab.py::test_full_lab_browser_authorization_recovery_and_business_completion[]`; JUnit time `53.107s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_browser_lab'][@name='test_full_lab_browser_authorization_recovery_and_business_completion[]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_browser_lab.py::test_full_lab_browser_authorization_recovery_and_business_completion[DROP_ACK_AFTER_EFFECT]`; JUnit time `40.978s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_browser_lab'][@name='test_full_lab_browser_authorization_recovery_and_business_completion[DROP_ACK_AFTER_EFFECT]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_browser_lab.py::test_full_lab_browser_authorization_recovery_and_business_completion[DUPLICATE_DELIVERY]`; JUnit time `36.050s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_browser_lab'][@name='test_full_lab_browser_authorization_recovery_and_business_completion[DUPLICATE_DELIVERY]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_browser_lab.py::test_full_lab_browser_authorization_recovery_and_business_completion[WMS_UNAVAILABLE]`; JUnit time `37.990s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_browser_lab'][@name='test_full_lab_browser_authorization_recovery_and_business_completion[WMS_UNAVAILABLE]']`.

### A13

- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_opc_health_probe.py::test_slow_real_server_state_probe_preserves_original_execution_session`; JUnit time `8.764s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_opc_health_probe'][@name='test_slow_real_server_state_probe_preserves_original_execution_session']`.

### A14

- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_opc_health_probe.py::test_sustained_real_server_state_delay_is_bounded_without_a_second_execution`; JUnit time `12.996s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_opc_health_probe'][@name='test_sustained_real_server_state_delay_is_bounded_without_a_second_execution']`.

### A15

- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_plc_process_restart.py::test_opc_server_process_restart_does_not_regrant_effect`; JUnit time `4.429s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_plc_process_restart'][@name='test_opc_server_process_restart_does_not_regrant_effect']`.

### A16

- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_plc.py::test_acknowledgement_cannot_mark_a_concurrently_advanced_result`; JUnit time `0.783s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_plc'][@name='test_acknowledgement_cannot_mark_a_concurrently_advanced_result']`.

### A17

- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_plc.py::test_journal_rejects_payload_and_result_conflicts`; JUnit time `0.702s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_plc'][@name='test_journal_rejects_payload_and_result_conflicts']`.

### A18

- **PASS (historical a881acf suite 1 only)**: `tests/browser/test_guided_console.py::test_guided_retry_delivery_indicators_and_expandable_payload_are_persisted_and_readonly[BROKER_TRANSIENT-synthetic]`; JUnit time `6.002s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_retry_delivery_indicators_and_expandable_payload_are_persisted_and_readonly[BROKER_TRANSIENT-synthetic]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/browser/test_guided_console.py::test_guided_retry_delivery_indicators_and_expandable_payload_are_persisted_and_readonly[DUPLICATE_DELIVERY-synthetic]`; JUnit time `5.896s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_retry_delivery_indicators_and_expandable_payload_are_persisted_and_readonly[DUPLICATE_DELIVERY-synthetic]']`.

### A19

- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_business.py::test_every_displayed_source_symbol_actually_executed_and_excerpt_matches_file[None]`; JUnit time `5.983s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_business'][@name='test_every_displayed_source_symbol_actually_executed_and_excerpt_matches_file[None]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_business.py::test_every_displayed_source_symbol_actually_executed_and_excerpt_matches_file[DROP_ACK_AFTER_EFFECT]`; JUnit time `6.305s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_business'][@name='test_every_displayed_source_symbol_actually_executed_and_excerpt_matches_file[DROP_ACK_AFTER_EFFECT]']`.

### A20

- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_source_map.py::test_every_lab_stage_source_symbol_executes_and_excerpt_matches`; JUnit time `15.789s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_source_map'][@name='test_every_lab_stage_source_symbol_executes_and_excerpt_matches']`.

### A21

- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided.py::test_trace_sanitizes_exception_text_headers_and_credentials`; JUnit time `0.220s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_trace_sanitizes_exception_text_headers_and_credentials']`.

### A22

- **PASS (historical a881acf suite 1 only)**: `tests/browser/test_guided_console.py::test_guided_lost_ack_reconciles_original_command_without_second_effect[synthetic]`; JUnit time `11.536s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_lost_ack_reconciles_original_command_without_second_effect[synthetic]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/browser/test_guided_console.py::test_guided_lost_ack_reconciles_original_command_without_second_effect[blender]`; JUnit time `26.078s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_lost_ack_reconciles_original_command_without_second_effect[blender]']`.

### A23

- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided.py::test_readonly_routes_and_stream_do_not_advance`; JUnit time `2.065s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_readonly_routes_and_stream_do_not_advance']`.

### A24

- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_readonly.py::test_deleted_guided_store_reads_do_not_recreate_database[False-get]`; JUnit time `0.088s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[False-get]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_readonly.py::test_deleted_guided_store_reads_do_not_recreate_database[False-list]`; JUnit time `0.087s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[False-list]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_readonly.py::test_deleted_guided_store_reads_do_not_recreate_database[False-prior_authorization]`; JUnit time `0.092s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[False-prior_authorization]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_readonly.py::test_deleted_guided_store_reads_do_not_recreate_database[True-get]`; JUnit time `0.135s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[True-get]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_readonly.py::test_deleted_guided_store_reads_do_not_recreate_database[True-list]`; JUnit time `0.137s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[True-list]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_readonly.py::test_deleted_guided_store_reads_do_not_recreate_database[True-prior_authorization]`; JUnit time `0.137s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[True-prior_authorization]']`.

### A25

- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided.py::test_active_stream_closes_when_world_is_cleared_or_deleted[False-clear-4409]`; JUnit time `0.635s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_active_stream_closes_when_world_is_cleared_or_deleted[False-clear-4409]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided.py::test_active_stream_closes_when_world_is_cleared_or_deleted[False-delete-4404]`; JUnit time `0.556s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_active_stream_closes_when_world_is_cleared_or_deleted[False-delete-4404]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided.py::test_active_stream_closes_when_world_is_cleared_or_deleted[True-clear-4409]`; JUnit time `0.891s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_active_stream_closes_when_world_is_cleared_or_deleted[True-clear-4409]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided.py::test_active_stream_closes_when_world_is_cleared_or_deleted[True-delete-4404]`; JUnit time `0.808s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_active_stream_closes_when_world_is_cleared_or_deleted[True-delete-4404]']`.

### A26

- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_distributed.py::test_broker_failure_retains_outbox_and_opc_disconnect_never_executes`; JUnit time `7.999s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_distributed'][@name='test_broker_failure_retains_outbox_and_opc_disconnect_never_executes']`.

### A27

- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_guided_boot_recovery.py::test_boot_change_before_dispatch_rechecks_then_requires_renewed_physical_consent`; JUnit time `12.687s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_boot_recovery'][@name='test_boot_change_before_dispatch_rechecks_then_requires_renewed_physical_consent']`.

### A28

- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_guided_boot_recovery.py::test_boot_change_after_dispatch_intent_remains_uncertain_without_repeat`; JUnit time `12.719s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_boot_recovery'][@name='test_boot_change_after_dispatch_intent_remains_uncertain_without_repeat']`.

### A29

- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_guided_boot_recovery.py::test_interrupted_unstarted_lab_dispatch_returns_to_preconditions`; JUnit time `11.762s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_boot_recovery'][@name='test_interrupted_unstarted_lab_dispatch_returns_to_preconditions']`.

### A30

- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_plc.py::test_restart_invalidates_readiness_until_fresh_checks[False]`; JUnit time `0.769s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_plc'][@name='test_restart_invalidates_readiness_until_fresh_checks[False]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/lab/test_plc.py::test_restart_invalidates_readiness_until_fresh_checks[True]`; JUnit time `0.771s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_plc'][@name='test_restart_invalidates_readiness_until_fresh_checks[True]']`.

### A31

- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided.py::test_uncertain_run_queries_original_identity_and_never_repeats_effect[DROP_ACK_AFTER_EFFECT-1-COMPLETED]`; JUnit time `2.658s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_uncertain_run_queries_original_identity_and_never_repeats_effect[DROP_ACK_AFTER_EFFECT-1-COMPLETED]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided.py::test_uncertain_run_queries_original_identity_and_never_repeats_effect[DROP_ACK_BEFORE_EFFECT-0-FAILED]`; JUnit time `2.477s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_uncertain_run_queries_original_identity_and_never_repeats_effect[DROP_ACK_BEFORE_EFFECT-0-FAILED]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided.py::test_uncertain_run_queries_original_identity_and_never_repeats_effect[STALE_OBSERVATION-1-COMPLETED]`; JUnit time `2.478s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_uncertain_run_queries_original_identity_and_never_repeats_effect[STALE_OBSERVATION-1-COMPLETED]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided.py::test_uncertain_run_queries_original_identity_and_never_repeats_effect[MISSING_OBSERVATION-1-COMPLETED]`; JUnit time `2.311s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_uncertain_run_queries_original_identity_and_never_repeats_effect[MISSING_OBSERVATION-1-COMPLETED]']`.

### A32

- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_business.py::test_wms_outage_cannot_complete_erp_order_before_business_stage`; JUnit time `2.674s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_business'][@name='test_wms_outage_cannot_complete_erp_order_before_business_stage']`.

### A33

- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_business.py::test_erp_completion_requires_durable_acknowledgement_for_every_order_line`; JUnit time `4.417s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_business'][@name='test_erp_completion_requires_durable_acknowledgement_for_every_order_line']`.

### A34

- **PASS (historical a881acf suite 1 only)**: `tests/contract/test_governance.py::test_knowledge_base_links_ids_sources_and_status`; JUnit time `1.296s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.contract.test_governance'][@name='test_knowledge_base_links_ids_sources_and_status']`.

### A35

- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_demo_driver.py::test_automatic_lost_ack_demo_queries_original_without_another_pick`; JUnit time `3.287s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_demo_driver'][@name='test_automatic_lost_ack_demo_queries_original_without_another_pick']`.

### A36

- **PASS (historical a881acf suite 1 only)**: `tests/contract/test_governance.py::test_domain_boundary_has_no_blender_or_network_dependency`; JUnit time `0.019s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.contract.test_governance'][@name='test_domain_boundary_has_no_blender_or_network_dependency']`.

### A37

- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_http_server_lifecycle.py::test_http_server_peer_reset_exits_cleanly[peer-reset-http]`; JUnit time `0.227s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_http_server_lifecycle'][@name='test_http_server_peer_reset_exits_cleanly[peer-reset-http]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_http_server_lifecycle.py::test_http_server_peer_reset_exits_cleanly[peer-reset-websocket]`; JUnit time `0.215s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_http_server_lifecycle'][@name='test_http_server_peer_reset_exits_cleanly[peer-reset-websocket]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_http_server_lifecycle.py::test_http_server_peer_reset_exits_cleanly[shutdown-reset-http]`; JUnit time `0.205s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_http_server_lifecycle'][@name='test_http_server_peer_reset_exits_cleanly[shutdown-reset-http]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_http_server_lifecycle.py::test_http_server_peer_reset_exits_cleanly[shutdown-reset-websocket]`; JUnit time `0.224s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_http_server_lifecycle'][@name='test_http_server_peer_reset_exits_cleanly[shutdown-reset-websocket]']`.

### A38

- **PASS (historical a881acf suite 1 only)**: `tests/unit/test_visualization.py::test_playback_controls_never_dispatch_and_preserve_partial_recording_limits`; JUnit time `1.925s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.unit.test_visualization'][@name='test_playback_controls_never_dispatch_and_preserve_partial_recording_limits']`.

### A39

- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_playback.py::test_playback_scenario_survives_reload_for_every_line_without_read_effects[None]`; JUnit time `0.615s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[None]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_playback.py::test_playback_scenario_survives_reload_for_every_line_without_read_effects[DUPLICATE_DELIVERY]`; JUnit time `0.642s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[DUPLICATE_DELIVERY]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_playback.py::test_playback_scenario_survives_reload_for_every_line_without_read_effects[BROKER_TRANSIENT]`; JUnit time `0.630s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[BROKER_TRANSIENT]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_playback.py::test_playback_scenario_survives_reload_for_every_line_without_read_effects[EDGE_TRANSIENT]`; JUnit time `0.634s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[EDGE_TRANSIENT]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_playback.py::test_playback_scenario_survives_reload_for_every_line_without_read_effects[OPC_UA_DISCONNECT]`; JUnit time `0.868s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[OPC_UA_DISCONNECT]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_playback.py::test_playback_scenario_survives_reload_for_every_line_without_read_effects[PLC_RESTART]`; JUnit time `0.647s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[PLC_RESTART]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_playback.py::test_playback_scenario_survives_reload_for_every_line_without_read_effects[WMS_UNAVAILABLE]`; JUnit time `0.617s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_playback_scenario_survives_reload_for_every_line_without_read_effects[WMS_UNAVAILABLE]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_playback.py::test_unavailable_saved_scenario_never_becomes_a_baseline[missing]`; JUnit time `0.605s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_unavailable_saved_scenario_never_becomes_a_baseline[missing]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_playback.py::test_unavailable_saved_scenario_never_becomes_a_baseline[invalid]`; JUnit time `0.608s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_unavailable_saved_scenario_never_becomes_a_baseline[invalid]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_playback.py::test_unavailable_saved_scenario_never_becomes_a_baseline[different_order]`; JUnit time `0.558s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_unavailable_saved_scenario_never_becomes_a_baseline[different_order]']`.
- **PASS (historical a881acf suite 1 only)**: `tests/integration/test_guided_playback.py::test_legacy_playback_scenario_read_does_not_create_guided_schema`; JUnit time `0.143s`.
  - Exact pointer: `docs/evidence/acceptance/20261006T012424/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_playback'][@name='test_legacy_playback_scenario_read_does_not_create_guided_schema']`.

## Historical 4774 exact successful first-pass JUnit catalog

This secondary historical catalog is unchanged; the A catalog above is also historical, from a881acf. Neither catalog is current 9e83fe7 proof. All entries below are actual successful `<testcase>` elements in `docs/evidence/acceptance/20261005T224038/tests-1.xml` (SHA256 `c8713da9eb0f8352a3f35a05e66bd9debb8e1538e3bee3231b7e32d28e19b9dc`). Each has no failure, error or skipped child. These 36 mapped test functions expand to **61 unique successful cases**, included in the 799-case first suite rather than added to it. The entries below deliberately remain suite-1 locators and durations. Every exact classname/name pair was also resolved successfully in `docs/evidence/acceptance/20261005T224038/tests-2.xml`; use the same XML selector with that file for the second-pass pointer. Suite-2 per-case times are not represented by the suite-1 durations below.

Each entry provides the exact repository node ID and an exact XML selector. The parameter spelling is preserved verbatim, including the native happy browser empty `[]`. J02/J18/J22 are automated local browser tests; J12 is the automated independent-process native lab browser. Other lab integration cases use actual protocols but may use TestClient/in-process fixture listeners, so they are not automatically proof that all application services ran in separate processes. No entry records final manual work or remote CI.

### J01

- **PASS (suite 1 only)**: `tests/integration/test_guided.py::test_guided_authorization_is_bounded_durable_and_physically_gated`; JUnit time `4.385s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_guided_authorization_is_bounded_durable_and_physically_gated']`.

### J02

- **PASS (suite 1 only)**: `tests/browser/test_guided_console.py::test_guided_happy_reload_gate_trace_and_business_completion[synthetic]`; JUnit time `11.762s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_happy_reload_gate_trace_and_business_completion[synthetic]']`.
- **PASS (suite 1 only)**: `tests/browser/test_guided_console.py::test_guided_happy_reload_gate_trace_and_business_completion[blender]`; JUnit time `26.588s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_happy_reload_gate_trace_and_business_completion[blender]']`.

### J03

- **PASS (suite 1 only)**: `tests/lab/test_guided_lab.py::test_guided_network_stack_recovers_without_repeating_motion[None]`; JUnit time `18.711s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_lab'][@name='test_guided_network_stack_recovers_without_repeating_motion[None]']`.
- **PASS (suite 1 only)**: `tests/lab/test_guided_lab.py::test_guided_network_stack_recovers_without_repeating_motion[DROP_ACK_AFTER_EFFECT]`; JUnit time `20.749s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_lab'][@name='test_guided_network_stack_recovers_without_repeating_motion[DROP_ACK_AFTER_EFFECT]']`.
- **PASS (suite 1 only)**: `tests/lab/test_guided_lab.py::test_guided_network_stack_recovers_without_repeating_motion[DUPLICATE_DELIVERY]`; JUnit time `17.655s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_lab'][@name='test_guided_network_stack_recovers_without_repeating_motion[DUPLICATE_DELIVERY]']`.
- **PASS (suite 1 only)**: `tests/lab/test_guided_lab.py::test_guided_network_stack_recovers_without_repeating_motion[PLC_RESTART]`; JUnit time `18.726s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_lab'][@name='test_guided_network_stack_recovers_without_repeating_motion[PLC_RESTART]']`.
- **PASS (suite 1 only)**: `tests/lab/test_guided_lab.py::test_guided_network_stack_recovers_without_repeating_motion[WMS_UNAVAILABLE]`; JUnit time `18.621s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_lab'][@name='test_guided_network_stack_recovers_without_repeating_motion[WMS_UNAVAILABLE]']`.

### J04

- **PASS (suite 1 only)**: `tests/integration/test_guided.py::test_revision_guard_and_double_click_are_idempotent`; JUnit time `0.377s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_revision_guard_and_double_click_are_idempotent']`.

### J05

- **PASS (suite 1 only)**: `tests/integration/test_guided_recovery.py::test_reconciliation_idempotency_binds_observation_fault[None]`; JUnit time `2.694s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_recovery'][@name='test_reconciliation_idempotency_binds_observation_fault[None]']`.
- **PASS (suite 1 only)**: `tests/integration/test_guided_recovery.py::test_reconciliation_idempotency_binds_observation_fault[STALE_OBSERVATION]`; JUnit time `2.806s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_recovery'][@name='test_reconciliation_idempotency_binds_observation_fault[STALE_OBSERVATION]']`.

### J06

- **PASS (suite 1 only)**: `tests/integration/test_demo_driver.py::test_automatic_driver_requires_explicit_physical_consent_and_resumes_original`; JUnit time `5.678s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_demo_driver'][@name='test_automatic_driver_requires_explicit_physical_consent_and_resumes_original']`.

### J07

- **PASS (suite 1 only)**: `tests/e2e/test_workflow.py::test_happy_path`; JUnit time `0.988s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.e2e.test_workflow'][@name='test_happy_path']`.

### J08

- **PASS (suite 1 only)**: `tests/e2e/test_workflow.py::test_lost_ack_before_effect`; JUnit time `1.104s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.e2e.test_workflow'][@name='test_lost_ack_before_effect']`.

### J09

- **PASS (suite 1 only)**: `tests/lab/test_distributed.py::test_postgres_full_repository_intake_and_atomic_outbox`; JUnit time `4.753s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_distributed'][@name='test_postgres_full_repository_intake_and_atomic_outbox']`.

### J10

- **PASS (suite 1 only)**: `tests/lab/test_distributed.py::test_real_pg_rabbit_edge_opc_duplicate_and_lost_ack[DROP_ACK_BEFORE_EFFECT-0]`; JUnit time `4.715s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_distributed'][@name='test_real_pg_rabbit_edge_opc_duplicate_and_lost_ack[DROP_ACK_BEFORE_EFFECT-0]']`.
- **PASS (suite 1 only)**: `tests/lab/test_distributed.py::test_real_pg_rabbit_edge_opc_duplicate_and_lost_ack[DROP_ACK_AFTER_EFFECT-1]`; JUnit time `4.668s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_distributed'][@name='test_real_pg_rabbit_edge_opc_duplicate_and_lost_ack[DROP_ACK_AFTER_EFFECT-1]']`.

### J11

- **PASS (suite 1 only)**: `tests/lab/test_plc.py::test_real_opcua_browse_subscription_acceptance_gate_and_result`; JUnit time `2.766s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_plc'][@name='test_real_opcua_browse_subscription_acceptance_gate_and_result']`.

### J12

- **PASS (suite 1 only)**: `tests/lab/test_browser_lab.py::test_full_lab_browser_authorization_recovery_and_business_completion[]`; JUnit time `52.028s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_browser_lab'][@name='test_full_lab_browser_authorization_recovery_and_business_completion[]']`.
- **PASS (suite 1 only)**: `tests/lab/test_browser_lab.py::test_full_lab_browser_authorization_recovery_and_business_completion[DROP_ACK_AFTER_EFFECT]`; JUnit time `40.072s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_browser_lab'][@name='test_full_lab_browser_authorization_recovery_and_business_completion[DROP_ACK_AFTER_EFFECT]']`.
- **PASS (suite 1 only)**: `tests/lab/test_browser_lab.py::test_full_lab_browser_authorization_recovery_and_business_completion[DUPLICATE_DELIVERY]`; JUnit time `35.957s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_browser_lab'][@name='test_full_lab_browser_authorization_recovery_and_business_completion[DUPLICATE_DELIVERY]']`.
- **PASS (suite 1 only)**: `tests/lab/test_browser_lab.py::test_full_lab_browser_authorization_recovery_and_business_completion[WMS_UNAVAILABLE]`; JUnit time `39.102s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_browser_lab'][@name='test_full_lab_browser_authorization_recovery_and_business_completion[WMS_UNAVAILABLE]']`.

### J13

- **PASS (suite 1 only)**: `tests/lab/test_opc_health_probe.py::test_slow_real_server_state_probe_preserves_original_execution_session`; JUnit time `9.953s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_opc_health_probe'][@name='test_slow_real_server_state_probe_preserves_original_execution_session']`.

### J14

- **PASS (suite 1 only)**: `tests/lab/test_opc_health_probe.py::test_sustained_real_server_state_delay_is_bounded_without_a_second_execution`; JUnit time `12.755s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_opc_health_probe'][@name='test_sustained_real_server_state_delay_is_bounded_without_a_second_execution']`.

### J15

- **PASS (suite 1 only)**: `tests/lab/test_plc_process_restart.py::test_opc_server_process_restart_does_not_regrant_effect`; JUnit time `4.442s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_plc_process_restart'][@name='test_opc_server_process_restart_does_not_regrant_effect']`.

### J16

- **PASS (suite 1 only)**: `tests/lab/test_plc.py::test_acknowledgement_cannot_mark_a_concurrently_advanced_result`; JUnit time `0.685s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_plc'][@name='test_acknowledgement_cannot_mark_a_concurrently_advanced_result']`.

### J17

- **PASS (suite 1 only)**: `tests/lab/test_plc.py::test_journal_rejects_payload_and_result_conflicts`; JUnit time `0.655s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_plc'][@name='test_journal_rejects_payload_and_result_conflicts']`.

### J18

- **PASS (suite 1 only)**: `tests/browser/test_guided_console.py::test_guided_retry_delivery_indicators_and_expandable_payload_are_persisted_and_readonly[BROKER_TRANSIENT-synthetic]`; JUnit time `6.505s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_retry_delivery_indicators_and_expandable_payload_are_persisted_and_readonly[BROKER_TRANSIENT-synthetic]']`.
- **PASS (suite 1 only)**: `tests/browser/test_guided_console.py::test_guided_retry_delivery_indicators_and_expandable_payload_are_persisted_and_readonly[DUPLICATE_DELIVERY-synthetic]`; JUnit time `6.338s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_retry_delivery_indicators_and_expandable_payload_are_persisted_and_readonly[DUPLICATE_DELIVERY-synthetic]']`.

### J19

- **PASS (suite 1 only)**: `tests/integration/test_guided_business.py::test_every_displayed_source_symbol_actually_executed_and_excerpt_matches_file[None]`; JUnit time `5.778s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_business'][@name='test_every_displayed_source_symbol_actually_executed_and_excerpt_matches_file[None]']`.
- **PASS (suite 1 only)**: `tests/integration/test_guided_business.py::test_every_displayed_source_symbol_actually_executed_and_excerpt_matches_file[DROP_ACK_AFTER_EFFECT]`; JUnit time `6.153s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_business'][@name='test_every_displayed_source_symbol_actually_executed_and_excerpt_matches_file[DROP_ACK_AFTER_EFFECT]']`.

### J20

- **PASS (suite 1 only)**: `tests/lab/test_source_map.py::test_every_lab_stage_source_symbol_executes_and_excerpt_matches`; JUnit time `15.658s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_source_map'][@name='test_every_lab_stage_source_symbol_executes_and_excerpt_matches']`.

### J21

- **PASS (suite 1 only)**: `tests/integration/test_guided.py::test_trace_sanitizes_exception_text_headers_and_credentials`; JUnit time `0.227s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_trace_sanitizes_exception_text_headers_and_credentials']`.

### J22

- **PASS (suite 1 only)**: `tests/browser/test_guided_console.py::test_guided_lost_ack_reconciles_original_command_without_second_effect[synthetic]`; JUnit time `11.670s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_lost_ack_reconciles_original_command_without_second_effect[synthetic]']`.
- **PASS (suite 1 only)**: `tests/browser/test_guided_console.py::test_guided_lost_ack_reconciles_original_command_without_second_effect[blender]`; JUnit time `27.535s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.browser.test_guided_console'][@name='test_guided_lost_ack_reconciles_original_command_without_second_effect[blender]']`.

### J23

- **PASS (suite 1 only)**: `tests/integration/test_guided.py::test_readonly_routes_and_stream_do_not_advance`; JUnit time `1.998s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_readonly_routes_and_stream_do_not_advance']`.

### J24

- **PASS (suite 1 only)**: `tests/integration/test_guided_readonly.py::test_deleted_guided_store_reads_do_not_recreate_database[False-get]`; JUnit time `0.088s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[False-get]']`.
- **PASS (suite 1 only)**: `tests/integration/test_guided_readonly.py::test_deleted_guided_store_reads_do_not_recreate_database[False-list]`; JUnit time `0.085s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[False-list]']`.
- **PASS (suite 1 only)**: `tests/integration/test_guided_readonly.py::test_deleted_guided_store_reads_do_not_recreate_database[False-prior_authorization]`; JUnit time `0.080s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[False-prior_authorization]']`.
- **PASS (suite 1 only)**: `tests/integration/test_guided_readonly.py::test_deleted_guided_store_reads_do_not_recreate_database[True-get]`; JUnit time `0.136s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[True-get]']`.
- **PASS (suite 1 only)**: `tests/integration/test_guided_readonly.py::test_deleted_guided_store_reads_do_not_recreate_database[True-list]`; JUnit time `0.142s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[True-list]']`.
- **PASS (suite 1 only)**: `tests/integration/test_guided_readonly.py::test_deleted_guided_store_reads_do_not_recreate_database[True-prior_authorization]`; JUnit time `0.141s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_readonly'][@name='test_deleted_guided_store_reads_do_not_recreate_database[True-prior_authorization]']`.

### J25

- **PASS (suite 1 only)**: `tests/integration/test_guided.py::test_active_stream_closes_when_world_is_cleared_or_deleted[False-clear-4409]`; JUnit time `0.655s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_active_stream_closes_when_world_is_cleared_or_deleted[False-clear-4409]']`.
- **PASS (suite 1 only)**: `tests/integration/test_guided.py::test_active_stream_closes_when_world_is_cleared_or_deleted[False-delete-4404]`; JUnit time `0.571s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_active_stream_closes_when_world_is_cleared_or_deleted[False-delete-4404]']`.
- **PASS (suite 1 only)**: `tests/integration/test_guided.py::test_active_stream_closes_when_world_is_cleared_or_deleted[True-clear-4409]`; JUnit time `0.938s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_active_stream_closes_when_world_is_cleared_or_deleted[True-clear-4409]']`.
- **PASS (suite 1 only)**: `tests/integration/test_guided.py::test_active_stream_closes_when_world_is_cleared_or_deleted[True-delete-4404]`; JUnit time `1.121s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_active_stream_closes_when_world_is_cleared_or_deleted[True-delete-4404]']`.

### J26

- **PASS (suite 1 only)**: `tests/lab/test_distributed.py::test_broker_failure_retains_outbox_and_opc_disconnect_never_executes`; JUnit time `7.906s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_distributed'][@name='test_broker_failure_retains_outbox_and_opc_disconnect_never_executes']`.

### J27

- **PASS (suite 1 only)**: `tests/lab/test_guided_boot_recovery.py::test_boot_change_before_dispatch_rechecks_then_requires_renewed_physical_consent`; JUnit time `13.581s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_boot_recovery'][@name='test_boot_change_before_dispatch_rechecks_then_requires_renewed_physical_consent']`.

### J28

- **PASS (suite 1 only)**: `tests/lab/test_guided_boot_recovery.py::test_boot_change_after_dispatch_intent_remains_uncertain_without_repeat`; JUnit time `11.693s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_boot_recovery'][@name='test_boot_change_after_dispatch_intent_remains_uncertain_without_repeat']`.

### J29

- **PASS (suite 1 only)**: `tests/lab/test_guided_boot_recovery.py::test_interrupted_unstarted_lab_dispatch_returns_to_preconditions`; JUnit time `10.654s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_guided_boot_recovery'][@name='test_interrupted_unstarted_lab_dispatch_returns_to_preconditions']`.

### J30

- **PASS (suite 1 only)**: `tests/lab/test_plc.py::test_restart_invalidates_readiness_until_fresh_checks[False]`; JUnit time `0.701s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_plc'][@name='test_restart_invalidates_readiness_until_fresh_checks[False]']`.
- **PASS (suite 1 only)**: `tests/lab/test_plc.py::test_restart_invalidates_readiness_until_fresh_checks[True]`; JUnit time `0.660s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.lab.test_plc'][@name='test_restart_invalidates_readiness_until_fresh_checks[True]']`.

### J31

- **PASS (suite 1 only)**: `tests/integration/test_guided.py::test_uncertain_run_queries_original_identity_and_never_repeats_effect[DROP_ACK_AFTER_EFFECT-1-COMPLETED]`; JUnit time `3.894s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_uncertain_run_queries_original_identity_and_never_repeats_effect[DROP_ACK_AFTER_EFFECT-1-COMPLETED]']`.
- **PASS (suite 1 only)**: `tests/integration/test_guided.py::test_uncertain_run_queries_original_identity_and_never_repeats_effect[DROP_ACK_BEFORE_EFFECT-0-FAILED]`; JUnit time `3.386s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_uncertain_run_queries_original_identity_and_never_repeats_effect[DROP_ACK_BEFORE_EFFECT-0-FAILED]']`.
- **PASS (suite 1 only)**: `tests/integration/test_guided.py::test_uncertain_run_queries_original_identity_and_never_repeats_effect[STALE_OBSERVATION-1-COMPLETED]`; JUnit time `3.953s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_uncertain_run_queries_original_identity_and_never_repeats_effect[STALE_OBSERVATION-1-COMPLETED]']`.
- **PASS (suite 1 only)**: `tests/integration/test_guided.py::test_uncertain_run_queries_original_identity_and_never_repeats_effect[MISSING_OBSERVATION-1-COMPLETED]`; JUnit time `3.963s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided'][@name='test_uncertain_run_queries_original_identity_and_never_repeats_effect[MISSING_OBSERVATION-1-COMPLETED]']`.

### J32

- **PASS (suite 1 only)**: `tests/integration/test_guided_business.py::test_wms_outage_cannot_complete_erp_order_before_business_stage`; JUnit time `2.819s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_business'][@name='test_wms_outage_cannot_complete_erp_order_before_business_stage']`.

### J33

- **PASS (suite 1 only)**: `tests/integration/test_guided_business.py::test_erp_completion_requires_durable_acknowledgement_for_every_order_line`; JUnit time `4.350s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_guided_business'][@name='test_erp_completion_requires_durable_acknowledgement_for_every_order_line']`.

### J34

- **PASS (suite 1 only)**: `tests/contract/test_governance.py::test_knowledge_base_links_ids_sources_and_status`; JUnit time `2.449s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.contract.test_governance'][@name='test_knowledge_base_links_ids_sources_and_status']`.

### J35

- **PASS (suite 1 only)**: `tests/integration/test_demo_driver.py::test_automatic_lost_ack_demo_queries_original_without_another_pick`; JUnit time `6.084s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.integration.test_demo_driver'][@name='test_automatic_lost_ack_demo_queries_original_without_another_pick']`.

### J36

- **PASS (suite 1 only)**: `tests/contract/test_governance.py::test_domain_boundary_has_no_blender_or_network_dependency`; JUnit time `0.048s`.
  - Exact pointer: `docs/evidence/acceptance/20261005T224038/tests-1.xml` -> `.//testcase[@classname='tests.contract.test_governance'][@name='test_domain_boundary_has_no_blender_or_network_dependency']`.

## Mandatory final agent loop: all 14 steps

Exact action text is preserved. Actions 1, 3, 4 and 6-9 retain completed source-A inspection/manual evidence. Updated C entries carry the separate acceptance/publication closure. R still requires its own complete attestation.

| Step | Required action | Result / evidence boundary |
| --- | --- | --- |
| 1 | Re-read this entire `GOAL.md`. | LOCAL COMPLETE. Entire GOAL reread by this author, including non-checkbox topology/stages/UX/failure/truth requirements. Root independently reports an entire reread at04:23UTC. Exact51/14 text comparison is bound in the receipt. |
| 2 | Build a checklist from every Definition of Done item. | COMPLETE for audited C. All 51 exact requirements are mapped; all 169 MUSTs pass. R still requires independent attestation. |
| 3 | Inspect the implementation, not just test names, and map each item to concrete files/symbols/tests. | LOCAL COMPLETE. Retained inspected file/symbol/assertion mappings and source-A N77 dual-pass locators are reconciled with terminal/manual/audit receipts. This is not a claim of re-running every earlier source audit. |
| 4 | Start the complete integration-lab stack from a clean state. | LOCAL COMPLETE. New namespace0167de6e4ed545029461cc08cac14a11, native Blender and separate healthy API/WMS/edge/PLC over actual PostgreSQL/RabbitMQ; no Docker execution claim. |
| 5 | Run the full automated unit/integration/E2E suite. | COMPLETE for C: two clean 831-case Linux suites, identical testcase identities, zero failures/errors/skips, JUnit 1079.192/991.936s and coverage 91.36194029850746/91.36194029850746%. A's two 815-case suites remain separately scoped. |
| 6 | Execute the guided happy path in a real browser and verify the 3D handoff and post-execution reconciliation. | LOCAL COMPLETE. Fresh happy proves gate0/disabled replay, explicit consent, original Blender recording/rendered movement and post-execution verification/WMS/ERP completion. |
| 7 | Execute the lost-ACK-after-effect scenario and prove from persisted command/effect evidence that reconciliation does not execute the physical pick twice. | LOCAL COMPLETE. Fresh lost browser/CLI retain original command/receipt and effect 1 through explicit reconcile with no physical resend; browser runtime hash unchanged between unknown/completed. |
| 8 | Reload the browser mid-session and verify safe resume. | LOCAL COMPLETE. Fresh happy stage 10/revision 18 reload preserves full API bytes and does not auto-advance; source-A automated reload cases also pass. |
| 9 | Trigger duplicate authorization/delivery and verify idempotency. | LOCAL COMPLETE. Original happy stage 1 authorization replay preserves session/journals/effect; fresh duplicate publication retains effect 1 for two same-hash deliveries. Actual broker redelivery remains separately N10. |
| 10 | Check logs/trace UI for secret leakage and misleading “real” labels. | COMPLETE within the bound inventories: source-A trace/manual/DOM review, exact-P public tree/history audit and reviewed C workflow-only extension. New R payload receives its own review; heuristic/image limits remain explicit. |
| 11 | Run lint/type/security checks configured by the repository. | COMPLETE for C: configured lint/type/security and all local gates pass in the linked canonical manifest. Raw Bandit findings and reviewed policy exceptions retain their actual scope; no zero-finding assertion is inferred. |
| 12 | Fix every failure found, then repeat the relevant tests. | COMPLETE for C. Runtime/harness, publication-link, archived-Markdown and Windows-checkout failures are preserved with their relevant repeat proofs; C's complete acceptance/native/publication succeeds. Any failure in R blocks its final attestation. |
| 13 | Update documentation to match what actually exists. | COMPLETE at audited C, with coherent status/evidence synchronization proposed in R. Changed R publication is rebuilt/reviewed and its own remote checks remain mandatory. |
| 14 | Produce a final completion report containing: | SOURCE-BOUND COMPLETION REPORT PRODUCED for C: exact requirement evidence, actual test results, source-A manual scenarios, limitations and C SHA. R's independent CI/deployed-build artifacts and final response supply R's SHA after its own mandatory checks pass. |

## Preserved A/P preparation history and remaining simulation limits

[ADR0002](../docs/adr/0002-acceptance-attestations.md) requires immutable source attribution and an independently attested completion successor. **Do not publish known-broken A9e83fe7 merely to obtain remote attestation.** A remains the local runtime/manual baseline, with815 tests twice and its original outputs unchanged. The next candidate **P is identified by its later independent CI/public build manifests**, rather than a fabricated self-hash: unchanged robot/runtime code plus corrected publication-root validation, five added contract regressions, two report hrefs and reviewed documentation/status/evidence. It is not a status-only change. The five added focused tests are not a complete candidate run; no new full-suite passing total is claimed.

1. Finish the concrete staged proposal, generated-publication/link checks, report and proposed public-payload extension. Preserve original A evidence and explicit unchanged-runtime relationship; never relabel A manifests or manual proof as P execution.
2. Root may apply the reviewed proposal and create candidate P, still NOT DONE. Bind its exact tree/commit and public payload before requesting explicit approval. No report task performs a tracked edit, commit, push, dispatch or status sync. A's old public-preparation sequence is superseded by this section because its two broken links were discovered later.
3. After authorization for the concrete P release, publish P via a supported ref/trigger and verify its own Linux ci.yml two-full-suite acceptance with live PostgreSQL/RabbitMQ and pinned Chromium/Blender. Inspect actual JUnits/coverage and intended workflow conclusions; no inherited A815 result substitutes for P. Separately verify Windows desktop.yml window ownership/close/restart using its headless runtime, not Blender.
4. Verify P publish-reports.yml build/deploy/public smoke and public build.json.source_commit exactly P, including corrected links and artifact/content hashes. Its gh-pages/Pages writes are publication side effects, not robot acceptance. Capture P CI/publication/Pages/native artifacts before any successor replaces them.
5. Refresh the downloaded **exact-P CI acceptance manifest**, preserving its own original local evidence. Do not refresh the A local manifest as though it attests P. The six remote-dependent MUSTs and all three coded remote gates must be proven for P, with the separate native workflow explicitly reviewed.
6. Only once169MUSTs, the independent51/14 obligations, corrected publication and final payload are proven may root create a reviewed status/evidence successor **R**, whose SHA is also unknown until committed. Synchronize sources and rebuild/review changed publication; tools.sync_status alone does not establish manual truth or final commit identity.
7. Publish R only within explicit authorization; verify R's own complete Linux CI, Windows native and publication/Pages artifacts. P proof alone never attests R. Final response can cite R from independent artifacts/public build.json without an endless self-hash rewrite chain.

Remaining coded remote MUSTs: SC-DATA-005, SC-KB-006, SC-KB-007, SC-KB-008, HKM-VIS-MUST-025 and UI-INV-MUST-008. LAB-MUST-044 remains independently pending in the final checklist despite the local automated map entry. Windows native is explicit release scope, not an invented fourth sync_status key. Candidate P/R identity, full test totals and remote conclusions remain unobserved.

This is an independent synthetic integration simulator. PostgreSQL/AMQP/OPC UA/REST traffic is real; ERP/WMS models, virtual PLC, controller callback, robot/world and sensors are simulated. Blender provides synthetic geometry/motion, not validated dynamics, exact HKM1800 behavior or proprietary SICS.AI architecture. Consent, operational readiness and logical E-stop are not certified safety controls; no exactly-once physical hardware guarantee is made. Local demo security and retained-result limits remain documented. The Windows HTTP Selector loop is limited to512 sockets and no asyncio subprocesses/pipes; OPC UA and Playwright loops are separate. Local Windows success is not Linux CI or Docker execution proof.

Optional SC-BRAIN-005 remains unsatisfied; three other SHOULDs pass. No MUST is waived. **GOAL NOT ACHIEVED / NOT DONE** remains binding while the publication correction, proposed payload and exact P/R completion attestations are pending.

## Historical report-preparation provenance

This preserved preparation record describes the original ignored source-A draft and its historical failed evidence; the later tracked report adds audited-C closure above. The author reread GOAL/documentation/workflows and parses saved current receipts, JUnits/coverage and source mapping. Execution/visual work is attributed to its actual reviewer; no runtime, browser, tests, scans, rendering or network is launched here. The companion author receipt binds direct inputs, exact 51/14 texts, N77 dual-pass locators, unchanged historical catalogs and all relative targets. Local runtime success, bounded visual PASS, known broken links and remote-pending status are separate conclusions.


## Historical applied P correction addendum

The earlier preparation statements above are retained as the reviewed A record. The candidate now includes the publication guard and five new link regressions, plus provenance-bound archived Markdown handling in `tools/drift_check.py:archived_markdown` and eleven new archive contract cases. The first actual repository drift check found 2,099 relocated link occurrences in twelve frozen snapshots; it did not find a broken current-document link. Snapshot bytes remain unchanged. Only exact manifest/path/size/SHA256-bound copies retain their historical relative-link context; invalid bindings fail, and live or unlisted Markdown keeps normal link checks. Criterion, reference, diagram and credential checks remain active.

[Applied correction evidence](evidence/lab-publication-link-correction/applied/review.json) preserves the initial failure and subsequent actual commands, logs, JUnit and exit records. The corrected run passed **24 cases in 1.95 seconds**: five publication cases, eleven archive cases and eight existing governance cases, with zero failures/errors/skips. Ruff passed with 233 files formatted; drift passed all 169 MUST identifiers, 31 sources and 13 diagrams. These scoped checks were run on the intentionally dirty candidate before its commit and do not replace P's mandatory full CI suites. Two stale requirements notes now correctly identify completed local A log/UI and lifecycle/reload proof while leaving remote verification pending.

Candidate P also includes this archive-check correction; the earlier five-case description alone is not its full code/test delta. Exact P commit, clean build, PDF/HTML review and committed public-payload review are bound by the later independent preparation receipts. Public publication authorization and P/R Linux, Windows and Pages attestations remain pending. **GOAL NOT ACHIEVED.**
