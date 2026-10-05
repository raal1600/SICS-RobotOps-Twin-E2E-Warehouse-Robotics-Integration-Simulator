# Integration Lab implementation and evidence audit

Audited against the entire root `GOAL.md` on 2026-10-05. The goal remains authoritative. This replaces the initial proposal with inspected files, symbols and tests. Checked items have focused evidence; unchecked items await final evidence on the completed tree. Neither file existence nor historical simulator acceptance proves the new goal. Final commands, browser artifacts and source commit belong in the completion report. The mandatory final loop remains open.

## Implemented architecture

`apps/api/guided.py:mount_guided_routes` exposes versioned WMS intake and session authorization/reconciliation/read endpoints. `robotops/integration/engine.py:GuidedEngine` persists a reservation, executes one bounded handler, then persists its result. `IntegrationStore.reserve` compares revision/stage and stores an idempotent `AuthorizationDecision` before work. No transaction spans a human wait, network operation or runtime call. `ExecutionSession` and its steps survive process/browser reload.

`robotops/workflow/engine.py:Engine.stage_*` contains reusable observation, planning, validation, command, dispatch, result and verification operations. The legacy automatic engine and guided coordinator share these core operations. The full 22-stage automatic driver, `tools/integration_demo.py:drive`, calls exactly the guided REST endpoints and stops before physical authorization unless `--authorize-robot` grants batch consent. There is no second 22-stage implementation.

Fast mode uses SQLite and explicitly simulated in-process transport. Lab mode uses `PostgreSQLStore`, RabbitMQ, a separate edge service and actual OPC UA. `Store.prepare` atomically stores immutable command intent with the application outbox. `DeliveryStore.enqueue` retains the stable dispatch payload in PostgreSQL; `LabBridge.publish` performs publisher-confirmed AMQP delivery. `EdgeAdapter.consume_one` commits its durable inbox before manual broker ACK. `LabBridge` calls `EdgeRPC`; `robotops/lab/edge.py:EdgeControl` owns actual OPC UA sessions, browse/subscription operations and method calls to `VirtualPLC`. The API has no direct OPC UA fallback. `PLCJournal` retains accepted identity, execution claim, result sequence and history across restart.

The physical controller interface remains simulated: after the edge obtains the durable PLC execution claim, `EdgeRPC.execute` invokes the existing API-hosted runtime callback once, then reports the result through the edge. The edge retains its OPC UA subscription across that callback. This is not a vendor controller protocol, safety function or database-to-physical atomic transaction. Synthetic and Blender runtime choices share the durable controller journal and verifier contract.

Verified robot outcome, WMS acknowledgement and ERP completion are separate facts. `Store._order` projects terminal guided physical outcomes as `RECONCILING` until `IntegrationStore.complete_business` atomically commits ERP outcome, order marker and audit event after validating durable stage-20 acknowledgements for every order line. Pure planning rejection with no command remains terminal `FAILED`; there is no physical outcome to acknowledge.

Interrupted nonphysical stages resume with the original identities after the operation budget expires. Interrupted physical stages query the original command and never resend motion. Proven absent dispatch intent returns to the physical gate for renewed authorization. A human pause that makes the pre-observation stale returns to fresh observation/planning/validation rather than weakening freshness checks.

## Executing stage map

Every row is implemented. Local profiling tests check happy/lost-ACK paths. `tests/lab/test_source_map.py` runs all 22 stages against PostgreSQL/RabbitMQ/edge REST/OPC UA/WMS and proves every displayed source symbol executed, every excerpt matches its actual file, and the edge RPC methods executed. Latest focused lab source audit: **1 passed in 26.30s**, with effect count one. The profiler caches file paths to avoid instrumentation overhead affecting the unchanged sensor freshness policy.

| Stage | Executing implementation and persisted/protocol evidence |
| --- | --- |
| 1 ERP demand | `GuidedEngine._execute` -> `IntegrationStore.effect`, immutable `ERP_DEMAND`, order/line identities; synthetic enterprise system |
| 2 WMS task | `_execute` -> `effect`, immutable `WMS_TASK` retaining SKU/source/destination |
| 3 API intake gate | `_validate`, `CreateSession`/`OrderRequest`, `API_VALIDATION`; actual REST `/v1/wms/tasks` |
| 4 Durable intake | `Store.intake`, guided authority marker, `Engine.stage_intake`; atomic order/jobs/idempotency and session job IDs |
| 5 Observation | `Engine.stage_observe` -> `_observe`; persisted `WorldObservation`, separate from `WorldState` |
| 6 Planning | `Engine.stage_plan` -> `DeterministicBrain.plan`; proposal persisted, planner has no actuator |
| 7 Validation | `Engine.stage_validate` -> `ActionValidator.validate`; independent semantic/freshness checks |
| 8 Immutable command | `Engine.stage_command` -> `Store.prepare`; immutable command/hash and atomic application outbox. Interrupted replay reuses command and reports `_execute` source |
| 9 Outbox | `IntegrationStore.enqueue`, lab `LabBridge.enqueue` -> `DeliveryStore.enqueue`; pending identity committed before broker traffic |
| 10 Publication gate | Lab `LabBridge.publish`, real RabbitMQ confirm/message/routing metadata; fast `publish_local` labeled simulated |
| 11 Edge delivery | `LabBridge.edge_deliver`, durable `lab_inbox` from `EdgeAdapter.consume_one`; manual ACK after commit; fast `deliver_local` |
| 12 OPC session | `LabBridge.opc_connect` -> `EdgeRPC.call` -> `EdgeControl.call`/`OPCClient._call`; real connection/browse/subscription |
| 13 SubmitJob gate | `LabBridge.submit` checks durable inbox hash; edge OPC method -> `PLCJournal.submit`; acceptance without physical effect |
| 14 Preconditions | `SyntheticRuntime.rejection_reason`; lab `LabBridge.preconditions` -> `CheckPreconditions`; actual scene/mode/generation/tool/TCP checks, not certified safety |
| 15 Physical gate | `_execute` persists `PHYSICAL_AUTHORIZATION` binding command/hash; mandatory explicit consent |
| 16 Execution | `Engine.stage_dispatch`; `LabBridge.authorize_execute` -> `EdgeRPC.execute`, durable PLC claim, existing runtime callback, retained edge subscription; interface simulated |
| 17 Result | `RobotGateway.query`; lab `LabBridge.status` -> edge OPC `GetJobStatus`; original journal/result sequence |
| 18 Post-observation | `Engine._observe`; new persisted sensor observation after effect |
| 19 Verification | `Verifier.verify`, persisted verdict; interrupted committed result uses `Store.records_for_job`, reflected in source metadata |
| 20 WMS | Lab `LabBridge.reconcile_business` -> real REST `/v1/wms/acknowledgements`, durable idempotency; `WMS_ACKNOWLEDGEMENT` record. Fast mode synthetic |
| 21 ERP | `IntegrationStore.complete_business`; every job's durable WMS receipt required; atomic ERP effect/order marker/`ERP_BUSINESS_COMPLETED` event |
| 22 Trace | `_execute` -> `effect`, `TRACE_SUMMARY`, session/order/jobs/correlation/event references and acknowledgement distinctions |

Guard failures cite the handler that certainly executed rather than an adapter that may not have run. Injected pre-wire failures carry `injected_failure=true`, `network_attempted=false`, `SIMULATED SYSTEM`. Successful lab protocol stages use `REAL PROTOCOL`. A failed attempt does not claim confirmed protocol evidence.

## Persisted model and trace contract

- [x] `robotops/integration/models.py` defines versioned `ExecutionSession`, `ExecutionStep`, `AuthorizationDecision`, `ProtocolTrace`, pending authorization and source reference models. `IntegrationStore` persists sessions/decisions; the existing record repository persists protocol traces and correlated `AuditEvent` records.
- [x] Steps expose stable IDs, sequence, order/job/command/session/correlation IDs, stage/status, component, protocol, title/summary, source path/symbol/excerpt, sanitized input/output/wire, before/after state, persistence effect, invariant/failure semantics, truth classification, timestamp/duration, evidence IDs, authorization requirement and revision.
- [x] Revision/idempotency/physical-gate tests in `test_guided.py` and interrupted-operation tests in `test_guided_recovery.py` passed.
- [x] `sanitize` handles nested secret keys, credential URLs, auth headers, key material and exception text; focused tests passed. Final live log/UI inspection remains mandatory.
- [x] Guided reads use `Store.readonly_connect`: SQLite URI `mode=ro` plus query-only; PostgreSQL `SET TRANSACTION READ ONLY`. `test_guided_readonly.py` proves deleted paths are not recreated, replaced schema is unchanged and mutations are rejected.
- [ ] Final browser GET/WebSocket invalidation/reconnect evidence after the lifecycle fix; `apps/api/guided.py` closes streams for invalidated stores and explicit REST is the mutation boundary.

## Definition of Done: all 51 requirements

Unchecked means final verification is outstanding, not that mapped code is absent. Focused evidence does not waive the final suite.

### Workflow correctness (7)

- [ ] **WF-01:** Create/Run starts guided execution. `apps/erp_ui/app.js`, `integration-console.js`, `mount_guided_routes`; `tests/browser/test_guided_console.py` and lab browser happy path. Final refreshed browser result pending.
- [x] **WF-02:** Every stage maps to actual work. Stage table; local two-scenario profiler `test_guided_business.py` plus actual 22-stage lab profiler `test_source_map.py` passed.
- [x] **WF-03:** One authorization executes one stage. `GuidedEngine.authorize`/`_advance_reserved`, `IntegrationStore.reserve`; bounded-stage and all nonphysical interrupted-stage tests passed.
- [x] **WF-04:** Authorizations are idempotent/revision-guarded. Unique decision identity, stage/revision CAS; `test_revision_guard_and_double_click_are_idempotent` and recovery fences passed. Recovery payload hashing also binds optional observation fault; replay with changed fault conflicts without changing revision/effect.
- [x] **WF-05:** No transaction waits for a human. `reserve` commits before `_execute`; `finish` is separate; pending/reloaded reads are read-only. Bounded/read-only tests passed.
- [ ] **WF-06:** Automatic/guided share handlers. Core `Engine.stage_*` reused; full `tools.integration_demo.drive` calls guided REST sequence. `tests/integration/test_demo_driver.py`; final result/artifacts pending.
- [ ] **WF-07:** Existing invariants/scenarios remain functional. `tests/e2e`, integration/browser/Blender policy tests; focused legacy Store/workflow passed, final complete suite pending.

### Full-stack boundaries (10)

- [x] **FS-01:** Versioned idempotent WMS intake. `/v1/wms/tasks`, `CreateSession`, `IntegrationStore.create`, `Store.intake`; guided intake/replay/conflict tests passed.
- [x] **FS-02:** Actual PostgreSQL lab persistence. `PostgreSQLStore`, lab factory; authenticated SQL smoke and complete actual lab source audit passed. Broader rollback/concurrency case: `test_distributed.py:test_postgres_full_repository_intake_and_atomic_outbox`.
- [ ] **FS-03:** Transactional outbox. `Store.prepare` atomic application outbox; `DeliveryStore.enqueue` retained payload before publish. Actual happy path passed; final rollback/disconnect suite in `test_distributed.py` pending.
- [x] **FS-04:** Real RabbitMQ. `LabBridge.publish`, `EdgeAdapter.consume_one`, locked `pika`; native publisher-confirm/manual-ACK smoke and actual complete lab source audit passed.
- [x] **FS-05:** Confirm distinct from consumer ACK. Separate `lab_outbox.confirmed_at` and `lab_inbox.ack_sent`; `LabBridge.publish`/`edge_deliver`; actual stage10/11 source audit passed. Failure combinations also in distributed suite.
- [ ] **FS-06:** Robust edge identity. `EdgeAdapter.consume_one` hash/identity/inbox before ACK; final lost-consumer-ACK/redelivery tests in `test_distributed.py` pending.
- [x] **FS-07:** Actual OPC UA at edge/PLC boundary. `EdgeControl` owns sessions; `EdgeRPC` has no direct fallback; `OPCClient`, `VirtualPLC`. Actual complete source profiler verified edge RPC branches and stage references.
- [ ] **FS-08:** Durable PLC journal. `PLCJournal` accepted identity/claim/history/sequence/boot; final `test_plc.py` and actual process restart `test_plc_process_restart.py` after journal changes pending.
- [ ] **FS-09:** Same identity/payload never repeats effect. Immutable PLC claim/runtime journal/original recovery; final real duplicate/lost-ACK suite asserts one effect.
- [ ] **FS-10:** Same identity/different payload rejected. DeliveryStore/edge/PLC hash guards; `test_journal_rejects_payload_and_result_conflicts`, distributed conflict tests pending final run.

### UI (9)

- [ ] **UI-01:** What/Wire/Code/State/Why/failure views. `apps/erp_ui/integration-console.js`; browser console and lab browser tests; final refreshed artifact pending.
- [ ] **UI-02:** Truthful badges. `STAGES`, actual lab overrides, injected-pre-wire classification and `integration-console.js`; backend truth/source tests passed, final visual audit pending.
- [x] **UI-03:** Source references identify executed code. Local happy/lost-ACK profiling and actual full 22-stage lab source/edge-RPC profiling passed; excerpts match file text.
- [x] **UI-04:** Actual payloads and redaction. Steps built from handler results, persisted traces, recursive `sanitize`; nested-secret/exception/source tests passed. Final logs also require inspection.
- [ ] **UI-05:** Mini-map follows stage. `integration-console.js`; browser assertions, final refreshed result pending.
- [ ] **UI-06:** Reload preserves session. Backend revision/authorization persistence passed; local/lab browser reload tests await final updated run.
- [x] **UI-07:** Physical gate before effect. Stage15/16 checks, legacy run/reconcile bypass guards, gate/crash/identity tests passed; lab profiler ended with one effect.
- [ ] **UI-08:** 3D after gate, then console verification/WMS/ERP. `integration-console.js`, `playback.js`, `scene-view.js`, phase-B edge telemetry; final visual run pending.
- [ ] **UI-09:** Watching cannot mutate state. GET/WS read-only code, observational runtime, guided read tests and eight deleted/replaced database cases passed; final websocket invalidation/browser lane pending.

### Failure semantics (8)

- [x] **FAIL-01:** ACK lost before effect. Guided original-identity test includes before-effect fault, zero-effect evidence and recovery; passed.
- [x] **FAIL-02:** ACK lost after effect without duplicate motion. Guided original-identity and interrupted-physical after-effect cases passed; live browser evidence remains final-loop work.
- [ ] **FAIL-03:** Duplicate/redelivery effect count one. Local journal/authorization checks passed; actual distributed/guided-lab duplicate suite awaits final updated edge run.
- [ ] **FAIL-04:** Network interruption/restart deterministic. `EdgeRPC` rejects unavailable edge without callback; broker/OPC failures retain identity; `test_distributed.py`, `test_plc_process_restart.py`. UI injection honestly simulated; actual service/socket cases await final result.
- [x] **FAIL-05:** Inconclusive observation prevents false success. Guided stale/missing/verifier and human-wait reobserve/replan regression passed; no relaxed freshness window.
- [x] **FAIL-06:** WMS outage retries business only. `test_guided_business.py` proves RECONCILING through outage/ACK, stage21 completion, effect one; multi-line ACK and atomic ERP rollback tests passed.
- [ ] **FAIL-07:** UNKNOWN_OUTCOME visible/explainable. Backend traces passed; final browser uncertainty/recovery UI tests pending.
- [x] **FAIL-08:** Reconciliation queries original command. `GuidedEngine.reconcile`, `Engine._reconcile`, journal queries; interrupted physical/no-result/original-ID/legacy-bypass tests passed.

### E2E verification (11)

- [x] **TEST-01:** New state/domain tests. Guided 14 initial cases, recovery 33, business 6, read-only 8 focused cases; exact runs below. Additional browser lifecycle cases remain in their lane.
- [ ] **TEST-02:** Full distributed integration. Actual 22-stage happy/source audit passed; final complete `tests/lab/test_distributed.py`, `test_guided_lab.py` and restart suite pending.
- [ ] **TEST-03:** Complete happy browser through gate/3D/business. `tests/browser/test_guided_console.py`, `tests/lab/test_browser_lab.py`; final refreshed execution/artifacts pending.
- [ ] **TEST-04:** Browser/integration lost-ACK unknown/recovery. Same browser files and guided-lab after-effect case; final updated stack evidence pending.
- [ ] **TEST-05:** Browser reload/resume. Both browser lanes contain reload checks; pending refreshed execution.
- [x] **TEST-06:** Double authorization/idempotency tested. Guided concurrent/stale/replay and physical request replay checks passed, stable identity and one effect.
- [ ] **TEST-07:** Duplicate AMQP/OPC effect proof. Distributed duplicate checks inbox/PLC/runtime; final updated edge suite pending.
- [ ] **TEST-08:** Existing full suite passes. Final configured unit/integration/browser/E2E/Blender run pending, not replaced by focused audit.
- [ ] **TEST-09:** Repository lint/type policy passes. Focused checks passed; final whole-repository checks pending.
- [x] **TEST-10:** CI runs relevant tests. `.github/workflows/ci.yml` provisions PostgreSQL 17/RabbitMQ 4, lab env, pinned browser and CPU Blender then `tools.dev acceptance --local`. Inspected configuration; final commit CI result is separate evidence.
- [ ] **TEST-11:** Startup/smoke/health documented and exercised. `compose.yaml`, `tools/lab-services.ps1`, lab/native guides. Native install/start/status/repeated-start and PG/AMQP smoke passed; clean latest full stack evidence pending.

### Documentation/demo (6)

- [x] **DOC-01:** README matches implemented stages/real-vs-synthetic boundaries and links lab profiles/shared REST demo driver; final topology changes still require rereview.
- [x] **DOC-02:** Real protocols vs simulated systems explicit in README, lab guide, STAGES, edge responses, simulated runtime interface, sensor/replay labels.
- [x] **DOC-03:** Fast/full lab profiles documented. Main lab guide covers Compose/API/edge/PLC/WMS; native guide covers scoped portable services/ports/health. Windows bootstrap commands exercised.
- [x] **DOC-04:** ACK/uncertainty distinctions documented in trace summary/README/lab guide. This audit adds precise pending-business and interrupted-stage semantics.
- [ ] **DOC-05:** Reproducible happy/lost-ACK script. `tools/integration_demo.py`, README commands, consent/resume/evidence output; exact final command results/artifacts pending.
- [x] **DOC-06:** Independent synthetic scope explicit. README/lab docs disclaim proprietary SICS.AI architecture, exact HKM1800, real hardware and safety certification; no exactly-once physical guarantee.

## Additional clauses outside the 51-item list

- [ ] Chronological stream, pending card, mini-map, IDs, durations, expandable payloads, retry/redelivery and evidence links implemented in `integration-console.js`; final actual rendering evidence pending.
- [x] `VirtualPLC` exposes cell State/Generation/BootId/FaultCode, command identity/hash/state/resultsequence/result, robot Ready/ActiveToolId/TCPPose/MotionPhase; methods SubmitJob/GetJobStatus/CheckPreconditions/BeginExecution/ReportResult/AcknowledgeResult/RestartController. Unknown telemetry is explicit rather than fabricated static truth. Actual source/network audit passed.
- [ ] Result acknowledgement/retention separate: `PLCJournal` retains immutable terminal result and monotonic provisional-to-final history. Final process restart/protocol evidence after journal changes pending.
- [x] Controller link labeled **simulated controller interface**, operational checks/consent independent of E-stop/safety circuitry. No fake fieldbus or vendor protocol.
- [x] Existing `AuditEvent` plus persisted `ProtocolTrace`; actual stage attempts/duration/status/unknown/retry/reconciliation metrics in `robotops/observability/metrics.py`; read-only metrics test passed. No decorative OTLP claim.
- [x] A/B/C/D work reflected in bounded coordinator, real adapters, conservative recovery and inspectors. Visual polish does not substitute for the real stack/browser final loop.

## Focused evidence and environment

Actual audit test results: initial guided/recovery 43 passed; two more recovery cases plus transient regressions 6 passed; initial business/source plus legacy Store/workflow 31 passed; added physical-business-failure/atomic-ERP/planning-rejection/interrupted-stage-21 checks 5 passed; read-only 8 passed; real lab source/network 1 passed; final read-only/authorization/GET/WS-lifecycle selection 14 passed; changed-reconciliation-fault/injected-wire selection 3 passed. Runs overlap and must not be summed as a unique test count. Focused Ruff/format/strict mypy/Bandit checks passed; final policy checks must cover the final tree.

The Windows environment has no usable Docker/WSL. Task-scoped portable PostgreSQL 17.11, RabbitMQ 4.3.6, Erlang 27.3.4.18 were installed without system services/reboot. Authenticated SQL/persistence and actual publisher-confirm/manual-ACK smoke passed; `artifacts/lab-services/protocol-smoke.json` is evidence. `tools/lab-services.ps1` pins hashes and manages only ignored `artifacts/lab-tools`/`artifacts/lab-services`. Native guide documents ports/configuration. Edge/OPC/WMS/API run as independent processes or isolated test listeners. Compose is the portable deployment recipe; workstation evidence uses actual native protocols.

```text
uv sync --locked --all-groups
uv run --locked python -m tools.dev test
uv run --locked python -m tools.dev lint
uv run --locked python -m tools.dev typecheck
uv run --locked python -m tools.dev security
uv run --locked python -m tools.dev acceptance --local
```

Lab tests require working `ROBOTOPS_POSTGRES_DSN`/`ROBOTOPS_AMQP_URL`; missing services fail the mandatory lane rather than silently skipping it. Lab fixtures isolate PostgreSQL schemas, queues and OPC/edge/WMS listeners. Bandit/pip-audit/npm audit/vendored-JS integrity, contracts/publication/coverage and Blender policies remain applicable.

## Mandatory final loop ledger (14)

1. [x] Re-read complete current `GOAL.md`, including all clauses before Definition of Done.
2. [x] Map all 51 Definition of Done items above.
3. [x] Inspect actual implementations/symbols/tests and replace proposals; actual local/lab executed-source profiling passed.
4. [ ] Start complete latest stack from clean scoped state; retain versions/health/logs.
5. [ ] Run full automated unit/integration/E2E suite; retain failures/skips/environment/final results.
6. [ ] Drive real-browser happy path; inspect 3D handoff and business reconciliation.
7. [ ] Drive lost ACK after effect; prove original command/journal/effect records show no second pick.
8. [ ] Reload browser mid-session; prove unchanged authority/identity and safe resume.
9. [ ] Trigger duplicate authorization/delivery; inspect decisions/inbox/PLC/runtime evidence.
10. [ ] Inspect final logs/UI for credentials, false protocol labels and misleading safety claims.
11. [ ] Run all configured lint/type/security checks on final dependencies/tree.
12. [ ] Fix every failure and repeat relevant verification; refresh evidence after changes.
13. [ ] Final documentation review against completed startup/recovery/demo results and limitations.
14. [ ] Final report: requirement-to-evidence, exact commands/results, E2E scenarios, limitations, intentionally simulated components and final commit SHA.

The goal remains **NOT ACHIEVED** while mandatory evidence is absent/failing. A deterministic substitute does not prove real protocols or browser behavior. Replace pending evidence with actual results, not simply checked boxes.
