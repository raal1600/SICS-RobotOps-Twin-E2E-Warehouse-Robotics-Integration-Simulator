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
never cleared by a cell reset. Snapshot/command journals belong to the runtime
database, not the business store. See ADR 0001.

The HTTP contract currently supports durable intake, current status, job lookup,
timeline and health. Execution/reconciliation/metrics are added with their owning
components; no endpoint reports an unimplemented success. OpenAPI is generated
alongside schemas and compared in tests.
