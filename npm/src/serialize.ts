/**
 * SDK results -> the JSON objects tools return.
 *
 * The Node SDK returns camelCase and the Python SDK snake_case. Tool results use
 * snake_case, so an agent sees the same fields from either server.
 */

/** Holds transform values exactly as stored, so its keys aren't result fields. */
const OPAQUE_KEYS = new Set(["params"]);

/**
 * The API sends these as strings (Postgres BIGINT). The Node SDK only converts
 * them on some endpoints, so it happens once here for all of them.
 */
const NUMERIC_KEYS = new Set(["sizeBytes", "storageBytes"]);
const DIGITS = /^\d+$/;

const toSnake = (key: string): string => key.replace(/[A-Z]/g, (c) => `_${c.toLowerCase()}`);

const convertField = (key: string, value: unknown): unknown => {
  if (OPAQUE_KEYS.has(key)) {
    return value;
  }
  if (NUMERIC_KEYS.has(key) && typeof value === "string" && DIGITS.test(value)) {
    return Number(value);
  }
  return convert(value);
};

const convert = (value: unknown): unknown => {
  if (Array.isArray(value)) {
    return value.map(convert);
  }
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, inner]) => [toSnake(key), convertField(key, inner)]),
    );
  }
  return value;
};

export const toResult = (value: object): Record<string, unknown> =>
  convert(value) as Record<string, unknown>;
