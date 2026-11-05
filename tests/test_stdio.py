"""End to end: the installed command speaks MCP over stdio."""

from __future__ import annotations

import os
import sys

import pytest
from mcp import Client
from mcp.client.stdio import StdioServerParameters

from tests.support import API_KEY

pytestmark = pytest.mark.anyio


async def test_python_m_dreep_mcp_serves_tools_over_stdio() -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "dreep_mcp"],
        env={**os.environ, "DREEP_API_KEY": API_KEY, "DREEP_MCP_ALLOW_DELETE": "1"},
    )
    async with Client(params) as client:
        listing = await client.list_tools()
        result = await client.call_tool(
            "build_delivery_url",
            {"url": "https://cdn.example.com/a.jpg", "transform": {"format": "avif"}},
        )
    assert {"upload_file", "delete_media"} <= {tool.name for tool in listing.tools}
    assert result.structured_content == {"url": "https://cdn.example.com/a.jpg?format=avif"}
