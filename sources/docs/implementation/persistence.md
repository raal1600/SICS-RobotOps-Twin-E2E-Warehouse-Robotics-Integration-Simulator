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

The HTTP contract currently supports durable intake, current status, job lookup,
timeline, health, execution, reconciliation, metrics and presentation. No endpoint
reports an unimplemented success. OpenAPI is generated
alongside schemas and compared in tests.
