Scaffold a new focus tree file for a country in Millennium Dawn.

Country TAG (3-letter code): $ARGUMENTS

Steps:

1. Confirm the TAG is valid (3 uppercase letters). If $ARGUMENTS is empty, ask the user for the TAG.

2. Check if `common/national_focus/05_<TAG>.txt` already exists (uppercase TAG). If it does, warn the user before proceeding.

3. Create the file at `common/national_focus/05_<TAG>.txt` (uppercase TAG) with:
   - A `focus_tree` container block with the correct `id`, `country` filter, and a placeholder `continuous_focus_position`
   - One starter focus block following the required property order (see `.claude/docs/focus-tree-reference.md` § "Required Property Order")
   - The root focus id following the pattern `TAG_start`
   - All tags capitalised in script IDs (e.g. `SER_free_market_capitalism`, not `ser_free_market_capitalism`)
   - `relative_position_id` on all focuses after the root (all focus trees must use relative positioning)
   - Logging in completion_reward: `log = "[GetDateText]: [Root.GetName]: Focus TAG_start"`
   - `search_filters` (required on all focuses)
   - `ai_will_do` (required on all focuses)
   - Commented-out optional blocks (allow_branch, prerequisite, mutually_exclusive, bypass, cancel, select_effect, bypass_effect) as scaffolding hints; remind the user to remove any that stay empty (empty trigger blocks are bloat)
   - Omit default values: `cancel_if_invalid = yes`, `continue_if_invalid = no`, `available_if_capitulated = no`

4. Create the minimum localisation entry. If `localisation/english/MD_focus_<TAG>_l_english.yml` exists, append to it; otherwise create it with the `l_english:` header. Add keys for `TAG_start` and `TAG_start_desc`. Follow localisation rules: UTF-8 with BOM, 1-space indent, no trailing version numbers.

5. Remind the user of the **Focus Tree Lifecycle Checklist** (docs/src/content/resources/focus-tree-lifecycle-checklist.md) and next steps:

   **Immediate setup:**
   - Add `shared_focus` lines if the country should use shared trees (EU, AU, etc.)
   - Set a real icon instead of the placeholder
   - Fill in `continuous_focus_position` after building out the tree

   **Coding phase (from lifecycle checklist):**
   - National Ideas with localisation
   - National Decisions with localisation
   - History file updates (starting spirits, economy, political parties)
   - OOB (Order of Battle) updates
   - Leaders with at least 2 custom traits each
   - Political party localisation (icons + descriptions for all parties)
   - Unit namelists
   - Influence/Investment AI
   - AI game rules for player customisation
   - At least 10-15 flavour events

   **Content review standards (docs/src/content/resources/content-review-guide.md):**
   - Generic tree baseline is 114 focuses; aim to meet or exceed
   - All buildings in effects need monetary costs (use scripted effects from `docs/src/content/resources/code-resource.md`)
   - Limit permanent effects to 5 per focus; use timed ideas for more
   - Balanced paths; no path objectively stronger than another
   - Fictional/implausible paths must be locked behind a game rule
   - Effects targeting another nation should come from an event (give the target player agency)
   - Where a focus triggers events, use tooltips to indicate what may happen
   - No free cores; require a mechanic (decision/focus with 80% compliance, or integration system)
   - Do not use `add_ai_strategy` in effects (harmful to AI performance)
   - Use `relative_position_id` throughout the tree
   - Remove unused/commented-out code once real content is filled in
   - Ensure political neutrality and thorough research
   - All player-facing text localised; no blank descriptions
   - Do not add the nation to bookmarks; that happens after merge
