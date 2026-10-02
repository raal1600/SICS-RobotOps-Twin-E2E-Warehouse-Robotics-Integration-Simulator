# Deterministic runtime and controller journal

P2 implements the headless Runtime protocol in `robotops/cell/runtime.py` and a
logical `CellController`. It shares transaction utilities with Store, using a
separate database and no business-state decisions. The first empty initialization
is atomic. Restart reads the existing world; it never resets an existing scene.

World update, one PICK_EFFECT event and final controller receipt commit together
for this discrete synthetic adapter. Duplicate IDs with identical canonical
payloads return the original receipt. Changed payloads conflict. These semantics
are limited to this simulator and do not assert physical exactly-once behavior.

DROP_ACK_AFTER_EFFECT raises only after the committed move and SUCCEEDED journal.
DROP_ACK_BEFORE_EFFECT commits a REJECTED/PROVEN_NOT_STARTED receipt without a
move, then loses the acknowledgement. Communication timeout alone is never used
to distinguish these outcomes. Reconciliation must also obtain a fresh observation.

Cell faults and logical E-stop are persistent states. Reset goes through RESETTING
to READY, preserves world/journal, and changes the generation. Old plans are
invalid. Scene reset creates a new epoch without deleting earlier command history.
All non-READY states block new motion. This is not a safety-rated cell.

RobotGateway accepts only the persisted original RobotCommand and imports immutable
RobotEvents into the business timeline. Runtime events are linked through command
identity to the durable intent. Transport outcomes and controller outcomes remain
distinct. The headless capture operation writes a JSON diagnostic; it is never
labelled a Blender screenshot. The Blender adapter is P4 work.
