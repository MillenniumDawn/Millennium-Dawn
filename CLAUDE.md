# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Millennium Dawn is a Hearts of Iron IV mod set in the modern era (2000-present). It's a Paradox Interactive game modification with extensive game systems including focus trees, events, decisions, ideas, technologies, and more.

## Directory Structure

- `common/` - Game data files:
  - `national_focus/` - Focus tree files
  - `ideas/` - National spirits and ideas
  - `decisions/` - Decision and mission files
  - `scripted_effects/` - Reusable effect blocks
  - `scripted_triggers/` - Reusable trigger blocks
  - `on_actions/` - On action hooks (`on_daily_TAG`, `on_weekly`, etc.)
  - `technologies/` - Research tree files
  - `modifiers/`, `ai-*/` - Modifier and AI strategy files
  - `ai_strategy/` - AI production weights, role ratios, and combat strategies
  - `ai_templates/` - AI division template compositions (role-to-template mapping)
  - `ai_equipment/` - AI equipment variant designs (tank/ship/plane module configurations)
  - `units/` - Unit type definitions (battalions, companies) and equipment archetypes
- `localisation/` - Language files (English yml files with UTF-8 BOM)
- `events/` - Event chains and triggered events
- `history/` - Historical country data, states, units
- `interface/` - UI definitions
- `gfx/` - Graphics assets
- `tools/` - Python development and validation scripts
- `docs/` - Development documentation

Ignore the `resources` directory entirely, this is mostly used for supporting team resources.

## Available Skills

The following slash commands are available in this project (`.claude/skills/`):

| Skill                         | Description                                                                                   |
| ----------------------------- | --------------------------------------------------------------------------------------------- |
| `/validate [staged] [strict]` | Run all validation tools; optionally limit to staged files or fail on errors                  |
| `/standardize <file>`         | Auto-standardize a focus/event/decision/idea file against MD conventions                      |
| `/new-focus <TAG>`            | Scaffold a new country focus tree file with correct structure and localisation stubs          |
| `/review-branch`              | Review the current branch diff vs main for style violations, logic errors, and balance issues |
| `/fix-issue [number]`         | Find an open GitHub bug, diagnose the root cause, fix it, and open a PR                       |

## Validation & Formatting Tools

Validation runs automatically on GitHub CI when a PR is opened. Do not run validators proactively after making changes — only run `/validate` on explicit request.

Standardization tools are available in `tools/standardization/`. Use the `/standardize` skill for quick access, or run the scripts directly — the directory has a README with full usage details.

A standalone diff summary script is also available: `python3 tools/analysis/review_branch.py [base-branch]`.

## General Formatting Rules

- Use **tabs** for indentation (not spaces), increase by 1 on `{`, decrease by 1 on `}`
- Keep simple checks on one line: `available = { has_country_flag = some_flag }`
- Opening `{` stays on the same line as the property; closing `}` gets its own line at the outer indentation level
- 1 blank line between elements
- Remove unused/commented-out code
- Use multiplication instead of division (e.g., `* 0.01` not `/ 100`)
- Use `if/else` instead of two consecutive `if` blocks with complementary conditions — avoids double-execution risk and is clearer in intent
- Use variables instead of magic numbers; always prefix country-specific variables with the country tag (e.g., `ISR_operation_success`, not `oper_succ_var`) to avoid cross-country collisions

## Performance Tips

- Avoid open-fire MTTH events (always use `is_triggered_only = yes`)
- Use tag-specific on_actions (`on_daily_TAG`) instead of global triggers
- Use dynamic modifiers sparingly; avoid `force_update_dynamic_modifier`
- Replace `every_country`/`random_country` with specific array triggers
- Only log when there are meaningful effects (logging causes I/O overhead)

## Focus Trees

- Focus ID format: `TAG_focus_name_here`
- Use `relative_position_id` for positioning
- Always include logging: `log = "[GetDateText]: [Root.GetName]: Focus TAG_focus_name"`
- Always include `ai_will_do = { base = N }` with game options checks — use `base`, not `factor`, at the root level
- Always include `search_filters` — use the two-layer pattern: country-specific filter + matching generic where a custom filter exists (see `.claude/docs/search-filters.md`)
- Omit default values: `cancel_if_invalid = yes`, `continue_if_invalid = no`, `available_if_capitulated = no`
- Avoid empty `mutually_exclusive` and `available` blocks
- Limit permanent effects to 5; use timed ideas for more
- Use scripted effects and triggers where applicable
- Implement starting ideas that weaken nations, resolvable through focus trees/decisions
- Never use `available = { always = no }` on a focus that also has a `bypass`. Always set `available` to match or approximate the bypass condition — otherwise the player is hard-locked if the bypass fails to auto-fire.
- High-cost focuses (cost >= 8, or cost >= 5 for military/economy/research focuses) should include `NOT = { has_active_mission = bankruptcy_incoming_collapse }` in `available` to prevent the AI from queueing expensive focuses during financial collapse.

For property order, structure, building costs, and examples, see `.claude/docs/focus-tree-reference.md`.

## Decisions

- Use `fire_only_once` only when necessary
- Include logging in `complete_effect`: `log = "[GetDateText]: [Root.GetName]: Decision DECISION_ID"`
- Structure with clear `visible` and `available` conditions
- Include `ai_will_do = { base = N }` — `base` not `factor` at root level; use `modifier = { factor = X ... }` for conditional adjustments

For structure, scripted effects, and examples, see `.claude/docs/decision-reference.md`.

## Events

- Always use `is_triggered_only = yes` for triggered events
- Log only if there are actual effects in the option
- Use `major = yes` sparingly (news events only)
- Trigger date-based events via `common/scripted_effects/00_yearly_effects.txt`; when the intended recipient may no longer own the target state, use the owner-guard pattern (check expected owner, fall back to `random_country = { limit = { owns_state = X } }`)
- When a focus or event fires to another nation, always add `TT_IF_THEY_ACCEPT` / `TT_IF_THEY_REJECT` tooltips so the player can see both outcomes — see `.claude/rules/general-rules.md` for the full pattern and available keys.
- `add_building_construction` for `naval_base` requires `province = XXXXX` — without it the build silently fails or misplaces the base in multi-province states
- When adding new subideology parties, register them in `common/scripted_localisation/00_subideology_scripted_localisation.txt` for every relevant ideology group — missing registration causes fallback to a generic entry

For structure, ETD system, and examples, see `.claude/docs/event-reference.md`.

## Ideas

- Include `allowed_civil_war = { always = yes }` for civil war tags
- Use `original_tag` not `tag` in `allowed` blocks — during civil wars the split-off country has a different runtime tag but the same `original_tag`; `allowed = { tag = TAG }` breaks for those countries
- **Remove** `allowed = { always = no }` - this is the default and hurts performance
- **Remove** `cancel = { always = no }` - checked hourly, never true
- **Remove** empty `on_add = { log = "" }` unless actually doing something
- Log in `on_add` only when making changes

For structure and examples, see `.claude/docs/idea-reference.md`.

## Military-Industrial Organizations (MIO)

- Name MIOs with `TAG_organization_name` format
- Always include `allowed = { original_tag = TAG }` to restrict to the correct country
- Set `task_capacity` proportional to nation size (typically 10-25)
- Equipment types must reference valid `equipment_type` categories
- Trait grid runs `y = 0` to `y = 9`; use relative positioning for trait layout
- Add `initial_trait` for the organization's defining bonus

For structure and examples, see `.claude/docs/mio-reference.md`.

## AI Strategies & Unit Production

The AI unit production system has three layers: a unit-building gate (`AI_is_threatened` flag), role ratio strategies, and division templates. See `.claude/docs/ai-strategy-reference.md` for full details.

Key rules:

- `role_ratio id = X` must match a `role = X` defined in `common/ai_templates/` — the `validate_ai_roles` pre-commit hook catches mismatches
- Unit names in OOB files and AI templates are **case-sensitive** — the `validate_oob_units` pre-commit hook catches typos
- When setting template `enable` conditions with factory thresholds, ensure adjacent templates cover the full range with no gaps (e.g., `> 10` and `< 21` for one, `> 20` for the next)
- Subject/puppet nations always get the `AI_is_threatened` flag — do not add conditions that would clear it for subjects
- `give_AI_templates` uses `division_template` (additive) — each sub-effect is guarded by `has_template` checks to prevent duplicates
- When puppeting a nation via events/decisions, `on_puppet` already handles AI template initialization — no additional scripting needed

## AI Equipment

AI equipment files (`common/ai_equipment/`) define equipment variants the AI should build. See `.claude/docs/ai-equipment-reference.md` for full structure.

Key rules:

- Every role template needs `category`, `roles = { ... }`, and a top-level `priority = { ... }` block
- Every design needs `target_variant` with `type`, `match_value`, and `modules`
- Role template names must be unique across all files with overlapping `available_for` — duplicates silently overwrite
- Nations blocked from generic files MUST have all needed roles covered in custom/shared files
- Module assignments must match the slot type (e.g., don't put armor modules in `reload_type_slot`)
- CAS designs must use `medium_cas_fighter` role, not `medium_as_fighter`
- Use date-based thresholds (e.g., `date < 2000.6.1`) instead of factory count thresholds for small nations that may never reach high factory counts

## Key Resources

- [Contributing Guidelines](./CONTRIBUTING.md)
- [HOI4 Scripting Reference](./.claude/docs/hoi4-data-structures.md) - Variables, arrays, loops, collections, loc
- [Documentation Index](./.claude/docs/documentation-references.md) - Effects, triggers, modifiers docs & wiki links
- [Search Filter Reference](./.claude/docs/search-filters.md) - All `FOCUS_FILTER_*` values, Israel filter mapping, subcategory logic
- [Focus Tree Reference](./.claude/docs/focus-tree-reference.md) - Property order, building costs, examples
- [Event Reference](./.claude/docs/event-reference.md) - Event structure, ETD system, examples
- [Decision Reference](./.claude/docs/decision-reference.md) - Decision/mission structure, scripted effects, examples
- [Idea Reference](./.claude/docs/idea-reference.md) - Idea structure and examples
- [MIO Reference](./.claude/docs/mio-reference.md) - MIO structure and examples
- [AI Strategy Reference](./.claude/docs/ai-strategy-reference.md) - Unit-building gate, role ratios, templates, subject AI
- [AI Equipment Reference](./.claude/docs/ai-equipment-reference.md) - Equipment variant designs, coverage model, common mistakes
- [Diplomatic Action Reference](./.claude/docs/diplomatic-action-reference.md) - Scripted diplomatic action structure, cooldowns, AI weighting
- [Content Guidelines](./.claude/docs/content-guidelines.md) - Quality checklist, general/admiral formulas
- [Faction Rules](./.claude/docs/faction-rules.md) - Faction rule structure, locked faction patterns
