---
name: adversarial-review
description: "Adversarial edge-case hunt over the branch diff or a single file: challenges every change for unhandled scenarios, silent failures, scope/timing/variable traps, and logic gaps rule-based review misses. Use when asked to adversarially review, stress-test, or find edge cases in a change."
---

**Syntax:** `/adversarial-review [file_path]`. Without a path, review every file the
branch changes against `main`.

Do not check compliance against known rules. Imagine every way the change could break
in practice.

## 1. Gather context

`git log origin/main..HEAD --oneline` and `git diff origin/main...HEAD`. Identify the
changed files and their types.

If the diff touches `tools/**`, dispatch `tools-reviewer` in parallel with the list of
changed tooling files, and fold its findings into the report.

## 2. Challenge every changed block

Apply both sections of `.claude/docs/bug-patterns.md`, plus the relevant parts of
`.claude/docs/scripting-edge-cases.md` and `.claude/docs/hoi4-data-structures.md`. Flag
every question whose answer is "no, it is not handled".

## 3. Output

Lead with the findings, or "No findings in the reviewed scope." Per file:

1. The path and type.
2. A numbered issue list with category labels (`[Scope]`, `[Timing]`, `[Variable]`,
   `[Silent]`, `[Cross-Country]`, `[GUI]`, `[Content]`) and line numbers.
3. For each issue: the exact scenario that breaks, what happens to the player or game
   state, and a suggested defense, or a note that the omission looks intentional.

Mark anything that could corrupt a save, soft-lock the player, or crash the GUI
`[critical]`. State what was not verified.

When the branch has an open PR, a title or body that does not match the diff is a
`[blocker]`. Name what the body claims that the diff lacks and what the diff contains
that the body omits. A missing body counts.

End with `BLUF`.
