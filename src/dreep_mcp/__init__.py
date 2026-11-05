"""The official Dreep MCP server.

Run ``dreep-mcp`` (or ``python -m dreep_mcp``) with ``DREEP_API_KEY`` set. To
embed it, build the server yourself::

    from dreep import AsyncDreep
    from dreep_mcp import Settings, create_server

    server = create_server(Settings.from_env(), AsyncDreep())
"""

from __future__ import annotations

from dreep_mcp._cli import main
from dreep_mcp._server import create_server
from dreep_mcp._settings import Settings
from dreep_mcp._version import __version__

__all__ = ["Settings", "__version__", "create_server", "main"]
