"""Builds the MCP server: one Dreep client, every tool group registered on it."""

from __future__ import annotations

from collections.abc import Callable
from typing import Final

from dreep import AsyncDreep
from mcp.server.mcpserver import MCPServer

from dreep_mcp import _constants as c
from dreep_mcp._settings import Settings
from dreep_mcp._tool_host import ToolHost
from dreep_mcp._tools_media import register_media_tools
from dreep_mcp._tools_processing import register_processing_tools
from dreep_mcp._tools_project import register_project_tools
from dreep_mcp._tools_uploads import register_upload_tools
from dreep_mcp._tools_urls import register_url_tools
from dreep_mcp._version import __version__

TOOL_GROUPS: Final[tuple[Callable[[ToolHost], None], ...]] = (
    register_upload_tools,
    register_media_tools,
    register_processing_tools,
    register_url_tools,
    register_project_tools,
)

INSTRUCTIONS: Final = """\
Dreep stores, transforms and delivers images, videos, audio and documents.

- Upload with upload_file (a local path, or base64 content). The result's `url`
  is the delivery URL; always use URLs exactly as Dreep returns them, never
  build one by hand (projects can be on a custom CDN domain).
- To resize, crop, convert or compress, call build_delivery_url with a
  transform. Nothing is re-uploaded: the CDN transforms on the fly.
- For assets in signed folders, use build_signed_url.
- remove_background, extract_text (OCR) and convert_document each take a file.
- Folders and presets organise the project; get_usage reports storage.
- Delete tools exist only when the server sets DREEP_MCP_ALLOW_DELETE; deletes
  are permanent, so confirm with the user first.
"""


def create_server(settings: Settings, client: AsyncDreep) -> MCPServer:
    """The Dreep MCP server, calling the API through ``client``.

    The caller owns ``client`` and closes it once the server stops.
    """
    server: MCPServer = MCPServer(
        c.SERVER_NAME,
        title=c.SERVER_TITLE,
        instructions=INSTRUCTIONS,
        website_url=c.WEBSITE_URL,
        version=__version__,
    )
    host = ToolHost(server, client, settings)
    for register in TOOL_GROUPS:
        register(host)
    return server
