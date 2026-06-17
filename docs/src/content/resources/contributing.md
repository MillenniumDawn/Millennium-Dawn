---
title: Contributing to the Docs Site
description: How to contribute to the Millennium Dawn documentation site, bun setup, content conventions, link rules, and the docs CI pipeline.
---

This guide covers contributing to the **documentation site** (the `docs/` directory and the pages it builds). For contributing to the mod itself (focus trees, events, ideas, AI, graphics, map work), see the [Developer Setup Guide](/dev-resources/developer-setup/).

> **Repo-root context**: [`CONTRIBUTING.md`](https://github.com/MillenniumDawn/Millennium-Dawn/blob/main/CONTRIBUTING.md) is a slim pointer to the right docs.

---

## Setup

The docs site requires [Node.js 24 LTS](https://nodejs.org/) and [Bun](https://bun.sh/):

```bash
python3 tools/setup.py --docs    # installs Node.js + Bun dependencies
```

To preview locally:

```bash
cd docs
bun run dev    # opens at http://localhost:4321/
```

---

## Before Opening a Docs PR

Run the full check suite against your changes:

```bash
cd docs
bun run ci     # lint, typecheck, build, link check, a11y, perf budgets
```

To run individual checks during development:

```bash
bun run lint:md          # markdownlint
bun run check            # astro check (type errors)
bun run build            # full build
bun run check:all        # every docs check (skips the build; reuses dist/)
bun run check:link-syntax # malformed Markdown links
bun run check:content-html # raw HTML, duplicate H1s
bun run check:links      # broken internal links (needs build first)
bun run check:a11y       # accessibility baseline (needs build first)
```

All docs checks live in `tools/docs_checks/` (a single Python package with a shared `common.py` and the `check_docs.py` runner that `bun run ci` / `check:all` call). The `bun run check:*` scripts wrap them with the right arguments (base path, repo root); prefer them over invoking the Python files directly.

---

## Content Structure

| Path                                  | Content                                  |
| ------------------------------------- | ---------------------------------------- |
| `docs/src/content/pages/`             | Top-level pages (FAQ, Getting Started)   |
| `docs/src/content/resources/`         | Developer resource guides                |
| `docs/src/content/tutorials/`         | Player and developer tutorials           |
| `docs/src/content/countries/`         | Country-specific documentation           |
| `docs/src/content/navigation/`        | Site navigation and footer               |
| `docs/src/content/redirects/`         | URL redirects for moved pages            |
| `docs/src/content/changelogSections/` | Version changelogs                       |
| `docs/src/content/devDiaries/`        | Published dev diaries                    |
| `docs/templates/`                     | Contributor templates (not in the build) |

Content uses Markdown with YAML frontmatter. Each content collection has a schema in `docs/src/schemas/base.ts`. The `pages` collection is the simplest; `countries` has the most fields.

---

## Frontmatter Requirements

Every content file needs at least a `title`. The schema validates other fields:

- `title` (string): the page title. Rendered as an H1 by the layout.
- `description` (string, optional): used for the page meta description.
- `permalink` (string, optional): explicit URL path. Must be root-relative (`/some/path/`).
- `toc` (`"auto"` | `"off"`, optional): table of contents control.
- `hidden` (boolean, optional): if true, the page is not in the index or navigation.
- `last_updated` (date, optional): rendered in the page footer.

Country pages have additional required fields: `unique_focus_tree` (boolean), `grid_order` (integer), and optional `grid_note`, `flag_image`, `infobox`.

---

## Writing Rules

### Links

Internal links must be **root-relative**: `[Guide](/dev-resources/guide-name/)`. Do not hardcode `"/Millennium-Dawn/..."` or use `../` relative paths. The base path is applied during build.

Always include a trailing slash on internal links. Both forms resolve, but trailing-slash is the standard and avoids inconsistencies.

External links must be full URLs: `[GitHub](https://github.com/...)`. The build adds `target="_blank"` and `rel="noopener noreferrer"` automatically.

### Images

Image paths follow the same root-relative pattern: `![Alt](/assets/images/example.png)`. Drop new images into `docs/src/assets/images/` first.

### Prose

- Terse and direct. Short lines, plain words, vary sentence length.
- No em-dashes (en-dash or em-dash). Use periods, commas, or parentheses instead. Enforced by the `MD9999` custom markdownlint rule.
- American spelling (color, not colour). Exception: in-game proper nouns keep their spelling.
- Avoid AI-marketing words (authoritative, canonical, seamless, robust, sweet spot, load-bearing, stays in sync, on top).
- Match the voice of the existing page you are editing. When in doubt, check `docs/src/content/resources/code-stylization-guide.md` or a recent dev diary for the tone.
- Do not use GitHub-specific emoji shortcodes (`:repeat:`, `:white_check_mark:`). Use literal emoji or strip them.

### Code Blocks

Use `hoiscript` as the language identifier for HOI4 script blocks:

```hoiscript
country_event = {
    id = tag_ns.N
    ...
}
```

For other languages use `bash`, `python`, `json`, `yaml`, or `text` as appropriate.

### Tables

Markdown tables are supported and preferred over raw HTML. The markdownlint `MD060` rule enforces consistent pipe alignment.

---

## Country Pages

Country pages live in `docs/src/content/countries/`. Each page has a frontmatter block with `unique_focus_tree`, `grid_order`, and an optional `infobox` array.

The `infobox` is an array of groups, each with a `section` (string) and `stats` (array of `{label, value}`). The `Status` section with `Content: WIP` is used by the grid card to render a WIP badge.

When writing a country page:

- Start with a prose introduction (2-4 paragraphs) covering the country's starting position, diplomacy, economy, and military.
- Use the `## Initial National Spirits` section to list the spirits the country starts with. Match the actual `add_ideas` in `history/countries/`.
- Use the `## Unique National Features` section to describe mechanics specific to the country.
- Use the `## National Focus` section to describe the focus tree structure.
- Use the `## Q&A` section for common player questions.

See `docs/src/content/countries/italy.md` for the reference implementation.

---

## Changelog Sections

Changelog sections live in `docs/src/content/changelogSections/`. Each file has:

- `title`: the version heading (e.g., `v1.10.0 'The Lion of Brussels and Babylon'`).
- `page_id`: a stable identifier used in the URL (`changelog-v1-10-the-lion-of-brussels-and-babylon`).
- `order`: an integer controlling the sort order on the changelogs index page.
- `hidden` (optional): if true, the page is not in the index.

The `page_id` drives the URL (`/changelogs/{page_id}/`). Changing the `page_id` or the filename changes the URL; use the `redirects` collection to preserve old links.

---

## Dev Diaries

Dev diaries live in `docs/src/content/devDiaries/`. They use MDX (not plain Markdown) so the `MarkdownContent` component can map `img` tags to `MarkdownImage`.

A template is available at `docs/templates/dev-diary-template.mdx`. Copy it to `docs/src/content/devDiaries/NN-short-slug.mdx` and fill in the frontmatter and body.

The dev-diary archive (`docs/src/content/devDiaryArchive/index.yml`) lists published diaries grouped by version. Add your diary to the appropriate group.

---

## Redirects

If you move or rename a page, add a redirect in `docs/src/content/redirects/`:

```markdown
---
title: Old Page Redirect
permalink: /old-path/
redirect_to: /new-path/
seo: false
robots: noindex, nofollow
toc: "off"
---

This page has moved to [/new-path/](/new-path/).
```

---

## What We Accept

Docs contributions are welcome in the following areas:

- New guides, tutorials, or reference pages.
- Updates to existing pages to reflect current game mechanics.
- Country page content (prose, not WIP stubs).
- Bug fixes (broken links, typos, wrong code samples).
- Changelog entries for new releases.
- Dev diaries.

Non-English localisation is managed through [Paratranz](https://paratranz.cn/projects/millennium-dawn); do not submit translations directly.

---

## Related Resources

- [Developer Setup Guide](/dev-resources/developer-setup/): main developer guide for the mod.
- [Code Stylization Guide](/dev-resources/code-stylization-guide/): formatting and code structure.
- [Content Review Guide](/dev-resources/content-review-guide/): quality checklist.
- [Git Workflow](/dev-resources/git-workflow/): branch/commit/PR process.
- [AI Modding Guide](/dev-resources/ai-modding-guide/): AI tools for development.
- [`CONTRIBUTING.md`](https://github.com/MillenniumDawn/Millennium-Dawn/blob/main/CONTRIBUTING.md): repo-root pointer.

---

For questions, join the [Discord](http://discord.gg/millenniumdawn) or open an issue.
