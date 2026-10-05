# Persistence and ownership

`Store` opens short SQLite BEGIN IMMEDIATE transactions, with WAL and FULL
synchronization. Atomic intake writes an order, its jobs, idempotency mapping and
causal audit events. Canonical JSON (sorted keys and schema-specific serialized
defaults) is hashed; schema-1 records omit schema-2 extensions so original command
digests remain valid. Strict golden fixtures verify the historical wire bytes;
an order ID or key cannot be reused with changed content. Identical requests
return the existing current semantic result, including after restart.

One persisted cell lease contains job ID, owner, expiration and monotonically
increasing fence. Every mutation checks ownership and expiration. Expired owners
cannot transition or persist an intent. Unknown/executing/verifying/reconciling
jobs quarantine the cell after lease expiration; intervention also blocks other
jobs. Expiry is never evidence of no effect. Runtime deduplication adds a second
independent boundary in P2. Transactions do not encompass external runtime calls.

Job transitions and audit events commit together. Commands and plans are immutable
and durable before dispatch. Transition guards forbid a direct timeout-to-FAILED
path and require verification/reconciliation evidence for resolution. History is
never cleared by a cell reset. Authoritative world checkpoints and controller
command journals belong to the runtime database. PresentationSnapshot stores a
separate immutable starting world in the workflow record store before a new job
executes, under the cell claim. It supports historical no-motion replay and is
never verification evidence. Legacy jobs without this record are labelled as
current references instead of inventing their historical layout. See ADRs 0001
and 0004.

New schema-2 worlds persist runtime settings, robot TCP/profile and mounted/rack
tool state. Reopening resolves those saved settings; a new application default
cannot reinterpret an existing world. Old schema-1 worlds are resolved in memory
without writing migration metadata merely because history was viewed. Tool
selection and trajectory intent remain immutable command/plan evidence. Tool
preparation events retain the original pick identity and do not increment the
product-transfer effect count.

Only COMPLETED and FAILED are terminal. Explicit re-observation may claim an
intervention job and enter RECONCILING with identity-matched evidence; normal
execution and automatic restart recovery cannot claim it. Each assessment is an
immutable record, returned in durable insertion order with the original causal
transitions retained. No database migration or rewriting of old jobs is required.
The same cell fence prevents competing evidence collectors (ADR 0008).

The HTTP contract currently supports durable intake, current status, job lookup,
timeline, health, execution, reconciliation, metrics and presentation. No endpoint
reports an unimplemented success. OpenAPI is generated
alongside schemas and compared in tests.

The dashboard adds a durable test catalog at `simulation-tests/catalog.db`.
Each new test has separate workflow/runtime files and Blender artifacts beneath
its UUID directory. The original database paths are preserved. Start new test
atomically switches the active pointer after initialization; prior worlds become
read-only. Request UUIDs prevent duplicate creation or reactivation on a late retry.
The catalog transaction spans API writes, including runtime calls, to serialize
test creation with ongoing work across hosts. It does not extend the workflow or
controller transactions. Direct Engine workers must use separate demo data.
Live reads continue during ordinary execution. Startup recovers only the active world; all prior outcomes
and evidence remain archived unless the operator explicitly deletes that test.
See [ADR 0007](../adr/0007-independent-simulation-tests.md).

ADR 0011 extends the catalog with cell-profile metadata and explicit retention
operations. A new test selects a registered cell; a saved test's profile is
durable and resolved from its own world. Legacy tests remain readable, with no
scene migration or new selectable legacy option.

ADR 0013 supersedes permanent deleted rows. Selected deletion and delete-all
commit temporary cleanup intent before bounded removal; completed cleanup removes
the test row and releases its display number. New tests use the lowest free
positive number, starting at 1 when empty. Surviving labels and UUIDs are stable.
Request/payload SHA-256 digests preserve duplicate suppression without retaining
raw deleted IDs, payloads or target lists. Legacy raw receipts are converted,
and old tombstones are cleaned up; retained worlds are untouched.

Clear keeps the same test identity, number and profile/settings. It commits a
revision increment and pending reset intent, removes the old world files, creates
an empty world with a fresh scene epoch, then activates that test. Pending clear
blocks new execution/creation. Retry/startup finishes that explicit reset without
recovering a discarded command. Cached engines are invalidated by revision;
the UI sends X-Test-Revision to fence stale writes. Repeated clears preserve any
newer orders. Clear is deliberate evidence disposal, not a business verdict.

The active pointer is nullable: deleting its test leaves no active world, including
after restart. Archives remain archives unless explicitly cleared for retry; creating a new
test is the other way to obtain a writable world. A retained active test survives deletion of another test.
A separate `simulation-tests/access.db` uses SQLite DELETE-journal shared locks
for the entire HTTP response lifetime, including artifact downloads. Deletion
requires its exclusive lock before the catalog transaction, so it cannot race
file use. Live jobs, leases and maintenance prevent deletion. The workspace
application factory opens the catalog first; a workspace marker prevents an
empty catalog from recreating the deleted original world.
The client first pauses polling and drains its own outstanding JSON and snapshot
response bodies before confirmed management. Its five-second stalled-view wait
sends no lifecycle request, leaving data intact for explicit retry. This client
coordination does not remove server protection for other readers or running jobs.

Only registered application-owned paths are removed. UUID world directories stay
beneath `simulation-tests`; the original world's known database/artifact paths
are handled explicitly: its configured workflow/runtime database filenames
(normally `workflow.db` and `runtime.db`), their SQLite sidecars and
`blender-artifacts`. `workspace_meta` retains those original basenames; a database
outside the workspace is not an eligible cleanup path. UUID test directories are
removed in full after validation.
Reparse points and unsafe paths are rejected. Catalog, access barrier,
anonymous request guards, parent directory, other files outside the owned
world paths and unrelated launcher/browser data remain. This is retention management, not a secure-erasure
guarantee or a job-state transition. Ordinary cell reset still never clears history.
See [ADR 0013](../adr/0013-reusable-test-lifecycle.md).
