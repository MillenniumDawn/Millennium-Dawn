# Docs site — inventory: where to adopt Astro `Image` / optimized assets

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Document every place in the Millennium Dawn docs where plain `<img>` or non-optimized loading triggers Astro Dev Toolbar **Audit → Performance** (“Use the Image component”, “Unoptimized loading attribute”), and list concrete files/assets to migrate or fix.

**Architecture:** Treat three layers separately: (1) **raw HTML in Markdown** — bypasses `MarkdownImage` and always emits plain `<img>`; (2) **Markdown `![alt](url)`** — rendered by `MarkdownContent` → `MarkdownImage.astro`, which uses `ResponsiveImage` + `Picture` only when width/height resolve (`getInternalImageAsset` for `src/assets/images/**` or `getPublicImageDimensions` for `public/`); otherwise **fallback `<img>`**; (3) **Astro widgets** — some already use `astro:assets`. Runtime **lightbox** `<img>` is intentional and must stay dynamic.

**Tech stack:** Astro 6, `docs/src/shared/ui/MarkdownImage.astro`, `docs/src/shared/ui/ResponsiveImage.astro` (`Picture` from `astro:assets`), `docs/src/shared/lib/image-assets.ts` (glob `src/assets/images/**/*.{png,jpg,jpeg,webp,avif,gif,svg}`), `docs/public/` for static copies.

---

## File map (planning only)

| Area | Role |
|------|------|
| `docs/src/content/devDiaries/*.md` | Raw `<img>` — primary migration batch |
| `docs/src/content/tutorials/*.md`, `docs/src/content/resources/*.md` | Markdown images — verify `Picture` vs fallback |
| `docs/src/shared/ui/MarkdownImage.astro` | Central switch: dimensions → `ResponsiveImage`; else raw `img` |
| `docs/public/assets/images/...` | Public files; need dimensions at build for optimization |
| `docs/src/assets/images/...` | Preferred for `getInternalImageAsset` + `Picture` |
| `docs/src/features/image-lightbox/model/index.ts` | Dynamic `img` — **exclude** from static `Image` migration |
| `docs/src/widgets/site-shell/ui/Header.astro` | Already `Image` from `astro:assets` |
| `docs/src/widgets/home/ui/Hero.astro` | Already `getImage` / optimized hero |
| `docs/src/widgets/home/ui/HomeRoadmaps.astro` | Already `ResponsiveImage` |
| `docs/src/entities/country/ui/CountryInfobox.astro` | Flags via **CSS `background-image`** — not `<img>`; out of scope for “Use Image component” unless redesigning |

---

## Already aligned (no migration required for Audit “Image component”)

- **Header logo:** `docs/src/widgets/site-shell/ui/Header.astro` — `<Image />` from `astro:assets`.
- **Home hero:** `docs/src/widgets/home/ui/Hero.astro` — `getImage` + imported asset.
- **Home roadmaps:** `docs/src/widgets/home/ui/HomeRoadmaps.astro` — `ResponsiveImage` → `Picture`.
- **Country flags in infobox:** `CountryInfobox.astro` — background image, not an `<img>` node.

---

## Tier 1 — Raw `<img>` in Markdown (always plain HTML, never `MarkdownImage`)

These files embed HTML `<img ...>` directly. They **do not** go through `MarkdownImage.astro` and are the **clearest** candidates to replace with Markdown image syntax `![alt](/path)` **and/or** move assets under `src/assets/images` so `getInternalImageAsset` resolves and `ResponsiveImage` runs.

**Note:** In the repo snapshot, `docs/public/assets/images/dev-diaries/` contains files for **054** and **055** only; **053** references `image-0.png` … `image-13.png` — confirm those files exist in `public` or CI assets before changing paths.

### `docs/src/content/devDiaries/053-military-of-japan.md`

| # | `src` (as in file) |
|---|---------------------|
| 1 | `/assets/images/dev-diaries/053/image-0.png` |
| 2 | `/assets/images/dev-diaries/053/image-1.png` |
| 3 | `/assets/images/dev-diaries/053/image-2.png` |
| 4 | `/assets/images/dev-diaries/053/image-3.png` |
| 5 | `/assets/images/dev-diaries/053/image-4.png` |
| 6 | `/assets/images/dev-diaries/053/image-5.png` |
| 7 | `/assets/images/dev-diaries/053/image-6.png` |
| 8 | `/assets/images/dev-diaries/053/image-7.png` |
| 9 | `/assets/images/dev-diaries/053/image-8.png` |
| 10 | `/assets/images/dev-diaries/053/image-9.png` |
| 11 | `/assets/images/dev-diaries/053/image-10.png` |
| 12 | `/assets/images/dev-diaries/053/image-11.png` |
| 13 | `/assets/images/dev-diaries/053/image-12.png` |
| 14 | `/assets/images/dev-diaries/053/image-13.png` |

### `docs/src/content/devDiaries/054-performance-of-the-md-beta.md`

| # | `src` |
|---|--------|
| 1 | `/assets/images/dev-diaries/054/image-01.png` |
| 2 | `/assets/images/dev-diaries/054/image-02.png` |
| 3 | `/assets/images/dev-diaries/054/image-03.png` |

### `docs/src/content/devDiaries/055-algeria-le-pouvoir.md`

| # | `src` |
|---|--------|
| 1 | `/assets/images/dev-diaries/055/bop_overview.png` |
| 2 | `/assets/images/dev-diaries/055/bop_warning.png` |
| 3 | `/assets/images/dev-diaries/055/deep_state_variable.png` |
| 4 | `/assets/images/dev-diaries/055/cabinet_appointment.png` |
| 5 | `/assets/images/dev-diaries/055/cabinet.png` |

**Recommended migration for Tier 1:** Replace each `<img>` with `![alt text](same path)` so content flows through `MarkdownImage`, then either (a) move PNGs to `docs/src/assets/images/dev-diaries/...` (adjust paths to match `image-assets` keys) for guaranteed `Picture`, or (b) keep under `public/` and rely on `getPublicImageDimensions` returning width/height at build (if that fails, you still get raw `<img>`).

---

## Tier 2 — Markdown `![alt](url)` (verify optimization path)

| File | Image reference |
|------|-----------------|
| `docs/src/content/tutorials/eu-law-flowchart.md` | `![image](/assets/images/tutorials/eu-law-flowchart.png)` |
| `docs/src/content/resources/focus-tree-tool.md` | `![example1](/assets/images/tutorials/example1.jpg)` |

**Action:** After `bun run build`, inspect HTML for these pages: if output is `<picture>` / optimized URLs, Audit may still flag inner `<img>` depending on Astro version; if output is plain `<img>` without dimensions, extend `getPublicImageDimensions` coverage or move files to `src/assets/images/tutorials/...` and update paths.

---

## Tier 3 — Country `flag_image` (frontmatter)

All `docs/src/content/countries/*.md` entries with `flag_image: /assets/images/flags/...` feed **background-image** in `CountryInfobox.astro`, not `<img>`. They are **not** the direct cause of “Use the Image component” unless you add a visible `<img>` flag later. Optional future work: use `<Image>` for a real flag `<img>` with `alt` for accessibility; separate from current Audit rule.

---

## Tier 4 — Do **not** convert to static `<Image />`

| Location | Reason |
|----------|--------|
| `docs/src/features/image-lightbox/model/index.ts` | `src` is set at runtime; must remain a plain `<img>` (or a small wrapper), not a build-time Astro `Image` component. |

---

## “Unoptimized loading attribute” (same Audit app)

Rules are **viewport-based** in dev (above/below fold). Fixes:

- **Below fold:** ensure `loading="lazy"` (MarkdownImage default is `lazy` for `ResponsiveImage` and fallback `img`).
- **Above fold:** `loading="eager"` and optionally `fetchpriority="high"` for LCP candidates (e.g. hero — already tuned in Hero).
- Raw `<img>` in Tier 1 often omits `loading` — adding `loading="lazy"` in HTML or switching to `MarkdownImage` path reduces noise.

---

## Implementation tasks (optional execution)

### Task 1: Tier 1 — dev diary 053

**Files:**

- Modify: `docs/src/content/devDiaries/053-military-of-japan.md`
- Ensure: `docs/public/assets/images/dev-diaries/053/*.png` (or `src/assets/...`) exist for all 14 references

- [ ] **Step 1:** Replace raw `<img>` tags with `![alt](path)` lines preserving alt text and layout classes via surrounding HTML `<div class="...">` only if still needed, or use MDX if classes are required.
- [ ] **Step 2:** Run `cd docs && bun run build` and open dev diary page; confirm optimized markup or document intentional fallback.
- [ ] **Step 3:** Commit

```bash
git add docs/src/content/devDiaries/053-military-of-japan.md
git commit -m "docs(dev-diary-053): use markdown images for astro asset pipeline"
```

### Task 2: Tier 1 — dev diary 054

**Files:** `docs/src/content/devDiaries/054-performance-of-the-md-beta.md`

- [ ] Same pattern as Task 1 (3 images).

### Task 3: Tier 1 — dev diary 055

**Files:** `docs/src/content/devDiaries/055-algeria-le-pouvoir.md`

- [ ] Same pattern as Task 1 (5 images).

### Task 4: Tier 2 — tutorials / resources

**Files:**

- `docs/src/content/tutorials/eu-law-flowchart.md`
- `docs/src/content/resources/focus-tree-tool.md`

- [ ] **Step 1:** Confirm built HTML for these routes; if still plain `img`, move assets to `docs/src/assets/images/tutorials/` and update markdown paths to match `image-assets` normalization (`/assets/images/...`).

### Task 5: Verification

Run:

```bash
cd docs && bun run check && bun run build
```

- [ ] **Step 2:** `bun run dev` — open dev diary pages, tutorial page, resource page; Astro Audit: count remaining “Use the Image component” on content images.

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2025-03-27-docs-image-migration-inventory.md`.

**1. Subagent-Driven (recommended)** — @superpowers:subagent-driven-development  
**2. Inline Execution** — @superpowers:executing-plans  

Which approach?

**Spec:** Informal — follows Astro Audit rule sources (`perf-use-image-component`, `perf-use-loading-lazy` / `eager`) and repo grep as of plan date; re-run `rg '<img|!\\[' docs/src/content` after new content is added.
