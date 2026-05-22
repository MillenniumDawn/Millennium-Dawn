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

Create a draft Pull Request for the current branch with an AngriestBird-style summary, linked GitHub issues, and changelog entries for any changes not yet listed in `Changelog.txt`.

Arguments (optional, space-separated):
- Issue numbers to close, e.g. `1354 1261`
- A quoted PR title override, e.g. `"Fix Cuba AI and Egypt bugs"`

Requested arguments: $ARGUMENTS

---

## Steps

### 1. Read branch state

```
git rev-parse --abbrev-ref HEAD
git log origin/main..HEAD --oneline
git diff origin/main...HEAD --stat
git diff origin/main...HEAD
```

If the branch has no commits ahead of `main`, stop and tell the user: "No commits ahead of main — nothing to open a PR for."

### 2. Parse arguments

From `$ARGUMENTS`:
- Extract any bare integers → these are issue numbers to close.
- Extract any double-quoted string → use as PR title override.

If no issue numbers were given: scan the commit messages from step 1 for `#N` patterns and collect them as candidate references. Do NOT fail — continue without `Closes #N` lines. At the end of the skill, tell the user which issue numbers you found referenced in commits and prompt them to re-run as `/open-pr N M` to link them properly.

### 3. Fetch linked issues

For each issue number parsed in step 2, run:

```
gh issue view <N> --repo MillenniumDawn/Millennium-Dawn --json number,title,body,labels
```

Use the issue title and body to write an accurate root-cause sentence in the PR summary. If `gh` returns an error (issue not found or private), note the failure and skip that number.

### 4. Derive the PR title

If the user supplied a quoted title: use it verbatim.

Otherwise: strip a `fix/`, `feature/`, `chore/`, or `content/` prefix from the branch name, replace hyphens and underscores with spaces, title-case each word, then append `(#N, #M)` if issue numbers were given.

Examples:
- Branch `fix/cuba-egypt-bugs` + issues 1354, 1261 → `"Fix Cuba Egypt Bugs (#1354, #1261)"`
- Branch `thegeneral-uk` (no prefix) → use it as-is in title-case: `"Thegeneral Uk"` — but prefer the most descriptive commit subject line as the title instead.

If the branch name is a personal fork branch with no clear description (e.g., `thegeneral-uk`), derive the title from the most descriptive commit subject in the log. Keep it under 70 characters.

### 5. Compose the PR body

Use this exact structure (AngriestBird format):

```
Closes #N
Closes #M

### Summary

#### Bug Fixes

- **Fixes #N — [Issue Title]** — [root cause in 1–2 sentences, specific: name focus ID, event ID, wrong value vs. correct value, using `backtick` for code identifiers].

#### [Other grouping, e.g. "AI", "Content", "Localisation", "Validation"]

- **[Component or focus/event ID]** — [what was added or changed and why].

### Test plan

- [Imperative step: "Play [country], take [focus] → verify [outcome]"]
- [One bullet per distinct thing to verify in-game]
```

Rules:
- Include `Closes #N` lines only when issue numbers were given. Place them above `### Summary` with one blank line between the last close and `### Summary`.
- `#### Bug Fixes` subsection: one bullet per distinct fix. Group micro-changes (e.g., "Fixed 12 log copy-paste errors") into a single bullet.
- Other subsections (`#### AI`, `#### Content`, etc.): include only if there are non-bug changes in that category.
- Bold the issue reference or component name, then an em-dash (`—`) as separator. Em-dashes are allowed in the PR body markdown — do NOT use them in `Changelog.txt` or `.yml` files.
- Be specific: name the focus ID, event ID, incorrect value, correct value, and HOI4 effect or trigger involved.
- Test plan: one bullet per in-game action needed to verify correctness. Use the `→` arrow to separate action from expected result.

### 6. Check and update `Changelog.txt`

a. Read `Changelog.txt`. Identify the top-most version heading (e.g., `v2.0.0`) and collect all existing category headings (lines matching `^ [A-Za-z].*:$`). The valid categories are whatever is already in the file — do **not** invent new ones.

b. For each distinct change in the diff, check whether a matching entry already exists in `Changelog.txt` by searching for the focus/event/decision ID or the issue number (`Issue #N`). Use `grep` or `Grep` for this:

```
grep -n "focus_id_or_issue" Changelog.txt
```

c. For changes **not yet listed**: write entries in the changelog format and insert them under the correct existing category in the top-most version section. Format:
```
 Category:
  - [TAG] Past-tense verb. Specific object name. (Issue #N)
```
- 1 space before the category name.
- 2 spaces + `- ` before each entry.
- `[TAG]` prefix for country-specific changes; no prefix for global changes.
- Past tense, specific, no em-dashes.
- If a change does not fit any existing category, use the closest match (e.g., a localisation fix → ` Localization:`, a script fix → ` Bugfix:`).

d. If changes were added to `Changelog.txt`, stage and commit them separately **before** creating the PR:

```
git add Changelog.txt
git commit -m "$(cat <<'EOF'
Update Changelog.txt

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
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
