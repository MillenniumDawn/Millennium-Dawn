Summarize all changes on the current branch compared to main and add them to `Changelog.txt`.

Requested arguments: $ARGUMENTS

Steps:

1. Read `Changelog.txt` to identify the top-most version heading (first line, e.g., `v2.0.0`) and existing categories.

2. Get the branch diff and commit history:

   ```
   git log main..HEAD --oneline
   git diff main...HEAD --stat
   git diff main...HEAD
   ```

3. Analyze every change and classify each into one of these categories (skip empty categories):
   - **Achievements** — New or changed achievements
   - **AI** — AI behavior, strategy, or decision-making changes
   - **Balance** — Stat tweaks, modifier adjustments, cost/value changes
   - **Bugfix** — Bug fixes, crash fixes, typo corrections
   - **Content** — New focus trees, events, decisions, ideas, MIOs, countries, or significant new gameplay
   - **Database** — Country history, OOBs, state data, technology assignments
   - **Documentation** — Docs, guides, modding resources
   - **Factions** — Faction mechanics, membership, leadership changes
   - **Game Rules** — New or modified game rules
   - **Graphics** — GFX, icons, portraits, sprites, 3D models
   - **Localization** — Localisation strings, translations, formatting
   - **Map** — Map changes, state boundaries, provinces, map modes
   - **Music** — New or changed music tracks, sound triggers
   - **Performance** — Optimizations, removed redundant triggers, on_action improvements
   - **Quality of Life** — QoL improvements, UI polish, tooltips
   - **Sound** — Sound effects and audio changes
   - **Technology** — Tech tree changes, research categories
   - **User Interface** — UI layout, scripted GUIs, interface definitions

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
