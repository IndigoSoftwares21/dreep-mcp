"""Server settings, resolved once from the environment and the command line.

The Dreep API key and URL signing secret are not read here: the ``dreep`` SDK
reads ``DREEP_API_KEY`` and ``DREEP_SIGNING_SECRET`` itself.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dreep_mcp import _constants as c


def _flag(env: Mapping[str, str], name: str) -> bool:
    value = env.get(name)
    return value is not None and value.strip().lower() in c.TRUTHY


def _roots(env: Mapping[str, str]) -> tuple[Path, ...]:
    raw = env.get(c.ENV_FILE_ROOTS, "")
    return tuple(Path(p).expanduser().resolve() for p in raw.split(os.pathsep) if p.strip())


@dataclass(frozen=True, kw_only=True)
class Settings:
    #: Register ``delete_media`` and ``delete_preset``.
    allow_delete: bool = False
    #: When non-empty, file tools may only read files beneath these directories.
    file_roots: tuple[Path, ...] = ()
    #: Whether a local path outside any root may be read. True over stdio (the
    #: server runs as the user, on the user's machine); False over HTTP, where
    #: the caller is remote and must not read the host's files.
    allow_any_local_path: bool = True
    #: Bearer token required by the HTTP transport, if set.
    http_token: str | None = None

    @classmethod
    def from_env(
        cls, env: Mapping[str, str] | None = None, *, transport: c.Transport = c.Transport.STDIO
    ) -> Settings:
        env = os.environ if env is None else env
        return cls(
            allow_delete=_flag(env, c.ENV_ALLOW_DELETE),
            file_roots=_roots(env),
            allow_any_local_path=transport is c.Transport.STDIO,
            http_token=env.get(c.ENV_HTTP_TOKEN) or None,
        )
