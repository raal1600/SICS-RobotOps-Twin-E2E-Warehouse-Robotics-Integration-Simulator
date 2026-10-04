# HANDOFF.md — Codex /goal Handoff

**Purpose:** This is the operating contract for an autonomous coding agent implementing RobotOps Twin.

## Exact recommended /goal prompt

```text
/goal Implement RobotOps Twin to completion according to PROJECT_PLAN.md and SUCCESS_CRITERIA.md.

Read HANDOFF.md first and obey its operating protocol. Then read PROJECT_PLAN.md, SUCCESS_CRITERIA.md, CODEX_GOAL_CHECKLIST.md, README.md, the research reports/source registry, PUBLICATION.md, existing contracts/tests/code, and GOAL_PROGRESS.md if present.

Work iteratively until every MUST criterion in SUCCESS_CRITERIA.md has inspectable PASS evidence. Do not weaken requirements, tests, thresholds, state semantics, or evidence rules to make the goal pass. Keep deterministic CI independent of external LLM APIs.

Treat the repository documentation, reports, diagrams, source registry, README and GitHub Pages as one governed knowledge base. Whenever implementation or evidence makes any documentation stale, update every affected source document/diagram in the same coherent change and rebuild generated publication through the repository workflow.

Preserve the public boundary: this is an independent simulator inspired by public sources. Never claim to reproduce SICS AI proprietary architecture, AGI, safety certification, or validated physical robot performance.

Maintain GOAL_PROGRESS.md while working. Make coherent milestone commits. Before declaring DONE, run the complete acceptance process, generate ACCEPTANCE_REPORT.md mapping every MUST criterion to evidence, synchronize the knowledge base, rebuild/verify GitHub Pages, and confirm every MUST is PASS. If any MUST remains unsatisfied, report NOT DONE and continue unless a defined human-escalation condition blocks progress.
```

## Mandatory read order

1. `HANDOFF.md`
2. `PROJECT_PLAN.md`
3. `SUCCESS_CRITERIA.md`
4. `CODEX_GOAL_CHECKLIST.md`
5. `README.md`
6. `reports/**`, source registry and diagrams relevant to the implementation
7. `PUBLICATION.md`
8. existing `contracts/**`, tests and implementation
9. `GOAL_PROGRESS.md` and `ACCEPTANCE_REPORT.md` if present
10. ADRs

Do not begin architecture-changing implementation before understanding the normative state/reconciliation rules.

## Execution loop

### Active revision: HKM-inspired warehouse cell

Fresh API/desktop worlds and Start new test use the six-SKU HKM profile. Existing
worlds retain their persisted execution settings and historical evidence; do not
pass a new default profile over a reopened runtime's resolved settings. Use
`/fixtures.product_sources` and `destination_id` instead of assuming one source
or that the second location is the destination. New-intake fixture validation
must preserve existing idempotency replay/conflict semantics.

The 2026-10-04 enhancement in PROJECT_PLAN.md and ADR 0010 is mandatory scope,
in addition to the original deterministic-system requirements. Work through
HKM-P0/P1/P2/P3, preserving all 85 existing MUSTs and satisfying the 25
HKM-VIS-MUST criteria. Record the actual HEAD and fresh baseline before editing;
archive prior reports/results with provenance instead of rewriting historical
acceptance. Current evidence never attests a later commit by implication.

Use original procedural HKM-inspired geometry, not exact/proprietary CAD or
inferred real controller mechanics. Unspecified real-world details become
explicit conservative SIMULATOR_DESIGN choices; they do not require ordinary
implementation clarification. Maintain the bounded typed Blender runtime and
the WorldState -> ObservationModel -> WorldObservation -> Verifier boundary.
No MCP/natural-language/generated code is permitted in runtime commands.

The procedural cell, six-product/tool catalogue, deterministic selection,
segmented preflight, visible tool preparation and quaternion replay are now
implemented and accepted at the audited source identified in ACCEPTANCE_REPORT.md.
Continue from that implementation and preserve the archived evidence in
GOAL_PROGRESS.md; do not restart this work as scaffolding. Later material changes
require fresh scoped evidence and the applicable acceptance gates.

Use the one canonical catalogue in `robotops/robotics/catalogue-v1.json` for
products, tools, fixture layout and camera calibration. Shared geometry supplies
both displayed static objects and collision bounds. Preserve the narrow registered
vertical dock-contact policy; parked tools remain obstacles elsewhere. Synthetic
source-contact centering uses the shared standard-library tolerance, distinct
from verifier pose tolerance and real robot accuracy.

Tool changes are persisted preparation under the original pick identity;
effect_count remains product transfers. An uncertain pick cannot be replaced
because of richer visuals/tool state. Version changed world/command/motion
contracts explicitly and retain old scene, payload/hash and recording meanings.
Schema-1 serializers omit schema-2 extensions, including defaults, so archived
command digests remain unchanged. New schema-2 records retain strict typed
fields; never replace that serializer with an unrestricted dictionary schema.
Never destructively reset saved user tests to make new fixtures work. A truly
destructive migration remains a human-escalation condition below.

Each milestone synchronizes affected catalogue-generated docs, contracts,
architecture/frame/state/tool diagrams, report provenance and public status.
Until old and new MUSTs and exact-final-SHA remote gates pass, public status is
NOT DONE. Planned tests or impressive renders are not acceptance evidence.

### Repeated milestone loop

Repeat:

1. **Inspect** repository state, failing tests, current progress and documentation drift.
2. **Select** the smallest coherent milestone that advances one or more unmet MUST criteria.
3. **Plan locally**: identify contracts, code, tests and knowledge-base files affected.
4. **Implement** production code and tests together.
5. **Verify** targeted tests, then broader affected suites.
6. **Synchronize knowledge base** using the protocol below.
7. **Run quality gates** appropriate to the milestone.
8. **Update GOAL_PROGRESS.md** with criteria advanced, evidence, remaining failures, decisions and drift synchronization.
9. **Commit coherently** with implementation + tests + affected docs/diagrams.
10. **Re-evaluate every MUST** and choose the next unmet criterion.

Near completion, run the full clean acceptance path, not only targeted tests.

## Stopping condition

You may declare **DONE** only when every MUST in SUCCESS_CRITERIA.md has inspectable PASS evidence, final mandatory CI/publication checks are green, ACCEPTANCE_REPORT.md is current, and no known material documentation drift remains.

SHOULD failures must be documented. OPTIONAL items never block DONE.

## Human escalation conditions

Stop and request a human decision only when one of these prevents safe progress:

- two normative requirements are materially contradictory and cannot be reconciled without changing intended behavior;
- a requested action needs unavailable credentials/permissions or real external hardware;
- a primary-source correction would materially change the project's public interpretation and cannot be responsibly resolved from evidence;
- a security/safety concern makes the requested implementation inappropriate;
- a destructive migration would discard user-created data not clearly defined as disposable fixture data;
- the only way to satisfy a MUST would be to falsify evidence or weaken the criterion;
- a major architecture deviation is necessary and has product implications beyond a normal ADR.

Do not escalate ordinary implementation choices that can be resolved conservatively within PROJECT_PLAN.md.

## Anti-shortcut rules

Never:

- edit SUCCESS_CRITERIA.md merely to make a failure disappear;
- lower a threshold without a justified, documented decision and corresponding human escalation if it changes acceptance intent;
- delete, skip, xfail or loosen a mandatory failing test to claim success;
- change expected output to match an implementation bug;
- use simulator ground truth as normal verifier input;
- treat timeout as proof of no physical effect;
- blindly retry a side-effecting robot command under a new identity after uncertain outcome;
- make mandatory CI depend on an LLM/API/GPU;
- represent a logical E-stop as safety-rated;
- claim Blender validates robot dynamics;
- claim SICS proprietary architecture/AGI has been reproduced;
- manually edit generated Pages/PDF output;
- mark a criterion PASS without inspectable evidence.

## Knowledge Base Synchronization Protocol

The repository is one governed knowledge base.

### Normative
`PROJECT_PLAN.md`, `SUCCESS_CRITERIA.md`, `HANDOFF.md`, committed contracts and acceptance-defining tests.

### Operational
`CODEX_GOAL_CHECKLIST.md`, `GOAL_PROGRESS.md`, `ACCEPTANCE_REPORT.md`, ADRs and implementation docs.

### Explanatory/public
`README.md`, `reports/**`, `publication/**`, source registry, diagrams, `PUBLICATION.md`, GitHub Pages and generated PDFs.

### Sync trigger
Run synchronization whenever implementation evidence, new primary-source research, an ADR, API/schema/state-machine change, corrected assumption, renamed component, changed command, changed metric/test count, or project-status change invalidates existing text.

### Required action
1. Identify every affected artifact.
2. Update normative source if the intended contract legitimately changed; never weaken acceptance to fit code.
3. Update explanatory/public source files to match repository reality.
4. Preserve claim provenance: VERIFIED_PUBLIC_FACT, COMPANY_REPORTED_CLAIM, GENERAL_PRACTICE, SIMULATOR_DESIGN.
5. Regenerate diagrams when architecture, state machines, recovery sequence or trust boundaries change.
6. Update README commands/status/paths/test counts.
7. Run drift checks: broken links/referenced paths, criterion IDs, schema/OpenAPI references, command validity, source-registry consistency and publication build.
8. Rebuild generated publication only through the existing build/workflow.
9. Record drift found and synchronized files in GOAL_PROGRESS.md.
10. Final ACCEPTANCE_REPORT.md must explicitly state whether drift was detected and what was synchronized.

Public docs must never use future tense for completed work or completed language for unimplemented work.

## GOAL_PROGRESS.md format

Keep a compact living file:

```markdown
# Goal Progress
Last updated: <UTC timestamp>
Commit/base: <sha>

## Current phase
<phase and objective>

## MUST status
- PASS: <IDs>
- IN PROGRESS: <IDs>
- FAIL/BLOCKED: <IDs + reason>

## Evidence added this iteration
- <criterion> -> <test/artifact/path>

## Decisions / ADRs
- ...

## Knowledge-base synchronization
- Drift detected: yes/no
- Cause:
- Updated:
- Publication/diagram impact:

## Next milestone
...
```

Never use progress text as acceptance evidence by itself.

## Commit discipline

Commit coherent milestones, for example:

- `feat(workflow): add durable job lifecycle and idempotent order intake`
- `feat(reconciliation): handle lost acknowledgement without duplicate pick`
- `feat(blender): implement bounded digital-twin runtime adapter`
- `test(e2e): cover restart and ambiguous reconciliation`
- `docs(kb): synchronize architecture and publication after runtime changes`

A milestone commit should include its tests and directly affected documentation. Do not claim completion in a commit message before acceptance is proven.

## Final release checklist

Before DONE:

- clean checkout/setup succeeds;
- deterministic demo succeeds;
- full mandatory tests succeed twice cleanly;
- lint/format/type/security gates satisfy criteria;
- critical lost-ack scenario applies exactly one pick;
- ambiguous reconciliation does not fabricate success;
- restart recovery passes;
- logical E-stop/cell fault behavior passes;
- mandatory CI needs no external model;
- metrics/log timeline requirements pass;
- all MUST criteria have evidence;
- ACCEPTANCE_REPORT.md is regenerated/current;
- documentation drift scan completed;
- README/plan/criteria/handoff/checklist/reports/diagrams/contracts are aligned;
- publication rebuilt through workflow;
- GitHub Pages/public links verified;
- final commit SHA recorded in acceptance evidence.

If any item tied to a MUST fails, status is NOT DONE.
