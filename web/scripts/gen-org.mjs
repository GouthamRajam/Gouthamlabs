// Generates src/generated/org.json from config/management.yaml (the same file the backend
// loads), so the Live Office seats exactly the org the orchestrator knows. Runs before
// dev/build/typecheck.
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import yaml from "js-yaml";

const here = dirname(fileURLToPath(import.meta.url));
const cfgDir = process.env.S2S_CONFIG_DIR ?? resolve(here, "..", "..", "config");
const mgmt = yaml.load(readFileSync(join(cfgDir, "management.yaml"), "utf8"));
const out = resolve(here, "..", "src", "generated", "org.json");
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, JSON.stringify({ org: mgmt.org, sla: mgmt.sla, gates: mgmt.gates }, null, 2) + "\n");
console.log(`gen-org: ${mgmt.org.divisions.length} divisions -> ${out}`);
