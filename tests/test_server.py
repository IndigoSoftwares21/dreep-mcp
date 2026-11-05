"""The server as a whole: which tools exist, and how clients are told to treat them."""

from __future__ import annotations

import pytest
from mcp import Client
from mcp.server.mcpserver import MCPServer

from dreep_mcp._server import INSTRUCTIONS, TOOL_GROUPS
from dreep_mcp._tool_host import ToolHost
from tests.conftest import MakeServer

pytestmark = pytest.mark.anyio

DELETE_TOOLS = {"delete_media", "delete_preset"}
READ_TOOLS = {"list_media", "list_folders", "list_presets", "get_usage"}
LOCAL_TOOLS = {"build_delivery_url", "build_signed_url"}


async def _tools(server: MCPServer) -> dict[str, object]:
    async with Client(server) as client:
        listing = await client.list_tools()
    return {tool.name: tool for tool in listing.tools}


async def test_delete_tools_are_opt_in(make_server: MakeServer) -> None:
    default = await _tools(make_server())
    allowed = await _tools(make_server(allow_delete=True))
    assert not DELETE_TOOLS & default.keys()
    assert set(allowed) - set(default) == DELETE_TOOLS


async def test_annotations_tell_clients_what_is_safe(make_server: MakeServer) -> None:
    tools = await _tools(make_server(allow_delete=True))
    for name, tool in tools.items():
        hints = tool.annotations  # type: ignore[attr-defined]
        assert hints is not None, name
        assert hints.read_only_hint is (name in READ_TOOLS | LOCAL_TOOLS), name
        if name in DELETE_TOOLS:
            assert hints.destructive_hint is True
        if name in LOCAL_TOOLS:
            assert hints.open_world_hint is False


async def test_every_tool_is_described(make_server: MakeServer) -> None:
    tools = await _tools(make_server(allow_delete=True))
    assert len(tools) == 16
    assert all(tool.description for tool in tools.values())  # type: ignore[attr-defined]


async def test_server_identifies_itself() -> None:
    assert "build_delivery_url" in INSTRUCTIONS
    assert len(TOOL_GROUPS) == 5
    assert ToolHost.__dataclass_fields__.keys() == {"server", "client", "settings"}
