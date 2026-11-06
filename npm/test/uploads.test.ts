import assert from "node:assert/strict";
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, test } from "node:test";

import { Dreep, DreepConflictError } from "dreep";

import { CONTRACT } from "../src/contract.js";
import { uploadPresigned } from "../src/presignedUpload.js";
import {
  API_KEY,
  ASSET_ID,
  ASSET_URL,
  assetPayload,
  callError,
  callOk,
  envelope,
  formField,
  restoreFetch,
  stubFetch,
} from "./support.js";

afterEach(restoreFetch);

const tempFile = async (name: string, content: string): Promise<string> => {
  const path = join(await mkdtemp(join(tmpdir(), "dreep-mcp-")), name);
  await writeFile(path, content);
  return path;
};

test("upload_file from a path returns a snake_case asset", async () => {
  const requests = stubFetch(envelope(assetPayload(), 201));
  const result = await callOk("upload_file", {
    path: await tempFile("hero.jpg", "jpeg-bytes"),
    folder: "marketing/2026",
    transform: { width: 800, trim_start: 2 },
  });
  assert.equal(result.id, ASSET_ID);
  assert.equal(result.url, ASSET_URL);
  assert.equal(result.size_bytes, 245000);
  assert.equal(result.original_filename, "hero.jpg");
  const body = requests[0]?.body;
  assert.equal(formField(body, "folder"), "marketing/2026");
  assert.equal(formField(body, "width"), "800");
  assert.equal(formField(body, "trimStart"), "2");
  const file = formField(body, "file") as File;
  assert.equal(file.name, "hero.jpg");
  assert.equal(file.type, "image/jpeg");
  assert.equal(await file.text(), "jpeg-bytes");
});

test("upload_file takes inline content, and an explicit content type wins", async () => {
  const requests = stubFetch(envelope(assetPayload(), 201));
  await callOk("upload_file", {
    content_base64: Buffer.from("hello").toString("base64"),
    filename: "a.txt",
    content_type: "text/markdown",
  });
  const file = formField(requests[0]?.body, "file") as File;
  assert.equal(file.name, "a.txt");
  assert.equal(file.type, "text/markdown");
});

test("API errors reach the agent", async () => {
  stubFetch(new Response(JSON.stringify({ message: "File too large", code: "LIMIT" }), { status: 413 }));
  const message = await callError("upload_file", {
    content_base64: "eA==",
    filename: "x.bin",
  });
  assert.match(message, /File too large/);
});

test("create_upload_url then confirm_upload", async () => {
  const requests = stubFetch(
    envelope({ id: "up_2", uploadUrl: "https://storage.example/put" }, 201),
    envelope(assetPayload()),
  );
  const presigned = await callOk("create_upload_url", {
    content_type: "video/mp4",
    size_bytes: 2048,
    filename: "clip.mp4",
  });
  assert.equal(presigned.upload_url, "https://storage.example/put");
  const asset = await callOk("confirm_upload", {
    upload_id: "up_2",
    transform: { format: "webm" },
  });
  assert.equal(asset.id, ASSET_ID);
  assert.match(requests[1]?.url.pathname ?? "", /\/upload\/up_2\/confirm$/);
});

test("confirm_upload refuses ids that would change the endpoint", async () => {
  stubFetch();
  assert.match(await callError("confirm_upload", { upload_id: "../usage" }), /Invalid id/);
});

test("upload_file sends files over the threshold through a presigned upload", async () => {
  const { limits } = CONTRACT;
  const threshold = limits.presignedThresholdBytes;
  limits.presignedThresholdBytes = 4;
  try {
    const requests = stubFetch(
      envelope({ id: "up_1", uploadUrl: "https://storage.example/put" }, 201),
      new Response(null, { status: 200 }),
      envelope(assetPayload()),
    );
    const asset = await callOk("upload_file", { path: await tempFile("clip.mp4", "0123456789") });
    assert.equal(asset.id, ASSET_ID);
    const presign = JSON.parse(requests[0]?.body as string);
    assert.equal(presign.sizeBytes, 10);
    assert.equal(presign.contentType, "video/mp4");
    assert.equal(requests[1]?.method, "PUT");
  } finally {
    limits.presignedThresholdBytes = threshold;
  }
});

const client = () => new Dreep({ apiKey: API_KEY });

test("uploadPresigned presigns, streams without the API key, and retries the confirm", async () => {
  const path = await tempFile("clip.mp4", "0123456789");
  const conflict = new Response(JSON.stringify({ message: "not yet" }), { status: 409 });
  const requests = stubFetch(
    envelope({ id: "up_1", uploadUrl: "https://storage.example/put" }, 201),
    new Response(null, { status: 200 }),
    conflict,
    envelope(assetPayload()),
  );
  const asset = await uploadPresigned(
    client(),
    { path, size: 10, contentType: "video/mp4", filename: "clip.mp4" },
    0,
  );
  assert.equal(asset.id, ASSET_ID);
  const put = requests[1];
  assert.equal(put?.method, "PUT");
  assert.equal(put?.headers.get("content-length"), "10");
  assert.equal(put?.headers.get("content-type"), "video/mp4");
  assert.equal(put?.headers.get("authorization"), null);
  assert.equal(requests.length, 4);
});

test("uploadPresigned skips the PUT when Dreep already has the content", async () => {
  const requests = stubFetch(
    envelope({ id: "up_1", alreadyExists: true }, 201),
    envelope(assetPayload()),
  );
  await uploadPresigned(client(), { path: "/unused", size: 1, contentType: "a/b" }, 0);
  assert.equal(requests.length, 2);
});

test("uploadPresigned reports a storage failure", async () => {
  const path = await tempFile("clip.mp4", "x");
  stubFetch(
    envelope({ id: "up_1", uploadUrl: "https://storage.example/put" }, 201),
    new Response(null, { status: 403 }),
  );
  await assert.rejects(
    uploadPresigned(client(), { path, size: 1, contentType: "a/b" }, 0),
    /status 403/,
  );
});

test("uploadPresigned gives up after repeated conflicts", async () => {
  const conflict = () => new Response(JSON.stringify({ message: "not yet" }), { status: 409 });
  stubFetch(
    envelope({ id: "up_1", alreadyExists: true }, 201),
    conflict(), conflict(), conflict(), conflict(), conflict(),
  );
  await assert.rejects(
    uploadPresigned(client(), { path: "/unused", size: 1, contentType: "a/b" }, 0),
    DreepConflictError,
  );
});
