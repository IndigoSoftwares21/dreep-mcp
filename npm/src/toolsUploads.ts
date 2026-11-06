import { CONTRACT } from "./contract.js";
import { contentTypeOf, type FileArgs, resolveFile, toBlob } from "./fileInput.js";
import { safeId } from "./ids.js";
import { uploadPresigned } from "./presignedUpload.js";
import { type FolderTargetArgs, folderTarget, type ToolDeps, type ToolHandlers } from "./toolTypes.js";
import { type TransformArg, toSdkTransform } from "./transform.js";

interface UploadFileArgs extends FileArgs, FolderTargetArgs {
  content_type?: string;
  key?: string;
  transform?: TransformArg;
  preset_key?: string;
}

interface CreateUploadUrlArgs extends FolderTargetArgs {
  content_type: string;
  size_bytes: number;
  filename?: string;
  key?: string;
  content_hash?: string;
}

interface ConfirmUploadArgs {
  upload_id: string;
  transform?: TransformArg;
  preset_key?: string;
}

export const uploadTools = ({ client, settings }: ToolDeps): ToolHandlers => ({
  upload_file: async (args: UploadFileArgs) => {
    const file = await resolveFile(settings, args);
    const shared = {
      key: args.key,
      ...folderTarget(args),
      transform: toSdkTransform(args.transform),
      presetKey: args.preset_key,
    };
    if (file.kind === "path" && file.size > CONTRACT.limits.presignedThresholdBytes) {
      return uploadPresigned(client, {
        ...shared,
        path: file.path,
        size: file.size,
        filename: file.filename,
        contentType: contentTypeOf(file.filename, args.content_type),
      });
    }
    return client.upload({
      ...shared,
      file: await toBlob(file, args.content_type),
      filename: file.filename,
    });
  },

  create_upload_url: (args: CreateUploadUrlArgs) =>
    client.presignUpload({
      contentType: args.content_type,
      sizeBytes: args.size_bytes,
      filename: args.filename,
      key: args.key,
      ...folderTarget(args),
      contentHash: args.content_hash,
    }),

  confirm_upload: (args: ConfirmUploadArgs) =>
    client.confirmUpload({
      id: safeId(args.upload_id),
      transform: toSdkTransform(args.transform),
      presetKey: args.preset_key,
    }),
});
