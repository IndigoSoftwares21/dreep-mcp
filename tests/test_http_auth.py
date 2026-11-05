"""BearerTokenMiddleware: only requests with the right token reach the app."""

from __future__ import annotations

from typing import Any

import pytest

from dreep_mcp._http_auth import BearerTokenMiddleware, Message, Scope, presented_token

pytestmark = pytest.mark.anyio


class App:
    def __init__(self) -> None:
        self.calls = 0

    async def __call__(self, scope: Scope, receive: Any, send: Any) -> None:
        self.calls += 1


async def _receive() -> Message:
    return {}


async def _request(scope: Scope) -> tuple[int, list[Message]]:
    app = App()
    sent: list[Message] = []

    async def send(message: Message) -> None:
        sent.append(message)

    await BearerTokenMiddleware(app, "s3cret")(scope, _receive, send)
    return app.calls, sent


def _http(auth: bytes | None) -> Scope:
    headers = [(b"authorization", auth)] if auth is not None else []
    return {"type": "http", "headers": headers}


async def test_right_token_passes() -> None:
    calls, sent = await _request(_http(b"Bearer s3cret"))
    assert (calls, sent) == (1, [])


@pytest.mark.parametrize("auth", [None, b"Bearer wrong", b"s3cret", b"Basic s3cret"])
async def test_missing_or_wrong_token_is_refused(auth: bytes | None) -> None:
    calls, sent = await _request(_http(auth))
    assert calls == 0
    assert sent[0]["status"] == 401


async def test_lifespan_events_pass_through() -> None:
    calls, _ = await _request({"type": "lifespan"})
    assert calls == 1


def test_presented_token_reads_the_header_case_insensitively() -> None:
    assert presented_token({"headers": [(b"Authorization", b"Bearer t")]}) == "t"
    assert presented_token({}) == ""
