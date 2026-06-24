Review all changes on the current branch compared to `main` and report issues across coding standards, performance, logic/correctness, and localisation. This skill is an **orchestrator**: it dispatches the canonical reviewers in parallel and merges their findings rather than carrying its own checklist (mirrors how `/audit` works), so the review rules live in exactly one place.

## Execution

### 1. Gather context

```
git log origin/main..HEAD --oneline
git diff origin/main...HEAD --stat
git diff origin/main...HEAD
```

Identify the changed files and their types. If the branch has no commits ahead of `main`, stop and say so.

### 2. Dispatch the reviewers in parallel

Launch both in a single message so they run concurrently:

- **`code-quality-reviewer` agent**: rules, standards, correctness, performance, readability, and localisation against project conventions (it reads `agent-conventions.md`, `general-rules.md`, `performance-patterns.md`, and for `.yml` files `localisation-rules.md` + `typo-watchlist.md`). Pass it `git diff main...HEAD` or the changed-file list.
- **`general-purpose` agent running the `adversarial-review` skill**: edge cases, silent failures, and timing/scope/variable hazards that rule-based review misses. It dispatches `tools-reviewer` itself for any `tools/**` changes. Pass it the branch diff context.

Wait for both before merging.

### 3. Content design (if applicable)

`adversarial-review` already covers content edge cases (free cores, buildings without monetary cost, cross-country agency). For the full content audit (economic balance, political neutrality, military, visual, AI game rules), tell the user to run `/content-review` rather than duplicating it here.

### 4. Merge findings

Combine both reports into a single report per file.

Deduplication rules:

- Same line, same underlying issue: keep the adversarial agent's explanation (it names the breaking scenario, which is more actionable).
- Same line, different reasons: list both under one entry.
- Never drop a finding just because it appears in both reports.

### 5. Output

List issues per file with line numbers. Flag crash, broken-state, or soft-lock risks as **critical**. End with a total count or "No issues found".
