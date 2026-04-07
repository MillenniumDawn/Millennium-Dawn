import type { ImageMetadata } from "astro";
import { getRootRelativeUrlForMetadata, resolveImageSource } from "@/shared/lib/media/image-assets";
import { SITE_FALLBACK_ORIGIN } from "@/shared/config/site";
import { normalizeSiteBase, stripPathBase } from "./site-path-base";

function normalizeOrigin(rawSite: string | undefined): string {
  const site = rawSite ?? SITE_FALLBACK_ORIGIN;
  return site.endsWith("/") ? site.slice(0, -1) : site;
}

export const SITE_ORIGIN = normalizeOrigin(import.meta.env.SITE);
export const SITE_BASE = normalizeSiteBase(import.meta.env.BASE_URL);

const ABSOLUTE_SCHEME = /^[a-zA-Z][a-zA-Z0-9+.-]*:/;

export function withBase(path: string): string {
  if (!path) return SITE_BASE ? `${SITE_BASE}/` : "/";
  if (path.startsWith("#")) return path;
  if (ABSOLUTE_SCHEME.test(path)) return path;
  if (path.startsWith("//")) return path;
  if (!path.startsWith("/")) return path;
  if (SITE_BASE && (path === SITE_BASE || path.startsWith(`${SITE_BASE}/`))) return path;
  if (path === "/") return SITE_BASE ? `${SITE_BASE}/` : "/";
  return SITE_BASE ? `${SITE_BASE}${path}` : path;
}

export function cssUrl(path: string | ImageMetadata): string {
  const resolved = resolveImageSource(path);
  let normalized: string;
  if (typeof resolved === "string") {
    normalized = withBase(resolved);
  } else {
    const staticDocsPath = getRootRelativeUrlForMetadata(resolved);
    normalized =
      staticDocsPath?.startsWith("/assets/images/")
        ? withBase(staticDocsPath)
        : withBase(resolved.src);
  }
  const escaped = normalized.replace(/['"()\\]/g, "\\$&");
  return `url('${escaped}')`;
}

export function stripBase(pathname: string): string {
  return stripPathBase(pathname, SITE_BASE);
}

export function ensureTrailingSlash(pathname: string): string {
  if (!pathname) return "/";
  if (pathname === "/") return "/";
  if (pathname.endsWith(".html")) return pathname;
  return pathname.endsWith("/") ? pathname : `${pathname}/`;
}

export function toAbsolute(pathname: string): string {
  if (!pathname) return new URL(withBase("/"), `${SITE_ORIGIN}/`).toString();
  if (ABSOLUTE_SCHEME.test(pathname)) return pathname;
  return new URL(withBase(pathname), `${SITE_ORIGIN}/`).toString();
}
