"""Settings.from_env reads the server's own environment variables."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from dreep_mcp import _constants as c
from dreep_mcp._settings import Settings


@pytest.mark.parametrize(("value", "expected"), [("1", True), (" TRUE ", True), ("0", False)])
def test_allow_delete_flag(value: str, expected: bool) -> None:
    assert Settings.from_env({c.ENV_ALLOW_DELETE: value}).allow_delete is expected


def test_defaults() -> None:
    settings = Settings.from_env({})
    assert (settings.allow_delete, settings.file_roots, settings.http_token) == (False, (), None)
    assert settings.allow_any_local_path is True


def test_roots_and_token(tmp_path: Path) -> None:
    env = {
        c.ENV_FILE_ROOTS: f"{tmp_path}{os.pathsep}{os.pathsep}",
        c.ENV_HTTP_TOKEN: "tok",
    }
    settings = Settings.from_env(env, transport=c.Transport.HTTP)
    assert settings.file_roots == (tmp_path.resolve(),)
    assert settings.http_token == "tok"
    assert settings.allow_any_local_path is False
