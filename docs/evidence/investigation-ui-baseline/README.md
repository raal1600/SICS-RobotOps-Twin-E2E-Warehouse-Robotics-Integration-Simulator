# Investigation UI baseline

The redesign began at clean source `0db6168b71bc4b500894fe7695ce082384c777b2`.
`ACCEPTANCE_REPORT.txt` is the exact earlier report, retained without relabelling
its audited source. `provenance.json` records its hash, goal hash and measured
baseline layout. The fresh Node baseline passed 119 checks. Those results and
historical full acceptance do not attest the new UI.

The baseline ready-page browser capture measured 2421 px document height at
1440×1000, with the raw evidence section beginning below 2220 px. The first
agent-browser fault capture occurred before its click actually submitted the
order; that failed attempt is not used as evidence of an executed fault. Later
Playwright journeys exercise real actions and persistence and retain their own
results. The redesign adds mandatory repeatable browser tests and fresh full
source-specific acceptance rather than modifying historical evidence.
