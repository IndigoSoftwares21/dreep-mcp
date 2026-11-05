"""Turns a tool's file arguments into something the SDK can upload.

A file arrives either as a local ``path`` or as inline ``content_base64``.
Paths are checked against the configured roots so a remote caller of the HTTP
transport cannot read the host's files.
"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from pathlib import Path

from mcp.server.mcpserver.exceptions import ToolError

from dreep_mcp import _constants as c
from dreep_mcp._settings import Settings


@dataclass(frozen=True)
class ResolvedFile:
    #: ``Path`` for a local file, ``bytes`` for inline content.
    source: Path | bytes
    filename: str | None
    size: int


def _within(path: Path, roots: tuple[Path, ...]) -> bool:
    return any(path == root or root in path.parents for root in roots)


def _local(settings: Settings, raw: str) -> ResolvedFile:
    path = Path(raw).expanduser().resolve()
    if settings.file_roots:
        if not _within(path, settings.file_roots):
            roots = ", ".join(str(r) for r in settings.file_roots)
            raise ToolError(f"{path} is outside the allowed file roots ({roots}).")
    elif not settings.allow_any_local_path:
        raise ToolError(
            f"Reading local files is disabled on this transport. Set {c.ENV_FILE_ROOTS} "
            "on the server, or send content_base64 instead."
        )
    if not path.is_file():
        raise ToolError(f"No such file: {path}")
    return ResolvedFile(path, None, path.stat().st_size)


def _inline(content: str, filename: str | None) -> ResolvedFile:
    if not filename:
        raise ToolError("filename is required with content_base64.")
    try:
        data = base64.b64decode(content, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ToolError(f"content_base64 is not valid base64: {error}") from error
    if len(data) > c.MAX_INLINE_BYTES:
        raise ToolError(
            f"Inline content is {len(data)} bytes; the limit is {c.MAX_INLINE_BYTES}. "
            "Pass a path instead."
        )
    return ResolvedFile(data, filename, len(data))


def resolve_file(
    settings: Settings, path: str | None, content_base64: str | None, filename: str | None
) -> ResolvedFile:
    """Exactly one of ``path`` or ``content_base64`` must be given."""
    if (path is None) == (content_base64 is None):
        raise ToolError("Give exactly one of 'path' or 'content_base64'.")
    if path is not None:
        resolved = _local(settings, path)
        return ResolvedFile(resolved.source, filename, resolved.size)
    assert content_base64 is not None
    return _inline(content_base64, filename)
