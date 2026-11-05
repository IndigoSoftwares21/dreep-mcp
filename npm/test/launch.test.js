import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { test } from "node:test";

import { candidates, launch, packageVersion } from "../lib/launch.js";

// A fake spawn: each command either fails to start with `code` or exits with `exit`.
function fakeSpawn(outcomes, calls) {
  return (command, args) => {
    calls.push([command, ...args]);
    const child = new EventEmitter();
    const outcome = outcomes[command] ?? { errorCode: "ENOENT" };
    queueMicrotask(() => {
      if (outcome.errorCode) {
        const error = new Error(`${command}: ${outcome.errorCode}`);
        error.code = outcome.errorCode;
        child.emit("error", error);
      } else {
        child.emit("exit", outcome.exit, null);
      }
    });
    return child;
  };
}

const sink = () => {
  const chunks = [];
  return { chunks, write: (text) => chunks.push(text) };
};

test("pins the PyPI version and forwards arguments", () => {
  const [uvx, pipx] = candidates("1.2.3", ["--transport", "http"]);
  assert.deepEqual(uvx.args, ["--from", "dreep-mcp==1.2.3", "dreep-mcp", "--transport", "http"]);
  assert.equal(pipx.command, "pipx");
  assert.ok(pipx.args.includes("dreep-mcp==1.2.3"));
});

test("version comes from package.json", () => {
  assert.match(packageVersion(), /^\d+\.\d+\.\d+/);
});

test("prefers uvx and returns its exit code", async () => {
  const calls = [];
  const code = await launch({ version: "1.0.0", args: [], spawn: fakeSpawn({ uvx: { exit: 0 } }, calls) });
  assert.equal(code, 0);
  assert.equal(calls.length, 1);
});

test("falls back to pipx when uvx is missing", async () => {
  const calls = [];
  const code = await launch({ version: "1.0.0", args: [], spawn: fakeSpawn({ pipx: { exit: 3 } }, calls) });
  assert.equal(code, 3);
  assert.deepEqual(calls.map((c) => c[0]), ["uvx", "pipx"]);
});

test("explains how to install uv when nothing can run it", async () => {
  const stderr = sink();
  const code = await launch({ version: "1.0.0", args: [], spawn: fakeSpawn({}, []), stderr });
  assert.equal(code, 1);
  assert.match(stderr.chunks.join(""), /needs uv/);
});

test("reports other start failures instead of falling through", async () => {
  const stderr = sink();
  const spawn = fakeSpawn({ uvx: { errorCode: "EACCES" } }, []);
  assert.equal(await launch({ version: "1.0.0", args: [], spawn, stderr }), 1);
  assert.match(stderr.chunks.join(""), /Failed to start uvx/);
});
