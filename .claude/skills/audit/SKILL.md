Run a comprehensive code-quality, performance, and content audit on a single file or the entire branch diff.

**Syntax:** `/audit [file_path]`

- With `file_path`: audit that file for simplification opportunities, performance issues, and content design problems.
- Without argument: audit all changed files on the current branch against `main`.

## Execution

### 1. Gather context

**File mode** (path provided):

- Read the file to understand its subsystem and hot-path exposure (daily on_action, per-frame GUI, player event, AI event, etc.).
- Identify related files it calls or is called by (scripted effects, triggers, events, GUI, loc).

**Branch mode** (no argument):

- `git diff origin/main...HEAD`
- `git log origin/main..HEAD --oneline`
- Identify the list of changed files.

### 2. Launch all three analyzers in parallel

Use the Agent tool to launch **all three agents in a single message** so they run concurrently.

**Agent 1: `simplify-analyzer`** — pass the file path or branch diff. Instruct it to apply the `/simplify` skill and report what it found.

**Agent 2: `performance-analyzer`** — pass the file path or branch diff. Instruct it to scan for the 8 performance anti-patterns from `.claude/docs/performance-patterns.md`.

**Agent 3: `general-purpose` (content review)** — pass the file path or branch diff. Instruct it to apply the `/content-review` skill: read `docs/src/content/resources/content-review-guide.md`, `docs/src/content/resources/new-general-guidelines.md`, and `.claude/docs/content-guidelines.md`, then check every changed file against the full checklist (Economic, Political, Visual, Military, AI, Code, Miscellaneous). For file mode, skip categories that don't apply to the file type (e.g., skip Military checks on a decisions file).

### 3. Wait for all three agents to complete

All three must report back before the merge step.

### 4. Merge and deduplicate findings

Combine all three reports into a single structured output.

**Deduplication rules:**

- Multiple agents flag the same line for different reasons: list both reasons under one entry.
- Multiple agents flag the same line for the same underlying issue: keep the more detailed explanation.
- Never drop a finding just because it appears in multiple reports.

**Output structure** — for each file reviewed, report:

1. **File summary** — one sentence on purpose and hot-path exposure.
2. **Simplification findings** — numbered list from `simplify-analyzer`.
3. **Performance findings** — numbered list from `performance-analyzer`, with severity (Critical / High / Medium / Low).
4. **Content findings** — numbered list from the content-review agent, with category labels (`[Economic]`, `[Political]`, etc.) and `[blocker]` tags where applicable.
5. **Cross-cutting concerns** — issues touching multiple categories (e.g., "Replace 15 `if/else_if` branches with array lookup" improves both simplification and performance).
6. **Action items** — prioritized fix list with file and line numbers. Blockers first.

### 5. Apply fixes (if user confirms)

If the user asks to fix the issues, apply them directly:

- **Simplification fixes** — edit files in place (Edit/Write).
- **Performance fixes** — edit files in place.
- **Critical issues** — fix first, even if they require structural changes.
- **Non-critical** — fix in order of impact.

After applying fixes, re-run the audit on the changed files to verify no regressions.

## Important Notes

- **Do not** run the agents sequentially — always launch all three in parallel.
- **Do not** modify files outside the scope of the audit.
- **Do not** run validators after fixing unless explicitly asked.
- When uncertain about a finding, flag it for human review rather than applying blindly.
- For branch mode, focus on files in the branch diff. Do not audit unchanged files unless the user asks.
- Skip generated or binary assets (`.dds`, `.png`, etc.).
- For localisation files (`.yml`), run the `localisation-editor` agent with `model: "haiku"` instead of `simplify-analyzer` for the simplification pass — haiku is sufficient for typo/grammar scanning and keeps costs low. Still run `performance-analyzer` for loc performance (undefined variable substitutions, excessive nested formatters).
- The content-review agent should skip Military checks for non-character/non-OOB files and skip Economic checks for non-focus-tree files. Instruct it accordingly.
- When reviewing script files, flag unnecessary scope expansion (e.g., `TAG = { exists = yes }` instead of `country_exists = TAG`) — both readability and performance issues.
