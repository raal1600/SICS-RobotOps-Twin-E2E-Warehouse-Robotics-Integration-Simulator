"""Desktop child: bind an OS-selected loopback port and drain on a private stop file."""

import argparse
import asyncio
import json
import os
import socket
from pathlib import Path

import uvicorn

from apps.api.app import create_app
from robotops.blender.adapter import BlenderRuntime
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


async def serve(data: Path, session: Path, identity: str, runtime_name: str) -> None:
    session.mkdir(parents=True, exist_ok=True)
    store = Store(data / "workflow.db")
    runtime = (BlenderRuntime if runtime_name == "blender" else SyntheticRuntime)(
        data / "runtime.db", Settings(visual_frame_seconds=1 / 24)
    )
    engine = Engine(store, runtime)
    engine.recover()  # Original journal + fresh observation; never replay an uncertain pick.
    server = uvicorn.Server(
        uvicorn.Config(create_app(store, engine), log_level="info", timeout_graceful_shutdown=15)
    )
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.setblocking(False)
        port = listener.getsockname()[1]

        async def lifecycle() -> None:
            while not server.started:
                if (session / "stop").exists():
                    server.should_exit = True
                    return
                await asyncio.sleep(0.05)
            ready = {
                "session_id": identity,
                "pid": os.getpid(),
                "origin": f"http://127.0.0.1:{port}",
                "runtime": runtime_name,
                "data_dir": str(data.resolve()),
            }
            temporary = session / "ready.tmp"
            temporary.write_text(json.dumps(ready), encoding="utf-8")
            temporary.replace(session / "ready.json")
            while not (session / "stop").exists():
                await asyncio.sleep(0.1)
            server.should_exit = True

        monitor = asyncio.create_task(lifecycle())
        try:
            await server.serve(sockets=[listener])
        finally:
            monitor.cancel()
            await asyncio.gather(monitor, return_exceptions=True)
            (session / "stopped.json").write_text(
                json.dumps({"session_id": identity, "pid": os.getpid(), "server_exited": True}),
                encoding="utf-8",
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--session-dir", type=Path, required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--runtime", choices=["blender", "headless"], default="blender")
    args = parser.parse_args()
    asyncio.run(
        serve(args.data_dir.resolve(), args.session_dir.resolve(), args.session_id, args.runtime)
    )


if __name__ == "__main__":
    main()
