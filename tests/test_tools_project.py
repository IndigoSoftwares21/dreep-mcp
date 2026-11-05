"""Folders, presets and usage."""

from __future__ import annotations

import httpx
import pytest

from tests.conftest import MakeServer
from tests.support import Recorder, body_json, call, call_error, call_ok, envelope

pytestmark = pytest.mark.anyio

PRESET = {"id": "p1", "key": "thumb", "name": "Thumb", "params": {"width": 200, "format": "webp"}}


async def test_create_folder_with_access_control(make_server: MakeServer) -> None:
    rec = Recorder(envelope({"id": "f1", "name": "Private", "accessControlType": "signed"}, 201))
    result = await call_ok(
        make_server(rec),
        "create_folder",
        {"name": "Private", "access_control_type": "signed", "default_expiry_seconds": 600},
    )
    assert result["access_control_type"] == "signed"
    assert body_json(rec.last)["accessControlType"] == "signed"


async def test_list_folders(make_server: MakeServer) -> None:
    rec = Recorder(envelope({"folders": [{"id": "f1", "path": "avatars"}]}))
    result = await call_ok(make_server(rec), "list_folders", {"root_only": True})
    assert result["folders"][0]["path"] == "avatars"
    assert result["current_folder"] is None


async def test_create_preset_requires_a_format(make_server: MakeServer) -> None:
    message = await call_error(
        make_server(), "create_preset", {"key": "thumb", "name": "Thumb", "transform": {"width": 1}}
    )
    assert "format" in message


async def test_create_preset_validates_the_key_in_the_schema(make_server: MakeServer) -> None:
    result = await call(
        make_server(),
        "create_preset",
        {"key": "Thumb-1", "name": "Thumb", "transform": {"format": "webp"}},
    )
    assert result.is_error


async def test_create_and_list_presets(make_server: MakeServer) -> None:
    rec = Recorder(envelope(PRESET, 201), envelope({"presets": [PRESET]}))
    server = make_server(rec)
    created = await call_ok(
        server,
        "create_preset",
        {"key": "thumb", "name": "Thumb", "transform": {"width": 200, "format": "webp"}},
    )
    assert created["key"] == "thumb"
    listed = await call_ok(server, "list_presets", {})
    assert listed["presets"][0]["params"] == PRESET["params"]


async def test_get_usage(make_server: MakeServer) -> None:
    rec = Recorder(envelope({"storageBytes": "1048576", "imageCount": 3}))
    result = await call_ok(make_server(rec), "get_usage", {})
    assert (result["storage_bytes"], result["image_count"]) == (1048576, 3)


async def test_delete_preset_when_allowed(make_server: MakeServer) -> None:
    rec = Recorder(httpx.Response(204))
    result = await call_ok(
        make_server(rec, allow_delete=True), "delete_preset", {"preset_id": "p1"}
    )
    assert result == {"id": "p1", "deleted": True}
