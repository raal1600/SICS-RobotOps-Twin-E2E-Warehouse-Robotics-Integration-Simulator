"use strict";

// This view renders server records. It never invents execution or protocol events.
class IntegrationConsole {
  constructor({request, path, readOnly, update, physical, activity, investigate = () => {}, sessionChanged = () => {}}) {
    Object.assign(this, {request, path, readOnly, update, physical, activity, investigate, sessionChanged});
    this.session = null;
    this.busy = false;
    this.startUnconfirmed = false;
    this.generation = 0;
    this.socket = null;
    this.retry = null;
    this.liveTimer = null;
    this.pollingLive = false;
    this.liveGeneration = 0;
    this.selected = null;
    this.pinned = false;
    this.tab = "Data";
    this.sourceMode = "recorded";
    this.sourceDocument = null;
    this.sourceRequest = 0;
    this.engineeringDocument = null;
    this.engineeringRequest = 0;
    this.phase = null;
    this.robotOpened = false;
    this.el = id => document.getElementById(id);
    this.el("integration-advance").onclick = () => this.advance();
    this.el("integration-reconcile").onclick = () => this.reconcile();
    this.el("integration-return").onclick = () => this.focus();
    this.el("integration-follow").onclick = () => this.follow();
    this.el("integration-follow-mobile").onclick = () => this.follow();
    this.el("integration-export").onclick = () => this.exportRun();
    this.el("integration-source-excerpt").onclick = () => { this.sourceMode = "recorded"; this.inspect(); };
    this.el("integration-source-full").onclick = () => this.sourceMode==="current"&&this.sourceDocument?.status==="loading" ? undefined : Promise.all([
      this.loadSourceFile(this.sourceDocument?.key === this.engineeringKey() ? this.sourceDocument.component || "entry" : "entry"),
      this.loadEngineering()
    ]);
    this.el("integration-source-select").onchange = event => this.loadSourceFile(event.target.value);
    this.el("integration-engineering-refresh").onclick = () => this.loadEngineering(true);
    this.el("integration-engineering-search").oninput = () => this.renderEngineering();
    this.el("integration-engineering-export").onclick = () => this.exportInspection();
    this.el("integration-investigate").onclick = () => this.investigate(this.selected?.job_id || this.session?.job_id);
    this.el("integration-reset-filters").onclick = () => { this.resetFilters(); this.renderTrace(); this.renderPhases(); };
    for(const name of ["search", "perspective", "status-filter", "component-filter", "protocol-filter", "repeat-filter"]){
      this.el(`integration-${name}`).oninput = () => this.renderTrace();
    }
    this.el("integration-history").onchange = event => this.selectSession(event.target.value);
    for (const tab of ["Data", "State", "Protocol", "Source", "Records", "Decisions", "Run info", "Recovery", "Raw JSON"]) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = tab;
      button.id = `integration-tab-${tab.toLowerCase().replaceAll(" ", "-")}`;
      button.className = "secondary";
      button.setAttribute("role", "tab");
      button.onclick = () => { this.tab = tab; this.el("integration-explanation").open = tab === "Data"; this.el("integration-payload").open = true; this.inspect(); if(this.engineeringTab())this.loadEngineering(); };
      button.onkeydown = event => {
        const tabs=Array.from(this.el("integration-tabs").children), index=tabs.indexOf(button);
        const next=event.key==="ArrowRight"?(index+1)%tabs.length:event.key==="ArrowLeft"?(index+tabs.length-1)%tabs.length:event.key==="Home"?0:event.key==="End"?tabs.length-1:null;
        if(next===null)return;event.preventDefault();tabs[next].onclick();tabs[next].focus();
      };
      this.el("integration-tabs").append(button);
    }
  }

  sessionLabel(session) {
    const scenario=typeof SimulationGuide!=="undefined"?SimulationGuide.explain("scenario",session.fault||"").label:session.fault||"Normal pick";
    const failed=(session.steps||[]).filter(step=>step.status==="FAILED").length;
    return `${scenario} · ${session.status}${failed?` · ${failed} failed attempt${failed===1?"":"s"}`:""} · ${(session.order_id||session.session_id).slice(-8)}`;
  }

  async selectSession(identity) {
      if(this.busy)return;
      const generation=++this.generation;
      this.disconnect();
      this.busy=true;this.activity(true);
      this.el("integration-stream").textContent="Loading saved run…";
      if(this.session)this.render();
      try {
        const saved=await this.request(`/integration/sessions/${encodeURIComponent(identity)}`);
        if(generation!==this.generation)return;
        this.accept(saved);await this.update(saved);
      }
      catch (error) { if(generation===this.generation)this.error(error); }
      finally {if(generation===this.generation){this.busy=false;this.activity(false);if(this.session){this.render();this.watch();}}}
  }

  async load() {
    const generation = ++this.generation;
    this.disconnect();
    this.resetLive();
    this.session = null;
    this.selected = null; this.pinned = false;
    this.el("integration-console").hidden = true;
    this.restoreRobot();
    const sessions = await this.request("/integration/sessions");
    if (generation !== this.generation) return;
    const items = (Array.isArray(sessions) ? sessions : sessions.sessions)?.slice().sort((a,b) => a.created_at.localeCompare(b.created_at));
    this.el("integration-history").replaceChildren();
    for (const item of items || []) {
      const option = document.createElement("option");
      option.value = item.session_id;
      option.textContent = this.sessionLabel(item);
      this.el("integration-history").append(option);
    }
    if (items?.length) {
      const item = items.find(value => !["COMPLETED", "FAILED"].includes(value.status)) || items.at(-1);
      const saved=await this.request(`/integration/sessions/${item.session_id}`);
      if(generation!==this.generation)return;
      this.accept(saved);
      this.watch();
    }
  }

  clear() {
    ++this.generation;
    this.disconnect();
    this.resetLive();
    this.session = null;
    this.el("integration-console").hidden = true;
    this.el("integration-live").hidden = true;
    this.sessionChanged(null);
    this.restoreRobot();
  }

  async start(request, fault) {
    if(this.startUnconfirmed)throw new Error("The previous request is unconfirmed. Reload this page to check saved runs before starting another pick.");
    this.startUnconfirmed = true;
    let session;
    try { session = await this.request("/v1/wms/tasks", {
      request, request_id: crypto.randomUUID(), fault, mode: "guided"
    }); }
    catch(error){
      // A failed response does not prove intake failed. Read durable sessions;
      // never repeat the write or invent a simulation outcome.
      try { await this.load(); this.startUnconfirmed = false; }
      catch { throw new Error(`${error.message}. The request is unconfirmed. Reload this page to check saved runs before starting another pick.`); }
      throw error;
    }
    this.startUnconfirmed = false;
    this.accept(session);
    const option = document.createElement("option");
    option.value = session.session_id;
    option.textContent = this.sessionLabel(session);
    this.el("integration-history").append(option);
    this.el("integration-history").value=session.session_id;
    this.watch();
    this.focus();
  }

  disconnect() {
    if (this.retry) clearTimeout(this.retry);
    this.retry = null;
    if (this.socket) { this.socket.onclose = null; this.socket.close(); }
    this.socket = null;
  }

  watch() {
    this.disconnect();
    if (!this.session || typeof WebSocket === "undefined") return;
    const generation = this.generation;
    const sessionId = this.session.session_id;
    const url = new URL(this.path(`/integration/sessions/${this.session.session_id}/stream`), location.href);
    url.protocol = location.protocol === "https:" ? "wss:" : "ws:";
    this.socket = new WebSocket(url);
    this.socket.onmessage = event => {
      if (generation !== this.generation || sessionId !== this.session?.session_id) return;
      try { const data = JSON.parse(event.data); this.accept(data.session || data); }
      catch { this.el("integration-stream").textContent = "Trace message unavailable; reload from persisted state."; }
    };
    this.socket.onopen = () => { this.el("integration-stream").textContent = "Live trace · read-only WebSocket"; };
    this.socket.onclose = event => {
      if (generation !== this.generation) return;
      if([1008,4404,4409].includes(event.code)){
        this.clear();
        this.el("integration-stream").textContent="Saved test changed; reload its current trace from history.";
        return;
      }
      this.el("integration-stream").textContent = "Trace disconnected · reconnecting to saved state";
      this.retry = setTimeout(() => this.watch(), 2000);
    };
  }

  accept(session) {
    if (!session?.session_id) return;
    if (this.session?.session_id === session.session_id && session.revision < this.session.revision) return;
    if(this.session?.session_id !== session.session_id){this.selected=null;this.pinned=false;this.robotOpened=false;this.resetFilters();}
    if(this.session?.session_id !== session.session_id || this.session?.command_id !== session.command_id)this.resetLive(session.command_id);
    this.session = session;
    this.render();
    if(session.current_stage>=16 && session.command_id && !this.liveTimer && !this.pollingLive)this.pollLive();
  }

  resetLive(commandId = null) {
    ++this.liveGeneration;
    if(this.liveTimer)clearTimeout(this.liveTimer);
    this.liveTimer=null;
    this.pollingLive=false;
    this.el("integration-protocol-live").textContent=commandId
      ? `Waiting for protocol evidence for command ${commandId}.`
      : "No protocol evidence loaded for this session.";
    this.el("integration-live-state").textContent="";
    this.el("integration-replay-evidence").textContent=commandId
      ? `No recorded motion loaded for original command ${commandId}.`
      : "No recorded motion loaded for this session.";
  }

  async pollLive() {
    if(!this.session?.command_id || !this.session.context?.physical_authorized || this.pollingLive)return;
    this.pollingLive=true;
    const generation=this.liveGeneration,sessionId=this.session.session_id,commandId=this.session.command_id;
    const current=()=>generation===this.liveGeneration && sessionId===this.session?.session_id && commandId===this.session?.command_id;
    try{
      const live=await this.request(`/integration/sessions/${sessionId}/live`);
      if(!current())return;
      if(live.command_id!==commandId)throw new Error("Response belongs to a different command");
      this.el("integration-protocol-live").textContent=JSON.stringify(live,null,2);
    }catch(error){
      if(current())this.el("integration-protocol-live").textContent=`Protocol evidence unavailable for command ${commandId}: ${error.message}. This read does not establish an execution outcome.`;
    }finally{
      if(current()){
        this.pollingLive=false;
        if(this.session?.current_stage===16 && this.session.context?.physical_authorized){
          this.liveTimer=setTimeout(()=>{this.liveTimer=null;this.pollLive();},500);
        }
      }
    }
  }

  focus() { globalThis.robotWorkspace?.show("run",true);this.el("integration-console").scrollIntoView({block: "start", behavior: "auto"}); }
  error(error) { this.el("integration-error").textContent = error.message; }

  async advance() {
    if (this.busy || !this.session || this.readOnly()) return;
    this.busy = true;
    this.activity(true);
    this.el("integration-error").textContent = "";
    const generation = this.generation;
    const stage = this.session.current_stage;
    try {
      if(stage === 16)await this.physical(this.session, "before");
      await this.authorizeOne();
      if(stage === 16)await this.physical(this.session, "after");
      // Gate 15 is the explicit consent. Only its successful response permits
      // the immediately following bounded physical stage request.
      if (stage === 15 && this.session.current_stage === 16) {
        this.el("integration-live").hidden = false;
        this.el("integration-live-state").textContent = "Execution authorized · waiting for recorded controller evidence";
        await this.physical(this.session, "before");
        await this.authorizeOne();
        await this.physical(this.session, "after");
      }
      if (generation === this.generation) await this.update(this.session);
    } catch (error) {
      if (generation === this.generation) {
        this.error(error);
        try { this.accept(await this.request(`/integration/sessions/${this.session.session_id}`)); } catch { /* Preserve the last committed view. */ }
      }
    } finally { this.busy = false; this.activity(false); this.render(); }
  }

  async authorizeOne() {
    const value = this.session;
    const generation = this.generation;
    this.render();
    const result = await this.request(`/integration/sessions/${value.session_id}/authorize`, {
      request_id: crypto.randomUUID(), expected_revision: value.revision,
      stage: value.current_stage, decision: "approve"
    });
    if(generation !== this.generation || value.session_id !== this.session?.session_id)throw new Error("The selected test changed. Reload the original session to inspect its saved result.");
    this.accept(result);
  }

  async reconcile() {
    if (this.busy || !this.session || this.readOnly()) return;
    this.busy = true; this.activity(true); this.render(); this.el("integration-error").textContent = "";
    const generation=this.generation,sessionId=this.session.session_id;
    try {
      const saved=await this.request(`/integration/sessions/${sessionId}/reconcile`, {
        request_id: crypto.randomUUID(), expected_revision: this.session.revision,
        fault: document.getElementById("observation").value || null
      });
      if(generation!==this.generation || sessionId!==this.session?.session_id)return;
      this.accept(saved);
      await this.update(this.session);
    } catch (error) { if(generation===this.generation)this.error(error); }
    finally { this.busy = false; this.activity(false); this.render(); }
  }

  resetFilters() {
    this.phase = null;
    for(const name of ["search", "perspective", "status-filter", "component-filter", "protocol-filter", "repeat-filter"]){
      this.el(`integration-${name}`).value = name === "search" ? "" : "all";
    }
  }

  follow() {
    this.pinned = false;
    this.selected = this.session?.steps?.at(-1) || null;
    this.resetFilters();
    this.render();
    this.el("integration-inspector-title").scrollIntoView({block:"nearest", behavior:"auto"});
  }

  selectStep(step) {
    this.selected = step;
    this.pinned = true;
    this.renderPhases();
    this.renderTrace();
    this.inspect();
  }

  node(tag, text, className) {
    const node = document.createElement(tag);
    if(text !== undefined)node.textContent = text;
    if(className)node.className = className;
    return node;
  }

  async exportRun() {
    const identity = this.session?.session_id;
    if(!identity)return;
    try {
      const saved = await this.request(`/integration/sessions/${identity}/export`);
      const url = URL.createObjectURL(new Blob([JSON.stringify(saved, null, 2)], {type:"application/json"}));
      const link = this.node("a");
      link.href = url; link.download = `robotops-run-${identity}.json`; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch(error) { this.error(error); }
  }

  async loadSourceFile(component = "entry") {
    const sessionId = this.session?.session_id, step = this.selected;
    if(!sessionId || !step)return;
    const key = `${sessionId}/${step.step_id}`, generation = this.generation, requestId = ++this.sourceRequest;
    const selected = component === "entry" ? step.source : this.engineeringDocument?.source_catalog?.find(item => item.key === component);
    if(!selected)return;
    this.sourceMode = "current";
    this.sourceDocument = {key, status:"loading", path:selected.path, symbol:selected.symbol, component};
    this.inspect();
    try {
      const source = await this.request(`/integration/sessions/${encodeURIComponent(sessionId)}/steps/${encodeURIComponent(step.step_id)}/source${component === "entry" ? "" : `?component=${encodeURIComponent(component)}`}`);
      if(requestId !== this.sourceRequest || generation !== this.generation || sessionId !== this.session?.session_id || step.step_id !== this.selected?.step_id)return;
      if(source.path !== selected.path)throw new Error("The returned source belongs to a different file.");
      this.sourceDocument = {...source, key, component};
    } catch(error) {
      if(requestId !== this.sourceRequest || generation !== this.generation || sessionId !== this.session?.session_id || step.step_id !== this.selected?.step_id)return;
      this.sourceDocument = {key, component, path:selected.path, symbol:selected.symbol, status:"unavailable", reason:error.message};
    }
    this.inspect();
    this.jumpToSource();
  }

  jumpToSource() {
    const line = this.sourceDocument?.symbol_start_line || this.sourceDocument?.excerpt_start_line;
    if(this.tab === "Source" && this.sourceMode === "current" && line){
      const code = this.el("integration-inspector");
      const lineHeight = typeof getComputedStyle === "function" ? parseFloat(getComputedStyle(code).lineHeight) : 20;
      code.scrollTop = Math.max(0, this.sourceHighlightNode ? this.sourceHighlightNode.offsetTop - lineHeight : (line - 2) * lineHeight);
      code.scrollLeft = 0;
    }
  }

  renderSourceLines(source) {
    const lines = source.content.split("\n"), start = source.symbol_start_line, end = source.symbol_end_line;
    const valid = Number.isInteger(start) && Number.isInteger(end) && start >= 1 && start <= end && end <= lines.length;
    const rows = [];
    for(let index = 0; index < lines.length; index++){
      const number = index + 1, related = valid && number >= start && number <= end;
      const row = this.node("span", lines[index], related ? "source-line source-related-line" : "source-line");
      row.dataset.sourceLine = number;
      if(related && number === start)this.sourceHighlightNode = row;
      rows.push(row);
      if(index < lines.length - 1)rows.push(this.node("span", "\n"));
    }
    this.el("integration-inspector").replaceChildren(...rows);
    this.el("integration-source-highlight").hidden = false;
    this.el("integration-source-highlight-label").textContent = valid
      ? `Highlighted ${source.symbol_kind || "code"}: ${source.symbol} · lines ${start}–${end}. The rest of the file stays visible for context.`
      : "The related code location is unavailable in this file. The full file is shown without a highlight.";
  }

  engineeringTab() { return ["Protocol", "Records", "Decisions", "Run info"].includes(this.tab); }

  engineeringKey() { return `${this.session?.session_id}/${this.selected?.step_id}`; }

  async loadEngineering(refresh = false) {
    const key = this.engineeringKey(), step = this.selected, session = this.session;
    if(!step || !session)return;
    if(!refresh && this.engineeringDocument?.key === key && this.engineeringDocument.status !== "unavailable"){this.renderEngineering();return;}
    const requestId = ++this.engineeringRequest, generation = this.generation;
    this.engineeringDocument = {key, status:"loading"}; this.renderEngineering();
    try {
      const data = await this.request(`/integration/sessions/${encodeURIComponent(session.session_id)}/steps/${encodeURIComponent(step.step_id)}/inspection`);
      if(requestId !== this.engineeringRequest || generation !== this.generation || key !== this.engineeringKey())return;
      if(data.session_id !== session.session_id || data.step_id !== step.step_id)throw new Error("The response belongs to another step.");
      this.engineeringDocument = {...data, key, status:"available"};
    } catch(error) {
      if(requestId !== this.engineeringRequest || generation !== this.generation || key !== this.engineeringKey())return;
      this.engineeringDocument = {key, status:"unavailable", reason:error.message};
    }
    this.renderEngineering();
  }

  async exportInspection() {
    const data = this.engineeringDocument;
    if(data?.status !== "available" || data.key !== this.engineeringKey())return;
    const {key, status, ...saved} = data;
    const url = URL.createObjectURL(new Blob([JSON.stringify(saved, null, 2)], {type:"application/json"}));
    const link = this.node("a");link.href = url;link.download = `robotops-inspection-${saved.step_id}.json`;link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  renderEngineering() {
    const active = this.engineeringTab(), data = this.engineeringDocument?.key === this.engineeringKey() ? this.engineeringDocument : null;
    const ready = data?.status === "available", panel = this.el("integration-engineering-body");
    this.el("integration-engineering").hidden = !active;
    this.el("integration-inspector").hidden = active;
    this.el("integration-engineering-export").disabled = !ready;
    this.el("integration-engineering-status").textContent = ready
      ? `Read at ${data.read_at} · session revision ${data.session_revision}. Refresh reads saved records only.`
      : data?.status === "loading" ? "Reading saved engineering evidence…" : data?.reason || "Select Refresh records to load the engineering view.";
    const select = this.el("integration-source-select"), previous = this.sourceMode === "current" ? this.sourceDocument?.component || "entry" : "entry";
    const selectFocused=document.activeElement===select;
    this.el("integration-source-browser").hidden = this.sourceMode !== "current";
    select.disabled = !ready;
    this.el("integration-source-catalog-status").textContent = data?.status === "unavailable" ? `Component list unavailable: ${data.reason}. Select Full Python file to retry.` : ready ? `${data.source_catalog.length} components available. Choose one to view its code.` : "Loading components…";
    this.el("integration-source-catalog-note").hidden = !ready;
    select.replaceChildren();
    const options = ready ? data.source_catalog : [{key:previous, label:"Selected component", symbol:this.sourceDocument?.symbol || this.selected?.source?.symbol || "Stage entry point"}];
    for(const item of options){const option=this.node("option",`${item.label} · ${item.symbol}`);option.value=item.key;select.append(option);}
    select.value = previous;
    if(selectFocused&&!select.disabled)select.focus({preventScroll:true});
    if(ready){
      this.el("integration-source-catalog-note").textContent = data.source_scope;
    }
    panel.replaceChildren();
    if(!active || !ready)return;
    const query = this.el("integration-engineering-search").value.toLowerCase();
    const matches = value => !query || JSON.stringify(value).toLowerCase().includes(query);
    const note = value => panel.append(this.node("p", value, "muted"));
    const heading = value => panel.append(this.node("h4", value));
    const details = (label, value) => {
      if(!matches([label, value]))return;
      const box = this.node("details"), summary = this.node("summary", label), pre = this.node("pre", JSON.stringify(value, null, 2));
      box.append(summary, pre);panel.append(box);
    };
    const table = rows => {
      const list = this.node("dl", undefined, "engineering-facts");let shown = 0;
      for(const row of rows || []){
        if(!matches(row))continue;
        const label = row.field.split(".").at(-1).replaceAll("_", " ");
        const term = this.node("dt", label), value = this.node("dd");
        value.append(this.node("span", row.value === null ? "null (recorded)" : typeof row.value === "object" ? JSON.stringify(row.value) : String(row.value)), this.node("small", row.field));
        list.append(term, value);shown++;
      }
      panel.append(list);
      if(!shown)note(query ? "No fields match this filter." : "No individual results were saved for this step.");
    };
    if(this.tab === "Protocol"){
      heading(`${data.protocol.protocol} · ${data.protocol.classification}`);note(data.protocol.scope);
      details("Saved stage input (may differ from exact wire arguments)", data.protocol.input);
      table(data.protocol.facts);
    } else if(this.tab === "Records"){
      note(data.records.scope);
      const items = data.records.items.filter(matches);
      heading(`${items.length} linked stored records`);
      for(const item of items)details(`${item.kind || item.table} · ${item.scope}${item.selected_step_reference ? " · selected step reference" : ""} · ${item.id}`, item);
      if(data.records.unresolved_selected_ids.length)details("References without a matching domain/effect row (may be job, order or external IDs)", data.records.unresolved_selected_ids);
      if(data.records.protocol_events_truncated)note("Showing the first 300 saved protocol notifications for this command.");
    } else if(this.tab === "Decisions"){
      note(data.decisions.scope);heading("Rule at this boundary");note(data.decisions.rule);
      heading("Recorded result");table(data.decisions.facts);
      details("Recorded input", data.decisions.input);
      for(const proof of data.decisions.proofs)details(`${proof.label} · ${proof.state}`, proof);
      heading("Planning and verification inputs");
      for(const item of data.records.items.filter(item => ["ActionPlan", "WorldObservation", "RobotCommand", "VerificationResult", "CommandReceipt"].includes(item.kind)))details(`${item.kind} · ${item.id} · linked job record (check timestamp)`, item.body);
      heading("When this boundary fails");note(data.decisions.recovery);
    } else {
      heading("Recorded run identity");table(Object.entries(data.run.recorded).map(([field,value])=>({field:`recorded.${field}`,value})));
      heading("Versions and hashes in this step");table(data.run.recorded_versions);
      heading("Current reference settings");note(data.run.current_reference.scope);
      details(`Current runtime: ${data.run.current_reference.runtime} · settings`, data.run.current_reference.settings);
      heading("Evidence not available");for(const item of data.run.missing)note(item);
    }
    heading("Follow this job through the saved journey");
    note("Links share a saved job or command identity. They are not a captured function call trace.");
    const links = this.node("div", undefined, "engineering-step-links");
    for(const item of data.related_steps.filter(matches)){
      const button=this.node("button",`${item.stage}. ${item.title} · ${item.status} · ${item.relation}`,"secondary");button.type="button";
      button.onclick=()=>{const step=this.session.steps.find(step=>step.step_id===item.step_id);if(step){this.selectStep(step);this.loadEngineering();}};links.append(button);
    }
    panel.append(links);
  }

  dockRobot() {
    const panel = this.el("motion-panel"), dock = this.el("integration-robot-dock");
    if(!panel?.parentNode || panel.parentNode === dock)return;
    this.robotHome = {parent:panel.parentNode, next:panel.nextSibling};
    dock.append(panel);
  }

  restoreRobot() {
    if(this.robotHome){
      this.robotHome.parent.insertBefore(this.el("motion-panel"), this.robotHome.next);
      this.robotHome = null;
    }
  }

  replayEvidence(data) {
    if(!this.session?.command_id)return;
    const clip = data?.jobs?.find(item => item.job_id === this.session.job_id) || data;
    const matching = clip?.job_id === this.session.job_id && clip?.command_id === this.session.command_id;
    this.el("integration-replay-evidence").textContent = !matching
      ? "No matching replay loaded for the original command. Other job playback is not evidence for this run."
      : clip.recording
      ? `RECORDED · ${clip.recording.complete ? "Complete" : "Partial"} Blender motion for command ${clip.command_id}. Replay does not prove verification.`
      : `UNAVAILABLE · No recorded Blender motion for command ${clip.command_id}. ${clip.reason || "This runtime provides events and a scene reference only."}`;
  }

  render() {
    const session = this.session;
    if(!session)return;
    this.sessionChanged(session);
    this.el("integration-console").hidden = false;
    this.dockRobot();
    this.el("integration-history").value = session.session_id;
    for(const option of this.el("integration-history").children){
      if(option.value === session.session_id)option.textContent = this.sessionLabel(session);
    }
    const steps = session.steps || [];
    this.selected = (this.pinned && steps.find(step => step.step_id === this.selected?.step_id)) || steps.at(-1) || null;
    const plain = session.workbench?.status || session.status;
    const scenario = typeof SimulationGuide !== "undefined" ? SimulationGuide.explain("scenario", session.fault || "").label : session.fault || "Normal pick";
    this.el("integration-run").textContent = `Order ${session.order_id || "not created"} · ${scenario}`;
    this.el("integration-execution-run").textContent = this.el("integration-run").textContent;
    this.el("integration-state").textContent = session.status.replaceAll("_", " ");
    this.el("integration-ids").textContent = [["Session",session.session_id],["Correlation",session.correlation_id],["Order",session.order_id],["Current job",session.job_id],["Original command",session.command_id]]
      .map(([label,value])=>`${label}: ${value || "not created"}`).join("\n");
    const stage = session.current_stage, pending = session.pending_authorization;
    const unproven = ["UNKNOWN_OUTCOME","REQUIRES_INTERVENTION"].includes(session.status);
    const businessFailure = stage === 20 && session.status === "RETRYABLE_FAILURE";
    const ended = ["COMPLETED","FAILED"].includes(session.status);
    const failures=steps.filter(step=>step.status==="FAILED");
    const summary=this.el("integration-attempt-summary");
    summary.hidden=!failures.length;
    summary.textContent=failures.length?`${failures.length} failed attempt${failures.length===1?"":"s"} recorded: ${[...new Set(failures.map(step=>step.title))].join(", ")}. ${session.status==="COMPLETED"?"The journey later finished; earlier failed attempts remain in the evidence.":"Inspect the failed attempt and current recovery evidence before continuing."}`:"";
    this.el("integration-pending").hidden = false;
    this.el("integration-pending-title").textContent = plain;
    this.el("integration-position").textContent = ended
      ? `Saved journey · last recorded stage ${steps.at(-1)?.stage || stage}`
      : `Step ${stage} · ${pending?.title || (unproven ? "Reconciliation required" : "Backend operation")}`;
    this.el("integration-pending-detail").textContent = unproven
      ? "Do not retry the pick. Reconciliation queries the original command journal and fresh observation; it does not create or send a replacement robot command."
      : businessFailure
      ? "Retry sends only the business acknowledgement. No robot command will be sent. Review the physical evidence below."
      : stage === 15 && !ended
      ? "Approving this boundary immediately requests execution of the original command once. This application authorization is not a certified safety function."
      : session.status === "EXECUTING_STAGE"
      ? "The backend owns this stage. Recovery checks persisted intent; an active operation may reject recovery until its lease expires. Physical recovery never resends a command."
      : ended ? "Open Inspect evidence to review each saved outcome. Replay shows recorded motion; it does not prove verification."
      : `${pending?.label || "No action permitted"}. This performs the current backend operation and saves its result. Inspection does not execute work.`;
    this.el("integration-command").textContent = `Original command: ${session.command_id || "not created yet"}`;
    this.el("integration-advance").textContent = this.busy ? "Executing bounded stage…" : unproven ? "Awaiting reconciliation" : pending?.label || "No execution action";
    this.el("integration-advance").disabled = this.busy || this.readOnly() || !pending || unproven;
    this.el("integration-advance").hidden = ended;
    this.el("integration-pending").classList.toggle("physical-gate", stage === 15 && !!pending);
    this.el("integration-pending").classList.toggle("uncertain", unproven);
    this.el("integration-pending").classList.toggle("business-failure", businessFailure);
    this.el("integration-reconcile").textContent = session.status === "EXECUTING_STAGE" ? "Recover interrupted stage" : "Reconcile original command";
    this.el("integration-reconcile").hidden = !unproven && session.status !== "EXECUTING_STAGE";
    this.el("integration-reconcile").disabled = this.busy || this.readOnly();
    this.el("integration-history").disabled = this.busy;
    this.el("integration-live").hidden = !(stage >= 16 && session.context?.physical_authorized);
    this.el("integration-live-state").textContent = `${plain}. Live controller data and replay do not establish sensor verification.`;
    if(stage >= 15 && !this.robotOpened){ this.el("integration-robot").open = true; this.robotOpened = true; }
    this.renderProofs();
    this.renderPhases();
    this.renderTrace();
    this.inspect();
  }

  renderProofs() {
    const proofs = this.session.workbench?.proofs || [];
    this.el("integration-proof-scope").textContent = `Robot boundaries apply to current job ${this.session.job_id || "not created"}. Business intent and ERP completion apply to the order. Select a boundary to inspect its saved result.`;
    const list = this.el("integration-proofs"); list.replaceChildren();
    for(const proof of proofs){
      const row = this.node("li"), button = this.node("button", undefined, "secondary");
      button.type = "button"; button.dataset.proof = proof.key; button.dataset.state = proof.state;
      button.append(this.node("strong",proof.label), this.node("span",{established:"✓ Recorded proof",failed:"× Recorded failure",simulated:"≈ Simulated boundary",unproven:"? Not proven"}[proof.state]));
      button.title = `${proof.fact}\n${proof.classification}\nDoes not prove: ${proof.does_not_prove}`;
      button.disabled = !proof.step_id;
      button.onclick = () => { const step=this.session.steps.find(item=>item.step_id===proof.step_id); if(step)this.selectStep(step); };
      row.append(button); list.append(row);
    }
    const uncertain = ["UNKNOWN_OUTCOME","REQUIRES_INTERVENTION"].includes(this.session.status);
    const business = this.session.current_stage === 20 && this.session.status === "RETRYABLE_FAILURE";
    this.el("integration-recovery").hidden = !uncertain && !business;
    this.el("integration-recovery-title").textContent = uncertain ? "Robot outcome not yet proven · do not retry the pick" : "Business acknowledgement failed · keep physical and business outcomes separate";
    this.el("integration-known").replaceChildren(); this.el("integration-unknown").replaceChildren();
    if(this.session.context?.physical_authorized)this.el("integration-known").append(this.node("li",`Original command ${this.session.command_id} was explicitly authorized.`));
    if(this.session.steps?.some(step => step.stage===16 && step.command_id===this.session.command_id && step.status!=="RECOVERED_NO_DISPATCH"))this.el("integration-known").append(this.node("li","The execution stage recorded an attempt. Its result alone does not prove the physical outcome."));
    for(const proof of proofs){
      const target = proof.state === "unproven" || proof.state === "simulated" ? "integration-unknown" : "integration-known";
      this.el(target).append(this.node("li",`${proof.label}: ${proof.fact}`));
    }
    this.el("integration-recovery-detail").textContent = uncertain
      ? "Reconcile original command: query its evidence and capture the required observation to assess the outcome. This does not create or send a replacement robot command. Inconclusive evidence keeps the outcome unproven."
      : "Retry WMS acknowledgement sends only the business result. It cannot repeat robot execution. Verification above states whether the physical result succeeded or failed.";
  }

  renderPhases() {
    const focusedPhase=document.activeElement?.dataset?.phase;
    const phases = [["ERP / WMS",1,2],["REST / SQL",3,4],["Observe / plan",5,8],["Outbox / edge",9,11],["OPC UA / PLC",12,15],["Robot",16,17],["Verify",18,19],["Business",20,22]];
    const session=this.session, steps=session.steps || [];
    this.el("integration-map").replaceChildren();
    for(const [label,first,last] of phases){
      const current = session.status!=="COMPLETED" && session.current_stage>=first && session.current_stage<=last;
      const inspected = this.selected?.stage>=first && this.selected?.stage<=last;
      const relevant = steps.filter(step=>step.stage>=first && step.stage<=last && (step.stage<=4 || step.stage>=21 || step.job_id===session.job_id));
      const uncertain = ["UNKNOWN_OUTCOME","REQUIRES_INTERVENTION"].includes(session.status) && (current || first===18);
      const failed = relevant.some(step=>step.status==="FAILED" && !relevant.some(later=>later.stage===step.stage && later.sequence>step.sequence && later.status==="COMPLETED"))
        || (session.workbench?.proofs || []).some(proof=>proof.state==="failed" && relevant.some(step=>step.step_id===proof.step_id));
      const visited = !failed && !uncertain && Array.from({length:last-first+1},(_,i)=>first+i).every(stage=>relevant.some(step=>step.stage===stage && step.status==="COMPLETED"));
      const item=this.node("li"), button=this.node("button",undefined,"secondary"); button.type="button";
      button.dataset.phase=String(first);
      if(current)item.setAttribute("aria-current","step");
      item.classList.toggle("visited",visited); item.classList.toggle("inspected",inspected); item.classList.toggle("uncertain",uncertain); item.classList.toggle("failed",failed);
      button.append(this.node("strong",label),this.node("small",[current?"Execution now":visited?"Stages recorded":"",inspected?"Inspecting":"",uncertain?"Uncertain":failed?"Failed attempt":""].filter(Boolean).join(" · ")));
      button.setAttribute("aria-pressed",String(this.phase===first));
      button.onclick=()=>{this.phase=this.phase===first?null:first;this.phaseEnd=last;const candidate=relevant.at(-1);if(candidate)this.selectStep(candidate);else{this.renderTrace();this.renderPhases();}};
      item.append(button);this.el("integration-map").append(item);
      if(focusedPhase===String(first))button.focus({preventScroll:true});
    }
  }

  renderTrace() {
    const focusedStep=document.activeElement?.dataset?.stepId;
    const steps=this.session.steps || [], attempts=new Map(), totals=new Map();
    const key=step=>`${step.job_id || ""}:${step.stage}:${step.component || ""}`;
    for(const step of steps)totals.set(key(step),(totals.get(key(step)) || 0)+1);
    for(const [name,field] of [["status","status"],["component","component"],["protocol","protocol"]]){
      const select=this.el(`integration-${name}-filter`),previous=select.value || "all";
      select.replaceChildren();
      for(const value of ["all",...new Set(steps.map(step=>step[field]).filter(Boolean))]){
        const option=this.node("option",value==="all"?`All ${name === "status"?"statuses":name+"s"}`:value);option.value=value;select.append(option);
      }
      select.value=previous;
    }
    const search=this.el("integration-search").value.toLowerCase(),perspective=this.el("integration-perspective").value;
    const ranges={business:[[1,4],[20,22]],messaging:[[8,12]],controller:[[12,17]],verification:[[18,20]]};
    this.el("integration-events").replaceChildren();let shown=0;
    const traceButtons=[];
    for(const step of steps){
      const attempt=(attempts.get(key(step)) || 0)+1;attempts.set(key(step),attempt);
      const delivery=step.output?.redelivery || step.output;
      const repeat=this.el("integration-repeat-filter").value;
      if(this.phase && (step.stage<this.phase || step.stage>this.phaseEnd))continue;
      if(ranges[perspective] && !ranges[perspective].some(([first,last])=>step.stage>=first&&step.stage<=last))continue;
      if(search && !JSON.stringify(step).toLowerCase().includes(search))continue;
      if(["status","component","protocol"].some(name=>{const value=this.el(`integration-${name}-filter`).value;return value&&value!=="all"&&step[name]!==value;}))continue;
      if(repeat==="failed"&&step.status!=="FAILED")continue;
      if(repeat==="repeated"&&totals.get(key(step))<2&&!(delivery?.deliveries>1)&&!delivery?.redelivered)continue;
      shown++;
      const row=this.node("li"),button=this.node("button",undefined,"integration-event secondary");button.type="button";button.dataset.stage=step.stage;button.dataset.stepId=step.step_id;
      const selected=this.selected?.step_id===step.step_id;
      button.setAttribute("aria-pressed",String(selected));
      const current=step.stage===this.session.current_stage && step.job_id===this.session.job_id && this.session.status!=="COMPLETED";
      button.append(this.node("strong",`${String(step.sequence || step.stage).padStart(2,"0")}  ${step.title}`),this.node("span",`${step.status} · ${step.protocol || ""} · ${step.classification || "UNAVAILABLE"}`));
      if(selected||current)button.append(this.node("span",[current?"Execution boundary":"",selected?"Inspecting":""].filter(Boolean).join(" · "),"integration-marker"));
      button.append(this.node("small",`${step.timestamp || ""} · ${Number(step.duration_ms || 0).toFixed(1)} ms`));
      let label=`${attempt>1?"Repeated stage · ":""}Attempt ${attempt}`;
      if(Number.isInteger(delivery?.deliveries))label+=` · Deliveries ${delivery.deliveries}${delivery.deliveries>1?" · original command identity":""}`;
      if(delivery?.redelivered===true)label+=" · broker redelivery";
      button.append(this.node("small",label,"integration-attempt"));
      button.onclick=()=>this.selectStep(step);row.append(button);this.el("integration-events").append(row);
      traceButtons.push(button);
      button.onkeydown=event=>{
        const index=traceButtons.indexOf(button);
        const next=event.key==="ArrowDown"?Math.min(index+1,traceButtons.length-1):event.key==="ArrowUp"?Math.max(index-1,0):event.key==="Home"?0:event.key==="End"?traceButtons.length-1:null;
        if(next===null)return;event.preventDefault();traceButtons[next].focus();traceButtons[next].onclick();
      };
      if(focusedStep===step.step_id)button.focus({preventScroll:true});
    }
    const traceStop=traceButtons.find(button=>button.dataset.stepId===this.selected?.step_id)||traceButtons[0];
    for(const button of traceButtons)button.setAttribute("tabindex",button===traceStop?"0":"-1");
    this.el("integration-trace-count").textContent=`${shown} of ${steps.length} saved attempts${this.phase?" · phase filter active":""}.${shown?" Use Up/Down to move between saved steps.":" No matches. Clear the search or select Show all stages."}`;
    if(!this.pinned)this.el("integration-events").scrollTop=this.el("integration-events").scrollHeight;
  }

  inspect() {
    const step=this.selected,session=this.session;
    const sourceKey = `${session.session_id}/${step?.step_id}`;
    if(this.sourceDocument && this.sourceDocument.key !== sourceKey){this.sourceDocument=null;this.sourceMode="recorded";}
    const inspected = `Inspecting ${step ? `step ${step.stage}` : "no saved step"} · ${this.pinned ? "historical evidence" : "following latest saved step"}`;
    this.el("integration-current-inspection").textContent=inspected;
    this.el("integration-cursor-text").textContent=`${session.order_id || "Order not created"}\nExecution now: ${session.status==="COMPLETED"?"journey finished":`step ${session.current_stage}`} · ${session.workbench?.status || session.status}\n${inspected}\nOriginal command: ${session.command_id || "not created"}`;
    for(const button of this.el("integration-tabs").children){
      const active=button.textContent===this.tab;
      button.setAttribute("aria-selected",String(active));button.setAttribute("tabindex",active?"0":"-1");
      button.setAttribute("aria-controls",["Protocol","Records","Decisions","Run info"].includes(button.textContent)?"integration-engineering":"integration-inspector");
      if(active)this.el(this.engineeringTab()?"integration-engineering":"integration-inspector").setAttribute("aria-labelledby",button.id);
    }
    this.el("integration-inspector-title").textContent=step?`Step ${step.stage} · ${step.title}`:"No persisted stage yet";
    this.el("integration-inspection-position").textContent=this.pinned
      ? `Inspecting historical evidence · execution ${session.status==="COMPLETED"?"has finished":`is at step ${session.current_stage}`}. Selection does not move execution.`
      : `Following the latest saved result · ${session.status==="COMPLETED"?"journey finished":`execution is at step ${session.current_stage}`}. A pending stage has no result until it runs.`;
    for(const id of ["integration-follow", "integration-follow-mobile"]){
      const button = this.el(id);
      button.textContent = this.pinned ? "Follow latest step" : "Latest step selected";
      button.disabled = !this.pinned;
      button.title = this.pinned ? "Return the inspector to the latest saved step and follow new results. Does not run anything." : "The inspector already follows the latest saved step. Select an earlier step to inspect history.";
    }
    this.el("integration-robot-context").textContent=`Execution now: ${session.current_stage} · Inspecting: ${step?.stage || "none"} · Replay target: original command ${session.command_id || "not created"}.`;
    const overview=this.el("integration-overview");overview.replaceChildren();
    const sourceView = this.tab === "Source";
    this.el("integration-source").hidden = !sourceView;
    this.el("integration-inspector").classList.toggle("python-source", sourceView);
    this.el("integration-payload-summary").textContent = sourceView ? "Python source · read-only" : "Technical record · expand or collapse · read-only";
    let content="Execute a permitted stage to save its evidence.";
    if(step){
      const explanation=session.workbench?.stages?.[step.step_id] || {};
      const identities=[["Order",step.order_id],["Job",step.job_id],["Original command",step.command_id],["Request",step.input?.request_id]].filter(([,value])=>value).map(([label,value])=>`${label}: ${value}`).join("\n");
      const fields=[["What happened",explanation.what || step.summary],["Responsible",`${step.component} · ${step.classification || "UNAVAILABLE"} · ${step.protocol}`],["Important input",identities || "No input identity recorded."],["Changed",explanation.changed || `${step.state_before} → ${step.state_after}`],["Saved as / persisted in",explanation.saved || step.persistence_effect],["This proves",explanation.proves || "Only the saved result of this attempt."],["Supporting records",`Step ${step.step_id}\n${(step.evidence_ids || []).join("\n") || "No further evidence IDs recorded."}`],["This does not prove",explanation.does_not_prove || "Later boundaries or missing evidence."],["Why this boundary exists",step.invariant],["Recovery",explanation.recovery || step.failure_semantics]];
      for(const [label,value] of fields){overview.append(this.node("dt",label),this.node("dd",value || "Unavailable"));}
      const claims=(session.workbench?.proofs || []).filter(proof=>proof.step_id===step.step_id);
      for(const proof of claims)overview.append(this.node("dt",`${proof.label} · ${proof.state}`),this.node("dd",`${proof.fact}\nSource: ${proof.field}. Does not prove: ${proof.does_not_prove}`));
      const views={Data:{input:step.input,output:step.output},State:{before:step.state_before,after:step.state_after,persistence_effect:step.persistence_effect,revision:step.revision},Protocol:{classification:step.classification,protocol:step.protocol,note:"Structured adapter request/result; not a packet capture.",record:step.wire},Source:step.source,Recovery:{guidance:explanation.recovery,persisted_failure_semantics:step.failure_semantics},"Raw JSON":step};
      content=JSON.stringify(views[this.tab],null,2);
      if(this.tab==="Recovery"){
        const later=(session.steps||[]).find(item=>item.stage===step.stage&&item.job_id===step.job_id&&item.sequence>step.sequence&&item.status==="COMPLETED");
        const context=step.status==="FAILED"&&later
          ? `This attempt failed. A later attempt completed step ${step.stage}; no retry is needed for this saved failure.`
          : this.pinned ? "You are reviewing an earlier step. Use the current execution status for the next permitted action." : "This is the latest saved step. The current execution controls show which action is permitted.";
        const reason=step.stage===20&&step.status==="FAILED"?"The attempt to notify the warehouse system failed. Review Verification for the physical result.":step.summary;
        content=`${context}\n\nWhat happened\n${reason||"No explanation was recorded."}\n\nGuidance recorded for this boundary\n${explanation.recovery||step.failure_semantics||"No recovery guidance was recorded."}\n\nExact records remain available in Raw JSON.`;
      }
    }
    if(sourceView){
      const source = this.sourceDocument;
      const current = this.sourceMode === "current" && source?.key === sourceKey;
      this.el("integration-source-identity").textContent = `${step?.source?.path || "Source path unavailable"}\n${step?.source?.symbol || "Function unavailable"}`;
      if(current && source?.path)this.el("integration-source-identity").textContent = `${source.path}\n${source.symbol || ""}${source.role ? `\n${source.role}` : ""}`;
      this.el("integration-source-excerpt").setAttribute("aria-pressed",String(!current));
      this.el("integration-source-full").setAttribute("aria-pressed",String(current));
      this.el("integration-source-full").disabled = !step?.source?.path;
      this.el("integration-source-full").setAttribute("aria-disabled",String(!step?.source?.path || current && source.status === "loading"));
      this.el("integration-source-full").setAttribute("aria-busy",String(current && source.status === "loading"));
      content = step?.source?.excerpt || "No Python excerpt was saved for this step.";
      let note = "Python excerpt saved with this execution step. The full file is available separately as current reference code.";
      if(current){
        content = source.status === "available" ? source.content : source.status === "loading" ? "Loading Python file…" : "Full Python file unavailable. Select Full Python file to retry, or Saved excerpt to inspect the recorded code.";
        note = source.status === "available"
          ? `${source.scope}\n${source.line_count} lines${source.excerpt_start_line ? ` · saved excerpt matches at line ${source.excerpt_start_line}` : " · saved excerpt not found in the current file"}.\nDisplayed file SHA-256: ${source.displayed_sha256}`
          : source.status === "loading" ? "Reading the current file. This does not execute Python or change the run." : source.reason || "Source unavailable.";
        if(source.component && source.component !== "entry" && source.status === "available")note = `${source.scope}\n${source.line_count} lines · ${source.symbol}${source.symbol_start_line ? ` at line ${source.symbol_start_line}` : " (symbol location unavailable)"}.\nDisplayed file SHA-256: ${source.displayed_sha256}`;
      }
      this.el("integration-source-note").textContent = note;
    }
    this.sourceHighlightNode = null;
    this.el("integration-source-highlight").hidden = true;
    this.el("integration-inspector").replaceChildren();
    this.el("integration-inspector").textContent=content || "No value recorded.";
    if(sourceView && this.sourceMode === "current" && this.sourceDocument?.key === sourceKey && this.sourceDocument.status === "available")this.renderSourceLines(this.sourceDocument);
    this.renderEngineering();
    if(this.engineeringTab() && this.selected && this.engineeringDocument?.key !== this.engineeringKey())this.loadEngineering();
    const job=step?.job_id || session.job_id,link=this.el("integration-evidence");
    link.hidden=!job;this.el("integration-investigate").hidden=!job;
    if(job)link.href=this.path(`/jobs/${encodeURIComponent(job)}/evidence`);
    globalThis.robotWorkspace?.update(globalThis.robotWorkspace.test,session,step,this.tab,this.sourceMode==="current"?this.sourceDocument:null);
  }
}
globalThis.IntegrationConsole = IntegrationConsole;
