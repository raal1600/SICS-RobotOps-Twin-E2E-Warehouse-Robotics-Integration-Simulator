# Engineering inspection

The guided console now connects a saved step to protocol fields, related Python
components, stored records, decision inputs and run identity. It keeps the existing
execution cursor, authorization gates, proof ladder and original-command replay.

## Use it

1. Open a saved execution session and select a stage in the trace.
2. **Protocol** shows the saved exchange as labelled fields with exact source paths.
   False values, missing results and failure responses remain visible after recovery.
3. **Source** has two choices: **Saved excerpt** and **Full Python file**. Full-file
   mode always includes the component selector; the excerpt mode hides it. Choose
   a component to display its full Python file. For lab controller
   steps this includes the HTTP edge client, edge process, OPC UA client, virtual
   PLC and persistent PLC journal. Other stages expose planning, validation,
   tool/path selection, observation, storage, robot runtimes and WMS code.
   The selected function or class is highlighted in teal with line numbers and an
   explicit line range. The code pane jumps to it automatically. Selecting **Full
   Python file** again reloads the selected file and returns to its highlight.
   The rest of the full file stays visible. If the file or component list is
   unavailable, the same Full Python file control retries the read.
   This marks the named implementation, not lines proven to have executed.
4. **Records** resolves linked domain records, stage effects, authorization records,
   the selected job/order, inbox/outbox rows, and saved lab protocol notifications.
   Search for a record type, ID, table or field, then expand the matching record.
5. **Decisions** shows recorded results, the boundary rule, proof claims, recovery
   guidance and linked planning/observation/command/verification records. Linked
   job records may be later than the selected step; check their IDs and timestamps.
6. **Run info** separates recorded identity/version/hash fields from current runtime
   settings and identifies missing historical provenance.
7. Links at the bottom follow the same job or command through other saved steps.
   **Download this inspection** saves the currently displayed read snapshot. The
   ordinary saved-run export remains available separately.

Technical tabs collapse the long step explanation; it can be reopened at any time.
Execution status stays visible. Selecting, filtering, refreshing, downloading,
opening source and replaying never authorize another stage.

**Follow latest step** returns inspection from an older selection to the newest
saved result and follows new results as they arrive. When already following, it
becomes the disabled **Latest step selected** indicator. A pending stage has no
saved result until it runs; following does not advance execution.

## Evidence boundaries

- Saved excerpts and stage inputs/results are historical evidence. Full Python
  files are **current reference code**, with a displayed-content SHA-256 and symbol
  location. The related-component catalog is not a runtime call trace. Synthetic
  and Blender implementations are alternatives, not evidence that both ran.
- Domain records are immutable. Job/order/inbox/outbox rows are labelled **current
  row, read now**. The inspection timestamp and session revision are displayed.
  Record collections can include later records for the same job. Refresh is explicit.
- Protocol values are structured adapter evidence, not packet captures. Exact wire
  arguments or node IDs absent from a stage cannot be reconstructed. Saved OPC UA
  notifications are available under Records; at most the first 300 are returned,
  with truncation explicitly reported.
- A saved list of check names is not an individual pass/fail report. Current
  settings do not establish the thresholds used by a historical run.
- PLC logic is Python simulation code. No vendor PLC project, ladder/ST program,
  real-hardware validation or safety certification is supplied. The lab's actual
  OPC UA security mode remains visible in recorded protocol fields.
- Existing runs do not contain a complete immutable build/source or configuration
  snapshot. The UI explicitly lists those gaps. PLC database files, full motion
  files and source file bodies are not embedded in the inspection download.

## Implementation and verification

`robotops/integration/inspection.py` projects evidence using only the existing
workflow store's read-only connection. It does not construct another store, query
the live controller, read environment variables or invoke the robot runtime.
Identifiers come from the selected session/job; reads do not fall forward to the
session's newer job. SQL table/column identifiers are application constants and
record IDs are bound parameters. Responses pass through the existing sanitizer.

The additive endpoints are:

```
GET /integration/sessions/{session_id}/steps/{step_id}/inspection
GET /integration/sessions/{session_id}/steps/{step_id}/source?component={catalog_key}
```

The source route resolves a stage/profile-specific catalog key, validates the known
source-file allowlist and repository containment, and reads text without executing
it. Late step/session/component responses cannot replace the current selection.
Missing files and failed catalog reads remain unavailable, with a retry path.
Function/class ranges come from Python's syntax tree, including decorators. If a
symbol cannot be located or redaction changes line counts, highlighting is marked
unavailable. Code is inserted as text and copying it excludes the visual line numbers.
There are no database migrations or execution-path changes in this follow-up.

Checks cover immutable read routes, forbidden writable connections/runtime access,
source scope, catalog symbols, cross-job isolation, false/null/empty evidence,
stale UI responses, real-browser inspection/export/mobile layout, and the existing
authorization/recovery/playback journeys. See the
[inspection evidence pack](../evidence/engineering-inspector-20261008/README.md).
