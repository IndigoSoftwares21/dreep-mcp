#!/usr/bin/env node
import { launch, packageVersion } from "../lib/launch.js";

const code = await launch({ version: packageVersion(), args: process.argv.slice(2) });
process.exit(code);
