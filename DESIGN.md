# Client design

Canonical product facts live in [PRODUCT.md](PRODUCT.md). This document owns client
interaction and visual conventions; rebuild evidence lives under docs/client-rebuild.

## Direction: a task workspace

Impeccable Operate mode: familiar controls, restrained color, deliberate information
hierarchy. Preserve the existing identity; rebuild the organization around the task.
Use two workspaces: **Run & watch** for setup/execution/recorded motion and **Inspect
evidence** for the saved trace and technical investigation. A shared run context and
backend-authorized next action remain visible without a large sticky overlay.

Primary sequence: choose product/scenario → start guided run → approve each boundary
→ notice outcome or uncertainty → inspect its saved evidence → take the supported next
action. Detail must not imply that a historical failure remains an active failure.

## Layers

1. Current status, unusual recorded attempts, next action.
2. Selected stage explanation, robot context, evidence boundary.
3. Protocol fields, current database rows, source, exact records, IDs and JSON exports.

The component selector belongs to Full Python file. Keep only that mode and Saved
excerpt; preserve related-symbol highlighting. No separate source browser button.

## Tokens and components

Keep neutral dark backgrounds, teal for the primary action/selection, amber for
uncertainty/physical authorization, and explicit text alongside status color.
Use system sans for the interface, monospace only for code and exact values. A 16px
base, 14px secondary copy, rem sizing, consistent spacing and 44px principal controls
support legibility and touch. Avoid nested decorative cards and repeated status copy.

Navigation uses links; actions use buttons; disclosures use native details; protected
confirmation uses native dialog. Tabs require roving focus and associated panels.
No visual-only custom select controls. Preserve the invoking control's focus after a
dialog. Dynamic replacement must not drop focus or reset an investigation.

## Responsive and state requirements

For the measured cell, keep the next calibration action beside the robot view, with
camera-specific state and actual image previews. Detailed equations, source, HTTP
records and raw arrays belong in Inspect evidence. Use the same two source modes;
highlight related functions without claiming an executed-line trace. Swedish presenter
explanations are optional disclosures. The client renders backend decisions and never
solves calibration or decides approval. A known mount change blocks affected targets;
routine checks and new candidates cannot silently restore approval.

At narrow widths, stack setup and robot; stack trace and inspector. Allow code/table
scrolling within labelled regions. Never hide essential evidence to fit the viewport.
No sticky element may cover a focused control. Respect reduced motion; replay has
pause and frame controls and a text phase alternative.

Keep form choices on recoverable errors. Disable duplicate submission while pending.
Loading/saved/stale/disconnected/current-reference states must be truthful. URL state
should restore test, session, selected step and view without issuing execution requests.

## Guidance choices

Impeccable distill/operate/harden informed hierarchy, common controls and edge cases.
Vercel review informs semantic navigation, focus, URL state and visible feedback.
UI/UX Pro Max's focus-not-obscured result supports removing large sticky status blocks.
Its generated marketing layout did not fit this operating tool and was rejected;
no imported fonts, framework or competing generated design system is used.
