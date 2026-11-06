import { realpathSync } from "node:fs";
import { homedir } from "node:os";
import { delimiter, join, resolve } from "node:path";

import { ENV, TRANSPORT, TRUTHY, type Transport } from "./constants.js";

/**
 * Server settings. The API key and signing secret aren't here: the client is
 * built from them separately and they go nowhere else.
 */
export interface Settings {
  /** Register `delete_media` and `delete_preset`. */
  allowDelete: boolean;
  /** When non-empty, file tools may only read files beneath these directories. */
  fileRoots: string[];
  /**
   * Whether a local path outside any root may be read. True over stdio (the
   * server runs as the user, on the user's machine); false over HTTP, where the
   * caller is remote and must not read the host's files.
   */
  allowAnyLocalPath: boolean;
  /** Bearer token required by the HTTP transport, if set. */
  httpToken: string | undefined;
}

type Env = Record<string, string | undefined>;

export const expandHome = (path: string): string =>
  path === "~" || path.startsWith("~/") ? join(homedir(), path.slice(1)) : path;

/** The real location of a path, following symlinks when the path exists. */
export const realLocation = (path: string): string => {
  const absolute = resolve(expandHome(path));
  try {
    return realpathSync(absolute);
  } catch {
    return absolute;
  }
};

export const settingsFromEnv = (
  env: Env = process.env,
  transport: Transport = TRANSPORT.STDIO,
): Settings => ({
  allowDelete: TRUTHY.has((env[ENV.ALLOW_DELETE] ?? "").trim().toLowerCase()),
  fileRoots: (env[ENV.FILE_ROOTS] ?? "")
    .split(delimiter)
    .filter((root) => root.trim().length > 0)
    .map(realLocation),
  allowAnyLocalPath: transport === TRANSPORT.STDIO,
  httpToken: env[ENV.HTTP_TOKEN] || undefined,
});
