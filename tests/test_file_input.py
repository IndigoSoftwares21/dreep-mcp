"""resolve_file: path vs inline content, size limits, and the file-root sandbox."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from dreep_mcp import _constants as c
from dreep_mcp._file_input import resolve_file
from dreep_mcp._settings import Settings


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def test_path_resolves_to_the_file(tmp_path: Path) -> None:
    file = tmp_path / "a.png"
    file.write_bytes(b"png")
    resolved = resolve_file(Settings(), str(file), None, "renamed.png")
    assert (resolved.source, resolved.filename, resolved.size) == (file, "renamed.png", 3)


def test_inline_content_decodes(tmp_path: Path) -> None:
    resolved = resolve_file(Settings(), None, _b64(b"hi"), "a.txt")
    assert (resolved.source, resolved.filename, resolved.size) == (b"hi", "a.txt", 2)


@pytest.mark.parametrize(
    ("path", "content", "filename", "message"),
    [
        (None, None, None, "exactly one"),
        ("x", _b64(b"x"), "a", "exactly one"),
        (None, _b64(b"x"), None, "filename is required"),
        (None, "not base64!", "a.txt", "not valid base64"),
        ("/definitely/missing.png", None, None, "No such file"),
    ],
)
def test_bad_arguments_explain_themselves(
    path: str | None, content: str | None, filename: str | None, message: str
) -> None:
    with pytest.raises(ToolError, match=message):
        resolve_file(Settings(), path, content, filename)


def test_inline_content_has_a_size_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(c, "MAX_INLINE_BYTES", 2)
    with pytest.raises(ToolError, match="limit"):
        resolve_file(Settings(), None, _b64(b"abc"), "a.txt")


def test_paths_outside_the_roots_are_refused(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    inside = allowed / "ok.txt"
    inside.write_text("ok")
    outside = tmp_path / "secret.txt"
    outside.write_text("secret")
    settings = Settings(file_roots=(allowed.resolve(),))
    assert resolve_file(settings, str(inside), None, None).size == 2
    with pytest.raises(ToolError, match="outside the allowed file roots"):
        resolve_file(settings, str(outside), None, None)
    with pytest.raises(ToolError, match="outside"):
        resolve_file(settings, str(allowed / ".." / "secret.txt"), None, None)


def test_local_paths_are_off_over_http_without_roots(tmp_path: Path) -> None:
    file = tmp_path / "a.txt"
    file.write_text("a")
    with pytest.raises(ToolError, match="disabled on this transport"):
        resolve_file(Settings(allow_any_local_path=False), str(file), None, None)
