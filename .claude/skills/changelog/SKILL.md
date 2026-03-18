Summarize all changes on the current branch compared to main and add them to `Changelog.txt`.

Requested arguments: $ARGUMENTS

Steps:

1. Read `Changelog.txt` to identify the top-most version heading (first line, e.g., `v2.0.0`) and existing categories.

2. Get the branch diff and commit history:

   ```
   git log origin/main..HEAD --oneline
   git diff origin/main...HEAD --stat
   git diff origin/main...HEAD
   ```

3. Scan the existing `Changelog.txt` for all category headings (lines matching ` CategoryName:`) and collect them into a list. **Only use categories that already exist in the file.** Do not invent new category names. If a change does not fit any existing category, use the closest match. The typical categories found in this file are: Achievements, AI, Balance, Bugfix, Content, Database, Factions, Game Rules, Graphics, Localization, Map, Map Modes, Performance, Quality of Life, Sound, Technology, User Interface.

   Classify each change into one of those existing categories (skip empty categories). Focus on user-facing and gameplay-relevant changes — omit internal refactors or implementation details that don't affect the player experience unless they have a meaningful performance or correctness impact.

4. Write each entry following the `Changelog.txt` format:
   - 1 space before category name, followed by a colon (e.g., ` AI:`)
   - 2 spaces + `- ` before each entry (e.g., `  - [SER] Fixed focus prerequisite`)
   - Prefix with `[TAG]` when the change is country-specific
   - No tag prefix for global/system changes
   - One bullet per distinct change; group related micro-changes into a single bullet
   - Use past tense ("Added", "Fixed", "Reduced", "Reworked")
   - Be specific: name the focus, event, decision, or mechanic affected
   - Mention issue numbers if referenced in commits (e.g., `(Issue #330)`)

5. Insert the new entries into `Changelog.txt` under the existing top-most version heading. Merge into existing categories if they already exist; append new categories after existing ones. Do not create a new version heading unless $ARGUMENTS contains a version string (e.g., `v1.13.0`), in which case add a new version heading above the current top-most one.
