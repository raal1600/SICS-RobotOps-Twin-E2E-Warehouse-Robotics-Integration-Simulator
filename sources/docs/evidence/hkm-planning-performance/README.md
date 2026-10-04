# Scoped planning performance evidence

This package records the performance correction after the first full HKM
acceptance attempt at `0d8a8dbf72b063f43f7ca80460a7b67c577172e9` failed two tests.
It is **not a complete acceptance result**, a later-commit attestation, or evidence
that CI/publication passed. The current benchmark and targeted checks ran on an
uncommitted correction; [review.json](review.json) identifies the five inspected
source files by SHA-256 and hashes every preserved raw artifact.

Whole-catalogue copying inside per-segment tool/rack checks dominated the original
instrumented run. Individual specification lookups now copy only that spec, and
one collision preflight reuses its own isolated catalogue and fixed rack bounds.
Occupancy and deliberate dock contact are still checked for every segment.
No freshness, Brain timeout, collision, verification or coverage limits changed.

The [before](benchmark-before.json) and [current](benchmark-current.json) benchmarks
contain all six tool-selection explanations and complete trajectories. Those
semantic values are identical. Under coverage branch tracing plus cProfile, the
harness fell from 47.995 to 3.284 seconds and whole-catalogue copies fell from
5,062 to 258. The current SKU-B plan took 0.150 seconds; the slowest current single
plan was 0.273 seconds. These are local diagnostic timings, not portable performance
thresholds or simulated robot cycle-time claims. The small
[before](profile-before.txt) and [current](profile-current.txt) profile summaries
preserve the measured call counts.

The profiling harness deliberately supplies the original observation timestamp to
validation so profiler overhead does not obscure the measured computation. That
diagnostic call is not a freshness test. The unchanged ordinary tests separately
exercise production freshness and timeout behavior:

- [Targeted JUnit](targeted.xml): 66 tests passed, including all six Brain plans
  and the six-product API case that previously failed. The command nevertheless
  **exited 1** because this partial suite covered only 69.17% of the application,
  below the unchanged 85% full-suite requirement. The complete
  [coverage result](targeted-coverage.json) is preserved; the coverage gate did not pass.
- [Broader regression JUnit](regressions.xml): 144 tests passed, zero failures or
  skips, including catalogue isolation, host/fixed-runtime preflight defenses,
  observation boundaries, scenarios and API behavior. This command exited 0.

[original-review.json](original-review.json) is the original review copied without
changes. Its `artifacts/` paths identify the original locations; `review.json`
maps them to the preserved files here. All copied benchmark, profile, coverage,
JUnit and harness files retain their original bytes. No historical result was
rewritten to look successful.

The raw [before harness](harness-before.py.txt) and
[current harness](harness-current.py.txt) retain their original `artifacts/` working
location assumptions. They are provenance, not launch scripts in this directory.
To reproduce them, use isolated checkouts of the recorded baseline and corrected
source, copy the applicable harness back to its original path listed in
`review.json`, and run from that checkout's repository root. The exact recorded
commands are in `review.json`. Full repeated acceptance remains a separate gate.
