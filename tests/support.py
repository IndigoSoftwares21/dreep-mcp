"""Test helpers: canned API payloads, a recording transport, an MCP call helper."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx
from mcp import Client
from mcp.server.mcpserver import MCPServer
from mcp_types import CallToolResult

API_KEY = "drp_test_0123456789abcdef"
SIGNING_SECRET = "test_signing_secret"
CDN_BASE = "https://cdn.dreep.cloud/api/v1/fetch"
ASSET_ID = "2f928a3f-1d2a-4a2b-8a8b-123456789abc"
ASSET_URL = f"{CDN_BASE}/{ASSET_ID}.webp"

Handler = Callable[[httpx.Request], httpx.Response]


def envelope(data: Any, status: int = 200) -> httpx.Response:
    """A success response wrapped the way the API wraps them."""
    return httpx.Response(status, json={"message": "ok", "code": "OK", "data": data})


def asset_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "id": ASSET_ID,
        "url": ASSET_URL,
        "originalFilename": "hero.jpg",
        "mimetype": "image/webp",
        "sizeBytes": "245000",
        "status": "ready",
        "folder": "marketing/2026",
        "createdAt": "2026-08-16T18:53:29.000Z",
    }
    payload.update(overrides)
    return payload


def form_fields(request: httpx.Request) -> dict[str, str]:
    """The non-file fields of a multipart request, parsed crudely but sufficiently."""
    boundary = request.headers["content-type"].split("boundary=")[1].encode()
    fields = {}
    for part in request.content.split(b"--" + boundary):
        head, _, value = part.partition(b"\r\n\r\n")
        if b'name="' in head and b"filename=" not in head:
            name = head.split(b'name="')[1].split(b'"')[0].decode()
            fields[name] = value.rstrip(b"\r\n").decode()
    return fields


def body_json(request: httpx.Request) -> Any:
    return json.loads(request.content)


class Recorder:
    """A handler that records requests and answers from a scripted queue."""

    def __init__(self, *responses: httpx.Response) -> None:
        self.responses = list(responses)
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        request.read()
        self.requests.append(request)
        if not self.responses:
            raise AssertionError(f"Unexpected request: {request.method} {request.url}")
        return self.responses.pop(0)

    @property
    def last(self) -> httpx.Request:
        return self.requests[-1]


async def call(server: MCPServer, tool: str, arguments: dict[str, Any]) -> CallToolResult:
    async with Client(server) as client:
        return await client.call_tool(tool, arguments)


async def call_ok(server: MCPServer, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Calls a tool that must succeed and returns its structured result."""
    result = await call(server, tool, arguments)
    assert not result.is_error, error_text(result)
    assert result.structured_content is not None
    return dict(result.structured_content)


async def call_error(server: MCPServer, tool: str, arguments: dict[str, Any]) -> str:
    """Calls a tool that must fail and returns the message the agent sees."""
    result = await call(server, tool, arguments)
    assert result.is_error, result.structured_content
    return error_text(result)


def error_text(result: CallToolResult) -> str:
    return " ".join(getattr(block, "text", "") for block in result.content)
