"""Media library tools: list assets, and (opt-in) delete them."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from dreep_mcp import _annotations as hints
from dreep_mcp._tool_call import run, run_delete
from dreep_mcp._tool_host import ToolHost


def register_media_tools(host: ToolHost) -> None:
    server, client, settings = host.server, host.client, host.settings

    @server.tool(annotations=hints.READ)
    async def list_media(
        *,
        page: Annotated[int | None, Field(ge=1, description="Page number, from 1.")] = None,
        limit: Annotated[int | None, Field(ge=1, description="Assets per page.")] = None,
        folder: Annotated[
            str | None, Field(description="Only assets in this folder slug path, which must exist.")
        ] = None,
        folder_id: Annotated[str | None, Field(description="Only assets in this folder.")] = None,
        recursive: Annotated[
            bool | None, Field(description="Include assets in subfolders of the folder.")
        ] = None,
    ) -> dict[str, Any]:
        """Lists ready assets, newest first, with `pagination.total` across all pages.

        Each asset has `id`, `url`, `filename`, `mimetype`, `size_bytes` and `folder`.
        There is no text search: page through and filter by filename or folder.
        """
        return await run(
            client.list_media(
                page=page, limit=limit, folder=folder, folder_id=folder_id, recursive=recursive
            )
        )

    if not settings.allow_delete:
        return

    @server.tool(annotations=hints.DELETE)
    async def delete_media(
        *,
        media_id: Annotated[str, Field(description="The asset's `id`.")],
    ) -> dict[str, Any]:
        """Permanently deletes an asset and every cached transform of it.

        Immediate and irreversible: URLs already handed out, signed ones included,
        stop working. Confirm with the user first.
        """
        return await run_delete(client.delete_media(media_id), media_id)
