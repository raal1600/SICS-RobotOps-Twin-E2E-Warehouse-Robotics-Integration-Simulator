"""The configured HTTP loop releases connections after an abrupt peer reset."""

import asyncio
import socket
import struct
import sys
import time

import pytest
import uvicorn

from robotops.http_server import UVICORN_LOOP


async def application(scope, receive, send):
    if scope["type"] == "http":
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-length", b"2")],
            }
        )
        await send({"type": "http.response.body", "body": b"OK"})
    elif scope["type"] == "websocket":
        assert (await receive())["type"] == "websocket.connect"
        await send({"type": "websocket.accept"})
        while (await receive())["type"] != "websocket.disconnect":
            pass


class ResetOnShutdown:
    """Only the installed Proactor cleanup path attempts this socket operation."""

    def __init__(self, underlying):
        self.underlying = underlying
        self.shutdown_calls = 0

    def __getattr__(self, name):
        return getattr(self.underlying, name)

    def shutdown(self, how):
        self.shutdown_calls += 1
        raise ConnectionResetError(10054, "injected peer reset during socket shutdown")


async def reset_and_stop(config, protocol, inject_shutdown_reset):
    loop = asyncio.get_running_loop()
    errors = []
    previous_handler = loop.get_exception_handler()
    loop.set_exception_handler(lambda _, context: errors.append(context))
    service = uvicorn.Server(config)
    wrappers = []
    with socket.socket() as listener, socket.socket() as client:
        listener.bind(("127.0.0.1", 0))
        listener.setblocking(False)
        serve = asyncio.create_task(service.serve(sockets=[listener]))
        try:
            deadline = time.monotonic() + 5
            while not service.started and not serve.done() and time.monotonic() < deadline:
                await asyncio.sleep(0.01)
            assert service.started, "HTTP lifecycle test server did not start"
            client.setblocking(False)
            await loop.sock_connect(client, listener.getsockname())
            if protocol == "http":
                request = b"GET / HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: keep-alive\r\n\r\n"
                expected_status = b"HTTP/1.1 200 OK"
            else:
                request = (
                    b"GET /stream HTTP/1.1\r\nHost: 127.0.0.1\r\n"
                    b"Upgrade: websocket\r\nConnection: Upgrade\r\n"
                    b"Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
                    b"Sec-WebSocket-Version: 13\r\n\r\n"
                )
                expected_status = b"HTTP/1.1 101 Switching Protocols"
            await loop.sock_sendall(client, request)
            response = bytearray()
            while b"\r\n\r\n" not in response:
                chunk = await asyncio.wait_for(loop.sock_recv(client, 8192), timeout=3)
                assert chunk, "Server closed before its HTTP response/WS upgrade"
                response.extend(chunk)
            assert response.split(b"\r\n", 1)[0] == expected_status
            assert len(service.server_state.connections) == 1
            if inject_shutdown_reset:
                # Reproduce the recorded Windows failure at its exact socket
                # boundary, without patching asyncio or swallowing loop errors.
                for connection in service.server_state.connections:
                    wrapper = ResetOnShutdown(connection.transport._sock)
                    connection.transport._sock = wrapper
                    wrappers.append(wrapper)
            linger_format = "hh" if sys.platform == "win32" else "ii"
            client.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack(linger_format, 1, 0))
            client.close()
            await asyncio.sleep(0.025)
            service.should_exit = True
            # No graceful-shutdown timeout, force_exit or task cancellation may
            # turn a leaked transport into a successful test.
            await asyncio.wait_for(asyncio.shield(serve), timeout=5)
            await asyncio.sleep(0)
            assert not errors, errors
            assert not service.server_state.connections
            assert not service.server_state.tasks
            assert all(not server._clients for server in service.servers)
            if inject_shutdown_reset:
                assert wrappers
                assert all(wrapper.shutdown_calls == 0 for wrapper in wrappers)
        finally:
            # On regression failure, clean only this test's owned resources so
            # the already-failing case cannot leak into later tests. This is
            # diagnostic cleanup, never a successful shutdown path.
            client.close()
            if not serve.done():
                serve.cancel()
            await asyncio.gather(serve, return_exceptions=True)
            for task in tuple(service.server_state.tasks):
                task.cancel()
            await asyncio.gather(*tuple(service.server_state.tasks), return_exceptions=True)
            for server in getattr(service, "servers", []):
                server.close()
                for transport in tuple(server._clients):
                    underlying = getattr(transport, "_sock", None)
                    if underlying is not None:
                        underlying.close()
                        transport._sock = None
                    server._detach(transport)
                    transport._server = None
            await asyncio.sleep(0)
            loop.set_exception_handler(previous_handler)


@pytest.mark.parametrize("protocol", ["http", "websocket"])
@pytest.mark.parametrize(
    "inject_shutdown_reset", [False, True], ids=["peer-reset", "shutdown-reset"]
)
def test_http_server_peer_reset_exits_cleanly(protocol, inject_shutdown_reset):
    config = uvicorn.Config(
        application,
        loop=UVICORN_LOOP,
        lifespan="off",
        log_level="error",
        access_log=False,
        timeout_graceful_shutdown=None,
    )
    # Use the same documented custom-loop import that server.run/native CLI use.
    asyncio.run(
        reset_and_stop(config, protocol, inject_shutdown_reset),
        loop_factory=config.get_loop_factory(),
    )
