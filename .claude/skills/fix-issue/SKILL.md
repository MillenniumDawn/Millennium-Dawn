---
name: fix-issue
description: 'Find an actionable open GitHub issue (or take an issue number or quoted task), implement the fix, commit, update the changelog, and open or update a PR. Use when asked to fix an issue or pick up work from the tracker, e.g. "/fix-issue 1354".'
---

Implement one actionable issue and open a pull request. Take only work that is small
and specified well enough to implement from the issue plus repo context, with no design
or balance decision left open.

Arguments: an issue number, a quoted task description, or none to auto-select.
Requested arguments: $ARGUMENTS

## 1. Pick the work

- A quoted task is the work item. Skip the issue search.
- An issue number: `gh issue view <number> --json title,body,labels,comments`.
- Otherwise list open issues and open PRs (`gh issue list --state open --limit 40`,
  `gh pr list --state open`) and pick an issue no open PR covers.

Eligible work is a bug with a clear reproduction, or a concrete task that names the
country, system, or files it touches and has a sibling implementation to mirror.

Skip the issue, and say why, when it is vague, needs a design or balance decision,
needs new art, audio, or map assets, spans many systems or countries, or is a large
feature. When in doubt, report it back.

With no actionable issue left, work through the "Scan patterns" section of
`.claude/docs/bug-patterns.md` instead.

Claim an issue that passes: `gh issue edit <number> --add-assignee @me`. Skip this for a
quoted task or a scanned bug.

## 2. Diagnose or plan

Read the issue, then the code it names, and understand the data flow before editing.

- Bug: trace where the wrong value or branch comes from. Confirm the cause in code. Do
  not guess.
- Task: find a sibling implementation and reuse its structure.

Produce an edit list: the exact files, blocks, and new text, with every value, name,
loc key, and ordering resolved. Note related out-of-scope problems and leave them alone.

## 3. Implement

Make the smallest change that resolves the issue. Follow `AGENTS.md` and the matching
`.claude/docs/` reference, and add every required loc key. Do not refactor nearby code
or fix unrelated problems in the same commit.

A one-line edit is made directly. For a larger edit list, the mechanical typing may go
to a `head-mod-developer` subagent with the edit list verbatim, an instruction to stay
within the listed files, and verification greps to report. Check its `git diff --stat`
before committing.

## 4. Commit

Always branch from `main`, never from whatever branch the session started on:

```
git fetch origin
git checkout -b <slug> origin/main
```

`<slug>` is a short kebab-case description, not an issue number. Stage only the files
for this work:

```
git commit -m "<Fix|Add|Implement> <short description> (#<issue>)" -m "<one or two sentences: the cause and fix, or what was added>"
```

Then `git merge origin/main` so the branch is current before the changelog and PR.

## 5. Changelog

Every PR that touches game files gets exactly one BLUF line in `Changelog.txt`, placed
by the `/changelog` rules and committed separately as `Update Changelog.txt`:

```
 - [TAG] <Past-tense verb> <what the player sees> (Issue #N)
```

Skip it only when the diff has no game files, and say so in the report.

## 6. Pull request

Push, then check for an open PR on the branch:

```
git push -u origin <branch>
gh pr list --head <branch> --state open --json number,url,body
```

- No open PR: hand off to `/open-pr <issue number>`. It owns the create path.
- An open PR exists: update its body in the `/open-pr` format with
  `gh pr edit <PR#> --body-file <file>`. Do not create a second PR. Keep every
  `Closes #N` line and any test-plan section already there.

Omit `Closes #` for a quoted task or a scanned bug.

## 7. Report

The PR URL, whether it was created or updated, the changelog line or why it was
skipped, and a short summary of what was fixed or added.
