# HKM-inspired warehouse cell adaptation

Status: implementation under verification; final acceptance remains pending.
Base: `eaf35b499e80a5ce31b2ea3a24fbfa010bc67c98`.
All values and mechanics below are SIMULATOR_DESIGN unless explicitly identified
as attributed manufacturer information in the source registry. This document
describes the new implementation and its required boundaries; the archived
baseline did not implement six tools. Targeted evidence is scoped separately
from the pending full enhancement acceptance.

## Boundary and versioning

The existing ERP/API/workflow/Brain/validation/gateway/cell/Blender/observation/
verification/reconciliation architecture remains. The fixed Blender subprocess
accepts typed versioned data; neither free-form prompts nor generated Python
cross the command boundary. Development-time authoring tooling is separate.

The visual model is `HKM_INSPIRED_VISUAL_KINEMATICS_V1`: a TCP pose maps
deterministically to base yaw, wrist pose and connected parallel-link endpoints.
It is not exact HKM1800 inverse kinematics. Shared stable object identities and
position/quaternion/visibility primitives must keep Blender and browser aligned.
Motion evidence additionally carries phase, attachment, tool and rack state.

New wire versions require strict contract tests and explicit compatibility.
Legacy three-product scenes, positional recordings, command payload hashes and
saved user tests retain their original interpretation. Unsupported historical
formats must be identified honestly, never silently drawn as the new machine.
No destructive migration or re-execution of historical commands is authorized.

Implemented entry-point compatibility: fresh API/desktop worlds and Start new
test now use `Settings.hkm()`. A reopened world's persisted execution settings
remain authoritative, including legacy three-product history. `/fixtures` gives
per-product source IDs, the actual destination and the typed canonical catalogue;
legacy worlds return null catalogue/profile metadata. API intake validates new
orders against that fixture after resolving existing idempotency identities.
`tests/integration/test_hkm_api.py` exercises these paths and six deterministic
tool selections through actual HTTP routes; this targeted evidence is not a
claim that the whole enhancement has passed acceptance.

## Cell and fixtures

The original procedural cell contains a base-centered hybrid-inspired
manipulator, six source totes A-F, destination tote and short conveyor, six tool
docks, control cabinet, stack light, logical E-stop, enclosure, operator gate and
three useful cameras. Stable names identify each robot link, tool, location,
product and camera. Camera intrinsics/model, pose, frame and calibration are
versioned; overhead and side cameras represent synthetic sensor viewpoints.
Source/destination totes use original synthetic access lips of 0.03 m at the
front and 0.05 m at the right, with full configured left/back walls. Their shared
geometry also supplies preflight obstacle bounds; they do not reproduce a
manufacturer tote or a customer's installation.

The conservative synthetic target envelope is radius 1.55 m, TCP Z 0.16-1.15 m
and safe transfer Z 1.02 m in a 4.60 x 4.20 m cell. Public-reference reach values
are descriptive metadata only, never validation thresholds or calibrated robot
specifications. Frame relations include `cell_world`, `robot_base`, `robot_wrist`,
`tool_flange`, `active_tool_tcp`, cameras, sources and destination. Pose contracts
carry meters, quaternion, frame and calibration; captures carry UTC timestamps.

The canonical catalogue resolves each SKU to dimensions, mass range, geometry
and preferred/compatible tools. Runtime data is the source for
[generated fixtures, tool constraints and compatibility](../generated/product-tool-catalogue.md).
`python -m tools.generate_robotics_docs --check` detects stale generated text;
`make docs` regenerates it and the publication matrix from the same JSON.
These are synthetic fixture dimensions and tools, not customer product data or
claims that Cognibotics supplies this exact tooling set. Catalogue definitions
alone do not establish end-to-end acceptance.

## Tool and trajectory semantics

Selection filters compatibility, actual mass, geometry and availability before
deterministic scoring. Stable catalogue order and tool identity break ties.
Persisted candidates explain why a preferred tool won and why alternatives lost.
Normally one tool is mounted and five remain visible in their rack docks. During
the verified empty-flange phase, all six tools are temporarily in their docks.

Under the original pick command, a tool-change sequence records request, safe
retreat, old-tool dock/release, empty flange verification, requested-tool
engagement/identity verification and retreat/completion. Correct already-mounted
tools emit a no-change decision. Unavailable tools cause zero transfer effects.
Tool preparation does not increment `effect_count`.

The pick trajectory includes HOME, optional preparation, PRE_GRASP, APPROACH,
GRASP, GRASP_CONFIRM, LIFT, SAFE_TRANSFER, PRE_PLACE, PLACE, RELEASE,
RELEASE_CONFIRM, RETRACT and a safe finishing pose. Vertical entry/exit and
elevated transfer use deterministic smooth interpolation. Tool and carried-product
clearance inflate obstacles for sampled segment preflight. A fixed finite set of
alternatives is attempted; failure yields
`NO_COLLISION_FREE_SYNTHETIC_TRAJECTORY` before a transfer.

Host and fixed Blender runtime share a 0.005 m synthetic grasp-contact tolerance.
Within it, attachment deterministically centers the product on the commanded
grasp; this accommodates configured millimetre observation noise. Larger source
contact errors are rejected before transfer. Commanded grasp and approach/grasp
waypoints must agree exactly. This is bounded simulator behavior, not measured
gripper compliance, computer vision or validated contact physics; verification
still uses its separately assessed observation and uncertainty contract.

The Blender runtime manifest records each fixed script/helper/catalogue hash
and an aggregate closure hash, in addition to the Blender version and legacy
entry-script hash, so a helper change cannot masquerade as an unchanged runtime.

These checks are conservative synthetic collision preflight, not certified robot
path planning or articulated-body physics. Synthetic motion duration and playback
speed are separate from real application latency and UTC evidence chronology.

## Evidence and operator experience

`WorldState -> ObservationModel -> WorldObservation -> Verifier` remains the only
normal observation path. Seeded/configured missing, low-confidence, stale,
contradictory and pose-uncertain data must remain deterministic. Active-tool
telemetry is marked `SIMULATED_CELL_TELEMETRY`; no pixel-analysis claim is made.

The operator should see order/job/command, cell state, SKU/tool, current phase,
observation confidence/version and persisted selection reasons. Lost acknowledgement
must distinguish completed effect, lost delivery and unknown workflow knowledge.
Reconciliation shows the original journal, fresh assessed observation and decision.
Contradictory evidence remains intervention even if presentation shows a transfer.
Normal observations may later resolve the same command without another pick.

Operator, overhead, side and Follow TCP views plus play/pause/scrub/step and
0.25x-4x speed are presentation only. Full delivery and historical replay cannot
mutate commands, observations, jobs or effects. Saved still images remain under
collapsed technical details. An unobtrusive limitations panel states that this
is not exact CAD, validated kinematics/dynamics, safety-certified control, SICS
proprietary software or real-world performance validation.

## Validation plan and current evidence

[Baseline manifest](../evidence/acceptance/20261004T000708/manifest.json) records
389 tests per run: 388 passed and one existing obsolete UI-label assertion failed
in both runs. Coverage was 89.11%; 101 UI checks, seven real Blender demos,
security, types, lint, drift and local publication passed. Exact preserved reports
and archive hashes are indexed by
[baseline provenance](../evidence/hkm-baseline-eaf35b4/provenance.json).

New acceptance covers catalogue/selector, workspace/collision negatives, transform
recording/history compatibility, actual Blender articulation/tool exchange,
ground-truth dependency guards, six-tool showcase, uncertainty/idempotency/restart,
read-only UI/evidence, documentation and final exact-SHA CI/Pages/PDF evidence.
No planned test name or successful render counts as proof of business verification.
The [actual Blender/native scoped run](../evidence/hkm-blender-local/result.json)
contains 12 passing Blender tests, six preferred tools/six exact-one transfers,
actual camera/hierarchy inspection, read-only saved-scene export, conservative
uncertainty/restart handling and eight native lifecycle checks. It also preserves
the initial defects and their fixes. These working-tree checks do not replace
the pending full repeated suite or exact-SHA CI/publication gates.
See [ADR 0010](../adr/0010-hkm-inspired-versioned-cell.md),
[acceptance criteria](../../SUCCESS_CRITERIA.md) and
[progress](../../GOAL_PROGRESS.md).

## Source provenance for this revision

The public source registry is [publication/references.json](../../publication/references.json).
Each entry identifies its own review date and evidence class. Relevant primary sources:

- S08 / S23: Cognibotics product and hybrid-mechanism descriptions; manufacturer claims inspire general form and reference metadata only.
- S24: Cognibotics/Smartshift tool-changing capability; the six simulator tools are our design.
- S25 / S07: Nowaste's 2024 Tostarp pilot report and Cognibotics' January 2026 second-cell **order**, not proof of completed second installation.
- S03: SICS/coordinator HYPER reporting hosted by CORDIS; structured-world/interface claims are company-reported, not EC performance validation.
- S04 / S26 / S05: academic bibliography and original AutoGrasper repository; the thesis full text remains unreviewed and its algorithm is not reproduced.
- S27 / S12: Blender Python API and MCP authoring documentation; no unrestricted MCP runtime control.
- S28 / S29 / S30: primary PyBullet and Isaac Sim documentation as physics, planning and sensor scope comparisons; neither library is a mandatory dependency.

No manufacturer CAD, image, proprietary implementation or inferred customer layout
has been imported as an implementation asset. Original geometry, catalogue rules,
visual timings and collision checks remain SIMULATOR_DESIGN.
