"""Every name, environment variable and default the server's behaviour depends on."""

from __future__ import annotations

from enum import Enum
from typing import Final

SERVER_NAME: Final = "dreep"
SERVER_TITLE: Final = "Dreep"
WEBSITE_URL: Final = "https://dreep.cloud"
LOGGER_NAME: Final = "dreep_mcp"

# --------------------------------------------------------------------------- #
# Environment
# --------------------------------------------------------------------------- #

#: ``1``/``true``/``yes``/``on`` registers the delete tools.
ENV_ALLOW_DELETE: Final = "DREEP_MCP_ALLOW_DELETE"
#: Directories (``os.pathsep``-separated) that file tools may read from.
ENV_FILE_ROOTS: Final = "DREEP_MCP_FILE_ROOTS"
#: Bearer token the HTTP transport requires on every request.
ENV_HTTP_TOKEN: Final = "DREEP_MCP_HTTP_TOKEN"  # noqa: S105 -- an env var name, not a secret
TRUTHY: Final = frozenset({"1", "true", "yes", "on"})


class Transport(str, Enum):
    STDIO = "stdio"
    HTTP = "http"


#: The MCP SDK's name for the HTTP transport.
MCP_HTTP_TRANSPORT: Final = "streamable-http"
DEFAULT_HOST: Final = "127.0.0.1"
DEFAULT_PORT: Final = 8000
DEFAULT_HTTP_PATH: Final = "/mcp"
LOOPBACK_HOSTS: Final = frozenset({"127.0.0.1", "localhost", "::1"})

# --------------------------------------------------------------------------- #
# Files
# --------------------------------------------------------------------------- #

#: Inline (base64) content larger than this is rejected; pass a path instead.
MAX_INLINE_BYTES: Final = 20 * 1024 * 1024
#: Local files larger than this go through a presigned upload automatically.
PRESIGNED_THRESHOLD_BYTES: Final = 100 * 1024 * 1024

# --------------------------------------------------------------------------- #
# HTTP auth
# --------------------------------------------------------------------------- #

ASGI_TYPE: Final = "type"
ASGI_HEADERS: Final = "headers"
ASGI_STATUS: Final = "status"
ASGI_BODY: Final = "body"
ASGI_RESPONSE_START: Final = "http.response.start"
ASGI_RESPONSE_BODY: Final = "http.response.body"
SCOPE_HTTP: Final = "http"
HEADER_AUTHORIZATION: Final = b"authorization"
HEADER_CONTENT_TYPE: Final = b"content-type"
HEADER_WWW_AUTHENTICATE: Final = b"www-authenticate"
HEADER_ENCODING: Final = "latin-1"
BEARER_PREFIX: Final = "Bearer "
HTTP_UNAUTHORIZED: Final = 401
UNAUTHORIZED_BODY: Final = b'{"error":"unauthorized"}'
JSON_CONTENT_TYPE: Final = b"application/json"
WWW_AUTHENTICATE: Final = b'Bearer realm="dreep-mcp"'

# --------------------------------------------------------------------------- #
# Result shapes
# --------------------------------------------------------------------------- #

RAW_FIELD: Final = "raw"
KEY_URL: Final = "url"
KEY_DELETED: Final = "deleted"
KEY_ID: Final = "id"
KEY_PRESETS: Final = "presets"
KEY_TEXT: Final = "text"
#: A preset without an output format is rejected by the API (verified live).
FORMAT_KEY: Final = "format"
