"use strict";

// This view renders server records. It never invents execution or protocol events.
class IntegrationConsole {
  constructor({request, path, readOnly, update, physical, activity}) {
    Object.assign(this, {request, path, readOnly, update, physical, activity});
    this.session = null;
    this.busy = false;
    this.generation = 0;
    this.socket = null;
    this.retry = null;
    this.liveTimer = null;
    this.pollingLive = false;
    this.selected = null;
    this.pinned = false;
    this.tab = "What";
    this.el = id => document.getElementById(id);
    this.el("integration-advance").onclick = () => this.advance();
    this.el("integration-reconcile").onclick = () => this.reconcile();
    this.el("integration-return").onclick = () => this.focus();
    this.el("integration-history").onchange = async event => {
      const generation=++this.generation;
      this.disconnect();
      try {
        const saved=await this.request(`/integration/sessions/${event.target.value}`);
        if(generation!==this.generation)return;
        this.accept(saved);this.watch();
      }
      catch (error) { if(generation===this.generation)this.error(error); }
    };
    for (const tab of ["What", "Wire", "Code", "State", "Why", "Failure semantics"]) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = tab;
      button.className = "secondary";
      button.setAttribute("role", "tab");
      button.onclick = () => { this.tab = tab; this.inspect(); };
      this.el("integration-tabs").append(button);
    }
  }

  async load() {
    const generation = ++this.generation;
    this.disconnect();
    this.session = null;
    this.selected = null; this.pinned = false;
    this.el("integration-console").hidden = true;
    const sessions = await this.request("/integration/sessions");
    if (generation !== this.generation) return;
    const items = (Array.isArray(sessions) ? sessions : sessions.sessions)?.slice().sort((a,b) => a.created_at.localeCompare(b.created_at));
    this.el("integration-history").replaceChildren();
    for (const item of items || []) {
      const option = document.createElement("option");
      option.value = item.session_id;
      option.textContent = `${item.order_id || item.session_id} · ${item.status}`;
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
    if(this.liveTimer)clearTimeout(this.liveTimer);
    this.liveTimer=null;
    this.session = null;
    this.el("integration-console").hidden = true;
    this.el("integration-live").hidden = true;
  }

  async start(request, fault) {
    const session = await this.request("/v1/wms/tasks", {
      request, request_id: crypto.randomUUID(), fault, mode: "guided"
    });
    this.accept(session);
    const option = document.createElement("option");
    option.value = session.session_id;
    option.textContent = `${session.order_id || request.order_id} · ${session.status}`;
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
    const url = new URL(this.path(`/integration/sessions/${this.session.session_id}/stream`), location.href);
    url.protocol = location.protocol === "https:" ? "wss:" : "ws:";
    this.socket = new WebSocket(url);
    this.socket.onmessage = event => {
      if (generation !== this.generation) return;
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
    if(this.session?.session_id !== session.session_id){this.selected=null;this.pinned=false;}
    this.session = session;
    this.render();
    if(session.current_stage>=16 && session.command_id && !this.liveTimer && !this.pollingLive)this.pollLive();
  }

  async pollLive() {
    if(!this.session?.command_id || this.pollingLive)return;
    this.pollingLive=true;
    const generation=this.generation,sessionId=this.session.session_id;
    try{
      const live=await this.request(`/integration/sessions/${sessionId}/live`);
      if(generation!==this.generation || sessionId!==this.session?.session_id)return;
      this.el("integration-protocol-live").textContent=JSON.stringify(live,null,2);
    }catch(error){
      if(generation===this.generation)this.el("integration-protocol-live").textContent=`Protocol evidence unavailable: ${error.message}. This read does not establish an execution outcome.`;
    }finally{
      this.pollingLive=false;
      if(generation===this.generation && this.session?.current_stage===16){
        this.liveTimer=setTimeout(()=>{this.liveTimer=null;this.pollLive();},500);
      }
    }
  }

  focus() { this.el("integration-console").scrollIntoView({block: "start", behavior: "auto"}); }
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
    this.render();
    const result = await this.request(`/integration/sessions/${value.session_id}/authorize`, {
      request_id: crypto.randomUUID(), expected_revision: value.revision,
      stage: value.current_stage, decision: "approve"
    });
    this.accept(result);
  }

  async reconcile() {
    if (this.busy || !this.session || this.readOnly()) return;
    this.busy = true; this.activity(true); this.render(); this.el("integration-error").textContent = "";
    try {
      this.accept(await this.request(`/integration/sessions/${this.session.session_id}/reconcile`, {
        request_id: crypto.randomUUID(), expected_revision: this.session.revision,
        fault: document.getElementById("observation").value || null
      }));
      await this.update(this.session);
    } catch (error) { this.error(error); }
    finally { this.busy = false; this.activity(false); this.render(); }
  }

  render() {
    const session = this.session;
    if (!session) return;
    this.el("integration-console").hidden = false;
    this.el("integration-history").value = session.session_id;
    for (const option of this.el("integration-history").children) {
      if (option.value === session.session_id) option.textContent = `${session.order_id || session.session_id} · ${session.status}`;
    }
    this.el("integration-state").textContent = `${session.status} · revision ${session.revision}`;
    this.el("integration-ids").textContent = [
      ["Session", session.session_id], ["Correlation", session.correlation_id],
      ["Order", session.order_id], ["Job", session.job_id], ["Command", session.command_id]
    ].map(([key, value]) => `${key}: ${value || "not created"}`).join("\n");
    const stage = session.current_stage;
    this.el("integration-live").hidden=!(stage>=16 && session.context?.physical_authorized);
    const phases = [
      ["ERP / WMS", 1, 2], ["REST / SQL", 3, 4], ["Observe / plan", 5, 8],
      ["Outbox / edge", 9, 11], ["OPC UA / PLC", 12, 15],
      ["Robot", 16, 17], ["Verify", 18, 19], ["Business", 20, 22]
    ];
    this.el("integration-map").replaceChildren();
    for (const [label, first, last] of phases) {
      const item = document.createElement("li");
      item.textContent = label;
      if (stage >= first && stage <= last) item.setAttribute("aria-current", "step");
      if (stage > last) item.className = "visited";
      this.el("integration-map").append(item);
    }
    const pending = session.pending_authorization;
    const current = session.steps?.find(step => step.stage === stage);
    const unproven = ["UNKNOWN_OUTCOME", "REQUIRES_INTERVENTION"].includes(session.status);
    this.el("integration-pending-title").textContent = unproven ? "Outcome unproven · reconciliation required" : pending?.title || current?.title || session.status;
    this.el("integration-pending-detail").textContent = unproven
      ? "The physical outcome is unproven. Reconcile queries the original command journal and fresh observation; it does not issue a new pick. Business completion remains blocked until verification and WMS acknowledgement."
      : stage === 15
      ? "This permits the original command to change the synthetic world. A lost response must be reconciled using its journal; it must never trigger a fresh pick. This is not a safety function."
      : pending?.summary || "Continue executes one bounded backend stage and saves its result. Waiting and viewing do not execute work.";
    this.el("integration-advance").textContent = this.busy ? "Executing bounded stage…"
      : unproven ? "Awaiting reconciliation" : stage === 15 ? "AUTHORIZE ROBOT EXECUTION" : pending?.label || `Continue · stage ${stage}`;
    this.el("integration-advance").disabled = this.busy || this.readOnly() || unproven || !pending;
    this.el("integration-pending").classList.toggle("physical-gate", stage === 15);
    const uncertain = ["UNKNOWN_OUTCOME", "REQUIRES_INTERVENTION", "EXECUTING_STAGE"].includes(session.status);
    this.el("integration-reconcile").textContent = session.status === "EXECUTING_STAGE" ? "Recover interrupted stage" : "Reconcile original command";
    this.el("integration-reconcile").hidden = !uncertain;
    this.el("integration-reconcile").disabled = this.busy || this.readOnly();
    this.el("integration-history").disabled = this.busy;
    this.el("integration-events").replaceChildren();
    for (const step of session.steps || []) {
      const row = document.createElement("li");
      const button = document.createElement("button");
      button.className = "integration-event secondary";
      button.dataset.stage = step.stage;
      const title = document.createElement("strong");
      title.textContent = `${String(step.sequence || step.stage).padStart(2, "0")}  ${step.title}`;
      const info = document.createElement("span");
      info.textContent = `${step.status} · ${step.protocol || "REAL CODE"} · ${step.classification || step.truth || ""}`;
      const timing = document.createElement("small");
      timing.textContent = `${step.timestamp || ""} · ${Number(step.duration_ms || 0).toFixed(1)} ms`;
      button.append(title, info, timing);
      button.onclick = () => { this.selected = step; this.pinned = true; this.inspect(); };
      row.append(button); this.el("integration-events").append(row);
    }
    if (session.steps?.length) {
      const previous = this.selected;
      this.selected = (this.pinned && session.steps.find(step => step.step_id === previous?.step_id)) || session.steps.at(-1);
    }
    this.inspect();
    if (stage > 16) {
      this.el("integration-live-state").textContent = `Recorded controller stage complete · ${session.status}. Continue with fresh observation and business reconciliation.`;
    }
  }

  inspect() {
    const step = this.selected;
    for (const button of this.el("integration-tabs").children) button.setAttribute("aria-selected", String(button.textContent === this.tab));
    this.el("integration-inspector-title").textContent = step ? `${step.stage}. ${step.title}` : "Select a persisted stage";
    let content = "Executed stage evidence will appear here.";
    if (step) {
      const views = {
        What: {summary: step.summary, component: step.component, protocol: step.protocol, classification: step.classification, status: step.status, evidence_ids: step.evidence_ids},
        Wire: {wire: step.wire, input: step.input, output: step.output},
        Code: step.source || {path: step.source_path, symbol: step.source_symbol, excerpt: step.source_excerpt},
        State: {before: step.state_before, after: step.state_after, persistence_effect: step.persistence_effect, revision: step.revision},
        Why: step.invariant,
        "Failure semantics": step.failure_semantics
      };
      content = typeof views[this.tab] === "string" ? views[this.tab] : JSON.stringify(views[this.tab], null, 2);
    }
    this.el("integration-inspector").textContent = content || "No value recorded.";
    const link = this.el("integration-evidence");
    link.hidden = !this.session?.job_id;
    if (this.session?.job_id) link.href = this.path(`/jobs/${this.session.job_id}/evidence`);
  }
}
globalThis.IntegrationConsole = IntegrationConsole;
