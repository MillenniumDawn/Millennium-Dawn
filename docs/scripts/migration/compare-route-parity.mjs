import { promises as fs } from "node:fs";
import path from "node:path";

async function readJsonArray(filePath) {
  const text = await fs.readFile(filePath, "utf8");
  return JSON.parse(text);
}

function diff(expected, actual) {
  const expectedSet = new Set(expected);
  const actualSet = new Set(actual);
  const missing = expected.filter((item) => !actualSet.has(item));
  const unexpected = actual.filter((item) => !expectedSet.has(item));
  return { missing, unexpected };
}

async function main() {
  const baselinePath = path.resolve(process.cwd(), "docs/scripts/migration/jekyll-urls.json");
  const astroPath = path.resolve(process.cwd(), "docs/scripts/migration/astro-urls.json");

  const baseline = await readJsonArray(baselinePath);
  const astro = await readJsonArray(astroPath);
  const { missing, unexpected } = diff(baseline, astro);

  if (missing.length) {
    console.error("Route parity failed. Missing URLs:");
    for (const item of missing) console.error(`- ${item}`);
    if (unexpected.length) {
      console.warn("Unexpected URLs (non-blocking):");
      for (const item of unexpected) console.warn(`- ${item}`);
    }
    process.exit(1);
  }

  if (unexpected.length) {
    console.warn("Route parity OK for baseline URLs.");
    console.warn("Unexpected URLs (non-blocking):");
    for (const item of unexpected) console.warn(`- ${item}`);
  } else {
    console.log(`Route parity OK. ${baseline.length} URLs matched.`);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
