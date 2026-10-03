"use strict";
const byId = id => document.getElementById(id);
const player = new MotionPlayer();
let selectedJob = null, selectedDelivery = null, fixture = null, deliveries = [], busy = false, refreshing = false, pollingMotion = false;
let orderSignature = "", productSignature = "", deliverySignature = "", nextMotionPoll = 0, cellMode = "READY", refreshVersion = 0;
let selectedTest = "original", activeTest = "original", testHistory = [], historySignature = "", viewVersion = 0;
let guideEvidence = null, guideJob = null, guidance = null;
const attentionSeen = new Set();
const readOnly = () => selectedTest !== activeTest;
const testPath = path => (selectedTest === "original" ? "" : `/simulation-tests/${selectedTest}`) + path;
function testControls() {
  const current=testHistory.find(item=>item.test_id===selectedTest);
  byId("test-history").value=selectedTest;
  byId("new-test").disabled=busy;
  byId("test-history").disabled=busy;
  byId("return-current").hidden=!readOnly();byId("return-current").disabled=busy;
  text("test-status",readOnly()
    ? `Test ${current?.number}: saved history, read-only. Its original outcomes are preserved. Return to the current test or start a new one.`
    : `Test ${current?.number||1}: current test. Start new test restores all products in a separate world and keeps your scenario and observation choices. Previous results stay in history.`);
  byId("metrics-link").href=testPath("/metrics");
}
async function refreshHistory() {
  const data=await request("/simulation-tests");
  activeTest=data.active_test_id;testHistory=data.tests;
  const signature=JSON.stringify(data);
  if(signature!==historySignature){
    byId("test-history").replaceChildren();
    data.tests.slice().reverse().forEach(item=>byId("test-history").add(new Option(
      `Test ${item.number} · ${item.active?"Current":"Saved"} · ${item.order_count} orders · ${[...new Set(item.outcomes)].join(", ")||"Ready"}`,item.test_id)));
    historySignature=signature;
  }
  byId("test-history").value=selectedTest;testControls();
}
async function selectTest(identity) {
  ++viewVersion;++refreshVersion;refreshing=false;
  selectedTest=identity;selectedJob=null;selectedDelivery=null;fixture=null;deliveries=[];
  guideEvidence=null;guideJob=null;
  byId("setup-panel").open=true;byId("review-panel").open=false;
  orderSignature=productSignature=deliverySignature="";nextMotionPoll=0;
  byId("orders").replaceChildren();byId("delivery").replaceChildren();
  byId("replay-scope").value="delivery";byId("visual-panel").hidden=true;byId("visual").removeAttribute("src");
  player.select(null);testControls();renderGuidance();
  await refresh();await refreshMotion(true);
}
function pendingExecution() {
  const executions=deliveries.flatMap(group=>group.executions);
  return executions.find(item=>item.state==="UNKNOWN_OUTCOME")||executions.find(item=>item.state==="REQUIRES_INTERVENTION");
}
function fixtureControls() {
  testControls();
  if (!fixture) {renderGuidance();return;}
  const products=fixture.products.map(item=>({...item,location:fixture.inventory.find(obj=>obj.product_id===item.product_id)?.location_id}));
  const anyAvailable=products.some(item=>item.location===fixture.source_id);
  const signature=JSON.stringify(products);
  if(signature!==productSignature){
    const selected=byId("product").value;
    byId("product").replaceChildren();
    products.forEach(item=>{
      const available=item.location===fixture.source_id;
      const option=new Option(`${item.sku} · ${available?"at source":anyAvailable?"already picked":"new delivery"}`,item.product_id);
      option.disabled=!available&&anyAvailable;byId("product").add(option);
    });
    byId("product").value=products.find(item=>item.product_id===selected&&item.location===fixture.source_id)?.product_id
      || products.find(item=>item.location===fixture.source_id)?.product_id || selected || products[0]?.product_id || "";
    productSignature=signature;
  }
  const available=products.some(item=>item.product_id===byId("product").value&&item.location===fixture.source_id);
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
  byId("reset").disabled=busy||readOnly();byId("motion-import").disabled=busy||readOnly();
  text("inventory-status", blocker==="SCENE_RESET_IN_PROGRESS" ? "Preparing a fresh scene. Previous orders and recordings are being retained."
    : pending ? `Next pick blocked by ${productName} (${pending.state}). Open Review evidence to continue.`
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
  const panel=byId(id);panel.open=true;
  panel.scrollIntoView({block:"start",behavior:"auto"});
  byId(focusId).focus({preventScroll:true});
}
function renderGuidance() {
  const pending=pendingExecution(), execution=guideExecution();
  const product=fixture?.products.find(item=>item.product_id===pending?.product_id)?.sku||pending?.product_id;
  const evidence=guideJob===execution?.job_id?guideEvidence:null;
  guidance=SimulationGuide.describe({ready:!!fixture,busy,archived:readOnly(),pending,state:execution?.state,
    cellMode,blocked:fixture?.scene_reset_blocked_reason,available:fixture?.inventory.filter(item=>item.location_id===fixture.source_id).length,product,evidence});
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
  // Open and focus once per job needing attention, not on every poll or repeat
  // observation. This navigation never captures evidence or dispatches a pick.
  const key=`${selectedTest}:${pending?.job_id}`;
  if(pending&&!readOnly()&&!busy&&evidence&&!attentionSeen.has(key)){
    attentionSeen.add(key);byId("setup-panel").open=false;
    focusPanel("review-panel","review-heading");
  }
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
async function request(path, body) {
  const options = body === undefined ? {cache:"no-store"} : {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)};
  const response = await fetch(path, options), data = await response.json();
  if (!response.ok) throw new Error(data.reason || JSON.stringify(data.detail));
  return data;
}
async function api(path, body) {
  if(body!==undefined&&readOnly())throw new Error("Saved tests are read-only. Return to the current test or start a new one.");
  return request(testPath(path),body);
}
function text(id, value) { if(byId(id).textContent!==value)byId(id).textContent = value; }
async function refresh(preferred, preferredDelivery) {
  if (refreshing && !preferred && !preferredDelivery) return;
  const version=++refreshVersion;
  refreshing = true;
  try {
    const [orders, cell, currentFixture, groups] = await Promise.all([api("/orders"), api("/cell"),api("/fixtures"),api("/deliveries")]);
    if(version!==refreshVersion)return;
    deliveries=groups;
    fixture=currentFixture;cellMode=cell.mode;fixtureControls();
    const wantedDelivery=preferredDelivery||byId("delivery").value||fixture.scene_epoch;
    selectedDelivery=groups.find(group=>group.delivery_id===wantedDelivery)?.delivery_id||fixture.scene_epoch;
    const group=groups.find(item=>item.delivery_id===selectedDelivery);
    const groupSignature=JSON.stringify(groups);
    if(groupSignature!==deliverySignature){
      byId("delivery").replaceChildren();
      groups.slice().reverse().forEach((item,index)=>byId("delivery").add(new Option(
        `${item.current?"Current delivery":"Saved delivery"} · ${item.started_at.slice(0,16).replace("T"," ")} UTC · ${item.executions.length} executions · ${item.delivery_id.slice(0,8)}`,item.delivery_id)));
      deliverySignature=groupSignature;
    }
    byId("delivery").value=selectedDelivery;
    const selectedExecution=byId("orders").value;
    const keepExecution=byId("replay-scope").value==="product"||group?.executions.some(item=>item.job_id===selectedExecution);
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
    const order = orders.find(item => item.job_ids.includes(byId("orders").value));
    if (!order) {
      const scene=await api("/cell/scene");if(version!==refreshVersion)return;
      selectedJob=null;selectReplay();player.previewScene(scene);
      byId("visual-panel").hidden=true;byId("reconcile").disabled=true;
      text("order-state","No order selected");text("job-state","Ready for a new order");
      text("verdict","Select a saved order to inspect its verification.");text("command","");
      text("evidence","No order selected.");byId("timeline").replaceChildren();await refreshGuide(null,version);return;
    }
    if (selectedJob !== byId("orders").value) {
      byId("visual-panel").hidden=true;byId("visual").removeAttribute("src");
    }
    selectedJob = byId("orders").value; selectReplay();
    const job = selectedJob;
    const [evidence, events] = await Promise.all([api(`/jobs/${job}/evidence`),api(`/orders/${order.order_id}/timeline`)]);
    if (version!==refreshVersion || selectedJob !== job || byId("orders").value !== job) return;
    text("order-state",order.status);text("job-state",evidence.job.state);
    byId("reconcile").disabled=busy || readOnly() || !["UNKNOWN_OUTCOME","EXECUTING","VERIFYING","RECONCILING","REQUIRES_INTERVENTION"].includes(evidence.job.state);
    text("reconcile",evidence.job.state==="REQUIRES_INTERVENTION"?"Observe again and reconcile":"Reconcile selected job");
    const verdict=evidence.verifications.at(-1);
    text("verdict",verdict ? verdict.verdict+" · "+verdict.reason : "No verification result yet.");
    text("command",evidence.command ? "Original command: "+evidence.command.command_id+" · Journal: "+(evidence.journal?.status || "unavailable") : "No robot command dispatched.");
    text("evidence",JSON.stringify(evidence,null,2));
    await refreshGuide(evidence,version);
    if(version!==refreshVersion)return;
    byId("timeline").replaceChildren();
    events.forEach(event => {const tr=document.createElement("tr");
      [event.timestamp.slice(11,23)+" / "+event.component,event.event_type+(event.state_after?" → "+event.state_after:""),event.reason]
        .forEach(value=>{const td=document.createElement("td");td.textContent=value;tr.append(td);});byId("timeline").append(tr);});
    if(fixture.runtime === "blender" && !["RECEIVED","EXECUTING"].includes(evidence.job.state)) {
      const url=testPath(`/jobs/${job}/artifact.png`);
      if(byId("visual").getAttribute("src")!==url) byId("visual").src=url;
    }
  } finally {if(version===refreshVersion)refreshing=false;}
}
async function refreshMotion(force=false) {
  const full=byId("replay-scope").value==="delivery";
  if(!(full?selectedDelivery:selectedJob) || pollingMotion || !force && Date.now()<nextMotionPoll) return;
  pollingMotion=true;
  const version=viewVersion;
  try {
    const data=await api(full?`/deliveries/${selectedDelivery}/playback`:`/jobs/${selectedJob}/playback`);
    if(version!==viewVersion)return;
    if(full)player.updateDelivery(data);else player.update(data);
    const clips=full?data.jobs:[data];
    nextMotionPoll=Date.now()+(clips.some(clip=>["RECORDING","WAITING"].includes(clip.status))?200:1500);
  }
  catch(error){if(version===viewVersion)text("motion-state","Recording feed unavailable · reconnecting");}
  finally {pollingMotion=false;}
}
async function action(fn, message="Running… live motion and status update below.", allowArchived=false) {
  if(busy)return;
  if(readOnly()&&!allowArchived){text("message","Saved tests are read-only. Return to the current test or start a new one.");return;}
  busy=true;fixtureControls();byId("reconcile").disabled=true;
  text("message",message);
  try {await fn();text("message","Updated from persisted evidence. Replay only changes the view.");}
  catch(error){text("message",error.message);}
  finally {busy=false;await refreshHistory();await refresh();await refreshMotion(true);fixtureControls();}
}
async function freshDelivery(){
  const scene=await api("/fixtures/fresh-scene",{});
  selectedJob=null;byId("replay-scope").value="delivery";
  player.previewScene(scene);await refresh("",scene.scene_epoch);await refreshMotion(true);
}
byId("create").addEventListener("click",()=>action(async()=>{
  if(fixture.scene_reset_blocked_reason)throw new Error("The previous job must be resolved before another pick. Open Review evidence to continue.");
  const product=byId("product").value, fault=byId("scenario").value||null;
  if(!fixture.inventory.some(item=>item.product_id===product&&item.location_id===fixture.source_id))await freshDelivery();
  byId("replay-scope").value="delivery";
  const orderId="order-"+crypto.randomUUID();
  const response=await fetch(testPath("/orders"),{method:"POST",headers:{"Content-Type":"application/json","Idempotency-Key":orderId},body:JSON.stringify({order_id:orderId,lines:[{order_line_id:"line-1",product_id:product,source_id:fixture.source_id,destination_id:fixture.destination_id}]})});
  const order=await response.json();if(!response.ok)throw new Error(JSON.stringify(order));
  await refresh(order.job_ids[0],fixture.scene_epoch); await refreshMotion(true);nextMotionPoll=0;
  await api(`/jobs/${order.job_ids[0]}/run`,{fault});
}));
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
byId("new-test").onclick=()=>action(async()=>{
  const created=await request("/simulation-tests",{request_id:crypto.randomUUID()});
  await refreshHistory();await selectTest(created.test_id);
},"Starting a fresh test and saving the previous result…",true);
byId("test-history").onchange=()=>{
  const identity=byId("test-history").value;
  return action(()=>selectTest(identity),"Loading saved test…",true);
};
byId("return-current").onclick=()=>action(()=>selectTest(activeTest),"Returning to the current test…",true);
byId("guide-action").onclick=async()=>{
  if(busy)return;
  if(guidance.action==="review"){
    const pending=pendingExecution();if(!pending)return;
    const group=deliveries.find(item=>item.executions.some(run=>run.job_id===pending.job_id));
    await refresh(pending.job_id,group?.delivery_id);await refreshMotion(true);
    focusPanel("review-panel","review-heading");
  }else if(guidance.action==="configure")focusPanel("setup-panel",guideExecution()?.state==="FAILED"?"scenario":"product");
  else if(guidance.action==="reset")await byId("reset").onclick();
  else if(guidance.action==="new-test")await byId("new-test").onclick();
  else if(guidance.action==="current")await byId("return-current").onclick();
};
byId("view-evidence").onclick=async()=>{
  const execution=guideExecution();if(busy||!execution)return;
  const group=deliveries.find(item=>item.executions.some(run=>run.job_id===execution.job_id));
  await refresh(execution.job_id,group?.delivery_id);
  byId("evidence-details").open=true;focusPanel("timeline-panel","timeline-panel");
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
  byId("replay-scope").value="product";await refresh(job,group?.delivery_id);await refreshMotion(true);
};
byId("delivery").onchange=async()=>{
  const id=byId("delivery").value,group=deliveries.find(item=>item.delivery_id===id);
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
  text("runtime",fixture.runtime === "blender"?"Blender · CPU · synthetic world":"Deterministic headless world");
  setInterval(()=>refreshHistory().then(()=>refresh()).catch(error=>text("message",error.message)),1000);
  setInterval(()=>refreshMotion(),250);
}catch(error){text("message",error.message);}})();
