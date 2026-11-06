# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- The npm package is now a native Node server (Node 20+), built on the `dreep` npm SDK and
  the official MCP TypeScript SDK. `npx -y dreep-mcp` no longer needs uv, pipx or Python.
  It serves the same tools as the Python server, from a contract generated from it. The one
  difference: `extract_text` has no `include_blocks` option yet, because the Node SDK can't
  send it.

## [0.1.0]

### Added

- The Dreep MCP server, built on the `dreep` Python SDK 0.1.x and the MCP Python SDK 2.x.
- Tools: `upload_file`, `create_upload_url`, `confirm_upload`, `list_media`,
  `remove_background`, `extract_text`, `convert_document`, `build_delivery_url`,
  `build_signed_url`, `create_folder`, `list_folders`, `create_preset`, `list_presets`,
  `get_usage`, and the opt-in `delete_media` and `delete_preset`.
- stdio and streamable HTTP transports, with bearer-token protection for HTTP.
- File-root sandboxing with `DREEP_MCP_FILE_ROOTS`.
- The `dreep-mcp` npm package, which runs the server through `uvx` or `pipx`.
