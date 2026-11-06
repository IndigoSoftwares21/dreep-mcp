/** Every name and default the server's behaviour depends on. */

export const ENV = {
  API_KEY: "DREEP_API_KEY",
  SIGNING_SECRET: "DREEP_SIGNING_SECRET",
  ALLOW_DELETE: "DREEP_MCP_ALLOW_DELETE",
  FILE_ROOTS: "DREEP_MCP_FILE_ROOTS",
  HTTP_TOKEN: "DREEP_MCP_HTTP_TOKEN",
} as const;

export const TRUTHY = new Set(["1", "true", "yes", "on"]);

export const TRANSPORT = { STDIO: "stdio", HTTP: "http" } as const;
export type Transport = (typeof TRANSPORT)[keyof typeof TRANSPORT];

export const DEFAULT_HOST = "127.0.0.1";
export const DEFAULT_PORT = 8000;
export const DEFAULT_HTTP_PATH = "/mcp";
export const LOOPBACK_HOSTS = new Set(["127.0.0.1", "localhost", "::1"]);

export const EXIT_USAGE = 2;

/** `dreep`'s Node SDK has no option for this, so the OCR tool doesn't offer it. */
export const UNSUPPORTED_PARAMS: Readonly<Record<string, readonly string[]>> = {
  extract_text: ["include_blocks"],
};

/** Literal `parentId` value that asks the API for top-level folders only. */
export const ROOT_PARENT_ID = "null";

/** Characters that would change which endpoint an id in a path reaches. */
export const UNSAFE_ID = /[/?#\\]/;
export const DOT_SEGMENTS = new Set([".", ".."]);

export const CONFIRM_ATTEMPTS = 5;
export const CONFIRM_RETRY_DELAY_MS = 1000;

export const DEFAULT_CONTENT_TYPE = "application/octet-stream";
export const BASE64 = /^[A-Za-z0-9+/]*={0,2}$/;
export const BASE64_BLOCK = 4;
export const URL_PROTOCOLS = new Set(["http:", "https:"]);

/** Base64 grows data by 4/3; the rest allows for the JSON-RPC envelope. */
export const HTTP_BODY_OVERHEAD_BYTES = 1024 * 1024;

export const HTTP_STATUS = {
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  METHOD_NOT_ALLOWED: 405,
  PAYLOAD_TOO_LARGE: 413,
} as const;

export const PACKAGE_NAME = "dreep-mcp";
