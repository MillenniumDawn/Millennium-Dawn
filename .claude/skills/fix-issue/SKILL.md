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

   Search for the named decisions, effects, triggers, scripted GUIs, or on_actions. If you can't find it, you do a wider database search:

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

   Never create or switch branches on your own. First check the current branch:

   ```
   git rev-parse --abbrev-ref HEAD
   ```

   - If the current branch is **`main`**: stop and use `AskUserQuestion` to ask the user which branch to use. Offer options: (a) check out an existing branch (user supplies the name), (b) create a new branch (user supplies the name). Only after the user answers do you run `git checkout <name>` or `git checkout -b <name>`. Do not invent a branch name.
   - If the current branch is **not `main`**: commit on the current branch. Do not switch, do not create a new branch.

   Then stage only the files changed for this fix and commit:

   ```
   git add <files>
   git commit -m "Fix <short description> (#<issue number>)

   <one or two sentences explaining root cause and fix>
   ```

7. **Ensure branch is up to date**

   Run `git merge origin/main` and ensure the branch is up to date before creating a changelog entry or a pull request.

8. **Update the changelog**

   Run `/changelog` to add an entry for the fix under the current version in `Changelog.txt`. Commit the changelog update separately.

9. **Open or update the pull request**

   Push the branch first:

   ```
   git push -u origin <branch>
   ```

   Then check whether an open PR already exists for this branch:

   ```
   gh pr list --head <branch> --state open --json number,url,body
   ```

   **a. If no open PR exists**: hand off to `/open-pr <issue number>`. That skill is the single source of truth for the create path — it writes the AngriestBird-format body, opens the draft PR, and handles the changelog. Do not duplicate its logic inline here.

   **b. If an open PR already exists**: rewrite its body in AngriestBird format and apply with `gh pr edit <PR#> --body "..."`. Do NOT create a second PR.

   When rewriting an existing PR body:
   - **Preserve every existing `Closes #N` line** at the top, then append a new `Closes #<this issue number>` for the fix you just made.
   - **Preserve every existing `#### Bug Fixes` bullet** — append a new bullet for this fix, never replace the prior bullets. Same for `#### Other`, `#### AI`, `#### Content`, etc. if present.
   - **Preserve every existing test-plan bullet** — append new bullets for the new fix.
   - If the existing body is in the older deep-dive format (root-cause code blocks, `file:line` citations, per-issue regression notes), normalise the whole body to AngriestBird format while still keeping every fact: each prior fix gets recomposed as a single bolded bullet in `#### Bug Fixes`, with the regression / file-citation details dropped (they live in the commits and the linked issues).
   - Follow `/open-pr` step 5 formatting rules: bold `**Fixes #N: Issue Title.**` prefix followed by a period, then 2 sentences (cause + resolution), 2–3 lines max, backticks for code identifiers, no em dashes (`—`) anywhere, no `→` separator. Use a colon, period, or comma instead.

   Apply with a heredoc to keep formatting intact:

   ```
   gh pr edit <PR#> --body "$(cat <<'EOF'
   <full rewritten body>
   EOF
   )"
   ```

10. **Report back**

Output the PR URL, whether the PR was **created** or **updated**, and a one-paragraph summary of the root cause and fix.
