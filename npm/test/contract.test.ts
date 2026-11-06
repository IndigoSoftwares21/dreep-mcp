import assert from "node:assert/strict";
import { test } from "node:test";

import { UNSUPPORTED_PARAMS } from "../src/constants.js";
import { CONTRACT, RAW_CONTRACT, VERSION } from "../src/contract.js";
import { connect } from "./support.js";

const DELETE_TOOLS = ["delete_media", "delete_preset"];

test("the server serves exactly the Python server's tools", async () => {
  const client = await connect({ allowDelete: true });
  const { tools } = await client.listTools();
  await client.close();
  assert.deepEqual(
    tools.map((tool) => tool.name),
    RAW_CONTRACT.tools.map((tool) => tool.name),
  );
  assert.equal(tools.length, 16);
  for (const tool of tools) {
    const expected = CONTRACT.tools.find((t) => t.name === tool.name);
    assert.equal(tool.description, expected?.description);
    assert.deepEqual(tool.annotations, expected?.annotations);
    assert.deepEqual(tool.inputSchema, expected?.inputSchema);
  }
});

test("delete tools are opt-in", async () => {
  const client = await connect();
  const { tools } = await client.listTools();
  const hidden = await client.callTool({ name: "delete_media", arguments: { media_id: "m" } });
  await client.close();
  assert.equal(tools.length, 14);
  assert.deepEqual(tools.filter((t) => DELETE_TOOLS.includes(t.name)), []);
  assert.equal(hidden.isError, true);
});

test("the only differences from the Python schemas are the declared ones", () => {
  for (const [tool, params] of Object.entries(UNSUPPORTED_PARAMS)) {
    const raw = RAW_CONTRACT.tools.find((t) => t.name === tool)?.inputSchema.properties;
    const served = CONTRACT.tools.find((t) => t.name === tool)?.inputSchema.properties;
    for (const param of params) {
      assert.ok(raw && param in raw, `${tool}.${param} is no longer in the contract`);
      assert.ok(served && !(param in served), `${tool}.${param} should not be served`);
    }
  }
});

test("the server identifies itself", async () => {
  const client = await connect();
  assert.equal(client.getServerVersion()?.name, "dreep");
  assert.equal(client.getServerVersion()?.version, VERSION);
  assert.equal(client.getInstructions(), CONTRACT.instructions);
  await client.close();
});
