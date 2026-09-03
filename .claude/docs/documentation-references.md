# Documentation References

## Local Documentation (`resources/documentation/`)

Offline references for HOI4 scripting, copied verbatim from the game's own `documentation/` folder. Read these to look up valid effects, triggers, modifiers, or other engine features. Refresh them after a HOI4 version bump with `python3 tools/validation/refresh_vanilla_data.py --only docs`.

| File                                 | Contents                                                |
| ------------------------------------ | ------------------------------------------------------- |
| `effects_documentation.md`           | All effects by scope (COUNTRY, STATE, CHARACTER, …)     |
| `triggers_documentation.md`          | All triggers by scope                                   |
| `modifiers_documentation.md`         | All modifiers by category (army, navy, country, …)      |
| `dynamic_variables_documentation.md` | Read-only dynamic variables by scope                    |
| `loc_formatter_documentation.md`     | Localization formatters (`idea_desc`, `tech_effect`, …) |
| `loc_objects_documentation.md`       | Localization scope objects and their properties         |
| `script_collection_input.md`         | Collection inputs (`game:all_countries`, …)             |
| `script_collection_operator.md`      | Collection operators (`faction_members`, `limit`, …)    |
| `script_concept_documentation.md`    | Bindable/formatted loc, collections, script constants   |
| `script_math_functions.md`           | Math functions for `value = { ... }` expressions        |
| `console_commands_documentation.md`  | Console commands and tweakable variables                |

## External Wiki References

Use for broader modding context not covered in local docs:

- [Focus Tree Modding](https://hoi4.paradoxwikis.com/National_focus_modding)
- [Decision Modding](https://hoi4.paradoxwikis.com/Decision_modding)
- [Event Modding](https://hoi4.paradoxwikis.com/Event_modding)
- [Idea Modding](https://hoi4.paradoxwikis.com/Idea_modding)
- [Scopes](https://hoi4.paradoxwikis.com/Scopes)
- [On Actions](https://hoi4.paradoxwikis.com/On_actions)
- [AI Modding](https://hoi4.paradoxwikis.com/AI_modding)
- [Scripted GUI](https://hoi4.paradoxwikis.com/Scripted_GUI_modding)
- [Technology Modding](https://hoi4.paradoxwikis.com/Technology_modding)
- [Equipment Modding](https://hoi4.paradoxwikis.com/Equipment_modding)
- [MIO Modding](https://hoi4.paradoxwikis.com/Military_industrial_organization_modding)
- [Unit Modding](https://hoi4.paradoxwikis.com/Unit_modding)
- [Faction Modding](https://hoi4.paradoxwikis.com/Faction_modding)

## Millennium Dawn Conventions

### Naming Scheme

Most filenames end in one of four suffixes: `-reference` (structure or valid-key lookup), `-rules` (must-follow conventions), `-patterns` (recipe/refactor catalogs), or `-system` (subsystem architecture). A handful of docs use a plain descriptive name instead when none of those fit (`agent-conventions.md`, `debug-commands.md`, `typo-watchlist.md`, `validation-pipeline.md`).

All files below live in `.claude/docs/`.

| File                             | Contents                                                     |
| -------------------------------- | ------------------------------------------------------------ |
| `agent-conventions.md`           | Rules for `.claude/agents/` definitions: anti-rules, reading |
| `ai-equipment-reference.md`      | AI equipment variants: role templates, coverage errors       |
| `ai-strategy-reference.md`       | Unit production: 5 layers, on_action entries, plan files     |
| `bug-patterns.md`                | Known bug patterns: scan signatures, diff-review questions   |
| `content-guidelines.md`          | Content checklist: economic, political, military, visual, AI |
| `debug-commands.md`              | Console recipes for testing MD systems (EU/USoE focus)       |
| `decision-reference.md`          | Decision structure, targeted-decision perf, examples         |
| `diplomatic-action-reference.md` | Scripted diplomatic actions: files, ROOT/THIS/PREV scopes    |
| `dynamic-modifier-tooltips.md`   | `adds_` vs `modifies_dynamic_modifier_tt` tooltips           |
| `energy-power-balance.md`        | Power-per-cost + tech S-curves; read before energy edits     |
| `entity-system.md`               | Mesh→entity→animation chain, pdxmesh naming, landmarks       |
| `event-reference.md`             | Event types, TT*IF*\* tooltips, `random_events` dispatch     |
| `faction-rules.md`               | `common/factions/rules/`: rule types and trigger scopes      |
| `focus-tree-reference.md`        | Focus structure, property order, bankruptcy-guard examples   |
| `formable-reference.md`          | Formable paths, AI ratchet, sentinel, cross-guards, traps    |
| `hoi4-data-structures.md`        | Variables, arrays, loops, collections, formatted loc         |
| `idea-reference.md`              | Idea structure: pictures, tiered naming, `name =` gotchas    |
| `known-false-positives.md`       | Intentional bug-lookalikes; review agents must skip them     |
| `localisation-rules.md`          | English `.yml` rules: BOM, file naming, key formatting       |
| `md-custom-modifiers.md`         | Non-vanilla modifier keys, grouped by category               |
| `meta-effect-patterns.md`        | `meta_effect`/`meta_trigger` dispatch; `[!]` tooltips        |
| `mio-reference.md`               | MIO structure, per-block modifier keys, trait-grid rules     |
| `music-system.md`                | Stations, playlists, chance weights, radio GUI wiring        |
| `namelist-reference.md`          | Division/ship name-list files and mandatory groups           |
| `oob-equipment-reference.md`     | OOB equipment types (NSB), stockpiles, variant errors        |
| `oob-variants-reference.md`      | Full OOB + variant reference (`history/units/`)              |
| `performance-patterns.md`        | Hoisting, dirty counters, clamp-before-divide, early-outs    |
| `refactor-checklist.md`          | Rename/migration sweeps: namespaces, GUI/GFX refs, tags      |
| `scripted-gui-patterns.md`       | `dynamic_lists`, loc dispatchers, dirty-var standard         |
| `scripted-gui-rules.md`          | scripted_gui mechanics: structure, dirty-var perf, AI        |
| `scripting-edge-cases.md`        | Niche pitfalls: temp-var defaults, `^index`, vacant office   |
| `search-filters.md`              | Every `FOCUS_FILTER_*`, Israel subcats, common mistakes      |
| `simplification-patterns.md`     | Lookups→arrays, parameterized loc, shared helpers            |
| `sound-system.md`                | Sound defs, combat sounds, voicelines, compressors           |
| `typo-watchlist.md`              | Recurring localisation typos to check in review              |
| `un-system-reference.md`         | UN votes/elections: invariants, new-resolution recipe        |
| `validation-pipeline.md`         | Pre-commit vs CI validator divergence; deprecation watch     |

Detail moved out of the table:

- `agent-conventions.md` anti-rules: no proactive validators, no AI attribution, stay in scope, never guess identifiers.
- `ai-equipment-reference.md` role-template structure keys: `category`/`roles`/`priority`.
- `entity-system.md` landmark buildings: state-file placement, `map/buildings.txt` spawn points, `provinces.bmp` validation, heightmap-calibrated y, rendering gotchas; plus a division-designer performance note.
- `formable-reference.md` paths: 23 decision formables, EU111 USoE, EU112 EFS, UAR, Yugoslavia, United States of Africa, Event Horizon, focus-tree unions; plus known traps and maintenance rules.
- `music-system.md` stations: Main, Regional, UKR-RUS war, Synthwave.
- `scripted-gui-patterns.md`: the dirty-variable standard is `update_<system>_dirty_variable`; checkbox swap = filter-checkbox image swap; ✓/✗ tooltips are per-entry.
- `scripting-edge-cases.md` holds niche pitfalls moved out of the always-loaded `general-rules.md`, including per-effect scope interpolation for `add_to_war` / `add_*_opinion_modifier` / `add_relation_modifier` (FROM in events fired from on_actions or `random_scope_in_array` defaults to the firing scope).
- `sound-system.md` also covers adding voicelines and audio-file requirements.

## AI Agent Definitions

Agents live in `.claude/agents/` (10 definitions); the session agent list carries their descriptions.

## Repository Access

Use `gh` CLI for GitHub operations: `gh issue list`, `gh pr list`, `gh pr view`, `gh api`
