import { readFile, stat } from "node:fs/promises";
import { basename, sep } from "node:path";

import { lookup } from "mime-types";

import { BASE64, BASE64_BLOCK, DEFAULT_CONTENT_TYPE, ENV } from "./constants.js";
import { CONTRACT } from "./contract.js";
import { ToolError } from "./errors.js";
import { realLocation, type Settings } from "./settings.js";

export type ResolvedFile =
  | { kind: "path"; path: string; filename: string; size: number }
  | { kind: "inline"; data: Uint8Array<ArrayBuffer>; filename: string; size: number };

export interface FileArgs {
  path?: string;
  content_base64?: string;
  filename?: string;
}

const within = (path: string, roots: string[]): boolean =>
  roots.some((root) => path === root || path.startsWith(root.endsWith(sep) ? root : root + sep));

const fromPath = async (
  settings: Settings,
  raw: string,
  filename: string | undefined,
): Promise<ResolvedFile> => {
  const path = realLocation(raw);
  if (settings.fileRoots.length > 0) {
    if (!within(path, settings.fileRoots)) {
      const roots = settings.fileRoots.join(", ");
      throw new ToolError(`${path} is outside the allowed file roots (${roots}).`);
    }
  } else if (!settings.allowAnyLocalPath) {
    throw new ToolError(
      `Reading local files is disabled on this transport. Set ${ENV.FILE_ROOTS} ` +
        "on the server, or send content_base64 instead.",
    );
  }
  const info = await stat(path).catch(() => undefined);
  if (!info?.isFile()) {
    throw new ToolError(`No such file: ${path}`);
  }
  return { kind: "path", path, filename: filename ?? basename(path), size: info.size };
};

const fromBase64 = (content: string, filename: string | undefined): ResolvedFile => {
  if (!filename) {
    throw new ToolError("filename is required with content_base64.");
  }
  if (!BASE64.test(content) || content.length % BASE64_BLOCK !== 0) {
    throw new ToolError("content_base64 is not valid base64.");
  }
  const decoded = Buffer.from(content, "base64");
  const limit = CONTRACT.limits.maxInlineBytes;
  if (decoded.length > limit) {
    throw new ToolError(
      `Inline content is ${decoded.length} bytes; the limit is ${limit}. Pass a path instead.`,
    );
  }
  return { kind: "inline", data: new Uint8Array(decoded), filename, size: decoded.length };
};

/** Exactly one of `path` or `content_base64` must be given. */
export const resolveFile = async (settings: Settings, args: FileArgs): Promise<ResolvedFile> => {
  if ((args.path === undefined) === (args.content_base64 === undefined)) {
    throw new ToolError("Give exactly one of 'path' or 'content_base64'.");
  }
  return args.path !== undefined
    ? fromPath(settings, args.path, args.filename)
    : fromBase64(args.content_base64 as string, args.filename);
};

export const contentTypeOf = (filename: string, explicit?: string): string =>
  explicit ?? (lookup(filename) || DEFAULT_CONTENT_TYPE);

/** A Blob for the SDK's multipart upload; a typed Blob keeps the MIME type on the wire. */
export const toBlob = async (file: ResolvedFile, contentType?: string): Promise<Blob> => {
  const type = contentTypeOf(file.filename, contentType);
  if (file.kind === "inline") {
    return new Blob([file.data], { type });
  }
  return new Blob([new Uint8Array(await readFile(file.path))], { type });
};
