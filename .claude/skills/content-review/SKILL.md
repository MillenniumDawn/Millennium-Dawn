---
name: content-review
description: "Check a file or the branch diff against the full MD content review checklist (economic, political, visual, military, AI, code) with blocker tags. Use when asked to content-review country content or verify content-guideline compliance before merge."
---

**Syntax:** `/content-review [file_path]`. With a path, review that file. Without one,
review every file the branch changes against `main`.

## 1. Gather context

- File mode: read the file and identify its type.
- Branch mode: `git diff origin/main...HEAD` and `git log origin/main..HEAD --oneline`.

Read `docs/src/content/resources/content-review-guide.md`,
`docs/src/content/resources/new-general-guidelines.md`, and
`.claude/docs/content-guidelines.md`. The first two are the full checklist. The third is
a summary.

## 2. Apply the checklist

Check each file against the categories in `content-guidelines.md`. Skip categories that
do not apply to the file type.

For a focus tree, run the Variety check as a comparison against Iran
(`05_iran.txt`) or Spain (`05_spain.txt`), not in isolation.

Sweep the whole file for these three. Sampling undercounts them:

- Treasury double-charge. The scripted building effects (`one_random_arms_factory`,
  `two_random_*`, `one_office_construction`, and the rest in
  `common/scripted_effects/`) charge treasury themselves unless
  `set_temp_variable = { skip_payment = 1 }` is set first. A focus that calls one and
  also adds an explicit `treasury_change` with `modify_treasury_effect` pays twice. A
  raw `add_building_construction` with one explicit charge is correct.
- Referenced loc keys. Check that every `tooltip = <key>`, idea key, and modifier `_tt`
  key the tree references resolves in `localisation/english/`, not only the keys the
  diff adds.
- Dynamic-modifier first add. An `add_dynamic_modifier` without a
  `NOT = { has_dynamic_modifier = { modifier = X } }` guard double-applies when another
  focus reachable in the same branch adds the same modifier.

## 3. Output

Per file: the path and type, then a numbered issue list with category labels
(`[Economic]`, `[Political]`, `[Visual]`, `[Military]`, `[AI]`, `[Code]`, `[Variety]`,
`[Misc]`) and line numbers. Mark anything that must be fixed before merge `[blocker]`.
End with a count per category, or "No content issues found."

When the branch has an open PR, a title or body that does not match the diff is a
`[blocker]`. Name what the body claims that the diff lacks and what the diff contains
that the body omits. A missing body counts.
