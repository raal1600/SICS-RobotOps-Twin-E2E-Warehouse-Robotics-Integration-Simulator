# Independent final Blender demo audit

This scoped audit examines the persisted demonstration evidence from source
`ca7798798f916c8130e1833cf16b4d4d3f10d546`, acceptance run
`20261004T122253`. [reviewed-audit.json](reviewed-audit.json) passes all four
scenarios. It supplements the formal acceptance report; it does not independently
attest full-suite coverage, remote CI, or publication.

| Scenario | Independent persisted result |
| --- | --- |
| Lost acknowledgement after effect | One order, one job, one original command, one controller journal entry, one Blender pick invocation, one `PICK_EFFECT`; `UNKNOWN_OUTCOME` ? reconciliation with the original journal and a fresh observation ? `COMPLETED`. |
| Restart | The same single-command/single-effect result after the separately invoked resume process; the original command identity is preserved. |
| Ambiguous observation | One original command and one effect; contradictory source/destination evidence yields `INCONCLUSIVE` and `REQUIRES_INTERVENTION`, with no replacement command. |
| Six-product tool showcase | One order, six jobs, six original commands and six effects; A/B/C/D/E/F use single suction, suction array, adaptive soft, narrow pinch, wide pinch and support fork respectively. The first tool is already mounted; five subsequent changes are persisted before their product effect. All six observed verifications succeed. |

The harness uses SQLite read-only/query-only connections and checks database/WAL
hashes before and after its reads. It imports no application runtime and invokes
no replay, recovery or execution behavior. It checks original command payload
digests, controller receipts, request/response identities, world-step changes,
scene/motion hashes, fresh-observation chronology, verification verdicts and
persisted tool-rack occupancy. Simulator world state is inspected only as a
labelled test oracle, never supplied to the verifier. Database rows do not record
process IDs; the restart-process claim additionally relies on the recorded CLI
resume output and the checked-in subprocess implementation.

## Transparent audit comparison correction

[initial-audit.json](initial-audit.json) preserves the initial ad hoc audit's
failure. That harness compared every unrelated product dictionary exactly across
Python float64 input and Blender float32 evaluated transforms. This was an audit
comparison mismatch, not a mandatory acceptance test or production failure.

[precision-review.json](precision-review.json) records all 45 unrelated-product
comparisons. Every non-transform field is exactly unchanged. The maximum absolute
position/quaternion component difference is **2.384185793236071e-08**, below the
existing actual-Blender test precision of **1e-6**. For example, an unchanged
`SKU-C` x position is represented as `-0.85` before Blender and
`-0.8500000238418579` afterward.

The reviewed harness applies that same established pose precision to unrelated
products as it already did to the transferred product. Object identity,
attachment, location, units, frame and calibration remain exact comparisons.
No production tolerance, mandatory test assertion, or acceptance requirement was
changed. Both original harnesses and both reports are preserved byte-for-byte.

## Evidence provenance and replayability

[manifest.json](manifest.json) contains hashes of every archived raw file and the
primary tracked demonstration exports/logs. The inspectable primary exports are:

- [Lost acknowledgement](../acceptance/20261004T122253/demo-lost_ack_after_effect.json)
- [Restart](../acceptance/20261004T122253/demo-restart.json)
- [Ambiguous observation](../acceptance/20261004T122253/demo-ambiguous.json)
- [Six-tool showcase](../acceptance/20261004T122253/demo-tool_showcase.json)

These exports include causal timelines, controller events, typed evidence and a
clearly labelled simulator oracle. The independent audit also read the original
SQLite databases and Blender exchanges under the ignored local
`runs/20261004T122253/` tree. Their hashes are retained in the reviewed report;
large `.blend` files and databases are not duplicated here. Therefore a clean
clone can inspect the committed exports and audit record, while re-running the
SQL audit requires retaining those original local inputs or producing a new
acceptance run and adapting the diagnostic paths explicitly.

`initial-harness.py.txt` and `reviewed-harness.py.txt` are archival diagnostic
source, not additional production/test modules. Their original executions were
`python artifacts/audit-hkm-final-demos.py --wait` and
`python artifacts/audit-hkm-final-demos-reviewed.py`, from the repository root.
The reviewed harness intentionally refuses to overwrite an existing report.
