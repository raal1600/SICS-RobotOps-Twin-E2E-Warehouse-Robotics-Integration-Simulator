# Measured calibration implementation

This scoped work implements the user's 2026-10-08 robot-cell calibration goal.
It does not replace or relabel historical HKM, lab or client acceptance reports.

## Starting evidence and boundaries

- Clean starting branch: `feat/client-rebuild`, commit `cacc5fb39ddd36ea10303b167fd209e149e14bf5`.
- Fetched origin before branching; main remains `26d7aac9774d4f014e70da872dd4045d94428748`.
- Working branch: `feat/measured-calibration`. At implementation start, remote push
  and deployment were not authorized. On 2026-10-13 the user authorized committing
  and pushing the current branch for GitHub review; public deployment remains out of scope.
- Exact requested `SICS_AI_Kalibrering_Rami_Halabi_v2(1).pdf` was not found locally.
  Read and visually inspected all four pages of Downloads/
  `SICS_AI_Kalibrering_Rami_Halabi_v2.pdf`, SHA-256
  `8b1b371d58824e2bc680ad1d8c0d16406502c5b3ecfee28e7118332c543c0f7f`.
  It has the four specified sections. The user's complete restated requirements govern.
- Confirmed: `ObservationModel.observe` copies WorldState object poses; observation
  quality compares calibration strings; `validate_workspace` rejects tilted tools.
- Preserve the old observer, HKM guard, saved artifacts, explicit physical consent,
  original-command reconciliation, transport labels, lab behavior and read-only replay.
- Add an explicitly identified calibration-capable synthetic profile; no claim of
  HKM joint kinematics. Its measured/controller poses, motion bounds and rendering
  must agree; never simply remove the existing upright guard.
- All scientific/operational coordinates and acceptance decisions belong in Python.
  Browser geometry is supplied by the backend; orbit/display math is presentation only.
- No RL or network-weight learning, real hardware, paid services or cloud dependency.

## Ordered vertical slices

1. **Measured core**: strict frame/camera/board/capture contracts; isolated oracle and
   Python image/depth renderer; real ChArUco/IPPE/LM; known-Y rigid fit, unknown-Y
   Park-Martin with independent mapping tests; frozen limits and holdouts.
2. **One integrated pick**: inactive candidates, independent validation, explicit
   approval and applicability; native depth correspondence; independent TCP checks;
   shared service/CLI/API; measured observation into real guided order execution,
   physical contact checks, fresh post-observation and business reconciliation.
3. **Multiple sensors and recovery**: own models/X, overlap rejection; routine checks,
   fault scenarios, evidence-limited diagnosis, candidate/active separation, restart,
   stale prepared-command rejection, valid rollback and no duplicate effect.
4. **Client/3D/inspection**: preserve Run & watch / Inspect evidence, progressive
   calibration sequence, supplied rays/frames/errors, actual images and overlays,
   source-linked calculations/transport records, accessible alternatives and Swedish
   presenter explanations. Read-only replay and selection/async-response guards.
5. **Acceptance campaign**: two fresh seeded worlds, all SC01-SC20 and PDF rows,
   Python/Node/browser/Blender/applicable lab lanes, source-bound exports/replay,
   keyboard/axe/responsive review, source/worktree identity and honest limitations.

## Non-negotiable details retained across slices

- T_A_B maps B to A, m/rad, optical x-right/y-down/z-forward, validated SE(3)/xyzw.
  A_i=T_b_f, B_i=T_c_t, X=T_b_c, Y=T_f_t; A_iY=XB_i. Explicit base-to-view axes.
- Captures include raw RGB/depth refs and hashes, all timestamps/settling, IDs,
  profile/config fingerprints, robot measurement and provenance; rejected captures
  persist. Camera profiles include models/K/D/crop/size/depth semantics/T_c_d.
- Actual synthetic RGB -> identified ChArUco corners -> positive-depth IPPE candidates
  -> LM on model-correct undistorted normalized points (K=I,D=0), ambiguity/outlier
  decisions, pose diversity/coverage/conditioning, rigid fits and inactive candidate.
- Simulator truth stays in sensor/physical simulation and independent test oracle;
  estimator and operational target generation receive only their allowed inputs.
- Native depth deprojection, registration, conservative visibility; documented aligned
  path only. Reject missing/zero/nonfinite/range/occlusion/mixed/ambiguous measurements.
  No identical-index shortcut, no RGB-Z assumption, no zero/fallback target.
- Point vs grasp orientation/contact/approach; independent tool checks; configured
  TCP command versus flange conversion without double offset; preserve interlocks.
- Independent PnP/chain point-count RMS, per-view/spatial residuals; chain mm/deg;
  independent measured references, vectors, coverage/count, median/max/p95 with
  declared support/method. Freeze candidate and simulation-only limits before holdout;
  final validation data cannot tune/select, and new candidates need unused holdouts.
- Immutable versioned artifacts carry configs, X/Y, sample exclusions, provenance,
  source/software/dataset hashes, validation and actor/time/scope. No invented approval.
- Active validity is separate from candidate lifecycle. Suspect blocks affected targets
  even with old versions; rejected candidate never substitutes. Recheck bindings at
  dispatch and execution. Calibration change never causes a second uncertain pick.
- All requested faults remain in scope: camera pose, K/profile/crop/units/depth/range/
  registration/invalid depth, timing/settling, corners/IDs/dimensions/diversity/ambiguity,
  TCP/remount/noise/missed pick and missing limits/approval/stale/invalid rollback.
- Diagnostics are clues, never forced diagnoses; include distinguishable scale/rigid
  cases and genuinely insufficient evidence. No fixing tool/depth faults by changing X.
- Idempotency, concurrent revisions, scoped read-only GET/export, allowlisted source,
  historical honesty and saved-vs-current source hashes are required backend behavior.
- Every material calculation exposes actual operands/results/formula/function and
  record/correlation identities. Shared-module CLI capture/fit/validate/approve/demo/
  reproduce/export, architecture diagrams, presenter path and limitations are deliverables.

## Status

**ACHIEVED for the scoped local synthetic simulator.** All SC01-SC20 criteria pass
current source-bound verification; see ACCEPTANCE_REPORT.md and TRACEABILITY.md.
The full unfiltered campaign passed 1080 tests with no skips and 91.18% coverage;
199 Node tests, lint, strict typing, security and the isolated publication build pass.
Two fresh locked-environment CLI worlds (seed37/flange, seed97/TCP) completed verified
picks and reproduced their exported evidence with matching source and raw hashes.
The independent UI reviewer scored all five fixes resolved; the documenter preserved
the incumbent design system. No remote commit/push, deployment or hardware operation
is claimed by that October 9 acceptance report. The subsequent GitHub review handoff
is recorded separately in VERIFICATION.md. Manual/hardware limits remain in LIMITATIONS.md.

Historical iterations, failures and fixes are retained in VERIFICATION.md and
`artifacts/calibration/plan-status-before-final-01.md`. Do not relabel them as fresh
passes. Final source identity and artifacts are recorded in the acceptance report.
