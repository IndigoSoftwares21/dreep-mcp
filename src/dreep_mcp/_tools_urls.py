"""URL tools: transformed delivery URLs and time-limited signed URLs. No network."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from dreep_mcp import _annotations as hints
from dreep_mcp import _constants as c
from dreep_mcp import _params as p
from dreep_mcp._tool_call import guard
from dreep_mcp._tool_host import ToolHost
from dreep_mcp._transform_input import to_sdk_transform


def register_url_tools(host: ToolHost) -> None:
    server, client = host.server, host.client

    @server.tool(annotations=hints.LOCAL)
    def build_delivery_url(url: p.AssetUrl, transform: p.Transform = None) -> dict[str, Any]:
        """Builds a delivery URL that resizes, crops, converts or otherwise transforms an asset.

        Transforms run on the fly at the CDN and are cached. Example: width 400 and
        format webp for a thumbnail; format pdf to convert a Word document.
        """
        transformed = guard(lambda: client.url(url, to_sdk_transform(transform)))
        return {c.KEY_URL: transformed}

    @server.tool(annotations=hints.LOCAL)
    def build_signed_url(
        *,
        asset_id: Annotated[str, Field(description="The asset's `id`; this is what is signed.")],
        url: p.AssetUrl,
        expires_in_seconds: Annotated[
            int, Field(ge=1, description="Seconds until the link stops working.")
        ],
        transform: p.Transform = None,
    ) -> dict[str, Any]:
        """Builds a time-limited URL for an asset in a signed folder.

        Needs DREEP_SIGNING_SECRET on the server. Anyone holding the link can fetch the
        asset until it expires, so share it only with the intended recipient.
        """
        asset = {c.KEY_ID: asset_id, c.KEY_URL: url}
        signed = guard(
            lambda: client.signed_url(
                asset, expires_in=expires_in_seconds, transform=to_sdk_transform(transform)
            )
        )
        return {c.KEY_URL: signed}
