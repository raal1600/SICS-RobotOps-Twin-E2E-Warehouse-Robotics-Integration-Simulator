# Current saved-evidence audit preparation only

Target source is `9e83fe7d41a52a63ba65b77730e392dafca8fffe`, fingerprint
`136641a25c5fbd7d45c016582ec2c5c5197362f44f0a894ee95a69c652e3eafd`, campaign
`docs/evidence/acceptance/20261006T024719`. These are ignored preparation copies.
No current audit, DOM decode, PDF read, render, browser, test or DB action has run.
Historical copies and proof remain unchanged. Syntax checks do not validate guards.

After the full campaign AND all fresh manual work finish, root must independently
verify the terminal results and stop the owned manual processes. Only then may an
explicitly authorized saved-file audit populate a new `final-trace-audit-inventory.json`
from `inventory-template.json`. The template deliberately remains NOT READY.
All references are repository-relative `{path, sha256}` objects. No stale fallback
or missing file is substituted. `scan_entries` additionally needs `kind` and `group`.

The common guard requires:

- Exact current HEAD and source fingerprint; no tracked source changes except the
  expected generated `ACCEPTANCE_REPORT.md`. A later source/status successor needs
  separate preparation, not a looser guard.
- Hashed current `manifest.json`, all twenty local gates passed with exit zero,
  and `artifacts/acceptance-response-sync-exit.json` with the exact source and
  start/end bracketing this campaign. `local_acceptance_review` must be the current
  pack's source-matched `local-acceptance-review.json` with local acceptance passed.
- Two `junit` references to this campaign's `tests-1.xml` and `tests-2.xml`, each
  exactly 815 unique cases, actual/declared counts matching, no failure/error/skip,
  identical testcase sets and different actual fixture roots. Coverage and the
  eight intended demo outcomes are separately verified by the terminal reviewer.
- Two `case_reviews` references to this pack's `pass1-case-review-final.json` and
  `pass2-case-review-final.json`, each source/campaign matched, four formal passing
  lab cases, 164 evidence checks, source hashes matched, and no outstanding issues
  or potential credential findings. The second review must assert equal full sets.
- Eight `cases`, one per `(acceptance_pass, case)` for happy, drop_ack_after_effect,
  duplicate_delivery and wms_unavailable. Each supplies runtime, session_id,
  job_id, command_id, case_json and trace. case_json MUST name the corresponding
  `passN-finalized-snapshots/<case>.json`, bound by the final review's snapshot hash.
  Mutable `pass-N/*.json` watcher outputs are rejected as final inputs. Session,
  command and job identities must be distinct and match actual pass fixture roots,
  terminal testcase identity, completed stage 22 and saved effect one. Happy is
  Blender; the other three use the synthetic runtime. Trace path must be exactly
  that case's saved artifact directory plus `/trace.zip`.
- `manual.status` SAVED_COMPLETE_AND_STOPPED, current source, a fresh explicit
  directory, completed_at, and a hashed stopped_processes record within that
  directory with nonempty stopped_ids and remaining:[] after completion. This is
  saved ownership/stop evidence, not a live process check. Manual completion and
  all journal/CLI timestamps must follow successful acceptance.
- Five manual cases: happy, lost, duplicate, cli-happy_path,
  cli-lost_ack_after_effect. Each needs session_id, command_id, expected_fault,
  session and journals refs. IDs must be fresh and distinct from the acceptance
  cases. Sessions must be lab, COMPLETED stage 22 with all stages present, correct
  saved scenario, source-bound runtime/PLC original receipt equality and effect one.
  CLI entries additionally require exact README command/exit/source/timestamps and
  explicit physical consent. Wrapper/raw session formats follow the prior helper.
- At least one complete six-tab inspector JSON in manual.inspectors, at least six
  explicit service/launcher paths in manual.log_paths, and ALL settled manual
  JSON/JSONL/log/Markdown/text/PNG files, recursively, listed in scan_entries.
  Every referenced manifest, terminal, JUnit, independent review, immutable case,
  trace, inspector, journal, CLI exit and stop record must be included with matching
  hashes. All eight trace paths must match the eight ZIP scan entries exactly.

After root authorizes the work and every input has been reviewed and bound:

```powershell
.venv/Scripts/python.exe artifacts/final-evidence-pack/9e83fe7/scan_saved_traces.py --inventory artifacts/final-evidence-pack/9e83fe7/final-trace-audit-inventory.json --run-saved-audit
.venv/Scripts/python.exe artifacts/final-evidence-pack/9e83fe7/review_trace_dom.py --inventory artifacts/final-evidence-pack/9e83fe7/final-trace-audit-inventory.json --run-saved-audit
.venv/Scripts/python.exe artifacts/final-evidence-pack/9e83fe7/finalize_saved_audit.py --inventory artifacts/final-evidence-pack/9e83fe7/final-trace-audit-inventory.json --run-saved-audit
```

The scripts refuse existing result outputs. Preserve any partial output after
failure; diagnose the mismatch before a newly reviewed attempt. Do not delete old
proof or weaken source/identity/completion guards to accommodate a missing field.
No scanner imports/execution is permitted during the live campaign.

The text scanner reads every member of each ZIP sequentially, CRC/hash checks it,
accounts for binary members, fully scans saved text and structured/decoded JSON,
and records candidate locations without copying private credential values into
its report. Public fixture credentials and redaction markers are classified
separately. Unknown candidates, parse/decode failure or changed inputs require
review. It is a heuristic scoped review, not a global secret-free guarantee.

The DOM reviewer decodes every saved main-frame delta snapshot, groups equal
relevant states with counts/first/last checkpoints, and checks supported briefs,
correct saved scenario captions, runtime/protocol/simulation labels, neutral
completion guidance and original current-command identity. It does not infer
pixel visibility from attributes or prove every transient millisecond.

The finalizer derives findings from those outputs and saved manual/inspector
checks. It never hardcodes historical failure or assumes a current pass. Current
source defects or missing observations stay findings. Saved semantic/one-effect
facts, presentation checks, formal test outcomes and manual actions remain distinct.

This review covers the explicit EIGHT CURRENT LAB TRACES plus inventoried current
logs/manual proof. It is NOT an audit of every file/ZIP that will be published.
See `public-payload-review-plan.md` for the separate historical/new payload review,
including the failed a881 trace. No GOAL completion or remote publication is
promoted by these local helpers. Archive program bytes later as `.py.txt` snapshots.
