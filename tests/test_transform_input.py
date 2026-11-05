"""TransformInput and the shared parameter schemas the agent reads."""

from __future__ import annotations

from typing import get_args

import pytest
from pydantic import ValidationError

from dreep_mcp import _params
from dreep_mcp._transform_input import TransformInput, to_sdk_transform


def test_only_set_fields_reach_the_sdk() -> None:
    transform = TransformInput(width=400, format="webp", radius="max")
    assert transform.to_sdk() == {"width": 400, "format": "webp", "radius": "max"}
    assert to_sdk_transform(None) is None


@pytest.mark.parametrize("bad", [{"width": 5000}, {"fit": "squish"}, {"widht": 10}])
def test_invalid_transforms_are_rejected(bad: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        TransformInput.model_validate(bad)


def test_schema_lists_valid_values() -> None:
    schema = TransformInput.model_json_schema()
    assert "cover" in str(schema["properties"]["fit"])
    assert schema["additionalProperties"] is False


def test_shared_params_carry_descriptions() -> None:
    for alias in (_params.FilePath, _params.ContentBase64, _params.Folder, _params.AssetUrl):
        assert get_args(alias)[1].description
