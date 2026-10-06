# Real-protocol integration lab

This is an independent synthetic integration simulator. PostgreSQL, AMQP 0-9-1,
and OPC UA binary TCP are real protocols. The ERP, WMS, PLC, robot, and sensor
models remain simulations. The PLC-to-runtime link is a **simulated controller
interface**. No component is a certified safety function or a proprietary SICS.AI
interface, and no exactly-once physical-execution guarantee is claimed.

## Start the complete stack

```sh
docker compose up --build --wait
curl http://127.0.0.1:8000/health
docker compose exec plc python -m robotops.lab health
```

Open <http://127.0.0.1:8000>. Create an order and advance the persisted guided
stages. The final **AUTHORIZE ROBOT EXECUTION** gate precedes the runtime callback.
PostgreSQL, RabbitMQ, PLC, WMS, edge heartbeat, and API have health checks. Durable Docker volumes retain
application records, the edge inbox, broker messages, PLC identities, and robot
world/journal separately. `docker compose down` retains these volumes. A clean
experiment uses an explicitly new Compose project name and its own volumes.

The container profile runs the existing deterministic HKM-inspired synthetic
runtime. Its browser replays recorded events against a stationary 3D scene; it
does not generate Blender motion frames or claim animated robot motion.
Native launch supports the existing `BlenderRuntime` using
`ROBOTOPS_LAB_RUNTIME=blender` and `BLENDER_EXECUTABLE`.

The deployment uses deliberately public demo credentials and anonymous OPC UA
SecurityPolicy None, with host ports bound to loopback. It is a local development
lab. Credential values never enter protocol trace payloads. Configure production
authentication, encryption, authorization, certificate trust, broker access
control, and network isolation before adapting these educational components.

## Native services and smoke test

Windows without Docker can run the same services independently. The portable
PostgreSQL/RabbitMQ bootstrap is documented in
[the native service guide](integration-lab-native.md).

Set `ROBOTOPS_POSTGRES_DSN`, `ROBOTOPS_AMQP_URL`, and `ROBOTOPS_OPCUA_URL` in the
process environment, then run these in separate terminals:

```sh
uv run python -m robotops.lab plc
uv run python -m robotops.lab edge
uv run uvicorn robotops.lab.business:create_app --factory --loop robotops.http_server:new_event_loop --host 127.0.0.1 --port 8081
uv run uvicorn robotops.lab.api:create_app --factory --loop robotops.http_server:new_event_loop --host 127.0.0.1 --port 8000
```

`ROBOTOPS_LAB_DATA` selects runtime artifacts (default `runs/lab`).
`ROBOTOPS_PLC_JOURNAL` selects retained PLC memory (default `runs/lab/plc.db`).
The lab uses one retained cell; creating/deleting independent fast-profile tests
is disabled and advertised through `/health` capabilities.
`ROBOTOPS_WMS_URL` selects the actual business REST service (default
`http://127.0.0.1:8081`). `python -m robotops.lab edge-health` checks both the
edge control service's HTTP health and its recent PostgreSQL heartbeat after
successful broker polling.
`ROBOTOPS_EDGE_URL` selects the separate edge control service (default
`http://127.0.0.1:8082`). The edge process owns the OPC UA client; the API has no
direct OPC UA fallback. The edge's bounded REST control endpoint makes each
guided trust gate execute only its selected OPC UA operation.

Run the mandatory distributed smoke lane against live services:

```powershell
uv run python -m pytest tests/lab -q
```

The tests allocate isolated PostgreSQL schemas and RabbitMQ queues, start actual
OPC UA TCP servers, and prove publisher confirms, manual consumer ACK, durable
inbox-before-ACK, redelivery, precondition validation, physical authorization,
lost-ACK recovery, and unchanged physical effect counts. They never substitute
broker or OPC UA mocks. The normal fast profile runs SQLite and in-process
transport with truthful simulated-transport labels. For an explicitly limited fast
check, use `uv run python -m pytest -m 'not lab_integration and not blender'`.
There are no environment-based test skips: the full suite fails if mandatory lab
services are unavailable. OPC UA TCP tests also run in the fast suite.
CI provisions live PostgreSQL/RabbitMQ and runs the
distributed lane inside both full acceptance runs and coverage accounting.

For a reproducible clean full lab over running PostgreSQL/RabbitMQ, use:

```sh
uv run python -m tools.lab_stack --fresh --data-dir artifacts/lab-final --report artifacts/lab-final-stack.json
```

This creates a new PostgreSQL schema, durable queue/routing identity, and local
artifact directory, then starts separate PLC, edge, WMS, and API processes. It
checks actual OPC UA, HTTP, and recent edge heartbeat readiness before reporting
the loopback addresses. The report contains no credentials. Ctrl+C stops only
the supervisor's children and retains evidence. It never stops the existing
PostgreSQL/RabbitMQ services. `--runtime blender` selects the existing Blender
adapter; the default explicitly selects the deterministic synthetic runtime.
For recorded robot animation, use the same complete stack with
`--runtime blender` and an installed Blender executable. Before physical consent,
guided playback and event autoplay are disabled while the static cell and camera
controls remain inspectable. Consent selects the current job before playback is
enabled, so an earlier delivery cannot appear to be its motion. The console's
payload body expands/collapses without a REST mutation; attempt and delivery
indicators come from persisted step and inbox evidence.

`tests/lab/test_browser_lab.py` drives Chromium against this separate-process
stack. Its mandatory happy case uses Blender and checks nonempty original motion
frames, a motion track, product displacement, and changing evaluated and rendered
robot poses during browser playback after consent. The lost-ACK-after-effect,
duplicate-delivery and real WMS HTTP503 cases use the synthetic runtime and prove
protocol, effect and recovery semantics, not animated robot motion. All cases
check pre-gate effect zero, disabled playback, mid-stage reload, duplicate physical
authorization, final business completion and no credential values in trace/log
artifacts under `artifacts/lab-browser`.

## Persistence and execution contract

`robotops/lab/postgres.py:PostgreSQLStore` implements the same Store operations as
the local repository. Orders/jobs, sessions, authorization decisions, traces,
immutable plans/commands, and business outcomes live in PostgreSQL. Short write
transactions serialize with a transaction-scoped advisory lock. No transaction
is held during human waiting, broker calls, OPC UA calls, or physical execution.

`DeliveryStore.enqueue` atomically commits an immutable dispatch payload and
pending outbox row. The payload hash comes from the same canonical command
digest used by the runtime. The workflow's original command and
`integration_outbox` intent commit together in `Store.prepare`; the explicit
outbox stage materializes its immutable `lab_outbox` dispatch record before any
network side effect. `LabBridge.publish` sends persistent messages with
stable `message_id=command_id`, a durable direct exchange/queue, mandatory routing,
and publisher confirms. Confirmed publication is a separate PostgreSQL update;
a crash in that window can republish. This is deliberately at-least-once delivery.

`EdgeAdapter.consume_one` validates identity/hash and commits the PostgreSQL inbox
before calling `basic_ack`. Duplicate delivery increments a durable delivery count.
The trace says **consumer ACK sent** because AMQP consumer ACK is one-way. An inbox
commit followed by connection loss redelivers safely. Edge consumption does not
call SubmitJob or execute motion; those are later guided boundaries.

After each explicit gate, `LabBridge` calls `EdgeRPC`, which sends the bounded
operation to `robotops/lab/edge.py:EdgeControl`. The separate edge process performs
browse/subscribe/SubmitJob/precondition/status/restart/ack traffic to the PLC.
For physical authorization it opens a retained OPC UA subscription and obtains
the PLC's one-use execution claim, then returns the permit. The API invokes the
same existing runtime callback as local/automatic execution; this co-located
adapter is the explicitly **simulated controller interface**, not an OPC UA
connection. ReportResult goes back through the edge's retained UA session.
OPC UA requests and background ServerState probes use the same bounded network
timeout; a delayed probe never authorizes a second runtime callback.
If the callback or API disappears, the edge closes its session after a bounded
180-second retention window without resetting the PLC claim. Reconciliation can
reconnect through the edge and report the original journal receipt. Tests assert
the OPC client process ID equals the separate edge process and differs from API.

## OPC UA address space

Namespace: `urn:robotops:integration-lab:cell-1`.

| Object/method | Meaning |
| --- | --- |
| `Objects/RobotCell/Cell` | State, Generation, BootId, FaultCode |
| `RobotCell/Command` | ActiveCommandId, PayloadHash, State, ResultSequence, LastResult |
| `RobotCell/Robot` | Ready, ActiveToolId, TCPPose, MotionPhase; simulated model fields |
| `SubmitJob(commandJson)` | Validate/retain immutable command; returns ACCEPTED without effect |
| `CheckPreconditions(id, worldJson)` | Check retained hash and current scene/generation/cell/source/tool/trajectory; returns READY |
| `BeginExecution(id)` | Atomically transition READY to EXECUTING and grant one durable permit |
| `ReportResult(id, receiptJson)` | Retain matching original runtime journal receipt after execution/reconciliation |
| `GetJobStatus(id)` | Read original retained status/result without dispatching |
| `AcknowledgeResult(id, sequence)` | Mark one retained result acknowledged; does not delete identity |
| `RestartController()` | Explicit simulated controller boot; changes BootId and retains all claims/results |

Each client operation opens an actual OPC UA session, discovers the namespace,
browses RobotCell, creates a data-change subscription, and calls/reads the relevant
node. During execution one session/subscription stays open across the bounded
runtime callback. Actual data-change notifications persist in PostgreSQL and are
available through the read-only live-status trace. `CheckPreconditions` sets the
cell generation/state, tool, TCP pose, and motion phase from the supplied current
runtime snapshot. The robot Ready flag becomes false during execution; phase is
the actual controller state transition, not fake streamed joint telemetry. TCP
pose becomes explicitly unavailable during motion and after a receipt until fresh
world evidence arrives. The browser's 3D motion comes from the existing runtime
recording, independently from the OPC UA protocol status feed.

## Uncertainty, restart, and acknowledgements

The PLC journal is a separate SQLite database with FULL synchronous commits. It
retains command identity, canonical hash, boot identity, execution claim, immutable
result, result sequence, and acknowledgement. Retention lasts until the operator
explicitly removes that experiment's storage; there is no timed duplicate expiry.
Provisional RUNNING/STATUS_UNKNOWN receipts may advance to a terminal receipt with
a higher result sequence; every version is retained. A terminal result is immutable.

Same ID/same hash returns retained status/result. Same ID/different hash rejects.
Neither resubmission nor process restart can renew an execution claim. If an API
or PLC process stops after a claim but before its result is retained, status remains
EXECUTING and the workflow exposes UNKNOWN_OUTCOME. It never blindly calls the pick
again. Explicit reconciliation queries the **original runtime command journal**
and fresh observation, then backfills `ReportResult`; it does not issue a new ID.
Missing evidence remains uncertain. Runtime operational checks run again at effect.
Readiness records the BootId that passed preconditions. A logical or process restart
invalidates that readiness until fresh checks pass under the new boot; an existing
execution claim remains retained and can never be renewed by revalidation.

An interrupted authorization remains `EXECUTING_STAGE`. Explicit reconciliation
cannot take over while the original bounded operation could still be running: it
waits for the larger of the configured lease, runtime timeout plus twice the lab
network timeout plus 60 seconds, and planner timeout plus 60 seconds. After that
budget, nonphysical stages resume their same stage and identity. For interrupted
physical stage 16, a committed dispatch intent triggers original-journal/fresh-
observation reconciliation only. If neither dispatch intent nor controller result
exists, lab recovery returns to preconditions at stage 14, then mandatory gate 15,
with physical authorization cleared. Local recovery returns directly to gate 15.
A missing result after committed intent remains uncertain/intervention. Persisted
command/verdict stages recover their existing records; a stale pre-plan observation
returns to the observation stage, while hard planner rejection terminates FAILED.

Lost ACK before effect yields the runtime's retained PROVEN_NOT_STARTED receipt;
lost ACK after effect retains effect_count=1. Both are reconciled by original
identity. Broker failure preserves pending outbox intent; edge failure preserves
broker/inbox state. OPC UA connection failure before a permit cannot execute the
callback. Connection loss after a permit/result may be uncertain and is reconciled.
WMS retry belongs to business reconciliation and never grants a new robot permit.
The guided restart fault calls a real OPC UA method that simulates a controller
boot; the separate automated restart test actually terminates/relaunches the
OPC UA server process between physical effect and result publication.

`robotops/lab/business.py` runs a separate synthetic WMS REST server.
`POST /v1/wms/acknowledgements` validates the verified outcome, retains a durable
command-keyed acknowledgement in PostgreSQL, and rejects payload conflicts. The
WMS outage scenario returns a real HTTP 503 on its first attempt; its durable fault
record makes the next authorized retry succeed without invoking robot motion.
Stage 20 records the HTTP response separately from PLC/controller/sensor evidence.

The console's scenario summaries describe the configured injection; persisted
stage and journal evidence shows what actually happened. Replay reads the original
guided scenario through each job's saved session association, including transport
and WMS faults that do not inject a robot-runtime fault. Live protocol responses
are displayed only for the currently selected session and command. A pending or
unavailable read cannot establish an execution outcome.

These acknowledgements are intentionally distinct:

`HTTP 202 != DB commit != publisher confirm != consumer ACK != OPC UA method
acceptance != PLC readiness != controller success != sensor verification != WMS
acknowledgement != ERP completion`.

The robot journal's deterministic simulator transaction can atomically retain its
synthetic world change. This is not evidence that a real mechanical effect can be
included in a PostgreSQL/RabbitMQ transaction.
