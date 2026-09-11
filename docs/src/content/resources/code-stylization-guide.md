---
title: Code Stylization Guide
description: Millennium Dawn's Code Stylization Guide
---

Write code another contributor can understand without reconstructing your intent.
Keep the change local, reuse existing behavior, and add only what the task needs.

## Keep It Simple

- Prefer plain names and direct control flow over clever or compressed code.
- Add a helper only when it removes meaningful duplication or clarifies a required boundary.
  Do not turn a few clear lines into a one-use wrapper.
- Query existing game state instead of maintaining flags that mirror it. Keep flags
  for historical transitions or state the engine cannot otherwise answer.
- Keep behavior-preserving cleanup separate from gameplay changes.
- Remove unused code and commented-out blocks. Add a comment only for a non-obvious
  reason, in one short line. Do not narrate the code.

### Names and Encoding

Country-specific variables and flags use `TAG_`; global state uses `GLOBAL_`; shared
systems use their domain prefix. Use `snake_case` after the prefix and keep system
acronyms uppercase. Match identifier case exactly.

Script `.txt` files use UTF-8 without BOM. English localisation `.yml` files use
UTF-8 with BOM. Python tools must preserve LF when writing; see
[Maintaining Tools](https://github.com/MillenniumDawn/Millennium-Dawn/blob/main/tools/README.md#maintaining-tools).

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
| Ideas       | Keep picker gates on slotted ideas, use `allowed_civil_war`    |
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
- **Tooltip Duplication**: Never duplicate logic in `effect_tooltip` + `for_each_scope_loop`. Use `tooltip = TT_ALL_*` inside the loop instead, this eliminates double-evaluation and prevents drift between tooltip text and actual execution.
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

## Tree Layout

Focus trees are laid out **horizontally**: every branch gets its own `x` lane, placed side by side. Examples are China and France

- Leave a clear gap between lanes so branch boundaries read at a glance
- Position focuses inside a lane with `relative_position_id` off the branch root, so the whole branch
  can be shifted sideways by moving one focus
- Place `continuous_focus_position = { x = ... y = ... }` clear of the branch lanes

## Focus Shortcuts

Shortcuts render as jump buttons above the tree and are the main navigation aid for players who
cannot fit the whole tree on screen. Every tree gets roughly one shortcut per branch lane. Keep it around 4 - 6

They are declared at `focus_tree` level, not inside a `focus`, directly after
`continuous_focus_position`:

```hoiscript
# Focus Shortcuts
shortcut = {
    name = political_shortcut_title
    target = FRA_state_of_french_politics
    scroll_wheel_factor = 0.80
}
```

- `name` is a localisation key, `target` is the branch root focus `id`
- `scroll_wheel_factor = 0.80` is the Millennium Dawn standard, keep it identical on every shortcut

### Standard Shortcut Tooltips

Reuse these shared keys for the four common branch types instead of writing tag-prefixed ones. They
live in `localisation/english/MD_misc_l_english.yml` and are already translated in every language:

| Key                        | Tooltip             |
| -------------------------- | ------------------- |
| `political_shortcut_title` | Political           |
| `economy_shortcut_title`   | Economy             |
| `military_shortcut_title`  | Military            |
| `diplomacy_shortcut_title` | Foreign Interaction |

Write a custom `TAG_name_shortcut` key only when a branch genuinely is not one of those four, for
example `AFG_civil_war_shortcut`. Custom keys go in that country's `MD_focus_TAG_l_english.yml`.

`common/national_focus/05_france.txt` is the reference tree using the standard keys end to end.

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
- Lay branches out in horizontal lanes and give every branch a `shortcut`, reusing the standard
  shortcut tooltip keys where they fit
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

    prerequisite = { focus = SER_western_approach }

    search_filters = { FOCUS_FILTER_POLITICAL }

    available = { western_liberals_are_in_power = yes }

    completion_reward = {
        log = "[GetDateText]: [Root.GetName]: Focus SER_free_market_capitalism"
        add_ideas = SER_free_market_idea
    }

    ai_will_do = { base = 1 }
}
```

Write only the properties the focus uses. An empty commented-out slot marker
(`# bypass = { }`) is dead code, and `standardize.py focus` deletes it.

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

    ai_will_do = { base = 10 }
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
- **Remove** the whole `allowed` block from an idea in a category with no slot (`country`, `hidden_ideas`). Nothing picks from those categories, so `add_idea` is the only way in and it never consults `allowed`. The gate does nothing no matter what is inside it
- **Keep** `allowed = { always = no }` on slotted ideas that must not appear in the picker (religion and other laws). `add_idea` still applies them. Missing `allowed` means everyone sees the idea in the list
- **Remove** `cancel = { always = no }` - checked hourly, never true; redundant default
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

- Place opening braces on the same line as the keyword
- Put closing braces on their own line at the outer indent, except for simple one-line blocks
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

- Keep trait x positions at or below 9. Negative x is allowed; y is not capped
- Use relative positioning within the grid

---

# Related Resources

- [Code Resources](/dev-resources/code-resource/) - Modifiers and effects
- [Dynamic Modifiers](/dev-resources/dynamic-modifiers/) - Dynamic modifier tooltip usage
- [Claude Code Skills](/dev-resources/claude-code-skills/) - AI-assisted development tools
- [Game Rules](/player-tutorials/game-rules/) - Game rule reference
