"""AI processing tools: background removal, OCR and document conversion.

Each takes a file the same way upload_file does and stores its output as a new
asset (OCR stores a ``.txt`` only when a folder is given).
"""

from __future__ import annotations

from typing import Annotated, Any

from dreep.types import BackgroundRemovalFormat, ConvertFormat
from pydantic import Field

from dreep_mcp import _annotations as hints
from dreep_mcp import _params as p
from dreep_mcp._file_input import resolve_file
from dreep_mcp._tool_call import run
from dreep_mcp._tool_host import ToolHost


def register_processing_tools(host: ToolHost) -> None:
    server, client, settings = host.server, host.client, host.settings

    @server.tool(annotations=hints.CREATE)
    async def remove_background(
        *,
        path: p.FilePath = None,
        content_base64: p.ContentBase64 = None,
        filename: p.Filename = None,
        format: Annotated[
            BackgroundRemovalFormat | None,
            Field(description="png or webp; both keep the alpha channel."),
        ] = None,
        folder: p.Folder = None,
        folder_id: p.FolderId = None,
        auto_create_folders: p.AutoCreateFolders = None,
    ) -> dict[str, Any]:
        """Cuts the subject out of an image and stores the transparent cutout.

        To show it on a colour, build a delivery URL with transform `bg`, e.g. 'ffffff'.
        """
        file = resolve_file(settings, path, content_base64, filename)
        return await run(
            client.remove_background(
                file.source,
                filename=file.filename,
                format=format,
                folder=folder,
                folder_id=folder_id,
                auto_create_folders=auto_create_folders,
            )
        )

    @server.tool(annotations=hints.CREATE)
    async def extract_text(
        *,
        path: p.FilePath = None,
        content_base64: p.ContentBase64 = None,
        filename: p.Filename = None,
        folder: Annotated[
            str | None, Field(description="Also store the text as a .txt asset in this folder.")
        ] = None,
        folder_id: p.FolderId = None,
        auto_create_folders: p.AutoCreateFolders = None,
        include_blocks: Annotated[
            bool | None, Field(description="Also return line blocks with bounding boxes.")
        ] = None,
    ) -> dict[str, Any]:
        """Runs OCR on an image or PDF and returns the extracted `text`."""
        file = resolve_file(settings, path, content_base64, filename)
        return await run(
            client.extract_text(
                file.source,
                filename=file.filename,
                folder=folder,
                folder_id=folder_id,
                auto_create_folders=auto_create_folders,
                include_blocks=include_blocks,
            )
        )

    @server.tool(annotations=hints.CREATE)
    async def convert_document(
        *,
        format: Annotated[ConvertFormat, Field(description="Target format, e.g. pdf or docx.")],
        path: p.FilePath = None,
        content_base64: p.ContentBase64 = None,
        filename: p.Filename = None,
        page: Annotated[
            int | None, Field(ge=1, description="PDF page to render, for png/jpeg output.")
        ] = None,
        key: p.ObjectKey = None,
        folder: p.Folder = None,
        folder_id: p.FolderId = None,
        auto_create_folders: p.AutoCreateFolders = None,
    ) -> dict[str, Any]:
        """Converts a document (Word to PDF, PDF to Word, a PDF page to an image...).

        Stored as a new asset. If `status` is 'processing', the `url` answers 202
        until the conversion finishes.
        """
        file = resolve_file(settings, path, content_base64, filename)
        return await run(
            client.convert_document(
                file.source,
                format=format,
                filename=file.filename,
                page=page,
                key=key,
                folder=folder,
                folder_id=folder_id,
                auto_create_folders=auto_create_folders,
            )
        )
