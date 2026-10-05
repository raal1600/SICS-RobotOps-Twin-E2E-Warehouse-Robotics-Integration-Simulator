# Investigation workflow: development review

This is scoped development evidence from the dirty working tree based on
`0db6168b71bc4b500894fe7695ce082384c777b2`, not full release acceptance.
[Provenance](provenance.json) records source identity and copies of the browser
results. Each case's `browser.json` records hashes of the actual served UI and
journey test at browser start; those hashes were checked again when archiving.

The final affected browser run passed all five cases. Four exercise normal pick,
lost reply, evidence/manual inspection and download, return, contradictory then
normal re-observation, a new independent test and saved-history inspection.
They use actual HTTP/SQLite and both synthetic and real Blender runtimes at
1440×1000 and 390×844. The fifth intentionally returns HTTP 503 and verifies that
an application error does not become a simulated outcome. Normal journeys have
zero page/console errors. Exact JUnit and logs are retained here.

The lost-reply paths retain one original command and one PICK_EFFECT through
UNKNOWN_OUTCOME, REQUIRES_INTERVENTION and COMPLETED. Downloaded evidence matches
the API. Navigation issues no POST and leaves JobEvidence unchanged. Scoped URLs
are checked for the original world and a newly created test. The old replay can
remain selected while the blocking job's evidence is inspected.

Three browser-discovered defects were fixed and rerun: selection jumping during
slow planning, an optional snapshot requested too early, and inspection becoming
clickable before a saved test's evidence loaded. Earlier failing runs remain in
local artifacts; they are not counted as passes. The mandatory Node suite now
includes the new attribution tests as well as the prior suites (132 checks).

## Visual clarity assessment

The baseline ready page measured 2421 px at 1440×1000, with raw evidence below
2220 px. The redesigned ready capture is shorter (exact dimensions in provenance),
with scenario/run controls beside the cell and evidence one explicit action away.
The timeline no longer occupies the main page. It stays collapsed and limited to
260 px desktop / 230 px compact when expanded. Raw JSON and manual paths are
progressive disclosures, not removed technical detail.

Reviewed captures include the main cell, uncertain result, evidence, conflicting
observation, manual commands and independent-test identity. Desktop layout keeps
the scene recognizable behind a bounded inspector. The compact layout stacks
setup before the cell; Run scrolls to the cell, and investigation fills the viewport
with persistent header/tabs and an internal scroll area. No horizontal overflow,
clipped controls or browser errors occurred in the tested journeys. Supporting
plain-language guidance explains that checking again does not move the robot.

- [Desktop setup](blender-desktop/01-ready.png)
- [Desktop uncertainty notice](blender-desktop/03-notice-uncertainty.png)
- [Desktop investigation](blender-desktop/03-unusual-result.png)
- [Compact evidence](blender-compact/04-evidence.png)
- [Compact manual inspection](blender-compact/05-manual-inspection.png)
- [Compact contradictory report](blender-compact/06-conflicting-sensor-report.png)

This is an implementer review, not an independent first-time usability study.
The UI still teaches terms such as command journal and reconciliation; a novice
may need its inline explanations. Small-screen JSON is deliberately dense and
can be downloaded for external inspection. Touch-device and screen-reader studies
were not performed. Automation proves the tested interactions and evidence
ownership, not universal discoverability or real robot performance.

The generated report/diagram additions were visually inspected with Poppler.
An outdated publication footer/citation version was found and synchronized to
publication 1.3 / 2026-10-05; external research control dates were preserved.
Full clean repeated acceptance, exact-SHA CI and Pages/PDF checks remain separate
release gates. See [the operator guide](../../implementation/investigation.md).
