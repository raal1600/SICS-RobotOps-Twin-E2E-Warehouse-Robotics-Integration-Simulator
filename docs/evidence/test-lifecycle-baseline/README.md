# Historical HKM acceptance before the test-lifecycle change

[ACCEPTANCE_REPORT.txt](ACCEPTANCE_REPORT.txt) preserves the report copied from the
Windows checkout at `ae6d5d85c813e47aea042aea2a87236b5a8bc204`, before the
cell-selection and explicit test-deletion revision. Its audited implementation
source is `ca7798798f916c8130e1833cf16b4d4d3f10d546`; the new lifecycle feature
does not inherit those acceptance results.

The archived bytes are unchanged. The `.txt` extension prevents its original
root-relative Markdown links from being interpreted relative to this archive
directory. Those links refer to paths at the repository root of the recorded
revision, not files beneath this directory.

| Preserved object | SHA-256 |
|---|---|
| Windows checkout report, with CRLF line endings | `508183749dd5effe0ff875ebb1cc94363ba2e086a7d6f8d5256a47591bf7449f` |
| Git blob at `ae6d5d8:ACCEPTANCE_REPORT.md`, with LF line endings | `b0efa863c6eb87cb4f0a9b2dd2106503c9217314d9767c0ef4c781148a11d00a` |

Comparison confirms that these differ only by CRLF/LF line endings. No criterion,
result, command, log reference or explanation was edited in the archive.
Current verification belongs to [ACCEPTANCE_REPORT.md](../../../ACCEPTANCE_REPORT.md).
