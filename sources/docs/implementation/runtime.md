# Deterministic runtime and controller journal

P2 implements the headless Runtime protocol in `robotops/cell/runtime.py` and a
logical `CellController`. It shares transaction utilities with Store, using a
separate database and no business-state decisions. The first empty initialization
is atomic. Restart reads the existing world. Only an explicitly requested,
persisted fresh-scene intent may resume fixture preparation during recovery.

World update, one PICK_EFFECT event and final controller receipt commit together
for this discrete synthetic adapter. Duplicate IDs with identical canonical
payloads return the original receipt. Changed payloads conflict. These semantics
are limited to this simulator and do not assert physical exactly-once behavior.

Fresh worlds use the six-product HKM-inspired profile. The command includes its
selected tool, candidate reasoning, calibrated grasp/target poses and segmented
trajectory. The machine boundary independently checks current product/source,
tool availability, workspace and conservative geometry before applying a transfer.
Tools parked in the rack are obstacles except for the matching registered vertical
engage/uncouple motion. Tool changes are deterministic preparation under the same
command; their phases and final occupancy persist. `PICK_EFFECT` still means one
product transfer. A tool change is never counted as another business effect.

Configured small observation error uses a shared 5 mm synthetic source-contact
centering bound at grasp, separate from observation/verifier pose tolerance.
Frame/calibration/orientation and the final target remain strictly checked.
This bounded contact abstraction does not model physical grip forces or accuracy.

DROP_ACK_AFTER_EFFECT raises only after the committed move and SUCCEEDED journal.
DROP_ACK_BEFORE_EFFECT commits a REJECTED/PROVEN_NOT_STARTED receipt without a
move, then loses the acknowledgement. Communication timeout alone is never used
to distinguish these outcomes. Reconciliation must also obtain a fresh observation.

Cell faults and logical E-stop are persistent states. Reset goes through RESETTING
to READY, preserves world/journal, and changes the generation. Old plans are
invalid. Scene reset creates a new epoch without deleting earlier command history.
An explicit fresh-scene action restores fixture products, with a durable workflow
maintenance guard and an idempotent runtime epoch checkpoint. It is blocked by
pending/uncertain jobs, active owners or unresolved controller commands. See
[ADR 0005](../adr/0005-explicit-fresh-fixture-scene.md).
All non-READY states block new motion. This is not a safety-rated cell.

RobotGateway accepts only the persisted original RobotCommand and imports immutable
RobotEvents into the business timeline. Runtime events are linked through command
identity to the durable intent. Transport outcomes and controller outcomes remain
distinct. The headless capture operation writes a JSON diagnostic; it is never
labelled a Blender screenshot. The implemented Blender adapter uses the same
reset identity and renders the prepared fixture through its bounded runtime.

## Read-only evidence

Runtime.recorded_journal reads the persisted receipt without recovery. Evidence
GETs use this boundary so viewing a saved test cannot finish a pending Blender
checkpoint. Runtime.journal remains the recovery-capable query for reconciliation.
See ADR 0007 for independent test storage and active-only restart recovery.
