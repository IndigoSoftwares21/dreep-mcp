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

step "Node server's tool contract matches the Python server"
"$PY" scripts/export_contract.py --check

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

step "Node server (tsc, node --test, coverage >= 90%)"
(
  cd npm
  [ -d node_modules ] || npm ci --silent
  npm run --silent test:coverage
)

printf '\n\033[32mQuality gate passed.\033[0m\n'
