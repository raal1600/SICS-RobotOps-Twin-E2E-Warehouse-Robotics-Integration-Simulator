# Fresh 9e83fe7 manual proof: execution sequence only

Preparation, not a result. Source 9e83fe7d41a52a63ba65b77730e392dafca8fffe. After root reviews exit0/all20 local gates/both terminal JUnits for acceptance/20261006T024719, use artifacts/run-manual-lab-9e83fe7.ps1 and the hidden-launch instructions below. No overlap with acceptance.

Bind actual API/UI URL and directory from artifacts/lab-final-9e83fe7.json. All <...> fields below must be replaced with NEW runtime IDs; save under artifacts/final-manual-9e83fe7. Preserve report/source/helper hashes. No /run, TTL overrides, physical retries or evidence overwrites.

## Guarded launch and owned stop evidence

The actual manifest observed during preparation is `docs/evidence/acceptance/20261006T024719/manifest.json`: clean commit `9e83fe7d41a52a63ba65b77730e392dafca8fffe`, fingerprint `136641a25c5fbd7d45c016582ec2c5c5197362f44f0a894ee95a69c652e3eafd`. Terminal record must be `artifacts/acceptance-response-sync-exit.json`. Preparation does not attest any currently running gate. Root must review the complete terminal local PASS before invoking the launcher; no overlap with acceptance.

The launcher requires explicit `-RunManual`, exact campaign start `2026-10-06T02:47:20.134216+00:00`, exact HEAD, unchanged tracked source except generated `ACCEPTANCE_REPORT.md`, matching current fingerprint, matching clean manifest/source/timestamps and terminal exit0, all20 local gates, both actual JUnits with no failure/error/skip and the same nonempty unique testcase identities, and both coverage results >=85 percent. It refuses existing lab report/data/exit and final-manual evidence. The launch snippet must also refuse reused owner/stdout/stderr paths before Start-Process creates them. Remote CI/Pages are separate pending requirements.

The shared `robotops.http_server:new_event_loop` is selected by the current `tools.lab_stack` for API/WMS and by the edge entry point. No extra manual override is needed. On Windows it uses the documented small-lab selector loop (512 sockets; no asyncio subprocesses/pipes); separate PLC/OPC UA and Playwright loops remain unchanged. Blender is the actual runtime here.

Before launch, verify these NEW paths are unused: `artifacts/lab-final-9e83fe7.json`, `artifacts/lab-final-9e83fe7/`, `artifacts/lab-final-9e83fe7-exit.json`, `artifacts/lab-final-9e83fe7-owner.json`, both stdout/stderr logs below, and `artifacts/final-manual-9e83fe7/`. Do not delete/recycle existing evidence. The snippet below is preparation only, not an execution record:

```powershell
foreach ($taskManualUnused in @('artifacts/lab-final-9e83fe7.json','artifacts/lab-final-9e83fe7','artifacts/lab-final-9e83fe7-exit.json','artifacts/lab-final-9e83fe7-owner.json','artifacts/lab-final-9e83fe7.stdout.log','artifacts/lab-final-9e83fe7.stderr.log','artifacts/final-manual-9e83fe7')) {
    if (Test-Path -LiteralPath $taskManualUnused) { throw ('Existing evidence: ' + $taskManualUnused) }
}
$taskManualLaunch = Start-Process -FilePath powershell.exe -WindowStyle Hidden -PassThru -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File','C:\Users\ramis\source\repos\robotops-twin\artifacts\run-manual-lab-9e83fe7.ps1','-RunManual') -RedirectStandardOutput 'C:\Users\ramis\source\repos\robotops-twin\artifacts\lab-final-9e83fe7.stdout.log' -RedirectStandardError 'C:\Users\ramis\source\repos\robotops-twin\artifacts\lab-final-9e83fe7.stderr.log'
[pscustomobject]@{ pid=$taskManualLaunch.Id; started_at_utc=$taskManualLaunch.StartTime.ToUniversalTime().ToString('o'); launcher='artifacts/run-manual-lab-9e83fe7.ps1'; source='9e83fe7d41a52a63ba65b77730e392dafca8fffe' } | ConvertTo-Json | Set-Content -LiteralPath 'artifacts/lab-final-9e83fe7-owner.json' -Encoding UTF8
```

Wait for the newly generated report and inspect its actual runtime/service addresses and process IDs before opening a browser or issuing workflow commands. Save manual evidence only under `artifacts/final-manual-9e83fe7/`; use browser session `robotops-lab-9e83fe7`.

At the end, close that named browser, inspect current creation time/command line and parentage against the owner record and the report's exact launcher/service PIDs, then stop only this owned lab process tree. Keep PostgreSQL/RabbitMQ dependency services outside that stop scope. There is no stop-file protocol in `tools.lab_stack`; do not invent a stop request or assume a file stops processes. Record actual before/after PID/identity/alive facts in the unique stop receipt `artifacts/final-manual-9e83fe7/stopped-processes.json`. A forced stop may prevent the launcher from writing its terminal exit file; record that distinction instead of inventing exit0. Never use an old report's PIDs.

The shared caption/inspector/driver/duplicate-auth helper JavaScript is reused byte-for-byte. `manual-caption-capture-usage.md` is historical b968 preparation: reuse its helper API details only; this runbook is authoritative for current source, campaign, session and paths. No source-specific helper copy is needed because this correction changes only test response/body synchronization and ADR documentation; product UI selectors and helper contracts remain unchanged.

## Common here-string patterns

Choose the browser session and install before original stage1; reinstall after reload:

    $taskBrowser = 'robotops-lab-9e83fe7'
    $taskEvidence = 'artifacts/final-manual-9e83fe7'
    Get-Content -LiteralPath artifacts/manual-browser-driver.js -Raw | npx --yes agent-browser --session $taskBrowser eval --stdin
    Get-Content -LiteralPath artifacts/manual-inspector-capture.js -Raw | npx --yes agent-browser --session $taskBrowser eval --stdin
    Get-Content -LiteralPath artifacts/manual-caption-capture.js -Raw | npx --yes agent-browser --session $taskBrowser eval --stdin

Replace targetStage and SID according to the sequence. Start returns immediately; observe separately until phase.running:false and review stopReason. Never start twice or reload/switch session while in flight. An observation timeout is not a failed physical action.

    @'
    manualProof.start({targetStage:10,sessionId:"<ACTUAL_SID>",reconcile:false})
    '@ | npx --yes agent-browser --session $taskBrowser eval --stdin
    @'
    manualProof.progress()
    '@ | npx --yes agent-browser --session $taskBrowser eval --stdin

Checkpoint bundle = full raw UTF-8 session GET from actual report API + /integration/sessions/<SID>; browser export; six-tab inspector; selected journals; screenshot. Preserve actual IDs and full JSON, not a truncated serialization:

    @'
    ({evidence:manualProof.export(),live:manualProof.progress(),inspector:manualInspect.lastCapture,pose:manualInspect.pose(),motion:manualInspect.lastMotion})
    '@ | npx --yes agent-browser --session $taskBrowser eval --stdin > "$taskEvidence/<CHECKPOINT>-browser.json"

    & .\.venv\Scripts\python.exe artifacts/final-evidence-pack/f00ad15/capture_manual_journals.py --report artifacts/lab-final-9e83fe7.json --session-file "$taskEvidence/<CHECKPOINT>-session.json" --expected-session-id '<ACTUAL_SID>' --expected-command-id '<ACTUAL_CMD>' --output "$taskEvidence/<CHECKPOINT>-journals.json"

Eval expressions return objects directly. agent-browser stdout may still wrap the result in a CLI envelope; inspect/decode that envelope and save the actual JSON object separately, retaining raw stdout. Do not label a quoted JSON string as a raw object. Top-level await is unsupported here; awaited examples use async IIFEs.

The journal helper is unchanged and closes read-only connections. Check exit0; compare selected_command/effect counts, not global totals. For six tabs, change stage16 to the checkpoint's actual persisted stage:

    @'
    manualInspect.capture({sessionId:"<ACTUAL_SID>",stepId:integration.session.steps.find(s=>s.stage===16).step_id})
    '@ | npx --yes agent-browser --session $taskBrowser eval --stdin

## Happy, then lost ACK, then duplicate delivery

Use real UI scenario/product/new-order controls. Bind SID/correlation/order/job/command as assigned, then preserve them. Unexpected error, identity change, stale gate or ambiguous physical outcome stops further actions.

| Order | Action; wait separately | Capture/expected evidence to assess |
|---|---|---|
| Happy1 | Happy path/new order; target10, reconcile:false | happy-reload-before: full API/browser; stage10/rev18, gated. |
| Happy2 | Idle reload same tab; reinstall helpers; restore original history selection if needed | happy-reload-after: entire API, IDs/revision/stage/consent unchanged. No automatic resume. |
| Happy3 | target15, reconcile:false | happy-gate bundle, stage14 six tabs:15/rev28, explicit consent, static scene/disabled playback, effect0. Capture promptly within normal freshness rules. |
| Happy4 | target17, reconcile:false | happy-postmotion bundle, stage16 six tabs:17/rev32, original IDs, matching runtime/PLC receipt, effect1. Stage15 real UI handler sends physical16 once. |
| Happy5 | target22, reconcile:false | happy-completed bundle, stage22 six tabs:22 stages, COMPLETED/rev44, verified success, actual WMS200/ERP complete, pending card hidden, effect1. |
| Happy6 | Caption/dropdown proof below, then exact saved stage1 replay below | Same completed original session; API/job/journal before/after comparison. |
| Lost1 | DROP_ACK_AFTER_EFFECT/new order; target15, reconcile:false | lost-gate bundle/effect0. |
| Lost2 | target22, reconcile:false; stop NEEDS_RECONCILIATION | lost-unknown bundle BEFORE recovery: UNKNOWN_OUTCOME stage20/rev38, original runtime receipt/effect1, one physical POST; retain actual PLC status/sequence. |
| Lost3 | After reviewing UNKNOWN evidence, target22 with reconcile:true ONCE | lost-completed bundle/captions:22 COMPLETED/rev46,23 records, same IDs, one reconcile, physical_resend:false, unchanged runtime/effect1, WMS200/ERP complete. Explain actual PLC newly retained result/sequence; do not assert all PLC rows unchanged. |
| Duplicate1 | DUPLICATE_DELIVERY/new order; target15, reconcile:false | duplicate-gate bundle, stage11 six tabs/effect0: deliveries1 to2 with same command/hash. duplicate_publish with actual redelivered:false flags is not broker redelivery. Hidden stale DOM is not visible proof. |
| Duplicate2 | target22, reconcile:false | duplicate-completed bundle, stage22 six tabs/captions:22 COMPLETED/rev44, one physical POST/effect1, original receipt, WMS200/ERP complete. |

At Happy4 observe actual authorized recording, with API before/after inspector/replay actions:

    @'
    (async()=>{return await manualInspect.samplePose({sessionId:"<HAPPY_SID>",durationMs:1500,intervalMs:100});})()
    '@ | npx --yes agent-browser --session $taskBrowser eval --stdin

Record actual frames/poses and evaluated/rendered movement, never historical counts. If replay is paused/ended, explicitly use normal read-only replay/scrub controls to select recorded motion and sample again; never repeat physical work. Check six tabs, expandable payload, unchanged durable API and truthful protocol/simulated robot/read-only replay labels.

Lost3 must be explicit, once; unresolved recovery stops:

    @'
    manualProof.start({targetStage:22,sessionId:"<LOST_SID>",reconcile:true})
    '@ | npx --yes agent-browser --session $taskBrowser eval --stdin

## Happy duplicate authorization

Install artifacts/manual-duplicate-auth-helper.js with the common Get-Content | eval --stdin pattern. Use separate here-string calls for manualDuplicateAuth.candidates("<HAPPY_SID>") and (async()=>{return await manualDuplicateAuth.prepare({sessionId:"<HAPPY_SID>",requestId:"<ACTUAL_SAVED_STAGE1_REQUEST_ID>"});})(). Review GET-only preparation; save happy-duplicate-auth-before API/journals. Then once:

    @'
    (async()=>{return await manualDuplicateAuth.replayOnce({confirm:"REPLAY_SAVED_STAGE_1"});})()
    '@ | npx --yes agent-browser --session $taskBrowser eval --stdin
    @'
    manualDuplicateAuth.export()
    '@ | npx --yes agent-browser --session $taskBrowser eval --stdin > "$taskEvidence/happy-duplicate-auth.json"

Save after API/journals/browser. Assess200, exact original stage1 body/request ID, unchanged complete API/job and selected journals/effect1. No retry. Filter driver POSTs by actual SID: exactly one physical16 before intentional stage1 replay; zero /run.

## Corrected captions and actual dropdown independence

At idle completion capture saved per-job scenario versus original session. For happy use null unquoted; for fault cases use actual original string:

    @'
    manualCaption.start({sessionId:"<ACTUAL_SID>",expectedFaults:{"<ACTUAL_SID>":"<ORIGINAL_FAULT>"}})
    '@ | npx --yes agent-browser --session $taskBrowser eval --stdin
    @'
    manualCaption.progress()
    '@ | npx --yes agent-browser --session $taskBrowser eval --stdin

Wait running:false/no error; retain <FIRST_CAPTURE_ID>; screenshot actual brief/caption. Change the real future-order dropdown while retaining original session/replay:

    npx --yes agent-browser --session $taskBrowser select '#scenario' 'BRAIN_TIMEOUT'
    @'
    manualCaption.start({sessionId:"<ACTUAL_SID>",compareTo:"<FIRST_CAPTURE_ID>",expectedDropdown:"BRAIN_TIMEOUT"})
    '@ | npx --yes agent-browser --session $taskBrowser eval --stdin

Wait progress(), then export and screenshot changed dropdown plus unchanged caption:

    @'
    manualCaption.export()
    '@ | npx --yes agent-browser --session $taskBrowser eval --stdin > "$taskEvidence/<CASE>-captions.json"

Assess original clip/job/command ownership, saved scenario, unchanged full original-session hashes/caption, actual dropdown change and zero POSTs. Restore next intended scenario via real UI before the next order. Root may select actual delivery/replay controls to capture mixed clips and original labels; differing scenarios require mixed caption. Missing/unknown is unassessed unless actual saved evidence exists; never fabricate metadata. Root chooses any WMS case: actual503 then explicit business recovery200, effect1 and correct caption, no physical resend.

## Both exact README CLI commands: once each, sequentially

After browser work settles, require same healthy lab/source and report API matching CLI default http://127.0.0.1:8000; otherwise resolve setup before calling these exact commands. Do not silently add --url. Run happy, capture/review it, then lost:

    uv run --locked python -m tools.integration_demo --scenario happy_path --authorize-robot
    uv run --locked python -m tools.integration_demo --scenario lost_ack_after_effect --authorize-robot

Capture stdout/stderr in cli-happy-* and cli-lost-* logs; persist $LASTEXITCODE immediately with command/start/end/source in cli-*-exit.json before another native command. Stop on nonzero; no rerun. Stdout JSON supplies the actual runs/integration-demos/<NEW_SID>.json path: copy raw bytes to cli-*-result.json, derive actual IDs and capture journals using that result as --session-file. Assess22 COMPLETED/rev44 or46, original IDs/effect1, lost uncertainty and one same-command reconciliation. Do not claim browser POST counts for CLI without a corresponding trace.

Finally derive all8 mini-map groups/current-stage alignment from saved maps/phase initial/final/action before/after: ERP / WMS1-2; REST / SQL3-4; Observe / plan5-8; Outbox / edge9-11; OPC UA / PLC12-15; Robot16-17; Verify18-19; Business20-22. Stage17 covers Robot when16 is transient. Read-only inspector selection must leave workflow map/API unchanged. Preserve hashes/screenshots/console errors and discrepancies. No manual, full-acceptance or remote PASS is asserted here.
