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

Use the title and body to write an accurate root-cause sentence in the summary. If `gh` errors (not found or private), note the failure and skip that number.

### 4. Derive the PR title

If the user supplied a quoted title, use it verbatim.

Otherwise: strip a `fix/`, `feature/`, `chore/`, or `content/` prefix from the branch name, replace hyphens and underscores with spaces, title-case each word, then append `(#N, #M)` if issue numbers were given.

Examples:

- Branch `fix/cuba-egypt-bugs` + issues 1354, 1261 → `"Fix Cuba Egypt Bugs (#1354, #1261)"`
- Branch `thegeneral-uk` (no prefix): prefer the most descriptive commit subject line as the title.

For a personal fork branch with no clear description (e.g. `thegeneral-uk`), derive the title from the most descriptive commit subject in the log. Keep it under 70 characters.

### 5. Compose the PR body

Use this exact structure (AngriestBird format):

```
Closes #N
Closes #M

### Summary

#### Bug Fixes

- **Fixes #N: [Issue Title].** [Root cause in 1-2 sentences, specific: name focus ID, event ID, wrong value vs. correct value, using `backtick` for code identifiers.]

#### [Other grouping, e.g. "AI", "Content", "Localisation", "Validation"]

- **[Component or focus/event ID].** [What was added or changed and why.]
```

Rules:

- Include `Closes #N` lines only when issue numbers were given. Place them above `### Summary` with one blank line between the last close and `### Summary`.
- `#### Bug Fixes`: one bullet per distinct fix. Group micro-changes (e.g. "Fixed 12 log copy-paste errors") into a single bullet.
- Other subsections (`#### AI`, `#### Content`, etc.): include only if there are non-bug changes in that category.
- **Never use em dashes (`—`, U+2014) anywhere: not in the PR title, body, bullet separators, Changelog.txt, or any `.yml` file.** Replace with a colon (introducing the explanation), a period (ending the bolded prefix, new sentence), or a comma (continuing the clause). Standing user rule, no exceptions even when mimicking AngriestBird's example PRs.
- Bullet structure: bold the issue ref and title together followed by a period (`**Fixes #N: Issue Title.**`), a space, then the description. No `—` separator.
- Bullet length: **2 sentences, 2-3 lines max** per fix (one for cause, one for resolution). Name the key focus/event/decision ID and the wrong-vs-right value; skip commit hashes, file:line citations, repro chains, and regression notes (those go in the commit and issue). The `Closes #N` lines are always preserved.
  The test plan is **not** part of the PR body. After creating the PR, run `/test-plan` to generate and attach an approximate playthrough checklist (`.claude/skills/test-plan/SKILL.md`).

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
