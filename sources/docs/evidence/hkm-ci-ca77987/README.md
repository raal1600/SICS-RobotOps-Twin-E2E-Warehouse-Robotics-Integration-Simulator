# Exact-source CI evidence: ca77987

This archive records independent inspection of remote evidence for source commit
`ca7798798f916c8130e1833cf16b4d4d3f10d546`. It does not attest any later
documentation, evidence or implementation commit.

All three exact-source workflows succeeded:

- [Deterministic acceptance, run 37201920103](https://github.com/raal1600/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/actions/runs/37201920103)
- [Windows desktop, run 37201920140](https://github.com/raal1600/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/actions/runs/37201920140)
- [Publication build and deployment, run 37201920122](https://github.com/raal1600/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/actions/runs/37201920122)

The downloaded `deterministic-evidence` artifact is ID `11303806852`, size
9,595,632 bytes, SHA-256
`d25b56711d9bc50918c9891f5b5886ab18ed9274aaa8db8e941813c9d3e92c97`.
The published digest was verified before extraction. Archive paths and file
types were checked to prevent traversal and symlinks; all 620 entries were
extracted inside the ignored local artifact directory. The ZIP is not copied
into this compact source archive.

Inspection selected only
`docs/evidence/acceptance/20261004T122415/manifest.json` from the artifact,
whose source is the exact clean commit above. Earlier archived manifests were
excluded. Both JUnit reports contain 622 passing tests, zero errors, failures
or skips, and identical test identities. Both coverage reports record
91.11514052583863%. All 19 local gates and eight Blender demos passed.
Controller events and typed reconciliation evidence independently confirm
one effect for lost acknowledgement and restart, inconclusive contradictory
evidence, and six preferred tools with six effects in the showcase.

The CI command runs acceptance with `--local`: its archived manifest retains
three unrefreshed remote gate placeholders and five associated pending MUSTs.
The independently completed workflow results are recorded separately here.
This archive does not rewrite the CI manifest or substitute for the current
root acceptance report. The optional model-fallback SHOULD remains unimplemented.

Files:

- `final.json`: exact-source workflow conclusions and URLs.
- `ci-evidence-verification.json`: selected manifest hash, environment, two test
  runs, coverage, local gates, demo invariants and pending remote placeholders.
- `*-artifacts.json`: original GitHub artifact metadata and published digests.
- `evidence-byte-verification.json`: all 39 earlier local evidence files match
  their original bytes in this source commit; all 15 browser manifest file
  hashes match committed Git blobs.
- `archive-manifest.json`: byte-exact copy provenance and hashes for the
  imported metadata.

All robot, tool, trajectory, observation and effect evidence concerns the
deterministic synthetic simulator. It is not validation of real robot dynamics,
physical perception, safety certification or industrial throughput.
