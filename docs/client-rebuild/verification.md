# Client rebuild verification

Status: **ACHIEVED**, 2026-10-08. Final sequential suites pass on the frozen client.
No known critical/high task-completion or accessibility issue remains in the rebuilt
scope. This is evidence for the defined workflows, not a claim of universal usability
or full WCAG conformance.

## Reproduction

From the repository, use the locked Python environment (`uv sync --locked
--all-groups`). Install the pinned Chromium shell with `uv run --locked python -m
playwright install chromium --only-shell`. Inside `tests/browser`, run
`npm ci --ignore-scripts --no-audit --no-fund`; return to the repository root.
Make setup and Linux CI include these browser dependencies.

```powershell
.venv/Scripts/python.exe -m tools.dev lint
.venv/Scripts/python.exe -m mypy
node --test (Get-ChildItem tests/ui/*.test.cjs).FullName
.venv/Scripts/python.exe -m tools.security_check
.venv/Scripts/python.exe -m pytest tests/browser -q -p no:cacheprovider --basetemp artifacts/client-rebuild/browser-reproduction
.venv/Scripts/python.exe -m pytest tests/unit tests/integration tests/contract tests/lab -q -p no:cacheprovider --basetemp artifacts/client-rebuild/core-reproduction --cov=robotops --cov=apps
```

Set `ROBOTOPS_POSTGRES_DSN` and `ROBOTOPS_AMQP_URL` to the local test services before
the lab lane. Its existing fixtures create and remove their own random PostgreSQL
schemas and RabbitMQ queues; they do not reuse the three saved demonstration runs.
Blender must be installed as documented in `docs/implementation/dependencies.md`.
Use a new basetemp directory for a new run. Run heavy browser/lab lanes sequentially:
overlapping suites can make genuinely fresh observations expire before verification.
The product's freshness rules and test assertions are unchanged.

The client is static HTML/CSS/JavaScript served by FastAPI; there is no production
bundler. `node --check` for all six client JS files, real static-asset delivery,
contract tests and actual browser loads are its build-equivalent checks. No stack
or runtime dependency was added. The separate publication generator and desktop
host were not rebuilt; neither was changed by this work.

## Evidence and outcomes

- GitHub/cloud review: [committed evidence package](../evidence/client-rebuild-20261008/README.md)
  contains the final test reports, screenshots, hashes and independent review. Full
  browser traces and runtime databases remain in ignored local artifacts.
- Baseline: `artifacts/client-rebuild/baseline/` and
  `artifacts/client-rebuild/independent-baseline/`.
- Final design/keyboard review: `artifacts/client-rebuild/independent-final/`.
  Ten screenshots cover 1440px desktop, 1366px laptop and 390px narrow views.
- Reusable client tests: `tests/browser/test_client_rebuild.py`; all other browser
  and lab journeys remain in the existing pytest/Playwright framework.
- Browser fixtures save screenshots, exact client source hashes, request logs,
  axe JSON and traces beneath `artifacts/investigation-browser/`; distributed
  journeys save corresponding evidence beneath `artifacts/lab-browser/`.
- `artifacts/client-rebuild/final-checks/checks.json` records individual commands
  and exit codes for lint, typing, 174 UI unit tests, security and JS syntax.
- Final core result: 753 passed, 90.28% coverage (85% required), recorded in
  `core-final.xml`, `core-final.txt` and `coverage.xml` under `artifacts/client-rebuild/`.
- Final browser result: **27 passed**, no failures/skips, in `browser-final-4.xml`
  and `browser-final-4.txt`. Fourteen axe states have **zero violations**. The
  evidence index is `artifacts/client-rebuild/evidence-index.json`: it links each
  final test to screenshots/traces and verifies zero client-source hash mismatches.
  All page-error lists are empty. Console errors occur only in the explicitly
  injected 503, real 409 rejection, and interrupted-network cases below.
- Before/after: `artifacts/client-rebuild/comparison/before-run.png` and
  `after-run.png`; independently reviewed settled screens are in `independent-final/`.
  Final zoom-reflow, narrow confirmation-dialog and 102-stage trace screenshots
  were also visually inspected, not only checked through DOM assertions.
- Preview restart preserved all three saved demonstration sessions exactly, including
  revisions and each original command's effect count of 1; see
  `artifacts/client-rebuild/final-saved-run-check.json`. These results predate the
  separately authorized review-branch commit/push. No deployment occurred.

Real-backend coverage includes normal execution, lost acknowledgement, conflicting
observation followed by safe reconciliation, WMS business-only retry, duplicate
delivery/authorization, refresh, read-only archives, clear/delete/create, Blender
motion, source/protocol/record inspection and evidence exports. The large-data
journey executes the real six-product showcase and inspects 102 persisted stages;
each original command must have exactly one effect.

Injected cases are explicitly labeled in the test source: source GET 503, held
source reads, failed intake response and unavailable follow-up reads. The lost
response test actually lets the backend create the run before hiding its reply.
Invalid input is injected into a request because the UI's registered select
options prevent that value; the real backend must return its 409 rejection. These
tests supplement genuine unmocked client-to-backend journeys.

## Defects found and fixed

The rebuild fixed focus lost during trace replacement, source-selector refresh
and full-file loading; missing arrow navigation in inspector tabs; incorrect
dialog return focus; lost historical context on refresh; unreadable UUID-only run
choices; hidden recovered failures; sticky overlays; and robot autoplay that
ignored reduced motion. Full source mode/component now also survive refresh.

Execution tests found that the unresolved pick's Review action disappeared when
another recording was selected. It now remains reachable. Network tests found
that a lost successful intake response left Create enabled. Intake now reads
durable sessions after a failed response and recovers the original run; if that
read is unavailable, further intake is blocked until reload confirms state. No
write is retried automatically and no physical result is inferred from a UI error.

Two scanner findings in the existing engineering inspector involved SQL assembled
from a fixed internal table list. The small backend hardening makes these four
queries explicit constant strings while retaining bound command parameters and
the exact record schema. No scanner exception or security rule was weakened.
The only other backend change serves the two new static client files.

Test changes retain outcome assertions. Old stage-title assertions now target the
dedicated stage position. Tests navigate to the visible workspace and explicitly
follow the final stage after refresh preserves a historical selection. The raw
payload disclosure test uses Raw JSON; Protocol is a structured view. The large
download must match the real export endpoint and all stage identities/outcomes;
its authorization fields are intentionally sanitized by the existing contract.
The penultimate browser run passed 26 cases and failed only the new export case.
The new export test initially decoded UTF-8 using Windows CP1252; that test bug
was fixed with explicit UTF-8 and comparison against the exact download response,
retaining all persisted stage identity/outcome assertions.
Its focused rerun and the full 27-case final rerun pass. Earlier failed runs remain
available as diagnostic history and are not counted as passing evidence. One existing
Starlette deprecation warning remains in the core run; no assertion was suppressed.

## Design and accessibility review

Impeccable's manual detector ran on the client. Static HTML scanning cannot resolve
the server-root `/ui/` stylesheet paths, so its flat-heading warning is incomplete
analysis. Actual computed sizes are 22px/18px/16px for h1/h2/h3, with visible weight
and grouping. The reported source-less image is a hidden snapshot element whose
real source is set before display. Direct CSS/JS scanning reports existing accent
borders and the old fallback font declaration; runtime uses system-ui. These are
reviewed style findings, not task or accessibility failures. No automatic hooks
were installed. Raw detector output is retained under `artifacts/client-rebuild/`.

Current Vercel Web Interface Guidelines were fetched and reviewed. Concrete fixes:

```text
apps/erp_ui/index.html:5 - main skip link added.
apps/erp_ui/index.html:61 - trace search has label, name and technical-input settings.
apps/erp_ui/index.html:71 - component name comes from visible label; source has two modes.
apps/erp_ui/index.html:116 - replay frame controls use their visible accessible names.
apps/erp_ui/workspace.css:54 - execution summary is static; it cannot cover keyboard focus.
apps/erp_ui/workspace.js:68 - native navigation links preserve URL context and browser Back.
apps/erp_ui/integration-console.js:49 - inspector tabs support roving focus and arrow keys.
apps/erp_ui/playback.js - reduced motion pauses autoplay; explicit Play remains available.
```

The native investigation dialog was exercised with Tab, Shift+Tab and Escape;
focus stayed inside and returned to its actual opener. Create/clear/delete dialogs
restore focus after cancellation or completion; when a deleted test removes the
opener, focus moves to the available new-test action. Axe WCAG A/AA checks cover
normal, empty, source, enlarged-source, validation-error, unconfirmed-request and
dialog states. Tests include 1440/1280/390/320px layouts, 200% text enlargement and a 640x360 CSS viewport at device scale 2 (the reflow geometry of a 1280x720 desktop at 200% zoom). This is not a real assistive-technology or OS magnifier session.
Canvas motion has a changing text phase, recorded event details, exact evidence
and keyboard/click camera and frame controls. Color is supplemented by status text,
selection attributes, labels and source line numbers.

Real screen-reader testing and human user research were **not performed**. The
independent reviews are agent heuristic reviews. Automated scans and these checks
do not establish full WCAG 2.2 AA conformance. The minor distinction between stage
number and repeated-attempt sequence remains; both are labeled in the evidence.

## Performance

The comparison script in `artifacts/client-rebuild/compare-client.py` routes a
reconstructed pre-rebuild client and the rebuilt client against the same saved lab
run. The baseline combines HEAD with the preserved initial dirty patch. Unchanged
CSS/scene/guide content is checked equal after line-ending normalization. Both
variants use identical vendor delivery, viewport, reduced-motion preference and
three alternating cold contexts. Preliminary runs with unequal vendor routing or
an excluded dirty patch are retained with explicit invalid-comparison names and
must not support a performance claim. The final comparison is
`comparison/performance.json`: median ready-to-replay time **3,075 ms before /
2,925 ms after**; median navigation load **42.8 ms / 47.5 ms**; client asset bytes
**215,599 / 239,664** (vendor assets excluded equally); DOM elements **943 / 957**.
The added 24,065 bytes are the workspace, focus/context and recovery behavior.
The 4.7 ms navigation difference is small beside data/motion loading. Final readiness
also waits for workspace restoration. Three alternating runs, after the heavy suites
finished, support no general speed claim; no meaningful loading regression was
observed. No framework, font download or runtime dependency was added.

The matched comparison intercepts local assets equally; its transient WebSocket
reconnecting label is not connectivity evidence. The independent normal-browser
review records zero failed requests and verifies the settled live application.
