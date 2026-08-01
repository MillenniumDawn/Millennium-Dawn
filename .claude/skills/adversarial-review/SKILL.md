---
name: adversarial-review
description: "Adversarial edge-case hunt over the branch diff or a single file: challenges every change for unhandled scenarios, silent failures, scope/timing/variable traps, and logic gaps rule-based review misses. Use when asked to adversarially review, stress-test, or find edge cases in a change."
---

Run an adversarial edge-case review on the current branch diff or a single file. Actively challenge every change by asking "what could go wrong?" and hunt for unhandled scenarios, silent failures, and logic gaps that rule-based reviews miss.

**Syntax:** `/adversarial-review [file_path]`

- With `file_path`: adversarial review on that file.
- Without argument: adversarial review on all changed files on the current branch vs `main`.

## Role

You are the adversarial reviewer. Don't verify compliance against known rules. Imagine every way the change could break in practice and force the author to defend or fix it.

## Execution

### 1. Gather context

- `git log origin/main..HEAD --oneline`
- `git diff origin/main...HEAD`
- Identify changed files and their types.

### 1a. Dispatch tools-reviewer for any tools/\*\* changes

If `git diff --name-only origin/main...HEAD` includes any path under `tools/` (linting, validation, standardization, shared_utils, etc.), dispatch the `tools-reviewer` subagent in parallel with your own review of content files. Pass it the list of changed tooling files.

The tools-reviewer covers Python-specific concerns (Correctness, Duplication, Performance, Robustness, Consistency, Style, Wiring) that this skill's HOI4-scripting checklists do not. Fold its findings into your final report for a single combined review.

Skip this step when no `tools/**` files changed.

### 2. Challenge every changed block

Apply the full catalog in `.claude/docs/bug-patterns.md` — both the "Adversarial questions" and "Scan patterns" sections — plus every pattern in `.claude/rules/general-rules.md` § Scripting Patterns. For each question, if the answer is "no, it's not handled", flag it.

### 3. Output

For each file reviewed, report:

1. **File** — path and type.
2. **Issues** — numbered list with category labels (`[Scope]`, `[Timing]`, `[Variable]`, `[Silent]`, `[Cross-Country]`, `[GUI]`, `[Content]`) and line numbers.
3. **Edge case** — the exact scenario that breaks.
4. **Impact** — what happens to the player or game state when it hits.
5. **Suggested defense** — guard, rewrite, or note if the omission is intentional.

Mark anything that could corrupt save state, soft-lock the player, or crash the GUI as **[critical]**.

End with total count or "No adversarial issues found — the author handled all edge cases."
