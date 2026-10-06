"""Independent services: python -m robotops.lab plc|edge|health."""

import argparse
import asyncio
import logging
import os
from urllib.parse import urlsplit

import httpx
import psycopg
import uvicorn

from robotops.http_server import UVICORN_LOOP
from robotops.lab.config import LabConfig
from robotops.lab.journal import PLCJournal
from robotops.lab.opcua import OPCClient, VirtualPLC


async def serve(config: LabConfig) -> None:
    server = VirtualPLC(config.opcua_url, PLCJournal(config.journal_path))
    await server.start()
    try:
        await asyncio.Event().wait()
    finally:
        await server.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("service", choices=["plc", "edge", "health", "edge-health"])
    arguments = parser.parse_args()
    config = LabConfig.from_env()
    logging.basicConfig(level=logging.WARNING)
    if arguments.service == "plc":
        asyncio.run(serve(config))
    elif arguments.service == "health":
        print(OPCClient(config.opcua_url).call()["state"])
    elif arguments.service == "edge-health":
        try:
            response = httpx.get(config.edge_url + "/health", timeout=3)
            response.raise_for_status()
        except httpx.HTTPError:
            raise SystemExit("EDGE_HTTP_UNAVAILABLE") from None
        with psycopg.connect(config.postgres_dsn, connect_timeout=5) as db:
            row = db.execute(
                "SELECT 1 FROM lab_edge_health WHERE queue=%s "
                "AND heartbeat > now() - interval '15 seconds'",
                (config.queue,),
            ).fetchone()
        if not row:
            raise SystemExit("EDGE_HEARTBEAT_MISSING")
        print("EDGE_HEALTHY")
    else:
        uvicorn.run(
            "robotops.lab.edge:create_app",
            factory=True,
            loop=UVICORN_LOOP,
            host=os.getenv("ROBOTOPS_EDGE_BIND_HOST", "127.0.0.1"),
            port=urlsplit(config.edge_url).port or 8082,
        )


if __name__ == "__main__":
    main()
