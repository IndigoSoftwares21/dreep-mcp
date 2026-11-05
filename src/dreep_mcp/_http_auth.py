"""Bearer-token guard for the HTTP transport, as plain ASGI middleware.

The server acts with the project's API key, so anyone who can reach the HTTP
endpoint can act on the project. When a token is configured, every HTTP request
must carry ``Authorization: Bearer <token>``; lifespan events pass through.
"""

from __future__ import annotations

import hmac
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any, Final

from dreep_mcp import _constants as c

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

_UNAUTHORIZED_HEADERS: Final = [
    (c.HEADER_CONTENT_TYPE, c.JSON_CONTENT_TYPE),
    (c.HEADER_WWW_AUTHENTICATE, c.WWW_AUTHENTICATE),
]


def presented_token(scope: Scope) -> str:
    """The bearer token on the request, or an empty string."""
    for name, value in scope.get(c.ASGI_HEADERS, []):
        if bytes(name).lower() == c.HEADER_AUTHORIZATION:
            header = bytes(value).decode(c.HEADER_ENCODING)
            if header.startswith(c.BEARER_PREFIX):
                return header.removeprefix(c.BEARER_PREFIX)
    return ""


class BearerTokenMiddleware:
    def __init__(self, app: ASGIApp, token: str) -> None:
        self._app = app
        self._token = token.encode()

    def _authorized(self, scope: Scope) -> bool:
        return hmac.compare_digest(presented_token(scope).encode(), self._token)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope[c.ASGI_TYPE] != c.SCOPE_HTTP or self._authorized(scope):
            await self._app(scope, receive, send)
            return
        await send(
            {
                c.ASGI_TYPE: c.ASGI_RESPONSE_START,
                c.ASGI_STATUS: c.HTTP_UNAUTHORIZED,
                c.ASGI_HEADERS: _UNAUTHORIZED_HEADERS,
            }
        )
        await send({c.ASGI_TYPE: c.ASGI_RESPONSE_BODY, c.ASGI_BODY: c.UNAUTHORIZED_BODY})
