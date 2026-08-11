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

### Naming Scheme

Most filenames end in one of four suffixes: `-reference` (structure or valid-key lookup), `-rules` (must-follow conventions), `-patterns` (recipe/refactor catalogs), or `-system` (subsystem architecture). A handful of docs use a plain descriptive name instead when none of those fit (`agent-conventions.md`, `debug-commands.md`, `typo-watchlist.md`, `validation-pipeline.md`).

| File                                          | Contents                                                                                                                                                                                                                                                                                      |
| --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `.claude/docs/agent-conventions.md`           | Shared rules for every `.claude/agents/` definition: universal anti-rules (no proactive validators, no AI attribution, stay in scope, never guess identifiers) plus standard required reading                                                                                                 |
| `.claude/docs/ai-equipment-reference.md`      | AI equipment-variant files (`common/ai_equipment/`): role-template structure (`category`/`roles`/`priority`), `target_variant` matching, common coverage errors                                                                                                                               |
| `.claude/docs/ai-strategy-reference.md`       | Unit-production and AI strategy system: 5 evaluation layers, on_action entry points, the live `ai_is_threatened` trigger, strategy/template/plan file reference                                                                                                                               |
| `.claude/docs/bug-patterns.md`                | Deduplicated catalog of known MD/HOI4 bug patterns: greppable scan signatures for codebase sweeps, plus adversarial what-could-go-wrong questions for diff review                                                                                                                             |
| `.claude/docs/content-guidelines.md`          | On-demand content-quality checklist (economic, political, military, visual, AI) condensed from the full content-review and new-general guides                                                                                                                                                 |
| `.claude/docs/debug-commands.md`              | In-game console command recipes for testing MD systems, with a focus on the EU/USoE subsystem                                                                                                                                                                                                 |
| `.claude/docs/decision-reference.md`          | Decision structure, icon-field auto-prefix rule, targeted-decision trigger evaluation order/performance, common effect examples                                                                                                                                                               |
| `.claude/docs/diplomatic-action-reference.md` | Scripted diplomatic actions (`common/scripted_diplomatic_actions/`): file listing and ROOT/THIS/PREV scope rules                                                                                                                                                                              |
| `.claude/docs/dynamic-modifier-tooltips.md`   | Tooltip syntax for dynamic modifiers (`common/dynamic_modifiers/`): `adds_dynamic_modifier_tt` vs `modifies_dynamic_modifier_tt`                                                                                                                                                              |
| `.claude/docs/energy-power-balance.md`        | Power-per-build-cost model comparing renewable/nuclear/fossil plants and the tech S-curve design; read before touching power buildings or energy tech                                                                                                                                         |
| `.claude/docs/entity-system.md`               | Mesh → entity → animation chain, three-level lookup, `gfx/entities/` organisation, pdxmesh naming, division designer performance note. Also landmark buildings: state-file placement, `map/buildings.txt` spawn points, `provinces.bmp` validation, heightmap-calibrated y, rendering gotchas |
| `.claude/docs/event-reference.md`             | Event structure/examples (triggered, cross-country, news, historical ETD), the complete TT*IF*\* tooltip pattern, `random_events` dispatch mechanics                                                                                                                                          |
| `.claude/docs/faction-rules.md`               | `common/factions/rules/` conventions: rule types and their trigger scopes, derived from the engine's own `_documentation.md`                                                                                                                                                                  |
| `.claude/docs/focus-tree-reference.md`        | Focus tree structure, required property order, shared/joint focus conventions, bankruptcy-guard and building-effect examples                                                                                                                                                                  |
| `.claude/docs/hoi4-data-structures.md`        | Full reference for HOI4 variable types (persistent/temporary/global), arrays, loops, collections, and formatted loc                                                                                                                                                                           |
| `.claude/docs/idea-reference.md`              | Idea structure/example: picture requirement, tiered naming, `name =` loc-redirection gotchas                                                                                                                                                                                                  |
| `.claude/docs/known-false-positives.md`       | Patterns that look like bugs but are intentional; review/fix/simplify agents must skip them                                                                                                                                                                                                   |
| `.claude/docs/localisation-rules.md`          | English-only `.yml` editing rules: BOM/encoding, one-loc-file-per-country naming, key formatting                                                                                                                                                                                              |
| `.claude/docs/md-custom-modifiers.md`         | Full list of non-vanilla modifier keys defined in `common/modifier_definitions/`, grouped by category                                                                                                                                                                                         |
| `.claude/docs/meta-effect-patterns.md`        | `token:` references and `meta_effect`/`meta_trigger` runtime substitution for collapsing N-branch dispatch into one parameterized call, keeping `[!]` tooltips alive                                                                                                                          |
| `.claude/docs/mio-reference.md`               | MIO structure/example, valid modifier keys per block type (organisation/production/equipment), trait-grid layout rules                                                                                                                                                                        |
| `.claude/docs/music-system.md`                | Music: `.asset` definitions, `.txt` playlists, all MD stations (Main, Regional, UKR-RUS war, Synthwave), chance weight logic, adding tracks, radio station GUI wiring                                                                                                                         |
| `.claude/docs/namelist-reference.md`          | Quick reference for division/ship-hull/ship-class-design name-list files and their mandatory groups                                                                                                                                                                                           |
| `.claude/docs/oob-equipment-reference.md`     | OOB equipment type mapping (NSB vs non-NSB), stockpile syntax, chassis/variant validation, common errors                                                                                                                                                                                      |
| `.claude/docs/oob-variants-reference.md`      | Full OOB file structure (DLC-gated `history/units/` patterns) and equipment-variant reference; the complete version behind `oob-equipment-reference.md`'s quick lookup                                                                                                                        |
| `.claude/docs/performance-patterns.md`        | Hoisting invariants, temp-variable booleans, GUI dirty counters, engine arrays, clamp-before-division, early-out guards                                                                                                                                                                       |
| `.claude/docs/refactor-checklist.md`          | Breaking-change checks for prefix renames, array migrations, event/decision namespace, GUI/GFX cross-references, scope safety, country-tag removal                                                                                                                                            |
| `.claude/docs/scripted-gui-patterns.md`       | Data-driven catalogs via `dynamic_lists` + scripted-loc dispatchers, MD dirty-variable standard (`update_<system>_dirty_variable`), filter checkbox image-swap, per-entry tooltips with ✓/✗                                                                                                   |
| `.claude/docs/scripted-gui-rules.md`          | Raw scripted_gui mechanics: file-prefix naming, window/effects structure, dirty-variable performance rule, AI configuration blocks                                                                                                                                                            |
| `.claude/docs/scripting-edge-cases.md`        | Niche scripting pitfalls moved out of the always-loaded `general-rules.md`: `change_influence_percentage` defaults, `^index` array semantics, vacant-office gating, per-effect scope interpolation rules for `add_to_war` / `add_*_opinion_modifier` / `add_relation_modifier` (FROM in events fired from on_actions or `random_scope_in_array` defaults to the firing scope) |
| `.claude/docs/search-filters.md`              | Complete `search_filters` reference: every `FOCUS_FILTER_*`, Israel-specific filter mapping, subcategory logic for ISRMILITARY/ISRECON, common mistakes checklist                                                                                                                             |
| `.claude/docs/simplification-patterns.md`     | Replacing N-branch lookups with arrays, parameterized scripted loc, shared helpers, meta_effect consolidation                                                                                                                                                                                 |
| `.claude/docs/sound-system.md`                | Sound: `sound`/`soundeffect` definitions, combat sounds, country voicelines (23 countries), categories/compressors, adding voicelines, audio file requirements                                                                                                                                |
| `.claude/docs/typo-watchlist.md`              | Recurring localisation typos to check for during review                                                                                                                                                                                                                                       |
| `.claude/docs/un-system-reference.md`         | UN voting/membership/election system architecture: owning files, vote lifecycle invariants, the SC/GA vote-type catalog, and the recipe for adding a new resolution type                                                                                                                      |
| `.claude/docs/validation-pipeline.md`         | Pre-commit vs CI hook-set divergence: which validators are CI-only, pre-commit-only, or dual-wired, plus the tooling-deprecation watch                                                                                                                                                        |

## AI Agent Definitions

Agents live in `.claude/agents/` (10 definitions); the session agent list carries their descriptions.

## Repository Access

Use `gh` CLI for GitHub operations: `gh issue list`, `gh pr list`, `gh pr view`, `gh api`
