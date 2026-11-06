import { DOT_SEGMENTS, UNSAFE_ID } from "./constants.js";
import { ToolError } from "./errors.js";

/**
 * Rejects ids that would change which endpoint a request reaches. The Node SDK
 * puts ids in the URL path as given, so `../usage` would otherwise resolve to a
 * different endpoint.
 */
export const safeId = (id: string): string => {
  if (id.length === 0 || UNSAFE_ID.test(id) || DOT_SEGMENTS.has(id)) {
    throw new ToolError(`Invalid id: ${JSON.stringify(id)}`);
  }
  return id;
};
