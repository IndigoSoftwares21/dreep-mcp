# dreep-mcp (npm)

The official [Dreep](https://dreep.cloud) MCP server, for clients that launch servers
with `npx`:

```json
{
  "mcpServers": {
    "dreep": {
      "command": "npx",
      "args": ["-y", "dreep-mcp"],
      "env": { "DREEP_API_KEY": "drp_live_your_key" }
    }
  }
}
```

This package is a small launcher. The server itself is the Python package
[`dreep-mcp`](https://pypi.org/project/dreep-mcp/); the launcher runs the matching version
through [uv](https://docs.astral.sh/uv/) (`uvx`), falling back to `pipx`. Install uv once:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Every option and argument is passed through, for example `npx -y dreep-mcp --transport http`.

Full documentation, the tool list and setup for Claude, Cursor, VS Code, Codex, Gemini and
other clients: **https://github.com/abetoluwani/dreep-mcp**
