# PROJECT_PLAN.md — RobotOps Twin Implementation Contract

**Status:** Normative implementation plan  
**Version:** 1.0 — 2026-10-01

## Mission

Build a deterministic, inspectable end-to-end warehouse robotics integration simulator:

`ERP/WMS -> Integration API -> Durable Workflow -> Brain Adapter -> Action Validator -> RobotGateway -> Cell/PLC Emulator -> Blender Runtime -> Observation -> Verifier -> Reconciliation -> ERP/WMS`.

This is an **independent simulator inspired by public sources and general industrial practice**. It MUST NOT claim to reproduce SICS AI proprietary architecture, AGI, safety certification, or validated physical performance.

## Priorities and non-goals

Priority order: correct workflow semantics; durable recovery/idempotency; explicit contracts/state; deterministic tests; observability; Blender visualization; optional model assistance.

MVP does not require real hardware/PLC, ROS 2, Gazebo, Isaac Sim, DGX/B200, neural-network training, certified real-time control, an exact HKM1800 replica, or SICS proprietary code. A simulated E-stop is a logical state only.

## Knowledge governance

Normative: `PROJECT_PLAN.md`, `SUCCESS_CRITERIA.md`, `HANDOFF.md`, committed schemas/API contracts, executable tests where they make requirements precise.

Operational derivatives: `CODEX_GOAL_CHECKLIST.md`, `GOAL_PROGRESS.md`, `ACCEPTANCE_REPORT.md`.

Explanatory/public: `README.md`, `reports/**`, `publication/**`, `PUBLICATION.md`, diagrams and generated Pages.

External claims must retain one provenance class: VERIFIED_PUBLIC_FACT, COMPANY_REPORTED_CLAIM, GENERAL_PRACTICE, or SIMULATOR_DESIGN.

Whenever implementation evidence, new primary-source research, an ADR, API/schema/state change, corrected assumption, renamed component, command, metric/test count, or project status makes documentation stale, ALL affected knowledge-base files MUST be synchronized in the same coherent change. Architecture/state/recovery/trust-boundary changes require diagram updates. Generated Pages/PDFs are rebuilt through the publication workflow, never hand-edited.

## Target repository

```text
apps/erp_ui/              mock ERP/WMS UI
apps/api/                 integration/orchestration HTTP API
robotops/domain/          typed domain schemas
robotops/workflow/        state machines + reconciliation
robotops/brain/           deterministic + optional model adapter
robotops/robot_gateway/   command boundary/journal
robotops/cell/            PLC/cell-state emulator
robotops/blender/         bounded Blender runtime adapter
robotops/observation/     ground truth -> observation
robotops/verification/    outcome verifier
robotops/observability/   logs/metrics/correlation
robotops/faults/          deterministic fault injection
contracts/                OpenAPI/events/schemas
blender/scene/            synthetic warehouse scene
blender/scripts/          runtime scripts
tests/{unit,contract,integration,e2e,fixtures}/
docs/{adr,implementation,generated}/
scripts/{demo.sh,test.sh,acceptance.sh}
```

## Technology baseline

Prefer Python 3.13, FastAPI/Pydantic, SQLite behind a repository abstraction, pytest, Ruff, and one enforced static type checker. Pin dependencies reproducibly. Mandatory CI MUST NOT require an LLM/API, GPU, paid service, or network after dependency installation. Blender Python is the visualization/world runtime.

## Required domain contracts

Implement versioned typed schemas for Product, InventoryLocation, Order, OrderLine, PickJob, WorldState, WorldObservation, ActionPlan, RobotCommand, CommandReceipt/Status, RobotEvent, VerificationResult, CellState, FailureInjection, and AuditEvent.

Cross-component records use stable IDs: `order_id`, `order_line_id`, `job_id`, `action_plan_id`, `command_id`, `event_id`, `correlation_id`, `causation_id`, `run_id`. Use UTC ISO-8601 timestamps. Spatial values carry unit, coordinate frame, timestamp where relevant, and calibration/version metadata. Schemas carry `schema_version`; Brain and observation outputs carry implementation/model versions.

## ERP/WMS API

Minimum endpoints:
- `POST /orders`
- `GET /orders/{order_id}`
- `GET /orders/{order_id}/timeline`
- `GET /jobs/{job_id}`
- `POST /jobs/{job_id}/reconcile`
- `GET /health`
- `GET /metrics`

Duplicate order submission with the same idempotency key and identical payload returns the existing semantic result. Same key + changed payload is a conflict. ERP completion means verified business outcome, not “command sent”.

## Job state machine

```text
RECEIVED -> VALIDATED -> PLANNING -> READY_TO_EXECUTE
 -> EXECUTING -> VERIFYING -> COMPLETED

deterministic pre/post error -> FAILED

EXECUTING/VERIFYING + uncertain external effect
 -> UNKNOWN_OUTCOME -> RECONCILING
 -> COMPLETED | FAILED | REQUIRES_INTERVENTION
```

Timeout after a side-effecting command MUST NOT directly imply failure. No exit from UNKNOWN_OUTCOME without reconciliation evidence. Ambiguous evidence never becomes fabricated success. Persist transitions transactionally with audit events.

## Robot command state

`CREATED -> DISPATCHED -> ACCEPTED -> RUNNING -> SUCCEEDED|FAILED`; rejection is explicit. Lost communication from a side-effect-capable state yields `STATUS_UNKNOWN`, then reconciliation. A timeout describes communication, not physical outcome.

## Cell state

At minimum: `READY | BUSY | FAULTED | ESTOP_LOGICAL | RESETTING | OFFLINE`. New motion is blocked unless permitted. Reset does not prove the world is unchanged; uncertain jobs require re-observation/reconciliation.

## Idempotency, concurrency, persistence

Every side-effecting boundary has an idempotency strategy. One intended physical effect keeps one stable command identity across transport retries. Duplicate command IDs return/reject based on the controller journal and MUST NOT reapply the effect. Same ID + different payload is rejected.

MVP may serialize physical picks per cell, but duplicate workers must be safe via persisted atomic claim/lease or equivalent. Lease expiry never proves an external command did not execute.

Persist orders, jobs/transitions, plans, commands/controller journal, audit events, reconciliation outcomes and sufficient world references. Restart reconstructs unfinished work and never blindly replays side effects.

## Brain and validation

Mandatory `DeterministicBrain` is local, seeded/reproducible, schema-valid and CI-safe. Optional model-assisted Brain implements the same strict interface, may not emit arbitrary executable code, and is never required for CI. ActionValidator remains authoritative and checks schema, ownership, cell state, source/destination, units/frame, configured workspace bounds, observation freshness/confidence and version compatibility.

Do not describe an optional LLM/VLM adapter as SICS AI's core model.

## Blender runtime

Blender is a synthetic test world, not validated robot physics. Stable scene concepts: `RobotOpsTwin/Cell`, `Robot`, `Gripper`, `SourceTote`, `DestinationTote`, `Products/<product_id>`, overview and observation cameras.

Runtime supports deterministic scene reset, ground-truth query, simplified robot/gripper motion, attach/detach product, command journal/events, dropped acknowledgement after effect, logical cell faults, and screenshots.

MCP may author/debug assets, but runtime control uses a bounded documented adapter/protocol, not unrestricted natural-language execution.

## Ground truth, observation, verification

Normal verifier logic MUST NOT read simulator ground truth directly:

`WorldState -> ObservationModel -> WorldObservation -> Verifier`.

ObservationModel supports deterministic missing object, pose noise, low confidence, stale data and contradictory evidence.

Verification returns exactly `VERIFIED_SUCCESS | VERIFIED_FAILURE | INCONCLUSIVE`. Pick success requires sufficient fresh evidence that target left expected source and is at intended destination. Inconclusive never becomes success.

## Critical lost-ack reconciliation

1. Persist timeout; job -> UNKNOWN_OUTCOME.
2. Do not generate a replacement command ID.
3. Query original command in RobotGateway/controller journal.
4. Obtain fresh WorldObservation.
5. Compare expected postcondition with evidence.
6. Sufficient journal + observation evidence of completed pick -> RECONCILING -> COMPLETED.
7. Proven no-effect may create a new explicitly related attempt only under retry policy.
8. Contradictory/insufficient evidence -> REQUIRES_INTERVENTION.
9. Persist evidence and causal links.

The required demo proves the product moves exactly once when the effect occurred but its acknowledgement was lost.

## Observability

Structured JSON events include timestamp, component, event type, correlation/causation IDs, relevant order/job/command IDs, state before/after, duration and reason/error codes. Metrics include received/completed/failed/unknown/intervention jobs, reconciliation outcomes, commands, duplicate suppression, injected faults and pipeline latency. UI exposes a causal order timeline.

## Required fault injection

`DROP_ACK_AFTER_EFFECT`, `DROP_ACK_BEFORE_EFFECT`, `ROBOT_COMMAND_FAILURE`, `CELL_FAULT`, `LOGICAL_ESTOP`, `LOW_CONFIDENCE_OBSERVATION`, `CONTRADICTORY_OBSERVATION`, `STALE_OBSERVATION`, `BRAIN_TIMEOUT`, `BRAIN_INVALID_OUTPUT`.

## UI MVP

Create/select fixture order; show order/job/cell state, observation/verifier summary, causal timeline, demo-safe fault controls, reconcile action, and latest Blender screenshot where practical. UI polish is secondary.

## Test strategy

Unit: schemas, transition guards, idempotency, verifier, reconciliation decision table, observation degradation.

Contract: OpenAPI and adapter schemas.

Integration: persistence/workflow, gateway/simulator, observation/verifier, restart.

E2E MUST cover happy path, duplicate order, duplicate robot command, lost ack after effect, lost ack before effect, restart during unknown outcome, contradictory observation, low confidence, logical E-stop/cell fault, two-worker claim race, and deterministic Brain failure behavior.

## Stable developer commands

Provide top-level equivalents of:
`make setup`, `make test`, `make lint`, `make typecheck`, `make demo`, `make acceptance`, `make docs`.

`make demo` is deterministic and needs no external model API.

## Phases

### P0 — Governance/contracts
Create skeleton, dependency policy, domain vocabulary, OpenAPI/schema contracts, state diagrams, ADR template. Exit: contract tests parse and docs align.

### P1 — Durable workflow
Implement persistence, order/job lifecycle, idempotency, audit timeline, claim semantics. Exit: unit/integration tests including restart and duplicate order.

### P2 — Deterministic cell runtime
Implement Cell emulator, RobotGateway/controller journal, deterministic non-Blender world adapter. Exit: command/idempotency/fault tests.

### P3 — Observation/reconciliation
Separate ground truth from observation; verifier and reconciliation decision table. Exit: critical lost-ack and ambiguous-evidence E2E tests pass.

### P4 — Blender
Create bounded Blender adapter/scene preserving the same runtime contract. Exit: happy path and lost-ack run against Blender and generate artifacts.

### P5 — UI/observability
ERP UI, dashboard/timeline, metrics and demo controls. Exit: one-command demo explains causal history.

### P6 — Optional model adapter
Only after deterministic path passes. Strict schema and safe failure. Never blocks acceptance.

### P7 — Acceptance/publication
Run all gates, generate ACCEPTANCE_REPORT.md, synchronize knowledge base, rebuild Pages, verify public links/artifacts.

## Demo script

Happy path: reset fixture -> create order -> plan -> validate -> dispatch -> Blender pick -> observe -> verify -> complete -> ERP shows completed timeline.

Critical path: reset -> enable DROP_ACK_AFTER_EFFECT -> create order -> command applies exactly once -> ack disappears -> UNKNOWN_OUTCOME -> reconcile original command journal + fresh observation -> COMPLETED -> prove no second pick event.

Ambiguous path: inject contradictory observation -> reconciliation cannot establish truth -> REQUIRES_INTERVENTION.

## Configurable, not hard-coded

Timeouts, confidence thresholds, observation freshness, workspace bounds, coordinate frames, fixture product/location IDs, lease duration, retry policy, fault selection, Brain mode, ports and database path.

## Optional backlog

ROS 2/Gazebo/Isaac adapters, real OPC UA/Modbus endpoints, advanced Blender physics, VLM perception, multi-cell scheduling, GPU inference, real hardware. None may block MVP DONE.

## Knowledge-base synchronization protocol

Before every milestone commit:
1. Detect changed facts/contracts/status.
2. Identify all affected normative, explanatory and generated artifacts.
3. Update source files, diagrams, README and criteria references together.
4. Run drift checks: links/paths, criterion IDs, OpenAPI/schema references, commands, test counts, source-registry consistency, publication build.
5. Rebuild generated Pages/PDFs via workflow.
6. Record synchronization in GOAL_PROGRESS.md.
7. Final ACCEPTANCE_REPORT.md states whether drift was found and exactly what was synchronized.

Never hand-edit generated publication output. Never make public documentation more certain than the evidence.
