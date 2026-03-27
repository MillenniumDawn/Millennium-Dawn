import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { SITE_BASE_PATH } from "../config/site";
import { isContainedInRoot } from "./fs-path-safety";
import { normalizeSiteBase, stripPathBase } from "./site-path-base";

const PUBLICATION_BASE = normalizeSiteBase(SITE_BASE_PATH);

let cachedPackageRoot: string | null = null;

/**
 * Directory that contains `astro.config.*` and `public/` for this docs package.
 * Matches logic in `public-image-size` (cwd vs monorepo root vs bundled fallback).
 */
export function getDocsPackageRoot(): string {
  if (cachedPackageRoot) return cachedPackageRoot;

  const cwd = process.cwd();
  if (existsSync(resolve(cwd, "astro.config.ts")) || existsSync(resolve(cwd, "astro.config.mjs"))) {
    cachedPackageRoot = cwd;
    return cachedPackageRoot;
  }

  const docsNested = resolve(cwd, "docs");
  if (
    existsSync(resolve(docsNested, "astro.config.ts")) ||
    existsSync(resolve(docsNested, "astro.config.mjs"))
  ) {
    cachedPackageRoot = docsNested;
    return cachedPackageRoot;
  }

  if (existsSync(resolve(cwd, "docs", "public"))) {
    cachedPackageRoot = resolve(cwd, "docs");
    return cachedPackageRoot;
  }

  const fromSourceTree = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
  if (existsSync(resolve(fromSourceTree, "astro.config.ts"))) {
    cachedPackageRoot = fromSourceTree;
    return cachedPackageRoot;
  }

  cachedPackageRoot = cwd;
  return cachedPackageRoot;
}

export function getDocsPublicRoot(): string {
  return resolve(getDocsPackageRoot(), "public");
}

export function getDocsSrcAssetsImagesRoot(): string {
  return resolve(getDocsPackageRoot(), "src", "assets", "images");
}

/** Strip `SITE_BASE_PATH` from URLs; same semantics as `stripBase` in `urls.ts` (via `stripPathBase`). */
export function stripPublicationBase(pathname: string): string {
  return stripPathBase(pathname, PUBLICATION_BASE);
}

const REMOTE_SCHEME = /^[a-zA-Z][a-zA-Z0-9+.-]*:/;

/**
 * Resolves a raster image file on disk for a root-relative or base-prefixed URL used in markdown.
 * Tries `public/` first, then `src/assets/images/`.
 */
export function resolveLocalRasterImageFile(srcAttr: string): string | null {
  if (!srcAttr || typeof srcAttr !== "string") return null;
  if (REMOTE_SCHEME.test(srcAttr) || srcAttr.startsWith("//")) return null;

  const normalized = stripPublicationBase(srcAttr);
  if (!normalized.startsWith("/") || normalized.startsWith("//")) return null;

  const segments = normalized.replace(/^\/+/, "").split("/").filter(Boolean);
  if (segments.some((s) => s === "..")) return null;

  const publicRoot = getDocsPublicRoot();
  const underPublic = resolve(publicRoot, ...segments);
  if (isContainedInRoot(publicRoot, underPublic) && existsSync(underPublic)) {
    return underPublic;
  }

  if (segments[0] === "assets" && segments[1] === "images") {
    const imagesRoot = getDocsSrcAssetsImagesRoot();
    const underSrc = resolve(imagesRoot, ...segments.slice(2));
    if (isContainedInRoot(imagesRoot, underSrc) && existsSync(underSrc)) {
      return underSrc;
    }
  }

  return null;
}
