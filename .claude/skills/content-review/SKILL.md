---
name: content-review
description: "Check a file or the branch diff against the full MD content review checklist (economic, political, visual, military, AI, code) with blocker tags. Use when asked to content-review country content or verify content-guideline compliance before merge."
---

Run the full Millennium Dawn content review checklist against a file or the current branch diff.

**Syntax:** `/content-review [file_path]`

- With `file_path`: review that specific file against all content guidelines.
- Without argument: review all changed files on the current branch against `main`.

The authoritative checklist lives in `docs/src/content/resources/content-review-guide.md` and `docs/src/content/resources/new-general-guidelines.md`. Read both before starting if not yet read this session. The condensed `.claude/docs/content-guidelines.md` is a quick summary but not exhaustive; always defer to the full docs.

## Execution

### 1. Gather context

**File mode** (path provided):

- Read the file and identify its type (focus tree, events, characters/generals, OOB, decisions, etc.).
- Read `docs/src/content/resources/content-review-guide.md`, `docs/src/content/resources/new-general-guidelines.md`, and `.claude/docs/content-guidelines.md`.

**Branch mode** (no argument):

- Run `git diff origin/main...HEAD` and `git log origin/main..HEAD --oneline`.
- Identify the changed files and their types.
- Read `docs/src/content/resources/content-review-guide.md`, `docs/src/content/resources/new-general-guidelines.md`, and `.claude/docs/content-guidelines.md`.

### 2. Apply the checklist

For each file in scope, check the categories in `.claude/docs/content-guidelines.md` (Economic, Political, Visual, Military, AI, Code, Variety, Miscellaneous). Skip categories that don't apply to the file type (no admiral counts in a decisions file, no building costs in a character file).

For focus-tree files, run the **Variety** check as a cross-comparison, not in isolation: pick a reference tree known for variety (Iran `common/national_focus/05_iran.txt`, Spain `common/national_focus/05_spain.txt`) and judge reward-shape diversity against it. A tree can pass every balance check and still be formulaic. See `.claude/docs/content-guidelines.md` → Variety & Anti-Formulaic Content.

### Detection notes

Three failure classes that spot-checking reliably undercounts. Sweep the whole file for these, don't sample:

- **Treasury double-charge (block-aware).** MD's self-charging build effects (`one_random_arms_factory`, `one_random_industrial_complex`, `two_random_*`, `one_random_infrastructure`, `one_office_construction`, and similar in `common/scripted_effects/`) already deduct treasury internally unless `set_temp_variable = { skip_payment = 1 }` is set beforehand. A focus that calls one of these **and** adds an explicit `set_temp_variable = { treasury_change = -X } modify_treasury_effect = yes` with no `add_building_construction` to justify the second charge pays twice. Distinguish from the legitimate pattern: a raw non-charging engine effect (`add_building_construction`) paired with one explicit charge is correct. Grep every focus that calls a self-charging effect and check each for a redundant explicit charge; per-branch sampling misses most of them.
- **Loc completeness checks _referenced_ keys, not just new ones.** Verify that every `tooltip = <key>`, idea key, and modifier `_tt` key _referenced_ from the tree resolves in `localisation/english/`, not merely that the diff's newly-added keys resolve. A modernization pass routinely references a generic `_tt` key that never existed, and a diff-only check will not catch it.
- **Dynamic-modifier first-add guard, per reachable path.** A focus that does `add_dynamic_modifier` without a `NOT = { has_dynamic_modifier = { modifier = X } }` guard double-applies when a second focus in the same plan adds the same modifier. Check every `add_dynamic_modifier` against all other focuses reachable in the same branch, not just the one focus in front of you.

### 3. Output

For each file reviewed, report:

1. **File**: path and file type.
2. **Issues**: numbered list with category labels (`[Economic]`, `[Political]`, `[Visual]`, `[Military]`, `[AI]`, `[Code]`, `[Variety]`, `[Misc]`) and line numbers where applicable.
3. Mark anything that must be fixed before merge as **[blocker]**.

End with a total issue count per category, or "No content issues found."
