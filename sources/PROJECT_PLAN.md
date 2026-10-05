# PROJECT_PLAN.md — RobotOps Twin Implementation Contract

**Status:** Normative implementation plan  
**Version:** 1.2 — 2026-10-04; HKM-inspired adaptation revision (ADR 0010). Original workflow requirements and ADR 0008 continuation remain normative.

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
robotops/robotics/        typed product/tool catalogue, selection and trajectory
robotops/hkm_geometry.py  shared procedural cell and visual kinematics
robotops/robot_gateway/   command boundary/journal
robotops/cell/            PLC/cell-state emulator
robotops/blender/         bounded Blender runtime adapter
robotops/observation/     ground truth -> observation
robotops/verification/    outcome verifier
robotops/observability/   logs/metrics/correlation
robotops/faults/          deterministic fault injection
contracts/                OpenAPI/events/schemas
blender/scripts/          fixed runtime and procedural scene realization
tests/{unit,contract,integration,e2e,blender,ui,fixtures}/
docs/{adr,implementation,generated}/
tools/                    stable developer, acceptance and publication commands
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

REQUIRES_INTERVENTION + explicit operator re-observation -> RECONCILING
 -> COMPLETED | FAILED | REQUIRES_INTERVENTION
```

Timeout after a side-effecting command MUST NOT directly imply failure. No exit from UNKNOWN_OUTCOME without reconciliation evidence. Ambiguous evidence never becomes fabricated success. Persist transitions transactionally with audit events.

REQUIRES_INTERVENTION pauses motion but permits explicit collection of another
fresh observation for the same original command. Each attempt requires journal
and observation evidence, preserves earlier results, and uses the unchanged
verifier. Restart does not automatically reopen intervention. Only COMPLETED and
FAILED are terminal; no direct intervention-to-success, execution or reset path
is allowed. This user-requested continuation is recorded in ADR 0008.

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

Blender is a synthetic test world, not validated robot physics. The current
profile uses stable `Robot/*` links/wrist/tool-changer objects, `Tools/EE_*`,
`ToolRack/Dock*`, `Locations/SRC_A` through `SRC_F`, `Locations/DESTINATION`,
`Products/<product_id>` and calibrated overview/observation cameras. Archived
schema-1 scenes retain their original Cartesian object names and interpretation.

Runtime supports deterministic scene reset, ground-truth query, simplified robot/gripper motion, attach/detach product, command journal/events, dropped acknowledgement after effect, logical cell faults, and screenshots.

The dashboard exposes explicit fixture preparation as Start fresh scene, retaining
old orders, journals and replay evidence. Durable maintenance identity serializes
it with intake/claims and survives restart. Pending or uncertain jobs block it;
logical cell reset remains distinct. See ADR 0005.
Scenario selection changes configuration only. Full-delivery
replay groups original executions by saved scene identity without merging ERP
orders or changing job/command semantics; individual replay remains available.
See ADR 0006.

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
10. An operator may request another observation after intervention. Repeat steps
    3–9 under the same fenced cell claim and command identity; never dispatch a
    replacement pick. Sufficient new evidence permits continuing the same test.

The required demo proves the product moves exactly once when the effect occurred but its acknowledgement was lost.

## Observability

Structured JSON events include timestamp, component, event type, correlation/causation IDs, relevant order/job/command IDs, state before/after, duration and reason/error codes. Metrics include received/completed/failed/unknown/intervention jobs, reconciliation outcomes, commands, duplicate suppression, injected faults and pipeline latency. UI exposes a causal order timeline.

## Required fault injection

`DROP_ACK_AFTER_EFFECT`, `DROP_ACK_BEFORE_EFFECT`, `ROBOT_COMMAND_FAILURE`, `CELL_FAULT`, `LOGICAL_ESTOP`, `LOW_CONFIDENCE_OBSERVATION`, `CONTRADICTORY_OBSERVATION`, `STALE_OBSERVATION`, `BRAIN_TIMEOUT`, `BRAIN_INVALID_OUTPUT`.

## UI MVP

Create/select fixture order; show order/job/cell state, observation/verifier summary, causal timeline, demo-safe fault controls, reconcile action, and latest Blender screenshot where practical. UI polish is secondary.

The user-requested presentation extension adds an always-visible 3D cell, live
recorded Blender machine/product motion and per-order scenario replay. A saved
starting scene and audit events illustrate orders with no movement. Orbit, pan,
zoom and playback controls remain separate from WorldObservation and cannot
change job outcomes or issue physical commands. Missing historical recordings
remain explicit; a stationary reference is never evidence of no effect.

Start new test and Test history provide a general experiment lifecycle in the
same window for every execution/observation combination. A new test gets separate
workflow/runtime storage and fresh products. Previous outcomes and replay remain
read-only, including uncertainty and intervention. Selections are retained; no
pick is issued by creation. A durable catalog serializes test creation with API
mutations and startup recovers only the active world (ADR 0007). Job state-machine,
idempotency, reconciliation and observation-boundary rules are unchanged.

### Cell selection and explicit retention controls

ADR 0011 extends the experiment lifecycle. Start new test opens a cell selector
backed by `GET /cell-profiles`; only the HKM-inspired profile is currently
selectable. Legacy profile metadata labels saved tests without making that cell
available for new creation. A test's profile is durable and never changed by
opening it or choosing a new default.

Delete selected test and Clear all test data are explicit confirmed retention
actions, distinct from physical execution, reconciliation and restocking. A
clear request names the displayed live test set; stale snapshots are rejected,
and retries retain their original targets. Removing an active test leaves an
empty active pointer, with no automatic archive promotion or world recreation.
Durable tombstones and deletion receipts prevent resurrection and support
interrupted bounded cleanup. The catalog serializes lifecycle operations with
reads, writes and downloads; in-flight work blocks deletion. Only registered
application-owned world files are removed; unrelated data and lifecycle metadata
remain. Tests validate these operations in temporary roots, never the owner's
existing data. The 110 existing MUST criteria and physical-effect semantics are
unchanged; current acceptance must include the new lifecycle regression evidence.

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
ERP UI, dashboard/timeline, metrics and demo controls. The implemented dark UI
provides a state-derived next-step guide and co-located evidence/re-observation
controls (ADR 0009). Every selectable scenario and review observation explains
what it simulates, its stage and its key difference, with same-window comparisons.
Execution choices affect new orders; review choices affect the next explicit
evidence capture. Expectations and replay never substitute for verification.
Exit: one-command demo explains causal history.

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

## HKM-inspired adaptation revision

Fresh API and desktop data roots and new test sessions select the HKM profile.
Existing saved worlds remain authoritative for their own execution settings and
are never silently migrated. Fixture metadata exposes each product's source and
the destination by identity, not list position. New intake validates these
identities atomically after idempotent replay/conflict handling.

This is an adaptation of the existing implementation, not a replacement of its
distributed-system semantics. The original P0-P7 phases above describe the
baseline system; the enhancement uses HKM-P0 through HKM-P3 below. Its 25 new
MUST criteria are additional to all 85 original MUSTs. No old pass is silently
promoted to a pass for a changed schema, runtime or scene.

The implemented cell is an original procedural **HKM1800-inspired hybrid-kinematic
manipulator**, with six source product families, exactly six interchangeable
tools, a six-position rack, destination tote/conveyor, enclosure, operator gate,
control cabinet, logical E-stop/stack light and three camera viewpoints. The
kinematic illustration is named `HKM_INSPIRED_VISUAL_KINEMATICS_V1`. It maps TCP
pose to visibly connected parallel links; no exact manufacturer IK, CAD,
controller code, dynamics, real throughput or safety certification is claimed.

Strict schema-2 contracts now include canonical ProductSpec/EndEffectorSpec, persistent
ToolState/robot presentation state, sensor/frame metadata, explainable selection
and trajectory intent. Product instances retain stable IDs; the catalogue owns
fixture dimensions, mass and compatibility. Runtime, UI and compatibility
documentation derive from that canonical catalogue. Concrete schema/profile
versions are recorded, tested against archived recordings and documented alongside
generated contracts. Schema-1 serialization excludes absent schema-2 fields to
preserve old payload hashes,
journals and scene identities; no silent reinterpretation or destructive reset
of saved user runs. Unsupported historical visualization is explicitly labelled.

Tool preparation is a deterministic, journaled sub-operation under the existing
PICK_AND_PLACE identity. Mounted/rack state and tool-change/no-change events
persist. `effect_count` continues to count product transfers only. Selection
filters compatibility, mass, geometry and availability with stable scoring and
tie-breaking, recording every candidate's reasons. No suitable/available tool
means zero product-transfer effects.

The planner builds entry/lift/transfer/place/retreat segments with deterministic
smooth presentation interpolation. It enforces the configured synthetic radial/Z
envelope, clearance-expanded obstacle checks and finite deterministic alternate routes.
Static collision bounds derive from the same visible meshes. Observed products,
mounted tool/carried-product envelopes and occupied rack tools are checked;
registered vertical engagement/uncoupling is an explicit contact exception.
Changing yaw uses a conservative swept envelope. Moving visual links are not a
validated articulated-body collision model.
No route yields NO_COLLISION_FREE_SYNTHETIC_TRAJECTORY before transfer. Blender
independently rechecks command identity/payload, scene/cell generation, product
source, tool, calibration, finite target and trajectory structure. These are
conservative synthetic checks, not certified robot motion planning.

WorldState stays private; WorldObservation carries synthetic sensor evidence and
explicitly distinguished SIMULATED_CELL_TELEMETRY. Normal, missing, low-confidence,
stale, contradictory and pose-uncertain evidence is configured/seeded. Verifier
and reconciliation cannot read hidden simulator truth. UNKNOWN_OUTCOME still
requires original journal plus fresh sufficient observation, never a replacement
pick or a successful render. Tool changing must not weaken restart recovery.

Shared scene and motion contracts add stable object hierarchy, quaternion and
visibility/phase/tool/attachment data for browser replay. Historical positional
recordings remain explicitly interpreted. Camera switches, speed, scrub and step
controls remain read-only; simulation timing is distinct from UTC/real latency.
The UI exposes IDs, state, tool reasoning and exact observation/reconciliation
evidence with an unobtrusive Simulation Boundaries explanation.

The HKM-inspired revision passed all 110 MUST criteria at audited source
`ca7798798f916c8130e1833cf16b4d4d3f10d546`. Its evidence records repeated mandatory
suites, actual Blender six-tool/transform/attachment tests, original-command
recovery, browser review and exact-source CI/publication verification. The
historical baseline remains separately attributed; it does not attest later
test-lifecycle changes. The phase definitions below
retain the implementation and exit requirements used for this revision.

### HKM-P0 — Model and adapter

Record/archive the current clean baseline, correct its known UI label regression,
add procedural robot/cell/cameras and richer transforms with explicit legacy
compatibility. Exit: existing happy/lost-ack semantics pass; articulated Blender
poses and browser replay agree. Do not claim the later tool system is complete.

### HKM-P1 — Catalogue, tools and trajectory

Implement six typed products/tools, canonical compatibility, deterministic
selection/reasons, durable occupancy, visible tool-changing, workspace and
synthetic collision preflight. Add the six-SKU tool-showcase through the existing
CLI. Exit: all preferred tools visibly used, invalid pairs/unavailable tools
produce no transfer, and tool state survives restart.

### HKM-P2 — Scenarios and preserved system semantics

Add deterministic/negative contract/unit/integration/real-Blender/E2E tests for
tool, geometry, workspace, collision, calibration and observation failures.
Retain every old uncertainty/idempotency/race/restart fixture. Exit: exactly-one
effects, no verifier truth access, archived replay compatibility and both old/new
mandatory behavior pass without skips, weakened assertions or lower thresholds.

### HKM-P3 — Operator review and publication

Complete tool/evidence/status inspectors, camera and read-only playback controls,
uncertainty guidance and boundaries panel. Review actual scene/motion in the app,
synchronize architecture/state/frame/tool diagrams, reports, schemas and sources,
then run clean acceptance twice and regenerate Pages/PDFs. Exit requires all
110 MUSTs with exact-SHA CI, publication, public-link and final report evidence.

See [ADR 0010](docs/adr/0010-hkm-inspired-versioned-cell.md) and the
[implementation design](docs/implementation/hkm-inspired.md). Public manufacturer
and deployment claims remain COMPANY_REPORTED_CLAIM; catalogue, kinematics,
timing and collision thresholds are SIMULATOR_DESIGN.

## Investigation workflow revision (2026-10-05)

Adapt the accepted workspace at clean `0db6168` around **Set up / Watch /
Investigate / Continue**, preserving all runtime/business semantics. The previous
report is archived in `docs/evidence/investigation-ui-baseline/`; new behavior
does not inherit its PASS results. ADR 0012 records this presentation boundary.
Eight UI-INV MUSTs join the existing 110, for 118 total.

The primary workspace shows a short scenario purpose, behavior to watch, run
action, scene and current outcome. Abnormal results highlight an explicit
investigation action without obscuring the cell automatically. A bounded dialog
separates symptom, confirmed evidence, limits and possible explanation. Evidence
and manual inspection remain one tab away; the timeline is collapsed, filtered
and height-bounded. Exact JSON, IDs, command/journal, assessed observation,
verification/review history and tool decisions remain accessible.

Inspection pins its own test/job while preserving replay selection/frame.
Navigation/downloads are read-only. Explicit sensor re-observation still invokes
the existing original-command reconciliation. New tests and deletion retain
ADR 0011's independent lifecycle. No API, robot schema, database migration or
state-machine change is introduced; the download wrapper is labelled
`robotops-investigation-1`. Manual guidance points to actual scoped endpoints,
source/configuration and local storage rather than a scripted root-cause claim.

Implementation/exit milestones:

1. Inspect/archive baseline, identify overload and real evidence ownership.
2. Implement the compact run/notice/inspect interface and pure evidence summaries;
   test attribution, focus, selection races, errors and replay preservation.
3. Exercise full real-browser journeys with both runtimes on desktop and compact
   screens; fix findings, retain screenshots/traces, assess clarity separately.
4. Synchronize operator docs, diagrams, criteria and reports; run clean full
   acceptance twice with the additive browser suite and unchanged quality gates,
   then verify exact-SHA CI/Pages/PDFs and current acceptance provenance.

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
