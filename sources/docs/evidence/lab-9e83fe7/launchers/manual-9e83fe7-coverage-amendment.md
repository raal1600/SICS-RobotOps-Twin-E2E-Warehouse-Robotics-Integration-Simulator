# Current manual launcher amendment: coverage parser repair

This separate amendment preserves the original manual runbook and preparation receipts. Their launcher hash a3116840fda22f7ea6506852db92cb3f34010bc80c4c98a5a5735e2616c7bc59 describes the prepared launcher before its first invocation.

The first invocation stopped before service launch because Windows PowerShell5.1 could not convert coverage.py JSON containing an empty context-name key. Root retained its owner36916 and logs as artifacts/lab-final-9e83fe7-coverage-guard-failure*. Original launcher/CLI/stderr bytes are preserved in artifacts/final-evidence-pack/9e83fe7/prep-before-coverage-fix-20261006T035307/.

Current artifacts/run-manual-lab-9e83fe7.ps1 SHA256 is 81b20e45df77e48a80239e376722415d5e741c0c731c4392b0fac44989f12e42. The only edit extracts finite numeric totals.percent_covered using Python JSON, verifies exit/output, then passes a small totals object to PowerShell. The original85percent check and source/campaign/20-gate/two-JUnit/fresh-evidence guards remain unchanged. Actual saved coverages were read successfully through PS5.1 with exit0 and both scripts parsed with0errors; this did not invoke the launcher. Independent review65932f06e4877d01611e66440d9c7e672e5a55bf77dfacc154def5e40c3ed623 confirmed the same.

Root subsequently launched the corrected wrapper at2026-10-06T03:54:35.9132796Z, owner31548, as saved in artifacts/lab-final-9e83fe7-owner.json. This amendment reads that saved owner record only; it does not independently inspect live processes, restart services or attest the whole manual loop. Continue the existing runbook's evidence ordering and safeguards on this original runtime. The prior guard failure was not a physical request retry.

The final CLI launcher contains no coverage JSON parsing and remains byte-unchanged at509598a236dcf240af76f61e6e0bb55427273dd7991a033fc8fe6acf92f76150. No workflow/test source changed.

The active audit guard, inventory template, audit usage and PDF guard/usage do not hardcode the old launcher hash. Final inventory must bind the actual current launcher bytes and separately retain historical preparation/failure bytes. Hash mismatch must be resolved with the correct explicitly scoped reference; never disable hash guards or rewrite historical receipts. No audit guard changes were needed.

This amendment is provenance, not a manual, saved-trace, PDF visual or remote PASS.
