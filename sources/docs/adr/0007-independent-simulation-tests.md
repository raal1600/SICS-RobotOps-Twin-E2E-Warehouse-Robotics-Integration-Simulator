# ADR 0007: Independent simulation tests in one window

Accepted locally 2026-10-03. No commit, push or public deployment requested.

Users need to try every execution/observation combination with the same products,
including after UNKNOWN_OUTCOME or REQUIRES_INTERVENTION. Clearing those states
in the same physical world would erase uncertainty. Opening another window for
each combination is unnecessary.

The dashboard always provides Start new test and Test history. Starting a test
creates a separate workflow database, runtime world, command journal and Blender
artifact directory. The previous test becomes read-only with its exact outcomes,
observations, events and replay retained. This is an experiment boundary, not a
job transition, reconciliation, cell reset or retry. It is available for every
execution/observation combination. Running work must finish first.

A durable SQLite catalog lives at `simulation-tests/catalog.db` beneath the
original data directory. The original world remains at its existing paths;
new worlds use `simulation-tests/<UUID>/workflow.db` and `runtime.db`. Catalog
rows store test identity, creation time and display number; a single pointer
selects the active test. The request UUID makes creation idempotent, including a
late retry after a different test has become active. Initialization precedes the
atomic pointer update; a failed transaction leaves the previous test active.

All API mutations are pinned to a test identity. Original routes retain `/orders`,
`/jobs/...` etc.; new worlds use `/simulation-tests/<UUID>` plus the same routes.
Archived mutations return 409 TEST_ARCHIVED_READ_ONLY. A catalog BEGIN IMMEDIATE
transaction spans each mutation, including runtime execution. This serializes
creation against in-flight run/reconcile/restock/import across API processes.
Conflicting operations return 409 TEST_OPERATION_IN_PROGRESS. Live reads continue.
Additional checks reject active leases, unfinished execution and maintenance.
Workflow/controller transactions retain their existing shorter boundaries.
Do not run external direct Engine workers against dashboard-owned data: they do
not participate in the catalog lock. This remains a local demonstration host.

Startup recovers only the catalog's active world. An archived UNKNOWN_OUTCOME
stays unknown even when another world's restart performs reconciliation. Reads,
including metrics and replay, cannot change archived evidence. The UI disables
execution, reconciliation, reset and legacy recording import while viewing an
archive; its camera, playback and evidence controls remain usable.
Evidence GETs use Runtime.recorded_journal, a pure persisted-receipt read.
Runtime.journal remains the recovery-capable query used by reconciliation;
Blender may complete a valid pending checkpoint there. Even a valid response
arriving after a timeout cannot be committed by viewing archived evidence.

Scenario/observation selections are configuration only and survive Start new
test. They never reset or run anything. This supersedes ADR 0006's automatic
restock on scenario selection. Explicit restock remains available for a resolved
test, and a depleted delivery can still prepare its next delivery explicitly.
The existing restock and uncertain-outcome guards are unchanged. History and
return-to-current navigation stay in the same window. Late responses from a
previous view cannot replace the current scene/evidence.

Tests cover all execution/observation combinations, unchanged archived evidence,
both original/prefixed write rejection, idempotency, concurrent hosts, active
leases, maintenance, active-only restart and original Blender frames/artifacts.
The actual dashboard scripts cover all 50 UI combinations and historical replay.
WorldState remains human illustration only; Verifier still receives observations.
