# ADR 0002: Immutable source identity and completion attestations

Accepted 2026-10-02. This records evidence handling, without changing any MUST or DONE rule.

A committed report cannot contain its own Git commit hash: changing the report
changes that hash. Each test run therefore records the exact inspected source SHA,
clean/dirty state, environment and source hash. Its original manifest and JUnit
remain inspectable. CI uploads its report and evidence for its actual GITHUB_SHA.

`make acceptance` runs the complete checks. After CI and publication finish,
`uv run --locked python -m tools.dev acceptance --refresh-remote <manifest-path>`
queries both workflows and public Pages for that manifest's exact source commit.
It preserves the original local manifest and adds timestamped remote evidence.
No local test result or source identity is upgraded or relabeled by this operation.
Missing or failed remote evidence remains FAIL.

Completion status synchronization requires every MUST and all three remote gates
to pass. A subsequent evidence/status commit still runs the complete CI and
publication workflows. Its exact SHA is recorded in the CI artifact and public
build.json. The final verification checks that successor explicitly; earlier
source evidence alone never attests an untested later revision.

The repository report identifies its audited source snapshot and links its
evidence. Final-SHA CI artifacts and the deployed manifest provide the independent
attestation for the commit that carries the report. This avoids an endless chain
of commits whose only purpose would be changing their own claimed identity.
