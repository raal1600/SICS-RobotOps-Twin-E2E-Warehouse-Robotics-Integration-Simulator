# A publication review preparation only

No PDF has been opened, scanned or rendered by this preparation. No build, browser,
service, dependency installation or tracked edit was performed. This is read-only
review preparation under the PDF skill, so no PDF create/edit marker applies.

Source A is `9e83fe7d41a52a63ba65b77730e392dafca8fffe`, fingerprint
`136641a25c5fbd7d45c016582ec2c5c5197362f44f0a894ee95a69c652e3eafd`, campaign
`docs/evidence/acceptance/20261006T024719`. Finish the full acceptance AND five fresh manual/CLI cases, then stop all owned manual processes first.
Root independently reviews its terminal exit, tests, coverage, demos and all gates.
Do not overlap this rendering workload with acceptance or physical demonstrations.

The prepared script checks exact HEAD/source fingerprint, no tracked changes except
generated `ACCEPTANCE_REPORT.md`, the campaign's clean identity, matching terminal
exit0/source/timestamp interval and all20 local gates. It requires `_site/build.json`
to identify A and match the exact archived `publication-build.json`, with status
`NOT DONE`. Each part PDF must match its build-manifest SHA256. It refuses a stale
4774/b968/B build or existing output directory; it does not rebuild or repair files.

The shared audit guard also requires the exact source-matched local review, two clean
identical 815-case JUnits, two formal case reviews and eight immutable final cases,
plus five complete fresh manual/CLI sessions and their stopped-process record.
It reads the explicit finalized inventory; it does not run a ZIP or DOM scan.
See `audit-programs-usage.md` for all inventory fields. The same binding is rechecked
after rendering. Current A preps or mutable watcher snapshots cannot substitute.

After those prerequisites, root may explicitly run this from the repository root,
using a new UTC suffix (example is a recipe, not an execution record):

```powershell
$taskReviewStamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$taskReviewOut = 'artifacts/publication-review-9e83fe7-' + $taskReviewStamp
& .venv/Scripts/python.exe artifacts/final-evidence-pack/9e83fe7/review_publication.py --render-after-terminal --inventory artifacts/final-evidence-pack/9e83fe7/final-trace-audit-inventory.json --output $taskReviewOut
$taskReviewExit = $LASTEXITCODE
```

Capture the actual command/UTC/exit/output. A failure retains partial outputs;
inspect its cause and use a new directory after correction. Never overwrite a prior
review or mark it PASS because some images exist. No dependency install is attempted.
The prepared environment has discoverable `pypdf` and `PIL`; rendering uses exactly:

`C:/Users/ramis/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe`.

The script reads all three parts plus the combined PDF using pypdf and requires
the combined per-page extracted text to equal the ordered part text exactly, with
all page counts matching the build manifest. It records four PDF hashes and
per-page text hashes. The build manifest has no combined-PDF expected SHA256;
the combined digest is freshly recorded, not falsely described as comparison to a
preexisting manifest digest.

Every combined page is rendered, in sequential eight-page Poppler batches with
a 60-second per-batch bound, at 85 dpi. Full-resolution PNGs and two-column,
four-row contact sheets preserve the page pixels without thumbnail downscaling.
Sheet/page ranges and hashes are listed in `structural-review.json`; the number
of pages is derived from the current PDFs, never assumed to be the old 64 pages.
All PDF, build, campaign and HTML hashes are rechecked after rendering. This is
structural verification, with `VISUAL_REVIEW_PENDING`, not visual PASS.

Root must then:

1. View **every** listed contact sheet at original resolution. Check every page
   for clipped/overlapping text, missing glyphs, black boxes, illegible tables or
   diagrams, covers, contents, page numbering and section transitions. Open the
   original page PNG when a sheet is unclear; capture any additional zoomed review
   explicitly. Reading extracted text alone is insufficient.
2. Confirm the visible `NOT DONE` status and simulator/real-protocol boundaries.
   Compare any claim of local results to source A, including preserved failures.
   This review does not validate external scientific claims again.
3. Open this exact local `_site` in the chosen browser only after the PDF pass:
   capture full `index.html`, full `governance.html`, and a representative
   `design.html` viewport. Also inspect changed/status sections and relevant
   diagrams/tables in the three reports as needed. Use the local files or an
   explicitly owned static preview; the script does not launch either. Record
   actual URL/path, viewport, screenshot file/hash and which regions were seen.
   A top-viewport screenshot is not evidence for all HTML below the fold.
4. Save a separate `visual-review.json` in the new output directory. Include A and
   the structural receipt hash, each sheet's actual reviewed flag and findings,
   actual HTML captures/hashes, review UTC, reviewer, chosen detail views,
   remaining limitations, and a truthful scoped result. Require every listed sheet
   reviewed and no unresolved visual findings before saying visual PASS. Preserve
   `structural-review.json` unchanged.

This is a local-build review, not remote Pages proof. Publication remains `NOT DONE`
before exact-source remote gates. A future evidence/status successor B needs a new
source-bound build/review of changed output and its own CI/publication/Pages proof;
this A-specific guard intentionally refuses B. Do not loosen it to reuse old proof.

This publication review does not cover every historical archive in the public payload.
Use the separately scoped `public-payload-review-plan.md`; do not promote an eight-trace
audit to all-published-archive coverage. All future review outputs remain pending.
