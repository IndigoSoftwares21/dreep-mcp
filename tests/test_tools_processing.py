"""remove_background, extract_text and convert_document."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import MakeServer
from tests.support import Recorder, call, call_ok, envelope, form_fields

pytestmark = pytest.mark.anyio


@pytest.fixture
def scan(tmp_path: Path) -> str:
    path = tmp_path / "scan.pdf"
    path.write_bytes(b"%PDF-1.7")
    return str(path)


async def test_remove_background(make_server: MakeServer, scan: str) -> None:
    rec = Recorder(envelope({"id": "bg1", "url": "https://cdn.example/bg1.png", "format": "png"}))
    result = await call_ok(make_server(rec), "remove_background", {"path": scan, "format": "png"})
    assert result["id"] == "bg1"
    assert rec.last.url.path.endswith("/bg-remove")


async def test_extract_text(make_server: MakeServer, scan: str) -> None:
    rec = Recorder(envelope({"text": "INVOICE 42", "blocks": []}))
    result = await call_ok(make_server(rec), "extract_text", {"path": scan, "include_blocks": True})
    assert result["text"] == "INVOICE 42"
    assert result["saved_asset"] is None


async def test_convert_document(make_server: MakeServer, scan: str) -> None:
    payload = {"id": "d1", "url": "https://cdn.example/d1.docx", "status": "ready"}
    rec = Recorder(envelope(payload, 201))
    result = await call_ok(make_server(rec), "convert_document", {"path": scan, "format": "docx"})
    assert result["status"] == "ready"
    assert form_fields(rec.last)["format"] == "docx"


async def test_unknown_format_is_rejected_by_the_schema(make_server: MakeServer, scan: str) -> None:
    result = await call(make_server(), "convert_document", {"path": scan, "format": "exe"})
    assert result.is_error
