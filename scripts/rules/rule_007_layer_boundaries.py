"""RULE-007: separation of concerns -- each layer imports only what it may.

"Client/transport communicates. Models describe. Domain logic decides.
Constants define." The server's layers, innermost first:

* **pure** -- constants, settings, schemas, serialisation, file resolution,
  error mapping, the ASGI auth guard: no I/O libraries, trivially testable.
* **tools** -- ``_tools_*`` and ``_server``: call the Dreep client they are
  handed, but never build one, so tests can hand them a mocked client.
* **entry** -- ``_cli``: the only module that runs an event loop or a web
  server, and the only one that constructs a Dreep or HTTP client.
"""

from __future__ import annotations

import ast
import re
from typing import ClassVar, Final

from rules.base import ERROR, BaseRule, FileContext, Severity, Violation

IO_LIBRARIES: Final = frozenset(
    {"httpx", "anyio", "uvicorn", "starlette", "requests", "aiohttp", "urllib3"}
)
ENTRY_LAYER: Final = re.compile(r"^_cli$")
CLIENT_CONSTRUCTORS: Final = frozenset({"Dreep", "AsyncDreep", "Client", "AsyncClient"})


def _imported_roots(tree: ast.Module) -> list[tuple[str, int]]:
    roots = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots += [(alias.name.split(".")[0], node.lineno) for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.append((node.module.split(".")[0], node.lineno))
    return roots


def _called_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    return func.attr if isinstance(func, ast.Attribute) else None


class LayerBoundaries(BaseRule):
    id: ClassVar[str] = "RULE-007"
    category: ClassVar[str] = "Layer Boundaries"
    severity: ClassVar[Severity] = ERROR
    description: ClassVar[str] = "I/O and client construction only in the entry layer"
    remediation: ClassVar[str] = "Do the I/O in _cli and pass the client or plain data inward."

    def check(self, file: FileContext) -> list[Violation]:
        if not file.is_package or ENTRY_LAYER.match(file.module):
            return []
        violations = [
            self.violation(file, line, f"Inner module imports I/O library {root!r}.")
            for root, line in _imported_roots(file.tree)
            if root in IO_LIBRARIES
        ]
        violations += [
            self.violation(file, node.lineno, "Client constructed outside the entry layer.")
            for node in ast.walk(file.tree)
            if isinstance(node, ast.Call) and _called_name(node) in CLIENT_CONSTRUCTORS
        ]
        return violations


RULE = LayerBoundaries()
