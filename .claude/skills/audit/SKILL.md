---
name: audit
description: "Comprehensive pre-merge review of one file or the whole branch diff: dispatches parallel reviewer agents (correctness, adversarial edge cases, performance, simplification, content) and merges findings. Use when asked to audit or fully review a branch or file."
---

**Syntax:** `/audit [file_path]`. With a path, review that file. Without one, review
every file the branch changes against `main`.

## 1. Gather context once

Gather the diff and file contents once, in this agent, and pass them to the reviewers
inline. Reviewers do not re-run `git` or re-read shared docs.

- File mode: read the file, note its subsystem and hot-path exposure, and identify the
  files it calls or is called by.
- Branch mode: `git diff origin/main...HEAD`, `git log origin/main..HEAD --oneline`, and
  `git diff --name-only origin/main...HEAD`.

Skip generated and binary assets.

## 2. Pick the lanes

- Trivial change (one small file, under about 80 changed lines, no hot path or
  cross-country logic): review it inline. Dispatch at most one focused agent.
- Localisation only: `localisation-editor` and `performance-analyzer`.
- Normal change: the lanes below, minus any with nothing in scope.

## 3. Launch the reviewers in parallel

Send every applicable lane in one message. Tell each one to report findings only.

- `code-quality-reviewer`: correctness, standards, readability, localisation.
- Adversarial edge cases: `head-mod-developer`, applying
  `.claude/docs/bug-patterns.md`.
- `performance-analyzer`: `.claude/docs/performance-patterns.md`.
- `simplify-analyzer`: simplification opportunities.
- Content design: `head-mod-developer`, checking against
  `.claude/docs/content-guidelines.md` and the two guides it names. Skip categories that
  do not apply to the file type.
- `tools-reviewer`: only when `tools/**` changed. Dispatch it here, never from inside
  another lane.

## 4. Merge the findings

Wait for every lane, then report per file:

1. File summary: purpose and hot-path exposure, in one sentence.
2. Correctness and standards.
3. Edge cases. Mark save-corruption, soft-lock, and crash risks `[critical]`.
4. Performance, with severity.
5. Simplification.
6. Content, with category labels and `[blocker]` tags.
7. Cross-cutting concerns.
8. Action items, blockers and criticals first, with file and line.

Drop empty sections. When two lanes flag the same line, keep one entry with both
reasons, or the more detailed explanation when the reason is the same. Never drop a
finding because it appears twice. Flag an uncertain finding for human review.

When the branch has an open PR, check that its title and body describe what the diff
changes. A mismatch, or a missing body, is a blocker. Name what the body claims that the
diff lacks and what the diff contains that the body omits.

## 5. Apply fixes when asked

Edit in place, criticals first. Stay within the reviewed files. Verify by re-reading
the changed lines. Do not re-dispatch the lanes or run validators unless asked.
