"use strict";

// Task navigation changes presentation only. Execution stays in IntegrationConsole.
class SimulationWorkspace {
  constructor() {
    this.el = id => document.getElementById(id);
    this.restoring = true;
    this.requested = this.readLocation();
    this.view = this.requested.view;
    this.test = null;
    this.session = null;
    const console = this.el("integration-console");
    document.querySelector(".test-toolbar").append(this.el("integration-history").closest(".integration-session-picker"));
    const grid = document.querySelector("#test-workspace > .grid");
    grid.id = "run-workspace";
    grid.setAttribute("aria-label", "Run and watch");
    const evidence = document.createElement("section");
    evidence.id = "evidence-workspace";
    evidence.setAttribute("aria-label", "Inspect evidence");
    grid.after(evidence);
    const heading = document.createElement("h2");
    heading.textContent = "Inspect evidence";
    heading.tabIndex = -1;
    evidence.append(heading);
    const empty = document.createElement("p");
    empty.id = "evidence-empty";
    empty.textContent = "No saved run yet. Start a guided run in Run & watch to record each step, then inspect its evidence here.";
    evidence.append(empty);
    const robot = this.el("integration-robot");
    grid.querySelector(".workspace").prepend(robot);
    this.el("integration-robot-dock").append(this.el("motion-panel"));
    robot.open = true;
    const robotNotes = document.createElement("details");
    const robotNotesTitle = document.createElement("summary");
    robotNotesTitle.textContent = "Replay evidence and limits";
    robotNotes.append(robotNotesTitle);
    for (const child of Array.from(robot.children)) if (child.tagName === "P") robotNotes.append(child);
    this.el("motion-panel").append(robotNotes);
    const phases = document.createElement("details");
    phases.className = "phase-navigation";
    const phaseTitle = document.createElement("summary");
    phaseTitle.textContent = "Explore system boundaries";
    phases.append(phaseTitle, this.el("integration-map"));
    evidence.append(phases, this.el("integration-proof-panel"));
    this.el("integration-proof-panel").open = false;
    evidence.append(console.querySelector(".integration-trace-grid"), console.querySelector(".integration-tools"), this.el("integration-ids").parentElement, console.querySelector(".acknowledgement-boundaries"));
    grid.after(evidence);
    grid.querySelector("aside").prepend(this.el("workflow-guide"));
    this.el("integration-cursor-strip").removeAttribute("aria-live");
    document.querySelector(".integration-detail").prepend(this.el("integration-cursor-strip"));
    this.el("integration-explanation").before(this.el("integration-tabs"));
    this.el("integration-explanation").open = false;
    // This location is shared across views. There is only one current action card.
    this.el("integration-heading-note").textContent = "Run a simulated warehouse pick, follow each system step, and inspect the evidence.";
    const nav = this.el("workspace-navigation");
    for (const link of nav.querySelectorAll("a")) {
      link.addEventListener("click", event => {
        if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        this.show(link.dataset.view, true);
      });
    }
    globalThis.addEventListener("popstate", () => {
      this.requested = this.readLocation();
      this.show(this.requested.view);
      this.restore?.(this.requested);
    });
    this.show(this.view);
  }

  readLocation() {
    const url = new URL(globalThis.location.href);
    return {view: url.hash === "#inspect" ? "inspect" : "run", test: url.searchParams.get("test"), session: url.searchParams.get("session"), step: url.searchParams.get("step"), tab: url.searchParams.get("tab"), component: url.searchParams.get("component")};
  }

  show(view, push = false) {
    this.view = view === "inspect" ? "inspect" : "run";
    this.el("run-workspace").hidden = this.view !== "run";
    this.el("evidence-workspace").hidden = this.view !== "inspect";
    for (const link of this.el("workspace-navigation").querySelectorAll("a")) {
      if (link.dataset.view === this.view) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    }
    if (push) this.save(true);
  }

  update(test, session, selected, tab, source) {
    this.test = test;
    this.session = session;
    this.step = selected?.step_id;
    this.tab = tab;
    this.component = tab === "Source" && source?.key === `${session?.session_id}/${selected?.step_id}` ? source.component || "entry" : null;
    this.el("evidence-empty").hidden = !!session;
    this.el("evidence-empty").textContent = this.restoring ? "Loading saved runs…" : "No saved run yet. Start a guided run in Run & watch to record each step, then inspect its evidence here.";
    for (const child of this.el("evidence-workspace").children) {
      if (child.tagName !== "H2" && child.id !== "evidence-empty") child.hidden = !session;
    }
    this.el("integration-history").closest(".integration-session-picker").hidden = !session;
    this.save();
  }

  save(push = false) {
    if (this.restoring) return;
    const url = new URL(globalThis.location.href);
    for (const [key, value] of Object.entries({test: this.test, session: this.session?.session_id, step: this.step, tab: this.tab, component: this.component})) {
      if (value) url.searchParams.set(key, value); else url.searchParams.delete(key);
    }
    url.hash = this.view;
    if (url.href !== globalThis.location.href) globalThis.history[push ? "pushState" : "replaceState"]({}, "", url);
    for (const link of this.el("workspace-navigation").querySelectorAll("a")) {
      const target = new URL(url); target.hash = link.dataset.view; link.href = target.href;
    }
  }
}
globalThis.SimulationWorkspace = SimulationWorkspace;
