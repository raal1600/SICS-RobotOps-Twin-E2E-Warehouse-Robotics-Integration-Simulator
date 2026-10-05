# /goal — RobotOps Integration Lab

## Agent handoff

Upgrade this repository from a deterministic warehouse-robotics simulator with 3D replay into an **explainable, interactive end-to-end industrial integration lab**.

This file is the authoritative delivery goal. Do not mark the goal complete because the UI looks convincing. Every important guided step must correspond to an actual persisted state transition, bounded backend operation, or real protocol interaction in the simulator. The final implementation must be tested end-to-end.

The audience is robotics/AI/system-integration researchers evaluating whether the author understands the complete path from enterprise systems to a robot cell: Python services, APIs, persistence, messaging, edge integration, OPC UA, PLC/controller semantics, physical execution, observations, verification, uncertain outcomes, reconciliation, observability, and production failure modes.

This remains an **independent synthetic integration simulator**. Never claim it reproduces SICS.AI proprietary architecture, an exact HKM1800, real safety-rated control, or real industrial hardware.

---

## Product outcome

Today Create/Run Order reaches the existing HKM-inspired 3D execution while most underlying behavior is hidden.

Change this so Create/Run Order starts a **Guided Integration Console / Execution Trace**. It should look like a serious CLI/agent execution interface but it is not chat and not a shell.

The user reviews meaningful E2E boundaries and explicitly authorizes selected transitions. Authorization must cause the backend to execute only the intended next bounded stage. Do not print fake progress around a monolithic workflow that has already executed.

Flow:

```text
PHASE A — PRE-EXECUTION
ERP -> WMS -> REST -> persistence -> observation -> planning -> validation
-> immutable command -> outbox -> RabbitMQ -> edge -> OPC UA -> virtual PLC acceptance
-> [AUTHORIZE PHYSICAL EXECUTION]

PHASE B — EXECUTION
virtual PLC/controller -> existing HKM-inspired runtime -> 3D viewer

PHASE C — POST-EXECUTION
controller result -> fresh observation -> verification -> reconciliation
-> WMS acknowledgement -> ERP/business status -> final trace
```

During Phase B show useful live protocol/motion status beside the 3D view. After motion, return to the console for verification and reconciliation.

---

## Target integration-lab topology

```text
Operator
  -> Guided Console
  -> FastAPI/Pydantic integration API
  -> guided Python workflow
  -> PostgreSQL (lab profile)
  -> transactional outbox
  -> RabbitMQ / AMQP 0-9-1
  -> Python edge adapter + durable inbox
  -> REAL OPC UA client/server traffic
  -> virtual PLC + command journal/state machine
  -> simulated controller adapter
  -> existing Blender/HKM-inspired runtime
  -> synthetic world/sensors
  -> existing verifier
  -> WMS reconciliation
  -> ERP/business status
```

Use REST/JSON at business boundaries; REST for browser mutations; read-only WebSocket for trace streaming; PostgreSQL for application durability in lab mode; RabbitMQ for distributed delivery; actual OPC UA traffic (for example asyncua) between edge and virtual PLC.

Do not fake PROFINET, EtherCAT, vendor robot protocols, or safety PLC behavior. Label the PLC->robot-runtime link **simulated controller interface** unless a real interface is implemented.

Keep a fast local/test profile (SQLite/in-process is fine) if it helps preserve deterministic tests. Prefer incremental evolution over rewrite.

---

## Core workflow rule

Refactor the current monolithic run path into reusable bounded stage handlers.

Guided mode:
```text
authorize -> execute one stage -> persist result -> expose next stage
```

Automatic mode:
```text
same stage handlers, automatically advanced
```

Never maintain two independent workflow implementations.

Never hold a DB transaction open while waiting for user input. Persist WAITING_AUTHORIZATION, commit, wait, then on a new request validate session/step/revision, persist the authorization, execute the bounded operation, and persist its result.

Browser reload/disconnect must not lose authoritative execution state.

---

## Persisted guided model

Add equivalents of:

- ExecutionSession
- ExecutionStep
- AuthorizationDecision
- ProtocolTrace

A step/trace must support: stable IDs; sequence; order/job/command/session/correlation IDs; stage/status; component; protocol; title/summary; exact repo path + symbol; sanitized input/output; state before/after; persistence effect; wire/protocol details; invariant; failure semantics; real-vs-simulated classification; timestamp/duration; evidence IDs; authorization requirement; revision/version.

Never expose credentials, passwords, private keys, secret headers, or credential-bearing connection strings.

Extend/reuse existing AuditEvent concepts where practical rather than creating an unrelated logging universe.

---

## Guided stages

Do not approve every function. Gates represent meaningful trust/distributed/physical boundaries.

1. ERP demand created — business intent.
2. WMS task created — SKU/source/destination; WMS responsibility.
3. API intake — versioned REST/JSON, Pydantic validation, idempotency. **Gate.**
4. Durable intake — atomic order/job persistence; DB durability != execution.
5. Fresh observation — teach WorldState != WorldObservation.
6. Planning — existing tool/grasp/trajectory logic; planner has no actuator capability.
7. Plan validation — planner output is not blindly trusted.
8. Immutable RobotCommand persisted — stable command ID/payload hash before dispatch.
9. Transactional outbox — DB commit before network side effect.
10. AMQP publish — exchange/routing key/message ID/publisher confirm. **Gate before distributed dispatch.**
11. Edge delivery — durable inbox/journal and consumer-ack policy.
12. OPC UA session — actual connection/browse/subscription operations that really occur.
13. PLC SubmitJob — stable command identity; quick accept/reject, async result/state. **Gate.**
14. PLC preconditions — cell/boot/generation/identity/hash/tool/scene operational checks; do not call ordinary checks safety-rated.
15. READY FOR PHYSICAL EXECUTION — explain irreversible simulated side effect. **Mandatory explicit AUTHORIZE ROBOT EXECUTION gate.**
16. Physical execution — switch to 3D viewer; no approval per keyframe.
17. Controller result — subscription/journal evidence; controller success != business verification.
18. Fresh post-execution observation.
19. Verification — VERIFIED_SUCCESS / VERIFIED_FAILURE / UNKNOWN_OUTCOME.
20. WMS reconciliation — report verified outcome; WMS ack distinct from robot completion.
21. ERP/business completion.
22. Final correlated trace summary.

---

## Integration Console UX

Must include:

- read-only chronological event stream
- pending authorization card
- architecture mini-map with current position
- protocol badges (REST, SQL, AMQP, OPC UA, controller, sensor)
- truth badges such as REAL PROTOCOL, REAL CODE, SIMULATED SYSTEM, SIMULATED ROBOT, SYNTHETIC SENSOR, READ-ONLY REPLAY
- order/job/command/session/correlation IDs
- timestamps/durations and workflow state
- expandable payload inspector
- exact source path/symbol + small relevant excerpt
- views for **What / Wire / Code / State / Why / Failure semantics**
- retry/redelivery visualization
- evidence links
- 3D handoff and post-execution return
- resume after reload

The browser must not fabricate protocol events. Streaming/watch operations must be read-only; mutations happen via explicit REST requests.

---

## OPC UA / virtual PLC

Use actual OPC UA in integration-lab mode.

A reasonable model:

```text
Objects/RobotCell
  Cell: State, Generation, BootId, FaultCode
  Command: ActiveCommandId, PayloadHash, State, ResultSequence, LastResult
  Robot: Ready, ActiveToolId, TCPPose, MotionPhase
  Methods: SubmitJob(...), GetJobStatus(commandId),
           AcknowledgeResult(commandId, resultSequence)
```

Exact names may vary, but semantics must be documented.

Mandatory duplicate rule:

```text
new command ID -> may execute
same ID + same payload hash -> MUST NOT execute physical effect again;
                               return/query original journal result
same ID + different hash -> reject conflict
```

Retain enough controller result state to reconcile after transient communication loss according to the documented simulator durability model.

---

## Failure/recovery requirements

Happy path alone is insufficient. Preserve and visibly demonstrate:

- ACK lost before effect
- ACK lost after effect
- duplicate/redelivered command
- broker/edge transient failure
- OPC UA disconnect
- controller/PLC restart where applicable
- stale/missing/inconclusive observation
- WMS unavailable after successful physical work

Central invariant:

> Never repeat a potentially completed physical operation merely because an acknowledgement/network response was lost.

If effect cannot be proven, use UNKNOWN_OUTCOME (or equivalent). Reconciliation queries the **original command identity**, controller journal, and fresh evidence. It must not blindly resend the pick.

Teach explicitly:

```text
HTTP 202
 != DB commit
 != RabbitMQ publisher confirm
 != consumer ACK
 != OPC UA method acceptance
 != PLC accepted
 != controller succeeded
 != sensor verification
 != WMS reconciliation
 != ERP completion
```

---

## Observability and truthfulness

Every run must be traceable using order_id, job_id, command_id, execution_session_id, correlation/trace ID, and ordered event sequence.

Expose structured logs/traces and useful timing/retry/unknown-outcome/reconciliation metrics. OpenTelemetry/OTLP is welcome if genuinely wired; do not make decorative telemetry.

Safety is an independent conceptual boundary. Do not present a Python/OPC UA boolean or browser button as a certified E-stop, enabling device, or safety function.

Never claim exactly-once physical execution or that a database/broker transaction atomically guarantees a physical effect.

---

## Implementation order

### Milestone A — guided execution on existing internals
Refactor bounded stages; persist sessions/steps/authorizations; add guided REST endpoints and read-only trace stream; build Integration Console; keep auto mode on same engine; preserve current behavior/tests.

### Milestone B — real distributed lab
Add PostgreSQL lab profile, transactional outbox, RabbitMQ, edge service/durable inbox, real OPC UA client/server, virtual PLC journal/state machine, Docker Compose/integration profile.

### Milestone C — production-semantics scenarios
Wire duplicate delivery, ACK-loss, disconnect/restart, stale observation, WMS outage, UNKNOWN_OUTCOME, and reconciliation into guided UI and automated E2E tests.

### Milestone D — polish
Architecture mini-map, source/payload inspectors, protocol badges, metrics/telemetry, demo fixtures, docs, performance/reliability cleanup.

Do not sacrifice correctness for visual polish.

---

# Definition of Done / success criteria

**The goal is NOT achieved until every applicable checkbox below is proven.**

## Workflow correctness
- [ ] Create/Run Order starts guided execution rather than secretly running the full robot workflow.
- [ ] Each displayed stage maps to actual backend work/state/protocol evidence.
- [ ] Authorization advances only the intended bounded stage.
- [ ] Authorizations are idempotent/revision-guarded against double click/replay.
- [ ] No DB transaction remains open while waiting for a human.
- [ ] Automatic and guided modes use the same stage handlers.
- [ ] Existing correctness invariants and scenarios remain functional.

## Full-stack boundaries
- [ ] WMS-style versioned REST task intake exists with idempotency.
- [ ] Integration-lab persistence uses PostgreSQL or a documented equivalent lab profile.
- [ ] Transactional outbox is real, not a log message.
- [ ] RabbitMQ/AMQP path is real in lab mode.
- [ ] Publisher confirm and consumer ACK are represented distinctly.
- [ ] Edge adapter persists/handles delivery identity robustly.
- [ ] OPC UA client/server communication is real in lab mode.
- [ ] Virtual PLC has durable-enough command identity/journal semantics for demonstrated recovery.
- [ ] Same command ID + same payload cannot cause a second physical effect.
- [ ] Same command ID + different payload is rejected.

## UI
- [ ] Console shows What/Wire/Code/State/Why/failure semantics.
- [ ] Protocol and real-vs-simulated badges are accurate.
- [ ] Source references point to code that actually executes.
- [ ] Payloads are derived from actual execution data and secrets are redacted.
- [ ] Architecture mini-map follows the current stage.
- [ ] In-progress session survives browser reload.
- [ ] Final physical gate precedes robot side effect.
- [ ] 3D viewer runs only after that gate and post-execution flow returns to verification/reconciliation.
- [ ] Read-only viewing/streaming cannot mutate robot/workflow state.

## Failure semantics
- [ ] ACK-before-effect loss scenario is demonstrated.
- [ ] ACK-after-effect loss scenario reaches uncertainty/reconciliation without duplicate physical action.
- [ ] Duplicate/redelivery scenario proves effect_count remains one.
- [ ] OPC UA/network interruption has deterministic documented behavior.
- [ ] Inconclusive observation can prevent false success.
- [ ] WMS outage after verified execution retries business reconciliation, not robot motion.
- [ ] UNKNOWN_OUTCOME is visible and explainable.
- [ ] Reconciliation queries the original command instead of issuing a fresh pick.

## E2E verification
- [ ] Unit tests cover new state/domain logic.
- [ ] Integration tests cover DB/outbox/broker/edge/OPC UA/virtual PLC path.
- [ ] Browser E2E test drives a complete guided happy path through authorization -> 3D execution -> verification -> reconciliation.
- [ ] Browser/integration E2E test drives at least ACK-after-effect/UNKNOWN_OUTCOME/reconciliation.
- [ ] Browser reload/resume is tested.
- [ ] Double authorization/idempotency is tested.
- [ ] Duplicate AMQP/OPC command does not duplicate physical effect and is asserted.
- [ ] Existing test suite passes.
- [ ] Lint/type checks pass at repository policy level.
- [ ] CI runs the relevant tests or documents any environment-specific Blender limitation with a deterministic headless substitute.
- [ ] Docker/integration-lab startup has a documented smoke test and health checks.

## Documentation/demo
- [ ] README architecture matches implementation.
- [ ] Clearly label simulated vs real-protocol components.
- [ ] Document local fast mode and full integration-lab mode.
- [ ] Document all acknowledgement meanings and uncertainty model.
- [ ] Include a reproducible demo script for happy path and lost-ACK recovery.
- [ ] No claim implies proprietary SICS.AI knowledge, exact HKM1800 behavior, or safety certification.

---

# Mandatory final agent loop

Before declaring this goal achieved:

1. Re-read this entire `GOAL.md`.
2. Build a checklist from every Definition of Done item.
3. Inspect the implementation, not just test names, and map each item to concrete files/symbols/tests.
4. Start the complete integration-lab stack from a clean state.
5. Run the full automated unit/integration/E2E suite.
6. Execute the guided happy path in a real browser and verify the 3D handoff and post-execution reconciliation.
7. Execute the lost-ACK-after-effect scenario and prove from persisted command/effect evidence that reconciliation does not execute the physical pick twice.
8. Reload the browser mid-session and verify safe resume.
9. Trigger duplicate authorization/delivery and verify idempotency.
10. Check logs/trace UI for secret leakage and misleading “real” labels.
11. Run lint/type/security checks configured by the repository.
12. Fix every failure found, then repeat the relevant tests.
13. Update documentation to match what actually exists.
14. Produce a final completion report containing:
    - checklist item -> implementation evidence
    - exact tests run and results
    - E2E scenarios run
    - remaining limitations
    - anything intentionally simulated
    - final commit SHA

**Do not declare GOAL ACHIEVED while any mandatory criterion is failing, untested, cosmetic-only, or known to be misleading.**

If an item is genuinely impossible in the current environment, document why, implement the strongest deterministic substitute, and leave the goal explicitly NOT ACHIEVED unless the limitation is non-mandatory.

The project succeeds when a technical reviewer can follow one order from enterprise intent to verified physical outcome, inspect every important boundary, inject realistic distributed failures, and see that the system recovers conservatively without pretending the simulation is a real safety-rated robot installation.
