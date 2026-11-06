import type { AccessControlType } from "dreep";

import { ROOT_PARENT_ID } from "./constants.js";
import { ToolError } from "./errors.js";
import { safeId } from "./ids.js";
import type { ToolDeps, ToolHandlers } from "./toolTypes.js";
import { type TransformArg, toSdkTransform } from "./transform.js";

interface CreateFolderArgs {
  name?: string;
  path?: string;
  parent_id?: string;
  parent_path?: string;
  access_control_type?: AccessControlType;
  default_expiry_seconds?: number;
}

interface ListFoldersArgs {
  path?: string;
  parent_id?: string;
  root_only?: boolean;
}

interface CreatePresetArgs {
  key: string;
  name: string;
  transform: TransformArg;
}

export const projectTools = ({ client }: ToolDeps): ToolHandlers => ({
  create_folder: (args: CreateFolderArgs) =>
    client.createFolder({
      name: args.name,
      path: args.path,
      parentId: args.parent_id,
      parentPath: args.parent_path,
      accessControlType: args.access_control_type,
      defaultExpirySeconds: args.default_expiry_seconds,
    }),

  list_folders: ({ path, parent_id, root_only }: ListFoldersArgs) => {
    if (root_only && (path !== undefined || parent_id !== undefined)) {
      throw new ToolError("root_only can't be combined with path or parent_id.");
    }
    return client.listFolders({ path, parentId: root_only ? ROOT_PARENT_ID : parent_id });
  },

  create_preset: ({ key, name, transform }: CreatePresetArgs) => {
    const params = toSdkTransform(transform);
    if (params?.format === undefined) {
      throw new ToolError("A preset's transform must include 'format'.");
    }
    return client.createPreset({ key, name, transform: params });
  },

  list_presets: async () => {
    // Typed as an array, but the API can also wrap the list as { presets }.
    const listed: unknown = await client.listPresets();
    const wrapped = (listed as { presets?: unknown } | null)?.presets;
    return { presets: Array.isArray(listed) ? listed : wrapped };
  },

  get_usage: () => client.getUsage(),

  delete_preset: async ({ preset_id }: { preset_id: string }) => {
    await client.deletePreset({ id: safeId(preset_id) });
    return { id: preset_id, deleted: true };
  },
});
