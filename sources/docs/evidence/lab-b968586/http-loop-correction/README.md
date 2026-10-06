# HTTP loop correction evidence

Focused correction on uncommitted source based on `b9685864afb6f47e440bd051789052070456c7b2`. **NOT ACHIEVED:** a new clean-source full acceptance and remaining final manual/publication/remote proof are pending.

[summary.json](summary.json) records the bounded causal diagnosis, exact case names/times, source identity and limits. [inputs.json](inputs.json) maps every byte-identical input to its original path and SHA256. Parent historical archive files and its input index were left unchanged.

- Deterministic transport probe reproduces skipped Proactor close/detach and retained-server shutdown; corresponding Selector cases drain cleanly. Twelve ordinary real resets pass on both loops, so exact Chromium timing is not claimed reproduced.
- Four permanent real HTTP/WebSocket lifecycle regressions passed (JUnit 0.955s); three desktop cases passed (15.667s); four Blender browser cases passed (223.458s, six intentionally deselected). These are focused scopes, not a complete corrected-source acceptance.
- Repository lint/format (201 files), typing (67 files) and the actual drift checker (169 MUSTs) passed. `drift-command-error.log` is the retained unsupported `tools.dev drift` invocation, never counted as PASS.
- `implementation-self-review.json` is the helper author's self-review. Root review is separately attributed. [independent-review.json](independent-review.json) records the separate evidence_pack review: no blocking finding within its stated static/saved-evidence scope; Linux/full acceptance/final manual/remote proof remain pending.

Script snapshots end in `.py.txt` / `.ps1.txt`; restore into an ignored diagnostic location to reproduce. Original log encodings and prior status wording are preserved.
