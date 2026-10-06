"""Event loop for the single-process HTTP/WebSocket services and their tests."""

import asyncio
import sys

from uvicorn.loops.auto import auto_loop_factory

UVICORN_LOOP = "robotops.http_server:new_event_loop"


def new_event_loop() -> asyncio.AbstractEventLoop:
    """Avoid Windows Proactor reset cleanup leaving accepted sockets attached.

    This is scoped to the small local ASGI services, not a global loop policy.
    Windows Selector supports at most 512 sockets and no asyncio subprocesses;
    Blender runs through synchronous subprocess calls in worker threads.
    """
    if sys.platform == "win32":
        return asyncio.SelectorEventLoop()
    return auto_loop_factory(use_subprocess=False)()
