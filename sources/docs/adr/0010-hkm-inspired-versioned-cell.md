# ADR 0010: Version the HKM-inspired cell without changing effect semantics

Accepted design 2026-10-04. Implementation and acceptance pending.
Classification: SIMULATOR_DESIGN.

The user requests a professional HKM1800-inspired hybrid-kinematic manipulator,
six product families and six interchangeable tools in the existing deterministic
warehouse integration simulator. The previous Cartesian scene and positional
recordings do not represent articulated links or tool preparation. Existing
orders, controller journals and saved evidence must remain interpretable.

The adaptation extends the bounded programmatic runtime rather than replacing
it with an opaque hand-authored scene. Original procedural geometry and a shared
semantic primitive representation drive Blender and browser presentation.
`HKM_INSPIRED_VISUAL_KINEMATICS_V1` maps a requested TCP pose to connected visual
links. It is an original illustrative mechanism, not inferred HKM joint equations.
No exact CAD, copied controller or proprietary software is imported.

A canonical typed catalogue supplies six products, six tools, compatibility and
synthetic mass/geometry constraints. Deterministic selection persists candidates,
scores and rejection reasons. Versioned world state includes mounted tool and
rack occupancy. Tool changing is journaled cell preparation under the same
`PICK_AND_PLACE` command. `effect_count` still counts product transfers only;
changing a tool is not another pick. An unavailable tool blocks product motion.

Plans and commands gain typed tool/grasp/trajectory data. Workspace bounds and
conservative sampled geometry preflight use simulator-owned configuration and
finite deterministic alternate routes. Blender independently checks critical
preconditions before effect. Animation interpolation and durations are explicitly
presentation timing, with no real robot cycle-time or safety guarantee.

Schema/profile/model versions must identify new semantics. Historical payloads,
journal hashes, scene snapshots and motion evidence cannot be silently rewritten
or interpreted using the new scene. Readers must retain explicit legacy support
or show an accurate unsupported-historical-format message. New fixtures use the
new profile; existing user tests are never destructively reset or migrated.
Concrete wire versions are recorded in contract documentation when implemented;
this design record does not claim a new schema has already shipped.

The unchanged trust boundary is `WorldState -> ObservationModel ->
WorldObservation -> Verifier`. Sensor metadata and explicitly labelled simulated
cell telemetry do not become claims of image processing. Favorable hidden world
truth cannot resolve an insufficient observation. Tool change and richer visuals
cannot weaken UNKNOWN_OUTCOME, journal-plus-fresh-observation reconciliation,
exactly-one transfer, claim fencing or restart conservatism. Replay remains read-only.

The enhancement is a new acceptance revision: the original 85 MUST requirements
remain and 25 HKM requirements are added. Clean baseline evidence is archived
without relabelling the earlier release as enhancement acceptance. See the
[implementation design](../implementation/hkm-inspired.md) and
[baseline provenance](../evidence/hkm-baseline-eaf35b4/provenance.json).
