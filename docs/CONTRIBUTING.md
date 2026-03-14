# Contributing to Millennium Dawn Docs (Astro)

## Prerequisites

- Node.js 24 LTS or newer ([nodejs.org](https://nodejs.org/))
- [Bun](https://bun.com/)
- Python 3 (for `check:links`, `check:og`, `check:a11y`, `check:perf`)

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
- Dev diaries: `src/content/devDiaries/*.md`
- Misc: `src/content/misc/*.md`

## Important Rules

- Use only Markdown + frontmatter.
- Do not use Liquid (`{% ... %}` / `{{ ... }}`).
- Use root-relative paths for internal links: `/tutorials/`, `/countries/germany/`.
- Do not manually add the `/Millennium-Dawn` prefix.

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
