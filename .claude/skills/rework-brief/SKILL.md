---
name: rework-brief
description: 'Rewrite a country rework/additions TASK issue into a clear, mechanic-by-mechanic design brief: study its mockups, inventory the country''s existing assets, and reframe each mechanic (goal / real-world idea / starting state / influences / player choices / progression) with AI/tooling hints stripped. Use when asked to reframe, clarify, or rewrite a rework task or roadmap issue, e.g. "/rework-brief JAP 801".'
disable-model-invocation: true
---

Rewrite a country **rework / additions task** issue (a roadmap or checklist of proposed mechanics) into a **design brief** that explains each mechanic on its own terms — so any reader understands *what the mechanic is* before code exists. This reframes an existing issue; it does not implement anything.

**Syntax:** `/rework-brief [TAG] [issue-number]` — e.g. `/rework-brief JAP 801`. Either argument may be omitted: infer the TAG from the issue body/branch, or take a pasted task description instead of an issue number.
Requested arguments: $ARGUMENTS

## House style (baked in — do not re-ask unless the user requests changes)

Organise the rewrite **mechanic by mechanic**. Each signature mechanic (and any economy-sector rework) gets this template:

- **Goal** — the design goal and the player experience it creates.
- **The real-world idea** — the real-world concept the mechanic models.
- **Starting state (<game start year>)** — where the country begins, and which *existing* assets already model this today.
- **What it influences** — the concrete game systems it touches (population, stability, productivity, the money system, influence, research, etc.).
- **Player choices** — the branches/paths and side decisions, with their trade-offs.
- **How it progresses** — how it evolves over a game and how it resolves.

Close each section with one italic line: *Built from: <real existing asset IDs>. Shape: <one-phrase implementation form — dynamic modifier / tiered dynamic modifier / timed idea / cosmetic tag / event chain / …>.*

Smaller **standalone additions** (a single MIO trait, extra leaders, a cosmetic tag, a diplomacy tweak) get a lighter treatment: a short Goal/choice paragraph plus the *Built from / Shape* line — not the full six fields.

Rules:
- **Pure design prose.** No slash-commands, no file paths or line numbers, no "mirror the China pattern"-style implementation pointers. The reader should understand the *mechanic*, not the build steps.
- **Name the real existing assets.** For each mechanic, name the actual ideas/spirits/focus branches/dynamic modifiers/decisions it draws on — but only ones you have **verified exist** (step 3). Never repeat an asset name from the old issue without checking it; if the issue names something that does not exist, say so in the rewrite instead of carrying the false claim forward.
- **Light shape hint only.** One phrase for the implementation form, so an implementer has a starting shape — no more.
- **Preserve every image.** Keep every `<img>`/image from the original issue, with its **exact same URL**, in the relevant mechanic's section. Study each image (step 2) and fold its boxes, labels, branch structure, and cross-links into that section's *Player choices* and *How it progresses*.
- **Reuse is optional.** State that reusing the existing assets is not required — replacing or removing old systems outright is fine where a clean rebuild serves the design better. The *Built from* notes are a starting inventory, not a constraint.
- **Interlocks.** If the mechanics reference each other (the mockups usually show this), add a short "How the mechanics interlock" section listing the cross-links.
- **Demote sequencing.** Move build-order/phasing and any `/validate`, `/lifecycle-check`, `/changelog`, `/open-pr` checklist into a short build-order appendix; drop the procedural tooling steps from the design body.
- Non-English localisation is out of scope (per AGENTS.md) — do not discuss loc parity.

## Steps

### 1. Resolve inputs
Determine the TAG (uppercase) and the issue number from `$ARGUMENTS`. Fetch the issue:

```
gh issue view <number> --repo MillenniumDawn/Millennium-Dawn --json title,body,labels,comments
```

If given a pasted task description instead, use that as the source. If the TAG is not given, infer it from the issue body or the current branch. Read the full body and any comments.

### 2. Study the mockups
Extract every image URL from the issue body. Download each to the scratchpad and **Read it as an image** (the mockups are usually wide flowcharts — boxes for each branch, coloured notes for trade-offs and cross-mechanic links):

```
curl -sL "<image-url>" -o "<scratchpad>/<tag>_<mechanic>.png"
```

Record, per image: the starting spirit/state, each branch/resolution and its stated pros/cons, side decisions, and any cross-mechanic dependencies. Keep the URLs — they go back into the rewrite unchanged.

### 3. Inventory the country's existing assets
Launch up to **3 Explore agents in parallel**, split by mechanic cluster, to map what already exists for this country and what each asset currently *does*. Ask each agent to report, with exact identifiers and concrete effects: the ideas/national spirits, focus-tree branches, dynamic modifiers, decisions (and categories), MIOs, characters, and diplomacy content the issue references — and to **flag explicitly any named asset that does not exist**. This grounds every "Starting state" line and catches false claims in the old issue (a common failure: the roadmap lists "foundation" ideas that were never coded).

### 4. Draft the rewrite
Write the new issue body in the house style: an opening "What this is" paragraph, one section per mechanic (images in place), a "How the mechanics interlock" section, standalone additions, and a build-order appendix. Correct any false claims surfaced in step 3.

### 5. Review with the user
Present the **full new body** for approval. Do not edit the issue yet.

### 6. Apply on confirm
After the user approves, write the body to a UTF-8 file and apply it — this replaces only the body; title, labels, and assignees are untouched:

```
gh issue edit <number> --repo MillenniumDawn/Millennium-Dawn --body-file <file>
```

### 7. Verify
Re-view the issue; confirm every image renders (URLs are unchanged, so they will), the title/labels are intact, and the section headings and *Built from / Shape* italics read correctly. Report the issue URL and a one-line summary.
