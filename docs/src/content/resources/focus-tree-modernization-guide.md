---
title: Focus Tree Modernization Guide
description: The repeatable method for bringing a stale focus tree up to current Millennium Dawn standards
---

Some of Millennium Dawn's older focus trees predate the mod's current reward, AI, and treasury conventions. Modernizing one of these trees is a different job than building new content: the tree already has a layout, decisions and events already reference its focus ids, and the goal is to bring the mechanics up to standard without breaking anything that depends on it. This guide is the repeatable method for that job. For the standards themselves, see:

- [Focus Tree Design Principles](/dev-resources/focus-tree-design-principles/), branch structure, pacing, and reward philosophy
- [Code Stylization Guide](/dev-resources/code-stylization-guide/), formatting and required focus field order
- [Dynamic Modifiers](/dev-resources/dynamic-modifiers/), variable-driven modifiers and tooltip keys
- [Code Resource](/dev-resources/code-resource/), modifier reference and building costs
- [Search Filters](/dev-resources/search-filters/), `search_filters` reference and the two-layer convention

---

## When a Tree Needs Modernization

A tree is a modernization candidate when it shows drift like:

- `completion_reward` blocks that are bare `add_political_power` / `add_stability` / `add_war_support`, with no mechanical effect behind them.
- `ai_will_do` with a flat `base = N` and no modifiers: no bankruptcy guard on costly focuses, no path-flag gating on political branches, no rival-path suppression.
- No `common/ai_strategy_plans/<TAG>_strategy_plans.txt`, so the in-game AI cannot meaningfully play the nation's branching content.
- Buildings or stat rewards with no treasury cost behind them, no `modify_treasury_effect` or `*_expenditure` call anywhere near an `add_building_construction` or office reward.
- Logging that's missing, or doesn't match the current `log = "[GetDateText]: [This.GetName]: focus <ID> executed"` format.
- Stat buffs stacked as permanent ideas instead of routed through a variable-backed entry in `common/dynamic_modifiers/`.
- Starting debt/treasury numbers that push the nation past the interest-rate spiral (see the debt/treasury check below).

Not every symptom needs to be present. Treat this as a checklist for scoping the work, not a pass/fail gate, some branches in an otherwise-stale tree may already be modern and should be left alone.

---

## The Method

### 1. Audit and Branch Map

Read the whole tree before editing anything. Classify every branch as stale or already-modern, changes only belong in the stale branches. For each branch, identify:

- Whether it's a political path: what flag it sets (`set_global_flag` / `set_country_flag`), and what gating already exists on it.
- What mechanical identity it should route rewards through: existing ideas, penalty variables, MIOs, and dynamic modifiers the nation already has, rather than mechanics invented from scratch.

Grep for `has_completed_focus`, `has_global_flag`, and `has_country_flag` against the tree file to find what events and decisions already depend on, and grep `common/ai_strategy_plans/` for any references to the tree's focus ids. The output of this phase is a map: focus id, branch, stale or modern, and political path membership.

### 2. Written Per-Nation Design

Before rewriting a single `completion_reward`, write down the nation's mechanical identity: which 3-4 modifier families it draws from (tax, per-building productivity/tax, workforce, cost multipliers, investment, influence, energy, corruption/law-cost, per-branch military), grounded in what the nation already has rather than invented tokens. Spell out, per branch, what each focus's reward will be before touching script, the same draft-before-code principle from the [Focus Tree Lifecycle Checklist](/dev-resources/focus-tree-lifecycle-checklist/), applied to a rework instead of new content.

If the nation's starting debt or treasury is in scope, include a debt/treasury check in the design doc: run `python3 tools/run.py estimate_gdp --all` for `gdp_total` inputs, then apply the interest-rate formula from `calculate_interest_rate` in `common/scripted_effects/00_money_system.txt`: `base = debt / gdp_total * 10` plus premiums, clamped 0.8-50. Interest above 15% triggers the `very_high_interest` penalty modifiers. Target starting numbers that sit clearly under that threshold with a treasury buffer that survives early deficits, without removing debt as a mechanic entirely.

### 3. Chunked Rewrite

Work in passes of roughly 60-80 focuses, not the whole file at once. A tree of any real size is too much to hold reliably in a single editing pass, and a bad chunk boundary is far easier to re-review than a bad whole-file diff. Locate work by focus id (`grep -n "id = TAG_focus_name"`), never by line number, reformatting shifts every line below the change, and the id is the only coordinate that stays stable across edits.

### 4. Per-Chunk Review and Verification

Run the verification gates below after each chunk, before starting the next one. A scope leak or a missing tooltip key is easy to catch and fix in a 70-focus chunk; the same issue across an entire multi-hundred-focus file at the end of a pass is not.

---

## Hard Rules During Modernization

- **Ids, positions, and structure are frozen.** Focus ids, `x`/`y`, `relative_position_id`, `prerequisite`, and `mutually_exclusive` stay exactly as they are. Events and decisions reference ids via `has_completed_focus`; renaming, moving, or reordering breaks them silently.
- **Enrich existing variable machinery, never replace it.** If a variable already drives a dynamic modifier, add to that variable. Don't stand up a second, parallel modifier for the same stat.
- **War-focus `ai_will_do` keeps its guards.** Faction and strength check modifiers stay in place. A modernization pass tunes weights; it does not remove the checks that stop the AI from starting wars it can't win.
- **Don't double-charge treasury.** MD's build scripted effects (`one_office_construction` and similar, from `common/scripted_effects/`) already charge treasury for the building. Adding a second `modify_treasury_effect` cost on top of one of these double-costs the player.
- **Guard first-add of dynamic modifiers.** Check `NOT = { has_dynamic_modifier = { modifier = X } }` (or the branch's equivalent) before `add_dynamic_modifier`, so a branch reachable from more than one entry focus doesn't add the same modifier twice.
- **Reuse generic tooltip keys.** Prefer the existing generic `<modifier>_tt` keys in `MD_dm_modifiers_l_english.yml` over minting a new per-variable key. Only add a new key when no generic one fits.
- **Loc files are append-only.** They're UTF-8 with BOM. Append new keys to the nation's existing localisation file; never re-encode or reorder it.

---

## Reward Conversion Table

| Old pattern                                                                           | Modern replacement                                                                                                                                                                                               |
| ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Bare `add_political_power` / `add_stability` / `add_war_support` as the entire reward | Keep as seasoning alongside a mechanical effect, never the whole `completion_reward`                                                                                                                             |
| Flat stat buff via permanent `add_ideas` stacking                                     | Route through the nation's dynamic modifier: `add_to_variable` on the backing var with a `tooltip`, `add_dynamic_modifier` only on first use                                                                     |
| Building or office reward with no cost                                                | Pair with `set_temp_variable = { treasury_change = -X } modify_treasury_effect = yes`, or a `small_`/`medium_`/`large_expenditure` call for GDP-scaled costs, per [Code Resource](/dev-resources/code-resource/) |
| `ai_will_do` with no modifiers                                                        | `base = N` plus modifier blocks: path-flag gating, rival-path `factor = 0`, and a bankruptcy guard on costly focuses                                                                                             |
| Missing or outdated log line                                                          | `log = "[GetDateText]: [This.GetName]: focus <ID> executed"` as the first line of `completion_reward`                                                                                                            |
| No `search_filters`, or a single-layer filter                                         | Two-layer filters: the nation/faction custom filter plus a generic `FOCUS_FILTER_*`                                                                                                                              |
| Stacked permanent ideas used as a reform ladder                                       | A timed idea with `swap_ideas` between rungs                                                                                                                                                                     |
| Military-industrial reward left disconnected from the nation's MIO                    | `if = { limit = { has_dlc = "Arms Against Tyranny" } mio:<TAG>_x = { add_mio_funds = N } }`                                                                                                                      |

Beyond these, the system-effect scripts in `common/scripted_effects/` (budget, corruption, productivity, influence, research, internal faction opinion) are the building blocks for turning a bare stat bump into something specific to the nation. See the [Code Resource](/dev-resources/code-resource/) and [Dynamic Modifiers](/dev-resources/dynamic-modifiers/) pages for the full catalogue.

---

## ai_will_do and ai_strategy_plans Checklist

- Every focus keeps `ai_will_do = { base = N ... }` as the last field in the focus.
- Economy-costly focuses carry `modifier = { factor = 0 has_active_mission = bankruptcy_incoming_collapse }`.
- Political-path focuses gate on the flag the tree already sets (`has_global_flag` / `has_country_flag`), and rival paths get `factor = 0` once a flag commits the AI to one path.
- Situational focuses (war, threat-driven) use `check_variable` / `threat` / war conditions the way an already-modern tree in the mod does, rather than firing unconditionally.
- One `common/ai_strategy_plans/<TAG>_strategy_plans.txt` per nation: `enable` on the path flag, `abort` on `is_subject`, an ordered `ai_national_focuses` list, and `focus_factors` zeroing rival path entry focuses.
- Flag names in the strategy plan must match flags the tree actually sets, verify with grep. If a path-entry focus never sets one, adding `set_global_flag`/`set_country_flag` there is an allowed tree edit during modernization.
- Verify every focus id referenced in the strategy plan still exists in the tree. A rename or a removed stub during the rewrite silently orphans the AI plan.

---

## Verification Gates

1. **Standardize first.** `python3 tools/run.py standardize focus common/national_focus/<file>`, run before the checks below so formatting churn is separated from content changes.
2. **Style and lint.** `python3 tools/validation/validate_style.py --no-color <changed files>` and `python3 tools/linting/check_common_mistakes.py <changed files>`, the same checks CI runs.
3. **Full-mod validation against a pre-change baseline.** Take a cwtools validation report before starting the pass, then re-run it after each chunk and compare. Match findings by file, error code, and message, not by line number, line numbers shift constantly during a rewrite and produce false diff noise if used as the comparison key.
4. **Loc completeness.** Grep the nation's localisation file for every tooltip and idea key referenced from the tree. Anything unresolved is a broken tooltip in-game.
5. **GDP/debt sanity.** If starting treasury or debt numbers changed, re-run `python3 tools/run.py estimate_gdp --all` and recheck the interest-rate formula against the updated `gdp_total`.

---

## Related Resources

- [Focus Tree Design Principles](/dev-resources/focus-tree-design-principles/)
- [Code Stylization Guide](/dev-resources/code-stylization-guide/)
- [Dynamic Modifiers](/dev-resources/dynamic-modifiers/)
- [Code Resource](/dev-resources/code-resource/)
- [Search Filters](/dev-resources/search-filters/)
- [Focus Tree Lifecycle Checklist](/dev-resources/focus-tree-lifecycle-checklist/)
- [Claude Code Skills](/dev-resources/claude-code-skills/)
