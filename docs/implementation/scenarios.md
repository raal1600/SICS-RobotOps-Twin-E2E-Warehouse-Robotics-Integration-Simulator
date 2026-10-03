# Understand execution scenarios and observation modes

These are deliberately injected simulator faults, not diagnoses of real hardware.
Descriptions assume the standard fixture settings. The persisted journal and
assessed WorldObservation determine each actual outcome; the 3D view is illustration.

**Execution scenario** applies when Create and run order starts a new pick. It can
change planning, cell control, acknowledgement delivery or the first observation
after movement. **Observation for this review** applies only when Reconcile or
Observe again captures new evidence for the original command. It does not repeat
the pick, rewind the scene, or change an earlier assessment. Selecting either
option alone does not execute anything.

Both selectors show the stage, **What this simulates**, **Key difference**, and the
expected behavior. **Compare all execution scenarios** and **Compare all
observation modes** let the operator read every option without running it.

## Execution scenarios

| Scenario | What is deliberately changed | Why its result differs |
| --- | --- | --- |
| Happy path | No fault is injected. Plan, movement, reply and fresh verification follow the normal path. | Baseline for comparing the fault cases. |
| Lose acknowledgement after effect | The controller moves the product and records the effect, but its reply is withheld. | The movement happened. A timeout still leaves the orchestrator uncertain until reconciliation. |
| Lose acknowledgement before effect | The controller records that the pick never started, and its reply is withheld. | No movement happened. The orchestrator sees the same missing reply as the after-effect case and must establish no effect from evidence. |
| Contradictory observation | The first post-pick observation reports the same product in incompatible locations. | Conflicting detections, even though the physical pick occurred. |
| Low-confidence observation | The first post-pick observation contains the product and location, with a deliberately reduced confidence score. | A present but unreliable detection; confidence is the failing quality check. |
| Stale observation | The first post-pick observation is given an old capture time. | Its age is unacceptable even if the reported position looks plausible. |
| Logical E-stop | A deliberate stop request puts the simulated cell into its logical stopped state before movement. | A requested stop, not a detected equipment error. It is not safety-rated. |
| Cell fault | A simulated detected error puts the cell into its faulted state before movement. | An error rather than an operator stop; both need an explicit logical reset. |
| Invalid Brain output | A planner reply violates the required action-plan format and is rejected. | A reply arrived but was invalid; no robot command is created. |
| Brain timeout | The planner is treated as having missed its response deadline. | No usable plan in time, instead of a malformed reply. This is before command creation, unlike a lost acknowledgement. |

The before/after lost-ack cases deliberately have the same uncertain business
status despite different physical results. Silence cannot tell them apart. Logical
E-stop, cell fault and Brain failures all keep the product still, but fail at
different stages and leave different causal evidence. The three observation-fault
execution scenarios all allow movement but reject a different quality property.

## Observation modes for review

| Mode | Meaning of the new capture | Key difference |
| --- | --- | --- |
| Normal observation | Capture without intentional sensing degradation. | Checks the current evidence against the original journal. It can prove completion or no effect, or remain inconclusive; normal does not guarantee success. |
| Contradictory evidence | The same product is reported in two different locations. | Multiple incompatible detections; no extra product is created in the world. |
| Low confidence | A product detection is present but its confidence score is reduced. | Weak evidence instead of absent or conflicting detections. |
| Stale evidence | The new capture receives an old timestamp to simulate a delayed report. | Tests freshness, without replaying an old scene or moving any product. |
| Missing evidence | The observation contains no detected products or location coverage. | No usable detections. Absence alone does not establish removal or failed motion. |

Contradictory, low-confidence and stale options exist in both selectors. Their
degradation mechanism is the same; the execution selector applies it to the first
check after a new pick, while the observation selector applies it to a later
reconciliation capture. Every review retains the original command and all prior
assessments. Repeated bad evidence remains inconclusive; changing to Normal only
changes the next capture mode and requires an explicit review action.

Implementation: `apps/erp_ui/workflow-guide.js` owns the UI descriptions and
comparison data. Fault semantics remain in `robotops/workflow/engine.py`,
`robotops/cell/runtime.py`, `robotops/blender/adapter.py`,
`robotops/observation/model.py` and `robotops/observation/quality.py`.
See [operator workflow](operations.md) and [reconciliation rules](reconciliation.md).
