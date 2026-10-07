---
name: lifecycle-check
description: 'Audit a country branch against the focus tree lifecycle checklist (focus tree, ideas, decisions, OOB, characters, loc, namelists, AI, game rules, graphics, changelog), reporting done/missing/partial per item. Use when asked if a country''s content is complete or review-ready, e.g. "/lifecycle-check UKR".'
---

**Syntax:** `/lifecycle-check [TAG]`. Without a TAG, infer it from the most frequent
country prefix in `git diff origin/main...HEAD --name-only`.

Read `docs/src/content/resources/focus-tree-lifecycle-checklist.md` first.

## Checks

Mark each item Done, Missing, or Partial (the file exists but looks like a stub).

Drafting cannot be checked from files. Remind the user that draft approval comes before
coding.

### Coding

| Item                    | How to check                                                           |
| ----------------------- | ---------------------------------------------------------------------- |
| Focus tree file         | `common/national_focus/05_TAG.txt` exists and is non-empty             |
| Focus tree rewards      | Count `completion_reward` blocks vs focus count to spot stubs          |
| National ideas          | `common/ideas/TAG.txt` exists; grep for `idea` blocks                  |
| National decisions      | `common/decisions/TAG*.txt` (or under `categories/`) exists            |
| History file updated    | `history/countries/TAG*.txt` in branch diff, or exists and non-trivial |
| OOB file                | `history/units/TAG_*.txt` exists                                       |
| Character file          | `common/characters/TAG.txt` has a `general` or `field_marshal` block   |
| Party localisation      | `localisation/english/` contains a file with `TAG.` ideology keys      |
| Focus localisation      | `localisation/english/MD_focus_TAG_l_english.yml` non-empty            |
| Ideas localisation      | `localisation/english/` file with `TAG_idea_` or `TAG_spirit_` keys    |
| Decisions localisation  | `localisation/english/` contains a file with decision keys for TAG     |
| Unit namelists          | TAG name entries in `common/units/names/` or `names_divisions/`        |
| Investment/Influence AI | `common/ai_strategy/TAG*.txt` has investment or influence entries      |
| Game rules              | `common/game_rules/` contains a rule referencing TAG                   |
| Scripted localisation   | `common/scripted_localisation/` file with TAG entries (if used)        |

### Graphics

| Item             | How to check                                                    |
| ---------------- | --------------------------------------------------------------- |
| Focus icons      | Every focus has `icon =`; flag placeholders like `goal_unknown` |
| Idea icons       | Grep the ideas file for `picture =`                             |
| Leader portraits | `gfx/leaders/TAG/` exists and contains at least one `.dds` file |

### Polish and completion

| Item            | How to check                                                |
| --------------- | ----------------------------------------------------------- |
| Spell-check     | Manual review needed                                        |
| error.log clear | Requires an in-game test                                    |
| Playtest        | Requires manual confirmation                                |
| Code compliance | Recommend `/content-review` and `/audit`                    |
| Changelog entry | Grep `Changelog.txt` for the TAG or country name            |
| Authors updated | Confirm manually against `docs/src/content/misc/authors.md` |

## Output

One line per item, grouped by phase, with `[✓]`, `[✗]`, `[~]`, or `[?]`, the item name,
and the path or reason. End with a count of done, missing, partial, and manual-only.
Flag any missing item required before lead review: focus tree, OOB, localisation,
changelog.
