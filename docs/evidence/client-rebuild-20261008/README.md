# Client rebuild review evidence

Review branch: `feat/client-rebuild`. This package accompanies the integrated client,
engineering inspection, source-view simplification, complete installed skills and
reusable regression tests. Start with [scope and acceptance](../../client-rebuild/README.md),
[verification and rerun commands](../../client-rebuild/verification.md),
[PRODUCT.md](../../../PRODUCT.md) and [DESIGN.md](../../../DESIGN.md).

## Recorded results

- `core-final.xml`: 753 passing unit/integration/contract/lab tests.
- `browser-final.xml`: 27 passing browser tests against isolated local/test backends.
- `coverage.xml`: 90.28% line coverage; the required threshold remains 85%.
- `checks.json`: passing lint, typing, 174 UI tests, security and JS syntax checks.
- `evidence-index.json`: 14 axe states with zero violations, zero page errors,
  and no client-source mismatch in the final browser run. Its artifact paths identify
  the original local screenshots/traces; only selected screenshots are copied here.
- `saved-run-preservation.json`: all three saved demos unchanged, each original
  command still at one effect after the preview restart.
- `skill-verification.json`: installed skill hashes verified against pinned sources.

## Visual and independent review

Compare [before](before-run.png) and [after](after-run.png), captured against the same
saved run. `performance.json` records matched conditions and samples; it supports no
general speed claim. The comparison's transient WebSocket reconnect label is not
connectivity evidence. Normal browser connectivity was checked by the independent review.

The [independent review](independent-final/README.md) and its ten screenshots cover
desktop, laptop, narrow layouts, source selection, investigation and keyboard focus.
`zoom-reflow.png` records 200% desktop-equivalent reflow; `six-product-trace.png`
records inspection of a real 102-stage showcase. This is agent heuristic evidence,
not human research. Real screen-reader testing was not performed, and no full WCAG
conformance claim is made.

`manifest.json` maps each copied file to its original path and SHA-256. Git preserves
these bytes and the installed skill bytes across checkout platforms. Source hashes
in the runtime reports describe the Windows files that were tested; normal Git
line-ending conversion can change hashes of application files on another platform.

Large traces, browser profiles, local databases, downloaded tool executables and
temporary build output are deliberately uncommitted. Reproduce them with the commands
linked above. No production deployment or real hardware action was performed.
