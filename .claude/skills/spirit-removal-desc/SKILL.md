---
name: spirit-removal-desc
description: 'Add or refresh the removal footer on a country''s fixable starting national spirits: trace how each negative spirit is removed, improved, or swapped (focus, decision, event, variable, weekly effect) and append the standard "This national spirit will be Removed if..." footer to every tier''s _desc, like PER and ARM. Permanent spirits and the economy/military dynamic modifiers get none. Use when asked to explain how starting spirits are solved or removed, e.g. "/spirit-removal-desc ISR".'
---

Append the standard removal footer to the `_desc` of a country's starting national spirits so the player can see how each one is solved.

**Syntax:** `/spirit-removal-desc TAG` (3-letter TAG; ask if none given).

Read `.claude/docs/localisation-rules.md` (section "Removable spirit footer") first. That section is the template; this skill is the procedure. Reference examples: `MD_focus_ARM_l_english.yml` (`ARM_armenian_mafia_6_desc`, `ARM_outdated_airforce_idea_desc`) and `MD_focus_PER_l_english.yml` (`PER_us_sanctions_desc`, `PER_khargh_lifeline_desc`).

## Execution

### 1. Inventory the starting spirits

Read `history/countries/<TAG> - *.txt`: every token in `add_ideas`, plus country-level `add_dynamic_modifier` and `add_timed_idea`. Drop tokens defined in shared law/system files (`common/ideas/AA_law_*.txt`, `misc.txt`, `generic_ideas.txt`, `Various.txt`, `united_states.txt`); generic systems manage them. Drop the permanent economy and military-branch dynamic modifiers (`<TAG>_economy_modifier`, `<TAG>_political_modifier`, `<TAG>_artesh_modifier` style) up front: they are never removed and get no footer. Locate the rest in `common/ideas/` and `common/dynamic_modifiers/` and read their modifiers.

### 2. Classify

For each spirit: negative, mixed, positive, or hidden. Then find every place it changes:

```bash
grep -rn "remove_ideas = TOKEN\|remove_idea = TOKEN\|has_idea = TOKEN" common events
```

Cover tier chains (`TOKEN_1..N` stepped by scripted effects in `common/scripted_effects/99_<TAG>_*.txt`), `swap_ideas` blocks, `common/on_actions/99_<TAG>_on_actions.txt` weekly swaps, events fired from focuses, decisions, and `cancel` blocks on the idea itself. Resolve every focus, decision, and event to its English name in `localisation/english/MD_focus_<TAG>_l_english.yml`.

The footer is for spirits the player can fix. In scope: every negative or mixed spirit that something removes, swaps, or improves, every tier of those chains, and a dynamic modifier only when it has penalties and a focus, decision, or event removes or improves it. Out of scope, no footer: anything nothing ever changes (permanent negative spirits, the economy and military-branch dynamic modifiers), positive flavour spirits nothing touches, hidden ideas, state-level dynamic modifiers.

### 3. Confirm before writing

Show a table: `token | tier | negative? | removal path (ids + names) | proposed footer`. List permanent spirits in a separate "no footer" group so the user can see they were considered. Flag dead ends (a tier no effect ever touches) and missing `_desc` keys. Wait for the user to confirm the table.

### 4. Write

Edit only `localisation/english/MD_focus_<TAG>_l_english.yml` (UTF-8 with BOM). Append the footer inside the existing closing quote; do not rewrite the flavour text. Follow the template rules in `localisation-rules.md`: `§Y$focus_id$§!` for focus names, `§Y` never `§H`, no em dashes, first person collective, the same footer on every tier of a chain with the last-tier and never-removed variants.

### 5. Verify

- `grep -c "§W--------------§!" <file>` equals the number of rows in the confirmed table.
- No `§H` and no em dash in the new text; every `$key$` used exists as a loc key in the same file.
- `pre-commit run --files <file>` passes.

Report the table with `done` per row, plus the unfixed script findings (dead ends, duplicates) as a separate list. Do not fix script files under this skill.
