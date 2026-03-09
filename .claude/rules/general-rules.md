# File Encoding

- All `.txt` files (focus trees, events, decisions, ideas, etc.) must be saved as **UTF-8 without BOM**.
- Only `.yml` localisation files use UTF-8 **with** BOM.
- When creating or editing `.txt` files, never add a BOM byte sequence (`EF BB BF`).

# Documentation References

## Local Documentation (`resources/documentation/`)

Authoritative offline references for HOI4 scripting. Read these when you need to look up valid effects, triggers, modifiers, or other engine features.

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

## Repository Access

Use `gh` CLI for GitHub operations: `gh issue list`, `gh pr list`, `gh pr view`, `gh api`
