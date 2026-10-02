"use strict";
const byId = id => document.getElementById(id);
const player = new MotionPlayer();
let selectedJob = null, fixture = null, busy = false, refreshing = false, pollingMotion = false;
let orderSignature = "";
async function api(path, body) {
  const options = body === undefined ? {cache:"no-store"} : {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)};
  const response = await fetch(path, options), data = await response.json();
  if (!response.ok) throw new Error(data.reason || JSON.stringify(data.detail));
  return data;
}
function text(id, value) { byId(id).textContent = value; }
async function refresh(preferred) {
  if (refreshing && !preferred) return;
  refreshing = true;
  try {
    const [orders, cell] = await Promise.all([api("/orders"), api("/cell")]);
    const selection = preferred || byId("orders").value;
    const signature = JSON.stringify(orders.map(order=>[order.order_id,order.status]));
    if (signature !== orderSignature && (document.activeElement !== byId("orders") || preferred)) {
      byId("orders").replaceChildren();
      orders.forEach(order => byId("orders").add(new Option(order.order_id+" · "+order.status,order.order_id)));
      orderSignature = signature;
    }
    if (orders.some(order => order.order_id === selection)) byId("orders").value = selection;
    text("cell-state",cell.mode);
    const order = orders.find(item => item.order_id === byId("orders").value);
    if (!order) return;
    if (selectedJob !== order.job_ids[0]) {
      byId("visual-panel").hidden=true;byId("visual").removeAttribute("src");
    }
    selectedJob = order.job_ids[0]; player.select(selectedJob);
    const job = selectedJob;
    const [evidence, events] = await Promise.all([api(`/jobs/${job}/evidence`),api(`/orders/${order.order_id}/timeline`)]);
    if (selectedJob !== job || byId("orders").value !== order.order_id) return;
    text("order-state",order.status);text("job-state",evidence.job.state);
    byId("reconcile").disabled=busy || !["UNKNOWN_OUTCOME","EXECUTING","VERIFYING","RECONCILING"].includes(evidence.job.state);
    const verdict=evidence.verifications.at(-1);
    text("verdict",verdict ? verdict.verdict+" · "+verdict.reason : "No verification result yet.");
    text("command",evidence.command ? "Original command: "+evidence.command.command_id+" · Journal: "+(evidence.journal?.status || "unavailable") : "No robot command dispatched.");
    text("evidence",JSON.stringify(evidence,null,2));
    byId("timeline").replaceChildren();
    events.forEach(event => {const tr=document.createElement("tr");
      [event.timestamp.slice(11,23)+" / "+event.component,event.event_type+(event.state_after?" → "+event.state_after:""),event.reason]
        .forEach(value=>{const td=document.createElement("td");td.textContent=value;tr.append(td);});byId("timeline").append(tr);});
    if(fixture.runtime === "blender" && !["RECEIVED","EXECUTING"].includes(evidence.job.state)) {
      const url=`/jobs/${job}/artifact.png`;
      if(byId("visual").getAttribute("src")!==url) byId("visual").src=url;
    }
  } finally {refreshing=false;}
}
async function refreshMotion() {
  if(!selectedJob || pollingMotion) return;
  pollingMotion=true;
  try {const data=await api(`/jobs/${selectedJob}/playback`);player.update(data);}
  catch(error){text("motion-state","Recording feed unavailable · reconnecting");}
  finally {pollingMotion=false;}
}
async function action(fn) {
  busy=true;byId("create").disabled=true;byId("reset").disabled=true;byId("reconcile").disabled=true;
  text("message","Running… live motion and status update below.");
  try {await fn();text("message","Updated from persisted evidence. Replay only changes the view.");}
  catch(error){text("message",error.message);}
  finally {busy=false;byId("create").disabled=false;byId("reset").disabled=false;await refresh();await refreshMotion();}
}
byId("create").addEventListener("click",()=>action(async()=>{
  const orderId="order-"+crypto.randomUUID();
  const response=await fetch("/orders",{method:"POST",headers:{"Content-Type":"application/json","Idempotency-Key":orderId},body:JSON.stringify({order_id:orderId,lines:[{order_line_id:"line-1",product_id:byId("product").value,source_id:fixture.source_id,destination_id:fixture.destination_id}]})});
  const order=await response.json();if(!response.ok)throw new Error(JSON.stringify(order));
  await refresh(orderId); await refreshMotion();
  await api(`/jobs/${order.job_ids[0]}/run`,{fault:byId("scenario").value || null});
}));
byId("reconcile").onclick=()=>action(async()=>{if(selectedJob)await api(`/jobs/${selectedJob}/reconcile`,{fault:byId("observation").value || null});});
byId("reset").onclick=()=>action(()=>api("/cell/reset",{}));
byId("orders").onchange=async()=>{selectedJob=null;player.select(null);byId("visual-panel").hidden=true;await refresh();await refreshMotion();};
byId("motion-import").onclick=()=>action(async()=>{
  byId("motion-import").disabled=true;
  try {await api(`/jobs/${selectedJob}/playback/import`,{});}
  finally {byId("motion-import").disabled=false;}
});
byId("visual").onload=()=>{byId("visual-panel").hidden=false;};
byId("visual").onerror=()=>{byId("visual-panel").hidden=true;};
(async()=>{try{
  fixture=await api("/fixtures");fixture.products.forEach(item=>byId("product").add(new Option(item.sku+" · "+item.product_id,item.product_id)));
  text("runtime",fixture.runtime === "blender"?"Blender · CPU · synthetic world":"Deterministic headless world");
  await refresh();await refreshMotion();
  setInterval(()=>refresh().catch(error=>text("message",error.message)),1000);
  setInterval(refreshMotion,250);
}catch(error){text("message",error.message);}})();
