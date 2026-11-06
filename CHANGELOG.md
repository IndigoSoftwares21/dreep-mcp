# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- The HTTP transport now accepts inline files up to the advertised 20 MB. It was using the MCP
  SDK's default 4 MiB request limit, which refused `content_base64` above about 3 MiB.

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
