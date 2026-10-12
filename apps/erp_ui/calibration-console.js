"use strict";

// Presentation of persisted Python measurements and lifecycle decisions. No solver
// or approval decision belongs here. Inspection and navigation issue GETs only.
class CalibrationConsole {
  constructor({request, path, readOnly, activity, changed, run, workspace, overlay, geometry}) {
    Object.assign(this, {request, path, readOnly, activity, changed, run, workspace, overlay, geometry});
    this.geometryGeneration=0;this.geometryMode="cell";
    this.generation = 0; this.selectionGeneration = 0; this.sourceGeneration = 0; this.pixelGeneration=0;
    this.test = null; this.overview = null; this.records = []; this.camera = null;
    this.selected = null; this.busy = false; this.pending = null;
    this.el = id => document.getElementById(id);
    const card = document.createElement("section");
    card.id = "calibration-console"; card.hidden = true;
    card.setAttribute("aria-labelledby", "calibration-title");
    card.innerHTML = `<h2 id="calibration-title">Calibrate the cell</h2>
      <p id="calibration-introduction" class="muted">Measure where each camera is relative to the robot, check the result, then explicitly approve it for this simulation.</p>
      <label for="calibration-camera">Camera</label><select id="calibration-camera"></select>
      <p id="calibration-state"></p><p id="calibration-next"></p>
      <form id="calibration-action-form"><div id="calibration-approval" hidden><label for="calibration-actor">Your name for simulated approval</label><input id="calibration-actor" name="simulated-approval-actor" autocomplete="name" maxlength="100"><p class="muted">Approval applies only to this candidate, camera configuration and simulation.</p></div>
      <button id="calibration-action" type="submit">Loading calibration…</button></form>
      <p id="calibration-feedback" role="status" aria-live="polite"></p>
      <p id="calibration-error" role="alert"></p>
      <button id="calibration-check" class="secondary" hidden>Check saved request</button>
      <button id="calibration-inspect" class="secondary">Inspect calibration evidence</button>
      <details id="calibration-checks"><summary>Checks and controlled recovery</summary><p class="muted">Routine references measure combined camera/depth accuracy. They do not verify tool geometry, and a passing check cannot restore a suspect approval.</p><button id="calibration-routine" class="secondary">Measure routine references</button><button id="calibration-new-measurements" class="secondary">Start new measurements</button><details><summary>Introduce a simulated camera fault</summary><p>Move the selected physical camera 40 mm along base x and rotate it 0.025 radians about base y. Its estimated transform stays unchanged. A recorded mounting-change notice blocks affected targets.</p><button id="calibration-move-camera" class="secondary">Move camera in this simulation</button></details></details>
      <details><summary>Förklara för kunden</summary><p lang="sv">Kameran mäter i sitt eget koordinatsystem. Avståndet till ett föremål räcker inte för att veta var det finns i robotens koordinatsystem. Vi använder bilder av en känd tavla och robotens rapporterade lägen för att beräkna sambandet.</p><p lang="sv">Flera olika vinklar och lägen ger bättre underlag än många nästan identiska bilder. Det är geometrisk parameterberäkning, inte träning genom belöningar. Oberoende mätningar och uttryckliga toleranser avgör om resultatet kan godkännas.</p><p lang="sv">Det här är syntetiska mätningar. Kamerakalibrering garanterar varken att alla föremål känns igen eller att varje grepp lyckas. Verktyg, djupmätning och mekanik behöver egna kontroller.</p></details>`;
    document.querySelector("#run-workspace aside").prepend(card);
    const measurementOptions=document.createElement("details");measurementOptions.id="calibration-measurement-options";measurementOptions.hidden=true;
    measurementOptions.innerHTML=`<summary>Measurement plan and quality experiments</summary><label for="calibration-capture-scenario">Capture plan</label><select id="calibration-capture-scenario"></select><p id="calibration-capture-description"></p><p class="muted">The same acquisition pipeline saves the images, reported poses and rejection decisions for every plan.</p>`;
    this.el("calibration-action").before(measurementOptions);
    this.el("calibration-capture-scenario").onchange=()=>{this.captureScenario=this.el("calibration-capture-scenario").value;this.saveSelection();this.render();};
    const faults=document.createElement("details");faults.id="calibration-faults";
    faults.innerHTML=`<summary>Sensor, board and tool experiments</summary><p>These controls change this isolated simulation. Sensor faults block the selected camera. A shared board change blocks both cameras. Tool faults require a separate tool check. Saved camera estimates remain unchanged.</p><label for="calibration-fault-kind">Experiment or restoration</label><select id="calibration-fault-kind"></select><p id="calibration-fault-description"></p><button id="calibration-fault-apply" class="secondary">Apply selected simulation change</button><button id="calibration-tool-recheck" class="secondary">Measure and verify the tool</button><p class="muted">Restoration does not restore approval. Inspect saved measurements and complete the required checks before execution.</p>`;
    this.el("calibration-checks").append(faults);
    this.el("calibration-fault-kind").onchange=()=>this.renderFault();
    this.el("calibration-fault-apply").onclick=()=>this.auxiliary("faults",{kind:this.el("calibration-fault-kind").value});
    this.el("calibration-tool-recheck").onclick=()=>this.auxiliary("tool-check");
    const reuse=document.createElement("details");reuse.id="calibration-reuse-panel";
    reuse.innerHTML=`<summary>Revalidate a saved estimate</summary><p>Use this after restoring a fault when the camera, board mounting and configuration may still match a saved estimate. It creates an inactive candidate with the same X and Y. New independent measurements and a new explicit approval are required. A moved camera must fail that check.</p><label for="calibration-reuse-artifact">Previously approved estimate</label><select id="calibration-reuse-artifact"></select><p id="calibration-reuse-note" class="muted"></p><button id="calibration-reuse" class="secondary">Reuse as inactive candidate</button></details>`;
    this.el("calibration-checks").append(reuse);
    this.el("calibration-reuse").onclick=()=>this.auxiliary("reuse-estimate",{artifact_id:this.el("calibration-reuse-artifact").value,candidate_id:`candidate-${crypto.randomUUID()}`});
    const images = document.createElement("details"); images.id = "calibration-images"; images.hidden = true; images.open = true;
    images.innerHTML = `<summary>Acquired sensor images</summary><label for="calibration-capture">Saved capture</label><select id="calibration-capture"></select><p id="calibration-capture-note" class="muted"></p><div class="calibration-images"><figure><img id="calibration-rgb" width="960" height="720" loading="lazy" alt=""><figcaption>Actual RGB capture</figcaption></figure><figure><img id="calibration-depth" width="640" height="480" loading="lazy" alt=""><figcaption id="calibration-depth-display">Native depth · display range per image; magenta means missing</figcaption></figure></div><p class="muted">Native depth and RGB have different pixels. Correspondence is computed in Python using the separate camera models.</p><details><summary>Reported robot frames · text alternative to 3D</summary><p>Base coordinates use meters, z up. Camera optical axes are x right, y down, z forward. Each T_A_B maps B into A. This ideal gantry has an orientable flange; it is not an HKM kinematic model.</p><pre id="calibration-machine" tabindex="0" role="region" aria-label="Reported flange, tool and TCP"></pre></details>`;
    this.el("integration-robot").after(images);
    const geometryPanel=document.createElement("div");
    geometryPanel.innerHTML=`<label for="calibration-geometry-mode">3D evidence</label><select id="calibration-geometry-mode"><option value="cell">Cell and command replay</option><option value="capture">Selected capture · saved robot and board</option><option value="poses">Selected capture's plan and accepted poses</option><option value="record">Selected sample, validation or pick target</option></select><p id="calibration-geometry-status" role="status"></p><details><summary>3D evidence · numerical text alternative</summary><pre id="calibration-geometry-numbers" tabindex="0" role="region" aria-label="Saved geometry coordinates and decisions"></pre></details>`;
    images.prepend(geometryPanel);
    this.el("calibration-geometry-mode").onchange=()=>{this.geometryMode=this.el("calibration-geometry-mode").value;this.clearPixel();this.renderImages();this.saveSelection();this.renderGeometry();};
    const pixelPanel=document.createElement("details");pixelPanel.id="calibration-pixel-panel";
    pixelPanel.innerHTML=`<summary>Inspect an RGB pixel and its depth</summary><p>Select a point on the RGB image or enter its pixel coordinates. This reads saved measurements using the selected approved artifact. It does not create a grasp, approve calibration, or move the robot.</p><form id="calibration-pixel-form"><label for="calibration-pixel-u">RGB column (u)</label><input id="calibration-pixel-u" type="number" min="0" step="1" value="480" required><label for="calibration-pixel-v">RGB row (v)</label><input id="calibration-pixel-v" type="number" min="0" step="1" value="360" required><label for="calibration-pixel-mode">Depth correspondence</label><select id="calibration-pixel-mode"><option value="native">Native depth → RGB</option><option value="aligned">RGB registered · native depth meaning retained</option></select><button id="calibration-pixel-inspect" class="secondary">Inspect pixel</button></form><p id="calibration-pixel-status" role="status"></p><p id="calibration-overlay-scope" class="muted"></p><button id="calibration-pixel-clear" class="secondary" type="button" hidden>Clear selected ray</button><details><summary>Pixel calculation · coordinates, depth and transforms</summary><pre id="calibration-pixel-result" tabindex="0" role="region" aria-label="Read-only pixel calculation"></pre></details>`;
    images.append(pixelPanel);
    const artifactLabel=document.createElement("label"),artifactSelect=document.createElement("select");
    artifactLabel.htmlFor="calibration-pixel-artifact";artifactLabel.textContent="Saved artifact for this calculation";
    artifactSelect.id="calibration-pixel-artifact";
    this.el("calibration-pixel-form").prepend(artifactLabel,artifactSelect);
    artifactSelect.onchange=()=>{this.pixel={...(this.pixel||{}),artifact:artifactSelect.value};this.saveSelection();this.clearPixel();};
    for(const key of ["u","v","mode"])this.el(`calibration-pixel-${key}`).addEventListener("input",()=>this.clearPixel());
    this.el("calibration-pixel-form").onsubmit=event=>{event.preventDefault();this.inspectPixel();};
    this.el("calibration-pixel-clear").onclick=()=>{this.clearPixel();this.renderImages();};
    this.el("calibration-rgb").onclick=event=>{
      const image=event.currentTarget,box=image.getBoundingClientRect();
      if(!image.naturalWidth||!box.width||!this.capture)return;
      this.el("calibration-pixel-u").value=Math.max(0,Math.min(image.naturalWidth-1,Math.floor((event.clientX-box.left)*image.naturalWidth/box.width)));
      this.el("calibration-pixel-v").value=Math.max(0,Math.min(image.naturalHeight-1,Math.floor((event.clientY-box.top)*image.naturalHeight/box.height)));
      pixelPanel.open=true;this.saveSelection();this.inspectPixel();
    };
    const evidence = document.createElement("section"); evidence.id = "calibration-evidence"; evidence.hidden = true;
    evidence.setAttribute("aria-labelledby", "calibration-evidence-title");
    evidence.innerHTML = `<h3 id="calibration-evidence-title" tabindex="-1">Calibration evidence</h3><p id="calibration-evidence-context"></p><a id="calibration-export" download>Download evidence bundle (ZIP, includes raw images/depth)</a>
      <label for="calibration-record">Measurement or operation</label><select id="calibration-record"></select>
      <p id="calibration-record-status" role="status"></p><div id="calibration-summary"></div>
      <button id="calibration-investigate" class="secondary">Investigate this evidence</button><p id="calibration-operation-status" role="status" tabindex="-1"></p>
      <details id="calibration-calculations"><summary>Calculation operands and results</summary><pre id="calibration-calculation" tabindex="0" role="region" aria-label="Recorded numerical calculation"></pre></details>
      <details id="calibration-source"><summary>Source</summary><p id="calibration-source-scope" class="muted"></p><div class="source-modes"><button id="calibration-excerpt" class="secondary" aria-pressed="true">Saved excerpt</button><button id="calibration-full" class="secondary" aria-pressed="false">Full Python file</button></div><div id="calibration-component-control" hidden><label for="calibration-component">Choose component code</label><select id="calibration-component"></select></div><pre id="calibration-source-content" tabindex="0" role="region" aria-label="Python source"></pre></details>
      <details><summary>Protocol · actual HTTP and in-process calls</summary><p>HTTP records contain the received request and generated response. Python call records contain recorded inputs, results, timing and source. Response generation does not prove the client received it.</p><pre id="calibration-protocol" tabindex="0" role="region" aria-label="Calibration protocol"></pre></details>
      <details><summary>Records and run info · full saved JSON</summary><p id="calibration-record-identity" class="muted"></p><pre id="calibration-record-json" tabindex="0" role="region" aria-label="Calibration record JSON"></pre></details><details><summary>Reproduce from saved images in Python</summary><p>Download the evidence ZIP above. From this repository, this command verifies hashes and reruns corner detection, PnP and fitting. It does not approve calibration or execute a pick. It reports if the current source differs from the saved run.</p><pre tabindex="0" role="region" aria-label="Reproduction command">uv run --locked python -m tools.calibration reproduce --bundle calibration-evidence.zip</pre></details>`;
    this.el("evidence-empty").after(evidence);
    this.el("calibration-camera").onchange = () => { this.camera = this.el("calibration-camera").value; ++this.selectionGeneration; this.selected = null; this.saveSelection(); this.render(); this.renderRecords(); };
    this.el("calibration-action-form").onsubmit = event => { event.preventDefault(); this.act(); };
    this.el("calibration-inspect").onclick = () => this.inspect();
    this.el("calibration-check").onclick = () => this.checkPending();
    this.el("calibration-routine").onclick = () => this.auxiliary("routine-check");
    this.el("calibration-move-camera").onclick = () => this.auxiliary("move-camera");
    this.el("calibration-new-measurements").onclick = () => this.auxiliary("begin-measurements");
    this.el("calibration-capture").onchange = () => { this.capture = this.el("calibration-capture").value; this.saveSelection(); this.renderImages(); this.renderGeometry(); };
    this.el("calibration-record").onchange = () => { this.selected = this.el("calibration-record").value; this.saveSelection(); this.selectRecord(); };
    this.el("calibration-investigate").onclick = () => {const [kind,identity]=String(this.selected||"").split("/");this.auxiliary("investigate",{kind,identity});};
    this.el("calibration-excerpt").onclick = () => this.showSource(false);
    this.el("calibration-full").onclick = () => this.showSource(true);
    this.el("calibration-component").onchange = () => this.showSource(true);
  }
  text(id, value) { const node = this.el(id); if (node.textContent !== value) node.textContent = value; }
  json(id, value) { this.text(id, value ? JSON.stringify(value, null, 2) : "No recorded values for this selection."); }
  storage(key, value) { try { if (value === undefined) return JSON.parse(sessionStorage.getItem(key) || "null"); sessionStorage.setItem(key, JSON.stringify(value)); } catch { /* Browser storage is optional; server evidence remains authoritative. */ } return null; }
  saveSelection() { if (this.test) this.storage(`calibration-selection:${this.test}`, {camera: this.camera, selected: this.selected, capture: this.capture, pixel:this.pixel, captureScenario:this.captureScenario,geometryMode:this.geometryMode}); }
  clear(test = null) {
    ++this.generation; ++this.selectionGeneration; ++this.sourceGeneration;
    this.test = test; this.overview = null; this.records = []; this.selected = null; this.capture = null; this.camera = null;
    this.captureScenario="varied";
    this.clearGeometry();
    this.clearPixel();this.pixel=null;
    this.pending = test ? this.storage(`calibration-pending:${test}`) : null;
    this.pendingReceiptMissing = false;
    Object.assign(this, test ? this.storage(`calibration-selection:${test}`) || {} : {});
    if(this.pixel){for(const key of ["u","v","mode"])if(this.pixel[key]!==undefined)this.el(`calibration-pixel-${key}`).value=this.pixel[key];}
    this.workspace.calibrationAvailable = false;
    for (const id of ["calibration-console", "calibration-images", "calibration-evidence"]) this.el(id).hidden = true;
    this.text("calibration-error", ""); this.text("calibration-feedback", "");
  }
  async load(test = this.test) {
    if (test !== this.test) this.clear(test);
    if (!test) return;
    const generation = ++this.generation;
    try {
      const overview = await this.request("/calibration");
      if (generation !== this.generation) return;
      this.overview = overview;
      this.workspace.calibrationAvailable = !!overview.supported;
      if (!overview.supported) { this.render(); return; }
      const records = await this.request("/calibration/records");
      if (generation !== this.generation) return;
      this.records = records;
      if (!overview.cameras.some(item => item.camera_id === this.camera)) this.camera = overview.cameras[0].camera_id;
      this.options("calibration-camera", overview.cameras.map(item => [item.camera_id, item.camera_id]), this.camera);
      this.render(); this.renderRecords(); this.changed();
    } catch (error) {
      if (generation === this.generation) { this.text("calibration-error", `Cannot load calibration: ${error.message}. Reload to check saved state.`); this.overview = null; this.render(); }
    }
  }
  async inspect() {
    this.workspace.show("inspect", true);
    this.el("calibration-evidence-title").focus();
    this.text("calibration-record-status", "Checking for newly recorded evidence…");
    await this.load();
  }
  options(id, values, selected) {
    const node = this.el(id), signature = JSON.stringify(values);
    if (node.dataset.options !== signature) { node.replaceChildren(...values.map(([value, label]) => new Option(label, value))); node.dataset.options = signature; }
    if (values.some(([value]) => value === selected)) node.value = selected;
  }
  state() { return this.overview?.states?.find(item => item.camera.camera_id === this.camera); }
  step() { return this.overview?.next_steps?.[this.camera]; }
  canRun() { return !!this.overview?.supported && Object.values(this.overview.next_steps).some(item => item.action === "run") && !this.pending && !this.busy; }
  renderInvestigation(){const kind=String(this.selected||"").split("/")[0];const available=(this.overview?.investigation_kinds||[]).includes(kind);this.el("calibration-investigate").hidden=!available;this.el("calibration-investigate").disabled=this.busy||!!this.pending||this.readOnly();}
  render() {
    this.renderInvestigation();
    const supported = !!this.overview?.supported;
    this.el("calibration-console").hidden = !supported;
    this.el("calibration-images").hidden = !supported;
    this.el("calibration-evidence").hidden = !supported;
    if (!supported) return;
    const state = this.state(), step = this.step();
    this.el("calibration-introduction").hidden=!!state?.camera;
    this.el("calibration-measurement-options").hidden=step?.action!=="acquire";
    this.options("calibration-capture-scenario",(this.overview.capture_scenarios||[]).map(item=>[item.value,item.label]),this.captureScenario||"varied");
    this.el("calibration-capture-scenario").disabled=this.busy||!!this.pending||this.readOnly();
    this.text("calibration-capture-description",(this.overview.capture_scenarios||[]).find(item=>item.value===this.el("calibration-capture-scenario").value)?.detail||"");
    this.text("calibration-state", `${this.readOnly() ? "Saved, read-only · " : ""}${state?.active_validity || "UNCONFIGURED"} · ${state?.workflow_state || "configure first"}`);
    this.text("calibration-next", step?.detail || "Loading the next permitted action…");
    this.text("calibration-action", this.busy ? "Computing and saving evidence…" : step?.label || "Loading…");
    this.el("calibration-action").disabled = this.busy || this.readOnly() || !!this.pending || !step || ["pending-validation"].includes(step.action);
    if(step?.action === "run" && this.el("create").disabled) {
      this.el("calibration-action").disabled = true;
      this.text("calibration-next", "Calibration is approved. Continue or reconcile the current guided run using its execution controls.");
    }
    this.el("calibration-camera").disabled = this.busy;
    this.el("calibration-approval").hidden = step?.action !== "approve";
    this.el("calibration-actor").required = step?.action === "approve";
    this.el("calibration-check").hidden = !this.pending;
    this.text("calibration-check", this.pendingReceiptMissing ? "Retry the saved request" : "Check saved request");
    this.el("calibration-check").disabled = this.busy || (!!this.pendingReceiptMissing && this.readOnly());
    for (const id of ["calibration-routine", "calibration-move-camera", "calibration-new-measurements"]) this.el(id).disabled = this.busy || !!this.pending || this.readOnly() || !state || (id !== "calibration-new-measurements" && !state.active_artifact_id);
    this.options("calibration-fault-kind",(this.overview.fault_catalogue||[]).map(item=>[item.kind,item.label]),this.el("calibration-fault-kind").value);
    this.el("calibration-fault-apply").disabled=this.busy||!!this.pending||this.readOnly()||!state;
    this.el("calibration-tool-recheck").disabled=this.busy||!!this.pending||this.readOnly()||state?.active_validity!=="VERIFIED";
    const savedEstimates=this.records.filter(item=>item.kind==="artifact"&&item.camera_id===this.camera);
    this.options("calibration-reuse-artifact",savedEstimates.map(item=>[item.id,item.id]),this.el("calibration-reuse-artifact").value);
    this.el("calibration-reuse-artifact").disabled=this.busy||!!this.pending||this.readOnly()||!savedEstimates.length;
    this.el("calibration-reuse").disabled=this.busy||!!this.pending||this.readOnly()||!state||!savedEstimates.length;
    this.text("calibration-reuse-note",savedEstimates.length?"The backend checks configuration compatibility. Old approval is never restored; the keyed board is installed for a new validation.":"No approved estimate is saved for this camera. Measure and validate its first calibration using the main action.");
    this.renderFault();
    this.json("calibration-machine", this.overview.machine);
    this.text("calibration-evidence-context", `${this.camera} · seed ${this.overview.seed} · ${state?.active_artifact_id ? `${state.active_validity === "VERIFIED" ? "Verified active artifact" : "Blocked artifact retained for audit"}: ${state.active_artifact_id}` : "No active approval"}. ${state?.active_validity === "SUSPECT_INVALID" ? "Affected targets are blocked. " : ""}Synthetic measurements; simulation-only limits.`);
    this.el("calibration-export").href = this.path("/calibration/export");
  }
  async act() {
    if (this.busy || this.pending || this.readOnly()) return;
    const step = this.step(), state = this.state();
    if (!step) return;
    if (step.action === "restore-limits") { await this.auxiliary("faults", {kind:"restore_limits"}); return; }
    if (step.action === "select-camera") { this.camera = step.camera_id; this.el("calibration-camera").value = this.camera; this.saveSelection(); this.render(); this.renderRecords(); return; }
    if (step.action === "run") { this.clearPixel(); this.clearGeometry(); this.saveSelection(); this.run(); return; }
    const routes = {configure:"configure", acquire:"acquisitions", fit:"candidates", validate:"validations", approve:"approvals", "tool-check":"tool-check", "begin-measurements":"begin-measurements"};
    if (!routes[step.action]) { this.el("calibration-inspect").click(); return; }
    const identity = crypto.randomUUID();
    const body = {request_id: identity, expected_revision: step.revision};
    if (step.action === "acquire") Object.assign(body,{dataset_id:`fit-${identity}`,scenario:this.el("calibration-capture-scenario").value||"varied"});
    if (step.action === "fit") Object.assign(body, {dataset_id:step.dataset_id, candidate_id:`candidate-${identity}`});
    if (step.action === "validate") Object.assign(body, {dataset_id:`holdout-${identity}`, candidate_id:state.candidate_id});
    if (step.action === "approve") {
      const actor = this.el("calibration-actor").value.trim();
      if (!actor) { this.el("calibration-actor").focus(); this.text("calibration-error", "Enter your name to record simulated approval."); return; }
      Object.assign(body, {candidate_id:state.candidate_id, report_id:state.report_id, actor});
    }
    this.pending = {camera:this.camera, route:`/calibration/cameras/${encodeURIComponent(this.camera)}/${routes[step.action]}`, body};
    this.storage(`calibration-pending:${this.test}`, this.pending);
    await this.sendPending();
  }
  renderFault(){const item=(this.overview?.fault_catalogue||[]).find(item=>item.kind===this.el("calibration-fault-kind").value);this.text("calibration-fault-description",item?`${item.description} ${item.next_action}`:"");}
  async auxiliary(action, payload={}) {
    if (this.busy || this.pending || this.readOnly() || !this.state()) return;
    this.pending = {camera:this.camera, route:`/calibration/cameras/${encodeURIComponent(this.camera)}/${action}`,
      body:{request_id:crypto.randomUUID(), expected_revision:this.state().revision,...payload}};
    this.storage(`calibration-pending:${this.test}`, this.pending); await this.sendPending();
  }
  async sendPending() {
    const pending = this.pending, generation = this.generation, test = this.test;
    if (!pending || this.busy) return;
    this.pendingReceiptMissing = false;
    const returnFocus = document.activeElement;
    this.busy = true; this.activity(true); this.render(); this.text("calibration-error", "");
    this.text("calibration-feedback", "Python is processing measurements. The result will be saved before the next step is enabled.");
    this.text("calibration-operation-status", "Python is processing the request. The recorded result will appear here.");
    try {
      const receipt = await this.request(pending.route, pending.body);
      if (generation !== this.generation || test !== this.test) return;
      this.pending = null; this.storage(`calibration-pending:${test}`, null);
      this.text("calibration-feedback", `${receipt.operation} saved · revision ${receipt.state.revision}.`);
      this.text("calibration-operation-status", `${receipt.operation} saved. Inspection never authorizes robot execution.`);
      if(receipt.operation==="investigate"&&this.selected===`${pending.body.kind}/${pending.body.identity}`)this.selected=`investigation/${receipt.record_ids[0]}`;
      await this.load();
      if(receipt.operation==="investigate")this.el("calibration-operation-status").focus({preventScroll:true});
    } catch (error) {
      if (generation === this.generation) {
        this.text("calibration-operation-status", `${error.message}. The selected evidence is retained. Use Run & watch to inspect the saved request and recovery controls.`);
        if (error.status && error.status < 500) {
          this.pending = null; this.storage(`calibration-pending:${test}`, null);
          this.text("calibration-error", `${error.message}. The server rejected this request. Inspect its records, then use Checks and controlled recovery to collect new measurements if needed.`);
          this.text("calibration-feedback", "Request rejected; no approval was inferred."); await this.load();
        } else { this.text("calibration-error", `${error.message}. Check the saved request before continuing; no second request was sent.`); this.text("calibration-feedback", "Request outcome is unconfirmed in this browser."); }
      }
    } finally {
      this.busy = false; this.activity(false); this.render(); this.changed();
      if (test === this.test && document.activeElement === document.body && returnFocus?.isConnected && !returnFocus.disabled) returnFocus.focus({preventScroll:true});
    }
  }
  async checkPending() {
    const pending = this.pending, generation = this.generation;
    if (!pending || this.busy) return;
    if (this.pendingReceiptMissing) {
      if (!this.readOnly()) await this.sendPending();
      return;
    }
    this.text("calibration-error", "");
    try {
      const receipt = await this.request(`/calibration/operations/${encodeURIComponent(pending.camera)}/${encodeURIComponent(pending.body.request_id)}`);
      if (generation !== this.generation) return;
      this.pending = null; this.storage(`calibration-pending:${this.test}`, null);
      this.text("calibration-feedback", `Saved request found: ${receipt.operation}.`); await this.load();
    } catch (error) {
      if (generation !== this.generation || pending !== this.pending) return;
      if (error.status === 404) {
        this.pendingReceiptMissing = true;
        this.text("calibration-error", "No completed receipt is saved yet. The request may still be processing. You can retry the same saved request; the backend retains its original identity and reuses any saved measurements.");
      } else this.text("calibration-error", `No completed receipt could be confirmed: ${error.message}. Reconnect and check again; no retry was sent.`);
      this.render();
    }
  }
  renderRecords() {
    const records = this.records.filter(item => !item.camera_id || item.camera_id === this.camera);
    const selections = records.filter(item => !["calculation-trace", "validation-reservation"].includes(item.kind));
    this.options("calibration-record", selections.slice().reverse().map(item => [`${item.kind}/${item.id}`, `${item.kind} · ${item.id}`]), this.selected);
    this.selected = this.el("calibration-record").value;
    const captures = records.filter(item => item.kind === "capture");
    this.options("calibration-capture", captures.map(item => [item.id, `${item.partition} · ${item.id}`]), this.capture);
    this.capture = this.el("calibration-capture").value;
    this.renderImages(); this.selectRecord(); this.saveSelection();
  }
  clearGeometry(){++this.geometryGeneration;this.geometrySignature=null;this.geometryMode="cell";if(this.geometryActive)this.geometry?.(null);this.geometryActive=false;this.el("calibration-geometry-mode").value="cell";this.text("calibration-geometry-status","");}
  async renderGeometry(){
    const mode=this.geometryMode||"cell",test=this.test,camera=this.camera,capture=this.capture,selected=this.selected;
    this.el("calibration-geometry-mode").value=mode;
    const signature=JSON.stringify([mode,test,camera,capture,selected]);
    if(signature===this.geometrySignature)return;
    const generation=++this.geometryGeneration;this.geometrySignature=signature;
    this.json("calibration-geometry-numbers",null);
    if(mode==="cell"){if(this.geometryActive)this.geometry?.(null);this.geometryActive=false;this.text("calibration-geometry-status","");return;}
    this.geometryActive=true;this.geometry?.(null);
    const query=new URLSearchParams({camera_id:camera,mode});
    if(mode==="record"){
      const [kind,id]=String(selected||"").split("/");
      if(!["sample","validation","routine-check","runtime-target"].includes(kind)){
        this.text("calibration-geometry-status","Choose a sample, validation, routine check or runtime target in Inspect evidence to see its geometry.");return;
      }
      query.set("record_kind",kind);query.set("record_id",id);
    }else if(capture)query.set("capture_id",capture);
    else{this.text("calibration-geometry-status","Acquire or select a saved board capture first.");return;}
    this.text("calibration-geometry-status","Loading saved 3D evidence…");
    try{
      const result=await this.request(`/calibration/geometry?${query}`);
      if(generation!==this.geometryGeneration||test!==this.test||camera!==this.camera||capture!==this.capture||selected!==this.selected)return;
      this.geometry?.(result);this.text("calibration-geometry-status",`${result.title}. ${result.scope}`);this.json("calibration-geometry-numbers",result.numbers);
    }catch(error){if(generation===this.geometryGeneration){this.geometrySignature=null;this.text("calibration-geometry-status",`Geometry unavailable: ${error.message}. Select a saved board capture or another evidence record. No current geometry was substituted.`);}}
  }
  renderImages() {
    const capture = this.records.find(item => item.kind === "capture" && item.id === this.capture);
    if(this.pixelCapture!==this.capture||this.pixelCamera!==this.camera){this.clearPixel();this.pixelCapture=this.capture;this.pixelCamera=this.camera;}
    const camera=this.overview?.cameras?.find(item=>item.camera_id===this.camera);
    this.el("calibration-pixel-u").max=(camera?.rgb.width||1)-1;this.el("calibration-pixel-v").max=(camera?.rgb.height||1)-1;
    const artifacts=this.records.filter(item=>item.kind==="artifact"&&item.camera_id===this.camera);
    this.options("calibration-pixel-artifact",artifacts.map(item=>[item.id,`${item.id===this.state()?.active_artifact_id?"Current artifact":"Historical artifact"} · ${item.id}`]),this.pixel?.artifact||this.state()?.active_artifact_id);
    this.el("calibration-pixel-inspect").disabled=!capture||!artifacts.length;
    if(!artifacts.length)this.text("calibration-pixel-status","Pixel-to-base inspection becomes available after a calibration has explicit approval.");
    this.text("calibration-capture-note", capture ? `${this.camera} · ${capture.partition} · ${capture.id}. Images are saved measurements, not the browser viewpoint.` : "No images yet. Configure this camera, then acquire board images.");
    this.renderDepthDisplay(capture?.id);
    for (const view of ["rgb", "depth"]) {
      const image = this.el(`calibration-${view}`); image.hidden = !capture;
      if (capture) {
        const hasCorners = view === "rgb" && this.records.some(item => item.kind === "sample" && item.id === capture.id);
        if(hasCorners)this.el("calibration-capture-note").textContent+=" Corner labels show accepted detections; amber crosses marked X show excluded corners when their coordinates were recorded.";
        const src = this.path(`/calibration/captures/${encodeURIComponent(capture.id)}/${hasCorners ? "corners" : view}`);
        if (image.getAttribute("src") !== src) image.src = src;
        image.alt = `${this.camera}, ${capture.partition} capture ${capture.id}, ${hasCorners ? "RGB with detected corner IDs" : view}. Numerical values and rejection reasons are available in Inspect evidence.`;
      } else image.removeAttribute("src");
    }
  }
  async renderDepthDisplay(capture){
    const test=this.test,camera=this.camera,signature=JSON.stringify([test,camera,capture]);
    if(signature===this.depthDisplaySignature)return;
    this.depthDisplaySignature=signature;
    this.text("calibration-depth-display",capture?"Native depth · reading display range…":"Native depth · no saved image");
    if(!capture)return;
    try{
      const result=await this.request(`/calibration/captures/${encodeURIComponent(capture)}/depth-display`);
      if(signature!==this.depthDisplaySignature||test!==this.test||camera!==this.camera||capture!==this.capture)return;
      const range=result.low_raw===null?"no positive finite returns":`${Number(result.low_raw).toFixed(1)}–${Number(result.high_raw).toFixed(1)} raw sensor units (1st–99th percentile; colors clipped outside)`;
      this.text("calibration-depth-display",`Native depth · ${range}. Magenta: ${result.invalid_pixels} nonfinite/nonpositive pixels. Color scale is display only, not a calibrated distance or quality decision.`);
    }catch(error){if(signature===this.depthDisplaySignature&&test===this.test&&camera===this.camera&&capture===this.capture){this.depthDisplaySignature=null;this.text("calibration-depth-display",`Native depth · display range unavailable: ${error.message}. Raw values remain in Records.`);}}
  }
  clearPixel(){
    this.pixelGeneration=(this.pixelGeneration||0)+1;this.overlay?.([]);
    this.text("calibration-pixel-status","");this.text("calibration-overlay-scope","");this.json("calibration-pixel-result",null);
    this.el("calibration-pixel-clear").hidden=true;
  }
  async inspectPixel(){
    this.clearGeometry();
    const artifact=this.el("calibration-pixel-artifact").value;
    if(!this.capture||!artifact||!this.el("calibration-pixel-form").reportValidity())return;
    const generation=++this.pixelGeneration,test=this.test,capture=this.capture,camera=this.camera;
    this.pixel={u:this.el("calibration-pixel-u").value,v:this.el("calibration-pixel-v").value,mode:this.el("calibration-pixel-mode").value,artifact};this.saveSelection();
    const query=new URLSearchParams({u:this.pixel.u,v:this.pixel.v,mode:this.pixel.mode,capture_id:capture,artifact_id:artifact});
    this.text("calibration-pixel-status","Reading saved RGB/depth and computing this correspondence in Python…");
    try{
      const result=await this.request(`/calibration/inspect-pixel?${query}`);
      if(generation!==this.pixelGeneration||test!==this.test||capture!==this.capture||camera!==this.camera)return;
      const measured=result.result;
      this.json("calibration-pixel-result",{scope:result.scope,artifact_id:result.artifact_id,alignment:result.alignment,result:measured});
      this.text("calibration-pixel-status",measured.point?`Base point: ${measured.point.map(value=>Number(value).toFixed(4)).join(", ")} m. A point is not a grasp pose.`:measured.code==="ALIGNED_DEPTH_HOLE"?"This RGB pixel has no depth sample in the registered image. Choose Native depth to inspect nearby projected returns, or select another pixel. No missing values were filled.":`No point: ${measured.code}. ${measured.detail||"Select an interior surface with valid depth and inspect the saved capture."}`);
      this.el("calibration-rgb").src=result.rgb_preview;this.el("calibration-depth").src=result.depth_preview;
      this.text("calibration-overlay-scope",result.overlay_scope);this.overlay?.(result.overlay);
      this.el("calibration-pixel-clear").hidden=false;
    }catch(error){if(generation===this.pixelGeneration)this.text("calibration-pixel-status",`Cannot inspect this pixel: ${error.message}. Choose a matching capture and artifact.`);}
  }
  async selectRecord() {
    this.renderInvestigation();
    const generation = ++this.selectionGeneration, test = this.test, key = this.selected;
    ++this.sourceGeneration; this.savedTrace = null; this.currentRecord = null;
    this.components=[];
    this.options("calibration-component",[],"");
    this.text("calibration-source-scope",key?"Loading source for the selected record…":"No record selected.");
    this.text("calibration-source-content","");
    this.json("calibration-protocol",null);
    this.renderGeometry();
    this.text("calibration-record-status", key ? "Loading saved evidence…" : "No measurements yet. Acquire images in Run & watch.");
    this.el("calibration-summary").replaceChildren(); this.json("calibration-record-json", null); this.json("calibration-calculation", null);
    if (!key) return;
    try {
      const value = await this.request(`/calibration/records/${key.split("/").map(encodeURIComponent).join("/")}`);
      if (generation !== this.selectionGeneration || test !== this.test) return;
      this.currentRecord = value;
      const row = this.records.find(item => `${item.kind}/${item.id}` === key);
      this.text("calibration-record-status", "Saved evidence loaded. Inspecting does not change approval or execute work.");
      this.text("calibration-record-identity", `${key} · SHA-256 ${row?.sha256}`);
      this.json("calibration-record-json", value); this.json("calibration-calculation", value.calculation || value);
      this.summary(value);
      const savedTrace = row?.source_trace_id ? await this.request(`/calibration/records/calculation-trace/${encodeURIComponent(row.source_trace_id)}`) : null;
      if (generation !== this.selectionGeneration || test !== this.test) return;
      this.savedTrace = savedTrace;
      this.json("calibration-protocol", value.classification === "HTTP" ? value : this.savedTrace ? {...this.savedTrace, source:"See Source for saved content"} : {scope:"No instrumented call linked to this record. Its full saved content is under Records.", record:key});
      this.populateSources(); await this.showSource(!!this.fullSource);
    } catch (error) { if (generation === this.selectionGeneration) this.text("calibration-record-status", `Evidence unavailable: ${error.message}. Choose another saved record or reload.`); }
  }
  failureGroups(failures=[]) {
    const labels={CHAIN_RMS_PX:"Robot-chain image error",CHAIN_TRANSLATION_MM:"Robot-chain position error",CHAIN_ROTATION_DEG:"Robot-chain orientation error",REFERENCE_ERROR_MM:"Independent reference error",PNP_RMS_PX:"Board image error",INSUFFICIENT_REFERENCE_COVERAGE:"Reference coverage",MISSING_REQUIRED_LIMITS:"Required acceptance limits"};
    const groups=new Map();
    for(const reason of failures){const code=reason.split(":",1)[0];groups.set(code,(groups.get(code)||0)+1);}
    return [...groups].map(([code,count])=>[labels[code]||code,`${count} recorded failure${count===1?"":"s"}`]);
  }
  summary(value) {
    const host = this.el("calibration-summary"); host.replaceChildren();
    const add = (label, content) => { const p = document.createElement("p"), strong = document.createElement("strong"); strong.textContent = `${label}: `; p.append(strong, document.createTextNode(String(content))); host.append(p); };
    const number=value=>Number.isFinite(value)?new Intl.NumberFormat("en",{maximumFractionDigits:3}).format(value):"unavailable";
    if(value.quality_id){add("Measured checks",value.passed?"PASS · statistical confidence and point uncertainty are not estimated":`FAILED · ${value.failures.join(", ")}`);add("RGB/depth correspondence",`${number(value.correspondence_error_px)} px · limit ${number(value.correspondence_limit_px)} px`);add("Camera overlap",`${number(value.overlap_difference_mm)} mm · limit ${number(value.overlap_limit_mm)} mm`);add("Saved independent validation",`${number(value.validation_reference_max_mm)} mm maximum · limit ${number(value.validation_limit_mm)} mm`);add("Scope",value.scope);}
    else if(value.batch_id && value.captures){add("Reference acquisition",`${value.captures.length} saved RGB/depth captures · ${value.camera_id} · ${value.partition}`);add("Independent survey",value.scope);add("Retry behavior","The original capture times and bytes are retained. A new measurement needs a new dataset identity.");}
    else if(value.captures && value.machine){add("Runtime acquisition",`${value.captures.length} saved camera observations · scene step ${value.step}`);add("Scope","Sensor-reported robot state and actual image references. Acquisition alone does not approve a target.");}
    else if(value.mask && value.selected_rgb_pixel){add("Image identification",value.method==="reference_center"?"One declared purple survey patch":"One declared red product top");add("Selected RGB pixel",value.selected_rgb_pixel.map(number).join(", "));add("Selected pixels",value.selected_pixel_count);add("Surface mask",`Saved NPY array · SHA-256 ${value.mask.sha256} · included in evidence export`);add("Scope",value.scope);}
    else if(value.reference_id && value.measurement){add("Independent reference","Survey coordinate and reconstructed measurement are separate inputs to validation.");add("Surveyed base point",`${value.base_point_m.map(number).join(", ")} m`);add("Reconstructed base point",`${value.measurement.point.map(number).join(", ")} m`);add("Calculation","Protocol contains the recorded depth call, raw-array references, X and limits. Calculations contains its numerical result.");}
    else if (value.report_id && "ready_to_fit" in value) {
      add("Measurement quality",value.ready_to_fit?"Accepted measurements · this report alone does not authorize work":"More informative measurements required");
      add("Images",`${value.accepted_capture_ids.length} accepted of ${value.capture_count} · ${value.rejections.length} rejected`);
      add("Coverage failures",value.coverage.failures.join(", ")||"None");
      add("Position spans",`${value.coverage.translation_span_m.map(number).join(", ")} m`);
      add("Rotation diversity",`${value.coverage.rotation_singular_values_rad.map(number).join(", ")} rad · at least two independent axes required`);
      add("Next action",value.next_action);
    } else if(value.plan_id && value.flange_poses) {add("Capture plan",`${value.scenario} · ${value.flange_poses.length} poses`);add("Timing",`${value.settled?"Settled":"Unsettled"} · depth timestamp offset ${number(value.timestamp_skew_s*1000)} ms`);add("Scope",value.scope);}
    else if (value.streams && value.camera_configuration_fingerprint) {
      add("Optical model verification",value.passed?"PASS · separate synthetic factory fixture":`FAILED · ${value.failures.join(", ")}`);
      for(const stream of value.streams)add(`${stream.stream.toUpperCase()} projection`,`${number(stream.rms_px)} px RMS · ${number(stream.maximum_px)} px maximum · ${stream.point_count} measured references`);
      add("What this does not verify",value.limitations.join(" "));
    } else if(value.optical_points_m){add("Optical reference fixture",`${value.stream} · ${value.optical_points_m.length} surveyed camera-local points and measured pixel correspondences`);add("Scope",value.scope);}
    else if (value.report_id && "passed" in value) {
      add("Saved validation decision", value.passed ? "PASS · validation alone does not authorize work. Current approval is shown above." : "REJECTED · this candidate cannot authorize work");
      if(!value.passed){for(const [label,count] of this.failureGroups(value.failures))add(label,count);add("Exact failure evidence","Codes and sample IDs are retained in Records and run info below.");}
      add("PnP image RMS", `${number(value.pnp_rms_px)} px · ${value.point_count} 2D points`);
      add("Robot-chain image RMS", `${number(value.chain_rms_px)} px`);
      add("Independent references", `${value.reference_count} · maximum ${number(value.reference_max_mm)} mm · median ${number(value.reference_median_mm)} mm`);
      add("p95", value.reference_p95_mm === null ? "Not reported: insufficient support" : `${number(value.reference_p95_mm)} mm · ${value.quantile_method}`);
      add("Rejected measurements retained", value.rejected_measurements.length);
    } else if (value.check_id) {
      add("Routine reference check", value.passed ? "PASS · does not approve or restore calibration" : `FAILED · ${value.failures.join(", ")}`);
      add("Reference measurements", `${value.reference_count} · maximum error ${number(value.maximum_error_mm)} mm`);
      add("Diagnosis", value.diagnostic.conclusion); add("Clues, not proven causes", value.diagnostic.clues.join(", ") || "None yet");
      add("Next measurements", value.diagnostic.next_measurements.join(" ")); add("Scope", value.scope);
    } else if (value.coverage) { if(value.reused_from)add("Saved estimate", `Unchanged X/Y from ${value.reused_from.artifact_id}. This is not a new fit. Unused validation and new approval are required.`); add("Estimate", "INACTIVE candidate · does not authorize work"); add("Coverage", `${value.coverage.sample_count} accepted images · multiple-axis rotation values and position spans below`); if(value.fit_diagnostics){add("Training exclusions",`${value.excluded_sample_ids.length} inconsistent robot/board pairs · ${value.fit_diagnostics.tested_hypotheses} reproducible hypotheses`);add("Selection rule",value.fit_diagnostics.selection_rule);} }
    else if (value.selected_rgb_pixel) { add("Measured point", `${value.point?.join(", ") ?? "no target"} · ${value.frame || "unknown frame"} · ${value.unit || "see record"}`); add("Selected RGB pixel", value.selected_rgb_pixel.join(", ")); }
    else if (value.corner_ids) { add("Detected corners", value.corner_ids.length); add("PnP image RMS", `${number(value.pnp_rms_px)} px`); add("Excluded corners", value.excluded_corner_ids.join(", ") || "None"); }
    else if (value.verification_id) { add("Tool verification",value.passed?"PASS · independent translation and orientation check":`FAILED · ${value.failures.join(", ")}`); add("Translation error",`${number(value.translation_error_mm)} mm`);add("Orientation error",`${number(value.orientation_error_deg)} degrees`);add("Evidence",`${value.pivot_count} pivot positions and ${value.probe_count} indexed probes. Select the tool-measurements record with the same ID for raw observations.`); }
    else if (value.measurement_id) {add("Tool measurements",`${value.pivot_flange_poses.length} pivot positions and ${value.probes.length} independently measured points`);add("Scope",value.scope);}
    else if (value.definition && value.scope === "ISOLATED_SIMULATION_FAULT") {add("Simulation experiment",value.definition.label);add("Changed",value.definition.description);add("Next action",value.definition.next_action);add("Evidence limit","The injected cause is instructor configuration, not a diagnosis inferred from measurements.");}
    else if(value.outcome_id){add("Measured pick outcome",`${value.verification.verdict} · ${value.verification.reason}`);add("Original command",value.command.command_id);add("Controller result",value.receipt?`${value.receipt.status} · ${value.receipt.reason} · ${value.receipt.effect_count} product transfers`:"Unconfirmed; retain the original command");add("Fresh observation",`${value.observation.observation_id} · ${value.observation.captured_at}`);add("Scope",value.scope);}
    else if(value.investigation_id){add("Investigation",value.conclusion);for(const clue of value.clues){add(clue.code,clue.observation);add("Check",clue.investigate);add("Next measurement",clue.next_measurement);add("What remains uncertain",clue.limitation);}add("Scope",value.scope);}
    else if (value.reason) add("Rejected", `${value.reason} · ${value.detail || "Inspect the saved record."}`);
    else if (value.artifact_id) { add("Approval", `${value.approval.actor} · ${value.approval.scope}`); add("Candidate", value.candidate.candidate_id); }
    else if ("admitted" in value) { add("Acquisition", value.admitted ? "Admitted · board pose is evaluated separately" : "Rejected"); add("Camera", value.camera_id); add("Timestamps and frames", "Recorded below with RGB/depth artifact hashes."); }
    else add("Saved record", "Full recorded values and identities are available below.");
  }
  populateSources() {
    this.components = [
      {path:"robotops/calibration/acquisition.py",symbol:"make_plan"},
      {path:"robotops/calibration/acquisition.py",symbol:"assess"},
      {path:"robotops/calibration/estimation.py",symbol:"estimate_board"},
      {path:"robotops/calibration/estimation.py",symbol:"fit"},
      {path:"robotops/calibration/estimation.py",symbol:"_fit_transforms"},
      {path:"robotops/calibration/optics.py",symbol:"verify_camera_model"},
      {path:"robotops/calibration/depth.py",symbol:"pixel_to_base"},
      {path:"robotops/calibration/depth.py",symbol:"reconstruct"},
      {path:"robotops/calibration/perception.py",symbol:"identify_surface"},
      {path:"robotops/calibration/agreement.py",symbol:"compare_cameras"},
      {path:"robotops/calibration/tcp.py",symbol:"verify_measurements"},
      {path:"robotops/calibration/tcp.py",symbol:"verify_tool"},
      {path:"robotops/calibration/registration.py",symbol:"align_native_depth"},
      {path:"robotops/calibration/inspection.py",symbol:"inspect_pixel"},
      {path:"robotops/calibration/validation.py",symbol:"validate"},
      {path:"robotops/calibration/lifecycle.py",symbol:"CalibrationStore.approve"},
    ];
    if (this.savedTrace) this.components.unshift({path:this.savedTrace.path,symbol:this.savedTrace.symbol});
    this.options("calibration-component", this.components.map((item,index) => [String(index), `${item.path} · ${item.symbol}`]), "0");
  }
  async showSource(full) {
    this.fullSource=full;
    const generation = ++this.sourceGeneration;
    this.el("calibration-component-control").hidden = !full;
    this.el("calibration-excerpt").setAttribute("aria-pressed", String(!full));
    this.el("calibration-full").setAttribute("aria-pressed", String(full));
    if (!full) {
      this.text("calibration-source-scope", this.savedTrace ? this.savedTrace.source.scope : "No instrumented source snapshot is linked to this record. Full Python file provides current reference code.");
      this.text("calibration-source-content", this.savedTrace?.source.excerpt || "No saved excerpt."); return;
    }
    this.text("calibration-source-scope", "Loading current reference source…");
    this.text("calibration-source-content", "");
    const selected = this.components?.[Number(this.el("calibration-component").value)];
    if (!selected) return;
    try {
      const result = await this.request(`/calibration/source?path=${encodeURIComponent(selected.path)}&symbol=${encodeURIComponent(selected.symbol)}`);
      if (generation !== this.sourceGeneration) return;
      this.text("calibration-source-scope", `${result.scope}. Displayed SHA-256: ${result.displayed_sha256}. Highlight marks the related function, not executed lines.`);
      const host = this.el("calibration-source-content"); host.replaceChildren();
      result.content.split("\n").forEach((line,index) => { const span = document.createElement("span"); span.textContent = `${index+1}  ${line}`; if (index+1 >= result.symbol_start_line && index+1 <= result.symbol_end_line) span.className = "related-source-line"; host.append(span); });
      const line = host.querySelector(".related-source-line"); if (line) host.scrollTop = line.offsetTop - host.offsetTop;
    } catch (error) { if (generation === this.sourceGeneration) this.text("calibration-source-scope", `Current source unavailable: ${error.message}`); }
  }
}
globalThis.CalibrationConsole = CalibrationConsole;
