import type { TransformParams } from "dreep";

/** The `transform` tool argument: the SDK's fields, under snake_case names. */
export type TransformArg = Record<string, unknown>;

const toCamel = (key: string): string => key.replace(/_([a-z])/g, (_, c: string) => c.toUpperCase());

export const toSdkTransform = (transform: TransformArg | undefined): TransformParams | undefined =>
  transform === undefined
    ? undefined
    : (Object.fromEntries(
        Object.entries(transform).map(([key, value]) => [toCamel(key), value]),
      ) as TransformParams);
