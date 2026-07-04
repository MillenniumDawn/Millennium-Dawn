---
title: Changelog Guide
description: Standards for writing changelog entries in Millennium Dawn.
---

# Changelog Guide

How to write changelog entries for Millennium Dawn. All contributors and agents must follow these standards.

## Purpose

Changelog.txt records user-visible changes between releases. Entries explain what changed and why, so players understand the impact of an update without needing to read code or diffs.

## Who Adds Entries

- **Every PR** that introduces user-visible changes must include a Changelog.txt entry.
- The author of the change is responsible for adding the entry during the PR lifecycle.
- If a change is made during development and no entry exists, add one before the PR is merged.

## Version Sections

Each version section begins with `vX.Y.Z` on its own line. Only add entries under the **top-most version** that has not been tagged/released.

## Category Headings

Use the existing category structure. Common categories:

- Achievements
- AI
- Balance
- Bugfix
- Content
- Database
- Factions
- Game Rules
- Graphics
- Localization
- Map
- Performance
- Quality of Life
- Sound
- Technology
- User Interface

If a change does not fit an existing category, use the closest match. Do not invent new categories without discussing with the project lead.

## Entry Format

```
 Category:
  - [TAG] Past-tense verb. Specific object name. (Issue #N)
```

**Rules:**

- **1 space** before the category name.
- **2 spaces + `- `** before each entry.
- **`[TAG]` prefix** for country-specific changes; no prefix for global changes.
- **Past tense** — describe what changed, not what will change.
- **Specific** — name the exact focus ID, event ID, decision ID, or mechanic.
- **No em dashes** — use a period to end the sentence.
- **Issue reference** — include `(Issue #N)` when the change resolves or relates to a GitHub issue.

## Examples

```
 Bugfix:
  - [ENG] Fixed typo ENG_elisabeth_ruling_monarch → ENG_elizabeth_ruling_monarch in country history, which blocked completion of the Queen's Family focus tree branch (Issue #894)
  - Converted 24 hidden events (AFG, ALG, BDI, CHI, CTR, Iran, JAP, KOR, KUR, LAR, LBR, SYR, SUD, TAL, USA, BOS) from option-based to immediate-only pattern, and removed dead localisation keys for converted events (Issue #1389)

 AI:
  - Added employment-based staffing triggers to prevent AI from taking construction focuses when it cannot staff the resulting building

 Content:
  - [HKG] Major Hong Kong content expansion: ~142-focus tree across 12 branches
```

## What Makes a Good Entry

1. **Lead with the change** — what was added, fixed, or removed?
2. **Name the specific object** — focus ID, event ID, decision ID, or mechanic.
3. **Include the impact** — what does the player notice?
4. **Use consistent casing** — match the style of surrounding entries.

## What NOT to Write

- **No padding filler** — "Fixed an issue where the AI would not behave correctly" is not specific enough. Write "Fixed AI sending volunteers to countries it cannot reach."
- **No internal terminology** — players do not know what "immediate block" or "trigger scope" means.
- **No em dashes** — em dashes read as soft connectors and do not fit the changelog style.
- **No future tense** — "Will add" is wrong. "Added" is correct.
- **No duplicates** — if an entry already covers a change, do not add another for the same change.

## Quality Checklist

Before adding an entry, verify:

- [ ] Is it under the correct version section?
- [ ] Does it use the correct category?
- [ ] Is the [TAG] prefix correct (or omitted for global changes)?
- [ ] Is it in past tense?
- [ ] Does it name the specific focus/event/decision ID?
- [ ] Does it describe the user-visible impact?
- [ ] Does it reference the Issue # if applicable?
- [ ] Does it contain no em dashes?
- [ ] Is it not a duplicate of an existing entry?

## Related Documentation

- [Code Stylization Guide](/resources/code-stylization-guide/) — coding standards
- [Event Reference](/resources/new-general-guidelines/) — event conventions
