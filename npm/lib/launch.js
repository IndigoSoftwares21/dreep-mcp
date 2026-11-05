// Runs the Python dreep-mcp server, pinned to this package's version.
// One implementation lives on PyPI; this package only finds a way to start it.
import { spawn as nodeSpawn } from "node:child_process";
import { readFileSync } from "node:fs";

const PYPI_PACKAGE = "dreep-mcp";
const ENOENT = "ENOENT";
const INSTALL_HINT =
  "dreep-mcp needs uv (https://docs.astral.sh/uv/) or pipx to run.\n" +
  "Install uv with: curl -LsSf https://astral.sh/uv/install.sh | sh\n" +
  "Or skip npm entirely: pip install dreep-mcp && dreep-mcp\n";

export function packageVersion() {
  const manifest = new URL("../package.json", import.meta.url);
  return JSON.parse(readFileSync(manifest, "utf8")).version;
}

// Launchers in order of preference. Each runs the exact matching PyPI version.
export function candidates(version, args) {
  const spec = `${PYPI_PACKAGE}==${version}`;
  return [
    { command: "uvx", args: ["--from", spec, PYPI_PACKAGE, ...args] },
    { command: "pipx", args: ["run", "--spec", spec, PYPI_PACKAGE, ...args] },
  ];
}

// Tries each launcher until one starts; resolves with the server's exit code.
export function launch({ version, args, spawn = nodeSpawn, stderr = process.stderr }) {
  const queue = candidates(version, args);
  return new Promise((resolve) => {
    const next = () => {
      const launcher = queue.shift();
      if (!launcher) {
        stderr.write(INSTALL_HINT);
        resolve(1);
        return;
      }
      const child = spawn(launcher.command, launcher.args, { stdio: "inherit" });
      child.once("error", (error) => {
        if (error.code === ENOENT) {
          next();
        } else {
          stderr.write(`Failed to start ${launcher.command}: ${error.message}\n`);
          resolve(1);
        }
      });
      child.once("exit", (code, signal) => resolve(signal ? 1 : (code ?? 0)));
    };
    next();
  });
}
