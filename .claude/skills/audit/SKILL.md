Run a comprehensive review of a single file or the entire branch diff (correctness, edge cases, simplification, performance, and content design) by dispatching the canonical reviewers in parallel and merging their findings. This is the single Millennium Dawn pre-merge review command; it absorbs the former `/review-branch`.

**Syntax:** `/audit [file_path]`

- With `file_path`: review that file.
- Without argument: review all changed files on the current branch against `main`.

## Execution

### 1. Gather context

**File mode** (path provided):

- Read the file to understand its subsystem and hot-path exposure (daily on_action, per-frame GUI, player event, AI event, etc.).
- Identify related files it calls or is called by (scripted effects, triggers, events, GUI, loc).

**Branch mode** (no argument):

- `git diff origin/main...HEAD`
- `git log origin/main..HEAD --oneline`
- Identify the list of changed files.

### 2. Launch all reviewers in parallel

Use the Agent tool to launch **all of these in a single message** so they run concurrently. Pass each the file path (file mode) or the branch diff (branch mode).

- **`code-quality-reviewer` agent** — rules, standards, correctness, readability, and localisation against project conventions.
- **`general-purpose` agent running the `adversarial-review` skill** — edge cases, silent failures, and timing/scope/variable hazards that rule-based review misses. It dispatches `tools-reviewer` itself for any `tools/**` changes.
- **`performance-analyzer` agent** — the performance anti-patterns from `.claude/docs/performance-patterns.md`.
- **`simplify-analyzer` agent** — simplification opportunities (collapse `if/else_if` chains, array lookups, dead code).
- **`general-purpose` agent (content review)** — applies the `/content-review` skill: read `docs/src/content/resources/content-review-guide.md`, `docs/src/content/resources/new-general-guidelines.md`, and `.claude/docs/content-guidelines.md`, then check every changed file against the full checklist (Economic, Political, Visual, Military, AI, Code, Miscellaneous). For file mode, skip categories that don't apply to the file type (e.g., skip Military checks on a decisions file).

### 3. Wait for all reviewers to complete

All must report back before the merge step.

### 4. Merge and deduplicate findings

Combine all reports into a single structured output.

**Deduplication rules:**

- Multiple agents flag the same line for different reasons: list both reasons under one entry.
- Multiple agents flag the same line for the same underlying issue: keep the more detailed explanation (the adversarial agent usually names the breaking scenario, which is more actionable).
- Never drop a finding just because it appears in multiple reports.

**Output structure** — for each file reviewed, report:

1. **File summary** — one sentence on purpose and hot-path exposure.
2. **Correctness & standards** — from `code-quality-reviewer`.
3. **Edge cases** — from `adversarial-review`; mark save-corruption, soft-lock, or crash risks `[critical]`.
4. **Performance** — from `performance-analyzer`, with severity (Critical / High / Medium / Low).
5. **Simplification** — from `simplify-analyzer`.
6. **Content** — from the content-review agent, with category labels (`[Economic]`, `[Political]`, etc.) and `[blocker]` tags where applicable.
7. **Cross-cutting concerns** — issues touching multiple categories (e.g., "replace 15 `if/else_if` branches with an array lookup" improves both simplification and performance).
8. **Action items** — prioritized fix list with file and line numbers. Blockers and criticals first.

### 5. Apply fixes (if user confirms)

If the user asks to fix the issues, apply them directly:

- **Correctness / simplification / performance fixes** — edit files in place (Edit/Write).
- **Critical issues** — fix first, even if they require structural changes.
- **Non-critical** — fix in order of impact.

After applying fixes, re-run the affected reviewers on the changed files to verify no regressions.

## Important Notes

- **Do not** run the agents sequentially — always launch them in parallel in a single message.
- **Do not** modify files outside the scope of the review.
- **Do not** run validators after fixing unless explicitly asked.
- When uncertain about a finding, flag it for human review rather than applying blindly.
- For branch mode, focus on files in the branch diff. Do not review unchanged files unless the user asks.
- Skip generated or binary assets (`.dds`, `.png`, etc.).
- For localisation files (`.yml`), run the `localisation-editor` agent (it defaults to haiku, which is sufficient for typo/grammar scanning and keeps costs low) instead of `simplify-analyzer` for the simplification pass. Still run `performance-analyzer` for loc performance (undefined variable substitutions, excessive nested formatters).
- The content-review agent should skip Military checks for non-character/non-OOB files and skip Economic checks for non-focus-tree files. Instruct it accordingly.
