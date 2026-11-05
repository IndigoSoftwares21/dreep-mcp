"""Upload tools: one-shot upload, and the presign/confirm pair for remote bytes."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from dreep_mcp import _annotations as hints
from dreep_mcp import _constants as c
from dreep_mcp import _params as p
from dreep_mcp._file_input import resolve_file
from dreep_mcp._tool_call import run
from dreep_mcp._tool_host import ToolHost
from dreep_mcp._transform_input import to_sdk_transform


def register_upload_tools(host: ToolHost) -> None:
    server, client, settings = host.server, host.client, host.settings

    @server.tool(annotations=hints.CREATE)
    async def upload_file(
        *,
        path: p.FilePath = None,
        content_base64: p.ContentBase64 = None,
        filename: p.Filename = None,
        content_type: Annotated[
            str | None, Field(description="MIME type; guessed from the filename if omitted.")
        ] = None,
        folder: p.Folder = None,
        key: p.ObjectKey = None,
        folder_id: p.FolderId = None,
        auto_create_folders: p.AutoCreateFolders = None,
        transform: p.Transform = None,
        preset_key: p.PresetKey = None,
    ) -> dict[str, Any]:
        """Uploads an image, video, audio file or document to Dreep and returns the asset.

        The result's `url` is the ready-to-use delivery URL. Files over 100 MB stream
        straight to storage through a presigned upload. A transform given here is
        applied before storage and replaces the original.
        """
        file = resolve_file(settings, path, content_base64, filename)
        upload = (
            client.upload_presigned if file.size > c.PRESIGNED_THRESHOLD_BYTES else client.upload
        )
        return await run(
            upload(
                file.source,
                filename=file.filename,
                content_type=content_type,
                folder=folder,
                key=key,
                folder_id=folder_id,
                auto_create_folders=auto_create_folders,
                transform=to_sdk_transform(transform),
                preset_key=preset_key,
            )
        )

    @server.tool(annotations=hints.CREATE)
    async def create_upload_url(
        *,
        content_type: Annotated[str, Field(description="MIME type of the file, e.g. video/mp4.")],
        size_bytes: Annotated[int, Field(ge=1, description="Exact size of the file in bytes.")],
        filename: p.Filename = None,
        folder: p.Folder = None,
        key: p.ObjectKey = None,
        folder_id: p.FolderId = None,
        auto_create_folders: p.AutoCreateFolders = None,
        content_hash: Annotated[
            str | None,
            Field(description="Hex SHA-256 of the file; skips the upload if Dreep has it."),
        ] = None,
    ) -> dict[str, Any]:
        """Starts a direct-to-storage upload for bytes this server can't read.

        PUT the file to `upload_url` with exactly this Content-Type and Content-Length
        (valid about ten minutes), then call confirm_upload with the returned `id`.
        If `already_exists` is true, skip the PUT and confirm straight away.
        """
        return await run(
            client.presign_upload(
                content_type=content_type,
                size_bytes=size_bytes,
                filename=filename,
                folder=folder,
                key=key,
                folder_id=folder_id,
                auto_create_folders=auto_create_folders,
                content_hash=content_hash,
            )
        )

    @server.tool(annotations=hints.CREATE)
    async def confirm_upload(
        *,
        upload_id: Annotated[str, Field(description="The `id` create_upload_url returned.")],
        transform: p.Transform = None,
        preset_key: p.PresetKey = None,
    ) -> dict[str, Any]:
        """Finalises a presigned upload once its bytes are in storage; returns the asset.

        A conflict error means the bytes haven't landed yet: retry this call, not the PUT.
        """
        return await run(
            client.confirm_upload(
                upload_id,
                transform=to_sdk_transform(transform),
                preset_key=preset_key,
            )
        )
