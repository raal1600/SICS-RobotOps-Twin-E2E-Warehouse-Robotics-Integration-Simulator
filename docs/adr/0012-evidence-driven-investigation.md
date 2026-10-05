# ADR 0012: Run, notice and investigate without losing context

Status: implemented; source-specific acceptance pending.

The accepted dashboard exposed genuine evidence, but stacked status cards, long
selector explanations and an unbounded timeline made the cell and investigation
tools hard to find. This presentation revision starts from clean `0db6168` and
archives the previous acceptance report. It preserves the API, schemas, world,
command journal, verifier and explicit reconciliation semantics.

Keep the scenario purpose, one thing to watch, run action and cell central.
Highlight uncertain or failed results beside the cell and in the persistent guide.
Do not automatically cover the animation with a modal or move focus on polling.
The operator opens **Investigate this pick** or the guide's named review action.
This supersedes ADR 0009's automatic review opening, not its evidence boundary.

Use a bounded native dialog with three views: **What happened**, **Evidence** and
**Manual inspection**. Separate the recorded symptom, confirmed record contents,
limits and explicitly unproven possible explanations. Only `JobEvidence` and the
relevant persisted order/job events supply these statements. Resolve the assessed
observation by the latest verification's observation ID; never substitute a later
planning capture, current scenario selection, animation or private world truth.
The original command's successful journal alone does not establish completion.

Pin the inspection to its test and job independently of the main replay selection.
The guide may inspect the blocking job while an earlier product remains selected
for replay. Opening inspection pauses only the player, preserving its frame;
**Back to simulation** keeps that view and Play resumes explicitly. Polling
updates this same evidence without changing tabs or stealing focus. Test changes
invalidate late responses and close the old inspector. Explicit reconciliation
still targets the unresolved original command and may update its outcome.

Keep exact command/journal, assessed observation, verification/review records,
tool reasoning and full JSON. Put the event timeline in a collapsed section with
a bounded scroll region, filtering and a full-record drill-down. Manual inspection
offers test-scoped read-only API requests, a JSON evidence/event download, recorded
fault reproduction guidance and real source, database, artifact and log paths.
The download is presentation format `robotops-investigation-1`, not a new robot
wire contract. It includes the full order timeline, explicitly labelled as such.

Separate actual app request failures from intentionally injected simulation
faults. Keep busy state, terminal workflow state and paused replay distinct.
Guard a newly submitted job's selection while slow planning has not yet registered
its delivery entry. Request the optional Blender checkpoint only after a successful
durable journal and resolved/uncertain post-execution workflow state exist.

Mandatory Playwright journeys exercise real HTTP and persistence with both the
synthetic and Blender runtimes at 1440×1000 and 390×844. They inspect/download
evidence, prove navigation makes no writes, reconcile contradictory then normal
evidence with one original effect, and review saved tests. A controlled service
failure proves the app-error distinction. Node tests cover attribution, context,
selection races, focus, replay pause and existing lifecycle combinations.

Browser test success proves tested functionality, not first-time usability.
Visual review and remaining comprehension uncertainty must be recorded separately.
Eight additive UI-INV MUSTs join all 110 prior criteria; thresholds and prior
evidence attribution remain unchanged. Publication is generated from source.
