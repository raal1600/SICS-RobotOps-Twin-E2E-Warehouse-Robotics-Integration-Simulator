# ADR 0005: Repeatable fixture scenes without discarding history

Accepted locally 2026-10-03. Publication and commits are deferred at the user's request.

The persisted desktop fixture can be exhausted: all products have already moved
to the destination. The old selector still offered these products for source
picks, and the replay hid SOURCE_NOT_OBSERVED behind a generic planning error.
The source precondition was correct; the repeat-demo workflow was incomplete.

The UI now displays current fixture inventory, disables unavailable products,
and explains planning rejections. An explicit Start fresh scene action invokes
POST /fixtures/fresh-scene and creates a new scene epoch with products at source.
It retains orders, immutable starting scenes, recordings, journals and audit
history. This is fixture preparation, never another pick or a retry. Logical
cell reset remains separate and never replenishes products.

Store serializes the maintenance intent with intake and worker claims. Every
existing job must be COMPLETED or FAILED and no live worker may own the cell.
The durable intent blocks new intake/claims without holding a workflow database
transaction during a runtime call. Runtime reset is idempotent by requested scene
epoch and refuses unresolved controller commands. Its checkpoint and reset event
commit together. Startup completes a pending intent with the same identity,
including a crash after runtime reset but before workflow acknowledgement.
Delayed duplicates cannot restore an older scene over a newer one.

UNKNOWN_OUTCOME and REQUIRES_INTERVENTION cannot be cleared with this action.
Old command delivery still returns its original journal result without applying
another physical effect. Fixture inventory is human-facing simulator state;
Brain and Verifier continue using the observation contract.

Regression coverage reproduces exhausted inventory, picks all products through
Blender across two scenes, checks saved history/replays, blocks unresolved work,
and exercises interrupted maintenance and concurrent intake. This fixes local
demo usability without changing the job state machine or acceptance thresholds.
