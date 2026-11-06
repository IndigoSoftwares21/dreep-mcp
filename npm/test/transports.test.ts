import assert from "node:assert/strict";
import type { Server as HttpServer } from "node:http";
import type { AddressInfo } from "node:net";
import { dirname, join } from "node:path";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

import { main, parseCli, UsageError } from "../src/cli.js";
import { ENV, EXIT_USAGE } from "../src/constants.js";
import { createMcpHttpServer, tokenMatches } from "../src/httpServer.js";
import { API_KEY, registry } from "./support.js";

const BIN = join(dirname(fileURLToPath(import.meta.url)), "..", "src", "bin.js");

test("end to end over stdio", async () => {
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: [BIN],
    env: { [ENV.API_KEY]: API_KEY, [ENV.ALLOW_DELETE]: "1" },
  });
  const client = new Client({ name: "test", version: "1" });
  await client.connect(transport);
  const { tools } = await client.listTools();
  const result = await client.callTool({
    name: "build_delivery_url",
    arguments: { url: "https://cdn.example.com/a.jpg", transform: { format: "avif" } },
  });
  await client.close();
  assert.equal(tools.length, 16);
  assert.deepEqual(result.structuredContent, { url: "https://cdn.example.com/a.jpg?format=avif" });
});

const TOKEN = "s3cret";
let http: HttpServer;
let base: string;

before(async () => {
  http = createMcpHttpServer({
    registry: registry({ allowAnyLocalPath: false }),
    host: "127.0.0.1",
    path: "/mcp",
    token: TOKEN,
  });
  await new Promise<void>((resolve) => http.listen(0, "127.0.0.1", resolve));
  base = `http://127.0.0.1:${(http.address() as AddressInfo).port}`;
});

after(() => {
  http.close();
});

const post = (headers: Record<string, string> = {}, body = "{}", path = "/mcp"): Promise<Response> =>
  fetch(`${base}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json", ...headers },
    body,
  });

const bearer = { authorization: `Bearer ${TOKEN}` };

test("end to end over HTTP with the token", async () => {
  const transport = new StreamableHTTPClientTransport(new URL(`${base}/mcp`), {
    requestInit: { headers: bearer },
  });
  const client = new Client({ name: "test", version: "1" });
  await client.connect(transport as never);
  const { tools } = await client.listTools();
  const result = await client.callTool({
    name: "upload_file",
    arguments: { path: "/etc/hosts" },
  });
  await client.close();
  assert.equal(tools.length, 14);
  assert.equal(result.isError, true);
  assert.match(JSON.stringify(result.content), /disabled on this transport/);
});

test("HTTP refuses a missing or wrong token", async () => {
  const refused: Record<string, string>[] = [
    {},
    { authorization: "Bearer wrong" },
    { authorization: TOKEN },
  ];
  for (const headers of refused) {
    const response = await post(headers);
    assert.equal(response.status, 401);
    assert.match(response.headers.get("www-authenticate") ?? "", /Bearer/);
  }
});

test("HTTP answers other paths, methods and bad bodies plainly", async () => {
  assert.equal((await post(bearer, "{}", "/other")).status, 404);
  assert.equal((await post(bearer, "not json")).status, 400);
  const get = await fetch(`${base}/mcp`, { headers: bearer });
  assert.equal(get.status, 405);
});

test("HTTP refuses an oversized request", async () => {
  const response = await post(bearer, "x".repeat(40 * 1024 * 1024));
  assert.equal(response.status, 413);
});

test("a loopback server refuses other Host headers", async () => {
  const { request } = await import("node:http");
  const { port } = http.address() as AddressInfo;
  for (const host of ["evil.example", "a b"]) {
    const status = await new Promise<number | undefined>((resolve, reject) => {
      const req = request({ port, method: "POST", path: "/mcp", headers: { ...bearer, host } }, (res) => {
        res.resume();
        resolve(res.statusCode);
      });
      req.on("error", reject);
      req.end("{}");
    });
    assert.ok(status === 403 || status === 400, `Host ${host} got ${status}`);
  }
});

test("a malformed request path doesn't take the server down", async () => {
  const { connect } = await import("node:net");
  const { port } = http.address() as AddressInfo;
  await new Promise<void>((resolve, reject) => {
    const socket = connect(port, "127.0.0.1", () => {
      socket.write(`POST // HTTP/1.1\r\nHost: 127.0.0.1\r\nAuthorization: Bearer ${TOKEN}\r\n\r\n`);
    });
    socket.once("data", (data) => {
      socket.destroy();
      assert.match(data.toString(), /^HTTP\/1\.1 404/);
      resolve();
    });
    socket.on("error", reject);
  });
});

test("tokenMatches compares only exact bearer tokens", () => {
  assert.equal(tokenMatches("Bearer t", "t"), true);
  assert.equal(tokenMatches("Bearer tt", "t"), false);
  assert.equal(tokenMatches(undefined, "t"), false);
});

test("the CLI parses its options", () => {
  assert.deepEqual(parseCli([]), {
    transport: "stdio",
    host: "127.0.0.1",
    port: 8000,
    path: "/mcp",
    version: false,
    help: false,
  });
  assert.throws(() => parseCli(["--transport", "carrier-pigeon"]), UsageError);
  assert.throws(() => parseCli(["--port", "abc"]), UsageError);
  assert.throws(() => parseCli(["--nope"]), UsageError);
});

const captureStderr = async (run: () => Promise<number | undefined>) => {
  const write = process.stderr.write;
  let output = "";
  process.stderr.write = ((chunk: string) => {
    output += chunk;
    return true;
  }) as typeof process.stderr.write;
  try {
    return { code: await run(), output };
  } finally {
    process.stderr.write = write;
  }
};

test("the CLI refuses unsafe or impossible starts", async () => {
  const publicHttp = await captureStderr(() =>
    main(["--transport", "http", "--host", "0.0.0.0"], { [ENV.API_KEY]: API_KEY }),
  );
  assert.equal(publicHttp.code, EXIT_USAGE);
  assert.match(publicHttp.output, /DREEP_MCP_HTTP_TOKEN/);
  const noKey = await captureStderr(() => main([], {}));
  assert.equal(noKey.code, EXIT_USAGE);
  assert.match(noKey.output, /DREEP_API_KEY/);
  const badArgs = await captureStderr(() => main(["--nope"], {}));
  assert.equal(badArgs.code, EXIT_USAGE);
});
