"""The one place a tool's SDK call is awaited, its errors mapped and its result shaped.

The MCP SDK withholds the message of any exception that is not a
``ToolError``, so the agent would only see "tool failed". Every anticipated
failure -- the API's own errors, and the SDK's argument validation -- becomes a
``ToolError`` carrying the SDK's message, which says what to change.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from typing import Any, TypeVar

from dreep import DreepAPIError, DreepError
from mcp.server.mcpserver.exceptions import ToolError

from dreep_mcp import _constants as c
from dreep_mcp._serialize import to_result

T = TypeVar("T")

#: Raised by the SDK for arguments it rejects before sending anything.
_VALIDATION_ERRORS = (ValueError, TypeError)


def describe(error: Exception) -> str:
    if isinstance(error, DreepAPIError):
        return f"Dreep API error: {error}"
    return str(error)


@contextmanager
def _mapped_errors() -> Iterator[None]:
    try:
        yield
    except (DreepError, *_VALIDATION_ERRORS) as error:
        raise ToolError(describe(error)) from error


def guard(call: Callable[[], T]) -> T:
    """Runs a synchronous SDK call (URL building), mapping its errors."""
    with _mapped_errors():
        return call()


async def run(call: Awaitable[Any]) -> dict[str, Any]:
    """Awaits an SDK call and returns its result as a JSON object."""
    with _mapped_errors():
        result = await call
    return to_result(result)


async def run_delete(call: Awaitable[None], resource_id: str) -> dict[str, Any]:
    """Awaits an SDK delete, which returns nothing, and reports what went."""
    with _mapped_errors():
        await call
    return {c.KEY_ID: resource_id, c.KEY_DELETED: True}
