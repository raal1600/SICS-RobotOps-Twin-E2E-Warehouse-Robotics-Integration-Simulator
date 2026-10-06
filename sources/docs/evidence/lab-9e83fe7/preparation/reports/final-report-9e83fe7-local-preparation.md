# Final Integration Lab local-acceptance report preparation: 9e83fe7

Prepared 2026-10-06T03:55:24.894666+00:00 as a new snapshot; the [reviewed first-pass draft](final-report-9e83fe7-preparation.md) remains unchanged. Overall GOAL remains **NOT ACHIEVED**. Current local acceptance is **PASS: both 815-case suites clean, all 20 local gates passed, 163 locally satisfied MUSTs and six remote-dependent MUSTs unresolved**. Fresh manual/CLI proof, actual final PDF/HTML visual review, full current archive/log/trace/secret review and exact-source remote attestation remain **PENDING**. This update reads saved text/JSON/XML only; no runtime/browser/test/database, broad payload scan or rendering actions.

## Current source identity and pending outcomes

- Clean implementation commit recorded by the new manifest: `9e83fe7d41a52a63ba65b77730e392dafca8fffe`.
- Manifest: [`docs/evidence/acceptance/20261006T024719/manifest.json`](../docs/evidence/acceptance/20261006T024719/manifest.json), started `2026-10-06T02:47:20.134216+00:00`, `dirty=false`.
- Recorded source SHA256 fingerprint: `136641a25c5fbd7d45c016582ec2c5c5197362f44f0a894ee95a69c652e3eafd`.
- Manifest lock SHA256: `50f23c94f4a7601404f7c45ea324a846afe34cb0cfa890c6c44963aca8cd26d1`.
- Actual launcher: [run-acceptance-response-sync.ps1](run-acceptance-response-sync.ps1); [terminal record](acceptance-response-sync-exit.json) exit0, started `2026-10-06T02:47:19.5256375Z`, ended `2026-10-06T03:45:16.7213113Z`. Complete local acceptance is distinct from remote completion.
- Both current JUnits **PASS**, 815 unique clean cases each, identical identities/outcomes. JUnit 1649.757/1675.043s; coverage 91.38059701492537/91.43656716417911%. Repeatability and all 20 local gates **PASS**.
- Fresh current-source manual happy/lost-ACK/duplicate/reload/CLI, full trace/log audit and final PDF/HTML review: **PENDING**.
- Exact-source CI/publication/Pages and final evidence/status successor attestation: **PENDING**. No historical result is relabeled as testing this commit.

## Current terminal local acceptance

The [independent bounded terminal review](final-evidence-pack/9e83fe7/local-acceptance-independent-review.json), SHA256 `d302ec3ac7388b672a5d3b829f6fec875155100a51274f94c9fe11757d034c4d`, confirms all 20 local gates with no issue. It bound 51 saved inputs, compared both complete JUnits and criterion results, and checked eight core Blender demo journal/verdict/effect results. Its [upstream receipt](final-evidence-pack/9e83fe7/local-acceptance-review.json) SHA256 is `e0729460d11ce5c64e7fbd08e58304a68ed593c404d600692780a2126bdf270d`. This report independently parses terminal manifest/exit, both JUnits/coverage and registry/map; it cites the broader independent review without repeating its payload examination.

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

Both runs have the same 815 identities/outcomes and different owned fixture directories; [repeatability](../docs/evidence/acceptance/20261006T024719/repeatability.json) passes. Each console retains one existing deprecation warning, not a failure/teardown error. Current N77 case entries below include exact successful selectors and each run's actual duration; focused overlaps are not added to either 815 total.

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

Current configured quality: Ruff/lint passed, **204 files** already formatted; strict typing passed **67 source files**. Configured security passed with raw Bandit exit1 and **five explicitly reviewed findings**, pip/npm audit exit0 and vendor integrity true. [Security receipt](../docs/evidence/acceptance/20261006T024719/security-review.json) retains the fingerprint-bound exceptions; raw Bandit did not report zero findings. This is distinct from the pending complete archive/log/trace/publication-payload secret review.

There are **169 MUSTs plus 4 SHOULDs**: **163 MUSTs locally satisfied**, all 51 LAB automated-map entries PASS, three SHOULDs PASS and optional `SC-BRAIN-005` unsatisfied (`optional_model_fallback`). The six unresolved MUSTs depend only on the following remote gates in the automated map:

| Remaining mandatory criterion | Required exact-source remote evidence |
| --- | --- |
| `SC-DATA-005` | `ci` |
| `SC-KB-006` | `publication_remote` |
| `SC-KB-007` | `publication_remote` |
| `SC-KB-008` | `pages`, `publication_remote` |
| `HKM-VIS-MUST-025` | `ci`, `publication_remote`, `pages` |
| `UI-INV-MUST-008` | `ci`, `publication_remote`, `pages` |

The automated map does not replace mandatory manual demonstrations, complete trace/secret review or actual PDF/HTML visual review. Every final GOAL row therefore retains PENDING until the remaining manual/audit/publication/remote proof is reconciled.

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

The showcase uses six distinct original commands/tools with one effect each. These core demos do not themselves prove separate-process AMQP/OPC UA or the two exact guided README CLI commands. Native automated browser cases provide protocol evidence; final fresh manual browser/CLI proof remains PENDING.

Publication/build gates passed. The independent review confirms same-source build metadata, **35+13+16=64 pages**, status **NOT DONE**; it did not read/render actual PDFs. Current PDF/HTML visual review and full archive/publication-payload review remain **PENDING**. Root is handling fresh manual work separately; no in-progress manual artifacts are read or attested here.

## Retained first-suite evidence and bounded native lab review

[Current JUnit](../docs/evidence/acceptance/20261006T024719/tests-1.xml) contains 815 actual and unique successful testcase elements, no failure/error/skipped children, and declared counts match. JUnit time **1649.757 s**; [console log](../docs/evidence/acceptance/20261006T024719/tests_1.log) reports **815 passed, 1 warning in 1649.78 s**. The existing Starlette/httpx deprecation warning is not a failure or teardown error. The manifest gate exited 0 in **1651.2559275999956 s** including its wrapper. [Coverage](../docs/evidence/acceptance/20261006T024719/coverage-1.json): **4898/5360**, 462 missing, 17 excluded, **91.38059701492537%**. JUnit SHA256 `7899f43724ec15a2ec4fa7be612fd7eb95c60e690fbeb3af9dbb6ed5e073e5af`; coverage SHA256 `6ace26dd946895fd16504886d8761ee7ce9a00ce4246a22b870cebf144d6c317`. JUnit timestamp `2026-10-06T04:47:41.512942+02:00` is its suite timestamp, not an invented completion UTC.

Exact saved command, not rerun by this preparation:

```text
C:\Users\ramis\source\repos\robotops-twin\.venv\Scripts\python.exe -m tools.dev test --basetemp=C:\Users\ramis\AppData\Local\Temp\robotops-acceptance-1-to2atak6/fixtures --junitxml=C:\Users\ramis\source\repos\robotops-twin\docs\evidence\acceptance\20261006T024719\tests-1.xml --cov=robotops --cov=apps --cov-report=json:C:\Users\ramis\source\repos\robotops-twin\docs\evidence\acceptance\20261006T024719\coverage-1.json --cov-report=term
```

The [finalized first-pass case review](final-evidence-pack/9e83fe7/pass1-case-review-final.json), SHA256 `e0ae138edaddc5d5d08ec3544a7646660e6e7bc55f863a5ac5544a12242d188f`, records **164 checks, four formally passed native lab cases, 35 matching source files, no reported issue**. The retained first-pass preparation independently rehashed its 26 exact saved inputs and 35 named source files, and bound its JUnit/coverage metadata to the actual files. Those inputs were frozen snapshots or saved raw JSON, not a mutable watcher lookup. That preparation opened or rehashed no database; this terminal update does not repeat those checks. The campaign began with `dirty=false`; the case review's contemporaneous source identity recorded `dirty=true` but the same fingerprint. The tracked-difference observation from that first-pass preparation is retained in its [author receipt](final-report-9e83fe7-preparation-review.json); it is not a new observation in this terminal update. A matching fingerprint/named-source set does not claim that every generated document stayed unchanged.

| Current formal native lab testcase (classname `tests.lab.test_browser_lab`) | Runtime | Original command | JUnit seconds | Saved result |
| --- | --- | --- | --- | --- |
| `test_full_lab_browser_authorization_recovery_and_business_completion[]` | blender | `c8806eb8-d12a-59a1-bfb1-7acef07216ec` | 54.177 | COMPLETED, stage 22, revision 44; original-command effect 1; WMS acknowledged and ERP completed. |
| `test_full_lab_browser_authorization_recovery_and_business_completion[DROP_ACK_AFTER_EFFECT]` | synthetic | `8963d437-b345-5af5-8db7-d2477d76a0b9` | 41.033 | COMPLETED, stage 22, revision 46; original-command effect 1; WMS acknowledged and ERP completed. |
| `test_full_lab_browser_authorization_recovery_and_business_completion[DUPLICATE_DELIVERY]` | synthetic | `678aadd3-5d02-53c5-bf1e-548080d5ec38` | 37.049 | COMPLETED, stage 22, revision 44; original-command effect 1; WMS acknowledged and ERP completed. |
| `test_full_lab_browser_authorization_recovery_and_business_completion[WMS_UNAVAILABLE]` | synthetic | `4548efe1-467c-5e5c-a644-79fb4faed2cb` | 38.913 | COMPLETED, stage 22, revision 46; original-command effect 1; WMS acknowledged and ERP completed. |

Only the happy case uses evaluated Blender motion; the fault cases use the synthetic runtime with actual PostgreSQL/AMQP/edge REST/OPC UA/WMS services. They are automated native Windows cases, not the required final manual run, Docker/Compose execution or remote CI. Pre-gate effect zero and replay revision stability rely on exact passed-test assertions where no standalone before-journal/replay-response capture exists. Browser request listeners omit `page.request` calls, including intentional authorization replay: one recorded browser physical POST does not mean only one total HTTP request. Original receipt/effect evidence and formal assertions have separate roles.

The [independent saved-image review](final-evidence-pack/9e83fe7/pass1-saved-visual-review.json), SHA256 `6f5e729e292a86d64bdd0b781fae99bf186f13a55e4f1b6119b8dd696df1c260`, actually viewed eight saved PNGs across the four cases and read happy motion JSON (133 frames, 118 poses, nonzero evaluated/rendered position changes), with no actionable visible finding. This preparation did not re-view those PNGs. Saved captions remained tied to recorded scenarios while future selectors differed; duplicate/WMS-specific briefs were not visible, so no visual brief attestation follows. The image review is bounded saved-artifact work, not a full DOM/trace-secret audit or manual journey. Full current log/trace/secret review, final manual work and final PDF/HTML remain **PENDING**.

## Evidence boundaries and all-repository obligations

| Campaign | Verified historical result or present preparation status | Scope boundary |
| --- | --- | --- |
| Current clean 9e83fe7 | Both 815-case suites clean; all 20 local gates PASS; 163/169 MUSTs locally satisfied | Six remote-dependent MUSTs, fresh manual, full archive/trace/secret and PDF/HTML visual review remain PENDING. |
| Historical clean a881acf | First 815 clean; second 814 passed plus one failure; wrapper exit 1; 18/20 local gates passed | `tests_2` and `repeatability` failed. Final manual/remote closure was not achieved. |
| C5 response/body synchronization, based on a881 | Four existing browser cases passed; one of those cases repeated once with a delayed successful response body and passed | Four unique cases, one controlled repeat; not five additional unique tests or a complete clean-source acceptance. |
| Historical clean b968 | First suite 810 clean JUnit cases plus one teardown error; second interrupted | 811 test bodies passed does not make the teardown-error suite PASS. |
| C4 HTTP-loop correction, based on b968 | Four lifecycle, three desktop and four Blender browser cases passed | Scoped Windows correction evidence; not whole acceptance or Linux proof. |
| Historical clean 4774 | Two 799-pass suites; 20 local gates passed; saved manual/CLI semantics supported, presentation **NOT PASS** | Duplicate/WMS unsupported brief and false Happy replay caption remain archived. |
| Earlier scenario-label correction, based on 4774 | 90 Python, 160 standalone Node and 10 focused browser/protocol cases passed | Separate exact source/wording boundaries; not clean current 9e83fe7 acceptance. |

All **169 MUSTs plus 4 SHOULDs (173 mapped criteria)** remain in scope. The 51 LAB requirements supplement the earlier MUSTs and the mandatory final manual loop. Historical 4774 had 163/169 MUSTs locally satisfied and six remote-dependent unresolved MUSTs: `SC-DATA-005` (`ci`), `SC-KB-006`/`SC-KB-007` (`publication_remote`), `SC-KB-008` (`pages`, `publication_remote`), `HKM-VIS-MUST-025` and `UI-INV-MUST-008` (all three remote gates). Optional `SC-BRAIN-005` (`optional_model_fallback`) was unsatisfied separately. These historical counts do not promote the current source. [Registry](../SUCCESS_CRITERIA.md), [acceptance map](../docs/acceptance-map.json) and [ADR 0002](../docs/adr/0002-acceptance-attestations.md) govern final closure.

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

Historical [4774 archive](../docs/evidence/lab-4774af5/summary.json) records two complete 799-pass suites (1807.596/1648.556 s; 91.38351792753895/91.43983480382954% coverage), all 20 local gates, three saved browser and two README CLI journeys. The historical full saved-trace and secret-candidate review scanned 198,471,933 text bytes, verified 292 persisted truth/protocol labels, and preserved the duplicate/WMS presentation failures. The historical 64-page PDF review and CLI receipts remain historical; no fresh current PDF/visual/secret audit is asserted. The [earlier report](final-report-a881acf-preparation.md) retains the exact archived evidence paths and scope limits.

C1-C3 scenario fixes persist recorded scenario metadata per job, use all six supported briefs, and reject stale live-response identities. The earlier 90 Python/160 Node/10 focused browser-protocol receipts are in [scenario-label correction evidence](../docs/evidence/scenario-label-correction/summary.json). Exact successful a881 first-pass regression locators remain A38/A39 below; they do not prove current final manual captions.

C4's [HTTP-loop correction](../docs/evidence/lab-b968586/http-loop-correction/summary.json) follows the failed b968 campaign. `robotops.http_server.new_event_loop` and `UVICORN_LOOP` select Windows Selector only for HTTP; non-Windows retains Uvicorn auto selection. `apps/api/__main__.py`, `apps/desktop/backend.py`, `robotops/lab/__main__.py` and `tools/lab_stack.py` apply the factory to native API/desktop/edge/API-WMS services; `tests/conftest.py` shares it with strict shutdown checks. OPC UA and Playwright loop ownership is unchanged. `tests/integration/test_http_server_lifecycle.py::test_http_server_peer_reset_exits_cleanly` covers HTTP/WebSocket resets and the deterministic shutdown-reset boundary, with zero retained transports and clean shutdown. Scoped results: four lifecycle cases (0.955 s), three desktop cases (15.667 s), four Blender browser cases (223.458 s; six deliberately deselected). Diagnostics reproduced the Proactor detach failure, not the exact original Chromium timing. Windows Selector's 512-socket/no-asyncio-subprocess limits and absence of Linux/optional-uvloop execution proof remain explicit. C5 changed the investigation test afterward; this draft does not claim all old frozen hash snapshots still equal the current tree.

## All 51 GOAL criteria

The requirement column matches all 51 exact root GOAL checkbox texts. Concrete implementation references are retained from the [inspected map](../docs/integration-lab-requirements.md). N01-N39 are **current 9e83fe7 two-suite** pointers (77 selected unique cases within each 815-case suite), resolved with both actual durations. A01-A39 remain secondary **historical a881 suite-1** pointers (77 cases within its 815-pass first suite, followed by a failed second suite); J01-J36 remain secondary **historical 4774 suite-1** pointers (61 cases within 799). Historical catalogs are unchanged. Both complete suites and all 20 local gates pass; remaining manual/full archive/PDF/remote obligations prevent final closure. Line numbers are navigation hints; named files/symbols define the mapped implementation.

Automated browser evidence is distinct from the required final manual journeys; native Windows evidence is distinct from an executed Compose profile; local evidence is distinct from exact-SHA CI/publication. Future runtime IDs must come from the new manual stack, never a historical case.

| ID | Requirement | Implementation / historical exact proof / current remaining obligations |
| --- | --- | --- |
| LAB-MUST-001 | Create/Run Order starts guided execution rather than secretly running the full robot workflow. | Implementation: `apps/erp_ui/integration-console.js` (IntegrationConsole.start); `apps/api/guided.py:23` (mount_guided_routes). Current 9e83fe7 successful JUnit in both full suites: [N01](#n01), [N02](#n02). Historical a881acf first-pass successful JUnit: [A01](#a01), [A02](#a02). Historical 4774 first-pass successful JUnit: [J01](#j01), [J02](#j02). Bounded REST intake leaves orders/journal absent before their stages; automated local browser Create/Run reaches the persisted guided flow rather than legacy run.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-002 | Each displayed stage maps to actual backend work/state/protocol evidence. | Implementation: `robotops/integration/engine.py:310` (GuidedEngine._execute); `robotops/integration/engine.py:716` (GuidedEngine._advance_reserved). Current 9e83fe7 successful JUnit in both full suites: [N01](#n01), [N03](#n03). Historical a881acf first-pass successful JUnit: [A01](#a01), [A03](#a03). Historical 4774 first-pass successful JUnit: [J01](#j01), [J03](#j03). One stored step per authorized boundary and successful real-service scenarios retain stage results. Executed-symbol proof is additionally J19/J20, cited at LAB-MUST-020.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-003 | Authorization advances only the intended bounded stage. | Implementation: `robotops/integration/engine.py:710` (GuidedEngine.authorize); `robotops/integration/store.py:159` (IntegrationStore.reserve). Current 9e83fe7 successful JUnit in both full suites: [N01](#n01). Historical a881acf first-pass successful JUnit: [A01](#a01). Historical 4774 first-pass successful JUnit: [J01](#j01). The test walks all 22 boundaries, checks current stage/revision, forbids legacy run bypass and observes no robot journal before the physical gate.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-004 | Authorizations are idempotent/revision-guarded against double click/replay. | Implementation: `robotops/integration/store.py:159` (IntegrationStore.reserve); `robotops/integration/engine.py:1048` (GuidedEngine.reconcile). Current 9e83fe7 successful JUnit in both full suites: [N04](#n04), [N05](#n05). Historical a881acf first-pass successful JUnit: [A04](#a04), [A05](#a05). Historical 4774 first-pass successful JUnit: [J04](#j04), [J05](#j05). Concurrent same-request authorization replays one decision; stale revision and changed payload conflict. Reconciliation request hashing also rejects changed observation fault.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-005 | No DB transaction remains open while waiting for a human. | Implementation: `robotops/integration/store.py:159` (IntegrationStore.reserve); `robotops/integration/store.py:229` (IntegrationStore.finish); `robotops/integration/engine.py:716` (GuidedEngine._advance_reserved). Current 9e83fe7 successful JUnit in both full suites: [N01](#n01), [N04](#n04). Historical a881acf first-pass successful JUnit: [A01](#a01), [A04](#a04). Historical 4774 first-pass successful JUnit: [J01](#j01), [J04](#j04). Source control flow closes reserve transaction before handler execution and uses a separate finish transaction; persisted waiting/reloaded boundaries are exercised. Tests alone do not measure every live transaction lifetime.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-006 | Automatic and guided modes use the same stage handlers. | Implementation: `tools/integration_demo.py:38` (drive); `robotops/workflow/engine.py:174` (Engine.stage_dispatch); `robotops/integration/engine.py:310` (GuidedEngine._execute). Current 9e83fe7 successful JUnit in both full suites: [N06](#n06). Historical a881acf first-pass successful JUnit: [A06](#a06). Historical 4774 first-pass successful JUnit: [J06](#j06). The imported REST driver stops at stage 15 without consent, resumes the same session/command with consent and finishes exactly 22 steps/effect one. Source inspection confirms calls to the guided endpoints and shared core operations.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-007 | Existing correctness invariants and scenarios remain functional. | Implementation: `robotops/workflow/engine.py:233` (Engine.run); `robotops/workflow/engine.py:299` (Engine._reconcile); `robotops/verification/verifier.py:23` (Verifier.verify). Current 9e83fe7 successful JUnit in both full suites: [N07](#n07), [N08](#n08). Historical a881acf first-pass successful JUnit: [A07](#a07), [A08](#a08). Historical 4774 first-pass successful JUnit: [J07](#j07), [J08](#j08). The named legacy happy and before-effect-loss cases passed in both historical 4774 complete 799-case suites. The first-pass catalog locators are retained; final manual and remote obligations remain separate.  The later b968 full suite failed one teardown; C4 corrects the demonstrated transport-cleanup path and has focused 4/3/4 passing scopes. Historical a881 first suite passed all 815 cases, but its second suite had 814 passes and one failure; repeatability and whole acceptance failed. C5 has focused passing correction evidence. Both current 815-case suites and all 20 local gates passed; final manual/audit/remote closure remains PENDING. Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-008 | WMS-style versioned REST task intake exists with idempotency. | Implementation: `apps/api/guided.py:23` (mount_guided_routes); `robotops/integration/store.py:122` (IntegrationStore.create); `robotops/workflow/store.py:241` (Store.intake). Current 9e83fe7 successful JUnit in both full suites: [N04](#n04), [N03](#n03). Historical a881acf first-pass successful JUnit: [A04](#a04), [A03](#a03). Historical 4774 first-pass successful JUnit: [J04](#j04), [J03](#j03). Versioned /v1/wms/tasks intake persists stable request identity, replay/conflict semantics and lab recovery. The lab factory rejects legacy unbounded intake/run bypasses.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-009 | Integration-lab persistence uses PostgreSQL or a documented equivalent lab profile. | Implementation: `robotops/lab/postgres.py:99` (PostgreSQLStore.transaction); `robotops/lab/api.py:21` (create_app). Current 9e83fe7 successful JUnit in both full suites: [N09](#n09), [N03](#n03). Historical a881acf first-pass successful JUnit: [A09](#a09), [A03](#a03). Historical 4774 first-pass successful JUnit: [J09](#j09), [J03](#j03). Actual PostgreSQL repository intake and durable pending delivery were exercised; five guided scenarios used the real service-backed factory. No SQLite substitute is counted as PostgreSQL evidence.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-010 | Transactional outbox is real, not a log message. | Implementation: `robotops/workflow/store.py:595` (Store.prepare); `robotops/integration/store.py:318` (IntegrationStore.enqueue); `robotops/lab/transport.py:52` (DeliveryStore.enqueue). Current 9e83fe7 successful JUnit in both full suites: [N09](#n09). Historical a881acf first-pass successful JUnit: [A09](#a09). Historical 4774 first-pass successful JUnit: [J09](#j09). Store.prepare encloses command and application outbox writes in one transaction. The PostgreSQL test verifies committed pending delivery and payload conflict; it does not inject a transaction rollback despite its name.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-011 | RabbitMQ/AMQP path is real in lab mode. | Implementation: `robotops/lab/transport.py:212` (LabBridge.publish); `robotops/lab/transport.py:133` (EdgeAdapter.consume_one). Current 9e83fe7 successful JUnit in both full suites: [N10](#n10). Historical a881acf first-pass successful JUnit: [A10](#a10). Historical 4774 first-pass successful JUnit: [J10](#j10). Actual publisher-confirmed AMQP delivery, deliberately lost manual consumer ACK, broker redelivery and durable inbox processing occurred before OPC dispatch.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-012 | Publisher confirm and consumer ACK are represented distinctly. | Implementation: `robotops/lab/transport.py:212` (LabBridge.publish); `robotops/lab/transport.py:259` (LabBridge.edge_deliver); `robotops/lab/transport.py:87` (DeliveryStore.inbox). Current 9e83fe7 successful JUnit in both full suites: [N10](#n10). Historical a881acf first-pass successful JUnit: [A10](#a10). Historical 4774 first-pass successful JUnit: [J10](#j10). The test separately asserts publisher_confirm, consumer_ack_sent=false, broker redelivery, then consumer_ack_sent=true. Source stores outbox confirmed_at separately from inbox ack_sent.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-013 | Edge adapter persists/handles delivery identity robustly. | Implementation: `robotops/lab/transport.py:133` (EdgeAdapter.consume_one); `robotops/lab/transport.py:87` (DeliveryStore.inbox). Current 9e83fe7 successful JUnit in both full suites: [N10](#n10). Historical a881acf first-pass successful JUnit: [A10](#a10). Historical 4774 first-pass successful JUnit: [J10](#j10). A lost consumer ACK causes redelivery with deliveries=2; durable inbox identity is retained before ACK and duplicate delivery proceeds with the original command.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-014 | OPC UA client/server communication is real in lab mode. | Implementation: `robotops/lab/edge.py:71` (EdgeControl.begin); `robotops/lab/edge_rpc.py:17` (EdgeRPC.call); `robotops/lab/opcua.py:179` (OPCClient._call). Current 9e83fe7 successful JUnit in both full suites: [N11](#n11), [N12](#n12), [N13](#n13), [N14](#n14). Historical a881acf first-pass successful JUnit: [A11](#a11), [A12](#a12), [A13](#a13), [A14](#a14). Historical 4774 first-pass successful JUnit: [J11](#j11), [J12](#j12), [J13](#j13), [J14](#j14). Actual OPC browse/subscription/method calls, independent native edge process ownership and DataChangeNotification evidence passed. Slow ServerStatus.State preserves one session; sustained delay is bounded without another callback.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-015 | Virtual PLC has durable-enough command identity/journal semantics for demonstrated recovery. | Implementation: `robotops/lab/journal.py:150` (PLCJournal.begin); `robotops/lab/journal.py:183` (PLCJournal.result); `robotops/lab/journal.py:215` (PLCJournal.acknowledge). Current 9e83fe7 successful JUnit in both full suites: [N15](#n15), [N16](#n16). Historical a881acf first-pass successful JUnit: [A15](#a15), [A16](#a16). Historical 4774 first-pass successful JUnit: [J15](#j15), [J16](#j16). A real OPC server process restart cannot grant execution again; the separate result-ack race test rejects acknowledgement of a concurrently advanced sequence. This proves the implemented retained-journal model, not power-loss atomicity with hardware.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-016 | Same command ID + same payload cannot cause a second physical effect. | Implementation: `robotops/lab/journal.py:150` (PLCJournal.begin); `robotops/cell/runtime.py:293` (SyntheticRuntime._execute). Current 9e83fe7 successful JUnit in both full suites: [N10](#n10). Historical a881acf first-pass successful JUnit: [A10](#a10). Historical 4774 first-pass successful JUnit: [J10](#j10). Both same-payload redelivery cases prohibit a second callback; after-effect loss keeps effect_count=1 and before-effect loss stays 0. No exactly-once physical hardware guarantee is inferred.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-017 | Same command ID + different payload is rejected. | Implementation: `robotops/lab/journal.py:65` (PLCJournal.submit); `robotops/lab/journal.py:183` (PLCJournal.result). Current 9e83fe7 successful JUnit in both full suites: [N17](#n17). Historical a881acf first-pass successful JUnit: [A17](#a17). Historical 4774 first-pass successful JUnit: [J17](#j17). Changing cell_generation under the same command ID raises PAYLOAD_CONFLICT; result before authorization and mismatched acknowledgement sequence are rejected.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-018 | Console shows What/Wire/Code/State/Why/failure semantics. | Implementation: `apps/erp_ui/integration-console.js` (IntegrationConsole.inspect). Current 9e83fe7 successful JUnit in both full suites: [N02](#n02), [N18](#n18), [N38](#n38). Historical a881acf first-pass successful JUnit: [A02](#a02), [A18](#a18), [A38](#a38). Historical 4774 first-pass successful JUnit: [J02](#j02), [J18](#j18). Automated browser evidence covers guided flow, Code inspection and expandable/retry payload persistence. Source maps What/Wire/Code/State/Why/Failure semantics directly from a saved step. All six rendered views require the corrected-source final manual comparison; the historical comparison is retained separately.  Historical manual happy-review compared all six inspectors to saved data; the historical duplicate/WMS brief defect is explicitly retained as NOT PASS. Correction C1 covers all six supported distributed briefs.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-019 | Protocol and real-vs-simulated badges are accurate. | Implementation: `robotops/integration/engine.py:716` (GuidedEngine._advance_reserved); `apps/erp_ui/integration-console.js` (IntegrationConsole.render). Current 9e83fe7 successful JUnit in both full suites: [N03](#n03), [N02](#n02), [N38](#n38), [N39](#n39). Historical a881acf first-pass successful JUnit: [A03](#a03), [A02](#a02), [A38](#a38), [A39](#a39). Historical 4774 first-pass successful JUnit: [J03](#j03), [J02](#j02). Lab scenario assertions distinguish REAL PROTOCOL stages and actual WMS HTTP 503 from simulated runtime behavior; local browser shows stored trace. Final visual audit must include injected pre-wire failures and every displayed scope label.  Historical saved-trace audit verified 292 stored truth/protocol labels but found duplicate/WMS replay captions misleading; correction C2 fixes saved scenario labels and C3 guards live identity. Recorded scenario configuration is not execution/effect proof.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-020 | Source references point to code that actually executes. | Implementation: `robotops/integration/engine.py:716` (GuidedEngine._advance_reserved); `robotops/lab/edge_rpc.py:17` (EdgeRPC.call). Current 9e83fe7 successful JUnit in both full suites: [N03](#n03), [N19](#n19), [N20](#n20). Historical a881acf first-pass successful JUnit: [A03](#a03), [A19](#a19), [A20](#a20). Historical 4774 first-pass successful JUnit: [J03](#j03), [J19](#j19), [J20](#j20). Local happy/lost-ACK and full lab profilers record actual called (file, symbol) pairs, require each displayed source to appear in those calls and compare excerpts to the file. Lab source proof also checks the complete two-line opc_connect boundary.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-021 | Payloads are derived from actual execution data and secrets are redacted. | Implementation: `robotops/integration/store.py:27` (sanitize); `robotops/integration/engine.py:716` (GuidedEngine._advance_reserved). Current 9e83fe7 successful JUnit in both full suites: [N21](#n21). Historical a881acf first-pass successful JUnit: [A21](#a21). Historical 4774 first-pass successful JUnit: [J21](#j21). Nested secret keys, credential URLs, auth text and synthetic key material are sanitized; injected exception secrets are absent from response and reloaded persisted session. Trace construction uses actual handler results. Final live UI/log inspection remains separate.  Historical complete saved-text audit scanned 198,471,933 bytes and found no credential candidates within its defined scope. Correction C3 excludes unrelated command data from live presentation. Current-source final trace/log audit remains pending.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-022 | Architecture mini-map follows the current stage. | Implementation: `apps/erp_ui/integration-console.js` (IntegrationConsole.render). Current 9e83fe7 successful JUnit in both full suites: [N02](#n02). Historical a881acf first-pass successful JUnit: [A02](#a02). Historical 4774 first-pass successful JUnit: [J02](#j02). Source chooses current map group from session.current_stage, independently of a pinned historical step. The mapped happy browser case is contextual evidence only: it does not assert mini-map position. Final all-boundary/current-versus-pinned manual proof is pending.  Historical manual captures covered eight map groups/50 boundaries; transient stage 16 had no standalone screenshot (Robot group was captured at 17). This is a retained limitation, not claimed evidence for every transient frame.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-023 | In-progress session survives browser reload. | Implementation: `apps/erp_ui/integration-console.js` (IntegrationConsole.load); `robotops/integration/store.py:102` (IntegrationStore.get). Current 9e83fe7 successful JUnit in both full suites: [N02](#n02), [N39](#n39). Historical a881acf first-pass successful JUnit: [A02](#a02), [A39](#a39). Historical 4774 first-pass successful JUnit: [J02](#j02). Automated local synthetic and Blender browser reloads preserve session ID and revision at stage 10, then finish the original command. Final manual reload journey remains pending.  Historical manual happy reload preserved full saved session identity. Correction C2 also tests saved per-job scenario persistence across reload and earlier order lines.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-024 | Final physical gate precedes robot side effect. | Implementation: `robotops/integration/engine.py:310` (GuidedEngine._execute); `robotops/integration/store.py:159` (IntegrationStore.reserve). Current 9e83fe7 successful JUnit in both full suites: [N01](#n01), [N02](#n02). Historical a881acf first-pass successful JUnit: [A01](#a01), [A02](#a02). Historical 4774 first-pass successful JUnit: [J01](#j01), [J02](#j02). The backend requires stage-15 physical authorization; tests prove no command journal before it, reject bypass, then observe exactly one effect after stage 16. Final manual gate evidence remains pending.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-025 | 3D viewer runs only after that gate and post-execution flow returns to verification/reconciliation. | Implementation: `apps/erp_ui/integration-console.js` (IntegrationConsole.advance); `apps/erp_ui/playback.js`; `robotops/integration/engine.py:310` (GuidedEngine._execute). Current 9e83fe7 successful JUnit in both full suites: [N02](#n02), [N22](#n22), [N38](#n38), [N39](#n39). Historical a881acf first-pass successful JUnit: [A02](#a02), [A22](#a22), [A38](#a38), [A39](#a39). Historical 4774 first-pass successful JUnit: [J02](#j02), [J22](#j22). Automated synthetic and Blender browser cases exercise the post-consent live/motion views, effect one, and subsequent verification/reconciliation/business flow. Final manual phase-B usability and return-to-console evidence remains pending.  Correction C2 binds replay captions to persisted per-job configuration; correction C3 clears previous protocol text before a newly authorized command can display it. No physical or gate semantics changed.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-026 | Read-only viewing/streaming cannot mutate robot/workflow state. | Implementation: `apps/api/guided.py:23` (mount_guided_routes); `robotops/workflow/store.py:112` (Store.readonly_connect); `robotops/lab/postgres.py:106` (PostgreSQLStore.readonly_connect). Current 9e83fe7 successful JUnit in both full suites: [N23](#n23), [N24](#n24), [N25](#n25), [N18](#n18), [N37](#n37), [N38](#n38), [N39](#n39). Historical a881acf first-pass successful JUnit: [A23](#a23), [A24](#a24), [A25](#a25), [A18](#a18), [A37](#a37), [A38](#a38), [A39](#a39). Historical 4774 first-pass successful JUnit: [J23](#j23), [J24](#j24), [J25](#j25), [J18](#j18). GET/WebSocket inspection preserves revision/state; six deleted-file reads do not recreate SQLite, four clear/delete stream cases close with lifecycle codes, and payload expansion emits no mutating requests. Native PostgreSQL read-only transactions are explicit in source.  Correction C2 metadata lookup uses readonly_connect without guided-store initialization, and C3 delayed response/error tests assert no mutation requests.  C4 also tests clean termination of read-only WebSocket connections under actual/injected peer resets; workflow state semantics were not changed. Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-027 | ACK-before-effect loss scenario is demonstrated. | Implementation: `robotops/cell/runtime.py:293` (SyntheticRuntime._execute); `robotops/integration/engine.py:1048` (GuidedEngine.reconcile). Current 9e83fe7 successful JUnit in both full suites: [N10](#n10). Historical a881acf first-pass successful JUnit: [A10](#a10). Historical 4774 first-pass successful JUnit: [J10](#j10). The [DROP_ACK_BEFORE_EFFECT-0] real-protocol case reaches an uncertain retained claim with runtime effect 0; querying/reporting the original journal permits no replacement execution.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-028 | ACK-after-effect loss scenario reaches uncertainty/reconciliation without duplicate physical action. | Implementation: `robotops/cell/runtime.py:293` (SyntheticRuntime._execute); `robotops/workflow/engine.py:299` (Engine._reconcile). Current 9e83fe7 successful JUnit in both full suites: [N10](#n10), [N22](#n22). Historical a881acf first-pass successful JUnit: [A10](#a10), [A22](#a22). Historical 4774 first-pass successful JUnit: [J10](#j10), [J22](#j22). The [DROP_ACK_AFTER_EFFECT-1] real-protocol case retains effect 1 and refuses another execution callback. Automated synthetic/Blender browser reconciliation keeps the original command and one effect.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-029 | Duplicate/redelivery scenario proves effect_count remains one. | Implementation: `robotops/lab/transport.py:133` (EdgeAdapter.consume_one); `robotops/lab/journal.py:150` (PLCJournal.begin); `robotops/cell/runtime.py:293` (SyntheticRuntime._execute). Current 9e83fe7 successful JUnit in both full suites: [N10](#n10). Historical a881acf first-pass successful JUnit: [A10](#a10). Historical 4774 first-pass successful JUnit: [J10](#j10). Real consumer redelivery and repeated OPC SubmitJob/BeginExecution preserve identity; the after-effect case asserts one runtime step and effect_count=1. Before-effect case correctly remains 0.  Historical manual duplicate publication had broker redelivered=false and two deliveries/effect one; it is described as duplicate publication, separately from J10 broker redelivery. The erroneous replay caption is preserved in the archive and corrected under C1/C2.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-030 | OPC UA/network interruption has deterministic documented behavior. | Implementation: `robotops/lab/edge.py:71` (EdgeControl.begin); `robotops/lab/journal.py:150` (PLCJournal.begin); `robotops/integration/engine.py:975` (GuidedEngine._recover_unstarted_dispatch). Current 9e83fe7 successful JUnit in both full suites: [N26](#n26), [N27](#n27), [N28](#n28), [N29](#n29), [N30](#n30), [N15](#n15), [N16](#n16), [N13](#n13), [N14](#n14). Historical a881acf first-pass successful JUnit: [A26](#a26), [A27](#a27), [A28](#a28), [A29](#a29), [A30](#a30), [A15](#a15), [A16](#a16), [A13](#a13), [A14](#a14). Historical 4774 first-pass successful JUnit: [J26](#j26), [J27](#j27), [J28](#j28), [J29](#j29), [J30](#j30), [J15](#j15), [J16](#j16), [J13](#j13), [J14](#j14). Broker/OPC failure prevents callback; boot change before intent returns to checks and renewed consent, after intent stays uncertain; interrupted no-intent dispatch safely rewinds. Real process restart, ACK sequence race and slow/stalled OPC probes retain one execution claim.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-031 | Inconclusive observation can prevent false success. | Implementation: `robotops/verification/verifier.py:23` (Verifier.verify); `robotops/workflow/engine.py:56` (Engine._observe); `robotops/integration/engine.py:1048` (GuidedEngine.reconcile). Current 9e83fe7 successful JUnit in both full suites: [N31](#n31). Historical a881acf first-pass successful JUnit: [A31](#a31). Historical 4774 first-pass successful JUnit: [J31](#j31). Stale/missing post-observation first produces uncertainty rather than success; original-command reconciliation with fresh evidence completes only when provable. Before-effect loss yields verified failure with zero effect.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-032 | WMS outage after verified execution retries business reconciliation, not robot motion. | Implementation: `robotops/lab/transport.py:328` (LabBridge.reconcile_business); `robotops/integration/store.py:251` (IntegrationStore.complete_business); `robotops/workflow/store.py:335` (Store._order). Current 9e83fe7 successful JUnit in both full suites: [N03](#n03), [N32](#n32), [N33](#n33). Historical a881acf first-pass successful JUnit: [A03](#a03), [A32](#a32), [A33](#a33). Historical 4774 first-pass successful JUnit: [J03](#j03), [J32](#j32), [J33](#j33). A real REST WMS 503 is retried as business reconciliation only. Guided order stays RECONCILING through physical verification/WMS wait and becomes COMPLETED at ERP stage 21 only after durable acknowledgements for every line; effect count stays one.  The historical WMS test passed physical/business semantics but its replay caption was misleading. Correction C2 and the focused WMS browser case prove the saved WMS scenario caption without changing recovery semantics.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-033 | UNKNOWN_OUTCOME is visible and explainable. | Implementation: `apps/erp_ui/integration-console.js` (IntegrationConsole.render); `robotops/integration/engine.py:1048` (GuidedEngine.reconcile). Current 9e83fe7 successful JUnit in both full suites: [N22](#n22). Historical a881acf first-pass successful JUnit: [A22](#a22). Historical 4774 first-pass successful JUnit: [J22](#j22). Automated lost-ACK browsers assert UNKNOWN_OUTCOME, blocked ordinary advance and explanatory text that reconciliation queries original journal/fresh observation without a new pick. Final manual legibility check remains pending.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-034 | Reconciliation queries the original command instead of issuing a fresh pick. | Implementation: `robotops/integration/engine.py:1048` (GuidedEngine.reconcile); `robotops/workflow/engine.py:299` (Engine._reconcile). Current 9e83fe7 successful JUnit in both full suites: [N22](#n22). Historical a881acf first-pass successful JUnit: [A22](#a22). Historical 4774 first-pass successful JUnit: [J22](#j22). Automated lost-ACK browsers reconcile the original command ID and journal while retaining effect one; backend source uses original-command query and new observation, with no new dispatch branch.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-035 | Unit tests cover new state/domain logic. | Implementation: `robotops/integration/models.py`; `robotops/integration/store.py:159` (IntegrationStore.reserve); `robotops/integration/engine.py:710` (GuidedEngine.authorize). Current 9e83fe7 successful JUnit in both full suites: [N01](#n01), [N04](#n04), [N37](#n37), [N38](#n38), [N39](#n39). Historical a881acf first-pass successful JUnit: [A01](#a01), [A04](#a04), [A37](#a37), [A38](#a38), [A39](#a39). Historical 4774 first-pass successful JUnit: [J01](#j01), [J04](#j04). Focused state/domain assertions test bounded transitions, physical permission, revision CAS, replay and conflict behavior through guided integration fixtures. These files live under tests/integration, not tests/unit; the evidence is the inspected assertions, not a directory-name claim.  Additional correction tests C2 cover the ExecutionScenario read model and missing/invalid/legacy cases; C3 covers delayed live response/error identity and clear transitions.  C4 adds four permanent HTTP/WebSocket lifecycle regressions using the product loop factory; their scoped receipt is separate from full acceptance. Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-036 | Integration tests cover DB/outbox/broker/edge/OPC UA/virtual PLC path. | Implementation: `robotops/lab/postgres.py:88` (PostgreSQLStore); `robotops/lab/transport.py:202` (LabBridge); `robotops/lab/edge.py:56` (EdgeControl); `robotops/lab/opcua.py:20` (VirtualPLC). Current 9e83fe7 successful JUnit in both full suites: [N10](#n10), [N03](#n03), [N12](#n12). Historical a881acf first-pass successful JUnit: [A10](#a10), [A03](#a03), [A12](#a12). Historical 4774 first-pass successful JUnit: [J10](#j10), [J03](#j03), [J12](#j12). Actual PG/AMQP/edge REST/OPC/virtual PLC cases and all five guided network scenarios passed. Four native browser cases additionally launch independent API/edge/WMS/PLC processes; the edge PID is distinct from API and matches stage evidence.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-037 | Browser E2E test drives a complete guided happy path through authorization -> 3D execution -> verification -> reconciliation. | Implementation: `apps/erp_ui/integration-console.js` (IntegrationConsole.advance); `tools/lab_stack.py:163` (LabStack.start). Current 9e83fe7 successful JUnit in both full suites: [N02](#n02), [N12](#n12). Historical a881acf first-pass successful JUnit: [A02](#a02), [A12](#a12). Historical 4774 first-pass successful JUnit: [J02](#j02), [J12](#j12). Automated happy browser cases passed for local synthetic and Blender runtimes and for the native independent-process lab (empty-parameter case). They cover consent, phase-B/3D, observation, verification and WMS/ERP completion. Mandatory final manual journey is still pending.  The later C4 focused lane passed guided Blender happy/reload and separate-service lab Blender happy; these are automated cases, not the final manual journey. Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-038 | Browser/integration E2E test drives at least ACK-after-effect/UNKNOWN_OUTCOME/reconciliation. | Implementation: `apps/erp_ui/integration-console.js` (IntegrationConsole.reconcile); `robotops/integration/engine.py:1048` (GuidedEngine.reconcile). Current 9e83fe7 successful JUnit in both full suites: [N22](#n22), [N12](#n12). Historical a881acf first-pass successful JUnit: [A22](#a22), [A12](#a12). Historical 4774 first-pass successful JUnit: [J22](#j22), [J12](#j12). Automated local synthetic/Blender and native independent-process browser DROP_ACK_AFTER_EFFECT cases observe UNKNOWN_OUTCOME, reconcile the original command and finish with effect one. This is automated browser evidence, not the final manual loop.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-039 | Browser reload/resume is tested. | Implementation: `apps/erp_ui/integration-console.js` (IntegrationConsole.load); `robotops/integration/store.py:102` (IntegrationStore.get). Current 9e83fe7 successful JUnit in both full suites: [N02](#n02). Historical a881acf first-pass successful JUnit: [A02](#a02). Historical 4774 first-pass successful JUnit: [J02](#j02). Automated local synthetic/Blender browser tests reload mid-session and finish the same durable authority/command. Native browser reload assertions are supplementary in J12; final manual evidence is pending.  Correction C2 additionally verifies persisted scenario metadata after reload; this is separate from executing a new final manual journey.  C4 focused guided Blender reload and desktop close/reopen cases passed with strict clean shutdown; final manual reload remains pending. Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-040 | Double authorization/idempotency is tested. | Implementation: `robotops/integration/store.py:159` (IntegrationStore.reserve); `robotops/integration/engine.py:1048` (GuidedEngine.reconcile). Current 9e83fe7 successful JUnit in both full suites: [N04](#n04), [N05](#n05). Historical a881acf first-pass successful JUnit: [A04](#a04), [A05](#a05). Historical 4774 first-pass successful JUnit: [J04](#j04), [J05](#j05). Concurrent double authorization, exact replay, stale revision, changed authorization payload and changed recovery-fault payload are asserted. Native physical-request replay also occurs in J12 without a second effect.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-041 | Duplicate AMQP/OPC command does not duplicate physical effect and is asserted. | Implementation: `robotops/lab/transport.py:133` (EdgeAdapter.consume_one); `robotops/lab/journal.py:150` (PLCJournal.begin); `robotops/cell/runtime.py:293` (SyntheticRuntime._execute). Current 9e83fe7 successful JUnit in both full suites: [N10](#n10). Historical a881acf first-pass successful JUnit: [A10](#a10). Historical 4774 first-pass successful JUnit: [J10](#j10). The actual AMQP/OPC duplicate test asserts broker redelivery, repeated SubmitJob, a rejected second execution callback and unchanged runtime effect count.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-042 | Existing test suite passes. | Implementation: `tools/dev.py`; `pyproject.toml`. Current 9e83fe7 successful JUnit in both full suites: [N07](#n07). Historical a881acf first-pass successful JUnit: [A07](#a07). Historical 4774 first-pass successful JUnit: [J07](#j07). Both historical 4774 complete suites passed 799/799 with 0 failures/errors/skips; JUnit times 1807.596s and 1648.556s, coverage 91.38351792753895% and 91.43983480382954%. Repeatability verifies identical case sets/outcomes. Exact artifacts are below. J07 is one mapped case, not a substitute for these whole-suite results.  Subsequent b968 acceptance failed (810 clean JUnit cases plus one teardown error); C4 scoped corrections passed. Historical a881 first suite passed 815/815 with no failures/errors/skips in 1649.157 s, coverage 91.41791044776119%; its second suite had 814 passes and one failure, so whole acceptance/repeatability failed. C5 passed four existing parameterized cases and one controlled repeat. Both current 815-case suites passed in 1649.757/1675.043s, coverage 91.38059701492537/91.43656716417911%; repeatability and all 20 local gates passed. Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-043 | Lint/type checks pass at repository policy level. | Implementation: `tools/dev.py`; `pyproject.toml`. Current 9e83fe7 successful JUnit in both full suites: [N34](#n34). Historical a881acf first-pass successful JUnit: [A34](#a34). Historical 4774 first-pass successful JUnit: [J34](#j34). The mapped governance test passed its reference/status drift check; it is not lint or typecheck evidence. Historical 4774 completed gates prove lint/format PASS (192 files formatted), strict typecheck PASS (66 source files) and configured security PASS; exact logs are indexed by the historical acceptance manifest.  The correction archive separately records focused Ruff seven-file and mypy two-file checks, followed by root repository lint/format (198 files), mypy (66 files) and drift (169 MUSTs); these pre-commit checks do not replace current frozen-run gates.  C4 repository focused checks subsequently passed lint/format 201 files, mypy 67 source files and drift 169 MUSTs. Historical a881 finished 18 of 20 local gates, including configured checks; tests_2 and repeatability failed. Current lint/format 204 files, strict typing of 67 source files and configured security passed; raw Bandit retains five reviewed exceptions. Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-044 | CI runs the relevant tests or documents any environment-specific Blender limitation with a deterministic headless substitute. | Implementation: `.github/workflows/ci.yml`. Current 9e83fe7 successful JUnit in both full suites: [N03](#n03). Historical a881acf first-pass successful JUnit: [A03](#a03). Historical 4774 first-pass successful JUnit: [J03](#j03). Workflow source configures PostgreSQL 17, RabbitMQ 4, locked dependencies, Chromium and pinned CPU Blender, then tools.dev acceptance --local. J03 proves local protocol execution only. Exact-source remote CI conclusion/URL remains PENDING.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-045 | Docker/integration-lab startup has a documented smoke test and health checks. | Implementation: `tools/lab_stack.py:163` (LabStack.start); `tools/lab_stack.py:94` (LabStack.healthy); `tools/lab-services.ps1`; `compose.yaml`. Current 9e83fe7 successful JUnit in both full suites: [N03](#n03), [N12](#n12). Historical a881acf first-pass successful JUnit: [A03](#a03), [A12](#a12). Historical 4774 first-pass successful JUnit: [J03](#j03), [J12](#j12). J12 starts and health-probes the independent native API/edge/WMS/PLC stack against live PostgreSQL/RabbitMQ; J03 covers network behavior. Native startup is exercised; compose.yaml is an inspected deployment recipe, not an executed Docker profile. Final clean manual smoke remains PENDING.  Historical manual stack receipts exist in docs/evidence/lab-4774af5/manual; the final corrected-source clean stack remains pending.  C4 wires the same HTTP loop into real native API/WMS/edge and desktop entrypoints plus test fixtures, with the 512-socket Windows Selector limit documented. Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-046 | README architecture matches implementation. | Implementation: `README.md`; `docs/integration-lab.md`; `robotops/lab/edge_rpc.py:36` (EdgeRPC.execute). Current 9e83fe7 successful JUnit in both full suites: [N34](#n34). Historical a881acf first-pass successful JUnit: [A34](#a34). Historical 4774 first-pass successful JUnit: [J34](#j34). README/lab architecture describes durable guided coordination, separate edge-owned OPC and simulated API runtime callback. The mapped drift test validates references/status, not prose semantics. Final documentation-to-source review remains PENDING.  C4 native/desktop docs now match the explicit shared HTTP loop and its limits; final whole-document review remains pending. Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-047 | Clearly label simulated vs real-protocol components. | Implementation: `README.md`; `docs/integration-lab.md`; `robotops/integration/engine.py:716` (GuidedEngine._advance_reserved). Current 9e83fe7 successful JUnit in both full suites: [N34](#n34). Historical a881acf first-pass successful JUnit: [A34](#a34). Historical 4774 first-pass successful JUnit: [J34](#j34). README/lab docs and trace construction distinguish real SQL/AMQP/OPC/REST from virtual systems/runtime/sensors. The mapped drift case does not validate every label; final text/UI truth review remains PENDING.  Correction C1/C2 distinguish saved scenario configuration from actual protocol/effect evidence; C3 rejects mismatched live identity. Historical false captions remain historical NOT PASS.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-048 | Document local fast mode and full integration-lab mode. | Implementation: `docs/integration-lab.md`; `docs/integration-lab-native.md`; `robotops/lab/api.py:21` (create_app). Current 9e83fe7 successful JUnit in both full suites: [N34](#n34). Historical a881acf first-pass successful JUnit: [A34](#a34). Historical 4774 first-pass successful JUnit: [J34](#j34). Main/native guides describe fast SQLite simulated transport and full real-service lab startup, ports and health. Governance execution only proves link/status consistency; final command/documentation review remains PENDING. No Docker run is implied.  Current native commands include --loop robotops.http_server:new_event_loop; Windows Selector scope/limits are documented, without claiming a Docker run. Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-049 | Document all acknowledgement meanings and uncertainty model. | Implementation: `docs/integration-lab.md`; `robotops/integration/engine.py:310` (GuidedEngine._execute); `robotops/lab/journal.py:215` (PLCJournal.acknowledge). Current 9e83fe7 successful JUnit in both full suites: [N34](#n34). Historical a881acf first-pass successful JUnit: [A34](#a34). Historical 4774 first-pass successful JUnit: [J34](#j34). The lab guide and stage-22 summary distinguish HTTP acceptance, DB commit, publisher confirm, consumer ACK, PLC acceptance, controller success, verification, WMS ACK and ERP completion. Drift test is supplementary; final semantic documentation review remains PENDING.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-050 | Include a reproducible demo script for happy path and lost-ACK recovery. | Implementation: `tools/integration_demo.py:38` (drive); `tools/integration_demo.py:144` (main); `README.md`. Current 9e83fe7 successful JUnit in both full suites: [N35](#n35). Historical a881acf first-pass successful JUnit: [A35](#a35). Historical 4774 first-pass successful JUnit: [J35](#j35). The imported REST demo driver lost-ACK case completes with one effect, one reconciliation and exactly one gateway COMMAND_DISPATCHED event; happy/consent/resume is J06. Current-source final CLI invocation/output artifacts remain PENDING.  Historical exact README CLI happy/lost-ACK commands now have archived cli-review.json: both completed with the original command and effect one, revisions 44/46. These are 4774 executions, not current-source CLI proof.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |
| LAB-MUST-051 | No claim implies proprietary SICS.AI knowledge, exact HKM1800 behavior, or safety certification. | Implementation: `README.md`; `docs/integration-lab.md`; `robotops/domain/ports.py`. Current 9e83fe7 successful JUnit in both full suites: [N36](#n36). Historical a881acf first-pass successful JUnit: [A36](#a36). Historical 4774 first-pass successful JUnit: [J36](#j36). Docs identify independent synthetic scope and disclaim proprietary architecture, exact hardware behavior and certification. The mapped test checks domain/brain/verifier import boundaries only; final claims/UI/publication wording audit remains PENDING.  The historical PDF/HTML visual review explicitly retained NOT DONE and synthetic scope; current rebuilt PDF/HTML verification remains pending.  Current automated mapping PASS in terminal manifest; both suites/all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING. **Final criterion: PENDING.** |

## Current 9e83fe7 exact successful two-suite JUnit catalog

N01-N36 provide 61 mapped cases and N37-N39 add 16 correction cases. All 77 selected unique cases passed in each complete 815-case suite, not an additional count. Each outcome/identity/duration below was resolved from both actual current JUnits. Both suites, repeatability and all 20 local gates PASS. Final manual/full archive/PDF/remote proof remains PENDING.

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

Exact GOAL action text is preserved. Final report must contain criterion -> implementation evidence, exact tests/results, E2E scenarios, remaining limitations, intentionally simulated components and final commit SHA.

| Step | Required action | Current result / retained evidence |
| --- | --- | --- |
| 1 | Re-read this entire `GOAL.md`. | PENDING final entire-GOAL reread on completed source; this preparation verifies exact 51/14 texts only. |
| 2 | Build a checklist from every Definition of Done item. | Prepared exact 51-row checklist and 14-step ledger; final evidence/status confirmation PENDING. Non-checkbox clauses remain binding. |
| 3 | Inspect the implementation, not just test names, and map each item to concrete files/symbols/tests. | Concrete implementation map, current N77 two-suite locators/durations and secondary historical A/J catalogs retained. Independent terminal/first-case reviews cited; final manual/full archive/PDF/remote reconciliation PENDING. |
| 4 | Start the complete integration-lab stack from a clean state. | PENDING separate fresh manual stack review. Automated native independent-process lab coverage passed; no Compose execution claim. |
| 5 | Run the full automated unit/integration/E2E suite. | PASS local automated obligation: two complete 815-case suites, zero failure/error/skip, same identities/outcomes; coverage 91.38059701492537/91.43656716417911%; all 20 local gates passed. Manual and remote work remain separate. |
| 6 | Execute the guided happy path in a real browser and verify the 3D handoff and post-execution reconciliation. | PENDING current manual happy path, Blender handoff and post-execution reconciliation. |
| 7 | Execute the lost-ACK-after-effect scenario and prove from persisted command/effect evidence that reconciliation does not execute the physical pick twice. | PENDING current manual lost-ACK journey with original command/receipt and effect-one proof; no physical resend. |
| 8 | Reload the browser mid-session and verify safe resume. | PENDING current manual mid-session reload with unchanged IDs/revision and no auto-resume. |
| 9 | Trigger duplicate authorization/delivery and verify idempotency. | PENDING current duplicate authorization/delivery and unchanged command/effect proof; use only new runtime IDs. |
| 10 | Check logs/trace UI for secret leakage and misleading “real” labels. | PENDING current complete trace/log/visual secret and truthful-label review. Older audited evidence retains its own scope and known failures. |
| 11 | Run lint/type/security checks configured by the repository. | PASS current configured checks: lint/format 204 files, strict typing of 67 source files, configured security with five reviewed raw Bandit findings, dependency audits/vendor integrity, drift and builds. Full trace/publication-payload audit PENDING. |
| 12 | Fix every failure found, then repeat the relevant tests. | Focused C5 correction and both clean full815-case suites passed; no current local gate failure remains. Any new findings from manual/full archive/PDF/remote review still require correction and relevant rechecks. |
| 13 | Update documentation to match what actually exists. | Local drift and publication builds PASS; metadata retains source9e83fe7,64pages and NOT DONE. Final docs/README CLI alignment, actual PDF/HTML visual review and published-source reconciliation PENDING. |
| 14 | Produce a final completion report containing: | This preparation exists; final criterion-to-evidence/test/E2E results, limitations, simulated components and independently attested final SHA remain PENDING. |

## Acceptance evidence fields

- Record the exact command, start/end UTC, exit code, duration and log/artifact path for every gate. Preserve the original manifest, environment, source hash, lock hash and clean/dirty flag.
- Read both `tests-1.xml` and `tests-2.xml`: total/pass/fail/error/skip counts, parameterized lab and synthetic/Blender browser cases, source-profiler assertions, boot recovery and business/read-only regressions. Report exact counts per run; never add overlapping focused runs.
- Record coverage percentage/threshold and artifact; lint, format, strict typing, Bandit, dependency audits, vendored JS integrity, contract/drift checks and publication builder results.
- Record every required Blender demo scenario, runtime binary/version, result/effect evidence and failed-attempt archives. A successful local build is not a remote deployment.
- After the run finishes, verify that the resulting manifest still identifies this frozen source. Document any later implementation/test change and the appropriate refreshed evidence; do not claim unchanged-source acceptance after a mutation.

## Current manual preparation, not execution evidence

The [manual launcher](run-manual-lab-9e83fe7.ps1), [runbook](manual-9e83fe7-runbook.md) and [preparation receipt](manual-9e83fe7-preparation.json) define the controlled process; their preparation checks do not prove a manual journey. Root is handling fresh manual work separately, which remains PENDING here. The launcher requires explicit `-RunManual`, exact commit/fingerprint/campaign start, terminal exit0 and all 20 local gates, two clean nonempty matching JUnits and both coverage results >=85 percent. It refuses existing report/data/manual evidence. Root must first review terminal campaign evidence and ensure no runtime overlap. New paths are `artifacts/lab-final-9e83fe7*` and `artifacts/final-manual-9e83fe7/`; actual new IDs/PIDs/URLs are deliberately absent until launch.

## Manual trace/UI data to retain

- For every journey: UTC, browser/runtime, source hash, API origin, saved session JSON, order/job/command/session/correlation IDs, screenshots and trace/network logs. Use one new namespace per clean run; retain failures.
- Happy path: zero journal/effect before stage 15 consent, one effect after stage 16, independent verification, WMS ACK and ERP stage-21 transition. WMS outage must leave business status pending without another pick.
- Inspect selected saved stages against rendered What/Wire/Code/State/Why/Failure semantics. The What JSON must equal summary/component/protocol/classification/status/evidence IDs; Wire equals input/output/wire; Code equals the executing source reference with clipped excerpt; State equals before/after/persistence/revision; Why and Failure equal their stored strings.
- Mini-map selector `#integration-map li[aria-current="step"]`: exactly one current group. Stages 1-2 ERP/WMS; 3-4 REST/SQL; 5-8 Observe/plan; 9-11 Outbox/edge; 12-15 OPC UA/PLC; 16-17 Robot; 18-19 Verify; 20-22 Business. It follows current stage, not a pinned historical inspector row.
- Retain phase-B live OPC DataChangeNotification evidence and distinct read-only motion recording. The code/trace labels must not imply live measured joint telemetry, real safety control or a proprietary robot implementation.
- Lost-ACK/duplicate/restart: preserve original payload hash, acceptance/validated/current boot IDs, result sequence/history, physical execution claim, receipt and effect counts. A reboot found before dispatch renews checks/consent; a restart after intent stays conservative.
- Check all six distributed briefs and recorded replay captions against saved session configuration; changing the next-order dropdown must not rewrite historical captions. Keep saved configuration distinct from dispatch/result evidence. Exercise late live-response identity rejection or retain its current regression evidence.
- Prove inspection-only actions make no mutation requests and leave session revision, command identity and effect count unchanged. Include reload and archived/deleted/cleared-session behavior as exercised by current tests.

## ADR 0002 publication sequence (root only, after authorization)

1. Finish all local and manual work and make the exact proposed public commit reviewable. Request explicit publication approval; do not treat elapsed time or the earlier auto-review rejection as approval.
2. After authorization, publish the intended source and verify successful `ci.yml` and `publish-reports.yml` runs for that exact SHA. Verify public `build.json.source_commit` matches and expected HTML/source/PDF links return valid content; retain workflow IDs/URLs/conclusions and artifact hashes.
3. Run `uv run --locked python -m tools.dev acceptance --refresh-remote docs/evidence/acceptance/20261006T024719/manifest.json` only when its exact source is independently attested. It preserves `local-manifest.json` and adds timestamped remote evidence; it does not rerun or upgrade local results.
4. Synchronize DONE only after every MUST and all three gates (`ci`, `publication_remote`, `pages`) pass. The generated report/build must retain audited-source identity; never hand-edit generated PDFs/Pages.
5. Any evidence/status successor gets complete CI/publication again. Verify that successor explicitly and cite its final SHA from independent CI/public `build.json`; the committed report cannot contain its own hash. Do not create an endless chain of commits just to rewrite the self-hash.

## Remaining limitations to state concretely

- Independent synthetic industrial-integration simulator, not proprietary SICS.AI architecture, exact HKM1800 behavior, safety certification or a real hardware performance claim.
- Real PostgreSQL/AMQP/OPC UA/business REST; synthetic ERP/WMS semantics, virtual PLC, simulated controller callback, simulated robot/world/sensors and read-only replay. Blender evidence demonstrates the implemented adapter, not validated contact dynamics.
- Native Windows stack is the exercised profile when Docker/WSL is absent. Distinguish actual native smoke evidence from the inspected Compose recipe; do not claim a Docker run that did not occur.
- Anonymous/local development protocol settings and explicit retained-memory model are documented; no exactly-once physical guarantee is made. Unprovable outcomes remain uncertain/intervention rather than granting another pick.
- Publication and exact-final-SHA remote gates remain pending until authorized and verified. Report partial local success separately from repository DONE.

## Bounded terminal-update scope

This is a new local-acceptance snapshot. The [first-pass report](final-report-9e83fe7-preparation.md), its author receipt and independent review stay byte-identical; the initial-pending snapshot remains preserved. All 51 exact requirements and 14 final actions are unchanged. N77 cases resolve in both complete clean JUnits with actual per-run durations; historical A77/J61 remain unchanged. The manifest supplies 20 local PASS gates and 163 local MUST results, with six remote-only MUSTs unresolved. The independent terminal review supplies its bounded 51-input/core-demo/publication-metadata cross-check; this author did not repeat a broad payload scan.

Fresh manual browser/CLI/reload/idempotency, full current archive/log/trace/secret and truthful-label audit, actual PDF/HTML visual review, and exact-source CI/publication/Pages remain PENDING. No tracked edits or runtime/browser/service/test/database/PDF/rendering/broadscan actions occurred. Overall **NOT ACHIEVED** remains binding. The [author receipt](final-report-9e83fe7-local-preparation-review.json) binds direct saved inputs and the upstream review's scope/limitations.
