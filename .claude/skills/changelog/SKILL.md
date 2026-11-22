---
name: changelog
description: "Add the branch's changes to Changelog.txt under the current version, then tidy and deduplicate it with merge_changelog.py. Use when asked to update the changelog, add changelog entries, clean up duplicate or repeated entries, or refresh the beta or release changelog pages. Optional version argument (e.g. v1.13.0) starts a new version heading."
---

Summarize all changes on the current branch compared to main and add them to `Changelog.txt`. Then let `tools/merge_changelog.py` tidy, sort, and check for duplicates.

Optional argument: a version string (e.g. `v1.13.0`) to start a new version heading above the current top-most one. Without it, entries go under the existing top-most version.

Requested arguments: $ARGUMENTS

Steps:

1. Decide whether the branch needs a line. Skip `Changelog.txt` and say why when:
   - The diff touches no game files, only `tools/`, `.claude/`, `docs/`, or CI.
   - The diff only makes event or decision AI weights cost-aware or situational. The top-level `AI:` entry ("Improved AI event and decision choices to account for budgets, ...") covers it. If a bug fix or new mechanic rides along, ask before adding a line.

2. Get the branch diff and commit history:

   ```
   git log origin/main..HEAD --oneline
   git diff origin/main...HEAD --stat
   git diff origin/main...HEAD
   ```

3. Read the current version of `Changelog.txt` (everything above the second `vX.Y` heading). Run `python3 tools/merge_changelog.py --preview`. Note the category headings, and any entry that already covers part of this branch's change.

   **Only use categories that already exist in the file.** Do not invent new names. If a change doesn't fit any existing category, use the closest match. Typical categories: Achievements, AI, Balance, Bugfix, Content, Database, Factions, Game Rules, Graphics, Localization, Map, Map Modes, Performance, Quality of Life, Sound, Technology, User Interface. Focus on user-facing and gameplay changes. Omit internal refactors unless they have a real performance or correctness impact.

4. Write each entry:
   - BLUF, one line: ` - [TAG] <Past-tense verb> <what the player sees> (Issue #N).` Lead with the outcome. No cause clauses ("which left...", "because..."), no "It now..." follow-up sentence, no before/after numbers unless they are the change itself. Aim for under 120 characters before the issue suffix. Depth belongs in the commit and PR body.
   - One line per distinct change. A single-topic PR gets one line. A PR with unrelated fixes gets one untagged line for cross-country changes and one `[TAG]` line per country, not one run-on sentence.
   - Extend instead of duplicating. If an existing entry covers the same change, add your tag (`[ENG]/[FRA]`) or issue number (`(Issue #12, #34)`) to it. Do not write a parallel line.
   - The same change for several countries is one line with joined tags (`[ERI]/[ETH]`). For many countries, use an untagged line that lists them ("for ALG, CUB, and DEN").
   - `[TAG]` prefix for country-specific changes. No tag for global changes.
   - Past tense ("Added", "Fixed", "Reduced", "Reworked"). Name the focus, event, decision, or mechanic. Mention issue numbers from the commits.
   - No em dashes. End the sentence with a period instead.

   What NOT to write:
   - Padding filler. "Fixed an issue where the AI would not behave correctly" is too vague. Say what changed, e.g. "Fixed AI sending volunteers to countries it cannot reach".
   - Internal terminology players don't know ("immediate block", "trigger scope").
   - Future tense ("Will add"). Use "Added".
   - Per-country copies of the same sentence.

5. Insert the entries under the top-most version, in their existing categories. Don't hand-sort or fix spacing; `--fix` does both. Do not create a new version heading unless $ARGUMENTS contains a version string. If it does, add the heading above the current top-most one. Before you do, ask whether to write the finished version's release page first (see Docs pages).

6. Run `python3 tools/merge_changelog.py --fix`. It does all of this:
   - normalizes bullets, spacing, `[A]/[B]` tags, and final periods;
   - removes exact repeats within a category;
   - sorts each category;
   - warns about exact repeats across categories.

   Resolve every warning by keeping the entry in the category that fits best.

7. Run `python3 tools/merge_changelog.py --preview` again. Clear each finding that includes your entries:
   - **Same entry for other tags**: use the combined line it prints.
   - **Near-duplicate entries**: keep one line, with every tag and issue number listed after "keep".
   - **Shared phrase**: fold the lines into one entry that keeps the listed tags and issue numbers. Use joined tags, or a country list for many tags.

   Report findings that involve only other entries. Do not rewrite them unless asked. Finish with `python3 tools/linting/check_changelog.py`, which must print nothing.

8. After merging main into the branch, rerun steps 6 and 7 and commit the result. A union merge leaves new lines unsorted.

Docs pages (only when asked):

- `python3 tools/merge_changelog.py --beta` refreshes `docs/src/content/misc/beta-changelogs.md` from the current version. Run it when a beta build is cut.
- `python3 tools/merge_changelog.py --release "Name"` writes the release page for the current version under `docs/src/content/changelogSections/`. It renders only the top version, so run it before adding the next version heading.
- Both run `--fix` first. Afterward, run `bun run lint:md` in `docs/` (see `docs/CONTRIBUTING.md`).

Report the lines added or extended, any skip and its reason, and any warnings or preview findings left.
