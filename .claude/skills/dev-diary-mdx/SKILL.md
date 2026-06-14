---
name: dev-diary-mdx
description: >-
  Convert a Millennium Dawn dev diary supplied as a .docx Word document (Word,
  or Google Docs exported via Download -> Microsoft Word) into a publish-ready
  .mdx file for the docs site's dev-diaries section. Use whenever someone
  provides a dev-diary .docx (narrative write-ups about focus trees, mechanics,
  nations, or mod features) and wants it turned into MDX, "formatted for the
  diary site", or "made ready to publish"; when a .docx named "Dev Diary" is
  attached; when images need extracting into the assets/images/dev-diaries/<NNN>/
  folder convention; or when someone references "dev diary 057"-style numbering.
  Handles frontmatter, section headers, image extraction and in-order placement,
  while preserving the author's original voice verbatim.
---

# Dev Diary -> MDX

Turns a Millennium Dawn dev diary `.docx` into a publish-ready `.mdx` for the
docs site. **The job is structure, not editing**: scaffold the MDX and place the
images, but leave the author's prose as written.

## Core rule: preserve the author's voice (read this first)

Dev diaries are written in a deliberate, often in-character voice. The rule most
likely to be broken is "improving" the prose. Do not.

- **Do NOT** proofread, normalize, sanitize, reword, reorder, or delete text.
- **Keep** casual spellings ("breakin", "gonna", "mayhaps"), run-on sentences,
  asides, mild profanity/jokes, smart quotes, and the author's own
  spelling/hyphenation ("self sufficiency", "Self Government Act").
- **Keep the author's stylistic ellipses** (`….`, `....`, `…..`) exactly as
  written. These are voice, not AI ellipsis abuse. Do not collapse them.
- The **only** allowed change to source text is **splitting a paragraph at a
  sentence boundary** so an image can sit beside the passage it illustrates.

### Anti-AI-tell exceptions (still apply, scoped narrowly)

The repo's no-em-dash / no-ellipsis-abuse style rules also keep the published
page from *looking* AI-generated, so:

- **Text you author** (section headers, image alt text, the seam where you split
  a paragraph): never use an em dash (`—`) or `...` ellipsis abuse, and never
  generic AI phrasing.
- **Author's source prose:** convert any em dash (`—`) per the loc rule (period,
  comma, or colon as fits) — em dashes are a strong AI tell and the author
  rarely intends one. But keep their stylistic ellipses (above) untouched.

If the user explicitly asks for proofreading, that is a separate, opt-in task:
do it then, and list every change so they can revert.

## Step 1 — Get the source `.docx`

If `$ARGUMENTS` (or an attached file) already points to a `.docx`, use it.
Otherwise **ask the user to attach or give the path to the `.docx`** before
doing anything else. If they have a Google Doc, tell them to use
*Download -> Microsoft Word (.docx)* — that export is the same format. Reject
non-`.docx` input.

## Step 2 — Determine the next diary number

List `docs/src/content/devDiaries/*.mdx`, take the highest `NNN-` prefix, add 1,
and zero-pad to 3 digits (e.g. `057` -> `058`). This `NNN` is reused for both the
`.mdx` filename and the image folder. Warn if
`docs/src/assets/images/dev-diaries/<NNN>/` already exists.

## Step 3 — Extract text and images

Run the bundled helper (stdlib-only, no deps). From the repo root:

```bash
python .claude/skills/dev-diary-mdx/extract_docx.py \
  --docx "<path to .docx>" \
  --image-dir docs/src/assets/images/dev-diaries/<NNN>
```

It creates the image folder, copies every embedded image — in document order —
to `picture-1.png`, `picture-2.png`, … (extensions preserved), and prints JSON:

```json
{ "title": "…|null",
  "blocks": [ {"type":"heading","level":2|3,"text":"…"},
              {"type":"para","text":"…"},
              {"type":"image","index":N} ],
  "images": ["picture-1.png", …] }
```

The JSON text is verbatim UTF-8. Treat the `blocks` order as the source order.

## Step 4 — Collect frontmatter (ask the user)

Prompt for the fields that can't be reliably derived, offering defaults:

- **title** — default to the JSON `title` or the doc's first heading. Final
  frontmatter form is `"Dev Diary #NN: <Title>"` (NN = number without padding,
  e.g. `#58`).
- **description** — one line.
- **author** — the **real** developer handle (e.g. `Luigi`). NOT the in-character
  narrator ("Luigi IV von Limingly").
- **version tag** — default `v2.0`.
- **date** — default today, format `YYYY-MM-DD`.

Derive the **slug** by kebab-casing the title *without* the "Dev Diary #NN:"
prefix (e.g. `Greenland: Holiday Paradise` -> `greenland-holiday-paradise`).
Build `permalink: /dev-diaries/<NNN>-<slug>/` (zero-padded NNN).

## Step 5 — Assemble the `.mdx`

Write `docs/src/content/devDiaries/<NNN>-<slug>.mdx`, **UTF-8 without BOM**
(it is not a loc file), in this exact shape:

```mdx
---
title: "Dev Diary #58: Greenland"
description: <one line>
permalink: /dev-diaries/058-greenland-holiday-paradise/
author: Luigi
date: 2026-06-12
tags:
  - dev diary
  - v2.0
---

_By Luigi – 12 June 2026_

<body>
```

Body rules:

- **No `# H1`.** The title lives only in frontmatter; the body opens with the
  italic byline `_By <Author> – <DD Month YYYY>_`.
- **Headings:** keep the narrative intro and the sign-off header-less. Insert
  `##` (or `###` for sub-topics) only at genuine topic shifts. If the docx had
  heading styles, honor them; if it was flat prose (common — the author often
  writes one long stream), add headers yourself using the diary's own wording
  (typical focus-tree diary: `## The National Situation`,
  `## The National Focus Tree`, `## Decisions and Policies`).
- **Every extracted image goes into the body — always place the full content.**
  No image is dropped. Image placement prefers the text's reading-order cues
  over the raw block position. Word docs frequently dump every screenshot in one
  cluster at the top; the `blocks` array reflects that. The `index` in each image
  block is the stable filename number (`picture-<index>.png`). Place each image
  **immediately after the sentence/paragraph that introduces it**, following the
  prose cues:
  - "The first picture shows …" -> `picture-1` after that sentence.
  - "The next pictures in order are the economic tree and political trees" ->
    place those consecutively right after that sentence.
  - When two visuals are described in separate passages of one paragraph (e.g.
    the military tree, then "Moving to the GIS tree…"), **split** the paragraph
    at that boundary so each image sits with its own passage.
  - Match the repo's reference form exactly:
    `![picture1](assets/images/dev-diaries/<NNN>/picture-1.png)` — alt text
    `![pictureN]`. (Descriptive alt text is more accessible; offer it as an
    option but default to `![pictureN]`.)
  - **If the prose gives no cue for an image** (e.g. a Decisions screenshot the
    author never calls out), do not drop it — place it at the position it
    occupies in the document, i.e. after the body text that corresponds to the
    block immediately preceding that image in the extractor's `blocks` array.
    Then note it in Step 6 so the user can move it if they prefer.

## Step 6 — Report and flag for confirmation

Tell the user, concisely:

- the new `.mdx` path and the image folder;
- **image count** — how many were extracted and placed (all of them), and which
  ones had no prose cue and were placed by document-position fallback (so they
  can move them);
- a reminder to eyeball the frontmatter (`author` = real handle, version tag,
  date) against an existing diary;
- suggested checks from `docs/`: `bun run lint:md`, `bun run lint:remark`, and
  `prettier --write src/content/devDiaries/<NNN>-<slug>.mdx`, plus
  `bun run check` to validate the content-collection frontmatter schema.
