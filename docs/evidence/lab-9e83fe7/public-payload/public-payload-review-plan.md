# Separate eventual public-payload review plan - preparation only

Current source: 9e83fe7d41a52a63ba65b77730e392dafca8fffe. Publication authorization,
final payload, all current manual proof and remote attestation remain pending.
No archive scan or publication action has been performed by this plan.

The current eight-trace audit has a deliberately closed inventory of THIS source's
two four-case lab suites plus current logs/manual proof. Its historical-path guard
must not be relaxed to make that report claim coverage of old or published files.
A second explicit payload inventory/review is required before publication.

1. After evidence is complete, enumerate the concrete proposed public Git payload
   by exact commit/tree and compare it with the freshly verified remote base.
   Include newly added/modified tracked evidence, final manual archives, reports,
   source snapshots, logs, JSON/JSONL, raw text, ZIPs, images and PDFs. Also account
   for retained evidence reachable from that payload tree; distinguish already
   public unchanged bytes from newly published bytes. Do not use a partial changed
   filename list as a claim that every published archive was reviewed.
2. Freeze a separate inventory with repository paths, sizes, SHA256, provenance
   source/campaign, proposed inclusion and content disposition. No runtime/DB
   access is needed. Only actual public-payload files belong in this inventory;
   ignored local working files are not automatically published.
3. Explicit known historical input: `docs/evidence/lab-a881acf/failed-case/raw/trace.zip`
   and its surrounding failure/correction logs, JSON, source snapshots and timing
   receipts. A failed a881 source remains FAILED and its slow-response cause remains
   unproven. A current passing trace cannot replace that failed history. The actual
   public tree may contain other older archives (including 4774/b968); enumerate
   them, do not assume this one ZIP exhausts historical scope.
4. For every included ZIP: fully read all members, validate CRC, hash every member,
   scan full decoded textual network/DOM/resources/logs for credentials, and account
   for binary members. For logs/JSON/text, scan whole contents, not watcher prefixes
   or the first N bytes. Reuse a prior complete scan ONLY when exact current bytes
   match its explicit input/member hashes and the prior method/limits cover this
   purpose; record the reused receipt rather than implying a new scan.
5. Review potential private credential findings with redacted values/location/hash,
   distinguish known public demo-only credentials, and preserve immutable originals.
   If redaction is needed for publication, create a separately identified sanitized
   export and record provenance; do not silently rewrite original failed evidence.
   Metadata-only JSON summaries are not proof of all unsaved request headers.
6. Review truth/provenance of the actual publication text: historical versus current,
   passing versus failed/interrupted, synthetic stationary replay versus evaluated
   Blender recording, real protocol versus simulated systems, local versus remote,
   and exact tested source A versus evidence/status successor B. Human review of
   selected artifacts complements credential heuristics; binary screenshots are
   not scanned by text patterns or implicitly OCR-reviewed.
7. Keep PDF/text and image limitations explicit. The separate publication review
   renders every combined PDF page and requires root to view all sheets and selected
   HTML regions; it is not itself a complete credential scan of arbitrary binary
   artifacts. Future B status/build changes need their own fresh source-bound review.
8. Save a separate `public-payload-audit-inventory.json` and
   `public-payload-audit-review.json` with exact tree/base, all included/omitted paths,
   reused proof hashes, newly scanned byte/member counts, findings, resolutions and
   limitations. Never rename the eight-current-trace receipt to 'all archives PASS'.

Do not run this work concurrently with full acceptance or live physical demos.
No push/upload/workflow dispatch or external disclosure is authorized by this plan.
Root will review the concrete complete payload before requesting final approval.
