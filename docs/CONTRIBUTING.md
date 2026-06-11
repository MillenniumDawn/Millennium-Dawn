# Contributing to Millennium Dawn Docs (Astro)

> **Looking to contribute to the mod itself?** See the root [CONTRIBUTING.md](../CONTRIBUTING.md) for focus trees, events, AI policy, fork workflow, and everything else. This file covers only the documentation site (under `docs/`).

## Prerequisites

- Node.js 24 LTS or newer ([nodejs.org](https://nodejs.org/))
- [Bun](https://bun.com/) — see **Bun version** below.
- Python 3 (for `check:links`, `check:og`, `check:a11y`, `check:perf`)

### Bun version

The supported Bun release for this package is pinned in `package.json` as `packageManager` (for example `bun@1.3.14`). Treat that value as the canonical toolchain version: CI and other contributors use it, and Bun’s resolver and lockfile behavior can differ between releases, so drifting too far can cause “works on my machine” install or script failures. **Upgrade Bun on your machine from time to time** (security fixes and compatibility with newer tooling), and when this repo bumps the `packageManager` entry or refreshes `bun.lock`, align your local Bun to that version before working on docs.

## Quick Start

```bash
cd docs
bun install
bun run dev
```

Open the local site using the URL shown in the `astro dev` output.

## Where to Edit Content

| Content folder                       | Published URL pattern                       | Notes                                            |
| ------------------------------------ | ------------------------------------------- | ------------------------------------------------ |
| `src/content/pages/*.md`             | `permalink` frontmatter (or `/<filename>/`) | See **Regular pages** below                      |
| `src/content/countries/*.md`         | `/countries/<slug>/`                        | Use `slug` frontmatter when the filename differs |
| `src/content/changelogSections/*.md` | `/changelogs/<filename>/`                   | Listed on `/changelogs/` unless `hidden: true`   |
| `src/content/tutorials/*.md`         | `/player-tutorials/<filename>/`             | Index page is `/tutorials/`                      |
| `src/content/resources/*.md`         | `/dev-resources/<filename>/`                | Index page is `/resources/`                      |
| `src/content/devDiaries/*.{md,mdx}`  | `permalink` or `/dev-diaries/<filename>/`   | Prefer `.mdx` for optimized images               |
| `src/content/misc/*.md`              | `/misc/<filename>/`                         |                                                  |

### Regular pages

Add a Markdown file under `src/content/pages/` with frontmatter. Set `permalink` to the public URL (root-relative, trailing slash), for example `/mod-overview/`. The build creates the route automatically unless the page already has a dedicated route file (`faq`, `getting-started`, and `countries` are special cases).

If you omit `permalink`, the URL defaults to `/<filename>/` (for example `mod-overview.md` → `/mod-overview/`).

## Page headings (H1)

Each published page must have **exactly one** `<h1>`. The layout supplies it for most collections — **do not** repeat the page title as `# Title` in the Markdown body.

| Collection / route                   | Who renders the H1       | Body rule                                                         |
| ------------------------------------ | ------------------------ | ----------------------------------------------------------------- |
| `src/content/pages/*.md` (catch-all) | Layout (`showPageTitle`) | Start with intro text or `##` sections — **no** `#` title line    |
| `getting-started`, `faq`             | Layout (`showPageTitle`) | Same as pages above                                               |
| `src/content/tutorials/*.md`         | Article hero             | **No** `#` matching `title` in frontmatter; use `##` for sections |
| `src/content/resources/*.md`         | Article hero             | Same as tutorials                                                 |
| `src/content/changelogSections/*.md` | Article hero             | Same as tutorials                                                 |
| `src/content/devDiaries/*.{md,mdx}`  | Article hero             | Same as tutorials                                                 |
| `src/content/countries/*.md`         | Country layout           | **No** `#` country name; use `##` for sections                    |
| `src/content/misc/*.md`              | Article hero             | Same as tutorials                                                 |

`bun run check:content-html` fails if a hero-collection file opens with `#` text that matches its frontmatter `title` (case-insensitive).

## Important Rules

- If you change any Markdown under `src/content/**/*.md`, run **`bun run lint:md`** (and preferably **`bun run lint:remark`**) **before you commit**. The same checks run in CI; fixing MD/style issues locally avoids broken builds and noisy follow-up commits.
- Use only Markdown + frontmatter.
- Do not use Liquid (`{% ... %}` / `{{ ... }}`).
- Use root-relative paths for internal links. Folder names are **not** always the URL:
  - Tutorial index: `/tutorials/`
  - Individual tutorial: `/player-tutorials/<slug>/`
  - Resource index: `/resources/`
  - Individual resource: `/dev-resources/<slug>/`
  - Country page: `/countries/germany/`
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

# Required for standalone pages: public URL (trailing slash)
permalink: "/mod-overview/"

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

### Infobox stat labels

In **Military & Industry** and **Economy** sections, stat `label` values must match exactly or the stat is dropped at build time:

| Section kind        | Accepted labels                                                                            |
| ------------------- | ------------------------------------------------------------------------------------------ |
| Military & Industry | `Tag`, `Divisions`, `Total Factories`, `Military Ind.`, `Civilian Ind.`, `Naval Dockyards` |
| Economy             | `Treasury`, `Debt`, `Investments`                                                          |

Overview sections accept any label. A mistyped label in a structured section fails `bun run check`.

Country content is written in the Markdown body:

```md
## Political Situation

Regular markdown text.

| Party | Ideology         | Popularity |
| ----- | ---------------- | ---------- |
| SPD   | Social Democracy | 28%        |
```

## Custom content blocks

### National spirits (`:::spirits`)

Country pages can render a styled spirits list from a container directive. Body must be YAML listing items with `name`, `type`, and optional `desc`:

```md
:::spirits

- name: EU Member
  type: positive
  desc: Access to EU mechanics
- name: Aging Population
  type: negative
  :::
```

`type` must be one of `positive`, `negative`, `mixed`, or `neutral`.

### Dev diary image galleries

Wrap consecutive images in a gallery container:

```md
<div class="dev-diary-gallery">

![First screenshot](/assets/images/dev-diaries/054/example-a.png)
![Second screenshot](/assets/images/dev-diaries/054/example-b.png)

</div>
```

### `.md` vs `.mdx` for images

Use `.mdx` under `src/content/devDiaries/` when the page has images. MDX routes markdown images through the responsive image pipeline (`MarkdownImage` / `Picture`). Plain `.md` bodies compile to basic `<img>` tags without AVIF/WebP `srcset`.

## Checks Before PR

```bash
bun run lint:md
bun run lint:remark
bun run check:content-html
bun run check:flags
bun run check
bun run build
bun run check:links
bun run check:og
bun run check:a11y
bun run check:perf
```
