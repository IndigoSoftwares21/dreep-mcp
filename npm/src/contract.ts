import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { PACKAGE_NAME, UNSUPPORTED_PARAMS } from "./constants.js";

/**
 * The tool contract, generated from the Python server by
 * scripts/export_contract.py. Names, descriptions, schemas and annotations all
 * come from it, so the two servers can't drift apart.
 */
export interface ToolContract {
  name: string;
  description: string;
  inputSchema: Record<string, unknown> & { properties?: Record<string, unknown> };
  annotations: { destructiveHint?: boolean; readOnlyHint?: boolean; openWorldHint?: boolean };
}

export interface Contract {
  serverName: string;
  serverTitle: string;
  websiteUrl: string;
  instructions: string;
  limits: { maxInlineBytes: number; presignedThresholdBytes: number };
  tools: ToolContract[];
}

const MANIFEST = "package.json";
const CONTRACT_PATH = ["contract", "tools.json"];

const readJson = (path: string): unknown => JSON.parse(readFileSync(path, "utf8"));

/** Walks up to this package's root: the layout differs between dist and tests. */
const packageRoot = (start: string): string => {
  const manifest = join(start, MANIFEST);
  if (existsSync(manifest) && (readJson(manifest) as { name?: string }).name === PACKAGE_NAME) {
    return start;
  }
  const parent = dirname(start);
  if (parent === start) {
    throw new Error(`Can't find the ${PACKAGE_NAME} package root.`);
  }
  return packageRoot(parent);
};

const ROOT = packageRoot(dirname(fileURLToPath(import.meta.url)));

export const VERSION = (readJson(join(ROOT, MANIFEST)) as { version: string }).version;

const withoutUnsupported = (tool: ToolContract): ToolContract => {
  const properties = { ...tool.inputSchema.properties };
  for (const param of UNSUPPORTED_PARAMS[tool.name] ?? []) {
    delete properties[param];
  }
  return { ...tool, inputSchema: { ...tool.inputSchema, properties } };
};

const raw = readJson(join(ROOT, ...CONTRACT_PATH)) as Contract;

export const CONTRACT: Contract = { ...raw, tools: raw.tools.map(withoutUnsupported) };

/** The contract exactly as exported, for the test that checks what was removed. */
export const RAW_CONTRACT: Contract = raw;
