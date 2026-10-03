# ADR 0006: Full delivery replay and scenario preparation

Accepted locally 2026-10-03; no commit, push or public deployment requested.

Three product runs share one synthetic scene but create separate business orders.
The previous viewer replayed only the selected job, and changing scenario left
the depleted fixture unchanged. The dashboard now defaults to full delivery
replay, grouped by the original saved scene epoch. Individual product execution
details and replay remain selectable. This presentation grouping does not merge
business orders, commands, journals or verification outcomes.

GET /deliveries indexes jobs with a saved PresentationSnapshot or original command
identity. GET /deliveries/{delivery_id}/playback returns their original JobPlayback
records in durable PLANNING-event sequence, independently of order-intake time.
Older attempts with no recorded scene identity remain individual-only. Empty
current scenes are selectable; reset archives the previous delivery by retaining
its existing evidence. A concurrent reset cannot relabel an empty current scene.

The viewer concatenates original event/motion segments without interpolating
between jobs. Every segment uses its own saved starting geometry and frame
overrides, so products already delivered stay where their recording places them.
The scrubber, playback speed and Replay span all included products. Paused
cursors retain their product if earlier audit evidence grows. Partial clips stop
at the last recorded pose, and missing clips keep their explicit provenance.
The completion badge counts persisted job states; replay never declares success.

The initial implementation prepared a fresh delivery on scenario selection.
ADR 0007 supersedes that behavior: selection changes configuration only, and a
permanent Start new test control creates independent worlds for all combinations.
Explicit fixture preparation retains its ADR 0005 guards. If all products have been picked, the main action explicitly
becomes Start new delivery and run order. This prepares fixtures before creating
a new order. Active and uncertain work still blocks preparation and dispatch.
No physical command is retried or issued by scenario selection or replay.

The cell quarantine also applies when the user selects a different product.
The dashboard makes this explicit beside Run and provides an action targeting
the unresolved job independently of the viewed execution. It honors the chosen
observation fault and issues reconciliation only. Inconclusive evidence leaves
the guard intact and offers inspection instead of another reconcile or pick.

Regression tests cover reverse intake versus execution order, three real Blender
clips and cumulative poses, restart/reset retention, partial playback, unchanged
uncertainty, and the actual dashboard script's scenario and delivery controls.
