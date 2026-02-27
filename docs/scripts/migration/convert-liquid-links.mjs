import { promises as fs } from "node:fs";
import path from "node:path";

const ROOT = path.resolve(process.cwd(), "docs/src/content");
const RELATIVE_RE = /\{\{\s*['"]([^'"]+)['"]\s*\|\s*relative_url\s*\}\}/g;
const ABSOLUTE_RE = /\{\{\s*['"]([^'"]+)['"]\s*\|\s*absolute_url\s*\}\}/g;

async function walk(dir, out = []) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      await walk(full, out);
      continue;
    }
    if (entry.isFile() && entry.name.endsWith(".md")) out.push(full);
  }
  return out;
}

async function main() {
  const files = await walk(ROOT);
  let changed = 0;

  for (const file of files) {
    const before = await fs.readFile(file, "utf8");
    let after = before.replace(RELATIVE_RE, "$1");
    after = after.replace(ABSOLUTE_RE, (_m, p1) => `https://millenniumdawn.github.io/Millennium-Dawn${p1}`);
    if (after !== before) {
      await fs.writeFile(file, after, "utf8");
      changed++;
    }
  }

  console.log(`Converted Liquid links in ${changed} file(s).`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
