"""The dreep-mcp command: argument parsing, safety checks and transport wiring."""

from __future__ import annotations

import argparse
from typing import Any

import pytest

from dreep_mcp import _cli
from dreep_mcp._http_auth import BearerTokenMiddleware
from dreep_mcp._settings import Settings
from tests.conftest import MakeServer
from tests.support import API_KEY


def test_defaults_to_stdio() -> None:
    args = _cli.build_parser().parse_args([])
    assert (args.transport, args.host, args.port, args.path) == ("stdio", "127.0.0.1", 8000, "/mcp")


def test_public_http_without_a_token_is_refused(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        _cli.main(["--transport", "http", "--host", "0.0.0.0"])  # noqa: S104 -- the case under test
    assert exit_info.value.code == _cli.EXIT_USAGE
    assert "DREEP_MCP_HTTP_TOKEN" in capsys.readouterr().err


def test_missing_api_key_is_a_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        _cli.main([])
    assert exit_info.value.code == _cli.EXIT_USAGE
    assert "DREEP_API_KEY" in capsys.readouterr().err


def test_main_runs_the_server(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DREEP_API_KEY", API_KEY)
    ran: list[tuple[Any, ...]] = []
    monkeypatch.setattr("anyio.run", lambda *args: ran.append(args))
    _cli.main(["--transport", "stdio"])
    assert ran[0][0] is _cli._serve


@pytest.mark.anyio
async def test_http_app_is_guarded_only_with_a_token(make_server: MakeServer) -> None:
    server = make_server()
    open_app = _cli.http_app(server, Settings(), host="127.0.0.1", path="/mcp")
    guarded = _cli.http_app(server, Settings(http_token="t"), host="127.0.0.1", path="/mcp")
    assert not isinstance(open_app, BearerTokenMiddleware)
    assert isinstance(guarded, BearerTokenMiddleware)


@pytest.mark.anyio
@pytest.mark.parametrize("transport", ["stdio", "http"])
async def test_serve_runs_the_transport_and_closes_the_client(
    make_server: MakeServer, monkeypatch: pytest.MonkeyPatch, transport: str
) -> None:
    server = make_server()
    served: list[str] = []

    async def fake_stdio() -> None:
        served.append("stdio")

    class FakeUvicorn:
        def __init__(self, config: Any) -> None:
            self.config = config

        async def serve(self) -> None:
            served.append("http")

    monkeypatch.setattr(server, "run_stdio_async", fake_stdio)
    monkeypatch.setattr("uvicorn.Server", FakeUvicorn)
    closed: list[bool] = []

    class Client:
        async def aclose(self) -> None:
            closed.append(True)

    args = argparse.Namespace(transport=transport, host="127.0.0.1", port=0, path="/mcp")
    await _cli._serve(server, Client(), Settings(), args)  # type: ignore[arg-type]
    assert (served, closed) == ([transport], [True])
