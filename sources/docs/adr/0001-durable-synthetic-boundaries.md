# ADR 0001: Durable synthetic boundaries

Accepted, 2026-10-02. Classification: SIMULATOR_DESIGN.

Use Python 3.13, strict Pydantic wire contracts and two SQLite stores: the
orchestrator owns business state; the runtime owns world snapshots and the
controller journal. No shared transaction spans these boundaries. Headless
simulation commits its synthetic world change and effect journal atomically.
Blender will execute a bounded, checked-in script in a separate background
process. It will checkpoint the logical scene state and reconstruct scene objects
from that checkpoint. A command left in RUNNING after a crash is uncertain and
must not be replayed automatically.

This is the batch form of the proposed programmatic Blender boundary, avoiding
a network listener or background-thread scene mutation. The renderer is not a
sensor; ObservationModel explicitly degrades synthetic state. Verifier imports
only observation/command contracts. Tests may read ground truth.

One cell serializes work. Claims and revisions are persisted atomically. A
lease expiry permits recovery, never an inference that no effect occurred.
The API is the mock ERP/WMS status contract: verified completion is returned by
GET /orders. A separate remote ERP outbox is optional future integration; the
older report's ERP_SYNC_PENDING and MANUAL_REVIEW names are replaced by the
normative state names. No acceptance criterion is weakened.

No model adapter or MCP is required at runtime. Model suggestions, if added,
must pass the same schema and semantic validation as DeterministicBrain.
