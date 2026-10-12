# Measured calibration contracts

The canonical executable schemas are the Pydantic records in
`robotops/calibration/contracts.py`, with specialized records in `optics.py`,
`tcp.py`, `runtime_contracts.py`, `registration.py`, `checks.py` and `trace.py`.
Records are frozen, reject extra fields and non-finite scalar values, and carry
`schema_version: calibration-1.0`. Legacy v1/v2 world serialization does not gain
measured fields; the separate gantry world uses application schema 3.0.

Published JSON schemas live under `contracts/schemas/calibration/`; the application
OpenAPI and v1/v2/v3 schemas remain under `contracts/`. Regenerate with
`uv run --locked python -m tools.export_contracts`. Contract tests compare both
validation and serialization schemas, including nested measured plan/observation
records. Legacy-shape wrap serializers preserve strict schemas and original hashes.
Observer-2 v3 object confidence and point uncertainty are explicitly null; actual
rule gates live in `MeasurementQuality`. Legacy v1/v2 observations still require
numeric fields and retain their original bytes. Historical measured observer-1
records remain readable without relabeling their fixed fields as statistical estimates.

| Contract | Meaning and relevant checks |
|---|---|
| `Transform` | `T_A_B` maps B into A; rigid homogeneous 4x4 matrix, right-handed orthonormal rotation, translations in meters |
| `Stream`, `Camera` | RGB/depth sizes, K, model-correct coefficients, crop/resize, profile/revision, depth units/semantics and `T_c_d`; fingerprint changes when configuration changes |
| `Board` | ChArUco dictionary, ordered corner IDs/metric points, measured dimensions and mounting identity; inconsistent order or units rejected |
| `Tool` | Tool identity/revision and `T_f_tcp`; verification is separate evidence |
| `Capture` | RGB PNG and native float32 NPY references, shape/hash, three timestamps, settling/motion status, `T_b_f`, configuration/board fingerprints, admission and rejection reasons |
| `PoseSample` | Actual detected image/metric correspondences, excluded IDs, candidate pixel RMS, selected `T_c_t`, local sensitivity and measurement partition |
| `CapturePresentation`, `EvidenceGeometry` | Read-only saved controller/physical presentation or Python-generated plan/residual/target geometry; frame b and meters, numerical alternatives, explicit instructor/estimate scope; never estimator or command authority |
| `Candidate` | Inactive X/Y, accepted/excluded measurements, coverage, training-only robust policy/residuals, immutable configuration/limits/source identity |
| `ValidationReport` | Separate PnP/chain image metrics, chain mm/degrees, independent references and error vectors, count/coverage/statistics and explicit failed limits |
| `CalibrationArtifact` | Approved candidate/report, actor/time/simulation scope and verified optical report identity; record identity does not imply current applicability |
| `Point3` / structured error | Robot-base meters or a specific failure; invalid depth never becomes a zero/fallback target |
| `GraspSpecification`, runtime target | Point, configured orientation/contact/approach/tool sources and TCP/flange command mode remain distinguishable |
| `ComputationTrace`, HTTP trace | Actual call/request inputs, results, timestamps, correlation and saved source; in-process calls are not relabelled network transport |

## Frames and equations

`b` is robot base; `f` flange; `t` board; `c` RGB optical; `d` depth optical;
`tcp` tool reference. Camera axes are x right, y down, z forward. Robot base is
z-up. Quaternions use xyzw where a quaternion interface is required. Presentation
conversion is implemented in `visualization.py`; scientific coordinates stay in
Python, meters and radians.

`A_i = T_b_f(i)`, `B_i = T_c_t(i)`, `X = T_b_c`, `Y = T_f_t`.
The constraint is `A_i Y = X B_i`. Known mounting yields
`X_i = A_i Y inv(B_i)` followed by rigid fitting. The unknown-mount Park mapping
uses A and inv(B) and returns Y; independent golden tests check this direction.

Native depth first creates `q = [x_n, y_n, 1]` from the correct depth model.
Axial depth yields `p_d = Z q`; radial range yields `p_d = r q / ||q||`.
Then `p_c = T_c_d p_d`, correspondence is checked in RGB, and `p_b = X p_c`.
The documented aligned path retains native-value semantics and an explicit native
index map. Missing, occluded, mixed or ambiguous correspondence is an error.

For a flange-command interface,
`T_b_f_target = T_b_tcp_target inv(T_f_tcp)`. A TCP-command interface uses its
configured tool without a second offset. Both paths are tested separately.

## Persistence and mutations

Scientific records are immutable JSON with SHA-256 identities. Large arrays are
referenced by confined artifact paths and content hashes. The SQLite lifecycle
uses camera-scoped request IDs and expected revisions. Actual simulated controller
commands, captures, tool measurements and motion reports have separate journals.
Retries reuse those identities rather than producing new physical effects.

Routes follow `/simulation-tests/{test}/calibration/...`, using the existing
test/session permission boundary. GET, source, image preview, pixel inspection,
history and export are read-only. Mutations require a current writable test and
revision. See `apps/api/calibration.py` for actual request contracts, and
[ARCHITECTURE.md](ARCHITECTURE.md) for editable state/sequence diagrams.

`GET .../calibration/geometry` validates camera/record bindings and supports saved
capture scenes, saved capture plans, samples, validation/routine references and
recorded targets. Capture scenes live in the controller's separate
`calibration_capture_scenes` table. They retain the reported flange with explicitly
labelled synthetic physical layout. Report noise can differ slightly from the true
pose that rendered pixels. Historical captures lacking scenes report unavailable;
they are not silently rebuilt from today's moved camera.

`POST .../calibration/cameras/{camera_id}/reuse-estimate` takes an approved artifact
ID, a new candidate ID, request ID and expected revision. The transaction copies
unchanged X/Y and original fit provenance from the immutable artifact. Optional
`Candidate.reused_from` records parent artifact/candidate hashes and creation time;
its absence is omitted from serialization to preserve historical fingerprints.
The operation copies neither validation authority nor approval. Configuration must
match; unused final measurements and new explicit approval establish applicability.
The keyed board is installed and the independent tool check is cleared. A remount
with a different board identity cannot reuse old Y. Export reproduction checks
lineage and recalculates the original image fit as well as the new validation.

New `PoseSample.excluded_image_points_px` retains the observed image coordinates
paired with `excluded_corner_ids`. The excluded points do not enter PnP/fitting.
Older records omit the optional field and retain their fingerprints; the viewer
does not invent missing historical coordinates. Reproduction checks accepted and
recorded excluded corner measurements against actual raw-image detection.

`ReferenceBatch` contains a camera/dataset/partition identity and typed captures
paired with independently specified synthetic survey coordinates. The controller
journals the complete batch atomically; retries retain bytes and timestamps, even
after restart. Reusing the identity with different declared configuration or
partition rejects. A new observation requires a new dataset. Physical geometry
is frozen while the synthetic survey images are rendered; this is not a claim of
sequential hardware fixture motion or clock synchronization.

`SurfaceDetection` records the actual RGB-only detector, selected pixel, mask count
and a hashed boolean NPY mask. Reference and operational correspondence consume
that saved mask. Acquisition, identification and depth reconstruction have separate
actual Python-call traces. A batch trace may link several capture records, explicitly
as one batch call. Source inspection does not fabricate an individual call per image.
Exports include masks; offline reproduction detects them again from RGB and compares
both coordinates and mask bytes before checking reference/runtime calculations.

`GET .../calibration/captures/{id}/depth-display` supplies the displayed raw-unit
1st/99th percentile range and nonfinite/nonpositive counts. This read-only display
scale is shared by capture and pixel previews. Clipping is visual only and is not
depth validation, distance calibration, filling or a target-generation decision.

New `measured-rgbd-observer-2` observations retain application schema 3.0 and add
`CalibratedObject.measurement_quality`. This source-linked record reports actual
RGB/depth correspondence, cross-camera agreement and the approved holdout's maximum
error against their separate limits. It is not a probability or uncertainty model.
New measured objects therefore explicitly emit `confidence: null` and
`uncertainty_m: null`; unestimated uncertainty adds no verification tolerance.
Legacy v1/v2 still require finite numeric values and keep their original wire
serialization. Historical measured observer-1 objects remain readable with original
fields, but the current client does not call their fixed score statistical confidence.
Fresh operational observations require the current bound measurement-quality record.
Canonical generated schemas/OpenAPI were refreshed and pass the bounded contract
campaign; the final complete regression checks them again.

Unresolved planar pose rejection can carry an optional saved `Calculation`.
It contains the actually measured corner IDs/pixels, normalized points, metric
board points, A_i, camera model, ambiguity threshold and distinct positive-depth
T_c_t candidates with residuals and score gap. The decision explicitly selects no
pose. The rejected Python trace retains this calculation separately from its null
success output. Older rejection/trace records omit the new optional field and keep
their original serialized fingerprints. Image reproduction compares the recorded
rejection calculation, not merely its error code.

New measured-cell creation accepts optional `StartTestRequest.command_mode` (`tcp`
or `flange`). The configured mode is immutable for that world and recorded in its
execution settings and reported `CalibrationMachine`. Omitted historical settings
keep their original bytes and flange default. Reusing a creation request with a
different mode fails; legacy profiles reject the option. TCP commands use the
configured tool once in the controller; flange commands receive Python's converted
flange target. Dispatch still rejects a mode/target/tool mismatch.

After an unconfirmed browser request, `GET .../calibration/operations/{camera}/{id}`
checks its saved receipt. A 404 means no completed receipt was found, not proof that
work never started. The client may explicitly resend the unchanged original body
and identity; service/controller journals reuse saved measurements and revision
guards remain authoritative. A transport failure during the receipt check does not
enable retry, and historical views cannot resend a mutation.

Cross-camera agreement checks each measured point's camera, transform and camera
configuration fingerprints against its own artifact. A shared board-mount comparison
is made only when the complete board/mount configuration agrees. Conflicting points
are retained separately and rejected, never averaged into an operational target.
