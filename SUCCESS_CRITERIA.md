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

## DONE

The project is DONE only when:
1. every MUST criterion is PASS with inspectable evidence;
2. mandatory CI and publication workflow are green for the final commit;
3. no unresolved critical documentation drift is known;
4. SHOULD failures, if any, are documented;
5. OPTIONAL backlog is explicitly non-blocking.

If any MUST is not satisfied, the correct state is **NOT DONE**.
