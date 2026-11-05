#!/usr/bin/env bash
# The full quality gate: run by the pre-commit hook and by CI.
# Cheap checks first, then analysis, then tests. Never bypass with --no-verify.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
PY="${PYTHON:-.venv/bin/python}"
[ -x "$PY" ] || PY="python"

step() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }

step "PyPI and npm versions agree"
"$PY" scripts/check_versions.py

step "Lint (ruff)"
"$PY" -m ruff check src tests scripts

step "Format (ruff)"
"$PY" -m ruff format --check src tests scripts

step "Repository rules (scripts/verify_rules.py)"
"$PY" scripts/verify_rules.py --summary

step "Types (mypy --strict)"
"$PY" -m mypy

step "Tests (pytest, coverage >= 90%)"
"$PY" -m pytest -q --cov --cov-report=term-missing:skip-covered

step "npm launcher (node --test)"
if command -v node >/dev/null 2>&1; then
  node --test npm/test/*.test.js
else
  echo "node not found: skipping (CI runs it)."
fi

printf '\n\033[32mQuality gate passed.\033[0m\n'
