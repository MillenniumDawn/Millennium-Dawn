import { spawnSync } from "node:child_process";
import { SITE_BASE_PATH } from "../src/shared/config/site";

const [scriptPath, ...scriptArgs] = process.argv.slice(2);

if (!scriptPath) {
  throw new Error("Missing python script path");
}

const result = spawnSync("python", [scriptPath, ...scriptArgs, "--baseurl", SITE_BASE_PATH], {
  stdio: "inherit",
});

if (result.error) {
  throw result.error;
}

process.exit(result.status ?? 1);
