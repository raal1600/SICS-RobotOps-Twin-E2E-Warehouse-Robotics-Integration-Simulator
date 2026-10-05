# ADR 0013: Delete a test; clear and reuse the same test

Accepted design, 2026-10-05, following the owner's explicit correction. Verification
is recorded separately in GOAL_PROGRESS.md. This supersedes ADR 0011's permanent
deleted-test entries and lifetime display numbering, not its concurrency or
physical-effect protections.

## Operator meaning

- **Delete selected test** removes its world, orders, evidence, recordings and
  catalog row. **Delete all tests** applies that operation to the confirmed set.
  Once cleanup finishes its number is available again. New tests take the lowest
  unused positive number, so an empty workspace starts at Test 1. Surviving tests
  keep their numbers. Test UUIDs and robot command identities are never reused.
- **Clear test and retry** keeps the selected test's identity, number, creation
  time and saved cell/settings, removes its old execution data, restores a fresh
  scene and makes that test current. Scenario/observation selections remain in
  the UI. Clearing an archive is an explicit request to reuse that test; its old
  outcome is discarded, never relabelled successful. Other tests stay unchanged.
- Both operations require confirmation of data removal. Neither runs a pick,
  reconciles an outcome or decides a business verdict. Navigation, replay and
  ordinary startup still preserve all retained test data.

Restock/fresh scene remains different: it retains previous evidence and refuses
unresolved work. Logical cell reset still preserves products and jobs.

## Contracts and recovery

`POST /simulation-tests/{test_id}/clear` accepts `ClearTestRequest` with a UUID
`request_id` and positive `expected_revision`, and returns `TestClearing` with
request/test identity, `cleanup_pending` and current history. SimulationTest gains
additive `revision` and `clearing` fields (defaults 1/false for old fixtures).
These are test-management contracts; robot/world/observation schemas are unchanged.
The UI sends `X-Test-Revision` on world mutations. A stale revision returns
`TEST_REVISION_CHANGED` before any work. Legacy clients without the header retain
their existing interface.

`POST /simulation-tests/delete-all` names the destructive bulk operation clearly.
The old `/simulation-tests/clear` endpoint remains a deprecated delete-all alias
for existing clients; it is not used by the updated UI. Its expected-ID snapshot
and retry semantics are preserved. Selected deletion retains its existing API.

The existing catalog transaction and response-lifetime access barrier protect
reads, downloads, motion and file cleanup. In-flight work prevents clearing or
deletion. A clear first commits its intent, saved settings and incremented
revision, then removes owned world files and initializes an empty world with a
new scene epoch. Only then is the test made active and available. A partial clear
is visibly pending; no new execution or test creation is permitted until it is
finished. A retry or startup resumes that explicit intent, never the discarded
command. Cached API hosts invalidate their Engine when the revision changes.

Deleted test rows exist only while cleanup is pending. Completed deletion purges
them and releases the display number. A workspace-initialized marker prevents an
empty restart from recreating the original test. Migration also finishes cleanup
of historical tombstones, while preserving every retained test's identity and data.

The catalog keeps only SHA-256 request and payload digests for duplicate-request
protection, not deleted test IDs, labels, creation times, profiles, payloads or
target lists. Old raw operation receipts are converted and removed. These small
anonymous guards prevent a delayed creation from resurrecting a deleted world,
a repeated deletion from absorbing new tests, or a repeated clear from erasing
newer orders. Transient cleanup intent is retained only until removal finishes.

The application-owned path boundary is unchanged: registered UUID directories,
or the original world's configured databases/SQLite sidecars and Blender artifacts.
The installation, access/catalog infrastructure and unrelated files remain. This
does not claim forensic erasure of storage media.

## Verification

Regression tests inspect both filesystem and catalog after deletion, number reuse,
same-test clear after completed/uncertain/stopped work, intact neighboring tests,
stale requests, response loss, cached hosts, locked files, interrupted clear and
migration of old deleted entries. Real Chromium journeys exercise confirmation,
cancellation, clear/retry and delete/create Test 1 in both runtimes at desktop and
compact sizes. Test data is disposable; developing this feature does not authorize
deleting the owner's current history. No existing robot acceptance is weakened.

Browser verification exposed two adjoining presentation defects: periodic reads
could request the deleted original world before its response updated selection,
and unbounded display-rate replay could compete with Blender on CPU rendering.
Management pauses background polling and invalidates in-flight view versions.
Replay draws at 24 fps while preserving elapsed-time cursor advancement and
immediate scrubbing. Runtime deadlines, Blender quality and uncertain-outcome
semantics remain unchanged; the earlier failed runs remain in development evidence.

Final-source repetition then exposed an outstanding replay read racing deletion.
The backend correctly retained its response-lifetime barrier. The client now
drains its pending JSON and snapshot response bodies before confirmed management,
with polling paused and view versions invalidated. Snapshots are fetched to local
blob URLs so their HTTP reads participate too. A five-second stalled-view wait
sends no management request and permits explicit retry. Controls stay busy through
final refresh. Other clients' reads/downloads and real execution still block
destruction. Controlled delayed-body, failed-read and stalled-read tests exercise
this boundary without raising robot timeouts or retrying a pick. The original
failure is preserved in [read-race evidence](../evidence/test-reset-read-drain/README.md).
