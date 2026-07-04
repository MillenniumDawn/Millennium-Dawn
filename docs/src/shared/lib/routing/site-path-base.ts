/**
 * Normalized site base path: `""` at site root, else no trailing slash (e.g. `/Millennium-Dawn`).
 * Shared by runtime URLs and Node-only markdown/rehype (must stay aligned with `astro.config` `base`).
 */
export function normalizeSiteBase(rawBase: string | undefined): string {
  if (!rawBase || rawBase === "/") return "";
  return rawBase.endsWith("/") ? rawBase.slice(0, -1) : rawBase;
}

/** Strip a normalized base prefix from a pathname (same rules as `stripBase` in `routing/urls.ts` and `stripPublicationBase` in `media/docs-content-paths`). */
export function stripPathBase(pathname: string, baseNormalized: string): string {
  if (!pathname) return "/";
  if (!baseNormalized) return pathname;
  if (pathname === baseNormalized) return "/";
  if (pathname.startsWith(`${baseNormalized}/`)) {
    const sliced = pathname.slice(baseNormalized.length);
    return sliced.startsWith("/") ? sliced : `/${sliced}`;
  }
  return pathname;
}
