import { SITE_FALLBACK_ORIGIN } from "../shared/config/site";

function normalizeBase(rawBase: string | undefined): string {
  if (!rawBase || rawBase === "/") return "";
  return rawBase.endsWith("/") ? rawBase.slice(0, -1) : rawBase;
}

function normalizeOrigin(rawSite: string | undefined): string {
  const site = rawSite ?? SITE_FALLBACK_ORIGIN;
  return site.endsWith("/") ? site.slice(0, -1) : site;
}

export const SITE_ORIGIN = normalizeOrigin(import.meta.env.SITE);
export const SITE_BASE = normalizeBase(import.meta.env.BASE_URL);

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

export function cssUrl(path: string): string {
  const normalized = withBase(path);
  const escaped = normalized.replace(/['"()\\]/g, "\\$&");
  return `url('${escaped}')`;
}

export function stripBase(pathname: string): string {
  if (!pathname) return "/";
  if (!SITE_BASE) return pathname;
  if (pathname === SITE_BASE) return "/";
  if (pathname.startsWith(`${SITE_BASE}/`)) {
    const sliced = pathname.slice(SITE_BASE.length);
    return sliced.startsWith("/") ? sliced : `/${sliced}`;
  }
  return pathname;
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
