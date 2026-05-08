Run a comprehensive code-quality, performance, and content audit on a single file or the entire branch diff.

**Syntax:** `/audit [file_path]`

- With `file_path`: audit that specific file for simplification opportunities, performance issues, and content design problems.
- Without argument: audit all changed files on the current branch against `main`.

## Execution

### 1. Gather context

**File mode** (user provided a path):

- Read the file to understand its subsystem and hot-path exposure (daily on_action, per-frame GUI, player event, AI event, etc.).
- Identify related files it calls or is called by (scripted effects, triggers, events, GUI, loc).

**Branch mode** (no argument):

- Get the full diff: `git diff origin/main...HEAD`
- Get the commit log: `git log origin/main..HEAD --oneline`
- Identify the list of changed files.

### 2. Launch all three analyzers in parallel

Use the Agent tool to launch **all three agents in a single message** so they run concurrently.

**Agent 1: `simplify-analyzer`**

- Pass the file path or the branch diff.
- Instruct it to apply the `/simplify` skill and report what it found.

**Agent 2: `performance-analyzer`**

- Pass the file path or the branch diff.
- Instruct it to scan for the 8 performance anti-patterns from `.claude/docs/performance-patterns.md`.

**Agent 3: `general-purpose` (content review)**

- Pass the file path or the branch diff.
- Instruct it to apply the `/content-review` skill: read `docs/src/content/resources/content-review-guide.md`, `docs/src/content/resources/new-general-guidelines.md`, and `.claude/docs/content-guidelines.md`, then check every changed file against the full checklist (Economic, Political, Visual, Military, AI, Code, Miscellaneous categories).
- For file mode, skip categories that don't apply to the file type (e.g., skip Military checks on a decisions file).

### 3. Wait for all three agents to complete

All three agents must report back before proceeding to the merge step.

### 4. Merge and deduplicate findings

Combine all three reports into a single structured output.

**Deduplication rules:**

- If multiple agents flag the same line for different reasons, list both reasons under one entry.
- If multiple agents flag the same line for the same underlying issue, keep the more detailed explanation.
- Never drop a finding just because it appears in multiple reports.

**Output structure:**

For each file reviewed, report:

1. **File summary** — one sentence on purpose and hot-path exposure.
2. **Simplification findings** — numbered list of issues found by `simplify-analyzer`.
3. **Performance findings** — numbered list of issues found by `performance-analyzer`, with severity (Critical / High / Medium / Low).
4. **Content findings** — numbered list of issues found by the content-review agent, with category labels (`[Economic]`, `[Political]`, etc.) and `[blocker]` tags where applicable.
5. **Cross-cutting concerns** — issues that touch multiple categories (e.g., "Replace 15 `if/else_if` branches with array lookup" improves both simplification and performance).
6. **Action items** — prioritized list of what to fix first, with file and line numbers. Blockers first.

### 5. Apply fixes (if user confirms)

If the user asks to fix the issues, apply them directly:

- **Simplification fixes** — edit files in place (use Edit/Write tools).
- **Performance fixes** — edit files in place.
- **Critical issues** — fix first, even if they require structural changes.
- **Non-critical** — fix in order of impact.

After applying fixes, re-run the audit on the changed files to verify no regressions.

## Important Notes

- **Do not** run the agents sequentially — always launch all three in parallel.
- **Do not** modify files outside the scope of the audit.
- **Do not** run validators after fixing unless explicitly asked.
- When uncertain about a finding, flag it for human review rather than applying blindly.
- For branch mode, focus on files that are part of the branch diff. Do not audit unchanged files unless the user explicitly asks.
- If a file is a generated or binary asset (`.dds`, `.png`, etc.), skip it.
- If a file is a localisation file (`.yml`), run the `focus-localisation-editor` agent with `model: "haiku"` instead of `simplify-analyzer` for the simplification pass — haiku is sufficient for typo and grammar scanning and keeps costs low. Still run `performance-analyzer` for loc performance (e.g., undefined variable substitutions, excessive nested formatters).
- The content-review agent should skip Military checks for non-character/non-OOB files and skip Economic checks for non-focus-tree files. Instruct it accordingly in the prompt you pass.
- When reviewing script files, flag unnecessary scope expansion (e.g., `TAG = { exists = yes }` instead of `country_exists = TAG`) — these are both readability and performance issues.
