import type { Dreep } from "dreep";

import type { Settings } from "./settings.js";

export interface ToolDeps {
  client: Dreep;
  settings: Settings;
}

/**
 * Arguments have already passed the tool's JSON Schema when a handler runs, so
 * each handler can declare the shape it expects.
 */
export type ToolHandler = (args: any) => Promise<object> | object;
export type ToolHandlers = Record<string, ToolHandler>;

export interface FolderTargetArgs {
  folder?: string;
  folder_id?: string;
  auto_create_folders?: boolean;
}

/** The SDK's name for where a stored result goes. */
export const folderTarget = (args: FolderTargetArgs) => ({
  folder: args.folder,
  folderId: args.folder_id,
  autoCreateFolders: args.auto_create_folders,
});
