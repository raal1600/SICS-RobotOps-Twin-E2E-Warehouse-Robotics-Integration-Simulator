"""Scoped native lab processes over existing PostgreSQL/RabbitMQ services.

Run ``uv run python -m tools.lab_stack --fresh`` and keep this supervisor alive.
Ctrl+C stops only its own PLC/edge/WMS/API children; durable evidence is retained.
"""

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Any, TextIO
from uuid import uuid4

import httpx
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo

from robotops.lab.config import LabConfig
from robotops.lab.opcua import OPCClient

ROOT = Path(__file__).resolve().parents[1]


def available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


class LabStack:
    def __init__(
        self,
        config: LabConfig,
        directory: Path,
        *,
        api_port: int = 0,
        wms_port: int = 0,
        opc_port: int = 0,
        runtime: str = "synthetic",
    ):
        self.directory = directory.resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.api_port = api_port or available_port()
        self.wms_port = wms_port or available_port()
        self.opc_port = opc_port or available_port()
        self.edge_port = available_port()
        self.origin = f"http://127.0.0.1:{self.api_port}"
        self.runtime = runtime
        self.config = replace(
            config,
            opcua_url=f"opc.tcp://127.0.0.1:{self.opc_port}/robotops/",
            wms_url=f"http://127.0.0.1:{self.wms_port}",
            edge_url=f"http://127.0.0.1:{self.edge_port}",
            journal_path=self.directory / "plc.db",
        )
        self.processes: dict[str, subprocess.Popen[bytes]] = {}
        self.service_process_ids: dict[str, int] = {}
        self.health_failures: dict[str, str] = {}
        self.logs: list[TextIO] = []

    def launch(self, name: str, args: list[str]) -> None:
        environment = {
            **os.environ,
            "ROBOTOPS_POSTGRES_DSN": self.config.postgres_dsn,
            "ROBOTOPS_AMQP_URL": self.config.amqp_url,
            "ROBOTOPS_OPCUA_URL": self.config.opcua_url,
            "ROBOTOPS_WMS_URL": self.config.wms_url,
            "ROBOTOPS_EDGE_URL": self.config.edge_url,
            "ROBOTOPS_PLC_JOURNAL": str(self.config.journal_path),
            "ROBOTOPS_LAB_DATA": str(self.directory),
            "ROBOTOPS_AMQP_QUEUE": self.config.queue,
            "ROBOTOPS_AMQP_ROUTING_KEY": self.config.routing_key,
            "ROBOTOPS_AMQP_EXCHANGE": self.config.exchange,
            "ROBOTOPS_LAB_RUNTIME": self.runtime,
        }
        log = (self.directory / f"{name}.log").open("w", encoding="utf-8")
        self.logs.append(log)
        self.processes[name] = subprocess.Popen(
            [sys.executable, *args],
            cwd=ROOT,
            env=environment,
            stdout=log,
            stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )

    def healthy(self) -> bool:
        if any(process.poll() is not None for process in self.processes.values()):
            failed = [
                name for name, process in self.processes.items() if process.poll() is not None
            ]
            raise RuntimeError("LAB_CHILD_EXITED: " + ",".join(failed))
        failures = {}
        for name, origin in {
            "api": self.origin,
            "wms": self.config.wms_url,
            "edge": self.config.edge_url,
        }.items():
            try:
                response = httpx.get(origin + "/health", timeout=3)
                if not response.is_success:
                    failures[name] = f"HTTP_{response.status_code}"
                else:
                    self.service_process_ids[name] = int(response.json()["process_id"])
            except (httpx.TransportError, ValueError, KeyError) as exc:
                # Exception text can contain connection details. Persist only its type.
                failures[name] = type(exc).__name__
        try:
            with psycopg.connect(self.config.postgres_dsn, connect_timeout=2) as db:
                row = db.execute(
                    "SELECT 1 FROM lab_edge_health WHERE queue=%s "
                    "AND heartbeat > now() - interval '15 seconds'",
                    (self.config.queue,),
                ).fetchone()
            if not row:
                failures["broker_consumer"] = "HEARTBEAT_OLDER_THAN_15_SECONDS"
        except psycopg.Error as exc:
            failures["postgres"] = type(exc).__name__
        self.health_failures = failures
        return not failures

    def monitor(self, grace_seconds: float = 30, minimum_failures: int = 3) -> None:
        """Report temporary degradation; stop after a bounded sustained failure."""
        first_failure: float | None = None
        failures = 0
        while True:
            time.sleep(1)
            if self.healthy():
                if failures:
                    print(json.dumps({"status": "health_restored"}), flush=True)
                first_failure, failures = None, 0
                continue
            now = time.monotonic()
            first_failure = first_failure if first_failure is not None else now
            failures += 1
            elapsed = now - first_failure
            print(
                json.dumps(
                    {
                        "status": "degraded",
                        "failures": self.health_failures,
                        "consecutive_failures": failures,
                        "duration_seconds": round(elapsed, 1),
                    }
                ),
                flush=True,
            )
            if failures >= minimum_failures and elapsed >= grace_seconds:
                raise RuntimeError("LAB_HEALTH_LOST: " + json.dumps(self.health_failures))

    def start(self, timeout: float = 45) -> "LabStack":
        self.launch("plc", ["-m", "robotops.lab", "plc"])
        self.launch("edge", ["-m", "robotops.lab", "edge"])
        self.launch(
            "wms",
            [
                "-m",
                "uvicorn",
                "robotops.lab.business:create_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                str(self.wms_port),
            ],
        )
        self.launch(
            "api",
            [
                "-m",
                "uvicorn",
                "robotops.lab.api:create_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                str(self.api_port),
            ],
        )
        deadline = time.monotonic() + timeout
        try:
            while time.monotonic() < deadline:
                if self.healthy():
                    try:
                        opc = OPCClient(self.config.opcua_url, 3).call()
                        self.service_process_ids["plc"] = int(opc["server_process_id"])
                        return self
                    except OSError:
                        pass
                time.sleep(0.1)
            raise TimeoutError("LAB_STARTUP_TIMEOUT_CHECK_SCOPED_LOGS")
        except BaseException:
            self.stop()
            raise

    def report(self) -> dict[str, Any]:
        return {
            "status": "degraded" if self.health_failures else "healthy",
            "api": self.origin,
            "wms": self.config.wms_url,
            "opcua": self.config.opcua_url,
            "edge": self.config.edge_url,
            "queue": self.config.queue,
            "runtime": self.runtime,
            "data_directory": str(self.directory),
            "processes": self.service_process_ids.copy(),
            "launcher_processes": {name: process.pid for name, process in self.processes.items()},
            "truth": "real PostgreSQL/AMQP/OPC UA/REST; simulated WMS/PLC/robot/sensors",
        }

    def stop(self) -> None:
        for process in reversed(list(self.processes.values())):
            if process.poll() is None:
                if sys.platform == "win32":
                    # A venv launcher can own another Python process. Terminate only
                    # the process tree we created, never other lab instances/services.
                    subprocess.run(
                        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                        check=False,
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )
                else:
                    process.terminate()
        for process in reversed(list(self.processes.values())):
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        for log in self.logs:
            log.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fresh", action="store_true", help="Create new schema/queue/data identity"
    )
    parser.add_argument("--data-dir", type=Path, default=Path("runs/lab-supervised"))
    parser.add_argument("--report", type=Path)
    parser.add_argument("--api-port", type=int, default=8000)
    parser.add_argument("--wms-port", type=int, default=8081)
    parser.add_argument("--opc-port", type=int, default=4840)
    parser.add_argument("--runtime", choices=["synthetic", "blender"], default="synthetic")
    args = parser.parse_args()
    config = LabConfig.from_env()
    directory = args.data_dir
    schema = None
    if args.fresh:
        identity = uuid4().hex
        schema = "lab_run_" + identity
        with psycopg.connect(config.postgres_dsn, autocommit=True) as db:
            db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        config = replace(
            config,
            postgres_dsn=make_conninfo(config.postgres_dsn, options=f"-c search_path={schema}"),
            queue="robotops.run." + identity,
            routing_key="run." + identity,
        )
        directory = directory / identity
    stack = LabStack(
        config,
        directory,
        api_port=args.api_port,
        wms_port=args.wms_port,
        opc_port=args.opc_port,
        runtime=args.runtime,
    ).start()
    report = {**stack.report(), "postgres_schema": schema}
    encoded = json.dumps(report, indent=2)
    print(encoded, flush=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(encoded + "\n", encoding="utf-8")
    try:
        stack.monitor()
    except KeyboardInterrupt:
        pass
    finally:
        stack.stop()


if __name__ == "__main__":
    main()
