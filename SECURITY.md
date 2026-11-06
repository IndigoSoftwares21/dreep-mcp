# Security policy

## Reporting a vulnerability

**Please don't report security problems in public issues.** Use GitHub's
[private vulnerability reporting](https://github.com/IndigoSoftwares21/dreep-mcp/security/advisories/new)
instead. The maintainers, Abe Toluwani ([abetoluwani](https://github.com/abetoluwani)) and
Indigo ([IndigoSoftwares21](https://github.com/IndigoSoftwares21)), will acknowledge
your report, investigate it, and keep you updated until it is fixed.

Include the server version (`dreep-mcp --version`), your MCP client and transport, a
description of the problem and its impact, and how to reproduce it. Never include real
API keys, signing secrets or HTTP tokens.

## Supported versions

Security fixes are released for the latest minor version.

## How the server protects your project

- The Dreep API key stays in the server's environment. It is sent only to the Dreep API
  (by the [`dreep` SDK](https://github.com/IndigoSoftwares21/dreep-python)) and never
  appears in tool results.
- Delete tools are not registered unless `DREEP_MCP_ALLOW_DELETE` is set, and are
  annotated as destructive so clients ask before running them.
- File tools only read beneath `DREEP_MCP_FILE_ROOTS` when it is set. Over the HTTP
  transport, local file reads are disabled unless it is set, so a remote caller can't
  read the host's files.
- The HTTP transport binds to `127.0.0.1` by default, refuses a non-loopback address
  without `DREEP_MCP_HTTP_TOKEN`, and compares bearer tokens in constant time.
- Asset ids are validated by the SDK before they are put in a request path, so an id
  can't redirect a call to another endpoint.
