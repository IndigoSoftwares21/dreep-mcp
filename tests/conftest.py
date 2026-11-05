"""Shared fixtures: servers whose Dreep client talks to an in-memory transport."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Any

import httpx
import pytest
from dreep import AsyncDreep
from mcp.server.mcpserver import MCPServer

from dreep_mcp import Settings, create_server
from tests.support import API_KEY, SIGNING_SECRET, Recorder

MakeServer = Callable[..., MCPServer]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "DREEP_API_KEY",
        "DREEP_SIGNING_SECRET",
        "DREEP_API_URL",
        "DREEP_MCP_ALLOW_DELETE",
        "DREEP_MCP_FILE_ROOTS",
        "DREEP_MCP_HTTP_TOKEN",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def make_server() -> AsyncIterator[MakeServer]:
    """``make_server(recorder, **settings)``: a server wired to a scripted API."""
    clients: list[AsyncDreep] = []

    def factory(recorder: Recorder | None = None, **settings: Any) -> MCPServer:
        http = httpx.AsyncClient(transport=httpx.MockTransport(recorder or Recorder()))
        client = AsyncDreep(API_KEY, signing_secret=SIGNING_SECRET, http_client=http)
        clients.append(client)
        return create_server(Settings(**settings), client)

    yield factory
    for client in clients:
        await client._http.aclose()
