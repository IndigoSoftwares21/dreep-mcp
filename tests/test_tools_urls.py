"""build_delivery_url and build_signed_url: pure string work."""

from __future__ import annotations

import hashlib
import hmac
from urllib.parse import parse_qs, urlsplit

import pytest

from tests.conftest import MakeServer
from tests.support import ASSET_ID, ASSET_URL, SIGNING_SECRET, call_error, call_ok

pytestmark = pytest.mark.anyio


async def test_delivery_url_applies_a_sorted_transform(make_server: MakeServer) -> None:
    result = await call_ok(
        make_server(),
        "build_delivery_url",
        {"url": ASSET_URL, "transform": {"width": 400, "format": "webp", "fit": "cover"}},
    )
    assert result["url"] == f"{ASSET_URL}?fit=cover&format=webp&width=400"


async def test_delivery_url_keeps_custom_cdn_domains(make_server: MakeServer) -> None:
    custom = "https://cdn.getscale.ng/api/v1/fetch/abc.jpg"
    result = await call_ok(make_server(), "build_delivery_url", {"url": custom})
    assert result["url"] == custom


async def test_delivery_url_rejects_relative_urls(make_server: MakeServer) -> None:
    message = await call_error(make_server(), "build_delivery_url", {"url": "/a.jpg"})
    assert "absolute" in message


async def test_signed_url_signs_id_and_expiry_only(make_server: MakeServer) -> None:
    result = await call_ok(
        make_server(),
        "build_signed_url",
        {
            "asset_id": ASSET_ID,
            "url": ASSET_URL,
            "expires_in_seconds": 300,
            "transform": {"width": 200},
        },
    )
    query = parse_qs(urlsplit(result["url"]).query)
    expires = query["exp"][0]
    expected = hmac.new(
        SIGNING_SECRET.encode(), f"{ASSET_ID}:{expires}".encode(), hashlib.sha256
    ).hexdigest()
    assert query["sig"] == [expected]
    assert query["width"] == ["200"]
