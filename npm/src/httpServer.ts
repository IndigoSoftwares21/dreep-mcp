import { timingSafeEqual } from "node:crypto";
import {
  createServer as createHttpServer,
  type Server as HttpServer,
  type IncomingMessage,
  type ServerResponse,
} from "node:http";

import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";

import { HTTP_BODY_OVERHEAD_BYTES, HTTP_STATUS, LOOPBACK_HOSTS } from "./constants.js";
import { CONTRACT } from "./contract.js";
import type { ToolRegistry } from "./registry.js";
import { createServer } from "./server.js";

const BEARER = "Bearer ";
/** Only the path of a request's URL matters; this makes a relative one parseable. */
const ANY_ORIGIN = "http://localhost";
const MAX_BODY_BYTES =
  Math.ceil((CONTRACT.limits.maxInlineBytes * 4) / 3) + HTTP_BODY_OVERHEAD_BYTES;

export interface HttpOptions {
  registry: ToolRegistry;
  host: string;
  path: string;
  token: string | undefined;
}

const reply = (res: ServerResponse, status: number, error: string, headers = {}): void => {
  res.writeHead(status, { "content-type": "application/json", ...headers });
  res.end(JSON.stringify({ error }));
};

/** Compared in constant time, so the token can't be guessed byte by byte. */
export const tokenMatches = (header: string | undefined, token: string): boolean => {
  const presented = Buffer.from(header?.startsWith(BEARER) ? header.slice(BEARER.length) : "");
  const expected = Buffer.from(token);
  return presented.length === expected.length && timingSafeEqual(presented, expected);
};

/** A web page can't reach a local server through its own domain (DNS rebinding). */
const hostAllowed = (req: IncomingMessage, boundHost: string): boolean => {
  if (!LOOPBACK_HOSTS.has(boundHost)) {
    return true;
  }
  const origin = `http://${req.headers.host ?? ""}`;
  return URL.canParse(origin) && LOOPBACK_HOSTS.has(new URL(origin).hostname.replace(/^\[|\]$/g, ""));
};

const pathMatches = (req: IncomingMessage, path: string): boolean => {
  const url = req.url ?? "";
  return URL.canParse(url, ANY_ORIGIN) && new URL(url, ANY_ORIGIN).pathname === path;
};

const readBody = async (req: IncomingMessage): Promise<Buffer | undefined> => {
  const chunks: Buffer[] = [];
  let size = 0;
  for await (const chunk of req as AsyncIterable<Buffer>) {
    size += chunk.length;
    if (size > MAX_BODY_BYTES) {
      return undefined;
    }
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
};

/** Stateless: each POST gets its own transport, so no session state can leak or pile up. */
const serveMcp = async (req: IncomingMessage, res: ServerResponse, registry: ToolRegistry) => {
  const body = await readBody(req);
  if (body === undefined) {
    reply(res, HTTP_STATUS.PAYLOAD_TOO_LARGE, "request too large");
    return;
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(body.toString("utf8"));
  } catch {
    reply(res, HTTP_STATUS.BAD_REQUEST, "invalid JSON");
    return;
  }
  const server = createServer(registry);
  const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
  res.on("close", () => {
    void transport.close();
    void server.close();
  });
  await server.connect(transport as never);
  await transport.handleRequest(req, res, parsed);
};

export const createMcpHttpServer = ({ registry, host, path, token }: HttpOptions): HttpServer =>
  createHttpServer((req, res) => {
    if (token !== undefined && !tokenMatches(req.headers.authorization, token)) {
      reply(res, HTTP_STATUS.UNAUTHORIZED, "unauthorized", {
        "www-authenticate": 'Bearer realm="dreep-mcp"',
      });
    } else if (!hostAllowed(req, host)) {
      reply(res, HTTP_STATUS.FORBIDDEN, "host not allowed");
    } else if (!pathMatches(req, path)) {
      reply(res, HTTP_STATUS.NOT_FOUND, "not found");
    } else if (req.method !== "POST") {
      reply(res, HTTP_STATUS.METHOD_NOT_ALLOWED, "method not allowed", { allow: "POST" });
    } else {
      serveMcp(req, res, registry).catch((error: unknown) => {
        process.stderr.write(`HTTP request failed: ${String(error)}\n`);
        if (!res.headersSent) {
          reply(res, 500, "internal error");
        }
      });
    }
  });
