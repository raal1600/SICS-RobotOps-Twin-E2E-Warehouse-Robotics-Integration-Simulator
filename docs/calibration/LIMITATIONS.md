# Calibration simulation and commissioning boundaries

This is an executable local simulator, not evidence of completed experiments in
Rami Halabi's real cell. The available four-page brief and its exact hash are
identified in [PLAN.md](PLAN.md). No proprietary SICS.AI behavior is asserted.
Current acceptance status is in [TRACEABILITY.md](TRACEABILITY.md); an implemented
slice is not complete acceptance of the goal.

## What measurements mean here

Python renders synthetic RGB images and native depth arrays from private physical
geometry. OpenCV actually detects ChArUco corners from those RGB pixels. The
estimator receives images, declared models and noisy reported flange measurements;
it does not receive the hidden camera or unknown board mounting transform.
Reproducibility means seeded computation, not a recorded successful answer.

The synthetic factory optical fixture is separate camera-local metrology. It
verifies projection for the declared RGB/depth profile, but is not a working-cell
image acquisition, SDK certificate, depth-scale check or estimate of installation
geometry. Factory optics verification cannot determine camera-to-base X.

Robot kinematics are inputs. The calibration-capable profile is an ideal orientable
gantry/gimbal. It is not HKM1800 inverse kinematics, motor dynamics, stiffness or
metrology. The old HKM profile retains its upright-tool constraint. Flange noise,
depth error and contact offsets remain possible; a low fitting residual alone
does not establish reference accuracy.

Independent validation uses separately defined survey targets distributed through
the working volume, plus unused board captures. Limits are frozen,
`SIMULATION_ONLY`, and tied to the chosen synthetic grasp/error budget. They are
not SICS requirements, production tolerances or a safety certificate. Local
image-Jacobian sensitivity is not a complete physical uncertainty model.

## Perception, tools and execution

The operational detector identifies a configured red top surface of a known cube.
It is a deliberately simplified perception assumption, not universal recognition.
Orientation, contact offset, approach and tool geometry have explicit sources
separate from the reconstructed point. A valid point does not by itself define a
valid grasp.

Tool verification uses synthetic pivot contacts and indexed orientation probes.
The raw independent fixture measurements are saved; this is not a claim that the
robot executed a complete hardware tool-calibration motion. Tool changes cannot
be corrected by changing X. A failed or stale tool check blocks execution.

Application interlocks, reach bounds, conservative collisions and synthetic
contact checks are operational simulator behavior, not certified industrial safety
functions. Orders still require their original explicit execution authorization.
A calibration approval does not authorize a pick. An uncertain outcome is
reconciled against the original immutable command, not retried as another pick.

The missed-pick experiment models failure to retain a contacted object. The same
approval, reach, collision and contact gates apply; the controller then records
its full motion without attachment or transfer. It is not a material/friction or
gripper-dynamics model. Fresh images establish no completed transfer, while the
operational investigation cannot infer which physical cause produced that symptom.
The instructor's fault selection is not used as diagnostic evidence.

## Presentation and evidence

The measured Blender lane displays committed Python-controller reports. Its
evaluated geometry is numerically checked against those reports; rendering is not
a second physical controller and cannot change an outcome. Browser/Blender
viewpoints, history, pixel inspection and replay never approve or execute work.
Physical camera placement is distinct from estimated X. Test-oracle comparisons
must remain labelled.

Exports retain raw hashes, observations, source snapshots, computed results,
approvals and actual command/controller records. Reproduction recomputes supported
scientific stages and audits saved command/motion records; it does not physically
re-execute a historical pick. Archived Python is compared, not automatically run.
Application and controller snapshots are separately consistent; export a settled
run for complete evidence. They are not a cross-database atomic snapshot during
ongoing work.

New calculation traces compare the saved function and its nested Python code with
the loaded callable before execution. A mismatch stops the calculation and records
an error. Raw file bytes and normalized display text have distinct hashes. This is
not proof that every global object or native dependency matches that file. Historical
traces retain their narrower file-at-call scope. Fresh browser campaigns compare a
broader source manifest before and after the run. Final whole-campaign provenance
and all traceability rows passed the review recorded in ACCEPTANCE_REPORT.md.

## Real-cell commissioning still required

Real hardware requires vendor-specific pose/clock/SDK adapters; independently
measured dimensions and mounting stability; applicable camera/depth models;
physical survey references with known uncertainty; tool and mechanical metrology;
cell-specific tolerance and safety review; realistic materials/lighting/occlusion;
and supervised commissioning. No real device is connected by this local workflow.

The current browser and automated accessibility checks are agent-based engineering
verification. Human usability research and real screen-reader testing have not
been performed. Automated axe results do not prove full WCAG conformance.
