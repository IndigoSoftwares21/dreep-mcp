import { safeId } from "./ids.js";
import type { ToolDeps, ToolHandlers } from "./toolTypes.js";

interface ListMediaArgs {
  page?: number;
  limit?: number;
  folder?: string;
  folder_id?: string;
  recursive?: boolean;
}

export const mediaTools = ({ client }: ToolDeps): ToolHandlers => ({
  list_media: async (args: ListMediaArgs) => {
    const { assets, pagination } = await client.listMedia({
      page: args.page,
      limit: args.limit,
      folder: args.folder,
      folderId: args.folder_id,
      recursive: args.recursive,
    });
    return {
      // Python's model calls this field `mimetype`; the Node SDK keeps the wire's `type`.
      assets: assets.map(({ type, ...asset }) => ({ ...asset, mimetype: type })),
      pagination,
    };
  },

  delete_media: async (args: { media_id: string }) => {
    await client.deleteMedia({ id: safeId(args.media_id) });
    return { id: args.media_id, deleted: true };
  },
});
