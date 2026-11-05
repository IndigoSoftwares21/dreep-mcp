"""SDK models -> plain JSON-ready dicts for tool results.

The SDK's models are frozen dataclasses with snake_case fields; each keeps the
undecoded payload in ``raw``, which is dropped here so a result carries every
field exactly once.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from dreep_mcp import _constants as c


def to_json(value: Any) -> Any:
    """Recursively converts models, mappings, sequences and datetimes."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            f.name: to_json(getattr(value, f.name))
            for f in dataclasses.fields(value)
            if f.name != c.RAW_FIELD
        }
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(k): to_json(v) for k, v in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [to_json(v) for v in value]
    return value


def to_result(value: Any) -> dict[str, Any]:
    """A tool result: always a JSON object, as MCP structured output requires."""
    converted = to_json(value)
    if isinstance(converted, dict):
        return converted
    raise TypeError(f"Expected an object-shaped result, got {type(value).__name__}.")
