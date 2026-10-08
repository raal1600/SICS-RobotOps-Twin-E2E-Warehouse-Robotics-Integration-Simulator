# Client rebuild — achieved

Goal: rebuild the integrated client for an understandable, accessible end-to-end
engineering workflow. No deployment, push, external hardware or production actions.
Branch: `feat/client-rebuild`; initial HEAD `26d7aac9774d4f014e70da872dd4045d94428748`.
Pre-existing dirty work is preserved in `artifacts/client-rebuild/baseline-git.diff`
and `baseline-git-status.txt`. Untracked pre-existing files remain in place.

Product truth: [PRODUCT.md](../../PRODUCT.md). Design: [DESIGN.md](../../DESIGN.md).
Cloud review: [committed evidence package](../evidence/client-rebuild-20261008/README.md).
The user's explicit autonomous implementation instructions override skill suggestions
for interviews, mockup approval, or stopping after a fixed number of review passes.
No automatic hook approval is inferred. Direct implementation is this task's choice,
not a stored user-wide workflow preference.

## Critical journeys and observable acceptance

| Journey / start / goal | Actions and result | Failure/recovery | Baseline friction / improvement |
|---|---|---|---|
| J1 New local test, run a normal pick | Create isolated test, select product/scenario, authorize guided boundaries, verify original command effect count 1 and completed business records | Invalid/unavailable product and rejected stage preserve choices; duplicate click cannot execute twice | Setup below a long console → Run & watch with one next permitted action |
| J2 Run with lost acknowledgement | Notice uncertainty, inspect journal/observation, reconcile original command, verify outcome without a new command | Insufficient evidence remains uncertain and offers only genuine supported recovery | Repeated status and remote evidence → concise current outcome and direct inspection |
| J3 WMS unavailable after verified pick | Read physical/business distinction, inspect failed attempt, retry business acknowledgement, verify same command/effect count | Server rejection/network delay retain context and show recovery | All-green final view hides recovered failure → recorded failure history alongside final outcome |
| J4 Saved-run engineering inspection | Select saved scenario, stage, protocol/records/source; full Python selector and highlights; export; refresh/back restore selection | Source/record failures retain excerpt and allow real read retry | UUID-only history, focus loss, refresh resets → meaningful labels, keyboard tabs, persistent URL context |
| J5 Replay and test lifecycle | View original recorded motion/text phase, pause/step/camera, inspect then return; create/archive/delete only isolated tests | Read-only archive, confirmations, unavailable motion and backend refusal remain honest | Robot far below dense panels → separate task workspace preserving selection |

## Baseline evidence (before client rebuild)

`artifacts/client-rebuild/baseline/checks.json`: 174/174 Node UI tests, 5/5 actual
local-backend workbench browser tests, Ruff lint/format and mypy all pass.
`browser-audit.json`: initial saved lab screen has zero axe WCAG A/AA violations;
this does not detect the keyboard failures below. Includes resource/timing baseline.
Screenshots: `overview-1440.png`, `overview-1280.png`, `overview-390.png`.
Independent agent heuristic review: `artifacts/client-rebuild/independent-baseline/README.md`
and 14 screenshots. Zero attempted mutations. Not human research.

Prioritized issues: lost focus on trace/source changes; nonfunctional arrow navigation
in inspector tabs; wrong dialog return focus; refresh loses selected run/stage; UUID
history labels; recovered failures absent from summary; status repetition and sticky
overlays; long raw recovery wording. Baseline Source took 54 Tab presses from fresh
page; failed WMS attempt took 46. No fabricated task time or usability score.

## Capability mapping

| Existing capability | Rebuilt access |
|---|---|
| Test select/create/clear/delete; archive restrictions | Shared test context and Manage test data |
| Product and all scenario/observation choices, showcase/restock/reset | Run & watch setup and existing disclosures |
| 22 stages, physical gate, reconciliation, business-only retry | Shared current execution summary / authorized action |
| History, phases, proof ladder, search and all filters | Inspect evidence; secondary proof/phase disclosures |
| Data/State/Protocol/Source/Records/Decisions/Run info/Recovery/Raw JSON | Stage inspector; keyboard tabs |
| Two source modes, related components and symbol highlighting | Source → Full Python file selector |
| Investigation findings/evidence/manual requests and exports | Selected pick investigation / stage investigation |
| 3D replay, delivery/product selection, camera, frames, speed, snapshot | Run & watch; exact records remain separate |
| Live protocol evidence, metrics, API docs, simulation boundaries | Existing named disclosures and links |

## Acceptance matrix (final, 2026-10-08)

PASS requires observed behavior, not just an implementation. Final sequential
regressions passed: 753 core/lab, 27 browser and 174 UI tests; 90.28% coverage.
Fourteen axe states have zero violations; browser artifacts match the final client.
Detailed commands, evidence index and test distinctions:
[verification.md](verification.md). Skill provenance: [skills.md](skills.md).

| Criterion | Implementation | Test or review | Evidence | Status |
|---|---|---|---|---|
| Four skills installed and applied | Complete pinned project directories; direct reading; no automatic hooks | Tool smoke checks and file hashes match | skill-manifest.json; artifacts/client-rebuild/skill-verification.json | PASS |
| Integrated rebuild and capability mapping | Run & watch / Inspect evidence; existing logic and all mapped controls retained | Real journeys and independent navigation | Capability mapping above; independent-final | PASS |
| Usability | One current permitted action; setup beside robot; concise run choices | Actual execution and review paths | Client E2E; independent-final | PASS |
| Accessibility | Skip link, names, visible focus, roving tabs/trace, dialog focus, reduced motion, text alternatives | Axe plus keyboard and screenshot checks | Axe JSON; independent-final | PASS |
| Learnability | Product purpose, first-use next action, plain historical recovery | Independent task-based review | independent-baseline versus independent-final | PASS |
| Discoverability | Two named workspaces, visible source selector, unavailable-action reasons | Run/source/uncertainty task attempts | Independent review; client E2E | PASS |
| Consistency | Shared type/spacing/focus tokens, native controls, two source modes | Code and rendered review | DESIGN.md; workspace.css; screenshots | PASS |
| Feedback and visibility | Busy stages, failed-attempt history, honest disconnected/unconfirmed states | Lost response, source 503, empty and loading tests | Client E2E | PASS |
| Error prevention and recovery | Duplicate guard; read persisted state after failed intake; no automatic mutation retry | Real backend rejection and lost-response/offline cases | Client E2E; existing lifecycle tests | PASS |
| Efficiency | URL run/stage/tab/source context; retained focus; one trace Tab stop | Refresh/Back and keyboard actions | Independent review; client E2E | PASS |
| Cognitive load | Setup/replay separate from evidence; optional proof/map/technical detail; no sticky summary | Before/after screenshots and task review | Baseline versus independent-final | PASS |
| Information architecture | Task navigation and related evidence grouped; native links and Back | Navigation, source/component restoration | Client E2E; workspace.js | PASS |
| J1-J5 full final regression | Same backend and isolated real fixtures | All 27 browser and 753 core/lab tests pass | artifacts/client-rebuild/evidence-index.json; core-final.xml; browser-final-4.xml | PASS |
| Responsive, enlargement, large content | 320-1440px layouts; large Python files; 102-stage real showcase | Screens/axe; 200% text and zoom-equivalent reflow; actual UTF-8 export response | Final browser screenshots and traces in evidence-index.json | PASS |
| Engineering regressions and performance | No new framework; static query hardening; static asset allowlist | Lint/types/174 UI/security/syntax pass; 90.28% coverage; matched timing review | final-checks/checks.json; coverage.xml; comparison/performance.json | PASS |
| Authority, permissions and persistence | Existing execution guards, archived tests and API contracts retained | Real rejection/read-only tests; original commands effect count 1; all three saved demos unchanged after restart | Core/browser results; final-saved-run-check.json | PASS |
| No unresolved critical/high issue in rebuilt scope | Review and test defects corrected | Independent agent review plus final regression and screenshot inspection | independent-final/README.md; verification.md | PASS |
| Before/after comparison | Preserved dirty baseline versus final client on the same saved run | Actual screenshots, keyboard sequences and matched timing | comparison/before-run.png; comparison/after-run.png; independent reviews | PASS |
| Reusable E2E and reproducibility | Existing pytest/Playwright retained; six new cases; pinned axe and CI setup | Test files exercised against actual backend | tests/browser/test_client_rebuild.py; verification.md | PASS |
| Real screen-reader and human research | Not performed, explicitly reported | Not claimed as automated evidence | verification.md limits | NOT APPLICABLE - not required as a performed manual session; validation limit remains |

Observable comparison: Source required 54 Tab presses in the baseline agent review.
The first rebuilt review reached it in 12 Tabs + Enter + 3 arrows (16 key actions).
The final trace also has one Tab stop with Up/Down/Home/End traversal. The same
saved-run review now survives refresh and Back; before it reset. Recovered WMS
failures now appear in the run choice and summary before opening technical records.
These are observed workflow differences, not measured task times or usability scores.

The integrated preview remains available at `http://127.0.0.1:8000`. Work is on
`feat/client-rebuild`. The user subsequently authorized committing and pushing this
review branch; deployment remains outside scope. No external blocker remains.
Automatic skill discovery awaits a new repository session; all four
skills were explicitly read, smoke-tested and applied in this session. Human research
and real screen-reader testing remain unperformed validation limits, not conformance claims.
