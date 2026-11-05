"""list_media and the opt-in delete_media."""

from __future__ import annotations

import httpx
import pytest

from tests.conftest import MakeServer
from tests.support import ASSET_ID, Recorder, call_error, call_ok, envelope

pytestmark = pytest.mark.anyio


async def test_list_media_passes_filters_and_returns_pagination(make_server: MakeServer) -> None:
    rec = Recorder(
        envelope(
            {
                "assets": [
                    {"id": ASSET_ID, "url": "https://cdn.example/a.webp", "type": "image/webp"}
                ],
                "pagination": {"page": 2, "limit": 10, "total": 11},
            }
        )
    )
    result = await call_ok(
        make_server(rec), "list_media", {"page": 2, "limit": 10, "folder": "avatars"}
    )
    assert result["pagination"] == {"page": 2, "limit": 10, "total": 11}
    assert result["assets"][0]["mimetype"] == "image/webp"
    assert rec.last.url.params["folder"] == "avatars"


async def test_delete_media_when_allowed(make_server: MakeServer) -> None:
    rec = Recorder(httpx.Response(204))
    result = await call_ok(make_server(rec, allow_delete=True), "delete_media", {"media_id": "m1"})
    assert result == {"id": "m1", "deleted": True}
    assert (rec.last.method, rec.last.url.path.rsplit("/", 1)[-1]) == ("DELETE", "m1")


async def test_delete_rejects_ids_that_would_change_the_endpoint(make_server: MakeServer) -> None:
    message = await call_error(
        make_server(allow_delete=True), "delete_media", {"media_id": "../usage"}
    )
    assert "Invalid id" in message
