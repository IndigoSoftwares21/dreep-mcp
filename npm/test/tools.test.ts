import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, test } from "node:test";

import {
  ASSET_ID,
  ASSET_URL,
  callError,
  callOk,
  callTool,
  envelope,
  formField,
  restoreFetch,
  SIGNING_SECRET,
  stubFetch,
} from "./support.js";

afterEach(restoreFetch);

const scan = async (): Promise<string> => {
  const path = join(await mkdtemp(join(tmpdir(), "dreep-mcp-")), "scan.pdf");
  await writeFile(path, "%PDF-1.7");
  return path;
};

test("list_media passes filters and matches the Python result shape", async () => {
  const requests = stubFetch(
    envelope({
      assets: [{ id: ASSET_ID, url: ASSET_URL, type: "image/webp", sizeBytes: "5" }],
      pagination: { page: 2, limit: 10, total: 11 },
    }),
  );
  const result = await callOk("list_media", { page: 2, limit: 10, folder: "avatars" });
  assert.deepEqual(result.pagination, { page: 2, limit: 10, total: 11 });
  assert.equal(result.assets[0].mimetype, "image/webp");
  assert.equal(result.assets[0].type, undefined);
  assert.equal(requests[0]?.url.searchParams.get("folder"), "avatars");
});

test("delete_media reports what went, and refuses unsafe ids", async () => {
  const requests = stubFetch(new Response(null, { status: 204 }));
  const result = await callOk("delete_media", { media_id: "m1" }, { allowDelete: true });
  assert.deepEqual(result, { id: "m1", deleted: true });
  assert.equal(requests[0]?.method, "DELETE");
  for (const id of ["../usage", "a/b", "x?y", "..", ""]) {
    const message = await callError("delete_media", { media_id: id }, { allowDelete: true });
    assert.match(message, /Invalid id/);
  }
  assert.equal(requests.length, 1);
});

test("remove_background sends the file with its type and destination", async () => {
  const requests = stubFetch(envelope({ asset: { id: "bg1", url: "https://cdn.example/bg1.png" } }));
  const result = await callOk("remove_background", { path: await scan(), folder: "cutouts" });
  assert.equal(result.id, "bg1");
  assert.match(requests[0]?.url.pathname ?? "", /\/bg-remove$/);
  assert.equal(formField(requests[0]?.body, "folder"), "cutouts");
});

test("extract_text returns the text", async () => {
  stubFetch(envelope({ text: "INVOICE 42", blocks: [], savedAsset: null }));
  const result = await callOk("extract_text", { path: await scan() });
  assert.equal(result.text, "INVOICE 42");
  assert.equal(result.saved_asset, null);
});

test("convert_document sends the format", async () => {
  const requests = stubFetch(
    envelope({ asset: { id: "d1", url: "https://cdn.example/d1.docx", status: "ready" } }, 201),
  );
  const result = await callOk("convert_document", { path: await scan(), format: "docx" });
  assert.equal(result.status, "ready");
  assert.equal(formField(requests[0]?.body, "format"), "docx");
});

test("the schema rejects an unknown format before anything is sent", async () => {
  const requests = stubFetch();
  const message = await callError("convert_document", { path: await scan(), format: "exe" });
  assert.match(message, /Invalid arguments/);
  assert.equal(requests.length, 0);
});

test("null means not given", async () => {
  stubFetch(envelope({ text: "x", blocks: [], savedAsset: null }));
  const result = await callOk("extract_text", { path: await scan(), folder: null });
  assert.equal(result.text, "x");
});

test("build_delivery_url applies a sorted transform and keeps custom CDN domains", async () => {
  const result = await callOk("build_delivery_url", {
    url: ASSET_URL,
    transform: { width: 400, format: "webp", fit: "cover" },
  });
  assert.equal(result.url, `${ASSET_URL}?fit=cover&format=webp&width=400`);
  const custom = "https://cdn.getscale.ng/api/v1/fetch/abc.jpg";
  assert.equal((await callOk("build_delivery_url", { url: custom })).url, custom);
});

test("URL tools reject anything but absolute http(s) URLs", async () => {
  for (const url of ["/a.jpg", "ftp://cdn.example/a.jpg"]) {
    assert.match(await callError("build_delivery_url", { url }), /absolute/);
  }
});

test("build_signed_url signs the id and expiry only, as the API verifies", async () => {
  const result = await callOk("build_signed_url", {
    asset_id: ASSET_ID,
    url: ASSET_URL,
    expires_in_seconds: 300,
    transform: { width: 200, format: "webp" },
  });
  const query = new URL(result.url as string).searchParams;
  const expected = createHmac("sha256", SIGNING_SECRET)
    .update(`${ASSET_ID}:${query.get("exp")}`)
    .digest("hex");
  assert.equal(query.get("sig"), expected);
  assert.equal(query.get("width"), "200");
  assert.equal(query.get("format"), "webp");
});

test("create_folder maps its arguments", async () => {
  const requests = stubFetch(
    envelope({ id: "f1", name: "Private", accessControlType: "signed" }, 201),
  );
  const result = await callOk("create_folder", {
    name: "Private",
    access_control_type: "signed",
    default_expiry_seconds: 600,
  });
  assert.equal(result.access_control_type, "signed");
  const body = JSON.parse(requests[0]?.body as string);
  assert.equal(body.accessControlType, "signed");
  assert.equal(body.defaultExpirySeconds, 600);
});

test("list_folders asks for the root with root_only, and rejects combining filters", async () => {
  const requests = stubFetch(envelope({ folders: [{ id: "f1", path: "avatars" }] }));
  const result = await callOk("list_folders", { root_only: true });
  assert.equal(result.folders[0].path, "avatars");
  assert.equal(requests[0]?.url.searchParams.get("parentId"), "null");
  const message = await callError("list_folders", { root_only: true, path: "avatars" });
  assert.match(message, /root_only/);
});

const PRESET = { id: "p1", key: "thumb", name: "Thumb", params: { trimStart: 1, format: "webp" } };

test("create_preset requires a format and a valid key", async () => {
  const requests = stubFetch();
  const noFormat = await callError("create_preset", {
    key: "thumb",
    name: "Thumb",
    transform: { width: 1 },
  });
  assert.match(noFormat, /format/);
  const badKey = await callTool("create_preset", {
    key: "Thumb-1",
    name: "Thumb",
    transform: { format: "webp" },
  });
  assert.equal(badKey.isError, true);
  assert.equal(requests.length, 0);
});

test("presets round-trip, with their stored params left as they are", async () => {
  stubFetch(envelope(PRESET, 201), envelope({ presets: [PRESET] }));
  const created = await callOk("create_preset", {
    key: "thumb",
    name: "Thumb",
    transform: { format: "webp" },
  });
  assert.equal(created.key, "thumb");
  const listed = await callOk("list_presets", {});
  assert.deepEqual(listed.presets[0].params, PRESET.params);
});

test("list_presets accepts a plain array too", async () => {
  stubFetch(envelope([PRESET]));
  const listed = await callOk("list_presets", {});
  assert.equal(listed.presets[0].key, "thumb");
});

test("a response the SDK can't unwrap becomes a clear error", async () => {
  stubFetch(envelope({ unexpected: true }));
  const message = await callError("remove_background", { path: await scan() });
  assert.match(message, /unexpected response/);
});

test("get_usage normalises numbers to snake_case", async () => {
  stubFetch(envelope({ storageBytes: "1048576", imageCount: 3 }));
  const result = await callOk("get_usage", {});
  assert.equal(result.storage_bytes, 1048576);
  assert.equal(result.image_count, 3);
});

test("delete_preset reports what went", async () => {
  stubFetch(new Response(null, { status: 204 }));
  const result = await callOk("delete_preset", { preset_id: "p1" }, { allowDelete: true });
  assert.deepEqual(result, { id: "p1", deleted: true });
});
