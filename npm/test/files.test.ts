import assert from "node:assert/strict";
import { mkdir, mkdtemp, realpath, symlink, writeFile } from "node:fs/promises";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { ENV, TRANSPORT } from "../src/constants.js";
import { CONTRACT } from "../src/contract.js";
import { ToolError } from "../src/errors.js";
import { contentTypeOf, resolveFile, toBlob } from "../src/fileInput.js";
import { expandHome, settingsFromEnv } from "../src/settings.js";
import { settings } from "./support.js";

const b64 = (text: string): string => Buffer.from(text).toString("base64");

const tempDir = async (): Promise<string> =>
  realpath(await mkdtemp(join(tmpdir(), "dreep-mcp-")));

test("a path resolves to the file, under its own name unless renamed", async () => {
  const path = join(await tempDir(), "a.png");
  await writeFile(path, "png");
  const own = await resolveFile(settings(), { path });
  assert.deepEqual(own, { kind: "path", path, filename: "a.png", size: 3 });
  const renamed = await resolveFile(settings(), { path, filename: "b.png" });
  assert.equal(renamed.filename, "b.png");
  assert.equal(await (await toBlob(own)).text(), "png");
});

test("inline content decodes", async () => {
  const file = await resolveFile(settings(), { content_base64: b64("hi"), filename: "a.txt" });
  assert.equal(file.size, 2);
  assert.equal(await (await toBlob(file)).text(), "hi");
});

for (const [args, message] of [
  [{}, /exactly one/],
  [{ path: "x", content_base64: b64("x"), filename: "a" }, /exactly one/],
  [{ content_base64: b64("x") }, /filename is required/],
  [{ content_base64: "not base64!", filename: "a.txt" }, /not valid base64/],
  [{ content_base64: "abc", filename: "a.txt" }, /not valid base64/],
  [{ path: "/definitely/missing.png" }, /No such file/],
] as const) {
  test(`bad file arguments explain themselves: ${message}`, async () => {
    await assert.rejects(resolveFile(settings(), args), (error: Error) => {
      assert.ok(error instanceof ToolError);
      assert.match(error.message, message);
      return true;
    });
  });
}

test("inline content has a size limit", async () => {
  const size = CONTRACT.limits.maxInlineBytes + 1;
  const content = Buffer.alloc(size).toString("base64");
  await assert.rejects(resolveFile(settings(), { content_base64: content, filename: "a" }), /limit/);
});

test("paths outside the roots are refused, including through .. and symlinks", async () => {
  const base = await tempDir();
  const allowed = join(base, "allowed");
  await mkdir(allowed);
  await writeFile(join(allowed, "ok.txt"), "ok");
  await writeFile(join(base, "secret.txt"), "secret");
  await mkdir(`${allowed}-sibling`);
  await writeFile(join(`${allowed}-sibling`, "x.txt"), "x");
  await symlink(join(base, "secret.txt"), join(allowed, "link.txt"));
  const rooted = settings({ fileRoots: [allowed] });
  assert.equal((await resolveFile(rooted, { path: join(allowed, "ok.txt") })).size, 2);
  for (const path of [
    join(base, "secret.txt"),
    join(allowed, "..", "secret.txt"),
    join(allowed, "link.txt"),
    join(`${allowed}-sibling`, "x.txt"),
  ]) {
    await assert.rejects(resolveFile(rooted, { path }), /outside the allowed file roots/);
  }
});

test("local paths are off over HTTP without roots", async () => {
  const path = join(await tempDir(), "a.txt");
  await writeFile(path, "a");
  const http = settings({ allowAnyLocalPath: false });
  await assert.rejects(resolveFile(http, { path }), /disabled on this transport/);
});

test("content types come from the filename, unless given", () => {
  assert.equal(contentTypeOf("a.png"), "image/png");
  assert.equal(contentTypeOf("a.unknownext"), "application/octet-stream");
  assert.equal(contentTypeOf("a.png", "image/webp"), "image/webp");
});

test("settings come from the environment", async () => {
  const root = await tempDir();
  assert.equal(settingsFromEnv({ [ENV.ALLOW_DELETE]: " TRUE " }).allowDelete, true);
  assert.equal(settingsFromEnv({ [ENV.ALLOW_DELETE]: "0" }).allowDelete, false);
  const defaults = settingsFromEnv({});
  assert.deepEqual(defaults, {
    allowDelete: false,
    fileRoots: [],
    allowAnyLocalPath: true,
    httpToken: undefined,
  });
  const http = settingsFromEnv(
    { [ENV.FILE_ROOTS]: `${root}:`, [ENV.HTTP_TOKEN]: "tok" },
    TRANSPORT.HTTP,
  );
  assert.deepEqual(http.fileRoots, [root]);
  assert.equal(http.httpToken, "tok");
  assert.equal(http.allowAnyLocalPath, false);
  assert.equal(expandHome("~/x"), join(homedir(), "x"));
  assert.equal(expandHome("/x"), "/x");
});
