"""upload_file, create_upload_url and confirm_upload, through an MCP client."""

from __future__ import annotations

import base64
from pathlib import Path

import httpx
import pytest

from dreep_mcp import _constants as c
from tests.conftest import MakeServer
from tests.support import (
    ASSET_ID,
    ASSET_URL,
    Recorder,
    asset_payload,
    body_json,
    call_error,
    call_ok,
    envelope,
    form_fields,
)

pytestmark = pytest.mark.anyio


async def test_upload_from_path_returns_the_asset(make_server: MakeServer, tmp_path: Path) -> None:
    image = tmp_path / "hero.jpg"
    image.write_bytes(b"jpeg-bytes")
    rec = Recorder(envelope(asset_payload(), 201))
    result = await call_ok(
        make_server(rec),
        "upload_file",
        {"path": str(image), "folder": "marketing/2026", "transform": {"width": 800}},
    )
    assert result["id"] == ASSET_ID
    assert result["url"] == ASSET_URL
    assert result["size_bytes"] == 245000
    assert result["created_at"].startswith("2026-08-16")
    assert "raw" not in result
    fields = form_fields(rec.last)
    assert (fields["folder"], fields["width"]) == ("marketing/2026", "800")
    assert b"jpeg-bytes" in rec.last.content


async def test_upload_inline_content(make_server: MakeServer) -> None:
    rec = Recorder(envelope(asset_payload(), 201))
    content = base64.b64encode(b"hello").decode()
    await call_ok(make_server(rec), "upload_file", {"content_base64": content, "filename": "a.txt"})
    assert b'filename="a.txt"' in rec.last.content


async def test_large_files_use_a_presigned_upload(
    make_server: MakeServer, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(c, "PRESIGNED_THRESHOLD_BYTES", 4)
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"0123456789")
    rec = Recorder(
        envelope({"id": "up_1", "uploadUrl": "https://storage.example/put"}, 201),
        httpx.Response(200),
        envelope(asset_payload()),
    )
    await call_ok(make_server(rec), "upload_file", {"path": str(video)})
    presign, put, confirm = rec.requests
    assert body_json(presign)["sizeBytes"] == 10
    assert (put.method, put.content) == ("PUT", b"0123456789")
    assert confirm.url.path.endswith("/upload/up_1/confirm")


async def test_api_errors_reach_the_agent(make_server: MakeServer) -> None:
    rec = Recorder(httpx.Response(413, json={"message": "File too large", "code": "LIMIT"}))
    content = base64.b64encode(b"x").decode()
    message = await call_error(
        make_server(rec), "upload_file", {"content_base64": content, "filename": "x.bin"}
    )
    assert "File too large" in message


async def test_create_upload_url_and_confirm(make_server: MakeServer) -> None:
    rec = Recorder(
        envelope({"id": "up_2", "uploadUrl": "https://storage.example/put"}, 201),
        envelope(asset_payload()),
    )
    server = make_server(rec)
    presigned = await call_ok(
        server,
        "create_upload_url",
        {"content_type": "video/mp4", "size_bytes": 2048, "filename": "clip.mp4"},
    )
    assert presigned["upload_url"] == "https://storage.example/put"
    assert presigned["already_exists"] is False
    asset = await call_ok(
        server, "confirm_upload", {"upload_id": "up_2", "transform": {"format": "webm"}}
    )
    assert asset["id"] == ASSET_ID
    assert body_json(rec.last) == {"transform": {"format": "webm"}}
