---
name: dev-diary-mdx
description: >-
  Convert a Millennium Dawn dev diary .docx into a publish-ready .mdx for the docs
  site: frontmatter, headers, and images placed in reading order, with the author's
  voice preserved. Use when given a dev-diary .docx to format or publish, or
  "dev diary 057"-style numbering.
---

# Dev Diary to MDX

The job is structure, not editing. Scaffold the MDX and place the images. Leave the
author's prose as written.

## Preserve the author's voice

- Do not proofread, normalize, reword, reorder, or delete text.
- Keep casual spellings, run-on sentences, asides, jokes, smart quotes, and the
  author's own hyphenation. Keep stylistic ellipses (`….`, `....`) exactly.
- The only allowed change to source text is splitting a paragraph at a sentence
  boundary so an image can sit beside the passage it illustrates.
- Convert an em dash in the source to a period, comma, or colon.
- Text you author (headers, alt text) uses no em dash and no `...`.
- Proofreading is a separate task, only on request, with every change listed.

## 1. Get the `.docx`

Use the path in `$ARGUMENTS` or the attached file. Otherwise ask for it before doing
anything else. A Google Doc exports with Download, Microsoft Word (.docx). Reject other
formats.

## 2. Number

Take the highest `NNN-` prefix in `docs/src/content/devDiaries/*.mdx`, add 1, and
zero-pad to 3 digits. Warn if `docs/src/assets/images/dev-diaries/<NNN>/` exists.

## 3. Extract

```bash
python .claude/skills/dev-diary-mdx/extract_docx.py \
  --docx "<path to .docx>" \
  --image-dir docs/src/assets/images/dev-diaries/<NNN>
```

It copies every embedded image, in document order, to `picture-1.png`, `picture-2.png`,
and so on, and prints JSON with `title`, `blocks` (`heading`, `para`, and `image`
entries in source order), and `images`.

## 4. Frontmatter

Ask for what cannot be derived, offering defaults:

- `title`: the JSON title or first heading, as `"Dev Diary #NN: <Title>"` with NN
  unpadded.
- `description`: one line.
- `author`: the real developer handle, not the in-character narrator.
- `version`: default `v2.0`. It must match `^v\d+\.\d+$` or `bun run check` fails.
- `date`: default today, `YYYY-MM-DD`.

The slug is the kebab-cased title without the "Dev Diary #NN:" prefix. The permalink is
`/dev-diaries/<N>-<slug>/` with the unpadded number. The filename is `<NNN>-<slug>.mdx`.

## 5. Assemble

Write `docs/src/content/devDiaries/<NNN>-<slug>.mdx`, UTF-8 without BOM:

```mdx
---
title: "Dev Diary #58: Greenland"
description: <one line>
permalink: /dev-diaries/58-greenland-holiday-paradise/
author: Luigi
date: 2026-06-12
version: "v2.0"
tags:
  - dev diary
---

_By Luigi – 12 June 2026_

<body>
```

- No `# H1`. The body opens with the italic byline.
- Keep the intro and sign-off without headers. Add `##` or `###` only at real topic
  shifts. Honor the docx's heading styles. For flat prose, add headers in the diary's
  own wording.
- Every extracted image goes into the body. Place each one right after the sentence
  that introduces it, following the prose cues ("the first picture shows", "the next
  pictures in order are"). Word often dumps all screenshots at the top, so prefer the
  cues over block position.
- When one paragraph describes two visuals, split it so each image sits with its
  passage.
- With no cue, place the image where it sits in the `blocks` order and report it.
- Image form, with an absolute path:
  `![picture1](/assets/images/dev-diaries/<NNN>/picture-1.png)`.

## 6. Report

- The `.mdx` path and the image folder.
- How many images were placed, and which had no cue.
- A reminder to check `author`, `version`, and `date` against an existing diary.
- Checks to run from `docs/`: `bun run lint:md`, `bun run lint:remark`,
  `prettier --write` on the new file, and `bun run check`.
