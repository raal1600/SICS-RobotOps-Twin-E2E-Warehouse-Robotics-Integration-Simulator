# SUCCESS_CRITERIA.md — RobotOps Twin Acceptance Contract

**Status:** Normative. **DONE means every MUST criterion passes.** SHOULD failures are documented. OPTIONAL items never block completion.

Evidence for every MUST must appear in `ACCEPTANCE_REPORT.md` as test/command output, artifact, screenshot, log excerpt, metric, or file path. Mandatory CI must be deterministic and independent of external LLM APIs.

## Architecture and scope
- **SC-ARCH-001 MUST**: Implement the E2E boundaries defined in PROJECT_PLAN.md. Evidence: architecture contract/integration tests and current diagram.
- **SC-ARCH-002 MUST**: Runtime components communicate through documented typed contracts; no Blender internals leak into ERP domain logic. Evidence: contracts + dependency tests/review.
- **SC-ARCH-003 MUST**: Public docs state this is an independent simulator and make no claim of proprietary SICS architecture, AGI reproduction, safety certification, or validated physical performance.
- **SC-ARCH-004 SHOULD**: Replaceable adapters exist for Brain, robot runtime and observation model.

## Data/contracts
- **SC-DATA-001 MUST**: Required domain schemas in PROJECT_PLAN.md exist, are versioned and validated.
- **SC-DATA-002 MUST**: Cross-component records carry required stable IDs and correlation/causation IDs where applicable.
- **SC-DATA-003 MUST**: Spatial data includes units and coordinate frame; observation data includes timestamp/freshness and model/calibration metadata where relevant.
- **SC-DATA-004 MUST**: Same idempotency key + same order payload returns existing semantic result; same key + different payload is rejected.
- **SC-DATA-005 MUST**: OpenAPI/schema files validate in CI.

## State machines
- **SC-STATE-001 MUST**: Job transitions are centrally validated; forbidden transitions fail tests.
- **SC-STATE-002 MUST**: Timeout after a side-effect-capable dispatch cannot directly transition to FAILED solely because of timeout.
- **SC-STATE-003 MUST**: UNKNOWN_OUTCOME can only resolve through reconciliation evidence.
- **SC-STATE-004 MUST**: Ambiguous/contradictory evidence cannot transition to COMPLETED.
- **SC-STATE-005 MUST**: Cell FAULTED, ESTOP_LOGICAL, RESETTING and OFFLINE block new simulated motion.
- **SC-STATE-006 MUST**: Reset after cell fault forces appropriate re-observation/reconciliation for uncertain work.

## Idempotency/concurrency
- **SC-IDEM-001 MUST**: Re-delivering the same RobotCommand ID cannot apply the simulated physical effect twice.
- **SC-IDEM-002 MUST**: Same command ID with changed payload is rejected.
- **SC-IDEM-003 MUST**: Two workers racing for one job cannot both own/execute it.
- **SC-IDEM-004 MUST**: Transport retry for one intended effect reuses command identity.

## Persistence/restart
- **SC-PERSIST-001 MUST**: Empty local state initializes through the documented one-command setup/demo path.
- **SC-PERSIST-002 MUST**: Orders, jobs/transitions, commands/journal and audit events survive orchestrator restart.
- **SC-PERSIST-003 MUST**: Restart with an uncertain side effect does not blindly replay the command.
- **SC-PERSIST-004 MUST**: Restarted system can reconcile and complete the lost-ack-after-effect fixture without a second pick.

## Brain/validation
- **SC-BRAIN-001 MUST**: DeterministicBrain runs locally, reproducibly, without network/API/GPU.
- **SC-BRAIN-002 MUST**: Invalid Brain output is rejected before RobotGateway.
- **SC-BRAIN-003 MUST**: Optional model-assisted mode is isolated behind the same schema and is not required by mandatory CI.
- **SC-BRAIN-004 MUST**: No model output is executed as arbitrary generated code.
- **SC-BRAIN-005 SHOULD**: Optional model failure produces an explicit safe failure/fallback state.

## Blender/world model
- **SC-BLENDER-001 MUST**: A reproducible scene contains stable cell, robot/gripper, source, destination, products and camera identities.
- **SC-BLENDER-002 MUST**: Product objects map to stable product IDs.
- **SC-BLENDER-003 MUST**: Bounded runtime adapter can reset, query world state, apply the simplified pick, journal events and capture a visual artifact.
- **SC-BLENDER-004 MUST**: DROP_ACK_AFTER_EFFECT can apply the world change while suppressing the response.
- **SC-BLENDER-005 MUST**: Runtime control does not depend on unrestricted natural-language MCP execution.
- **SC-BLENDER-006 MUST**: Documentation explicitly says Blender is synthetic visualization/test state, not validated robot dynamics.

## Observation/verifier
- **SC-OBS-001 MUST**: Ground truth and WorldObservation are distinct schemas/data paths.
- **SC-OBS-002 MUST**: Normal verifier code cannot directly substitute ground truth for observation.
- **SC-OBS-003 MUST**: Deterministic observation degradation supports low confidence, stale, missing and contradictory evidence.
- **SC-OBS-004 MUST**: Verifier returns VERIFIED_SUCCESS, VERIFIED_FAILURE or INCONCLUSIVE with evidence/reason.
- **SC-OBS-005 MUST**: Low-confidence or contradictory evidence never fabricates success.

## Critical reconciliation
- **SC-REC-001 MUST**: E2E test: command applies a pick, acknowledgement is lost, job enters UNKNOWN_OUTCOME.
- **SC-REC-002 MUST**: Reconciliation queries the original command identity/journal and a fresh observation.
- **SC-REC-003 MUST**: When evidence proves the object is already at destination, job becomes COMPLETED.
- **SC-REC-004 MUST**: The SC-REC-001 scenario records exactly one simulated pick effect and zero duplicate physical/simulated picks.
- **SC-REC-005 MUST**: Contradictory/insufficient evidence ends in/stays REQUIRES_INTERVENTION or UNKNOWN, never COMPLETED.
- **SC-REC-006 MUST**: Lost acknowledgement before effect is distinguishable from lost acknowledgement after effect and handled according to evidence.
- **SC-REC-007 MUST**: Reconciliation evidence is persisted in the causal timeline.

## Fault/cell behavior
- **SC-FAULT-001 MUST**: Deterministic injection exists for all required scenarios in PROJECT_PLAN.md.
- **SC-FAULT-002 MUST**: Logical E-stop blocks new motion and is visibly logged/stateful.
- **SC-FAULT-003 MUST**: Cell fault blocks new motion.
- **SC-FAULT-004 MUST**: Clearing fault/E-stop does not silently mark uncertain work successful.
- **SC-FAULT-005 MUST**: Brain timeout/invalid output cannot reach physical-effect application.

## Observability
- **SC-LOG-001 MUST**: Structured event logs can reconstruct an order's causal timeline using correlation/causation IDs.
- **SC-LOG-002 MUST**: Timeline shows state transitions and command identity for critical E2E cases.
- **SC-METRIC-001 MUST**: Metrics expose pipeline latency and counts for completed, failed, unknown/intervention and reconciled jobs.
- **SC-METRIC-002 MUST**: Duplicate-command suppression and injected-failure counts are observable.

## UI/demo
- **SC-DEMO-001 MUST**: One documented command starts/runs a deterministic local happy-path demo from clean state.
- **SC-DEMO-002 MUST**: One documented command demonstrates lost-ack-after-effect reconciliation.
- **SC-DEMO-003 MUST**: UI/dashboard shows order/job/cell status and causal timeline.
- **SC-DEMO-004 SHOULD**: UI exposes demo-safe fault injection and latest Blender artifact.
- **SC-DEMO-005 MUST**: Demo requires no external LLM API.

## Automated tests/tooling
- **SC-TEST-001 MUST**: One command runs the complete mandatory automated suite.
- **SC-TEST-002 MUST**: Unit, contract, integration and E2E suites exist.
- **SC-TEST-003 MUST**: Mandatory tests are deterministic across two consecutive clean runs.
- **SC-TEST-004 MUST**: Lint/format check passes.
- **SC-TEST-005 MUST**: Static type check passes.
- **SC-TEST-006 MUST**: Dependency/security check selected by the project passes or has documented reviewed exceptions.
- **SC-TEST-007 MUST**: No mandatory test silently skips because Blender/model/network is absent; supported headless simulation strategy must be explicit.
- **SC-TEST-008 SHOULD**: Coverage threshold is defined and cannot be reduced merely to pass a goal loop.

## Knowledge-base alignment/publication
- **SC-KB-001 MUST**: README, plan, criteria, handoff, checklist, reports, source registry, diagrams, commands and implementation status contain no known material contradiction.
- **SC-KB-002 MUST**: Architecture/state/reconciliation/trust-boundary changes update affected diagrams in the same coherent change.
- **SC-KB-003 MUST**: External factual changes retain provenance class and source.
- **SC-KB-004 MUST**: README contains no stale command/path/test count and does not call unimplemented work completed.
- **SC-KB-005 MUST**: Automated drift checks validate internal links/referenced paths, criterion IDs, contracts/schema references and documentation build where practical.
- **SC-KB-006 MUST**: GitHub Pages/publication is rebuilt by the existing workflow, not by hand-editing generated output.
- **SC-KB-007 MUST**: Publication workflow passes after final normative/documentation changes.
- **SC-KB-008 MUST**: Public Pages expose current project status and links to the normative implementation/governance files or a clearly current governance section.
- **SC-KB-009 MUST**: ACCEPTANCE_REPORT.md states whether documentation drift was detected and lists synchronized artifacts.
- **SC-KB-010 MUST**: Public material preserves the boundary between verified facts, company-reported claims, general practice and simulator design.

## Documentation/reproducibility
- **SC-DOC-001 MUST**: README documents setup, architecture, deterministic demo, tests, project status and links to research reports plus PROJECT_PLAN/SUCCESS_CRITERIA/HANDOFF.
- **SC-DOC-002 MUST**: A clean checkout can follow documented setup without undocumented secrets.
- **SC-DOC-003 MUST**: Dependency versions are reproducible/pinned according to documented policy.
- **SC-DOC-004 MUST**: ADRs record material deviations from the normative plan.
- **SC-DOC-005 MUST**: No private recruitment messages, credentials or proprietary material are committed.

## Acceptance report
- **SC-ACC-001 MUST**: `make acceptance` or documented equivalent generates/updates ACCEPTANCE_REPORT.md.
- **SC-ACC-002 MUST**: Every MUST criterion maps to concrete evidence and PASS/FAIL.
- **SC-ACC-003 MUST**: SHOULD failures are explicitly listed with rationale.
- **SC-ACC-004 MUST**: Report includes commit SHA, environment/tool versions and test commands.
- **SC-ACC-005 MUST**: Report contains a documentation-drift/synchronization section.
- **SC-ACC-006 MUST**: No criterion is marked PASS solely by assertion; it needs inspectable evidence.

## Exact required E2E fixtures

At minimum automated fixtures named/equivalent to:
1. happy_path
2. duplicate_order_same_payload
3. duplicate_order_conflict
4. duplicate_robot_command
5. lost_ack_after_effect
6. lost_ack_before_effect
7. restart_unknown_outcome
8. contradictory_observation
9. low_confidence_observation
10. stale_observation
11. logical_estop
12. cell_fault
13. two_worker_claim_race
14. brain_invalid_output
15. brain_timeout

## Anti-shortcut rule

An agent MUST NOT make the project pass by weakening a MUST, lowering a threshold without justified ADR, deleting/xfailing/skipping a failing mandatory test, changing expected behavior to match a bug, bypassing observation with ground truth, or redefining DONE.

## HKM-inspired enhancement revision (2026-10-04)

This revision adds 25 MUST criteria to the existing 85 MUST criteria. It does not
supersede or weaken any existing requirement. Every new criterion requires an
executed verification command, named test or inspectable artifact, PASS/FAIL and
the exact inspected commit SHA in the acceptance report. Planned tests and prior
release results are not PASS evidence for this revision.

- **HKM-VIS-MUST-001 MUST**: The procedural scene contains an original HKM-inspired base, parallel-link hierarchy, wrist and tool changer, visibly distinct from the legacy Cartesian gantry. No proprietary or exact HKM1800 CAD is imported. Evidence: scene-object integration test, procedural source and asset provenance.
- **HKM-VIS-MUST-002 MUST**: Six reachable source boxes A-F contain six product families with canonical deterministic dimensions, mass ranges and distinct geometry: small carton, medium carton, soft pouch, bottle, can/jar and long carton. Evidence: catalogue and actual Blender scene tests.
- **HKM-VIS-MUST-003 MUST**: Exactly six typed interchangeable end-effector definitions exist: EE_VAC_SINGLE, EE_VAC_ARRAY, EE_PINCH_NARROW, EE_PINCH_WIDE, EE_ADAPTIVE_SOFT and EE_SUPPORT_FORK. One is mounted and the other five remain visible in the rack; unavailable or incompatible tools block transfer. Evidence: catalogue, occupancy, tool-change and negative validation tests.
- **HKM-VIS-MUST-004 MUST**: The full tool-showcase runs all six SKUs deterministically using their preferred tools (A/single vacuum, B/vacuum array, C/soft, D/narrow pinch, E/wide pinch, F/support fork), with persisted tool state and visible tool preparation before each verified pick. Evidence: real Blender showcase artifacts and restart-aware tool-state tests.
- **HKM-VIS-MUST-005 MUST**: Each selection persists the chosen tool, scored candidates, compatibility/mass/geometry/availability reasons and stable tie-breaking. Tool-change sub-operations and no-change decisions are inspectable under the original product-transfer command. Evidence: decision/event contract and deterministic selector tests, including mass/geometry rejection and tie-breaking.
- **HKM-VIS-MUST-006 MUST**: Every TCP waypoint and sampled trajectory lies within the configured synthetic radial/Z envelope before effect; malformed poses, incompatible frames/calibration and stale scene/cell identity are blocked. Blender independently checks critical command preconditions. Evidence: positive and negative validator/runtime tests proving zero transfer on rejection.
- **HKM-VIS-MUST-007 MUST**: Conservative synthetic collision preflight checks sampled segments with active-tool/carried-product clearance against static and dynamic obstacles, tries a finite deterministic set of alternate transfer routes, and rejects an impossible route with NO_COLLISION_FREE_SYNTHETIC_TRAJECTORY before effect. Evidence: intersection, deterministic alternative and no-route tests. No certified robot collision-planning claim is made.
- **HKM-VIS-MUST-008 MUST**: The TCP-driven HKM_INSPIRED_VISUAL_KINEMATICS_V1 model deterministically keeps articulated links connected and animates tool preparation, approach, grasp/confirmation, lift, safe transfer, place/release/confirmation and retreat. Smooth presentation timing is distinct from real latency and does not claim real robot dynamics. Evidence: actual Blender changing-link rotations, attachment/release and final-pose tests.
- **HKM-VIS-MUST-009 MUST**: Versioned motion records contain position, normalized orientation, visibility, phase, tool/occupancy and product-attachment information sufficient for browser replay of the committed Blender transforms. Legacy evidence is explicitly supported or clearly identified and gracefully degraded without silent reinterpretation. Evidence: transform contracts and old/new playback compatibility tests.
- **HKM-VIS-MUST-010 MUST**: Mandatory execution uses versioned typed requests through the bounded Blender adapter and fixed checked-in code. No natural-language/MCP/model-generated executable command can control the runtime. Evidence: strict command rejection and dependency/runtime-boundary tests.
- **HKM-VIS-MUST-011 MUST**: The verifier and reconciliation decisions cannot inspect WorldState, bpy, Blender objects or private world database rows. They use WorldObservation, the original command and typed journal/prior evidence. Deliberately favorable hidden truth with contradictory observation still yields INCONCLUSIVE. Evidence: structural dependency guards and adversarial observation tests.
- **HKM-VIS-MUST-012 MUST**: NORMAL, MISSING_OBJECT, LOW_CONFIDENCE, STALE, CONTRADICTORY and POSE_UNCERTAINTY observations remain reproducible from explicit configuration/seed and carry sensor, frame, time, calibration/model metadata. Cell tool telemetry is labelled SIMULATED_CELL_TELEMETRY, not pixel-derived perception. Evidence: degradation/configuration and observation contract tests.
- **HKM-VIS-MUST-013 MUST**: Lost acknowledgement after the durable Blender product effect places the workflow in UNKNOWN_OUTCOME, preserving the original command identity; transport timeout never alone means failed physical execution. Evidence: real Blender E2E transition/timeline test.
- **HKM-VIS-MUST-014 MUST**: That uncertain command resolves to COMPLETED only when its original journal and a fresh sufficient observation agree. There is exactly one PICK_EFFECT, one product-transfer command and zero replacement picks. A receipt alone is insufficient. Evidence: persisted exact-one-effect audit and real Blender reconciliation test.
- **HKM-VIS-MUST-015 MUST**: Insufficient or contradictory evidence after an effect yields INCONCLUSIVE and REQUIRES_INTERVENTION, without a new pick or fabricated success. Later explicit fresh evidence may resolve the same command while preserving prior assessments. Evidence: ambiguous and repeated re-observation E2E tests.
- **HKM-VIS-MUST-016 MUST**: Identical order/key replay returns the existing semantic result; changed payload/key reuse conflicts without another job, command or product effect. Evidence: independent order-versus-command idempotency E2E assertions.
- **HKM-VIS-MUST-017 MUST**: Restart after an uncertain effect preserves the original command, world/tool state and journal, reconciles conservatively, and never repeats a product transfer. Same command/same payload is suppressed and changed payload conflicts. Evidence: real process-restart and command replay tests with one PICK_EFFECT.
- **HKM-VIS-MUST-018 MUST**: The UI exposes order/job/command identity, distinguishable job/cell state, product/SKU, active tool and current robot phase, with persisted tool-selection reasons. UNKNOWN_OUTCOME communicates uncertainty rather than generic failure. Tool/trajectory outcome counters and synthetic motion duration are observable separately from actual pipeline latency. Evidence: dashboard/status/metrics contracts and operator screenshots.
- **HKM-VIS-MUST-019 MUST**: The UI exposes original-journal, exact assessed observation and reconciliation evidence with confidence, sensor/model/calibration version and causal IDs/timestamps. It distinguishes effect, acknowledgement delivery and workflow knowledge, and points intervention to review. Hidden debug truth is labelled SIMULATION GROUND TRUTH - NOT VERIFICATION EVIDENCE. Evidence: evidence inspector tests and uncertain/ambiguous browser review.
- **HKM-VIS-MUST-020 MUST**: Replay, scrub/step/speed controls, history and camera selection are read-only and cannot dispatch, reconcile, reset or change persisted outcomes. Playback supports 0.25x, 0.5x, 1x, 2x and 4x without altering workflow time or effects. Evidence: UI action and persisted-state immutability tests.
- **HKM-VIS-MUST-021 MUST**: Operator overview, overhead observation and side inspection cameras have stable identities and useful viewpoints; sensor cameras carry frame/calibration/camera-model/pose metadata. Operator/overhead/side/Follow TCP controls affect presentation only. Evidence: scene/camera contracts and browser viewpoint checks.
- **HKM-VIS-MUST-022 MUST**: Public docs and an unobtrusive in-app Simulation Boundaries panel describe an HKM1800-inspired hybrid-kinematic manipulator, synthetic observations and simulation-only collision/timing rules. They disclaim exact CAD/kinematics, validated dynamics/performance, safety certification, proprietary SICS software and fabricated CV. Manufacturer/deployment claims retain COMPANY_REPORTED_CLAIM provenance. Evidence: documentation/UI boundary checks and source registry review.
- **HKM-VIS-MUST-023 MUST**: All 85 existing MUST criteria still pass without deleted/skipped/weakened assertions, and clean deterministic suites pass twice. Previous acceptance evidence remains immutable and separately scoped. Evidence: complete old/new criterion mapping, both full suite outputs, coverage/security/type/lint gates and baseline archive.
- **HKM-VIS-MUST-024 MUST**: Plan, handoff, schema/API documentation, ADRs, diagrams, canonical compatibility documentation, README, reports, progress and acceptance report describe the final implemented architecture and versions without unresolved material drift. Evidence: generated catalogue consistency checks, drift scan and final knowledge-base review.
- **HKM-VIS-MUST-025 MUST**: GitHub Pages and public PDFs rebuild from synchronized source through the established publication workflow, pass exact-final-source CI/publication gates and serve verified public links. Generated output is never manually edited. Evidence: local build, exact-SHA workflows and public artifact/link hashes.

Required enhancement fixtures additionally include the full six-tool showcase,
unavailable tool, invalid product/tool pairing, workspace violation, impossible
collision route, stale calibration, historical replay compatibility and semantic
determinism. Thresholds and physics limitations remain explicit simulator rules.

## Cell selection and test-data lifecycle addendum (2026-10-04)

ADR 0011 extends the documented UI/API lifecycle without adding or weakening
criterion IDs: that revision retained 110 MUST criteria, before the eight
investigation criteria below brought the total to 118. Its scoped tests
join the evidence for SC-ARCH, SC-IDEM, SC-PERSIST, SC-DEMO, SC-TEST and SC-KB
requirements as applicable. Prior accepted source `ca779879` does not attest the
new behavior.

Verification includes the one selectable HKM cell, nonselectable legacy history,
durable per-test profile metadata, explicit confirmed deletion, stale clear-all
snapshot rejection, idempotent retries, pending cleanup, no-active-test restart,
in-flight operation guards and confined cleanup. Cancellation and navigation
leave data intact. Clear retries cannot delete later-created tests. Deletion
never fabricates a business verdict, sends a pick or promotes an archived world;
retained tests preserve their original outcomes and read-only replay semantics.
These destructive-action checks use isolated disposable data, not user history.
Full source-specific acceptance and publication remain governed by the rules below.

The owner's 2026-10-05 correction (ADR 0013) additionally requires complete
catalog/world removal after deletion, reusable positive display numbers (Test 1
when empty), and explicit same-test clearing that retains identity/number/cell
while discarding old execution data and restoring products. Verification covers
revision fencing, cached hosts, pending-clear restart, digest-only retry guards,
old-tombstone cleanup, intact neighboring tests and real browser clear/delete
journeys. An earlier expectation of monotonic labels or permanent deleted rows
is intentionally superseded; robot-effect and evidence assertions are unchanged.
Management verification includes delayed response bodies: the UI waits for its
own replay/snapshot reads before sending a confirmed lifecycle request. A stalled
read must leave data intact with an explicit retry, and final refresh must finish
before controls resume. Existing backend running-work/download guards remain required.

## Investigation workflow revision (2026-10-05)

These eight criteria add to all 110 prior MUSTs. The execution, observation,
idempotency, evidence and coverage requirements remain unchanged. Historical
passes are scoped to their original source; this revision needs fresh evidence.

- **UI-INV-MUST-001 MUST**: The primary workspace explains the cell's task, selected scenario purpose and a concrete behavior to watch, and offers a working run action alongside the cell/current result. Detailed explanations remain available without dominating the normal view. Evidence: desktop and compact normal-pick browser journeys and scenario-guide tests.
- **UI-INV-MUST-002 MUST**: Investigation separates observed symptom, confirmed record contents, their limits and unproven possible explanation. Claims come from the inspected job's evidence/events; a controller receipt, current dropdown, unrelated job or WorldState must never be substituted for an assessed observation/verdict. Evidence: attribution/negative tests and uncertain/ambiguous browser checks.
- **UI-INV-MUST-003 MUST**: A result needing attention links directly to the relevant command/journal, exact assessed observation, verification/reconciliation attempts, tool decision, identifiers and full structured evidence. Uncertain and intervention outcomes remain distinguishable from failure/success. Evidence: real lost-ack and contradictory-review journeys with original command ownership assertions.
- **UI-INV-MUST-004 MUST**: Investigation preserves the selected test/run/job and replay context, including when inspecting a blocking job while replaying an earlier pick. Opening inspection pauses only replay; returning retains its selection/frame. Polling must not steal focus or switch the inspector's tab. New test selection invalidates old inspection responses. Evidence: browser and dashboard/player context tests.
- **UI-INV-MUST-005 MUST**: The event timeline is secondary, initially collapsed and bounded on desktop and compact viewports, with accessible relevant events and exact record inspection. It must not push evidence below an unbounded event list. Evidence: actual browser geometry and interaction assertions.
- **UI-INV-MUST-006 MUST**: Manual inspection provides correctly scoped read-only requests, a usable evidence/event JSON export, recorded-input reproduction guidance and real source/configuration/log/storage paths. It must not infer the historical scenario from the current selector. Browsing/downloading does not mutate the world or workflow. Evidence: live API/download comparisons and no-write assertions.
- **UI-INV-MUST-007 MUST**: Actual application/request failures are labelled separately from injected simulation faults and do not invent a workflow outcome. Running work, recorded workflow result and paused/completed replay remain distinguishable. Evidence: intentional service-failure browser test, normal/fault journeys and slow-planning selection regression.
- **UI-INV-MUST-008 MUST**: Repeatable actual-browser tests exercise normal run, supported fault, evidence/manual inspection, return and saved history at desktop and compact viewports with both deterministic synthetic and actual Blender runtimes. They verify actions, evidence ownership, no navigation writes, no unexpected browser errors and bounded layout; retain screenshots, traces and semantic results. Clarity/discoverability assessment and first-time-user uncertainty are reported separately from functional test success. All prior MUSTs and final exact-SHA publication gates still apply.

## Integration Lab upgrade ? authoritative GOAL.md

These 51 additive MUSTs preserve every checkbox from the new GOAL.md in order.
The mandatory final agent loop also requires manual implementation inspection, a clean
complete lab startup, actual browser scenarios and a final exact-source report.
A test-name mapping alone is not completion evidence.

- **LAB-MUST-001 MUST**: Create/Run Order starts guided execution rather than secretly running the full robot workflow.
- **LAB-MUST-002 MUST**: Each displayed stage maps to actual backend work/state/protocol evidence.
- **LAB-MUST-003 MUST**: Authorization advances only the intended bounded stage.
- **LAB-MUST-004 MUST**: Authorizations are idempotent/revision-guarded against double click/replay.
- **LAB-MUST-005 MUST**: No DB transaction remains open while waiting for a human.
- **LAB-MUST-006 MUST**: Automatic and guided modes use the same stage handlers.
- **LAB-MUST-007 MUST**: Existing correctness invariants and scenarios remain functional.
- **LAB-MUST-008 MUST**: WMS-style versioned REST task intake exists with idempotency.
- **LAB-MUST-009 MUST**: Integration-lab persistence uses PostgreSQL or a documented equivalent lab profile.
- **LAB-MUST-010 MUST**: Transactional outbox is real, not a log message.
- **LAB-MUST-011 MUST**: RabbitMQ/AMQP path is real in lab mode.
- **LAB-MUST-012 MUST**: Publisher confirm and consumer ACK are represented distinctly.
- **LAB-MUST-013 MUST**: Edge adapter persists/handles delivery identity robustly.
- **LAB-MUST-014 MUST**: OPC UA client/server communication is real in lab mode.
- **LAB-MUST-015 MUST**: Virtual PLC has durable-enough command identity/journal semantics for demonstrated recovery.
- **LAB-MUST-016 MUST**: Same command ID + same payload cannot cause a second physical effect.
- **LAB-MUST-017 MUST**: Same command ID + different payload is rejected.
- **LAB-MUST-018 MUST**: Console shows What/Wire/Code/State/Why/failure semantics.
- **LAB-MUST-019 MUST**: Protocol and real-vs-simulated badges are accurate.
- **LAB-MUST-020 MUST**: Source references point to code that actually executes.
- **LAB-MUST-021 MUST**: Payloads are derived from actual execution data and secrets are redacted.
- **LAB-MUST-022 MUST**: Architecture mini-map follows the current stage.
- **LAB-MUST-023 MUST**: In-progress session survives browser reload.
- **LAB-MUST-024 MUST**: Final physical gate precedes robot side effect.
- **LAB-MUST-025 MUST**: 3D viewer runs only after that gate and post-execution flow returns to verification/reconciliation.
- **LAB-MUST-026 MUST**: Read-only viewing/streaming cannot mutate robot/workflow state.
- **LAB-MUST-027 MUST**: ACK-before-effect loss scenario is demonstrated.
- **LAB-MUST-028 MUST**: ACK-after-effect loss scenario reaches uncertainty/reconciliation without duplicate physical action.
- **LAB-MUST-029 MUST**: Duplicate/redelivery scenario proves effect_count remains one.
- **LAB-MUST-030 MUST**: OPC UA/network interruption has deterministic documented behavior.
- **LAB-MUST-031 MUST**: Inconclusive observation can prevent false success.
- **LAB-MUST-032 MUST**: WMS outage after verified execution retries business reconciliation, not robot motion.
- **LAB-MUST-033 MUST**: UNKNOWN_OUTCOME is visible and explainable.
- **LAB-MUST-034 MUST**: Reconciliation queries the original command instead of issuing a fresh pick.
- **LAB-MUST-035 MUST**: Unit tests cover new state/domain logic.
- **LAB-MUST-036 MUST**: Integration tests cover DB/outbox/broker/edge/OPC UA/virtual PLC path.
- **LAB-MUST-037 MUST**: Browser E2E test drives a complete guided happy path through authorization -> 3D execution -> verification -> reconciliation.
- **LAB-MUST-038 MUST**: Browser/integration E2E test drives at least ACK-after-effect/UNKNOWN_OUTCOME/reconciliation.
- **LAB-MUST-039 MUST**: Browser reload/resume is tested.
- **LAB-MUST-040 MUST**: Double authorization/idempotency is tested.
- **LAB-MUST-041 MUST**: Duplicate AMQP/OPC command does not duplicate physical effect and is asserted.
- **LAB-MUST-042 MUST**: Existing test suite passes.
- **LAB-MUST-043 MUST**: Lint/type checks pass at repository policy level.
- **LAB-MUST-044 MUST**: CI runs the relevant tests or documents any environment-specific Blender limitation with a deterministic headless substitute.
- **LAB-MUST-045 MUST**: Docker/integration-lab startup has a documented smoke test and health checks.
- **LAB-MUST-046 MUST**: README architecture matches implementation.
- **LAB-MUST-047 MUST**: Clearly label simulated vs real-protocol components.
- **LAB-MUST-048 MUST**: Document local fast mode and full integration-lab mode.
- **LAB-MUST-049 MUST**: Document all acknowledgement meanings and uncertainty model.
- **LAB-MUST-050 MUST**: Include a reproducible demo script for happy path and lost-ACK recovery.
- **LAB-MUST-051 MUST**: No claim implies proprietary SICS.AI knowledge, exact HKM1800 behavior, or safety certification.

## DONE

The project is DONE only when:
1. every MUST criterion is PASS with inspectable evidence;
2. mandatory CI and publication workflow are green for the final commit;
3. no unresolved critical documentation drift is known;
4. SHOULD failures, if any, are documented;
5. OPTIONAL backlog is explicitly non-blocking.

If any MUST is not satisfied, the correct state is **NOT DONE**.
