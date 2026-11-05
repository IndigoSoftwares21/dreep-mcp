"""Project tools: folders, presets and usage."""

from __future__ import annotations

from typing import Annotated, Any

from dreep import AsyncDreep
from dreep.types import AccessControlType
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from dreep_mcp import _annotations as hints
from dreep_mcp import _constants as c
from dreep_mcp._tool_call import run, run_delete
from dreep_mcp._tool_host import ToolHost
from dreep_mcp._transform_input import TransformInput


def register_project_tools(host: ToolHost) -> None:
    server, client, settings = host.server, host.client, host.settings

    @server.tool(annotations=hints.CREATE)
    async def create_folder(
        *,
        name: Annotated[str | None, Field(description="Create one folder by name.")] = None,
        path: Annotated[
            str | None, Field(description="Or create a whole chain, e.g. 'clients/acme/logos'.")
        ] = None,
        parent_id: Annotated[str | None, Field(description="Parent folder UUID.")] = None,
        parent_path: Annotated[str | None, Field(description="Parent folder slug path.")] = None,
        access_control_type: Annotated[
            AccessControlType | None,
            Field(description="public, private or signed. Top-level folders only."),
        ] = None,
        default_expiry_seconds: Annotated[
            int | None, Field(ge=1, description="Default signed-link lifetime, seconds.")
        ] = None,
    ) -> dict[str, Any]:
        """Creates a folder. Uploads create folders on demand, so this is mainly for
        setting access control before anything lands.

        Access control can only be set on a top-level folder (name, no parent);
        nested folders inherit it. Folders cannot be deleted through the API.
        """
        return await run(
            client.create_folder(
                name=name,
                path=path,
                parent_id=parent_id,
                parent_path=parent_path,
                access_control_type=access_control_type,
                default_expiry_seconds=default_expiry_seconds,
            )
        )

    @server.tool(annotations=hints.READ)
    async def list_folders(
        *,
        path: Annotated[str | None, Field(description="List this folder's children.")] = None,
        parent_id: Annotated[str | None, Field(description="Or this folder's, by UUID.")] = None,
        root_only: Annotated[bool, Field(description="Only top-level folders.")] = False,
    ) -> dict[str, Any]:
        """Lists folders with their full paths and access control. With no filter,
        returns every folder at any depth."""
        return await run(client.list_folders(path=path, parent_id=parent_id, root_only=root_only))

    @server.tool(annotations=hints.CREATE)
    async def create_preset(
        *,
        key: Annotated[
            str, Field(pattern=r"^[a-z0-9_]+$", description="Lowercase letters, digits, _.")
        ],
        name: Annotated[str, Field(min_length=1, description="Human-readable name.")],
        transform: Annotated[TransformInput, Field(description="Must include `format`.")],
    ) -> dict[str, Any]:
        """Saves a named transform, applied anywhere with transform `preset`: key."""
        params = transform.to_sdk()
        if c.FORMAT_KEY not in params:
            raise ToolError("A preset's transform must include 'format'.")
        return await run(client.create_preset(key=key, name=name, transform=params))

    @server.tool(annotations=hints.READ)
    async def list_presets() -> dict[str, Any]:
        """Lists every saved preset with its `id`, `key`, `name` and `params`."""
        return await run(_presets(client))

    @server.tool(annotations=hints.READ)
    async def get_usage() -> dict[str, Any]:
        """Storage consumed and image, file and folder counts for the project."""
        return await run(client.get_usage())

    if not settings.allow_delete:
        return

    @server.tool(annotations=hints.DELETE)
    async def delete_preset(
        *,
        preset_id: Annotated[str, Field(description="The preset's `id` (not its key).")],
    ) -> dict[str, Any]:
        """Deletes a preset. URLs still using its key start failing. Confirm first."""
        return await run_delete(client.delete_preset(preset_id), preset_id)


async def _presets(client: AsyncDreep) -> dict[str, Any]:
    return {c.KEY_PRESETS: await client.list_presets()}
