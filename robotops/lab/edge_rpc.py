"""API-to-edge bounded control calls. Only the edge process opens OPC UA sessions."""

import json
from collections.abc import Callable
from typing import Any

import httpx

from robotops.lab.config import LabConfig
from robotops.workflow.store import Conflict


class EdgeRPC:
    def __init__(self, config: LabConfig):
        self.config = config

    def call(self, method: str | None = None, *args: Any) -> dict[str, Any]:
        try:
            response = httpx.post(
                self.config.edge_url + "/v1/opcua",
                json={
                    "method": method,
                    "arguments": args,
                },
                timeout=self.config.timeout + 5,
            )
        except httpx.TransportError:
            raise OSError("EDGE_RPC_UNAVAILABLE_NO_DIRECT_OPCUA_FALLBACK") from None
        if response.status_code == 409:
            raise Conflict(str(response.json().get("detail", "EDGE_COMMAND_REJECTED")))
        if response.status_code >= 500:
            raise OSError("EDGE_OPCUA_UNAVAILABLE_QUERY_ORIGINAL_COMMAND")
        response.raise_for_status()
        return dict(response.json())

    def execute(self, command_id: str, callback: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        permit = self.call("BeginExecution", command_id)
        if not permit.get("execute"):
            if permit.get("result"):
                return dict(permit["result"])
            raise TimeoutError("EXECUTION_ALREADY_CLAIMED_QUERY_ORIGINAL_JOURNAL")
        # This is the same existing runtime callback, reached only after a durable
        # PLC claim obtained by the separate edge process. Never retry it here.
        receipt = callback()
        self.call("ReportResult", command_id, json.dumps(receipt))
        return receipt
