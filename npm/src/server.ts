import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";

import { CONTRACT, VERSION } from "./contract.js";
import type { ToolRegistry } from "./registry.js";

/**
 * The MCP server. It uses the SDK's lower-level `Server` because the schemas
 * already exist as JSON Schema in the contract, so there's nothing to rewrite
 * as zod, and nothing that could differ from the Python server.
 */
export const createServer = (registry: ToolRegistry): Server => {
  const server = new Server(
    {
      name: CONTRACT.serverName,
      title: CONTRACT.serverTitle,
      version: VERSION,
      websiteUrl: CONTRACT.websiteUrl,
    },
    { capabilities: { tools: {} }, instructions: CONTRACT.instructions },
  );
  server.setRequestHandler(ListToolsRequestSchema, () => ({ tools: registry.tools as never }));
  server.setRequestHandler(CallToolRequestSchema, ({ params }) =>
    registry.call(params.name, params.arguments ?? {}),
  );
  return server;
};
