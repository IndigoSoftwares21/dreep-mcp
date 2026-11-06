"""Exports the tool contract the Node server serves, so both servers stay identical.

    python scripts/export_contract.py          # write npm/contract/tools.json
    python scripts/export_contract.py --check  # fail if the file is stale

The Python server is the source of truth for tool names, descriptions, input
schemas and annotations. The Node server only implements the handlers.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Final

from dreep import AsyncDreep

from dreep_mcp import Settings, create_server
from dreep_mcp import _constants as c
from dreep_mcp._server import INSTRUCTIONS

CONTRACT: Final = Path(__file__).resolve().parent.parent / "npm" / "contract" / "tools.json"
PLACEHOLDER_KEY: Final = "contract-export"
CHECK_FLAG: Final = "--check"
OK, FAIL = 0, 1


async def build_contract() -> dict[str, Any]:
    client = AsyncDreep(PLACEHOLDER_KEY)
    try:
        tools = await create_server(Settings(allow_delete=True), client).list_tools()
    finally:
        await client.aclose()
    return {
        "serverName": c.SERVER_NAME,
        "serverTitle": c.SERVER_TITLE,
        "websiteUrl": c.WEBSITE_URL,
        "instructions": INSTRUCTIONS,
        "limits": {
            "maxInlineBytes": c.MAX_INLINE_BYTES,
            "presignedThresholdBytes": c.PRESIGNED_THRESHOLD_BYTES,
        },
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
                "annotations": (
                    tool.annotations.model_dump(by_alias=True, exclude_none=True)
                    if tool.annotations
                    else {}
                ),
            }
            for tool in sorted(tools, key=lambda t: t.name)
        ],
    }


def render(contract: dict[str, Any]) -> str:
    return json.dumps(contract, indent=2, sort_keys=True) + "\n"


def main(argv: list[str]) -> int:
    rendered = render(asyncio.run(build_contract()))
    if CHECK_FLAG in argv:
        if not CONTRACT.exists() or CONTRACT.read_text() != rendered:
            sys.stderr.write(f"{CONTRACT} is stale. Run: python scripts/export_contract.py\n")
            return FAIL
        return OK
    CONTRACT.parent.mkdir(parents=True, exist_ok=True)
    CONTRACT.write_text(rendered)
    return OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
