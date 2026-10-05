"""An actual OPC UA server process crash retains the claimed command identity."""

import os
import socket
import subprocess
import sys
import time

from robotops.lab.opcua import OPCClient


def test_opc_server_process_restart_does_not_regrant_effect(tmp_path, lab_command):
    command, runtime = lab_command
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    endpoint = f"opc.tcp://127.0.0.1:{port}/robotops/"
    environment = {
        **os.environ,
        "ROBOTOPS_POSTGRES_DSN": "postgresql://unused@127.0.0.1/unused",
        "ROBOTOPS_AMQP_URL": "amqp://unused@127.0.0.1/",
        "ROBOTOPS_OPCUA_URL": endpoint,
        "ROBOTOPS_PLC_JOURNAL": str(tmp_path / "retained-plc.db"),
    }
    client = OPCClient(endpoint, timeout=0.5)

    def start(log):
        process = subprocess.Popen(
            [sys.executable, "-m", "robotops.lab", "plc"],
            env=environment,
            stdout=log,
            stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            assert process.poll() is None, "PLC exited before becoming ready"
            try:
                client.call()
                return process
            except OSError:
                time.sleep(0.1)
        process.terminate()
        process.wait(10)
        raise AssertionError("OPC UA server startup timeout")

    with (tmp_path / "plc-process.log").open("w") as log:
        process = start(log)
        try:
            first = client.call("SubmitJob", command.model_dump_json())
            client.call("CheckPreconditions", command.command_id, runtime.world().model_dump_json())
            assert client.call("BeginExecution", command.command_id)["execute"]
            receipt = runtime.apply(command)
            # Stop the process before ReportResult reaches PLC retained memory.
            process.terminate()
            process.wait(10)
            process = start(log)
            assert client.call()["state"] == "EXECUTING"
            retained = client.call("GetJobStatus", command.command_id)
            assert retained["state"] == "EXECUTING"
            assert retained["boot_id"] != first["boot_id"]
            assert client.call("SubmitJob", command.model_dump_json())["duplicate"]
            assert not client.call("BeginExecution", command.command_id)["execute"]
            client.call("ReportResult", command.command_id, receipt.model_dump_json())
            result = client.call("GetJobStatus", command.command_id)
            assert result["result"]["effect_count"] == 1
            assert runtime.world().step == 1
        finally:
            process.terminate()
            process.wait(10)
