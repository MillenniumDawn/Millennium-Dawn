# Contributing to Millennium Dawn Docs (Astro)

## Prerequisites

- Node.js 24 LTS or newer ([nodejs.org](https://nodejs.org/))
- [Bun](https://bun.com/) — see **Bun version** below.
- Python 3 (for `check:links`, `check:og`, `check:a11y`, `check:perf`)

### Bun version

The supported Bun release for this package is pinned in `package.json` as `packageManager` (for example `bun@1.3.11`). Treat that value as the canonical toolchain version: CI and other contributors use it, and Bun’s resolver and lockfile behavior can differ between releases, so drifting too far can cause “works on my machine” install or script failures. **Upgrade Bun on your machine from time to time** (security fixes and compatibility with newer tooling), and when this repo bumps the `packageManager` entry or refreshes `bun.lock`, align your local Bun to that version before working on docs.

## Quick Start

```bash
cd docs
bun install
bun run dev
```

Open the local site using the URL shown in the `astro dev` output.

## Where to Edit Content

- Regular pages: `src/content/pages/*.md`
- Countries: `src/content/countries/*.md`
- Changelogs: `src/content/changelogSections/*.md`
- Tutorials: `src/content/tutorials/*.md`
- Resources: `src/content/resources/*.md`
- Dev diaries: `src/content/devDiaries/*.{md,mdx}` (MDX recommended so markdown images use `MarkdownImage` / `Picture`; plain `.md` compiles to HTML only)
- Misc: `src/content/misc/*.md`

## Important Rules

- If you change any Markdown under `src/content/**/*.md`, run **`bun run lint:md`** (and preferably **`bun run lint:remark`**) **before you commit**. The same checks run in CI; fixing MD/style issues locally avoids broken builds and noisy follow-up commits.
- Use only Markdown + frontmatter.
- Do not use Liquid (`{% ... %}` / `{{ ... }}`).
- Use root-relative paths for internal links: `/tutorials/`, `/countries/germany/`.
- Do not manually add the `/Millennium-Dawn` prefix.

## Images and static files

Raster images for the docs site are stored **only** under **`docs/src/assets/images/`**. In Markdown and YAML, keep using root-relative paths such as `/assets/images/flags/germany.png`; the build resolves them through the Astro asset pipeline (`getInternalImageAsset`, `Picture` / `getImage`) so optimized output does not rely on a duplicate tree under `public/`.

**`public/`** is for assets that are not part of that pipeline — for example **`public/assets/downloads/...`** (zip archives). Do not add new tracked files under `docs/public/assets/images/`; that directory should stay empty in git.

After `astro build`, the integration in `src/integrations/copy-src-images-to-dist.ts` copies `src/assets/images/**` into `dist/assets/images/**` so any HTML that still uses root-relative `/assets/images/...` (for example markdown `<img>` fallbacks) resolves in `check:links` and on static hosting. Treat **`dist/assets/images` as owned by that step**: it is wiped and repopulated each build, so nothing else should write there.

CI runs `python3 docs/scripts/check_docs_hygiene.py` (from the repo root) against `docs/public/assets/images/`, `docs/public/assets/downloads/`, and `docs/src/assets/images/`. It fails if a tracked asset is never referenced from other docs sources using `/assets/images/...`, `@/assets/images/...`, or a `src/assets/images/...` path string. Remove unused files or add an explicit entry to `ALLOW_UNUSED_ASSETS` in that script only when keeping an unreferenced file is intentional.

## Frontmatter Template (Regular Page)

```md
---
# Required: page title
title: "Page title"

# Recommended: description for SEO and social cards
description: "Short page description"

# Optional: canonical URL
permalink: "/player-tutorials/new-guide/"

# Optional: table of contents mode
# Allowed values: "auto" or "off"
toc: "auto"

# Optional: SEO/robots
seo: true
# robots: "noindex, nofollow"
---
```

## Frontmatter Template (Country)

```md
---
title: "Germany"
slug: "germany"
description: "National content overview for Germany."
unique_focus_tree: true
grid_order: 24
grid_note: "EU major branch"
flag_image: "/assets/images/flags/germany.png"
infobox:
  - section: "Overview"
    stats:
      - { label: "Tag", value: "GER" }
      - { label: "Capital", value: "Berlin" }
---
```

Country content is written in the Markdown body:

```md
## Political Situation

Regular markdown text.

| Party | Ideology         | Popularity |
| ----- | ---------------- | ---------- |
| SPD   | Social Democracy | 28%        |
```

## Checks Before PR

```bash
bun run lint:md
bun run lint:remark
bun run check
bun run build
bun run check:links
bun run check:og
bun run check:a11y
bun run check:perf
```
