# AGENTS.md — dreep-mcp

Rules for anyone (human or agent) changing this repository. The quality gate
enforces most of them; the rest are review standards.

## Core principle

> Transport communicates. Schemas describe. Tools decide. Constants define.
> Tests protect behaviour.

## Architecture

```
src/dreep_mcp/
  __init__.py              public API surface (the only re-export module)
  __main__.py              python -m dreep_mcp

  # pure layer: no I/O libraries, no client construction (RULE-007)
  _constants.py            env var names, defaults, limits, result keys
  _settings.py             Settings.from_env: delete flag, file roots, HTTP token
  _params.py               shared Annotated tool parameters (schema + description)
  _transform_input.py      TransformInput: the SDK Transform as a pydantic schema
  _annotations.py          READ / LOCAL / CREATE / DELETE tool hints
  _file_input.py           path or base64 -> uploadable file, root sandboxing
  _serialize.py            SDK dataclasses -> JSON objects (raw dropped)
  _tool_call.py            run / guard / run_delete: the only error mapping
  _http_auth.py            bearer-token ASGI middleware

  # tools layer: calls the client it is handed, never builds one
  _tool_host.py            ToolHost(server, client, settings)
  _tools_uploads.py        upload_file, create_upload_url, confirm_upload
  _tools_media.py          list_media, delete_media (opt-in)
  _tools_processing.py     remove_background, extract_text, convert_document
  _tools_urls.py           build_delivery_url, build_signed_url (no network)
  _tools_project.py        folders, presets (delete opt-in), usage
  _server.py               create_server: registers every tool group

  # entry layer: the only code that runs an event loop or builds a client
  _cli.py                  argparse, stdio and streamable-HTTP transports

npm/                       npx launcher: runs the PyPI package via uvx or pipx
```

A tool call flows: MCP client → `MCPServer` validates arguments against the
schema → tool function → `resolve_file` (if it takes a file) → SDK call wrapped
in `run(...)` → `to_result` → structured JSON back to the agent.

## Hard rules

1. **Build on the `dreep` SDK.** Tools call `AsyncDreep`; they never speak HTTP
   to the Dreep API. A missing capability goes into the SDK first.
2. **Follow the API reference, verified live.** Signed URLs sign `"{id}:{exp}"`
   only; presets need `format`; access control is top-level only; there is no
   folder delete; fetching text via the delivery URL (`format=txt`) 404s, so OCR
   goes through `extract_text`. Always use asset URLs exactly as returned:
   projects can be on a custom CDN domain.
3. **Errors reach the agent.** Every SDK call goes through `run`, `guard` or
   `run_delete`, which turn SDK errors into `ToolError` with the SDK's message.
   Any other exception is hidden from the agent by the MCP SDK.
4. **Destructive tools are opt-in.** They register only when
   `settings.allow_delete` is true and carry the `DELETE` annotation.
5. **Never read files a remote caller shouldn't.** File access goes through
   `resolve_file`, which enforces `DREEP_MCP_FILE_ROOTS` and disables local
   paths over HTTP unless roots are set.
6. **Tool parameters are keyword-only and described.** Reuse `_params.py`
   aliases; docstrings are the description the model reads, so write them for it.
7. **No magic strings (RULE-004).** Behavioural literals live in `_constants.py`.
8. **DRY (RULE-005, RULE-006).** No six-line logic block twice; one definition
   per name across the package.
9. **Small modules (RULE-001).** Warn above 200 lines, fail above 400.
10. **Every suppression names its code (RULE-010).** `# type: ignore[code]`,
    `# noqa: CODE`, `# allow-magic: reason`.
11. **Tests ship with behaviour.** Tools are tested through a real MCP `Client`
    against an `httpx.MockTransport`; coverage floor is 90%.
12. **Never commit secrets.** API keys, signing secrets and HTTP tokens come
    from the environment only. Live testing uses a key passed by env var.
13. **Versions move together.** `src/dreep_mcp/_version.py` and
    `npm/package.json` always carry the same version; the release workflow
    refuses a tag that matches neither.

## Workflow

- Setup: `bash scripts/setup_hooks.sh` (venv, deps, hooks).
- Gate: `bash scripts/quality_gate.sh` (runs on pre-commit and in CI).
- Every change starts from an issue. Branch as `<type>/<issue-number>-<description>`.
- Every PR says `Closes #<issue>` (CI enforces it) and requests review from both
  maintainers, `abetoluwani` and `IndigoSoftwares21` (CODEOWNERS requests them
  automatically). Merge only after both approve. See CONTRIBUTING.md.
- `main` is protected: never push to it directly.
- Commits: Conventional Commits, ≤100 characters per line, signed.
- Never bypass hooks with `--no-verify`.
- Rule debt only shrinks: `scripts/rules-baseline.json` fails on increases and
  on stale headroom. Update it with `--update-baseline` only when lowering it.
