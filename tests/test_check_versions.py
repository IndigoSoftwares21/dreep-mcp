"""scripts/check_versions.py keeps PyPI and npm versions in lockstep."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import check_versions
from dreep_mcp import __version__


def test_repository_versions_agree() -> None:
    assert check_versions.python_version() == check_versions.npm_version() == __version__
    assert check_versions.check() == check_versions.OK
    assert check_versions.check(f"v{__version__}") == check_versions.OK


def test_wrong_tag_fails() -> None:
    assert check_versions.check("v0.0.0-nope") == check_versions.FAIL


def test_mismatch_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(check_versions, "npm_version", lambda: "9.9.9")
    assert check_versions.check() == check_versions.FAIL
