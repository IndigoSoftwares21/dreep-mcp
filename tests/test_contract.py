"""The Node server's contract file stays in step with this server's tools."""

from __future__ import annotations

import sys
from pathlib import Path

import anyio
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import export_contract


def test_contract_file_is_up_to_date() -> None:
    assert export_contract.main([export_contract.CHECK_FLAG]) == export_contract.OK


def test_contract_has_every_tool_with_annotations() -> None:
    contract = anyio.run(export_contract.build_contract)
    tools = {tool["name"]: tool for tool in contract["tools"]}
    assert len(tools) == 16
    assert tools["delete_media"]["annotations"]["destructiveHint"] is True
    assert tools["list_media"]["annotations"]["readOnlyHint"] is True
    assert "transform" in tools["upload_file"]["inputSchema"]["properties"]


def test_stale_contract_fails_the_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    stale = tmp_path / "tools.json"
    stale.write_text("{}\n")
    monkeypatch.setattr(export_contract, "CONTRACT", stale)
    assert export_contract.main([export_contract.CHECK_FLAG]) == export_contract.FAIL
    assert "stale" in capsys.readouterr().err
    assert export_contract.main([]) == export_contract.OK
    assert export_contract.main([export_contract.CHECK_FLAG]) == export_contract.OK
