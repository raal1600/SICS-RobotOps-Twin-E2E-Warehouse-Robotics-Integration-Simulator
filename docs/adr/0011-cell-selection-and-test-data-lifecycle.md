# ADR 0011: Cell selection and explicit test-data deletion

Accepted design, 2026-10-04. Implementation verification is recorded separately
in GOAL_PROGRESS.md and ACCEPTANCE_REPORT.md. The earlier HKM acceptance at
`ca7798798f916c8130e1833cf16b4d4d3f10d546` does not attest this change.

## Context

Operators need to choose the cell for a new independent simulation test and
remove unwanted test data in the same application window. The current release
has one selectable cell: the HKM-inspired six-product/six-tool cell. Historical
Cartesian tests must remain understandable without offering an obsolete cell as
a new-test option. Opening, replaying or restarting a test must not delete data.

## Decision

Expose a typed cell-profile registry through `GET /cell-profiles`. Its stable
profile IDs, names, descriptions, product/tool counts and `selectable` flag drive
the new-test selector and history labels. `hkm_inspired_v1` is the default and
only selectable profile. `legacy_cartesian_v1` identifies saved legacy tests;
its presence in the registry does not make it selectable. Future cells require
an explicit registry implementation and their own verification, not free-form
runtime names or executable configuration supplied by the browser.

`POST /simulation-tests` accepts a UUID `request_id` and `cell_profile_id`.
Creation initializes an independent world for that profile before switching the
active pointer. Reopening uses the saved world's settings. Profile selection
never changes an existing world or triggers a pick. Test summaries carry the
profile ID and display name; profile selection and execution/observation faults
are separate choices.

Deletion is a separate, explicitly confirmed data-management action:

- `POST /simulation-tests/{test_id}/delete` accepts a UUID `request_id` and
  targets exactly that registered test.
- `POST /simulation-tests/clear` accepts a UUID `request_id` and
  `expected_test_ids`. The first request must match the current live test set;
  a changed inventory requires review and a new confirmation.
- Both return `TestDeletion`, containing the request identity, deleted test IDs,
  `cleanup_pending` and the resulting `TestHistory`.

The UI names the scope and asks for confirmation before either request. This
confirmation is an operator affordance, not production authorization: the app
remains a local loopback demonstration. Tests exercise deletion only in isolated
temporary data roots; implementing the feature does not authorize deleting the
owner's existing simulation data.

Deleting the active test leaves `active_test_id` null. Clearing all tests does
the same. An archive is never automatically promoted into a writable test, and
an empty catalog does not silently recreate the original world. The operator
explicitly starts a new test to obtain another active world. Deleting an archive
leaves a different active test unchanged.

## Persistence, concurrency and cleanup

The test catalog serializes lifecycle mutations. A separate SQLite `access.db`
uses shared locks for complete HTTP responses, including artifact downloads;
deletion acquires its exclusive lock before the catalog transaction.
Running work, active claims or fixture maintenance prevents
deletion. This protects the runtime/artifact owner while files are in use; direct
Engine workers still require separate data roots because they do not acquire the
dashboard lifecycle locks.

Durable deletion tombstones and operation receipts bind each request to its
original target set. A retry of clear-all cannot erase tests created later, and
deleted identities cannot be recreated by replaying an old creation request.
Logical removal precedes bounded file cleanup. If cleanup is interrupted, the
response reports `cleanup_pending`; a retry or restart resumes the same cleanup
instead of executing or restoring the deleted world.

Only registered, application-owned world paths are eligible. UUID directories
are confined beneath `simulation-tests`; the original world's known files and
artifact paths are handled explicitly (configured database basenames retained in
`workspace_meta`, their SQLite sidecars and `blender-artifacts`). An original
database outside the workspace is rejected. Validated UUID world directories are removed
in full. The parent data directory, catalog, access barrier, deletion
receipts/tombstones and files outside these owned world paths remain.
Reparse points or paths outside the ownership boundary are rejected. Clear-all
means registered simulation test data, not secure erasure of every byte under
the desktop application's directory.

## Preserved semantics and consequences

ADR 0007 continues to govern independent worlds and read-only historical
inspection. This decision adds explicit retention controls; ordinary navigation,
Start new test, closing/reopening the app and cell reset still preserve retained
history. Deletion is not reconciliation, a job transition, failure, success or a
physical operation. Deleting an uncertain test discards that selected evidence
after confirmation; it never changes UNKNOWN_OUTCOME or REQUIRES_INTERVENTION
into a resolved verdict. No lifecycle action sends a product-transfer command.

The existing 110 MUST criteria and their thresholds remain unchanged. Additional
tests cover profile metadata/selection, saved legacy interpretation, empty
catalog restart, explicit deletion scope, stale clear snapshots, idempotent
retries, in-flight operations, interrupted cleanup and path confinement. Browser
tests cover cancellation, confirmation, history refresh, stale responses and
the empty-state workflow. Generated contracts, diagrams and publication must be
rebuilt from their source; historical acceptance remains immutable.
