import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

/** The repository rules scan Python; these keep the same standards for the Node source. */
const MAX_LINES = 200;
const SOURCE = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "src");
const SECRET = /drp_live_[0-9A-Za-z]{16,}|sk_live_[0-9a-zA-Z]{24}|AKIA[0-9A-Z]{16}/;

const sources = readdirSync(SOURCE)
  .filter((name) => name.endsWith(".ts"))
  .map((name) => ({ name, text: readFileSync(join(SOURCE, name), "utf8") }));

test("source files stay small", () => {
  for (const { name, text } of sources) {
    assert.ok(text.split("\n").length <= MAX_LINES, `${name} is over ${MAX_LINES} lines`);
  }
});

test("nothing logs to stdout, which would corrupt the stdio transport", () => {
  for (const { name, text } of sources) {
    assert.doesNotMatch(text, /console\.(log|info|debug)\(/, name);
  }
});

test("no credentials in source", () => {
  for (const { name, text } of sources) {
    assert.doesNotMatch(text, SECRET, name);
  }
});
