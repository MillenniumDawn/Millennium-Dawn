import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { load } from "js-yaml";
import { SITE_BASE_PATH, SITE_FALLBACK_ORIGIN } from "../shared/config/site";

const docsRoot = fileURLToPath(new URL("../..", import.meta.url));
const contentRoot = path.join(docsRoot, "src/content");

interface Frontmatter {
  permalink?: string;
  seo?: boolean;
  hidden?: boolean;
  robots?: string;
  slug?: string;
}

function readFrontmatter(filePath: string): Frontmatter | null {
  const raw = readFileSync(filePath, "utf8");
  const match = /^---\r?\n([\s\S]*?)\r?\n---/.exec(raw);
  if (!match) return null;
  const parsed = load(match[1]);
  if (typeof parsed !== "object" || parsed === null) return null;

  const data = parsed as Record<string, unknown>;
  return {
    permalink: typeof data.permalink === "string" ? data.permalink : undefined,
    seo: typeof data.seo === "boolean" ? data.seo : undefined,
    hidden: typeof data.hidden === "boolean" ? data.hidden : undefined,
    robots: typeof data.robots === "string" ? data.robots : undefined,
    slug: typeof data.slug === "string" ? data.slug : undefined,
  };
}

function listMarkdownFiles(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true })
    .filter((entry) => entry.isFile() && /\.(md|mdx)$/i.test(entry.name))
    .map((entry) => path.join(dir, entry.name));
}

function toAbsoluteUrl(canonicalPath: string): string {
  const base = SITE_BASE_PATH.replace(/\/$/, "");
  const normalized = canonicalPath.startsWith("/") ? canonicalPath : `/${canonicalPath}`;
  const withSlash = normalized.endsWith("/") ? normalized : `${normalized}/`;
  return `${SITE_FALLBACK_ORIGIN}${base}${withSlash}`;
}

function shouldExcludeFromSitemap(data: Frontmatter): boolean {
  if (data.seo === false) return true;
  if (data.hidden === true) return true;
  if (data.robots?.includes("noindex")) return true;
  return false;
}

function collectFromDir(relativeDir: string, resolvePath: (id: string, data: Frontmatter) => string): string[] {
  const dir = path.join(contentRoot, relativeDir);
  const excluded: string[] = [];

  for (const filePath of listMarkdownFiles(dir)) {
    const data = readFrontmatter(filePath);
    if (!data || !shouldExcludeFromSitemap(data)) continue;
    const id = path.basename(filePath).replace(/\.(md|mdx)$/i, "");
    excluded.push(toAbsoluteUrl(resolvePath(id, data)));
  }

  return excluded;
}

/** Absolute URLs excluded from `sitemap-index.xml` (redirect stubs, noindex, hidden). */
export function getSitemapExcludedUrls(): Set<string> {
  const excluded = new Set<string>([toAbsoluteUrl("/404.html")]);

  for (const filePath of listMarkdownFiles(path.join(contentRoot, "redirects"))) {
    const data = readFrontmatter(filePath);
    if (data?.permalink) excluded.add(toAbsoluteUrl(data.permalink));
  }

  const pathResolvers: [string, (id: string, data: Frontmatter) => string][] = [
    ["changelogSections", (id) => `/changelogs/${id}/`],
    ["devDiaries", (id, data) => data.permalink ?? `/dev-diaries/${id}/`],
    ["tutorials", (id) => `/player-tutorials/${id}/`],
    ["resources", (id) => `/dev-resources/${id}/`],
    ["misc", (id) => `/misc/${id}/`],
    ["countries", (id, data) => `/countries/${data.slug ?? id}/`],
    ["pages", (id, data) => data.permalink ?? `/${id}/`],
  ];

  for (const [relativeDir, resolvePath] of pathResolvers) {
    for (const url of collectFromDir(relativeDir, resolvePath)) {
      excluded.add(url);
    }
  }

  return excluded;
}
