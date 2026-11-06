"""The ``dreep-mcp`` command: serve over stdio (default) or streamable HTTP.

dreep-mcp                                   # stdio, for desktop and IDE clients
dreep-mcp --transport http --port 8000      # http://127.0.0.1:8000/mcp
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from typing import Final

import anyio
import uvicorn
from dreep import AsyncDreep, DreepError
from mcp.server.mcpserver import MCPServer

from dreep_mcp import _constants as c
from dreep_mcp._http_auth import ASGIApp, BearerTokenMiddleware
from dreep_mcp._server import create_server
from dreep_mcp._settings import Settings
from dreep_mcp._version import __version__

EXIT_USAGE: Final = 2
_PUBLIC_WITHOUT_TOKEN: Final = (
    f"Refusing to serve on a non-loopback host without {c.ENV_HTTP_TOKEN}: anyone who can "
    "reach the port could act on your Dreep project. Set a token, or bind to 127.0.0.1.\n"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dreep-mcp", description="The Dreep MCP server.", epilog=__doc__
    )
    parser.add_argument(
        "--transport",
        choices=[t.value for t in c.Transport],
        default=c.Transport.STDIO.value,
        help="stdio for local clients (default), http for streamable HTTP.",
    )
    parser.add_argument("--host", default=c.DEFAULT_HOST, help="HTTP bind address.")
    parser.add_argument("--port", type=int, default=c.DEFAULT_PORT, help="HTTP port.")
    parser.add_argument("--path", default=c.DEFAULT_HTTP_PATH, help="HTTP endpoint path.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def http_app(server: MCPServer, settings: Settings, *, host: str, path: str) -> ASGIApp:
    """The streamable-HTTP ASGI app, behind the bearer-token guard when one is set."""
    app: ASGIApp = server.streamable_http_app(
        streamable_http_path=path, host=host, max_request_body_size=c.MAX_HTTP_BODY_BYTES
    )
    return BearerTokenMiddleware(app, settings.http_token) if settings.http_token else app


async def _serve(
    server: MCPServer, client: AsyncDreep, settings: Settings, args: argparse.Namespace
) -> None:
    try:
        if args.transport == c.Transport.STDIO.value:
            await server.run_stdio_async()
            return
        app = http_app(server, settings, host=args.host, path=args.path)
        await uvicorn.Server(uvicorn.Config(app, host=args.host, port=args.port)).serve()
    finally:
        await client.aclose()


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    transport = c.Transport(args.transport)
    settings = Settings.from_env(transport=transport)
    if (
        transport is c.Transport.HTTP
        and args.host not in c.LOOPBACK_HOSTS
        and not settings.http_token
    ):
        parser.exit(EXIT_USAGE, _PUBLIC_WITHOUT_TOKEN)
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    try:
        client = AsyncDreep()
    except DreepError as error:
        parser.exit(EXIT_USAGE, f"{error}\n")
    anyio.run(_serve, create_server(settings, client), client, settings, args)
