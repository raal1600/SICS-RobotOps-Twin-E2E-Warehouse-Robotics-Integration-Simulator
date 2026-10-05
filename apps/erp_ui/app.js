"use strict";
const byId = id => document.getElementById(id);
const player = new MotionPlayer();
let selectedJob = null, selectedDelivery = null, fixture = null, deliveries = [], busy = false, refreshing = false, pollingMotion = false;
let orderSignature = "", productSignature = "", deliverySignature = "", nextMotionPoll = 0, cellMode = "READY", refreshVersion = 0;
let selectedTest = "original", activeTest = "original", testHistory = [], historySignature = "", viewVersion = 0;
let selectedRevision = 1;
let managingTests = false;
let guideEvidence = null, guideJob = null, guidance = null;
let cellProfiles = [], newTestRequest = null, deletionRequest = null, historyVersion = 0;
let selectedEvidence = null, selectedEvents = [], knownOrders = [], inspection = null, inspectionVersion = 0, timelineSignature = "";
const inspectionPanes = ["findings", "evidence", "manual"];
function showInspectionPane(name) {
  for(const pane of inspectionPanes){
    byId(`pane-${pane}`).hidden=pane!==name;
    byId(`tab-${pane}`).setAttribute("aria-selected",String(pane===name));
    byId(`tab-${pane}`).setAttribute("tabindex",pane===name?"0":"-1");
  }
}
function renderInspectionTimeline(model) {
  const important = event => event.state_after || /FAULT|TIMEOUT|RECONCIL|VERIF|COMMAND|EFFECT|REJECT|ERROR/.test(event.event_type);
  const events=byId("timeline-filter").value==="all"?model.related:model.related.filter(important);
  text("timeline-summary",`Event timeline · ${events.length} of ${model.related.length} relevant events`);
  const signature=JSON.stringify([inspection?.evidence.job.job_id,byId("timeline-filter").value,events]);
  if(signature===timelineSignature)return;
  timelineSignature=signature;byId("timeline").replaceChildren();
  for(const event of events){
    const row=document.createElement("tr");
    for(const value of [event.timestamp.slice(11,23)+" / "+event.component,event.event_type+(event.state_after?" → "+event.state_after:""),event.reason]){
      const cell=document.createElement("td");
      if(value===event.reason){const button=document.createElement("button");button.className="text-button";button.textContent=value||"Inspect event";
        button.onclick=()=>{text("event-record",JSON.stringify(event,null,2));byId("event-details").open=true;};cell.append(button);
      }else cell.textContent=value;
      row.append(cell);
    }
    byId("timeline").append(row);
  }
}
function renderInspection() {
  if(!inspection||inspection.testId!==selectedTest)return;
  const evidence=inspection.evidence,model=SimulationGuide.inspect(evidence,inspection.events),job=evidence.job;
  const test=testHistory.find(item=>item.test_id===inspection.testId);
  const sku=fixture?.products.find(item=>item.product_id===(job.line?.product_id||evidence.command?.product_id))?.sku||job.line?.product_id||"Product";
  const plainState={UNKNOWN_OUTCOME:"Result uncertain",REQUIRES_INTERVENTION:"More evidence needed",COMPLETED:"Pick confirmed",FAILED:"Pick not completed",EXECUTING:"Pick running",VERIFYING:"Checking the result",RECONCILING:"Checking again"}[job.state]||job.state;
  text("investigation-title",`${sku} · ${plainState}`);
  text("inspection-context",`Test ${test?.number??inspection.testId} · ${job.state} · Job ${job.job_id}`);
  text("review-identity",`Order ${job.order_id||"not included"} · Job ${job.job_id} · original command ${evidence.command?.command_id||"not created"}`);
  text("review-label",readOnly()?"Saved test · read-only":"Recorded result for this pick");
  for(const [id,value] of Object.entries({"inspection-symptom":model.symptom,"inspection-finding":model.finding,"inspection-limit":model.limit,"inspection-hypothesis":model.hypothesis,"inspection-next":model.next,"inspection-observation":model.observation,"review-journal":model.summary.journal,"review-observation":model.summary.observation,"review-decision":model.summary.decision,"review-attempts":model.summary.attempts}))text(id,value);
  text("journal-record",JSON.stringify({command:evidence.command,journal:evidence.journal},null,2));
  text("observation-record",model.assessed?JSON.stringify(model.assessed,null,2):"No assessed observation available.");
  text("decision-record",JSON.stringify({verifications:evidence.verifications,reconciliations:evidence.reconciliations},null,2));
  text("evidence",JSON.stringify(evidence,null,2));
  const canCheck=!readOnly()&&["UNKNOWN_OUTCOME","REQUIRES_INTERVENTION"].includes(job.state);
  byId("observation-controls").hidden=!canCheck;
  byId("next-step").hidden=!canCheck;
  byId("view-evidence").disabled=false;
  roboticsEvidence(evidence);
  text("order-state",knownOrders.find(order=>order.order_id===job.order_id)?.status||"Not loaded");
  text("job-state",job.state);
  text("verdict",model.latest?`${model.latest.verdict} · ${model.latest.reason}`:"No verification result yet.");
  text("command",evidence.command?`Original command: ${evidence.command.command_id} · Journal: ${evidence.journal?.status||"unavailable"}`:"No robot command dispatched.");
  const origin=globalThis.location?.origin||"http://127.0.0.1:<port>";
  const path=(inspection.testId==="original"?"":`/simulation-tests/${encodeURIComponent(inspection.testId)}`);
  const urls=[`${origin}${path}/jobs/${encodeURIComponent(job.job_id)}/evidence`,`${origin}${path}/orders/${encodeURIComponent(job.order_id||"")}/timeline`];
  text("manual-identity",`Test ${test?.number??inspection.testId} · ${job.job_id} · command ${evidence.command?.command_id||"none"}`);
  text("manual-requests",urls.map(url=>`Invoke-RestMethod '${url.replaceAll("'","%27")}' | ConvertTo-Json -Depth 100`).join("\n\n"));
  text("manual-reproduce",`Use a new ${test?.cell_display_name||"matching cell"} test and product ${sku}. `+(model.initialFault?`The execution log records an injected ${model.initialFault} fault (${SimulationGuide.explain("scenario",model.initialFault).label}). Select that scenario and run the order.`:"No injected execution fault is recorded before the first outcome. Use the event log to establish the original setup; the current dropdown is not historical evidence."));
  text("manual-storage",inspection.testId==="original"?"This is the original test: its world files are directly under the configured data root.":`This test's world is under simulation-tests/${inspection.testId} inside the configured data root.`);
  byId("manual-sources").replaceChildren();
  for(const [path,reason] of model.sources){const item=document.createElement("li"),code=document.createElement("code"),detail=document.createElement("span");code.textContent=path;detail.textContent=` — ${reason}`;item.append(code,detail);byId("manual-sources").append(item);}
  byId("download-evidence").disabled=inspection.loading;
  renderInspectionTimeline(model);
}
async function openInspection(evidence, events=null) {
  if(!evidence||!selectedTest)return;
  const version=++inspectionVersion,testId=selectedTest,job=evidence.job;
  const same=inspection?.testId===testId&&inspection?.evidence.job.job_id===job.job_id;
  inspection={testId,evidence,events:events||[],loading:events===null};timelineSignature="";
  if(!same){showInspectionPane("findings");byId("timeline-panel").open=false;byId("evidence-details").open=false;byId("event-details").open=false;text("event-record","Select an event above.");}
  player.pause();
  byId("review-panel").open=true;text("inspection-error","");
  if(!byId("investigation-dialog").open)byId("investigation-dialog").showModal();
  renderInspection();
  const pane=inspectionPanes.find(name=>!byId(`pane-${name}`).hidden)||"findings";
  byId(pane==="findings"?"review-heading":`tab-${pane}`).focus({preventScroll:true});
  if(events===null){
    try{const loaded=await api(`/orders/${job.order_id}/timeline`);if(version!==inspectionVersion||testId!==selectedTest)return;inspection.events=loaded;inspection.loading=false;renderInspection();}
    catch(error){if(version===inspectionVersion){text("inspection-error","Event records could not be loaded: "+error.message);inspection.loading=true;}}
  }
}
const clearingTest = () => !!testHistory.find(item=>item.test_id===selectedTest)?.clearing;
const readOnly = () => !selectedTest || selectedTest !== activeTest || clearingTest();
const testPath = path => (selectedTest === "original" ? "" : `/simulation-tests/${selectedTest}`) + path;
const sourceFor = product => fixture?.product_sources?.[product] || fixture?.source_id;
const atSource = item => (item.location_id??item.location) === sourceFor(item.product_id);
function testControls() {
  const current=testHistory.find(item=>item.test_id===selectedTest);
  byId("test-history").value=selectedTest||"";
  byId("new-test").disabled=busy;
  byId("empty-new-test").disabled=busy;
  byId("test-history").disabled=busy||!testHistory.length;
  byId("delete-test").disabled=busy||!current;
  byId("clear-test").disabled=busy||!current;
  byId("clear-tests").disabled=busy||!testHistory.length;
  byId("return-current").hidden=!activeTest||selectedTest===activeTest;byId("return-current").disabled=busy;
  byId("empty-workspace").hidden=!!selectedTest;
  byId("test-workspace").hidden=!selectedTest||clearingTest();
  byId("test-workflow-steps").hidden=!selectedTest||clearingTest();
  text("test-status",!current
    ? (testHistory.length?"No test selected. Saved tests are available for review, or create a new test.":"No test data. Start a new test and choose a robot cell.")
    : `Test ${current.number} · ${current.cell_display_name} · `+(current.clearing
      ? "Clear is unfinished. Retry the confirmed clear, or reopen the app to finish restoring this test."
      : readOnly()
      ? "saved history, read-only. Return to the current test or start a new one."
      : "current test. Start new test creates a separate world; previous results stay in history."));
  if(selectedTest)byId("metrics-link").href=testPath("/metrics");
}
async function refreshHistory() {
  const version=++historyVersion;
  const data=await request("/simulation-tests");
  if(version!==historyVersion)return;
  activeTest=data.active_test_id;testHistory=data.tests;
  const signature=JSON.stringify(data);
  if(signature!==historySignature){
    byId("test-history").replaceChildren();
    byId("test-history").add(new Option("Select a test", ""));
    data.tests.slice().reverse().forEach(item=>byId("test-history").add(new Option(
      `Test ${item.number} · ${item.cell_display_name} · ${item.active?"Current":"Saved"} · ${item.order_count} orders · ${[...new Set(item.outcomes)].join(", ")||"Ready"}`,item.test_id)));
    historySignature=signature;
  }
  if(selectedTest&&!testHistory.some(item=>item.test_id===selectedTest))await selectTest(null);
  const current=testHistory.find(item=>item.test_id===selectedTest);
  if(current&&(current.revision??1)!==selectedRevision)await selectTest(selectedTest);
  byId("test-history").value=selectedTest||"";testControls();
}
async function selectTest(identity) {
  ++viewVersion;++refreshVersion;refreshing=false;
  ++inspectionVersion;inspection=null;selectedEvidence=null;selectedEvents=[];knownOrders=[];
  byId("inspect-selected").disabled=true;text("selected-result","Loading the selected test…");
  if(byId("investigation-dialog").open)byId("investigation-dialog").close();
  selectedTest=identity||null;selectedJob=null;selectedDelivery=null;fixture=null;deliveries=[];
  selectedRevision=testHistory.find(item=>item.test_id===selectedTest)?.revision??1;
  guideEvidence=null;guideJob=null;
  byId("setup-panel").open=true;byId("review-panel").open=false;
  orderSignature=productSignature=deliverySignature="";nextMotionPoll=0;
  byId("orders").replaceChildren();byId("delivery").replaceChildren();
  byId("replay-scope").value="delivery";byId("visual-panel").hidden=true;byId("visual").removeAttribute("src");
  player.select(null);testControls();fixtureControls();
  await refresh();await refreshMotion(true);
}
function pendingExecution() {
  const executions=deliveries.flatMap(group=>group.executions);
  return executions.find(item=>item.state==="UNKNOWN_OUTCOME")||executions.find(item=>item.state==="REQUIRES_INTERVENTION");
}
function fixtureControls() {
  testControls();
  if (!fixture) {
    for(const id of ["create","tool-showcase","reconcile","resolve-blocker","fresh-scene","reset","motion-import"])byId(id).disabled=true;
    renderGuidance();return;
  }
  const products=fixture.products.map(item=>({...item,location:fixture.inventory.find(obj=>obj.product_id===item.product_id)?.location_id}));
  const anyAvailable=products.some(atSource);
  const signature=JSON.stringify(products);
  if(signature!==productSignature){
    const selected=byId("product").value;
    byId("product").replaceChildren();
    products.forEach(item=>{
      const available=atSource(item);
      const option=new Option(`${item.sku} · ${available?"at source":anyAvailable?"already picked":"new delivery"}`,item.product_id);
      option.disabled=!available&&anyAvailable;byId("product").add(option);
    });
    byId("product").value=products.find(item=>item.product_id===selected&&atSource(item))?.product_id
      || products.find(atSource)?.product_id || selected || products[0]?.product_id || "";
    productSignature=signature;
  }
  const available=products.some(item=>item.product_id===byId("product").value&&atSource(item));
  const blocker=fixture.scene_reset_blocked_reason;
  const pending=blocker?pendingExecution():null;
  const productName=fixture.products.find(item=>item.product_id===pending?.product_id)?.sku||pending?.product_id;
  const uncertain=pending?.state==="UNKNOWN_OUTCOME";
  byId("create").disabled=busy||readOnly()||(!available&&anyAvailable)||(cellMode!=="READY"&&anyAvailable)||!!blocker;
  byId("create").textContent=busy?"Operation in progress…":uncertain?"Next pick paused — reconcile first":pending?"Next pick paused — observe again":anyAvailable?"Create and run order":"Start new delivery and run order";
  byId("next-step").hidden=!pending;
  text("next-step-title",uncertain?`${productName}: outcome uncertain`:`${productName}: more evidence needed`);
  text("next-step-detail",uncertain
    ? "Choose an observation below, then reconcile this original command. No new pick is sent."
    : "The last assessment was inconclusive. Choose another observation below to continue this test.");
  text("resolve-blocker",uncertain?`Reconcile ${productName}`:`Observe again: ${productName}`);
  byId("resolve-blocker").disabled=busy||!pending||readOnly();
  byId("resolve-blocker").hidden=!pending;
  byId("reconcile").hidden=!!pending;
  byId("scenario").disabled=busy;byId("product").disabled=busy||readOnly();
  byId("observation").disabled=busy;
  byId("fresh-scene").disabled=busy||readOnly()||!!blocker;
  byId("tool-showcase").hidden=!fixture.catalogue;
  byId("tool-showcase").disabled=busy||readOnly()||!!blocker||cellMode!=="READY";
  byId("reset").disabled=busy||readOnly();byId("motion-import").disabled=busy||readOnly();
  text("inventory-status", blocker==="SCENE_RESET_IN_PROGRESS" ? "Preparing a fresh scene. Previous orders and recordings are being retained."
    : pending ? `Next pick blocked by ${productName} (${pending.state}). Open Investigate this pick to continue.`
    : blocker ? "An active job must finish before another pick can start."
    : readOnly() ? "Saved test: use the replay and evidence controls to review it."
    : !anyAvailable ? "Delivery finished. Start new test for another combination, or start another delivery in this test. The full delivery replay stays saved."
    : cellMode!=="READY" ? "The cell is stopped or faulted. Reset logical cell state before running another order."
    : "Choose a scenario and run products in this test. Start new test above for a fresh, independent combination.");
  renderGuidance();
}
function guideExecution() {
  if(readOnly())return deliveries.flatMap(group=>group.executions).find(item=>item.job_id===selectedJob);
  return pendingExecution()||deliveries.find(group=>group.current)?.executions.at(-1);
}
function focusPanel(id, focusId) {
  if(id==="review-panel"){
    openInspection(guideEvidence,guideJob===selectedJob?selectedEvents:null);return;
  }
  const panel=byId(id);panel.open=true;
  panel.scrollIntoView({block:"start",behavior:"auto"});
  byId(focusId).focus({preventScroll:true});
}
function renderGuidance() {
  const pending=pendingExecution(), execution=guideExecution();
  const product=fixture?.products.find(item=>item.product_id===pending?.product_id)?.sku||pending?.product_id;
  const evidence=guideJob===execution?.job_id?guideEvidence:null;
  guidance=SimulationGuide.describe({ready:!!fixture,busy,archived:readOnly(),pending,state:execution?.state,
    cellMode,blocked:fixture?.scene_reset_blocked_reason,available:fixture?.inventory.filter(atSource).length,product,evidence});
  text("guide-title",guidance.title);text("guide-detail",guidance.detail);text("guide-action",guidance.label);
  text("guide-label",guidance.tone==="attention"?"NEEDS YOUR ATTENTION":"NEXT STEP");
  byId("workflow-guide").setAttribute("data-tone",guidance.tone);
  byId("guide-action").disabled=guidance.action==="none";
  for(let stage=0;stage<4;stage++){
    if(stage===guidance.stage)byId(`stage-${stage}`).setAttribute("aria-current","step");
    else byId(`stage-${stage}`).removeAttribute("aria-current");
  }
  for(const kind of ["scenario","observation"]){
    const info=SimulationGuide.explain(kind,byId(kind).value);
    text(`${kind}-phase`,info.phase);text(`${kind}-meaning`,info.meaning);
    text(`${kind}-difference`,info.difference);text(`${kind}-help`,info.expected);
  }
  const brief=SimulationGuide.brief(byId("scenario").value);
  text("scenario-brief",brief[0]);text("scenario-watch",brief[1]);
  const summary=SimulationGuide.evidenceSummary(evidence);
  text("review-journal",summary.journal);text("review-observation",summary.observation);
  text("review-decision",summary.decision);text("review-attempts",summary.attempts);
  text("review-label",readOnly()?"Saved result · read-only":pending?"Your attention is needed":execution?"Latest result":"No pick yet");
  const reviewedProduct=fixture?.products.find(item=>item.product_id===execution?.product_id)?.sku||execution?.product_id;
  text("review-identity",execution?`${reviewedProduct} · ${execution.state} · Job ${execution.job_id}`:"Run a pick to collect evidence. You can choose an observation mode in advance.");
  byId("view-evidence").disabled=busy||!execution;
  byId("use-normal").hidden=!byId("observation").value;
  byId("use-normal").disabled=busy||readOnly();
  byId("review-panel").classList.toggle("review-attention",!!pending&&!readOnly());
  // The attention banner and cell result invite investigation. Keep the scene
  // visible until the operator opens the panel; polling never steals focus.
  if(inspection?.testId===selectedTest&&inspection.evidence.job.job_id===evidence?.job.job_id)inspection.evidence=evidence;
  renderInspection();
}
async function refreshGuide(selectedEvidence, version) {
  const execution=guideExecution();
  const evidence=execution?(execution.job_id===selectedJob?selectedEvidence:await api(`/jobs/${execution.job_id}/evidence`)):null;
  if(version!==refreshVersion)return;
  guideJob=execution?.job_id||null;guideEvidence=evidence;renderGuidance();
}
function selectReplay() {
  player.select(byId("replay-scope").value==="delivery"&&selectedDelivery?"delivery:"+selectedDelivery:selectedJob);
}
async function request(path, body, revision) {
  const options = body === undefined ? {cache:"no-store"} : {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)};
  if(body!==undefined&&revision!==undefined)options.headers["X-Test-Revision"]=String(revision);
  const response = await fetch(path, options), data = await response.json();
  if (!response.ok) {
    const explanations={
      TEST_OPERATION_IN_PROGRESS:"A test operation is still running. Wait for it to finish, then try again.",
      TEST_HISTORY_CHANGED:"The test list changed. Cancel and review Delete all tests again before deleting.",
      TEST_REVISION_CHANGED:"This test was cleared elsewhere. Cancel and review the restored test before trying again.",
      TEST_CLEAR_PENDING:"The clear could not finish. Retry the confirmed clear or reopen the app. No pick can run until the test is ready.",
      CELL_PROFILE_NOT_AVAILABLE:"This robot cell is no longer available. Cancel and choose an available cell.",
      CELL_PROFILE_STATE_MISMATCH:"Saved data for this request belongs to a different robot cell. Cancel and create a new test; the existing data was kept.",
      TEST_REQUEST_CONFLICT:"This request conflicts with an earlier operation. Cancel and review the test list before trying again.",
      TEST_DELETED:"This test was already deleted. Cancel and create a new test.",
      TEST_STORAGE_UNSAFE_PATH:"The test storage path cannot be safely deleted. Data was kept; inspect the server log."
    };
    throw new Error(explanations[data.reason]||data.reason||JSON.stringify(data.detail));
  }
  return data;
}
async function api(path, body) {
  if(!selectedTest)throw new Error("Create or select a simulation test first.");
  if(body!==undefined&&readOnly())throw new Error("Saved tests are read-only. Return to the current test or start a new one.");
  return request(testPath(path),body,selectedRevision);
}
function text(id, value) { if(byId(id).textContent!==value)byId(id).textContent = value; }
function appError(error){
  text("message","App request problem — "+error.message+". This message is separate from the recorded simulation outcome.");
  byId("message").setAttribute("data-kind","error");byId("message").setAttribute("role","alert");
}
function roboticsEvidence(evidence){
  const assessment=evidence?.verifications?.at(-1);
  const command=evidence?.command,observation=assessment?SimulationGuide.inspect(evidence).assessed:evidence?.observations?.at(-1),decision=command?.tool_selection;
  const product=fixture?.products.find(item=>item.product_id===(evidence?.job?.line?.product_id||command?.product_id));
  const observed=observation?.objects?.filter(item=>item.product_id===product?.product_id)||[];
  const tool=observation?.machine_telemetry?.tool_state.active_tool_id;
  const name=id=>fixture?.catalogue?.tools.find(item=>item.tool_id===id)?.display_name||id;
  text("status-product",product?`${product.sku} / ${product.product_id}`:"No order selected");
  text("status-tool",tool?name(tool):"Not observed yet");
  text("status-observation",observation?`${observed.length?Math.round(Math.min(...observed.map(item=>item.confidence))*100)+"% confidence":"No product evidence"} / ${assessment?.reason||"Unassessed capture; not a verified result"} / ${observation.model_version}`:assessment?"Assessed observation not available":"Not captured");
  text("status-calibration",observation?.calibration_version||"Not observed");
  text("business-identity",evidence?`Order ${evidence.job.order_id} / Job ${evidence.job.job_id}`:"");
  text("status-job",evidence?`${evidence.job.state} / ${evidence.job.job_id}`:"No job selected");
  text("status-command",command?.command_id||"Not dispatched");
  text("status-order",evidence?.job.order_id||"No order selected");
  const uncertain=["UNKNOWN_OUTCOME","REQUIRES_INTERVENTION"].includes(evidence?.job.state);
  text("knowledge-state",uncertain?`Execution result is uncertain — do not retry automatically. Controller: ${evidence.journal?.effect_count===1?"one transfer recorded":"no confirmed transfer"}. Workflow: ${evidence.job.state}.`:"");
  byId("knowledge-state").hidden=!uncertain;
  text("tool-decision",decision?`${name(decision.selected_tool_id)} selected. Assessed mass ${decision.assessed_mass_kg.toFixed(2)} kg. ${decision.tool_change_required?"Automatic tool change required.":"Mounted tool already matches."}`:command?"Historical recording: no tool-selection contract was recorded.":"Run a pick to inspect the persisted selection.");
  byId("tool-candidates").replaceChildren();
  for(const candidate of decision?.candidate_tools||[]){
    const row=document.createElement("tr");
    for(const value of [name(candidate.tool_id),candidate.eligible?`${candidate.score}${candidate.tool_id===decision.selected_tool_id?" / selected":" / lower ranked"}`:"Rejected",candidate.reasons.map(reason=>reason.replaceAll("_"," ").toLowerCase()).join(" · ")]){
      const cell=document.createElement("td");cell.textContent=value;row.append(cell);
    }
    byId("tool-candidates").append(row);
  }
}
async function refresh(preferred, preferredDelivery) {
  if(!selectedTest||clearingTest())return;
  if (refreshing && !preferred && !preferredDelivery) return;
  const version=++refreshVersion;
  refreshing = true;
  try {
    const [orders, cell, currentFixture, groups] = await Promise.all([api("/orders"), api("/cell"),api("/fixtures"),api("/deliveries")]);
    if(version!==refreshVersion)return;
    knownOrders=orders;
    deliveries=groups;
    fixture=currentFixture;cellMode=cell.mode;fixtureControls();
    text("cell-summary",`Cell: ${cell.mode}`);
    const wantedDelivery=preferredDelivery||byId("delivery").value||fixture.scene_epoch;
    selectedDelivery=groups.find(group=>group.delivery_id===wantedDelivery)?.delivery_id||fixture.scene_epoch;
    const group=groups.find(item=>item.delivery_id===selectedDelivery);
    const groupSignature=JSON.stringify(groups);
    if(groupSignature!==deliverySignature){
      nextMotionPoll=0;
      byId("delivery").replaceChildren();
      groups.slice().reverse().forEach((item,index)=>byId("delivery").add(new Option(
        `${item.current?"Current delivery":"Saved delivery"} · ${item.started_at.slice(0,16).replace("T"," ")} UTC · ${item.executions.length} executions · ${item.delivery_id.slice(0,8)}`,item.delivery_id)));
      deliverySignature=groupSignature;
    }
    byId("delivery").value=selectedDelivery;
    const selectedExecution=byId("orders").value;
    const keepExecution=byId("replay-scope").value==="product"||group?.executions.some(item=>item.job_id===selectedExecution)
      ||busy&&orders.some(order=>order.job_ids.includes(selectedExecution));
    const selection=preferred ?? (keepExecution?selectedExecution:group?.executions.at(-1)?.job_id||"");
    const signature = JSON.stringify([orders.map(order=>[order.order_id,order.status]),group?.executions]);
    if (signature !== orderSignature && (document.activeElement !== byId("orders") || preferred)) {
      byId("orders").replaceChildren();
      byId("orders").add(new Option("Current cell · create a new order", ""));
      orders.forEach(order=>order.job_ids.forEach((job,index)=>byId("orders").add(new Option(
        `${order.lines[index].product_id} · ${order.order_id} · ${groups.flatMap(item=>item.executions).find(item=>item.job_id===job)?.state||order.status}`,job))));
      orderSignature = signature;
    }
    if (!selection || orders.some(order => order.job_ids.includes(selection))) byId("orders").value = selection;
    text("cell-state",cell.mode);
    text("status-cell",cell.mode);
    const order = orders.find(item => item.job_ids.includes(byId("orders").value));
    if (!order) {
      const scene=await api("/cell/scene");if(version!==refreshVersion)return;
      selectedJob=null;selectReplay();player.previewScene(scene);
      selectedEvidence=null;selectedEvents=[];byId("inspect-selected").disabled=true;text("selected-result","No pick selected. Run an order or choose a saved execution.");
      byId("visual-panel").hidden=true;byId("reconcile").disabled=true;
      text("order-state","No order selected");text("job-state","Ready for a new order");
      text("verdict","Select a saved order to inspect its verification.");text("command","");
      text("evidence","No order selected.");roboticsEvidence(null);byId("timeline").replaceChildren();await refreshGuide(null,version);return;
    }
    if (selectedJob !== byId("orders").value) {
      byId("visual-panel").hidden=true;byId("visual").removeAttribute("src");
    }
    selectedJob = byId("orders").value; selectReplay();
    const job = selectedJob;
    const [evidence, events] = await Promise.all([api(`/jobs/${job}/evidence`),api(`/orders/${order.order_id}/timeline`)]);
    if (version!==refreshVersion || selectedJob !== job || byId("orders").value !== job) return;
    selectedEvidence=evidence;selectedEvents=events;byId("inspect-selected").disabled=false;
    text("selected-result",`${order.lines.find(line=>line.product_id===evidence.command?.product_id)?.product_id||evidence.job.line?.product_id||"Selected pick"} · ${evidence.job.state}`);
    byId("inspect-selected").setAttribute("data-attention",String(["UNKNOWN_OUTCOME","REQUIRES_INTERVENTION","FAILED"].includes(evidence.job.state)));
    if(inspection?.testId===selectedTest&&inspection.evidence.job.job_id===job){inspection.evidence=evidence;inspection.events=events;inspection.loading=false;}
    text("order-state",order.status);text("job-state",evidence.job.state);
    byId("reconcile").disabled=busy || readOnly() || !["UNKNOWN_OUTCOME","EXECUTING","VERIFYING","RECONCILING","REQUIRES_INTERVENTION"].includes(evidence.job.state);
    text("reconcile",evidence.job.state==="REQUIRES_INTERVENTION"?"Observe again and reconcile":"Reconcile selected job");
    const verdict=evidence.verifications.at(-1);
    text("verdict",verdict ? verdict.verdict+" · "+verdict.reason : "No verification result yet.");
    text("command",evidence.command ? "Original command: "+evidence.command.command_id+" · Journal: "+(evidence.journal?.status || "unavailable") : "No robot command dispatched.");
    text("evidence",JSON.stringify(evidence,null,2));
    roboticsEvidence(evidence);
    await refreshGuide(evidence,version);
    if(version!==refreshVersion)return;
    renderInspection();
    if(fixture.runtime === "blender" && evidence.command && evidence.journal?.status==="SUCCEEDED"
      &&["COMPLETED","UNKNOWN_OUTCOME","REQUIRES_INTERVENTION"].includes(evidence.job.state)) {
      const url=testPath(`/jobs/${job}/artifact.png`);
      if(byId("visual").getAttribute("src")!==url) byId("visual").src=url;
    }
  } finally {if(version===refreshVersion)refreshing=false;}
}
async function refreshMotion(force=false) {
  if(clearingTest())return;
  const full=byId("replay-scope").value==="delivery";
  if(!(full?selectedDelivery:selectedJob) || pollingMotion || !force && Date.now()<nextMotionPoll) return;
  pollingMotion=true;
  const version=viewVersion;
  try {
    const data=await api(full?`/deliveries/${selectedDelivery}/playback`:`/jobs/${selectedJob}/playback`);
    if(version!==viewVersion)return;
    if(full)player.updateDelivery(data);else player.update(data);
    const clips=full?data.jobs:[data];
    nextMotionPoll=clips.some(clip=>["RECORDING","WAITING"].includes(clip.status))?Date.now()+250:Infinity;
  }
  catch(error){if(version===viewVersion)text("motion-state","Recording feed unavailable · reconnecting");}
  finally {pollingMotion=false;}
}
async function action(fn, message="Running… live motion and status update below.", allowArchived=false) {
  if(busy)return;
  if(readOnly()&&!allowArchived){text("message","Saved tests are read-only. Return to the current test or start a new one.");return;}
  busy=true;fixtureControls();byId("reconcile").disabled=true;
  byId("message").removeAttribute("data-kind");byId("message").setAttribute("role","status");
  text("message",message);
  try {await fn();text("message","Updated from persisted evidence. Replay only changes the view.");}
  catch(error){appError(error);}
  finally {
    busy=false;
    try{await refreshHistory();await refresh();await refreshMotion(true);}catch(error){appError(error);}
    fixtureControls();
  }
}
async function freshDelivery(){
  const scene=await api("/fixtures/fresh-scene",{});
  selectedJob=null;byId("replay-scope").value="delivery";
  player.previewScene(scene);await refresh("",scene.scene_epoch);await refreshMotion(true);
}
byId("create").addEventListener("click",()=>action(async()=>{
  byId("motion-panel").scrollIntoView({block:"start",behavior:"auto"});
  if(fixture.scene_reset_blocked_reason)throw new Error("The previous job must be resolved before another pick. Open Investigate this pick to continue.");
  const product=byId("product").value, fault=byId("scenario").value||null;
  if(!fixture.inventory.some(item=>item.product_id===product&&atSource(item)))await freshDelivery();
  byId("replay-scope").value="delivery";
  const orderId="order-"+crypto.randomUUID();
  const response=await fetch(testPath("/orders"),{method:"POST",headers:{"Content-Type":"application/json","Idempotency-Key":orderId},body:JSON.stringify({order_id:orderId,lines:[{order_line_id:"line-1",product_id:product,source_id:sourceFor(product),destination_id:fixture.destination_id}]})});
  const order=await response.json();if(!response.ok)throw new Error(JSON.stringify(order));
  await refresh(order.job_ids[0],fixture.scene_epoch); await refreshMotion(true);nextMotionPoll=0;
  await api(`/jobs/${order.job_ids[0]}/run`,{fault});
}));
byId("tool-showcase").onclick=()=>action(async()=>{
  byId("motion-panel").scrollIntoView({block:"start",behavior:"auto"});
  if(!fixture.catalogue||fixture.scene_reset_blocked_reason)throw new Error("Resolve the current job before starting the showcase.");
  if(!fixture.inventory.every(atSource))await freshDelivery();
  byId("scenario").value="";byId("replay-scope").value="delivery";
  const orderId="showcase-"+crypto.randomUUID();
  const lines=fixture.products.map((product,index)=>({order_line_id:"line-"+(index+1),product_id:product.product_id,source_id:sourceFor(product.product_id),destination_id:fixture.destination_id}));
  const response=await fetch(testPath("/orders"),{method:"POST",headers:{"Content-Type":"application/json","Idempotency-Key":orderId},body:JSON.stringify({order_id:orderId,lines})});
  const order=await response.json();if(!response.ok)throw new Error(JSON.stringify(order));
  for(const jobId of order.job_ids){
    await refresh(jobId,fixture.scene_epoch);await refreshMotion(true);nextMotionPoll=0;
    const job=await api(`/jobs/${jobId}/run`,{fault:null});
    if(job.state!=="COMPLETED")throw new Error("Showcase paused: "+job.state+". Review the original command evidence before continuing.");
  }
},"Running the six-tool happy-path showcase. Each product is verified before the next pick.");
byId("resolve-blocker").onclick=()=>action(async()=>{
  const pending=pendingExecution();if(!pending)return;
  const group=deliveries.find(item=>item.executions.some(run=>run.job_id===pending.job_id));
  await refresh(pending.job_id,group?.delivery_id);
  await api(`/jobs/${pending.job_id}/reconcile`,{fault:byId("observation").value||null});
},"Collecting a fresh observation for the original pick…");
byId("reconcile").onclick=()=>action(async()=>{if(selectedJob)await api(`/jobs/${selectedJob}/reconcile`,{fault:byId("observation").value || null});},"Collecting a fresh observation for the original pick…");
byId("reset").onclick=()=>action(()=>api("/cell/reset",{}));
byId("fresh-scene").onclick=()=>action(freshDelivery,"Preparing a new delivery; previous replays stay saved.");
byId("scenario").onchange=()=>{fixtureControls();text("message","Scenario selected for the next order. Start new test for fresh products and an independent result.");};
function cellDescription(){
  const profile=cellProfiles.find(item=>item.cell_profile_id===byId("cell-profile").value);
  text("cell-profile-description",profile?`${profile.description} ${profile.product_count} product families · ${profile.tool_count} tools.`:"No robot cells are available.");
  byId("create-test").disabled=busy||!profile;
}
byId("new-test").onclick=async()=>{
  if(busy)return;
  try{
    const data=await request("/cell-profiles");
    cellProfiles=data.profiles.filter(item=>item.selectable);
    byId("cell-profile").replaceChildren();
    cellProfiles.forEach(item=>byId("cell-profile").add(new Option(item.display_name,item.cell_profile_id)));
    byId("cell-profile").value=cellProfiles.find(item=>item.cell_profile_id===data.default_cell_profile_id)?.cell_profile_id||cellProfiles[0]?.cell_profile_id||"";
    newTestRequest={request_id:crypto.randomUUID()};
    byId("cell-profile").disabled=false;text("new-test-error","");cellDescription();
    byId("new-test-dialog").showModal();
  }catch(error){appError(error);}
};
byId("empty-new-test").onclick=()=>byId("new-test").onclick();
byId("cell-profile").onchange=cellDescription;
async function manageTests(dialogId,errorId,operation){
  if(busy)return;
  busy=true;managingTests=true;
  ++historyVersion;++refreshVersion;++viewVersion;refreshing=false;
  fixtureControls();
  byId("message").removeAttribute("data-kind");byId("message").setAttribute("role","status");
  for(const id of ["create-test","cancel-new-test","confirm-delete-test","cancel-delete-test"])byId(id).disabled=true;
  text(errorId,"");
  try{
    const message=await operation();
    byId(dialogId).close();text("message",message);
  }catch(error){text(errorId,error.message);appError(error);}
  finally{
    busy=false;
    for(const id of ["create-test","cancel-new-test","confirm-delete-test","cancel-delete-test"])byId(id).disabled=false;
    try{await refreshHistory();await refresh();await refreshMotion(true);}catch(error){appError(error);}
    managingTests=false;
    fixtureControls();
  }
}
byId("create-test").onclick=()=>{
  if(!newTestRequest||!byId("new-test-dialog").open||!cellProfiles.some(item=>item.cell_profile_id===byId("cell-profile").value))return;
  newTestRequest.cell_profile_id??=byId("cell-profile").value;
  byId("cell-profile").disabled=true;
  return manageTests("new-test-dialog","new-test-error",async()=>{
    const created=await request("/simulation-tests",newTestRequest);
    await refreshHistory();await selectTest(created.test_id);
    return `Test ${created.number} created · ${created.cell_display_name}. Choose a scenario and run an order.`;
  });
};
function confirmDeletion(all){
  if(busy)return;
  const targets=all?testHistory:testHistory.filter(item=>item.test_id===selectedTest);
  if(!targets.length)return;
  deletionRequest={path:all?"/simulation-tests/delete-all":`/simulation-tests/${selectedTest}/delete`,
    body:{request_id:crypto.randomUUID(),...(all?{expected_test_ids:targets.map(item=>item.test_id)}:{})}};
  text("delete-test-title",all?"Delete all tests?":"Delete simulation test?");
  text("confirm-delete-test",all?"Delete all tests":"Delete test");
  text("test-data-warning","The selected tests, orders, evidence and replay files will be permanently removed. Their test numbers become available again. This does not run the robot or resolve uncertain outcomes.");
  const uncertain=targets.some(item=>item.outcomes.some(state=>["UNKNOWN_OUTCOME","REQUIRES_INTERVENTION"].includes(state)));
  text("delete-test-detail",(all?`${targets.length} tests with ${targets.reduce((total,item)=>total+item.order_count,0)} orders will be deleted.`
    :`Test ${targets[0].number} · ${targets[0].cell_display_name} · ${targets[0].order_count} orders will be deleted.`)
    +(uncertain?" This includes unresolved outcomes. Their investigation evidence will also be removed.":"")
    +(targets.some(item=>item.test_id===activeTest)?" There will be no current test until you create a new one.":""));
  text("delete-test-error","");byId("delete-test-dialog").showModal();byId("cancel-delete-test").focus();
}
byId("delete-test").onclick=()=>confirmDeletion(false);
byId("clear-tests").onclick=()=>confirmDeletion(true);
byId("clear-test").onclick=()=>{
  const current=testHistory.find(item=>item.test_id===selectedTest);
  if(busy||!current)return;
  deletionRequest={path:`/simulation-tests/${selectedTest}/clear`,clearTestId:selectedTest,
    body:{request_id:crypto.randomUUID(),expected_revision:current.revision??1}};
  text("delete-test-title",`Clear Test ${current.number} and retry?`);
  text("confirm-delete-test","Clear test");
  text("delete-test-detail",`Keep Test ${current.number} · ${current.cell_display_name}. Remove its orders and results, restore every product and make this the current test, ready to run again.`);
  text("test-data-warning","This removes this test's previous evidence and recordings, including unresolved outcomes. Other tests and your scenario choices stay unchanged. No pick is performed.");
  text("delete-test-error","");byId("delete-test-dialog").showModal();byId("cancel-delete-test").focus();
};
byId("confirm-delete-test").onclick=()=>{
  if(!deletionRequest||!byId("delete-test-dialog").open)return;
  return manageTests("delete-test-dialog","delete-test-error",async()=>{
    const result=await request(deletionRequest.path,deletionRequest.body);
    await refreshHistory();
    if(deletionRequest.clearTestId){
      if(result.cleanup_pending)throw new Error("The clear could not finish. Keep this dialog open and retry Clear test, or reopen the app.");
      await selectTest(deletionRequest.clearTestId);
      const current=testHistory.find(item=>item.test_id===deletionRequest.clearTestId);
      if(current.order_count)return `Test ${current.number} was already cleared. Newer orders and results have been kept.`;
      return `Test ${current.number} cleared. Products restored; your scenario choices are kept. Ready to run again.`;
    }
    return result.cleanup_pending?"Test data removed from history. Some files are still in use; cleanup will retry when the app restarts.":"Test data deleted. Create a new test or review another saved test.";
  });
};
for(const [dialog,cancel] of [["new-test-dialog","cancel-new-test"],["delete-test-dialog","cancel-delete-test"]]){
  byId(cancel).onclick=()=>{if(!busy)byId(dialog).close();};
  byId(dialog).addEventListener("cancel",event=>{if(busy)event.preventDefault();});
}
byId("test-history").onchange=()=>{
  const identity=byId("test-history").value||null;
  return action(()=>selectTest(identity),"Loading saved test…",true);
};
byId("return-current").onclick=()=>action(()=>selectTest(activeTest),"Returning to the current test…",true);
byId("guide-action").onclick=async()=>{
  if(busy)return;
  if(guidance.action==="review"){
    const pending=pendingExecution();if(!pending)return;
    await openInspection(guideEvidence,guideJob===selectedJob?selectedEvents:null);
  }else if(guidance.action==="configure")focusPanel("setup-panel",guideExecution()?.state==="FAILED"?"scenario":"product");
  else if(guidance.action==="reset")await byId("reset").onclick();
  else if(guidance.action==="new-test")await byId("new-test").onclick();
  else if(guidance.action==="current")await byId("return-current").onclick();
};
byId("view-evidence").onclick=()=>{if(!inspection)return;showInspectionPane("evidence");byId("journal-details").open=true;byId("observation-details").open=true;byId("tab-evidence").focus();};
byId("inspect-selected").onclick=()=>openInspection(selectedEvidence,selectedEvents);
byId("return-simulation").onclick=()=>byId("investigation-dialog").close();
byId("investigation-dialog").addEventListener("close",()=>{byId("inspect-selected").focus({preventScroll:true});});
for(const pane of inspectionPanes){
  byId(`tab-${pane}`).onclick=()=>showInspectionPane(pane);
  byId(`tab-${pane}`).addEventListener("keydown",event=>{
    const index=inspectionPanes.indexOf(pane),next=event.key==="ArrowRight"?(index+1)%3:event.key==="ArrowLeft"?(index+2)%3:event.key==="Home"?0:event.key==="End"?2:null;
    if(next===null)return;event.preventDefault();showInspectionPane(inspectionPanes[next]);byId(`tab-${inspectionPanes[next]}`).focus();
  });
}
byId("timeline-filter").onchange=renderInspection;
byId("download-evidence").onclick=()=>{
  if(!inspection||inspection.loading)return;
  const payload={format:"robotops-investigation-1",test_id:inspection.testId,evidence:inspection.evidence,order_events:inspection.events};
  const blob=new Blob([JSON.stringify(payload,null,2)],{type:"application/json"}),url=URL.createObjectURL(blob),link=document.createElement("a");
  link.href=url;link.download=`investigation-${inspection.evidence.job.job_id}.json`;link.click();URL.revokeObjectURL(url);
};
byId("observation").onchange=renderGuidance;
byId("use-normal").onclick=()=>{
  if(busy||readOnly())return;
  byId("observation").value="";renderGuidance();
  byId(pendingExecution()?"resolve-blocker":"observation").focus();
};
byId("product").onchange=fixtureControls;
byId("orders").onchange=async()=>{
  const job=byId("orders").value,group=deliveries.find(item=>item.executions.some(run=>run.job_id===job));
  selectedEvidence=null;selectedEvents=[];byId("inspect-selected").disabled=true;
  byId("replay-scope").value="product";await refresh(job,group?.delivery_id);await refreshMotion(true);
};
byId("delivery").onchange=async()=>{
  const id=byId("delivery").value,group=deliveries.find(item=>item.delivery_id===id);
  selectedEvidence=null;selectedEvents=[];byId("inspect-selected").disabled=true;
  byId("replay-scope").value="delivery";await refresh(group?.executions.at(-1)?.job_id||"",id);await refreshMotion(true);
};
byId("replay-scope").onchange=()=>{selectReplay();refreshMotion(true);};
byId("motion-import").onclick=()=>action(async()=>{
  byId("motion-import").disabled=true;
  try {await api(`/jobs/${selectedJob}/playback/import`,{});}
  finally {byId("motion-import").disabled=false;}
});
byId("visual").onload=()=>{byId("visual-panel").hidden=false;};
byId("visual").onerror=()=>{byId("visual-panel").hidden=true;};
for(const kind of ["scenario","observation"]){
  SimulationGuide.choices(kind).forEach(info=>{
    const row=document.createElement("tr"),name=document.createElement("th"),detail=document.createElement("td");
    name.scope="row";name.textContent=info.label;
    const stage=document.createElement("strong"),meaning=document.createElement("p");
    stage.textContent=info.phase;meaning.textContent=info.meaning;
    detail.append(stage,meaning);row.append(name,detail);byId(`${kind}-comparisons`).append(row);
  });
}
(async()=>{try{
  await refreshHistory();await selectTest(activeTest);
  text("runtime",fixture?.runtime === "blender"?"Blender · CPU · synthetic world":"Deterministic headless world");
  setInterval(()=>{if(!managingTests)refreshHistory().then(()=>{if(!managingTests)return refresh();}).catch(appError);},1000);
  setInterval(()=>{if(!managingTests)refreshMotion();},250);
}catch(error){appError(error);}})();
