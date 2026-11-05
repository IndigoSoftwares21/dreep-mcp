"""Tool parameters shared by several tools, described once.

Each alias is an ``Annotated`` type whose description becomes part of the
tool's input schema, which is what the agent reads to decide how to call it.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from dreep_mcp._transform_input import TransformInput

FilePath = Annotated[
    str | None,
    Field(description="Path of a local file to send. Give this or content_base64, not both."),
]
ContentBase64 = Annotated[
    str | None,
    Field(description="File content, base64-encoded (20 MB max). Requires filename."),
]
Filename = Annotated[
    str | None,
    Field(description="Filename to store, e.g. 'hero.jpg'. Defaults to the path's name."),
]
Folder = Annotated[
    str | None,
    Field(description="Destination folder slug path, e.g. 'marketing/2026'. Created if missing."),
]
FolderId = Annotated[str | None, Field(description="UUID of an existing destination folder.")]
AutoCreateFolders = Annotated[
    bool | None, Field(description="False to require the folder path to exist already.")
]
ObjectKey = Annotated[
    str | None,
    Field(description="Full object key (folder path + filename). Excludes folder/folder_id."),
]
PresetKey = Annotated[
    str | None, Field(description="Key of a saved preset to apply instead of 'transform'.")
]
Transform = Annotated[
    TransformInput | None,
    Field(description="Transform to apply. On upload it runs before storage."),
]
AssetUrl = Annotated[
    str,
    Field(description="The asset's delivery URL exactly as Dreep returned it (from upload/list)."),
]
