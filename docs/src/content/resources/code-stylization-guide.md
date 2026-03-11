---
title: Code Stylization Guide
description: Millennium Dawn's Code Stylization Guide
---

This guide covers coding standards, best practices, and formatting rules for Millennium Dawn mod development.

> **Quick Tools**:
>
> - Run `python3 tools/standardization/standardize.py focus` to auto-format focus trees
> - Run `python3 tools/standardization/standardize.py event` to auto-format events
> - Run `python3 tools/standardization/standardize.py decision` to auto-format decisions
> - Run `python3 tools/standardization/standardize.py idea` to auto-format ideas

---

# Quick Reference

| Feature     | Key Rules                                                      |
| ----------- | -------------------------------------------------------------- |
| Focus Trees | Use `relative_position_id`, include logging, `ai_will_do` last |
| Decisions   | Include logging, use `fire_only_once` sparingly                |
| Events      | Use `is_triggered_only = yes`, log only if effects exist       |
| Ideas       | Remove `allowed = { always = no }`, use `allowed_civil_war`    |
| Formatting  | Tabs (not spaces), 1 line between elements                     |

---

# Performance Tips

These guidelines help keep the mod running smoothly:

- **Division vs Multiplication**: Use multiplication instead of division when possible (e.g., `* 0.01` instead of `/ 100`)
- **Logging**: Only log when there are meaningful effects. Logging causes I/O overhead
- **MTTH Events**: Avoid open-fire MTTH events (those without `is_triggered_only`). They continuously evaluate and hurt performance
- **On Actions**: Use tag-specific variants (`on_daily_TAG`) instead of global triggers
- **Dynamic Modifiers**: Use sparingly. Avoid `force_update_dynamic_modifier` as it causes lag
- **Arrays**: Replace `every_country`/`random_country` with specific array triggers
- **Cleanup**: Remove unused code and commented-out blocks

---

# Focus Trees

> **Reference**: [HOI4 Wiki - National Focus Modding](https://hoi4.paradoxwikis.com/National_focus_modding)

## File Naming

| Prefix   | Usage                                  |
| -------- | -------------------------------------- |
| `00_`    | System requirements only               |
| `01-04_` | Shared/joint trees (EU, African Union) |
| `05_`    | Country-specific trees                 |

The number forces load order (shared trees load before country-specific).

## Required Order Within a Focus

```
1. id (first line)
2. icon (second line)
3. x, y coordinates
4. relative_position_id
5. cost
6. allow_branch
7. prerequisite / mutually_exclusive
8. search_filters
9. available / bypass / cancel
10. completion_reward / select_effect / bypass_effect
11. ai_will_do (LAST)
```

## Best Practices

- Use `relative_position_id` for tree positioning
- Add logging: `log = "[GetDateText]: [Root.GetName]: Focus TAG_focus_name"`
- Omit default values: `cancel_if_invalid = yes`, `continue_if_invalid = no`
- Include `ai_will_do` with game options checks
- Add `search_filters` for all focuses
- Remove unused/commented code
- Limit permanent effects to 5, use timed ideas for more

## Example Focus

```hoiscript
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

---

# Decisions

## Best Practices

- Use `fire_only_once` only when necessary
- Include logging in `complete_effect`
- Structure with clear `visible` and `available` conditions
- Include `ai_will_do`

## Example Decision

```hoiscript
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

---

# Events

## Best Practices

- Use `is_triggered_only = yes` for triggered events
- Log only if there are actual effects in the block
- Use `major = yes` sparingly (for news events)
- Trigger date-based events via `common/scripted_effects/00_yearly_effects.txt`

## Example Event

```hoiscript
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

---

# Ideas

## Best Practices

- Include `allowed_civil_war = { always = yes }` for civil war tags
- **Remove** `allowed = { always = no }` - this is the default and hurts performance
- **Remove** `cancel = { always = no }` - checked hourly, never true
- **Remove** empty `on_add = { log = "" }` unless you're actually doing something
- Log in `on_add` only when making changes

## Example Idea

```hoiscript
BRA_idea_higher_minimum_wage_1 = {
    name = BRA_idea_higher_minimum_wage
	picture = gold
    allowed_civil_war = { always = yes }

    modifier = {
        political_power_factor = 0.1
        stability_factor = 0.05
        consumer_goods_factor = 0.075
        population_tax_income_multiplier_modifier = 0.05
    }
}
```

---

# Code Formatting

## Indentation

- Use **tabs**, not spaces
- Increase indent on `{`, decrease on `}`
- Keep consistent throughout

## Brackets

- Place closing brackets on the same line as the keyword
- Avoid excessive whitespace
- Keep simple checks on one line when appropriate

```hoiscript
# Good
available = { has_country_flag = some_flag }

# Avoid
available = {
    has_country_flag = some_flag
}
```

---

# Subideology Localization

Format for political party localization:

```hoiscript
TAG.ideology: "£PARTY_ICON (ABBRV) - Party Name"
TAG.ideology_icon: "£PARTY_ICON"
TAG.ideology_desc: "(Ideology Group) - Party Name (Native Name, ABBRV)\n\nDescription"
```

Example:

```hoiscript
MOR.conservatism: "£MOR_NRI (RNI) - National Rally of Independents"
MOR.conservatism_icon: "£MOR_NRI"
MOR.conservatism_desc: "(Classic Liberalism) - National Rally of Independents (Arabic: ..., RNI)\n\nParty description here."
```

---

# Military-Industrial Organizations (MIO)

## Company Structure

```hoiscript
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

## Trait Guidelines

- Maximum grid: `y = 0 - 9`
- Use relative positioning within the grid

---

# Related Resources

- [Code Resources](/dev-resources/code-resource) - Modifiers and effects
- [Game Rules](/player-tutorials/game-rules) - Game rule reference
