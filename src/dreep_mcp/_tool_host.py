"""What every tool group is registered with: the server, the client, the settings."""

from __future__ import annotations

from dataclasses import dataclass

from dreep import AsyncDreep
from mcp.server.mcpserver import MCPServer

from dreep_mcp._settings import Settings


@dataclass(frozen=True)
class ToolHost:
    server: MCPServer
    #: Owned by the caller of ``create_server``; tools only call it.
    client: AsyncDreep
    settings: Settings
