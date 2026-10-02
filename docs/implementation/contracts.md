# Runtime and data contracts

The normative vocabulary is PROJECT_PLAN.md. JSON Schemas are generated from
`robotops/domain/models.py` by `uv run python -m tools.export_contracts` and
compared by contract tests. Additional keys and arbitrary code fields are
rejected. Schema version 1.0 uses UTC timestamps, stable IDs, metres, an explicit
coordinate frame and calibration version. Quaternion norm tolerance is 1e-6.
Order quantities are one physical product per line; duplicate line/product IDs
are invalid. Transport retries reuse the complete original RobotCommand.

`robotops/domain/ports.py` defines Brain, Runtime and Observer protocols. Runtime
operations are reset, world query, apply, journal query, cell state and capture.
Only ObservationModel receives WorldState on the normal decision path; Verifier
receives WorldObservation. Observation coverage is explicit: a missing detection
alone never proves that a product left its source.

P0 establishes these contracts; behavior and OpenAPI are implemented in following
milestones. Current evidence and remaining work are in GOAL_PROGRESS.md.
