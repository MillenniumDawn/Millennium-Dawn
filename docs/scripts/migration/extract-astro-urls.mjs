import { promises as fs } from "node:fs";
import path from "node:path";

async function walk(dir, out = []) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      await walk(full, out);
      continue;
    }
    if (entry.isFile() && entry.name.endsWith(".html")) out.push(full);
  }
  return out;
}

function toUrl(siteDir, filePath) {
  const rel = path.relative(siteDir, filePath).replaceAll("\\", "/");
  if (rel === "404.html") return "/404.html";
  if (rel.endsWith("/index.html")) return `/${rel.slice(0, -"index.html".length)}`;
  if (rel === "index.html") return "/";
  return `/${rel}`;
}

async function main() {
  const siteDir = path.resolve(process.cwd(), "docs/dist");
  const outFile = path.resolve(process.cwd(), "docs/scripts/migration/astro-urls.json");
  const htmlFiles = await walk(siteDir);
  const urls = htmlFiles.map((file) => toUrl(siteDir, file)).sort();
  await fs.writeFile(outFile, JSON.stringify(urls, null, 2) + "\n", "utf8");
  console.log(`Saved ${urls.length} URLs to ${outFile}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
