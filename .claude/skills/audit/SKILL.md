Run a comprehensive review of a single file or the entire branch diff (correctness, edge cases, simplification, performance, and content design) by dispatching the canonical reviewers in parallel and merging their findings. This is the single Millennium Dawn pre-merge review command; it absorbs the former `/review-branch`.

**Syntax:** `/audit [file_path]`

- With `file_path`: review that file.
- Without argument: review all changed files on the current branch against `main`.

## Execution

### 1. Gather context once

Gather the diff and file contents **a single time in this (the main) agent**, then hand them to the reviewers inline. The reviewers must not re-run `git`, re-read the diff, or re-read shared reference docs — duplicated context-gathering across agents is the main token sink this skill avoids.

**File mode** (path provided):

- Read the file. Note its subsystem and hot-path exposure (daily on_action, per-frame GUI, player event, AI event, etc.).
- Identify related files it calls or is called by (scripted effects, triggers, events, GUI, loc).

**Branch mode** (no argument):

- `git diff origin/main...HEAD` and `git log origin/main..HEAD --oneline` — run these **once**, here.
- `git diff --name-only origin/main...HEAD` to get the file list and their types.

### 2. Decide the lane set

Don't fan out every reviewer on every change. Scale to the size and type of what changed:

- **Trivial change** (a single small file, roughly < 80 changed lines, with no hot-path or cross-country logic): skip the fan-out. Review it inline in this agent. Dispatch at most one focused agent if a specialised pass is clearly warranted.
- **Pure localisation** (`.yml` only): run **`localisation-editor`** (defaults to haiku — fine for typo/grammar) and **`performance-analyzer`** (undefined variable substitutions, excessive nested formatters). Skip the other lanes.
- **Normal change**: run the lanes in step 3, but **drop any lane with nothing in scope** — e.g. skip the content lane on a tools-only or pure-code diff, skip the simplification lane on a file with no branching, skip the tools lane unless `tools/**` changed.

### 3. Launch the applicable reviewers in parallel

Launch all applicable lanes **in a single message** so they run concurrently. Pass each agent the file path (file mode) or the already-gathered diff (branch mode) inline. Each lane is a **focused agent**, not a `general-purpose` agent running a whole sub-skill, and each is told explicitly: do not re-run `git`, do not re-gather context, report findings only.

- **`code-quality-reviewer`** — rules, standards, correctness, readability, and localisation against project conventions.
- **Adversarial edge cases** — dispatch **`head-mod-developer`** (or `game-mod-developer`). Tell it to apply the checklist in `.claude/skills/adversarial-review/SKILL.md` (existence/scope guards, timing/state transitions, variable/array safety, silent NOPs) and hunt for edge cases, silent failures, and logic gaps rule-based review misses. It must **not** re-run git and must **not** dispatch `tools-reviewer` — the main agent handles tools (below).
- **`performance-analyzer`** — the anti-patterns from `.claude/docs/performance-patterns.md`.
- **`simplify-analyzer`** — simplification opportunities (collapse `if/else_if` chains, array lookups, dead code). For `.yml` loc, this lane is replaced by `localisation-editor` per step 2.
- **Content design** — dispatch **`head-mod-developer`** (or `game-mod-developer`). Tell it to read `docs/src/content/resources/content-review-guide.md`, `docs/src/content/resources/new-general-guidelines.md`, and `.claude/docs/content-guidelines.md` (once), then check the changed files against the full checklist (Economic, Political, Visual, Military, AI, Code, Miscellaneous). Skip categories that don't apply to the file type (no Military checks on a decisions file, no Economic checks on a character file). It must **not** re-run git.
- **`tools-reviewer`** — **only if** `tools/**` changed. Dispatch it directly here, in the same parallel batch, with the list of changed tooling files. Do not nest it under another lane.

### 4. Wait for all reviewers to complete

All dispatched lanes must report back before the merge step.

### 5. Merge and deduplicate findings

Combine all reports into a single structured output.

**Deduplication rules:**

- Multiple agents flag the same line for different reasons: list both reasons under one entry.
- Multiple agents flag the same line for the same underlying issue: keep the more detailed explanation (the adversarial lane usually names the breaking scenario, which is more actionable).
- Never drop a finding just because it appears in multiple reports.

**Output structure** — for each file reviewed, report:

1. **File summary** — one sentence on purpose and hot-path exposure.
2. **Correctness & standards** — from `code-quality-reviewer`.
3. **Edge cases** — from the adversarial lane; mark save-corruption, soft-lock, or crash risks `[critical]`.
4. **Performance** — from `performance-analyzer`, with severity (Critical / High / Medium / Low).
5. **Simplification** — from `simplify-analyzer`.
6. **Content** — from the content lane, with category labels (`[Economic]`, `[Political]`, etc.) and `[blocker]` tags where applicable.
7. **Cross-cutting concerns** — issues touching multiple categories (e.g., "replace 15 `if/else_if` branches with an array lookup" improves both simplification and performance).
8. **Action items** — prioritized fix list with file and line numbers. Blockers and criticals first.

Drop empty sections rather than writing "none".

### 6. Apply fixes (if user confirms)

If the user asks to fix the issues, apply them directly:

- **Correctness / simplification / performance fixes** — edit files in place (Edit/Write).
- **Critical issues** — fix first, even if they require structural changes.
- **Non-critical** — fix in order of impact.

After applying fixes, verify the edited regions by **re-reading the changed lines** — do not re-dispatch the reviewer lanes unless the user explicitly asks for a fresh full pass.

## Important Notes

- Gather the diff and shared docs **once** (step 1); hand them to reviewers inline. Never let a lane re-run `git` or re-read reference docs.
- **Do not** run the lanes sequentially — launch all applicable ones in parallel in a single message.
- **Do not** nest reviewers inside other reviewers. `tools-reviewer` is dispatched by the main agent, only when `tools/**` changed.
- **Do not** modify files outside the scope of the review.
- **Do not** run validators after fixing unless explicitly asked.
- When uncertain about a finding, flag it for human review rather than applying blindly.
- For branch mode, focus on files in the branch diff. Do not review unchanged files unless the user asks.
- Skip generated or binary assets (`.dds`, `.png`, etc.).
