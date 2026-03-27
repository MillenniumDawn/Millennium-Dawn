# Design: single-source docs images (remove public/src duplication)

## Goal

Eliminate legacy duplication where the same logical image exists under both `docs/public/assets/images/` and `docs/src/assets/images/`. After this work:

- **Canonical storage** for raster images used by the docs site is **`docs/src/assets/images/**`** only.
- **`docs/public/assets/images/`** is empty or absent except for documented exceptions (none for normal content images).
- **`docs/public/assets/downloads/`** and other non-image static files remain in `public/` as today.
- **`bun run ci`** (including `check:links` and `check_docs_hygiene.py`) passes.

## Non-goals

- Changing Open Graph route generation (`/open-graph/...png`) beyond what is required for consistency.
- Adding every missing country flag asset in one pass (separate content task); this spec only defines **how** flags are referenced once assets exist.
- Lightbox runtime behavior (stays dynamic per existing inventory).

## Current constraints (why duplication existed)

1. **`MarkdownImage.astro`** uses `getInternalImageAsset` (src glob) or `getPublicImageDimensions` (public disk). When dimensions resolve, **`ResponsiveImage`** / `Picture` emit optimized URLs (typically under `/_astro/`). When they do not, output is a plain **`<img src={withBase(original path)}>`**, which requires the file at **`dist/assets/images/...`** — today satisfied by copying **`public/`** into `dist`.

2. **`HeadSeo.astro`** imports PNG favicon from `@/assets/images` but hardcodes **`<link rel="alternate icon" ... href={withBase("/assets/images/favicon.ico")}>`**, which requires **`public/.../favicon.ico`** in `dist`.

3. **`CountryInfobox.astro`** uses inline **`background-image: url(...)`** with `flag_image` from frontmatter (root-relative `/assets/images/flags/...`). That URL must exist in `dist` at the same path unless refactored.

## Target architecture

### Authoring

- Content keeps **stable logical paths** in Markdown/YAML: `/assets/images/...` (no `/Millennium-Dawn` prefix in source).
- All such paths resolve to files under **`src/assets/images/`** (same relative path after `/assets/images/`).

### Runtime / build output

- **Markdown images:** Prefer **`ResponsiveImage`** path for all tracked rasters under `src/assets/images` covered by `image-assets.ts` glob. Ensures build emits **hashed optimized assets** and HTML does not depend on `dist/assets/images/...` for those images.
- **Favicon:** Drop the hardcoded `/assets/images/favicon.ico` link **or** replace it with a **build-time resolved** URL (e.g. `import faviconIco from "@/assets/images/favicon.ico"` and `faviconIco.src`), so **`public/` is not required** for `.ico`.
- **Country flags:** Replace CSS-only `background-image` + raw URL with one of:
  - **Recommended:** real **`<Image>`** (or shared wrapper) with `alt` derived from country title for accessibility, using `getImage` / internal asset map from `flag_image` path; decorative mask styling can remain on a wrapper if needed, **or**
  - **Acceptable interim:** inject **`url()`** from a **build-time resolved** asset URL (import or `getImage`) so the emitted CSS/HTML never points at a bare `/assets/images/...` that must be copied from `public/`.

### `public/assets/images`

- **Remove** entire tree after migrations; add **`public/assets/images/.gitkeep`** only if an empty directory is required (prefer deleting the directory).

### Tooling

- **`check_docs_hygiene.py`:** Keep scanning `public/assets/images` and `src/assets/images`; after cleanup, **no tracked files** under `public/assets/images` except optional `.gitkeep`.
- **`check_site_links.py`:** No change required if HTML no longer references missing static paths; if any stable paths remain by design, they must exist in `dist` (via build output, not ghost `public/`).

## Phased rollout (recommended)

1. **Flags + favicon** — remove hard dependencies on `public/` for `HeadSeo` and `CountryInfobox`.
2. **Inventory `public/assets/images`** — for each file, ensure equivalent under `src/assets/images/` (git mv if missing in src), then **delete public copy**.
3. **Verify markdown / YAML** — any image still falling back to plain `<img>` without dimensions: either add to `src` glob coverage or pass dimensions explicitly.
4. **Docs** — update `CONTRIBUTING.md` to state: images live only in `src/assets/images`; `public` is not used for `/assets/images/` mirrors.

## Testing

- From repo root: `python3 docs/scripts/check_docs_hygiene.py --repo-root . --docs-dir docs`
- From `docs/`: `bun run ci`
- Manual spot-check: country page with flag, dev diary with images, home roadmaps, favicon in browser devtools.

## Risks

- **Large repo churn** (binary moves + deletes); use clear commits per area (favicon, flags, bulk public removal).
- **Missing flag files** for some countries: link checker does not validate `background-image`; after switching to `<Image>`, broken imports may fail **build** — fix by adding PNGs or adjusting frontmatter.

## Open decisions (implementation plan will resolve)

- Exact markup for flag (full-bleed background vs contained `<Image>`) subject to design/accessibility review.
- Whether to keep `.ico` at all or ship PNG/WebP icons only.

---

**Status:** Approved direction — canonical `src`, eliminate duplicate `public` images, refactor favicon link and country flags so output does not rely on copied static paths.
