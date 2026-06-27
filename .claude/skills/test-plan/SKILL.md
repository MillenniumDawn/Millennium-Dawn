---
name: test-plan
description: Generate an approximate playthrough test plan for the current branch in AngriestBird PR format. Run after /open-pr to attach a test plan, or standalone to draft test steps for a diff.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

Generate an **approximate**, best-effort playthrough test plan for the current branch, in the AngriestBird PR format. The model cannot run the game, so the output is a draft the human verifies and trims before trusting it.

Arguments (optional, space-separated):

- Issue numbers the plan should cover, e.g. `1354 1261`

Requested arguments: $ARGUMENTS

## Steps

### 1. Gather context

```
git rev-parse --abbrev-ref HEAD
git log origin/main..HEAD --oneline
git diff origin/main...HEAD --stat
git diff origin/main...HEAD
```

If the branch has no commits ahead of `main`, stop: "No commits ahead of main, nothing to test."

For each issue number in `$ARGUMENTS`, run `gh issue view <N> --repo MillenniumDawn/Millennium-Dawn --json number,title,body` to label which checks cover which issue. If `gh` errors, skip that number.

### 2. Derive the tests

From the diff, identify the affected country tags and systems (focus tree, events, decisions, ideas, AI, GUI, etc.). For each, infer the concrete in-game action a tester would take and the outcome they should confirm. Group checks into **playthroughs** keyed by country tag and start year (a tester loads one save and runs all its checks together). Keep every check grounded in what actually changed in the diff. Do not invent coverage for untouched systems.

### 3. Emit the test plan block

Use this exact structure:

```
### Test plan

**Playthrough A: <TAG> <year> (covers #N, #M)**

<phase header, e.g. "Game start, before unpausing:">

- [ ] `tag <TAG>`, <action>, confirm <expected outcome> (#N).
- [ ] <next checkbox> (#M).

<next phase header, e.g. "Mid-game checks (advance several in-game weeks first):">

- [ ] <action>, confirm <expected outcome> (#N).

**Playthrough B: <TAG> <year> (covers #X)**

- [ ] <action>, confirm <expected outcome> (#X).
```

Rules:

- Each playthrough block starts with a bold header naming the country tag, start year, and issues it covers, e.g. `**Playthrough A: ENG 2000 (covers #1400, #1515, #1516)**`. Group checks under phase sub-headers when a check needs setup beyond game start (e.g. `Game start, before unpausing:` vs `Mid-game checks (advance several in-game weeks first):`).
- Every check is a markdown task list item: start with `- [ ]`, never bare `- `. One checkbox per distinct in-game action. End each with the issue ref it covers, `(#N)`.
- Checkbox structure: console command (if any) in backticks, then the action, then `confirm <expected outcome>`. Separate clauses with commas or periods, not `→` or `—`. Example: ``- [ ] `tag UKR`, hover an internal faction the country does not have, confirm the preview tooltip opens with the shared header (#1516).``
- Single-issue or single-tag work may use one playthrough block. Skip phase sub-headers if every check happens at game start. The `- [ ]` rule still applies.
- **Never use em dashes (`—`, U+2014) anywhere.** Use a colon, period, or comma. Standing user rule.

### 4. Output

1. Print the test plan block for the user to paste.
2. If a PR already exists for the branch (`gh pr view --repo MillenniumDawn/Millennium-Dawn --json number,body`), offer to append the `### Test plan` section to the PR body via `gh pr edit`. Do not overwrite an existing test plan without confirmation.
3. State plainly that the plan is approximate and needs human review before it is trusted.
