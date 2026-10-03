# Persistence and ownership

`Store` opens short SQLite BEGIN IMMEDIATE transactions, with WAL and FULL
synchronization. Atomic intake writes an order, its jobs, idempotency mapping and
causal audit events. Canonical JSON (sorted keys, including defaults) is hashed;
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
Live reads continue. Startup recovers only the active world; all prior outcomes
and evidence remain archived. See [ADR 0007](../adr/0007-independent-simulation-tests.md).
