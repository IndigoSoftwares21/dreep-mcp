# dreep-mcp

The official [Dreep](https://dreep.cloud) MCP server: give any AI agent a media pipeline.
Upload, transform, convert, OCR and deliver images, videos and documents from Claude,
Cursor, VS Code, Codex, Gemini and every other MCP client.

This package is a native Node server. It needs Node 20 or later, and nothing else.

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

For streamable HTTP, run `npx -y dreep-mcp --transport http`.

Full documentation, the tool list, security settings and setup for each client:
**https://github.com/IndigoSoftwares21/dreep-mcp**

Prefer Python? The same tools are on PyPI as
[`dreep-mcp`](https://pypi.org/project/dreep-mcp/).
