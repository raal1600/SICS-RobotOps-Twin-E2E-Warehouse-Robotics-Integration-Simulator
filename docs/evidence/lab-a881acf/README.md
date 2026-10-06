# Source A local acceptance failed

Original source: a881acfee55bb56e808882f724a150ad77d05eb6. Source fingerprint and clean-start attestation remain in summary.json and the unchanged canonical acceptance manifest.

The first suite passed all 815 cases. The second suite had 814 passes and one clear-dialog assertion failure; zero errors/skips. The wrapper exited 1. Eighteen of 20 local gates passed; tests_2 and repeatability failed. CI, remote publication and Pages remain pending. Goal NOT ACHIEVED.

All eight lab cases passed their individual JUnit cases and retain effect1/completed22 snapshots. That does not make either the second suite or whole campaign pass. The first-pass independent 164-check review is preserved with fixed inputs. No second-pass 164-check semantic review was executed: its prepared success helper correctly remained unused after the suite failure.

The failed browser case sent the clear POST promptly. Its HTTP200 round trip took 4913.785ms, then refresh requests crossed the five-second dialog assertion deadline. Bounded trace metadata establishes timing, not the backend reason for the delay or eventual UI recovery. The original trace and two screenshots are retained; this archive performs no new rendering, DOM or exhaustive secret audit.

inputs.json maps preserved bytes to stable repository-relative archive paths and hashes. Canonical acceptance JUnits, coverage, manifest, logs and supporting gate reports stay in docs/evidence/acceptance/20261006T012424 and are referenced by hash. Original review bytes keep their historical paths and observation times; the mapping provides their archived counterparts. The older first-pass review is superseded only for input binding by the finalized review and formal-promotion proof.

The twelve selected lab PNGs were inspected earlier by the named reviewers. Their saved reviews state scope and limitations. Future manual, PDF, terminal-PASS and full trace/DOM audit helpers are excluded as proof and were never executed. No fresh exact-source manual/README CLI loop or remote completion is claimed.

Recipes are inert .py.txt snapshots of the actual read-only review procedures, bound to source A. They are evidence of method, not additional test runs. The archive requires root review before commit.
