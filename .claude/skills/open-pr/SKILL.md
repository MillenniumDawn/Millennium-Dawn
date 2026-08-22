---
name: open-pr
description: Create a draft PR with an AngriestBird-style summary, link issues, update Changelog.txt for unlisted changes, and report what issue numbers are needed.
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Glob
  - Grep
---

Create a draft PR for the current branch with an AngriestBird-style summary, linked GitHub issues, and changelog entries for any changes not yet listed in `Changelog.txt`.

Arguments (optional, space-separated):

- Issue numbers to close, e.g. `1354 1261`
- A quoted PR title override, e.g. `"Fix Cuba AI and Egypt bugs"`

Requested arguments: $ARGUMENTS

## Steps

### 1. Read branch state

```
git rev-parse --abbrev-ref HEAD
git log origin/main..HEAD --oneline
git diff origin/main...HEAD --stat
git diff origin/main...HEAD
```

If the branch has no commits ahead of `main`, stop: "No commits ahead of main, nothing to open a PR for."

### 2. Parse arguments

From `$ARGUMENTS`:

- Bare integers are issue numbers to close.
- Any double-quoted string is the PR title override.

If no issue numbers were given: scan the step-1 commit messages for `#N` patterns and collect them as candidates. Do NOT fail; continue without `Closes #N` lines. At the end, tell the user which issue numbers you found in commits and prompt them to re-run as `/open-pr N M` to link them.

### 3. Fetch linked issues

For each issue number from step 2, run:

```
gh issue view <N> --repo MillenniumDawn/Millennium-Dawn --json number,title,body,labels
```

Use the title and body to name the change accurately in one bullet. If `gh` errors (not found or private), note the failure and skip that number.

### 4. Derive the PR title

If the user supplied a quoted title, use it verbatim.

Otherwise: strip a `fix/`, `feature/`, `chore/`, or `content/` prefix from the branch name, replace hyphens and underscores with spaces, title-case each word, then append `(#N, #M)` if issue numbers were given.

Examples:

- Branch `fix/cuba-egypt-bugs` + issues 1354, 1261 → `"Fix Cuba Egypt Bugs (#1354, #1261)"`
- Branch `thegeneral-uk` (no prefix): prefer the most descriptive commit subject line as the title.

For a personal fork branch with no clear description (e.g. `thegeneral-uk`), derive the title from the most descriptive commit subject in the log. Keep it under 70 characters.

### 5. Compose the PR body

Use this exact structure (the project's real format, confirmed across recent merged PRs):

```
### Changes
- Adds Overall Productivity + Monthly Productivity Growth to toolbar options
- Adds lists of all options for any dropdown menu list

Closes #N
```

Rules:

- Single `### Changes` heading. No `### Summary`, no `#### ` subsections, no grouping by category.
- One bullet per user-visible change, one line each. Plain sentence, no bold prefixes, no quoted issue titles, no root-cause narration, no file paths, no `file:line`, no commit hashes, no focus/event/decision IDs unless the ID is the only way to name the thing.
- Describe the outcome the player sees, not the implementation.
- Group micro-changes (e.g. "Fixed 12 log copy-paste errors") into a single bullet.
- Default placement: `Closes #N` goes at the bottom, one blank line after the last bullet, one `Closes #N` per line for multiple issues (see PR #2523).
- If different bullets close different issues, skip the trailing block instead: append the closure to the bullet it belongs to, either on the same line (`- Fixed the debt repayment bug - Closes #2486`) or, when one bullet closes more than one issue, as indented sub-lines (`  - Closes #2492` / `  - Closes #2355`). See PR #2598 and #2515.
- **Never use em dashes (`—`, U+2014) anywhere: not in the PR title, body, bullets, Changelog.txt, or any `.yml` file.** Standing user rule, no exceptions.
- The test plan is **not** part of the PR body. After creating the PR, run `/test-plan` to generate and attach an approximate playthrough checklist (`.claude/skills/test-plan/SKILL.md`).

### 6. Check and update `Changelog.txt`

Apply the `/changelog` process (`.claude/skills/changelog/SKILL.md`) to add entries for any branch changes not already listed: identify the top-most version heading, reuse only the file's existing categories (never invent one), and insert past-tense `  - [TAG] ...` bullets with no em dashes. Skip changes already present (grep the focus/event/decision ID or `Issue #N`).

If entries were added, stage and commit them separately **before** creating the PR:

```
git add Changelog.txt
git commit -m "Update Changelog.txt"
```

If `Changelog.txt` is already up to date, skip this step and note "Changelog already up to date."

### 7. Push and create the draft PR

Push the branch if not already on the remote:

```
git push -u origin HEAD
```

Then create the draft PR:

```
gh pr create --draft \
  --repo MillenniumDawn/Millennium-Dawn \
  --title "<title from step 4>" \
  --body "$(cat <<'EOF'
<body from step 5>
EOF
)"
```

### 8. Report back

Output:

1. The PR URL.
2. Whether `Changelog.txt` was updated and which entries were added, or "Changelog already up to date."
3. If **no** issue numbers were provided: list any `#N` references found in commits and tell the user: "To link these issues, re-run as `/open-pr N M`."
4. Remind the user the PR body has no test plan by design: "Run `/test-plan` to generate and attach an approximate playthrough checklist."
