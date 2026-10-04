# RobotOps Twin

A deterministic warehouse robotics integration simulator with a durable workflow,
a synthetic Blender world, observations, verification and conservative recovery.

**Aktuell status:** Robot-cell selection and explicit test-data deletion are being implemented against baseline ae6d5d85c813e47aea042aea2a87236b5a8bc204. Previous 110-MUST HKM acceptance is preserved as historical evidence; this new revision is awaiting verification. **NOT DONE**.

[Acceptance evidence](ACCEPTANCE_REPORT.md) · [Progress](GOAL_PROGRESS.md) ·
[Plan](PROJECT_PLAN.md) · [Success criteria](SUCCESS_CRITERIA.md) ·
[Agent handoff](HANDOFF.md) · [Checklist](CODEX_GOAL_CHECKLIST.md)

The implemented cell contains an original **HKM1800-inspired hybrid-kinematic
manipulator**, six distinct product families, six interchangeable tools, a tool
rack, destination tote/conveyor, enclosure and three camera viewpoints. The
deterministic Brain records why it selected a tool; validated segmented motion
visibly changes tools, picks, transfers and releases the product. Shared scene
geometry and recorded quaternion transforms drive Blender and read-only browser
replay. [The adaptation guide](docs/implementation/hkm-inspired.md) describes the
synthetic mechanics and conservative geometric checks.

Fresh API/desktop data uses this six-SKU profile. **Start new test** opens
**New simulation test**: choose **Robot cell**, then **Create test**. The
HKM-inspired cell is the only selectable cell today; the registry supports future
additions. Saved legacy tests retain their original Cartesian scene, command
hashes and evidence, and are labelled by their saved cell.
[Actual Blender evidence](docs/evidence/hkm-blender-local/result.json) covers the
six-tool showcase, attachment/release, uncertainty, restart and read-only replay.
[The baseline archive](docs/evidence/hkm-baseline-eaf35b4/provenance.json) preserves
the earlier release and the fresh baseline failure. Scoped development results
retain their original source attribution. The 110-MUST HKM acceptance belongs
to audited source `ca779879` and its publication successor `ae6d5d8`.
[Current acceptance](ACCEPTANCE_REPORT.md) records evidence and remaining gates
for subsequent changes, including cell selection and test-data deletion.

This is an independent simulator inspired by public sources and general practice.
It does not reproduce SICS AI proprietary architecture or AGI. Blender supplies
synthetic visualization and test state, not validated robot dynamics, an exact
HKM1800 simulation or evidence of real-world robot performance. Logical E-stop is
an application interlock, not safety certification. No API key, model service,
GPU, real PLC or industrial hardware is required.

## Setup

Install [uv 0.12.13](https://docs.astral.sh/uv/getting-started/installation/) and
[Blender 5.2.1 LTS](https://download.blender.org/release/Blender5.2/).
Python 3.13.15 is selected by `.python-version`; uv can install it automatically.
Set `BLENDER_EXECUTABLE` to the Blender executable when it is not on PATH.
Install Node 20.17.0 and its npm for playback tests and dependency auditing.
Viewer assets are already vendored; no npm install is needed to run the app.
The standard Windows Blender 5.2 installation is also detected.

```sh
git clone https://github.com/raal1600/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator.git
cd SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator
uv sync --locked --all-groups
uv run --locked python -m tools.dev demo
```

The last command initializes empty SQLite state and runs the deterministic
headless happy path. Every demo creates a fresh directory under `runs/` and prints
its evidence path. Existing evidence is never overwritten. Full tests require
actual Blender and fail explicitly if it is absent. PDF publication additionally
needs the system libraries documented in [PUBLICATION.md](PUBLICATION.md).

| Make command | Portable equivalent (including PowerShell) |
|---|---|
| `make setup` | `uv sync --locked --all-groups` |
| `make test` | `uv run --locked python -m tools.dev test` |
| `make lint` | `uv run --locked python -m tools.dev lint` |
| `make typecheck` | `uv run --locked python -m tools.dev typecheck` |
| `make security` | `uv run --locked python -m tools.dev security` |
| `make demo` | `uv run --locked python -m tools.dev demo` |
| `make acceptance` | `uv run --locked python -m tools.dev acceptance` |
| `make docs` | `uv run --locked python -m tools.dev docs` |

Dependencies are pinned by `uv.lock`. Security auditing queries public advisory
databases during preflight; the mandatory runtime tests require no network after
installation. [Toolchain and reviewed exceptions](docs/implementation/dependencies.md).

## Demonstrations

### Windows desktop app

Double-click **RobotOps Twin** on your desktop to start its dashboard and Blender
runtime. Closing the app stops its owned processes; orders and evidence persist.
Build/install the launcher with
`powershell -NoProfile -ExecutionPolicy Bypass -File tools/build-desktop.ps1 -Install`.
It uses the existing local checkout, Python environment and Blender installation.
[Desktop lifecycle, data locations and tests](docs/implementation/desktop.md).

### Command-line demos

```sh
uv run --locked python -m tools.dev demo --runtime blender --scenario happy_path
uv run --locked python -m tools.dev demo --runtime blender --scenario lost_ack_after_effect
uv run --locked python -m tools.dev demo --runtime blender --scenario ambiguous
uv run --locked python -m tools.dev demo --runtime blender --scenario restart
uv run --locked python -m tools.dev demo --runtime blender --scenario tool_showcase
```

The lost-ack demo moves the product, loses the reply and persists UNKNOWN_OUTCOME.
Reconciliation queries the original command journal and obtains a fresh observation.
It completes only with sufficient evidence and proves one pick effect. Ambiguous
evidence produces REQUIRES_INTERVENTION. Further fixtures include
`lost_ack_before_effect`, `logical_estop` and `cell_fault`. `--runtime headless`
uses the same contracts with an atomic synthetic world for fast logic experiments.
The `tool_showcase` demo picks SKU-A through SKU-F with all six preferred tools,
verifies each job and records one product-transfer effect per original command.

```sh
uv run --locked python -m apps.api --runtime blender --data-dir runs/my-demo --port 8000
```

Open http://127.0.0.1:8000 for the local dashboard. The dark workspace guides you
through **Prepare / Run / Review / Continue** with a persistent **Next step** card.
Choose a product and scenario in **Set up a pick**. Each choice explains **What
this simulates**, its stage, its **Key difference** and the expected result.
Expand **Compare all execution scenarios** or **Compare all observation modes**
to read the options together. The execution selector changes a new order; the
observation selector changes only a later review capture for the original pick.
[Scenario and observation definitions](docs/implementation/scenarios.md).
Watch **Live cell & replay**, then follow the guide's next action.
If attention is needed, **Review evidence** opens and receives focus automatically.
It explains the original journal, the assessed observation and the latest decision,
with observation choices and the reconciliation action together. **Use normal
observation** only selects the next capture mode; click the named review action to
collect it. Repeated bad evidence keeps review available. Completed picks lead to
the next setup, stopped cells to reset, and saved tests back to the current test.
[Guided workflow and evidence boundary](docs/adr/0009-guided-simulation-workflow.md).
The saved Blender snapshot is available in the collapsed **Technical details**
section; the full 3D view and replay are the main visualization.
Reusing the data directory preserves state across restart.
Use **Start new test** at the top for any new execution/observation combination.
Choose **Robot cell** in the dialog, then **Create test**. It keeps both fault
selections, restores all products in an independent world and saves the previous
test unchanged. This works after success, failure, uncertainty or
intervention; a running operation must finish first. **Test history** opens saved
evidence and replay in the same window, read-only. **Return to current test**
resumes the active test. Startup recovers only that active world.

**Delete selected test** removes the selected test's orders, evidence and replay
after confirmation. **Clear all test data** confirms the displayed test set and
removes those registered worlds. These actions do not run or reconcile a pick.
Deleting the active test or clearing all tests leaves no active test; choose
**Start new test** to continue. No archived test is promoted automatically.
Cancellation changes nothing, and in-flight work blocks deletion. Cleanup that
cannot finish immediately remains visible as pending and is retried safely.
[Data scope and recovery](docs/adr/0011-cell-selection-and-test-data-lifecycle.md)
explain retained catalog metadata and the boundary around application-owned files.

Changing **Execution scenario** changes the next order's configuration only.
**Restock this test → Start fresh scene** restores products within a resolved
test; unresolved jobs still block it. **Reset logical cell state** does not move products.
When all products are picked, the main button offers **Start new delivery and run
order**. **Full delivery (all products)** replays every execution in the selected
scene; **Choose delivery or product replay** exposes current or saved deliveries, and individual
product replay remains available.
**Run six-tool showcase (happy path)** runs that same six-product sequence in the
app. **Why this tool?** exposes persisted candidate scores and constraint reasons.

After a lost acknowledgement, the **Next step** card names the unresolved product
and opens **Review evidence**. Select **Normal observation** and use
**Reconcile [product]** to check that original pick before running another product.
Each pick in the lost-ack scenario needs this step. Contradictory or insufficient
evidence pauses the next pick but allows **Observe again and reconcile** in the
same test. Choose an observation mode and try again; **Normal observation**
removes the injected degradation for that new capture. Each attempt checks the
original command and stays in the timeline. Sufficient evidence resolves the job
and unlocks the next explicit order; inconclusive evidence keeps it paused.
No new pick is sent by observation. Restart leaves intervention paused.
You can always start an independent test with **Start new test**; the previous
uncertain/intervention outcome remains recorded and is never labelled resolved.

**Live cell & replay** always shows the 3D environment, machine and products.
Orbit, pan and zoom around the cell. Orders with an effect move the machine and
product using recorded Blender poses; blocked orders replay their events with
the saved starting scene held still. Play/pause, scrubbing and speed affect only
the view. Operator, Overhead, Side inspection and Follow TCP are presentation
views; frame stepping and speeds from 0.25x to 4x never change execution evidence.
Replay sends no new pick. Software 3D remains available without WebGL.
For older orders, **Load saved animation** reads their original `.blend`.
[Playback behavior and evidence boundary](docs/implementation/playback.md).
`/metrics` exposes persisted job, command, tool, observation, trajectory and
reconciliation counts, with application latency separate from synthetic motion
duration; `/docs` exposes OpenAPI.
This local demo API has no production authentication and binds to loopback.

## Architecture

```mermaid
flowchart LR
    ERP[ERP/WMS UI] --> API[Integration API]
    API --> PROFILES[Registered cell profiles]
    API --> TEST[Test catalog: active world / retained history]
    TEST --> RETAIN[Confirmed deletion / tombstones / bounded cleanup]
    API --> WF[Durable workflow]
    WF --> O[ObservationModel]
    WO[WorldObservation] --> B[DeterministicBrain]
    B --> P[Tool selection and trajectory intent]
    P --> V[Action validation]
    V --> G[RobotGateway]
    G --> C[Cell and command journal]
    C --> W[Blender WorldState]
    W --> O
    O --> WO
    WO --> VERIFY[Verifier]
    VERIFY --> R[Reconciliation]
    R --> WF
    WF --> ERP
```

The verifier accepts observations, never simulator ground truth. Duplicate command
delivery preserves identity and cannot repeat the effect. Fenced durable claims
serialize the cell; lease expiry does not prove that motion failed. A fixed Blender
script and typed JSON form the runtime boundary. Missing/corrupt checkpoints remain
uncertain. No natural-language MCP execution or generated code controls the runtime.

| Code / contract | Documentation |
|---|---|
| `apps/api/`, `apps/erp_ui/` | [Operations, API and metrics](docs/implementation/operations.md) |
| `robotops/domain/`, `contracts/` | [Versioned contracts](docs/implementation/contracts.md) |
| `robotops/robotics/`, `robotops/hkm_geometry.py` | [HKM-inspired cell and tool catalogue](docs/implementation/hkm-inspired.md) |
| `robotops/workflow/` | [Persistence and fenced claims](docs/implementation/persistence.md) |
| `robotops/brain/`, `robotops/verification/`, `robotops/observation/` | [Validation and reconciliation](docs/implementation/reconciliation.md) |
| `robotops/cell/`, `robotops/robot_gateway/` | [Journal and fault semantics](docs/implementation/runtime.md) |
| `robotops/blender/`, `blender/scripts/` | [Bounded Blender runtime](docs/implementation/blender.md) |
| `apps/erp_ui/playback.js`, `scene-view.js`, `apps/api/playback.py` | [3D scenario replay](docs/implementation/playback.md) |
| `tests/`, `tools/`, `.github/workflows/` | [Acceptance process](docs/implementation/acceptance.md) |

Material design decisions are recorded in [ADR 0001](docs/adr/0001-durable-synthetic-boundaries.md).
Optional model assistance, OPC UA, external ERP delivery, realistic physics and real
hardware remain a non-blocking backlog. They are not implemented or validated.

## Research and publication

[GitHub Pages](https://raal1600.github.io/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/)
hosts documentation only. Current deployment identity appears in `build.json`.
Local implementation does not imply the public site has been deployed.

| Editable source | Published report |
|---|---|
| [Design and research](reports/01-design.md) | [Design study](https://raal1600.github.io/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/design.html) |
| [Scope and transfer limits](reports/02-avgransning.md) | [Scope](https://raal1600.github.io/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/avgransning.html) |
| [Technical discussion](reports/03-diskussion.md) | [Discussion](https://raal1600.github.io/SICS-RobotOps-Twin-E2E-Warehouse-Robotics-Integration-Simulator/diskussion.html) |

[Source registry](publication/references.json) and [diagram definitions](publication/diagrams.json)
distinguish independently verified public facts, company-reported claims, general
practice and our simulator design. Research is not acceptance evidence. All generated
HTML, SVG and PDFs are rebuilt from sources via [PUBLICATION.md](PUBLICATION.md).
No private recruitment messages, credentials or proprietary code are part of this project.

Rami Halabi · AI-assisted code, research text and publication · [MIT license](LICENSE).
