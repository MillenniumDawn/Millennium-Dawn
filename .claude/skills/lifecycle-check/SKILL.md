Audit a country's content branch against the focus tree lifecycle checklist and report which phases are done or missing.

**Syntax:** `/lifecycle-check [TAG]`

- With `TAG`: check all required files for that specific country tag.
- Without argument: infer the TAG from the current branch name or changed files.

The authoritative checklist is `docs/src/content/resources/focus-tree-lifecycle-checklist.md`. Read it before starting.

---

## Execution

### 1. Determine the TAG

If TAG is provided, use it directly (uppercase). Otherwise, run:

```
git diff origin/main...HEAD --name-only
```

and infer the TAG from the most frequently changed country-specific prefix in the diff.

### 2. Check each lifecycle item

Run the checks below. For each item mark it **Done**, **Missing**, or **Partial** (file exists but seems incomplete — e.g. an empty stub).

#### Drafting Phase

These cannot be checked from files — mark them as "not verifiable from code" and remind the user that draft approval must happen before coding.

#### Coding Phase

| Item                    | How to check                                                                                        |
| ----------------------- | --------------------------------------------------------------------------------------------------- |
| Focus tree file         | `common/national_focus/05_TAG.txt` exists and is non-empty                                          |
| Focus tree rewards      | Grep for `completion_reward` in the focus file — count blocks vs focus count to spot stubs          |
| National ideas          | `common/ideas/TAG.txt` exists; grep for `idea` blocks                                               |
| National decisions      | `common/decisions/TAG*.txt` or `common/decisions/categories/TAG*.txt` exists                        |
| History file updated    | `history/countries/TAG*.txt` modified in branch diff, or exists and is non-trivial                  |
| OOB file                | `history/units/TAG_*.oob` or `history/units/TAG/*.oob` exists                                       |
| Character file          | `common/characters/TAG.txt` exists with at least one `general` or `field_marshal` block             |
| Party localisation      | `localisation/english/` contains a file with `TAG.` ideology keys                                   |
| Focus localisation      | `localisation/english/MD_focus_TAG_l_english.yml` exists and is non-empty                           |
| Ideas localisation      | `localisation/english/` contains a file with `TAG_idea_` or `TAG_spirit_` keys                      |
| Decisions localisation  | `localisation/english/` contains a file with decision keys for TAG                                  |
| Unit namelists          | `common/units/names/` or `common/units/names_divisions/` contains a file with TAG name entries      |
| Investment/Influence AI | `common/ai_strategy/TAG*.txt` exists with investment or influence entries                           |
| Game rules              | `common/game_rules.txt` or `common/game_rules/` contains a rule referencing TAG                     |
| Scripted localisation   | `common/scripted_localisation/` contains a file with TAG entries (if the country uses scripted loc) |

#### Graphics Phase

| Item             | How to check                                                                                                    |
| ---------------- | --------------------------------------------------------------------------------------------------------------- |
| Focus icons      | Grep the focus file for `icon =` on every focus block; spot any using a default/placeholder like `goal_unknown` |
| Idea icons       | Grep the ideas file for `picture =`                                                                             |
| Leader portraits | `gfx/leaders/TAG/` directory exists and contains at least one `.dds` file                                       |

#### Polish Phase

| Item                     | How to check                                                     |
| ------------------------ | ---------------------------------------------------------------- |
| Localisation spell-check | Cannot be checked automatically — note as "manual review needed" |
| error.log clear          | Cannot be checked from files — note as "requires in-game test"   |
| Playtest done            | Cannot be checked — note as "requires manual confirmation"       |
| Code Resource compliance | Note that `/content-review` and `/review-branch` should be run   |

#### Completion Phase

| Item                | How to check                                                                                           |
| ------------------- | ------------------------------------------------------------------------------------------------------ |
| Changelog entry     | Grep `Changelog.txt` for the TAG or country name                                                       |
| Authors.txt updated | Grep `Authors.txt` for the developer's name (cannot verify automatically — note as "confirm manually") |

### 3. Output

Print a checklist table:

```
Lifecycle Check — TAG (Country Name)
=====================================

CODING PHASE
  [✓] Focus tree file            common/national_focus/05_TAG.txt
  [✗] National decisions         No file found matching common/decisions/TAG*.txt
  [~] Focus localisation         File exists but may be incomplete (N keys found)
  ...

GRAPHICS PHASE
  [✓] Focus icons                All N focuses have non-placeholder icons
  [✗] Leader portraits           gfx/leaders/TAG/ not found
  ...

COMPLETION PHASE
  [✓] Changelog entry            Found "TAG" in Changelog.txt
  [?] Authors.txt                Cannot verify — confirm manually
  ...

Summary: N done, N missing, N partial, N manual-only
```

Flag any **Missing** items that are required before a lead review can be requested (focus tree, OOB, localisation, changelog).
