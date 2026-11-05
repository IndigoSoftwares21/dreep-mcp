"""The transform argument, as a schema an agent can read.

Mirrors :class:`dreep.types.Transform` field for field, reusing the SDK's
literal types, so the MCP input schema lists every valid value. The SDK still
validates the result; this model only exists to describe it to the agent.
"""

from __future__ import annotations

from typing import Literal, cast

from dreep.types import Fit, Gravity, OutputFormat, Rotate, Transform, VideoCodec
from pydantic import BaseModel, ConfigDict, Field


class TransformInput(BaseModel):
    """Image, video and document transform. Every field is optional."""

    model_config = ConfigDict(extra="forbid")

    format: OutputFormat | None = Field(
        None,
        description=(
            "Output format. Image: jpeg, png, webp, avif, gif, tiff, heic. Video: mp4, webm, "
            "mov, hls, gif. Audio: mp3, wav, aac. Documents: pdf, docx, xlsx, pptx, csv..."
        ),
    )
    width: int | None = Field(None, ge=1, le=4000, description="Width in pixels, max 4000.")
    height: int | None = Field(None, ge=1, le=4000, description="Height in pixels, max 4000.")
    fit: Fit | None = Field(None, description="How the image fits width x height.")
    quality: int | None = Field(None, ge=1, le=100, description="Compression quality, 1-100.")
    gravity: Gravity | None = Field(None, description="Crop anchor when resizing.")
    crop: str | None = Field(None, description="Explicit crop as 'left,top,width,height'.")
    dpr: float | None = Field(None, gt=0, le=3, description="Device pixel ratio, max 3.")
    rotate: Rotate | None = Field(None, description="Rotation in degrees.")
    blur: float | None = Field(None, ge=0.3, le=100, description="Gaussian blur sigma, 0.3-100.")
    bg: str | None = Field(
        None, description="Background hex colour without '#': fff, ffffff or ffffffcc."
    )
    radius: int | float | Literal["max"] | None = Field(
        None, description="Corner radius in pixels, or 'max' for a circle or pill."
    )
    trim_start: float | None = Field(None, ge=0, description="Video trim start, seconds.")
    trim_end: float | None = Field(None, ge=0, description="Video trim end, seconds.")
    video_codec: VideoCodec | None = Field(None, description="Video codec.")
    fps: int | None = Field(None, ge=1, description="Video frames per second.")
    page: int | None = Field(None, ge=1, description="PDF page to render as png/jpeg.")
    preset: str | None = Field(None, description="Key of a saved preset, applied instead.")

    def to_sdk(self) -> Transform:
        """The SDK's ``Transform`` dict: only the fields that were set."""
        return cast(Transform, self.model_dump(exclude_none=True))


def to_sdk_transform(transform: TransformInput | None) -> Transform | None:
    return transform.to_sdk() if transform is not None else None
