import asyncio
import sys
import traceback

import pytest
import uvicorn

from robotops.domain.models import OrderLine, OrderRequest
from robotops.http_server import UVICORN_LOOP


class HTTPTestServer(uvicorn.Server):
    """Use the product HTTP loop and retain failure-only shutdown diagnostics."""

    def __init__(self, config):
        config.loop = UVICORN_LOOP
        super().__init__(config)
        self.loop = None
        self.loop_errors = []
        self.server_errors = []

    async def serve(self, sockets=None):
        self.loop = asyncio.get_running_loop()

        def record_error(loop, context):
            error = context.get("exception")
            self.loop_errors.append(type(error).__name__ if error else context.get("message"))
            loop.default_exception_handler(context)

        self.loop.set_exception_handler(record_error)
        try:
            await super().serve(sockets=sockets)
        except BaseException as error:
            self.server_errors.append(type(error).__name__)
            raise

    def stop(self, thread, timeout):
        self.should_exit = True
        thread.join(timeout)
        if thread.is_alive() or self.loop_errors or self.server_errors:
            frame = sys._current_frames().get(thread.ident)
            tasks = []
            if self.loop is not None and not self.loop.is_closed():
                for task in asyncio.all_tasks(self.loop):
                    chain = []
                    pending = task.get_coro()
                    while pending is not None:
                        chain.append(getattr(pending, "__qualname__", type(pending).__name__))
                        pending = getattr(
                            pending, "cr_await", getattr(pending, "gi_yieldfrom", None)
                        )
                    tasks.append(chain)
            raise AssertionError(
                {
                    "message": "HTTP test server did not shut down cleanly",
                    "thread_alive": thread.is_alive(),
                    "loop_type": type(self.loop).__name__,
                    "loop_errors": self.loop_errors,
                    "server_errors": self.server_errors,
                    "connections": len(self.server_state.connections),
                    "request_tasks": len(self.server_state.tasks),
                    "retained_transports": [
                        len(getattr(server, "_clients", ()))
                        for server in getattr(self, "servers", ())
                    ],
                    "asyncio_tasks": tasks,
                    "thread_stack": traceback.format_stack(frame) if frame else [],
                }
            )


@pytest.fixture
def http_server():
    return HTTPTestServer


@pytest.fixture
def order_request():
    return OrderRequest(
        order_id="order-1",
        lines=(
            OrderLine(
                order_line_id="line-1",
                product_id="product-red",
                source_id="source",
                destination_id="destination",
            ),
        ),
    )
