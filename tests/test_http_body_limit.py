"""The HTTP transport's request limit fits the largest inline file, and no more."""

from __future__ import annotations

import base64
import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
from mcp.server.mcpserver import MCPServer

from dreep_mcp import _cli
from dreep_mcp import _constants as c
from dreep_mcp._settings import Settings
from tests.conftest import MakeServer
from tests.support import ASSET_ID, Recorder, asset_payload, envelope

pytestmark = pytest.mark.anyio

HOST = "127.0.0.1"
BASE_URL = "http://127.0.0.1:8000"
PATH = "/mcp"
ACCEPT = {"Accept": "application/json, text/event-stream"}
PROTOCOL_VERSION = "2025-06-18"


def _rpc_result(response: httpx.Response) -> dict[str, Any]:
    """The JSON-RPC result carried in a server-sent-events response."""
    assert response.status_code == httpx.codes.OK, response.text
    data = next(
        line.removeprefix("data:")
        for line in response.text.splitlines()
        if line.startswith("data:") and line.removeprefix("data:").strip()
    )
    result: dict[str, Any] = json.loads(data)["result"]
    return result


@pytest.fixture
async def http(make_server: MakeServer, recorder: Recorder) -> AsyncIterator[httpx.AsyncClient]:
    """A client of the real ASGI app, with a session already initialised."""
    server: MCPServer = make_server(recorder)
    app = _cli.http_app(server, Settings(), host=HOST, path=PATH)
    transport = httpx.ASGITransport(app=app)
    client = httpx.AsyncClient(transport=transport, base_url=BASE_URL, headers=ACCEPT)
    async with server.session_manager.run(), client:
        initialised = await client.post(
            PATH,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "0"},
                },
            },
        )
        _rpc_result(initialised)
        client.headers["mcp-session-id"] = initialised.headers["mcp-session-id"]
        client.headers["mcp-protocol-version"] = PROTOCOL_VERSION
        yield client


@pytest.fixture
def recorder() -> Recorder:
    return Recorder(envelope(asset_payload(), 201))


async def test_the_largest_inline_file_reaches_the_api(
    http: httpx.AsyncClient, recorder: Recorder
) -> None:
    content = base64.b64encode(bytes(c.MAX_INLINE_BYTES)).decode()
    response = await http.post(
        PATH,
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "upload_file",
                "arguments": {"content_base64": content, "filename": "a.bin"},
            },
        },
    )
    result = _rpc_result(response)
    assert not result.get("isError"), result
    assert result["structuredContent"]["id"] == ASSET_ID
    assert len(recorder.last.content) > c.MAX_INLINE_BYTES


@pytest.mark.parametrize(
    ("size", "allowed"),
    [(c.MAX_HTTP_BODY_BYTES, True), (c.MAX_HTTP_BODY_BYTES + 1, False)],
)
async def test_the_request_limit_is_enforced(
    http: httpx.AsyncClient, size: int, allowed: bool
) -> None:
    response = await http.post(
        PATH, content=b" " * size, headers={"Content-Type": "application/json"}
    )
    assert (response.status_code != httpx.codes.REQUEST_ENTITY_TOO_LARGE) is allowed


def test_the_limit_fits_the_largest_inline_file_and_its_envelope() -> None:
    encoded = len(base64.b64encode(bytes(c.MAX_INLINE_BYTES)))
    assert encoded + c.HTTP_BODY_OVERHEAD_BYTES == c.MAX_HTTP_BODY_BYTES
