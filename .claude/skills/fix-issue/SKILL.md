Find an open GitHub issue that is actionable and fix it, then open a pull request. If no actionable issues remain, scan the codebase for common bug patterns instead.

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

   **If no actionable GitHub issues remain** (all are too vague, graphical, engine-level crashes, or already covered), scan the codebase for common bug patterns instead. Examples of patterns to search for:
   - `swap_ideas` where `remove_idea` and `add_idea` are the same, or `remove_idea` doesn't match the `limit` condition
   - Event options with `name =` referencing a different event's ID (copy-paste errors)
   - Duplicate option names within the same event
   - `give_resource_rights` / `transfer_state` targeting wrong state IDs
   - Variables accumulated monthly without being reset first
   - Events sending responses to the wrong country (wrong FROM/PREV/ROOT scope)
   - `else_if` blocks with the same `limit` as the preceding `if` (unreachable code)
   - `tag` instead of `original_tag` in idea `allowed` blocks (breaks civil war tags)
   - `CONTROLLER` used in country scope (undefined — must be in state scope)
   - `set_cosmetic_tag = original_tag` (should be `drop_cosmetic_tag = yes`)
   - Missing `country_exists` guard before firing an event to a potentially non-existent tag
   - AND conditions in `cancel` or `available` blocks that can never simultaneously be true
   - `for_each_scope_loop` iterating over a variable-index array (use `for_each_loop` instead)
   - GUI buttons with a `trigger` block but no `effects` block (clicking does nothing)
   - OOB templates using equipment variants that the country cannot have at game start (wrong tech level or missing DLC variant)
   - Idea names with wrong capitalisation in `has_idea`/`add_ideas`/`remove_ideas` — HOI4 checks are case-sensitive and fail silently
   - `swap_ideas` removing and re-adding the same idea (no-op at final upgrade tier)
   - `else_if` with the same `limit` as the preceding `if` (unreachable — lives in shadow of the `if`)
   - `NOT = { A B }` blocks where two conditions should each have their own `NOT`
   - `threat > N` where N > 1 (threat is 0.0–1.0; whole-number comparisons are always false)
   - `not_locked_faction` trigger in faction rules (non-existent; use `is_locked_faction = no`)
   - Stacked multipliers producing near-zero denominators (clamp before division)
   - `add_building_construction` for naval base missing `province`
   - Scripted trigger defined twice in the same file (second definition silently overwrites first)
   - New subideology parties missing registration in `00_subideology_scripted_localisation.txt`

   When fixing codebase-scanned bugs, omit the `Closes #` line from the PR since there is no issue to reference.

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
