"""Tool behaviour hints, so clients can auto-approve reads and confirm deletes."""

from __future__ import annotations

from typing import Final

from mcp_types import ToolAnnotations

#: Reads project state from the API.
READ: Final = ToolAnnotations(read_only_hint=True, open_world_hint=True)
#: Pure string work, no network call.
LOCAL: Final = ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=False)
#: Stores something new; repeating it stores a duplicate.
CREATE: Final = ToolAnnotations(
    read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True
)
#: Permanently removes something.
DELETE: Final = ToolAnnotations(
    read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=True
)
