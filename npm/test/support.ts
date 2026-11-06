import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { Dreep } from "dreep";

import { createRegistry } from "../src/registry.js";
import { createServer } from "../src/server.js";
import type { Settings } from "../src/settings.js";

export const API_KEY = "drp_test_0123456789abcdef";
export const SIGNING_SECRET = "test_signing_secret";
export const ASSET_ID = "2f928a3f-1d2a-4a2b-8a8b-123456789abc";
export const ASSET_URL = `https://cdn.dreep.cloud/api/v1/fetch/${ASSET_ID}.webp`;

export const envelope = (data: unknown, status = 200): Response =>
  new Response(JSON.stringify({ message: "ok", code: "OK", data }), {
    status,
    headers: { "content-type": "application/json" },
  });

export const assetPayload = (overrides: Record<string, unknown> = {}) => ({
  id: ASSET_ID,
  url: ASSET_URL,
  originalFilename: "hero.jpg",
  mimetype: "image/webp",
  sizeBytes: "245000",
  status: "ready",
  folder: "marketing/2026",
  createdAt: "2026-08-16T18:53:29.000Z",
  ...overrides,
});

export interface RecordedRequest {
  url: URL;
  method: string;
  headers: Headers;
  body: unknown;
}

/** Replaces global fetch with a scripted queue, recording every request. */
export const stubFetch = (...responses: Response[]): RecordedRequest[] => {
  const requests: RecordedRequest[] = [];
  globalThis.fetch = (async (input: string | URL | Request, init: RequestInit = {}) => {
    requests.push({
      url: new URL(String(input)),
      method: init.method ?? "GET",
      headers: new Headers(init.headers),
      body: init.body,
    });
    const response = responses.shift();
    if (!response) {
      throw new Error(`Unexpected request: ${String(input)}`);
    }
    return response;
  }) as typeof fetch;
  return requests;
};

const realFetch = globalThis.fetch;
export const restoreFetch = (): void => {
  globalThis.fetch = realFetch;
};

export const settings = (overrides: Partial<Settings> = {}): Settings => ({
  allowDelete: false,
  fileRoots: [],
  allowAnyLocalPath: true,
  httpToken: undefined,
  ...overrides,
});

export const registry = (overrides: Partial<Settings> = {}) =>
  createRegistry({
    client: new Dreep({ apiKey: API_KEY, signingSecret: SIGNING_SECRET }),
    settings: settings(overrides),
  });

/** A real MCP client connected to the server in memory. */
export const connect = async (overrides: Partial<Settings> = {}): Promise<Client> => {
  const [clientSide, serverSide] = InMemoryTransport.createLinkedPair();
  await createServer(registry(overrides)).connect(serverSide);
  const client = new Client({ name: "test", version: "1" });
  await client.connect(clientSide);
  return client;
};

export interface CallResult {
  isError?: boolean;
  structuredContent?: Record<string, any>;
  content: { type: string; text: string }[];
}

export const callTool = async (
  name: string,
  args: Record<string, unknown>,
  overrides: Partial<Settings> = {},
): Promise<CallResult> => {
  const client = await connect(overrides);
  try {
    return (await client.callTool({ name, arguments: args })) as CallResult;
  } finally {
    await client.close();
  }
};

/** Calls a tool that must succeed and returns its structured result. */
export const callOk = async (
  name: string,
  args: Record<string, unknown>,
  overrides: Partial<Settings> = {},
): Promise<Record<string, any>> => {
  const result = await callTool(name, args, overrides);
  if (result.isError || !result.structuredContent) {
    throw new Error(`Expected success: ${result.content[0]?.text}`);
  }
  return result.structuredContent;
};

/** Calls a tool that must fail and returns the message the agent sees. */
export const callError = async (
  name: string,
  args: Record<string, unknown>,
  overrides: Partial<Settings> = {},
): Promise<string> => {
  const result = await callTool(name, args, overrides);
  if (!result.isError) {
    throw new Error(`Expected failure: ${JSON.stringify(result.structuredContent)}`);
  }
  return result.content[0]?.text ?? "";
};

export const formField = (body: unknown, name: string) =>
  (body as FormData).get(name);
