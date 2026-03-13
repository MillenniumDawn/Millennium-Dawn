Find an open GitHub issue that is actionable and fix it, then open a pull request.

Supported arguments: an issue number to fix a specific issue, or none to auto-select one.
Requested arguments: $ARGUMENTS

Steps:

1. **Find an issue to fix**

   If an issue number is given, fetch it directly:

   ```
   gh issue view <number> --json title,body,labels,comments
   ```

   Otherwise, list open bugs and pick one that is not already covered by an open PR:

   ```
   gh issue list --state open --limit 40
   gh pr list --state open
   ```

   Prefer issues labelled `bug` with a clear reproduction path. Skip issues that already have an open PR or are vague with no reproduction steps.

2. **Understand the bug**

   Read the issue body carefully. Identify:
   - The specific behaviour that is wrong
   - The expected behaviour
   - Any country, decision, event, or system named in the report

3. **Locate the relevant code**

   Search for the named decisions, effects, triggers, scripted GUIs, or on_actions:

   ```
   grep -rn "keyword" common/ events/ --include="*.txt" -l
   ```

   Read the files involved. Understand the data flow before touching anything.

4. **Diagnose the root cause**

   Trace through the logic to find exactly where the wrong value is produced or the wrong branch is taken. Do not guess — confirm the cause in the code before writing a fix.

5. **Fix the bug**

   Make the minimal change needed. Follow all rules in CLAUDE.md:
   - Tabs for indentation
   - No magic numbers — use variables
   - No empty blocks, no commented-out code
   - Only add a comment if the fix is non-obvious

   Do not refactor surrounding code or fix unrelated issues in the same commit.

6. **Commit**

   Create a branch, stage only the files changed for this fix, and commit:

   ```
   git checkout -b fix/<short-description>
   git add <files>
   git commit -m "Fix <short description> (#<issue number>)

   <one or two sentences explaining root cause and fix>

   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

7. **Ensure branch is up to date**

   Run `git merge origin/main` and ensure the branch is up to date before creating a changelog entry or a pull request.

8. **Update the changelog**

   Run `/changelog` to add an entry for the fix under the current version in `Changelog.txt`. Commit the changelog update separately.

9. **Open a pull request**

   Push the branch and create a PR that closes the issue:

   ```
   git push -u origin <branch>
   gh pr create --title "Fix <short description> (#<issue number>)" --body "..."
   ```

   PR body must include:
   - Closes #<issue number>
   - **Root cause** — what was wrong and why
   - **Fix** — what was changed and how it resolves it
   - **Test plan** — steps to verify the fix in-game

10. **Report back**

Output the PR URL and a one-paragraph summary of the root cause and fix.
