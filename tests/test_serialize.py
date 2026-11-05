"""to_json / to_result: SDK models become plain JSON objects."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from dreep import Asset, MediaPage

from dreep_mcp._serialize import to_json, to_result


def test_models_drop_raw_and_render_datetimes() -> None:
    asset = Asset._from_api(
        {"id": "a", "url": "https://cdn.example/a", "createdAt": "2026-01-02T03:04:05Z"}
    )
    result = to_result(asset)
    assert result["id"] == "a"
    assert "raw" not in result
    assert result["created_at"] == datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc).isoformat()


def test_nested_models_and_sequences() -> None:
    page = MediaPage._from_api({"assets": [{"id": "a", "url": "u"}], "pagination": {"total": 1}})
    assert to_json(page)["assets"][0]["id"] == "a"
    assert to_json((1, "x", b"b")) == [1, "x", b"b"]


def test_results_must_be_objects() -> None:
    with pytest.raises(TypeError, match="object-shaped"):
        to_result([1, 2])
