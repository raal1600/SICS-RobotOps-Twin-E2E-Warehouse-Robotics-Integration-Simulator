"use strict";
const byId = id => document.getElementById(id);
let selectedJob = null;
let fixture = null;
async function api(path, body) {
  const options = body === undefined ? {} : {method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(body)};
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.reason || JSON.stringify(data.detail));
  return data;
}
function text(id, value) { byId(id).textContent = value; }
async function refresh(preferred) {
  const [orders, cell] = await Promise.all([api("/orders"), api("/cell")]);
  const selection = preferred || byId("orders").value;
  byId("orders").replaceChildren();
  orders.forEach(order => { const option = new Option(order.order_id + " · " + order.status, order.order_id); byId("orders").add(option); });
  if (selection && orders.some(order => order.order_id === selection)) byId("orders").value = selection;
  text("cell-state", cell.mode);
  const order = orders.find(item => item.order_id === byId("orders").value);
  if (!order) return;
  selectedJob = order.job_ids[0];
  const [evidence, events] = await Promise.all([api("/jobs/"+selectedJob+"/evidence"), api("/orders/"+order.order_id+"/timeline")]);
  text("order-state", order.status); text("job-state", evidence.job.state);
  byId("reconcile").disabled = !["UNKNOWN_OUTCOME","EXECUTING","VERIFYING","RECONCILING"].includes(evidence.job.state);
  const verdict = evidence.verifications.at(-1);
  text("verdict", verdict ? verdict.verdict + " · " + verdict.reason : "No verification result yet.");
  text("command", evidence.command ? "Original command: " + evidence.command.command_id + " · Journal: " + (evidence.journal?.status || "unavailable") : "No robot command dispatched.");
  text("evidence", JSON.stringify(evidence, null, 2));
  byId("timeline").replaceChildren();
  events.forEach(event => { const tr=document.createElement("tr");
    [event.timestamp.slice(11,23)+" / "+event.component, event.event_type+(event.state_after ? " → "+event.state_after : ""), event.reason].forEach(value => {const td=document.createElement("td");td.textContent=value;tr.append(td);});byId("timeline").append(tr); });
  if (fixture.runtime === "blender") { byId("visual").src = "/artifacts/latest.png?t=" + Date.now(); }
}
async function action(fn) {
  byId("create").disabled=true;byId("reconcile").disabled=true;text("message","Working…");
  try { await fn();text("message","Updated from persisted evidence."); }
  catch (error) { text("message",error.message); }
  finally { byId("create").disabled=false; await refresh(); }
}
byId("create").addEventListener("click",() => action(async () => {
  const orderId="order-"+crypto.randomUUID();
  const response=await fetch("/orders",{method:"POST",headers:{"Content-Type":"application/json","Idempotency-Key":orderId},body:JSON.stringify({order_id:orderId,lines:[{order_line_id:"line-1",product_id:byId("product").value,source_id:fixture.source_id,destination_id:fixture.destination_id}]})});
  const order=await response.json();if(!response.ok) throw new Error(JSON.stringify(order));
  await api("/jobs/"+order.job_ids[0]+"/run",{fault:byId("scenario").value || null});await refresh(orderId);
}));
byId("reconcile").addEventListener("click",() => action(async () => {if(selectedJob) await api("/jobs/"+selectedJob+"/reconcile",{fault:byId("observation").value || null});}));
byId("reset").addEventListener("click",() => action(() => api("/cell/reset",{})));
byId("orders").addEventListener("change",() => refresh());
byId("visual").addEventListener("load",() => {byId("visual-panel").hidden=false;});
byId("visual").addEventListener("error",() => {byId("visual-panel").hidden=true;});
(async () => {try {fixture=await api("/fixtures");fixture.products.forEach(item=>byId("product").add(new Option(item.sku+" · "+item.product_id,item.product_id)));text("runtime",fixture.runtime === "blender" ? "Blender · CPU · synthetic world" : "Deterministic headless world");await refresh();}catch(error){text("message",error.message);}})();
