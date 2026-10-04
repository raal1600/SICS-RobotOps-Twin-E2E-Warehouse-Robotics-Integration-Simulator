# Runtime and data contracts

The normative vocabulary is PROJECT_PLAN.md. JSON Schemas are generated from
`robotops/domain/models.py` and the separate presentation contracts in
`robotops/blender/visualization.py`, plus test-lifecycle contracts in
`apps/api/test_sessions.py`, by `uv run python -m tools.export_contracts` and
compared by contract tests. Additional keys and arbitrary code fields are
rejected. Schema version 1.0 uses UTC timestamps, stable IDs, metres, an explicit
coordinate frame and calibration version. Quaternion norm tolerance is 1e-6.
Order quantities are one physical product per line; duplicate line/product IDs
are invalid. Transport retries reuse the complete original RobotCommand.

The enhancement adds typed catalogue/robotics contracts in `robotops/robotics`.
`WorldState`, `WorldObservation`, `ActionPlan`, `RobotCommand`, `CommandReceipt`
and articulated presentation records explicitly support schema 2.0. Pose remains
the same strict schema-1 primitive; HKM-profile poses require `cell_world` and
`hkm-cal-1`. Schema-2 records carry robot/catalogue/tool/frame versions, observed
machine telemetry, selected tool and deterministic trajectory intent as applicable.
`ToolSelectionDecision` retains every candidate's eligibility, score and reasons.
`TrajectoryIntent` carries calibrated grasp/target poses, ordered TCP waypoints,
attachment/tool phases, planner/collision versions and synthetic duration.
`ToolState` enforces unique mounted/rack occupancy; unknown tools/SKUs, nonfinite
dimensions/masses/poses and foreign calibration are rejected. Machine telemetry
is explicitly `SIMULATED_CELL_TELEMETRY`, with capture time and cell generation
matched to the observation; it is not presented as camera inference.
Schema-1 serialization excludes every absent schema-2 extension, preserving
historical command payload hashes. Golden fixtures from the actual baseline
prove original JSON, SQLite recovery and duplicate suppression are unchanged.
Both request and response JSON schemas remain strict; the compatibility serializer
does not publish an unrestricted map. `tests/contract/test_schemas.py` checks both.

`robotops/domain/ports.py` defines Brain, Runtime and Observer protocols. Runtime
operations are reset, world query, apply, journal query, cell state and capture.
The separate recorded_journal read supplies saved receipts to evidence views;
it cannot finish a pending Blender checkpoint. Reconciliation uses the original
recovery-capable journal query.
Only ObservationModel receives WorldState on the normal decision path; Verifier
receives WorldObservation. Observation coverage is explicit: a missing detection
alone never proves that a product left its source.

Durable intake, execution, status and reconciliation APIs are implemented.
`POST /jobs/{job_id}/reconcile` also accepts an active REQUIRES_INTERVENTION job
for explicit fresh evidence collection. It retains command identity, never sends
a pick, and may pause again. COMPLETED/FAILED and archived jobs cannot reopen.
`contracts/openapi.json` is generated and tested. The JobPlayback/MotionRecording
schemas document the read-only visualization path, including partial/missing
recordings. JobPlayback also includes the selected job's audit events and a
VisualScene, with explicit SAVED_START_SCENE or CURRENT_WORLD_REFERENCE provenance.
GET /cell/scene supplies the initial environment before any order exists.
GET /fixtures includes current presentation inventory and a fresh-scene blocking
reason. Its `products` and `product_sources` describe the saved world's own
fixture; `destination_id` identifies the destination independently of location
ordering. `source_id` remains a compatibility alias for the first source.
`robot_profile_version` and typed `catalogue` are populated for the six-SKU HKM
profile and null for legacy worlds. Inventory is a presentation aid, never
verification evidence. New order intake validates product identity, its configured
source and destination before creating jobs. Identical replays and identity
conflicts retain their existing semantics before this new-intake validation.
POST /fixtures/fresh-scene returns VisualScene after explicit fixture
preparation; HTTP 409 preserves pending/uncertain work. Runtime.reset accepts an
optional durable scene epoch for idempotent maintenance recovery. See
[ADR 0005](../adr/0005-explicit-fresh-fixture-scene.md).
PresentationSnapshot persists the starting WorldState solely for human replay.
None of these presentation records is accepted by the observation/verifier boundary.
DeliverySummary, DeliveryExecution and DeliveryPlayback group original jobs by
saved scene epoch for full-delivery replay. GET /deliveries and
GET /deliveries/{delivery_id}/playback are read-only. Duplicate jobs or mixed
saved scene identities are rejected by the delivery contract. Ordering uses
durable execution events rather than intake timestamps (ADR 0006).
Current evidence is in GOAL_PROGRESS.md and ACCEPTANCE_REPORT.md.

GET /simulation-tests returns TestHistory: the active identity and numbered
SimulationTest summaries with their persisted job outcomes. POST /simulation-tests
accepts StartTestRequest with a UUID request_id and creates one independent world.
The UUID is idempotent even after later tests; retrying never reactivates an archive.
Original routes retain their paths; another test uses `/simulation-tests/<UUID>`
before the same routes. Writes to any archive return 409 TEST_ARCHIVED_READ_ONLY;
creation during work returns 409 TEST_OPERATION_IN_PROGRESS. Only the active test
is recovered on startup. Existing business schemas and verdict rules are unchanged.
Fresh API/desktop worlds and Start new test use `Settings.hkm()`; each reopened
world resolves its own persisted execution settings. Historical three-product
worlds, their commands and recordings are not migrated. Explicit CLI settings
configure a new world and cannot reinterpret an already saved world.

The local dashboard also serves bounded presentation assets at `/ui/theme.css`
and `/ui/workflow-guide.js`. The guide is a pure presentation of persisted job and
verification records. No domain schema, transition, or command endpoint changed
for ADR 0009; OpenAPI records the confined new asset routes.
