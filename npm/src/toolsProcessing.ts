import type { ConvertFormat } from "dreep";

import { type FileArgs, resolveFile, toBlob } from "./fileInput.js";
import { type FolderTargetArgs, folderTarget, type ToolDeps, type ToolHandlers } from "./toolTypes.js";

type ProcessingArgs = FileArgs & FolderTargetArgs;

interface ConvertDocumentArgs extends ProcessingArgs {
  format: ConvertFormat;
  page?: number;
  key?: string;
}

export const processingTools = ({ client, settings }: ToolDeps): ToolHandlers => {
  /** Every processing call takes its file and destination the same way. */
  const fileAndTarget = async (args: ProcessingArgs) => {
    const file = await resolveFile(settings, args);
    return { file: await toBlob(file), filename: file.filename, ...folderTarget(args) };
  };

  return {
    remove_background: async (args: ProcessingArgs) =>
      client.removeBackground(await fileAndTarget(args)),

    extract_text: async (args: ProcessingArgs) => client.extractText(await fileAndTarget(args)),

    convert_document: async (args: ConvertDocumentArgs) =>
      client.convertDocument({
        ...(await fileAndTarget(args)),
        format: args.format,
        page: args.page,
        key: args.key,
      }),
  };
};
