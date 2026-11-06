import { createReadStream } from "node:fs";
import { Readable } from "node:stream";
import { setTimeout as sleep } from "node:timers/promises";

import { type Asset, type Dreep, DreepConflictError, type TransformParams } from "dreep";

import { CONFIRM_ATTEMPTS, CONFIRM_RETRY_DELAY_MS } from "./constants.js";
import { ToolError } from "./errors.js";

export interface PresignedUploadParams {
  path: string;
  size: number;
  contentType: string;
  filename?: string | undefined;
  folder?: string | undefined;
  key?: string | undefined;
  folderId?: string | undefined;
  autoCreateFolders?: boolean | undefined;
  transform?: TransformParams | undefined;
  presetKey?: string | undefined;
}

/** Streams a file to storage. The URL is absolute, so no API key goes with it. */
const putFile = async (url: string, params: PresignedUploadParams): Promise<void> => {
  const response = await fetch(url, {
    method: "PUT",
    headers: { "content-type": params.contentType, "content-length": String(params.size) },
    body: Readable.toWeb(createReadStream(params.path)) as ReadableStream,
    duplex: "half",
  } as RequestInit);
  if (!response.ok) {
    throw new ToolError(`Storage rejected the upload with status ${response.status}.`);
  }
};

/** The API answers 409 until the bytes settle, so the confirm is what gets retried. */
const confirmSettled = async (
  client: Dreep,
  id: string,
  params: PresignedUploadParams,
  retryDelayMs: number,
): Promise<Asset> => {
  for (let attempt = 1; ; attempt += 1) {
    try {
      return await client.confirmUpload({
        id,
        transform: params.transform,
        presetKey: params.presetKey,
      });
    } catch (error) {
      if (!(error instanceof DreepConflictError) || attempt >= CONFIRM_ATTEMPTS) {
        throw error;
      }
      await sleep(retryDelayMs);
    }
  }
};

/** Presign, PUT and confirm: the path for files too large to hold in memory. */
export const uploadPresigned = async (
  client: Dreep,
  params: PresignedUploadParams,
  retryDelayMs: number = CONFIRM_RETRY_DELAY_MS,
): Promise<Asset> => {
  const presigned = await client.presignUpload({
    contentType: params.contentType,
    sizeBytes: params.size,
    filename: params.key ? undefined : params.filename,
    folder: params.folder,
    key: params.key,
    folderId: params.folderId,
    autoCreateFolders: params.autoCreateFolders,
  });
  if (!presigned.alreadyExists && presigned.uploadUrl) {
    await putFile(presigned.uploadUrl, params);
  }
  return confirmSettled(client, presigned.id, params, retryDelayMs);
};
