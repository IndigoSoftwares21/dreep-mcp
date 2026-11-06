"""The Python package and the Node server must carry the same version.

    python scripts/check_versions.py            # versions agree
    python scripts/check_versions.py v1.2.3     # ...and match this release tag

Prints the version on success, so the release workflow can reuse it.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parent.parent
PYTHON_VERSION_FILE: Final = ROOT / "src" / "dreep_mcp" / "_version.py"
NPM_MANIFEST: Final = ROOT / "npm" / "package.json"
VERSION_PATTERN: Final = re.compile(r'__version__ = "([^"]+)"')
TAG_PREFIX: Final = "v"
VERSION_KEY: Final = "version"
OK, FAIL = 0, 1


def python_version() -> str:
    match = VERSION_PATTERN.search(PYTHON_VERSION_FILE.read_text())
    if not match:
        raise SystemExit(f"No __version__ in {PYTHON_VERSION_FILE}")
    return match[1]


def npm_version() -> str:
    return str(json.loads(NPM_MANIFEST.read_text())[VERSION_KEY])


def check(tag: str | None = None) -> int:
    py, npm = python_version(), npm_version()
    if py != npm:
        sys.stderr.write(f"Version mismatch: _version.py has {py}, package.json has {npm}.\n")
        return FAIL
    if tag is not None and tag != f"{TAG_PREFIX}{py}":
        sys.stderr.write(f"Tag {tag} doesn't match package version {py}.\n")
        return FAIL
    print(py)
    return OK


if __name__ == "__main__":
    sys.exit(check(sys.argv[1] if len(sys.argv) > 1 else None))
