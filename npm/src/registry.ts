import { Ajv, type ValidateFunction } from "ajv";
import { DreepError } from "dreep";

import { CONTRACT, type ToolContract } from "./contract.js";
import { ToolError } from "./errors.js";
import { toResult } from "./serialize.js";
import { mediaTools } from "./toolsMedia.js";
import { processingTools } from "./toolsProcessing.js";
import { projectTools } from "./toolsProject.js";
import { uploadTools } from "./toolsUploads.js";
import { urlTools } from "./toolsUrls.js";
import type { ToolDeps, ToolHandler } from "./toolTypes.js";

export interface ToolResponse {
  [key: string]: unknown;
  content: { type: "text"; text: string }[];
  structuredContent?: Record<string, unknown>;
  isError?: boolean;
}

export interface ToolRegistry {
  tools: ToolContract[];
  call: (name: string, args: Record<string, unknown>) => Promise<ToolResponse>;
}

interface RegisteredTool {
  handler: ToolHandler;
  validate: ValidateFunction;
}

const failure = (message: string): ToolResponse => ({
  content: [{ type: "text", text: message }],
  isError: true,
});

/** Schemas allow null for "not given"; handlers only ever see undefined. */
const withoutNulls = (value: unknown): unknown => {
  if (Array.isArray(value)) {
    return value.map(withoutNulls);
  }
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .filter(([, inner]) => inner !== null)
        .map(([key, inner]) => [key, withoutNulls(inner)]),
    );
  }
  return value;
};

const describeError = (error: unknown): string => {
  if (error instanceof ToolError || error instanceof TypeError) {
    return error.message;
  }
  if (error instanceof DreepError) {
    const issues = (error.validationErrors ?? []).map((i) => `${i.path.join(".")}: ${i.message}`);
    const detail = issues.length > 0 ? ` (${issues.join("; ")})` : "";
    return error.status === undefined
      ? `${error.message}${detail}`
      : `Dreep API error: ${error.message}${detail}`;
  }
  // Anything else is a bug: log it, and don't hand internals to the agent.
  process.stderr.write(`Unexpected tool failure: ${String(error)}\n`);
  return "The tool failed unexpectedly. See the server's log.";
};

const isDestructive = (tool: ToolContract): boolean => tool.annotations.destructiveHint === true;

/** One per server process: schemas compile once, however many requests follow. */
export const createRegistry = (deps: ToolDeps): ToolRegistry => {
  const handlers: Record<string, ToolHandler> = {
    ...uploadTools(deps),
    ...mediaTools(deps),
    ...processingTools(deps),
    ...urlTools(deps),
    ...projectTools(deps),
  };
  const ajv = new Ajv({ allErrors: true, strict: false });
  const tools = CONTRACT.tools.filter((tool) => deps.settings.allowDelete || !isDestructive(tool));
  const registered = new Map<string, RegisteredTool>();
  for (const tool of tools) {
    const handler = handlers[tool.name];
    if (!handler) {
      throw new Error(`The contract has a tool with no handler: ${tool.name}`);
    }
    registered.set(tool.name, { handler, validate: ajv.compile(tool.inputSchema) });
  }

  const call: ToolRegistry["call"] = async (name, args) => {
    const tool = registered.get(name);
    if (!tool) {
      return failure(`Unknown tool: ${name}`);
    }
    if (!tool.validate(args)) {
      return failure(`Invalid arguments: ${ajv.errorsText(tool.validate.errors)}`);
    }
    try {
      const output = await tool.handler(withoutNulls(args));
      if (output === null || typeof output !== "object") {
        throw new ToolError("Dreep returned an unexpected response.");
      }
      const result = toResult(output);
      return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        structuredContent: result,
      };
    } catch (error) {
      return failure(describeError(error));
    }
  };

  return { tools, call };
};
