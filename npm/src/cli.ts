import { parseArgs } from "node:util";

import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { Dreep, DreepError } from "dreep";

import {
  DEFAULT_HOST,
  DEFAULT_HTTP_PATH,
  DEFAULT_PORT,
  ENV,
  EXIT_USAGE,
  LOOPBACK_HOSTS,
  TRANSPORT,
  type Transport,
} from "./constants.js";
import { VERSION } from "./contract.js";
import { createMcpHttpServer } from "./httpServer.js";
import { createRegistry } from "./registry.js";
import { createServer } from "./server.js";
import { type Settings, settingsFromEnv } from "./settings.js";

export const USAGE = `Usage: dreep-mcp [options]

The Dreep MCP server.

  --transport <stdio|http>  stdio for local clients (default), http for streamable HTTP
  --host <host>             HTTP bind address (default ${DEFAULT_HOST})
  --port <port>             HTTP port (default ${DEFAULT_PORT})
  --path <path>             HTTP endpoint path (default ${DEFAULT_HTTP_PATH})
  --version                 Show the version
  --help                    Show this help
`;

const PUBLIC_WITHOUT_TOKEN =
  `Refusing to serve on a non-loopback host without ${ENV.HTTP_TOKEN}: anyone who can ` +
  "reach the port could act on your Dreep project. Set a token, or bind to 127.0.0.1.\n";

export interface CliOptions {
  transport: Transport;
  host: string;
  port: number;
  path: string;
  version: boolean;
  help: boolean;
}

export class UsageError extends Error {}

export const parseCli = (argv: string[]): CliOptions => {
  let values;
  try {
    ({ values } = parseArgs({
      args: argv,
      options: {
        transport: { type: "string", default: TRANSPORT.STDIO },
        host: { type: "string", default: DEFAULT_HOST },
        port: { type: "string", default: String(DEFAULT_PORT) },
        path: { type: "string", default: DEFAULT_HTTP_PATH },
        version: { type: "boolean", default: false },
        help: { type: "boolean", default: false },
      },
    }));
  } catch (error) {
    throw new UsageError(`${(error as Error).message}\n`);
  }
  const transports: string[] = Object.values(TRANSPORT);
  if (!transports.includes(values.transport)) {
    throw new UsageError(`--transport must be one of: ${transports.join(", ")}\n`);
  }
  const port = Number(values.port);
  if (!Number.isInteger(port) || port < 0) {
    throw new UsageError("--port must be a port number.\n");
  }
  return { ...values, transport: values.transport as Transport, port };
};

const buildClient = (env: NodeJS.ProcessEnv): Dreep =>
  new Dreep({
    apiKey: env[ENV.API_KEY] ?? "",
    ...(env[ENV.SIGNING_SECRET] ? { signingSecret: env[ENV.SIGNING_SECRET] } : {}),
  });

const serve = async (options: CliOptions, settings: Settings, client: Dreep): Promise<void> => {
  const registry = createRegistry({ client, settings });
  if (options.transport === TRANSPORT.STDIO) {
    await createServer(registry).connect(new StdioServerTransport());
    return;
  }
  const { host, port, path } = options;
  createMcpHttpServer({ registry, host, path, token: settings.httpToken }).listen(port, host, () => {
    process.stderr.write(`dreep-mcp listening on ${host}:${port}${path}\n`);
  });
};

/** Returns the exit code, or undefined when the server keeps running. */
export const main = async (
  argv: string[],
  env: NodeJS.ProcessEnv = process.env,
): Promise<number | undefined> => {
  let options: CliOptions;
  try {
    options = parseCli(argv);
  } catch (error) {
    process.stderr.write((error as Error).message);
    return EXIT_USAGE;
  }
  if (options.help || options.version) {
    process.stdout.write(options.help ? USAGE : `dreep-mcp ${VERSION}\n`);
    return 0;
  }
  const settings = settingsFromEnv(env, options.transport);
  const isPublicHttp = options.transport === TRANSPORT.HTTP && !LOOPBACK_HOSTS.has(options.host);
  if (isPublicHttp && !settings.httpToken) {
    process.stderr.write(PUBLIC_WITHOUT_TOKEN);
    return EXIT_USAGE;
  }
  let client: Dreep;
  try {
    client = buildClient(env);
  } catch (error) {
    if (!(error instanceof DreepError)) {
      throw error;
    }
    process.stderr.write(`${error.message} Set ${ENV.API_KEY}.\n`);
    return EXIT_USAGE;
  }
  await serve(options, settings, client);
  return undefined;
};
