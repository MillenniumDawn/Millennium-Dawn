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

For each file in scope, check the categories in `.claude/docs/content-guidelines.md` (Economic, Political, Visual, Military, AI, Code, Miscellaneous). Skip categories that don't apply to the file type (no admiral counts in a decisions file, no building costs in a character file).

### 3. Output

For each file reviewed, report:

1. **File**: path and file type.
2. **Issues**: numbered list with category labels (`[Economic]`, `[Political]`, `[Visual]`, `[Military]`, `[AI]`, `[Code]`, `[Misc]`) and line numbers where applicable.
3. Mark anything that must be fixed before merge as **[blocker]**.

End with a total issue count per category, or "No content issues found."
