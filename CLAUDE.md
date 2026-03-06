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

## Validation & Formatting Tools

Validation and standardization tools are available in `tools/validation/` and `tools/standardization/`. Use the `/validate` and `/standardize` skills above for quick access, or run the scripts directly — both directories have READMEs with full usage details.

A standalone diff summary script is also available: `tools/review-branch.sh [base-branch]`.

## General Formatting Rules

- Use **tabs** for indentation (not spaces), increase by 1 on `{`, decrease by 1 on `}`
- Keep simple checks on one line: `available = { has_country_flag = some_flag }`
- Opening `{` stays on the same line as the property; closing `}` gets its own line at the outer indentation level
- 1 blank line between elements
- Remove unused/commented-out code
- Use multiplication instead of division (e.g., `* 0.01` not `/ 100`)
- Use variables instead of magic numbers

## Performance Tips

- Avoid open-fire MTTH events (always use `is_triggered_only = yes`)
- Use tag-specific on_actions (`on_daily_TAG`) instead of global triggers
- Use dynamic modifiers sparingly; avoid `force_update_dynamic_modifier`
- Replace `every_country`/`random_country` with specific array triggers
- Only log when there are meaningful effects (logging causes I/O overhead)

## Focus Trees

### File Naming

| Prefix   | Usage                                        |
| -------- | -------------------------------------------- |
| `00_`    | System requirements only (e.g., titlebar)    |
| `01-04_` | Shared/joint trees (EU, African Union, etc.) |
| `05_`    | Country-specific trees                       |

The prefix number forces load order: shared trees load before country-specific ones.

### Focus Tree Container

```
focus_tree = {
	id = greece_focus

	country = {
		factor = 0
		modifier = {
			tag = GRE
			add = 100
		}
	}

	shared_focus = USoE001
	shared_focus = POTEF001

	continuous_focus_position = { x = 2350 y = 1200 }
}
```

### Required Property Order

```
1.  id                          (always first)
2.  icon                        (always second)
3.  x, y coordinates
4.  relative_position_id
5.  cost
6.  allow_branch
7.  prerequisite / mutually_exclusive
8.  search_filters
9.  available / bypass / cancel
10. will_lead_to_war_with       (only if giving war goal)
11. select_effect / completion_reward / bypass_effect
12. ai_will_do                  (ALWAYS LAST)
```

### Best Practices

- Focus ID format: `TAG_focus_name_here`
- Use `relative_position_id` for positioning
- Always include logging: `log = "[GetDateText]: [Root.GetName]: Focus TAG_focus_name"`
- Always include `ai_will_do` with game options checks
- Always include `search_filters`
- Omit default values: `cancel_if_invalid = yes`, `continue_if_invalid = no`, `available_if_capitulated = no`
- Avoid empty `mutually_exclusive` and `available` blocks
- Limit permanent effects to 5; use timed ideas for more
- Use scripted effects and triggers where applicable
- Implement starting ideas that weaken nations, resolvable through focus trees/decisions

### Example Focus

```
focus = {
	id = SER_free_market_capitalism
	icon = blr_market_economy

	x = 5
	y = 3
	relative_position_id = SER_free_elections

	cost = 5

	# allow_branch = { }
	prerequisite = { focus = SER_western_approach }
	# mutually_exclusive = { }
	search_filters = { FOCUS_FILTER_POLITICAL }

	available = {
		western_liberals_are_in_power = yes
	}
	# bypass = { }
	# cancel = { }

	# will_lead_to_war_with = TAG  # Only if granting a war goal
	# complete_tooltip = { }        # Only if always-visible tooltip is needed
	# select_effect = { }
	completion_reward = {
		log = "[GetDateText]: [Root.GetName]: Focus SER_free_market_capitalism"
		add_ideas = SER_free_market_idea
	}
	# bypass_effect = { }

	ai_will_do = {
		base = 1
	}
}
```

## Decisions

### Best Practices

- Use `fire_only_once` only when necessary
- Include logging in `complete_effect`: `log = "[GetDateText]: [Root.GetName]: Decision DECISION_ID"`
- Structure with clear `visible` and `available` conditions
- Include `ai_will_do`

### Example Decision

```
URA_world_opr = {
	allowed = { original_tag = URA }
	icon = GFX_decision_sovfed_button

	cost = 50
	days_remove = 400

	visible = {
		country_exists = OPR
		OPR = {
			OR = {
				has_autonomy_state = autonomy_republic_rf
				has_autonomy_state = autonomy_kray_rf
			}
		}
	}

	complete_effect = {
		log = "[GetDateText]: [Root.GetName]: Decision URA_world_opr"
		OPR = { country_event = { id = subject_rus.121 days = 1 } }
	}

	ai_will_do = {
		factor = 10
	}
}
```

## Events

### Best Practices

- Always use `is_triggered_only = yes` for triggered events
- Log only if there are actual effects in the option
- Use `major = yes` sparingly (news events only)
- Trigger date-based events via `common/scripted_effects/00_yearly_effects.txt`

### Example Event

```
country_event = {
	id = france_md.504
	title = france_md.504.t
	desc = france_md.504.d
	picture = GFX_france_mcdonalds_bombing
	is_triggered_only = yes

	option = {
		name = france_md.504.a
		log = "[GetDateText]: [This.GetName]: france_md.504.a executed"
		set_party_index_to_ruling_party = yes
		set_temp_variable = { party_popularity_increase = -0.01 }
		add_relative_party_popularity = yes

		ai_chance = {
			base = 1
		}
	}

	option = {
		name = france_md.504.b
		ai_chance = {
			base = 0
		}
	}
}
```

## Ideas

### Best Practices

- Include `allowed_civil_war = { always = yes }` for civil war tags
- **Remove** `allowed = { always = no }` - this is the default and hurts performance
- **Remove** `cancel = { always = no }` - checked hourly, never true
- **Remove** empty `on_add = { log = "" }` unless actually doing something
- Log in `on_add` only when making changes

### Example Idea

```
BRA_idea_higher_minimum_wage_1 = {
	name = BRA_idea_higher_minimum_wage
	allowed_civil_war = { always = yes }

	picture = gold

	modifier = {
		political_power_factor = 0.1
		stability_factor = 0.05
		consumer_goods_factor = 0.075
		population_tax_income_multiplier_modifier = 0.05
	}
}
```

## Military-Industrial Organizations (MIO)

### Best Practices

- Name MIOs with `TAG_organization_name` format
- Always include `allowed = { original_tag = TAG }` to restrict to the correct country
- Set `task_capacity` proportional to nation size (typically 10–25)
- Equipment types must reference valid `equipment_type` categories
- Trait grid runs `y = 0` to `y = 9`; use relative positioning for trait layout
- Add `initial_trait` for the organization's defining bonus

### Example MIO

```
CHI_norinco_manufacturer = {
	allowed = { original_tag = CHI }
	icon = GFX_idea_Norinco_CHI

	task_capacity = 18

	equipment_type = {
		infantry_weapons_type
		artillery_equipment
		mio_cat_all_armor
	}

	research_categories = {
		CAT_infrastructure
		CAT_armor
		CAT_artillery
	}

	initial_trait = {
		name = CHI_norinco_company_trait
		equipment_bonus = {
			reliability = 0.03
			build_cost_ic = -0.03
		}
	}
}
```

## Localization Files (.yml)

- 1-space indentation
- Remove trailing 0/1 after colons (use `key: "value"` not `key:0 "value"`)
- UTF-8 with BOM encoding required

### Subideology Localization Format

```
TAG.ideology: "£PARTY_ICON (ABBRV) - Party Name"
TAG.ideology_icon: "£PARTY_ICON"
TAG.ideology_desc: "(Ideology Group) - Party Name (Native Name, ABBRV)\n\nDescription"
```

## Key Resources

- [Code Stylization Guide](./docs/dev-resources/code-stylization-guide.md) - Full formatting reference
- [Code Resources](./docs/dev-resources/code-resource.md) - Modifiers, effects, and how-to guides
- [Focus Tree Lifecycle](./docs/dev-resources/focus-tree-lifecycle-checklist.md) - Development checklist
- [Game Rules Reference](./docs/player-tutorials/game-rules.md) - Complete game rules guide
- [Error Debug Codes](./docs/dev-resources/error-debug-codes.md)
- [Contributing Guidelines](./CONTRIBUTING.md)
