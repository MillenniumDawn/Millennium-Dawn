Scaffold a new focus tree file for a country in Millennium Dawn.

Country TAG (3-letter code): $ARGUMENTS

Steps:
1. Confirm the TAG is valid (3 uppercase letters). If $ARGUMENTS is empty, ask the user for the TAG.

2. Check if `common/national_focus/05_$ARGUMENTS.txt` already exists. If it does, warn the user before proceeding.

3. Create the file at `common/national_focus/05_<TAG_lowercase>.txt` with:
   - A `focus_tree` container block with the correct `id`, `country` filter, and a placeholder `continuous_focus_position`
   - One starter focus block following the required property order from CLAUDE.md:
     id, icon, x/y, relative_position_id, cost, allow_branch (commented), prerequisite (commented),
     mutually_exclusive (commented), search_filters, available (commented), bypass (commented),
     cancel (commented), will_lead_to_war_with (commented), complete_tooltip (commented),
     select_effect (commented), completion_reward with log line, bypass_effect (commented), ai_will_do
   - The focus id should follow the pattern `TAG_start` as the root focus

4. Also create the minimum required localisation entry in `localisation/english/focus/` (or the appropriate localisation file if one exists for the country) with keys for `TAG_start`, `TAG_start_desc`.

5. Remind the user to:
   - Add `shared_focus` lines if the country should use shared trees (EU, AU, etc.)
   - Set a real icon instead of the placeholder
   - Fill in the `continuous_focus_position` after building out the tree
