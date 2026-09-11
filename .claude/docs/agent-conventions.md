# Agent Conventions

Read `AGENTS.md` at the start of every task. Its scope, KISS, validation, encoding,
and BLUF rules apply to every agent. Role files add only role-specific requirements.

## Scope and Reading

- Work on the caller's assigned files, issue, or diff. No idle scans or unrelated fixes
  unless requested. Trace shared consumers when needed without widening edit scope.
- Read the relevant definitions and callers, including nested effects and AI blocks.
  Use the task links in `AGENTS.md`; do not load every reference for every role.
- Reviewers read `known-false-positives.md` and the relevant domain reference before
  reporting a suspected bug. Scripting reviews also use `bug-patterns.md`.
- Read `performance-patterns.md` when execution frequency or scope expansion matters.
- English-localisation work uses `localisation-rules.md` and `typo-watchlist.md`.
- Tooling work uses `tools/README.md` and `validation-pipeline.md`, not game-script recipes.

Paths without a directory above are under `.claude/docs/`.

## Hand Back in BLUF Style

Lead with the result or blocker, then only the evidence the caller needs.

- Writers: changed behavior and `path:line`, checks actually run and their result,
  remaining work, and any in-game verification still needed. Do not paste whole files
  already edited; provide code blocks only when the caller requested a draft.
- Reviewers: findings ordered by severity, each with `path:line`, impact, and the
  smallest safe fix. Say no findings when clean. Do not invent issues to fill categories.
- Separate confirmed defects from uncertain observations. Never claim a check passed
  without running it. Omit empty headings and redundant counts.
- End the handoff with `BLUF`. Follow a requested machine-readable schema instead
  when a prose marker would invalidate it.

Severity: Critical means game-breaking or severe repeated runtime cost; High is a
correctness bug or significant cost; Medium is a smaller maintainability/performance
issue; Low is cosmetic. Judge frequency and reach, not syntax alone.

## Maintaining Agent Instructions

Keep each role to its purpose, task-specific reading, boundaries, and useful handoff
requirements. Do not copy scripting examples, toolchain versions, helper inventories,
or shared output templates into it. Update the owning reference instead.

Player instructions belong in `docs/src/content/pages/` or `tutorials/`; contributor
instructions belong in `docs/src/content/resources/`. Keep internal agent procedures
out of player guides. See `docs/CONTRIBUTING.md` for site links and content rules.
