---
name: open-pr
description: Create a draft PR with a BLUF body, linked issues, and the Changelog.txt line for the branch.
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Glob
  - Grep
---

Create a draft PR for the current branch.

Arguments (optional, space-separated): issue numbers to close (`1354 1261`) and a quoted
title override (`"Fix Cuba AI and Egypt bugs"`).

Requested arguments: $ARGUMENTS

## Steps

### 1. Read the branch

```
git rev-parse --abbrev-ref HEAD
git log origin/main..HEAD --oneline
git diff origin/main...HEAD --stat
git diff origin/main...HEAD
```

With no commits ahead of `main`, stop: "No commits ahead of main, nothing to open a PR
for."

### 2. Issues

Bare integers in `$ARGUMENTS` are issues to close. For each, run
`gh issue view <N> --repo MillenniumDawn/Millennium-Dawn --json number,title,body,labels`
and use it to describe the change accurately. Skip a number `gh` cannot read and say so.

With no issue numbers, collect `#N` references from the commit messages as candidates.
Do not add `Closes` lines for them. Report them at the end.

### 3. Title

Use the quoted title verbatim. Otherwise use the most descriptive commit subject, under
70 characters, and append `(#N, #M)` when issues were given.

### 4. Body

BLUF format, as `AGENTS.md` requires:

```
## Bottom line

One or two sentences: what changes for the player, and anything the reviewer must know.

## How

- Only for details that are not obvious from the bottom line.

Closes #N

BLUF
```

- Start with `## Bottom line` and end with `BLUF` on its own line.
- Lead with the outcome the player sees, not the implementation. No root-cause
  narration, file paths, or commit hashes in the bottom line.
- Add `## Why` only when the reason is not obvious. Add `## How` only for non-obvious
  details, as plain one-line bullets. Omit empty sections.
- Say what was checked and what was not, such as "Not tested in game."
- One `Closes #N` per line, above `BLUF`. When different bullets close different
  issues, append `Closes #N` to the bullet it belongs to.
- No test plan in the body. `/test-plan` adds one when asked.
- Never use em dashes in the title, body, or changelog.

### 5. Changelog

For game-file changes not yet listed, add the one BLUF line through `/changelog` and
commit it separately as `Update Changelog.txt` before creating the PR. Skip this when
the diff has no game files, and say so.

### 6. Push and create

```
git push -u origin HEAD
gh pr create --draft --repo MillenniumDawn/Millennium-Dawn --title "<title>" --body-file <file>
```

Write the body to a scratch file and pass it with `--body-file`.

### 7. Report

1. The PR URL.
2. The changelog line added, or why it was skipped.
3. Any `#N` candidates found in commits, with: "To link these issues, re-run as
   `/open-pr N M`."
