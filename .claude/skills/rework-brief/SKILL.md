---
name: rework-brief
description: 'Rewrite a country rework or additions task issue into a mechanic-by-mechanic design brief: study its mockups, inventory the country''s existing assets, and reframe each mechanic with tooling hints stripped. Use when asked to reframe, clarify, or rewrite a rework task or roadmap issue, e.g. "/rework-brief JAP 801".'
disable-model-invocation: true
---

Rewrite a rework task issue into a design brief that explains each mechanic on its own
terms. This reframes an existing issue. It implements nothing.

**Syntax:** `/rework-brief [TAG] [issue-number]`. Either may be omitted: infer the TAG
from the issue or branch, or take a pasted task description.
Requested arguments: $ARGUMENTS

## House style

Do not re-ask about this. Each signature mechanic, and each economy-sector rework, gets:

- **Goal**: the design goal and the player experience.
- **The real-world idea**: the concept the mechanic models.
- **Starting state (<start year>)**: where the country begins and which existing assets
  model it today.
- **What it influences**: the game systems it touches.
- **Player choices**: branches, paths, and side decisions, with trade-offs.
- **How it progresses**: how it evolves and resolves.

Close each section with one italic line:
_Built from: <existing asset ids>. Shape: <one phrase, such as dynamic modifier, timed
idea, cosmetic tag, or event chain>._

Smaller standalone additions (one MIO trait, extra leaders, a cosmetic tag) get a short
goal paragraph and the _Built from / Shape_ line.

Rules:

- Pure design prose. No slash commands, file paths, line numbers, or "mirror the China
  pattern" pointers.
- Name only assets you have verified exist. If the issue names one that does not, say
  so in the rewrite.
- Keep every image from the original issue, with its exact URL, in the relevant
  section. Fold each mockup's boxes, labels, and cross-links into _Player choices_ and
  _How it progresses_.
- Say that reusing existing assets is optional. A clean rebuild is fine where it serves
  the design.
- If the mechanics reference each other, add a "How the mechanics interlock" section.
- Move build order, phasing, and any tooling checklist to a short appendix.
- Do not discuss non-English localisation.

## Steps

1. Resolve the TAG and issue number, then fetch the issue with its comments:

   ```
   gh issue view <number> --repo MillenniumDawn/Millennium-Dawn --json title,body,labels,comments
   ```

2. Study the mockups. Download every image in the body to the scratchpad and read it as
   an image. Record the starting state, each branch and its pros and cons, side
   decisions, and cross-mechanic dependencies.

3. Inventory the country's existing assets. Launch up to 3 Explore agents in parallel,
   split by mechanic cluster. Each reports, with exact identifiers and concrete
   effects, the ideas, focus branches, dynamic modifiers, decisions, MIOs, characters,
   and diplomacy content the issue references, and flags any named asset that does not
   exist.

4. Draft the new body: a "What this is" paragraph, one section per mechanic with its
   images, the interlock section, standalone additions, and the build-order appendix.

5. Present the full body for approval. Do not edit the issue yet.

6. On approval, write the body to a UTF-8 file and apply it. This replaces only the
   body:

   ```
   gh issue edit <number> --repo MillenniumDawn/Millennium-Dawn --body-file <file>
   ```

7. View the issue again. Confirm the images render and the title and labels are intact.
   Report the URL.
