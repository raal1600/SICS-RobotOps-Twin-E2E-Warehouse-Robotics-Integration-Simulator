# Native Windows lab dependencies

The Windows development path runs actual PostgreSQL and RabbitMQ application processes from portable archives. It provides the same SQL and AMQP protocol boundaries as the container profile. The API, edge, OPC UA server, PLC, synthetic controller/runtime and browser still need to run as described in [Integration lab](integration-lab.md).

`tools/lab-services.ps1` installs no Windows service and changes no system PATH. Binaries, logs and durable service data are stored under the repository's ignored `artifacts/` directory. PostgreSQL and RabbitMQ bind to localhost. The script uses process-local environment variables and launches servers with hidden windows.

The pinned portable dependencies are PostgreSQL 17.11, RabbitMQ 4.3.6 and Erlang/OTP 27.3.4.18. The archives come from the [PostgreSQL Windows distribution provider](https://www.enterprisedb.com/download-postgresql-binaries), the [official Erlang release](https://github.com/erlang/otp/releases/tag/OTP-27.3.4.18) and the [official RabbitMQ release](https://github.com/rabbitmq/rabbitmq-server/releases/tag/v4.3.6). Archive SHA256 values are pinned in the bootstrap script. RabbitMQ documents [manual Windows application startup](https://www.rabbitmq.com/docs/install-windows-manual) and [Erlang compatibility](https://www.rabbitmq.com/docs/which-erlang).

Run these commands from the repository root in PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/lab-services.ps1 -Action Install
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/lab-services.ps1 -Action Start
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/lab-services.ps1 -Action Status
```

`-ExecutionPolicy Bypass` applies to that child PowerShell invocation only; it does not change the machine or user execution policy. `Install` checks the archive digests and extracts the tools. `Start` initializes a database only if the selected task data directory has no PostgreSQL cluster, then starts both servers. `Status` checks TCP readiness and makes no workflow mutations. TCP readiness alone is not protocol verification; the integration tests must authenticate and exercise SQL, publisher confirms, durable delivery, consumer acknowledgement and OPC UA.

Local fixture settings:

| Service | Address | Fixture identity |
| --- | --- | --- |
| PostgreSQL | `127.0.0.1:5432` | Database `robotops`, role `robotops`, public development password `demo-only` |
| RabbitMQ | `127.0.0.1:5672` | Default local-only `guest` / `guest`, virtual host `/` |
| RabbitMQ distribution | `127.0.0.1:25672` | Node `robotopslab@localhost` |
| Erlang node discovery | loopback port `4369` | Process-local node discovery |

These are synthetic localhost fixtures. The lab does not infer production security, real robot hardware or safety certification from these services. The RabbitMQ management plugin is not required or enabled by this bootstrap.

Start the application services in separate terminals using the configuration described in the main lab guide:

```powershell
$env:ROBOTOPS_POSTGRES_DSN = 'postgresql://robotops:demo-only@127.0.0.1:5432/robotops'
$env:ROBOTOPS_AMQP_URL = 'amqp://guest:guest@127.0.0.1:5672/%2F'
$env:ROBOTOPS_OPCUA_URL = 'opc.tcp://127.0.0.1:4840/robotops/'
$env:ROBOTOPS_EDGE_URL = 'http://127.0.0.1:8082'
$env:ROBOTOPS_WMS_URL = 'http://127.0.0.1:8081'
```

Set those process-local fixture variables in each service terminal, then start one
service per terminal:

```powershell
uv run --locked python -m robotops.lab plc
uv run --locked python -m robotops.lab edge
uv run --locked uvicorn robotops.lab.business:create_app --factory --host 127.0.0.1 --port 8081
uv run --locked uvicorn robotops.lab.api:create_app --factory --host 127.0.0.1 --port 8000
```

The edge service listens for bounded REST control on `127.0.0.1:8082` and owns the
OPC UA client sessions to the virtual PLC. The WMS acknowledgement service listens
on `127.0.0.1:8081`. The API never falls back to opening its own OPC UA session when
the edge is unavailable. Set `ROBOTOPS_EDGE_URL` and `ROBOTOPS_WMS_URL` if those
addresses differ from the defaults.

For a clean application-stack namespace over these existing PostgreSQL/RabbitMQ
services, the scoped launcher starts fresh API/edge/PLC/WMS processes and writes
health/service evidence:

```powershell
uv run --locked python -m tools.lab_stack --fresh --report artifacts/lab-final-stack.json
```

This creates fresh application persistence/queue identities; it does not erase
the shared PostgreSQL cluster or RabbitMQ installation. Follow the launcher report
for the exact service addresses and persistence paths used by that run.

Run the real-service integration tests and guided browser scenarios after all services are ready. A native service bootstrap is useful when Docker Desktop/WSL is unavailable; it does not replace the final complete-stack test or prove browser behavior on its own.

To stop only these task services while retaining their durable records:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/lab-services.ps1 -Action Stop
```

PostgreSQL uses `pg_ctl` against the selected data directory; RabbitMQ uses its named node's control command. The script never recursively deletes data. For a clean final run, stop the current lab, stop the API/edge/PLC processes, select a new task-scoped data directory with `-DataRoot`, and configure application persistence to use a fresh corresponding namespace. Reusing default ports requires the previous stack to be stopped first. Starting against an occupied unowned PostgreSQL port is rejected before cluster initialization.

Default locations:

| Path | Contents |
| --- | --- |
| `artifacts/lab-tools/downloads/` | Verified portable archives |
| `artifacts/lab-tools/pgsql/` | PostgreSQL executables |
| `artifacts/lab-tools/erlang/` | Erlang runtime |
| `artifacts/lab-tools/rabbitmq_server-4.3.6/` | RabbitMQ executables and plugins |
| `artifacts/lab-services/postgres-data/` | Durable PostgreSQL cluster |
| `artifacts/lab-services/rabbitmq/` | RabbitMQ configuration, journal and logs |
| `artifacts/lab-services/postgres.log` | PostgreSQL server log |
| `artifacts/lab-services/rabbitmq.stdout.log` | RabbitMQ startup/console log |
| `artifacts/lab-services/rabbitmq.stderr.log` | RabbitMQ launcher errors |

If a port is occupied, inspect its owner before changing ports or stopping processes. If a checksum fails, retain the failed download as evidence and obtain the expected official release again; do not silently disable verification. Existing task data is intentionally retained across stop/start for recovery tests.
