# ADR 0009: Guide the operator from persisted results

Accepted locally 2026-10-03. Classification: SIMULATOR_DESIGN.

Presentation follow-up: [ADR 0012](0012-evidence-driven-investigation.md)
supersedes automatic review opening and the stacked page layout. Attention now
highlights an explicit investigation action; the bounded inspector preserves
replay context. The evidence, uncertainty and explicit-action rules below remain.

Operators should not have to memorize different recovery sequences for each
execution/observation combination. The dashboard now has a dark theme, a
Prepare / Run / Review / Continue indicator and a persistent next-step card.
Scenario descriptions explain expected behavior before execution; they never
serve as evidence of what actually happened.

The follow-up adds a definition, affected stage and key difference for each
scenario and observation mode, with expandable comparison tables. Execution
selection applies to a new order; observation selection applies to a subsequent
review capture. The same degradation can appear in both, at different points in
the workflow. Descriptions and tables share one local catalog and are read-only;
they neither inject faults by themselves nor determine an actual outcome.

The presentation-only guide reads persisted job states, the original command
journal and verification records. It prioritizes the active uncertain pick over
a selected historical replay or a stopped cell. When a job first needs attention,
the UI opens and focuses Review evidence once. Polling and repeated inconclusive
assessments do not steal focus. Review identifies the product and job, explains
the journal, the exact assessed observation and the latest verifier decision, and
keeps all earlier assessments available in the timeline and schema evidence.
A planning observation is never relabelled as a post-pick assessment.

The observation selector, its expected degradation and the original-command
reconciliation action are together in the review panel. Use normal observation
only changes that selector; a separate explicit action captures evidence. It
does not promise success. Viewing the panel/evidence and next-step navigation
are read-only. A bad assessment permits another observation in the same test
(ADR 0008); a sufficient assessment permits the next explicit order. No guide
action creates an automatic retry, overrides the verifier, or uses replay/world
truth to decide a business outcome. Domain transitions and thresholds are unchanged.

Resolved outcomes point to configuration for the next pick. Stopped cells offer
an explicit logical reset. Depleted deliveries offer an independent new test;
the guarded restock action remains available for another delivery in the same
test. Test history stays read-only and the guide offers Return to current test.
The existing lifecycle, quarantine and journal guards remain authoritative.

The default dark interface uses visible keyboard focus, native labelled controls,
text as well as color for outcomes, and a narrow-screen layout. Technical replay
selection and diagnostics are expandable; the full-delivery 3D view remains the
default. Styles and guide code are served through bounded local static routes,
with no new package, external asset or model dependency.

Validation combines pure guide cases, dashboard action/navigation tests, existing
execution/observation combinations, HTTP asset/contract checks and isolated real
Blender browser flows. Local evidence is in docs/evidence/guided-workflow-local.json.
