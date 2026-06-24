Find an actionable open GitHub issue (a bug, or a well-scoped task or content request), implement it, then open a pull request. Only take on work small and well-specified enough to implement confidently from the issue plus repo context, with no design or balance decisions left open. If no actionable issue remains, scan the codebase for common bug patterns instead.

Supported arguments: an issue number, a short task description in quotes (for well-scoped work with no GitHub issue), or none to auto-select an issue.
Requested arguments: $ARGUMENTS

Steps:

1. **Pick the work**

   If a quoted task description is given, treat it as the work item and skip the issue search (still apply the scope guard below).

   If an issue number is given, fetch it directly:

   ```
   gh issue view <number> --json title,body,labels,comments
   ```

   Otherwise, list open issues and pick one not already covered by an open PR:

   ```
   gh issue list --state open --limit 40
   gh pr list --state open
   ```

   Eligible work is either a **bug** with a clear reproduction path, or a **task / content / enhancement** that is concrete and well-specified (clear outcome, names the country, system, or files it touches, and a sibling implementation exists to mirror).

   **Scope guard: only proceed if the work is small and unambiguous.** Skip it (and say why) when the issue is vague or has no acceptance criteria; needs a design or balance decision that is the user's or team's call; requires new art, audio, or map assets you cannot author; spans many systems or countries; or is a large feature better split into its own PR. When in doubt, report the issue back rather than guess.

   **If no actionable issue remains** (all too vague, graphical, engine-level crashes, out of scope, or already covered), scan the codebase for common bug patterns instead. Patterns to search for:
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

   When working a codebase-scanned bug or a quoted task with no issue number, omit the `Closes #` line from the PR since there is no issue to reference.

2. **Understand the work**

   Read the issue body (or the task description). For a bug, identify the wrong behaviour, the expected behaviour, and any country, decision, event, or system named. For a task, identify the desired outcome, its acceptance criteria, and which files or systems it touches.

3. **Locate the relevant code**

   Search for the named decisions, effects, triggers, scripted GUIs, or on_actions. If not found, do a wider search:

   ```
   grep -rn "keyword" common/ events/ --include="*.txt" -l
   ```

   Read the files involved. Understand the data flow before touching anything.

4. **Diagnose or plan**

   For a bug, trace the logic to find exactly where the wrong value is produced or the wrong branch is taken; confirm the cause in code before writing a fix, do not guess. For a task, plan the change against existing patterns: find a sibling implementation to mirror (a comparable focus, event, decision, idea, or MIO) and reuse its structure and conventions.

5. **Implement the change**

   Make the smallest change that resolves the issue, whether a bug fix or new/edited content. For content, follow the matching system conventions in `AGENTS.md` and the relevant `.claude/docs/` reference (focus trees, events, decisions, ideas, MIOs, localisation), and add every required loc key. Follow the project conventions (`AGENTS.md`):
   - Tabs for indentation
   - No magic numbers; use variables
   - No empty blocks, no commented-out code
   - Only add a comment if the change is non-obvious

   Do not refactor surrounding code or fix unrelated issues in the same commit.

6. **Commit**

   Never create or switch branches on your own. First check the current branch:

   ```
   git rev-parse --abbrev-ref HEAD
   ```

   - If on **`main`**: stop and use `AskUserQuestion` to ask which branch to use. Offer: (a) check out an existing branch (user supplies the name), (b) create a new branch (user supplies the name). Only after the user answers, run `git checkout <name>` or `git checkout -b <name>`. Do not invent a branch name.
   - If **not on `main`**: commit on the current branch. Do not switch or create a branch.

   Then stage only the files changed for this work and commit. Use an accurate verb (`Fix` for a bug, `Add` or `Implement` for a task):

   ```
   git add <files>
   git commit -m "<verb> <short description> (#<issue number>)

   <one or two sentences: a bug's root cause and fix, or what a task added or changed>
   ```

7. **Ensure branch is up to date**

   Run `git merge origin/main` and ensure the branch is up to date before creating a changelog entry or a pull request.

8. **Update the changelog**

   Run `/changelog` to add an entry under the current version in `Changelog.txt`. Commit the changelog update separately.

9. **Open or update the pull request**

   Push the branch first:

   ```
   git push -u origin <branch>
   ```

   Then check whether an open PR already exists for this branch:

   ```
   gh pr list --head <branch> --state open --json number,url,body
   ```

   **a. If no open PR exists**: hand off to `/open-pr <issue number>`. That skill is the single source of truth for the create path (AngriestBird-format body, draft PR, changelog). Do not duplicate its logic here.

   **b. If an open PR already exists**: rewrite its body in AngriestBird format and apply with `gh pr edit <PR#> --body "..."`. Do NOT create a second PR.

   When rewriting an existing PR body:
   - **Preserve every existing `Closes #N` line** at the top, then append a new `Closes #<this issue number>`.
   - **Preserve every existing `#### Bug Fixes` bullet**; append a new bullet, never replace prior ones. Same for `#### Other`, `#### AI`, `#### Content`, etc. Put a task or content change under the matching section (`#### Content`, `#### AI`, etc.), not `#### Bug Fixes`.
   - **Preserve every existing test-plan section**; to extend it for the new work, run `/test-plan` (the PR body's test plan is generated there, not inline).
   - If the existing body uses the older deep-dive format (root-cause code blocks, `file:line` citations, per-issue regression notes), normalise the whole body to AngriestBird format while keeping every fact: recompose each prior fix as a single bolded bullet, dropping regression/file-citation details (they live in the commits and linked issues).
   - Follow `/open-pr` step 5 formatting: bold `**Fixes #N: Issue Title.**` (or `**[Component].**` for a task) prefix + period, then 2 sentences, 2-3 lines max, backticks for code identifiers, no em dashes (`—`) anywhere, no `→` separator. Use a colon, period, or comma instead.

   Apply with a heredoc to keep formatting intact:

   ```
   gh pr edit <PR#> --body "$(cat <<'EOF'
   <full rewritten body>
   EOF
   )"
   ```

10. **Report back**

Output the PR URL, whether the PR was **created** or **updated**, and a one-paragraph summary of what was fixed or added.
