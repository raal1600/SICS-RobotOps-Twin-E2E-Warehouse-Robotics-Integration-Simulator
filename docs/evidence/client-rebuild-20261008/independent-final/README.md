# Independent final heuristic review

Agent-based review, not human user research. Reviewed the real application at http://127.0.0.1:8000/ on 2026-10-08 using saved integration-lab runs. No implementation source was used to choose navigation actions. No code or application data was changed.

## Outcome

No critical or high-severity task-completion/accessibility defect was confirmed in this read-only scope. The requested final fixes passed direct browser checks:

- Full Python file keeps its BUTTON focus immediately after Enter and after the source response; it remains operable during loading.
- The component selector is named by its visible Choose component code label.
- Full source mode and selected Virtual PLC component survive refresh through the URL. The same run and historical stage remain selected.
- The trace has one Tab stop. ArrowDown, ArrowUp, Home and End change the selected evidence and retain focus on the intended row.
- The historical WMS failure explains that a later attempt completed step 20 and no retry is needed. Original boundary guidance remains separately labeled.
- Lost-ack reconciliation explains that it queried the original command without a replacement command and changed UNKNOWN_OUTCOME to COMPLETED. Controller result, observation and verification remain distinct.
- Tested Tab/Shift+Tab movement remains inside the native investigation dialog; Escape returns to the actual opening control.
- Desktop, laptop and narrow Run & watch / Inspect evidence views remain usable. Narrow run, investigation and Python-source views have zero horizontal page overflow.
- Main next-pick hints now refer to choosing a product/scenario in the integration lab, rather than an unavailable Start new test above action.

## Evidence

| View | Screenshot |
|---|---|
| Desktop 1440x1000 Run & watch, settled | 01-desktop-run.png |
| Desktop Inspect evidence | 02-desktop-inspect.png |
| Desktop full PLC source | 03-desktop-plc-source.png |
| Laptop 1366x768 Run & watch | 04-laptop-run.png |
| Laptop uncertainty reconciliation | 05-laptop-inspect-reconciliation.png |
| Narrow 390x844 Inspect evidence | 06-narrow-inspect.png |
| Narrow Run & watch | 07-narrow-run.png |
| Narrow full PLC source and highlight | 08-narrow-source.png |
| Laptop historical WMS recovery | 09-laptop-historical-recovery.png |

review-results.json contains structured observed outcomes. request-log.json preserves 1554 HTTP/resource request records, failed-request events and attempted-write guard results. All recorded requests use GET; zero attempted mutations, zero failed requests and zero page errors were recorded. No request headers, response bodies or browser profile were saved.

## Minor remaining observations

The residual top test-history hint was corrected after the first final pass. A fresh reload confirmed the current integration lab and that results remain in its saved history. See 10-final-lab-history-wording.png and final-wording-confirmation.json. The baseline distinction between stage number and attempt position can still look confusing for repeated/reconciliation rows; the row title, selected state, attempt label and detailed explanation make the inspected outcome clear.

## Limits

This is independent agent heuristic evidence, not human research. No real screen-reader session, axe scan, zoom/text-enlargement check, new-run execution, fault injection or backend persistence assertion was performed by this reviewer. The root rebuild task owns those applicable checks. No full WCAG conformance or complete product validation claim is made. Saved motion was allowed to load before settled screenshots; the source URLs refer to current implementation, as the interface itself states.
