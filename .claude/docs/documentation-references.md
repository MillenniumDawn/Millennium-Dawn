# Documentation References

## Local Documentation (`resources/documentation/`)

Authoritative offline references for HOI4 scripting. Read these to look up valid effects, triggers, modifiers, or other engine features.

| File                                 | Contents                                                                          |
| ------------------------------------ | --------------------------------------------------------------------------------- |
| `effects_documentation.md`           | All effects by scope (COUNTRY, STATE, CHARACTER, etc.)                            |
| `triggers_documentation.md`          | All triggers by scope                                                             |
| `modifiers_documentation.md`         | All modifiers by category (army, navy, air, country, state, etc.)                 |
| `dynamic_variables_documentation.md` | Read-only dynamic variables (global, country, state, unit_leader, MIO)            |
| `loc_formatter_documentation.md`     | Localization formatters (`idea_desc`, `tech_effect`, `country_leader_desc`, etc.) |
| `loc_objects_documentation.md`       | Localization scope objects (Country, State, Character, etc.) and their properties |
| `script_collection_input.md`         | Collection inputs (`game:all_countries`, `game:all_states`, `game:scope`, etc.)   |
| `script_collection_operator.md`      | Collection operators (`faction_members`, `owned_states`, `limit`, etc.)           |
| `script_concept_documentation.md`    | Script concepts: bindable loc, formatted loc, collections, script constants       |
| `console_commands_documentation.md`  | Console commands and tweakable variables                                          |

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

| File                                      | Contents                                                                                                                                                                                                                                                                                      |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `.claude/docs/entity-system.md`           | Mesh → entity → animation chain, three-level lookup, `gfx/entities/` organisation, pdxmesh naming, division designer performance note. Also landmark buildings: state-file placement, `map/buildings.txt` spawn points, `provinces.bmp` validation, heightmap-calibrated y, rendering gotchas |
| `.claude/docs/music-system.md`            | Music: `.asset` definitions, `.txt` playlists, all MD stations (Main, Regional, UKR-RUS war, Synthwave), chance weight logic, adding tracks, radio station GUI wiring                                                                                                                         |
| `.claude/docs/sound-system.md`            | Sound: `sound`/`soundeffect` definitions, combat sounds, country voicelines (23 countries), categories/compressors, adding voicelines, audio file requirements                                                                                                                                |
| `.claude/docs/search-filters.md`          | Complete `search_filters` reference: every `FOCUS_FILTER_*`, Israel-specific filter mapping, subcategory logic for ISRMILITARY/ISRECON, common mistakes checklist                                                                                                                             |
| `.claude/docs/simplification-patterns.md` | Replacing N-branch lookups with arrays, parameterized scripted loc, shared helpers, meta_effect consolidation                                                                                                                                                                                 |
| `.claude/docs/performance-patterns.md`    | Hoisting invariants, temp-variable booleans, GUI dirty counters, engine arrays, clamp-before-division, early-out guards                                                                                                                                                                       |
| `.claude/docs/tokenization-patterns.md`   | `token:` references, `[?array^i.GetTokenKey]` runtime substitution, `meta_effect` / `meta_trigger` for collapsing N-branch dispatch into one parameterized call, keeping `[!]` tooltips alive                                                                                                 |
| `.claude/docs/scripted-gui-patterns.md`   | Data-driven catalogs via `dynamic_lists` + scripted-loc dispatchers, MD dirty-variable standard (`update_<system>_dirty_variable`), filter checkbox image-swap, per-entry tooltips with ✓/✗                                                                                                   |
| `.claude/docs/refactor-checklist.md`      | Breaking-change checks for prefix renames, array migrations, event namespace, GUI/GFX cross-references, scope safety                                                                                                                                                                          |
| `.claude/docs/oob-equipment-reference.md` | OOB equipment type mapping (NSB vs non-NSB), stockpile syntax, chassis/variant validation, common errors                                                                                                                                                                                      |
| `.claude/docs/pr-conventions.md`          | PR descriptions: concise structure (Summary / Why / Risk / Test plan), length budget, what NOT to include (marketing language, AI attribution footers, exhaustive change logs)                                                                                                                |

## AI Agent Definitions

| File                                     | Purpose                                                                                                                                                                |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `.claude/agents/simplify-analyzer.md`    | Analyze and simplify a single file; applies `/simplify` skill with HOI4-specific rules                                                                                 |
| `.claude/agents/performance-analyzer.md` | Scan files or branch diffs for HOI4 performance anti-patterns: unbounded loops, per-frame visible blocks, GUI dirty misuse, unhoisted invariants, missing clamp guards |

## Repository Access

Use `gh` CLI for GitHub operations: `gh issue list`, `gh pr list`, `gh pr view`, `gh api`
