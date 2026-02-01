---
layout: default
title: "Code Stylization Guide"
description: "Millennium Dawn's Code Stylization Guide"
---

# Table of Contents

- [Performance Tips](#performance-tips)
- [Focus Trees](#focus-trees)
- [Decisions](#decisions)
- [Events](#events)
- [Ideas](#ideas)
- [Code Formatting Rules](#code-formatting-rules)
- [Subideology Localization Format](#subideology-localization-format)
- [Military-Industrial Organisations (MIO)](#military-industrial-organisations-mio)

## Performance Tips

Generalized performance tips for the Millennium Dawn modding team.

- **Division**: Division is inherently more expensive than multiplication. If you do not need to divide, use multiplication instead. (Ex: Instead of dividing by 100, multiply by 0.01)
- **Logging**: Avoid excessive logging in events. Logging causes I/O overhead which can degrade performance on lower-end machines. Only log when there are meaningful effects being executed.
- **Checks**: Use simpler checks and early exit patterns to prevent unnecessarily complex evaluations. Structure conditions so that the most likely-to-fail or cheapest checks execute first.
- **Mean Time to Happen (MTTH)**: MTTH events without `is_triggered_only = yes` continuously evaluate and are extremely detrimental to performance. Avoid open-fire MTTH events unless specifically approved and necessary.
- **On Actions**: Ensure on actions are properly scoped using tag-specific variants (e.g., `on_daily_TAG` or `on_weekly_TAG`) rather than global triggers. Keep trigger conditions as simple and efficient as possible.
- **Cleanup**: If you are doing any work and you are not using something. Delete it. Don't just leave trash around in your code.

## Focus Trees

The following section delineates a stylization guide for Millennium Dawn and coding best practices for the Hearts of Iron IV feature "Focus Trees".

[Link to Focus Tree Modding Wiki](https://hoi4.paradoxwikis.com/National_focus_modding)

### Best Practices

- Use `relative_position_id` for focus alignment and tree positioning
- Implement logging in completion rewards: `log = "[GetDateText]: [Root.GetName]: Focus TAG_your_focus"`
- Avoid empty `mutually_exclusive` and `available` blocks
- Omit default values: `cancel_if_invalid = yes`, `continue_if_invalid = no`, `available_if_capitulated = no`
- Always include `ai_will_do` with historical game and game options checks
- Maintain consistent spacing (1 line between elements)
- Create balanced focus trees without clear military/economy/political branches
- Add search filters for all focuses
- Remove non-used code or commented out code if there is not intention to return to the tree section
- Utilize and review scripted effects and triggers where applicable
- Use variables instead of magic numbers
- Implement starting ideas that weaken nations, resolvable through focus trees/decisions.
  - This ensures there is a possible goal or focus to strive for to give the game some type of depth and consistency
- Limit permanent effects to 5, use timed ideas for additional effects
- Balance focus trees for flavor, not overpowering nations

### Millennium Dawn Specific Code Styling Requirements

- The focus tree file should start with one of the following requirements:
  - 00\_<name> for system requirements. This should only be reserved for specific contexts such as the titlebar_styles.txt file
  - 01/02/03/04\_<name> for shared or joint focus tress such as the European Union or the African Union
  - 05\_<name> for country specific focus trees
  - NOTE: The number does not mean anything, but it helps the team understand and forces a specific load order for focus trees. I.e. we can load all of the shared ones, but we cannot load country specific ones
- The ID of a focus should be the first line of the focus. It should also follow the standard `<TAG>_focus_name_here` pattern
- The icon should be second line of the of the focus
- The X and Y coordinates should be the next section of the focus tree definitions
- `relative_position_id` should be defined after the x and y coordinates
- `allow_branch` should be defined before `prerequisite` as it determines whether a focus branch is available in the first place (think of this like allowed)
- `prerequisite` and `mutually_exclusive` should be grouped together as they pertain to the section of the tree delineating structure of the focus tree
- `available`, `bypass` and `cancel` should be grouped together as these are specific to the triggers of a focus tree and as such should be grouped together
- `select_effect`, `completion_reward` and `bypass_effect` should be grouped together as these are specific to the effects of a focus tree
- `ai_will_do` is and always should be the last definition of the focus tree

Focus trees can be standardized using the script in tools using `standardize_focus_tree.py`.

### Example Focus Tree Structure

```python
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

```python
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

	# will_lead_to_war_with = TAG -- Only needed if you are giving a nation a war goal or preparing for conflict with another nation

	# complete_tooltip = { } -- This is not needed unless you want a specific thing always displayed
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

The following section delineates a stylization guide for the Millennium Dawn and coding best practices for the Hearts of Iron IV features Decisions/Missions.

[Link to Decision/Modding Wiki](https://hoi4.paradoxwikis.com/Decision_modding)

### Best Practices

- Use `fire_only_once` only when necessary
- Include proper logging in effects
- Structure decisions with clear visibility and availability conditions
- Implement proper AI behavior

### Example Decision Structure

```python
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
                has_autonomy_state = autonomy_oblast_rf
                has_autonomy_state = autonomy_okrug_rf
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

- Use `is_triggered_only` for triggered events
- Include proper logging
- Use `major = yes` sparingly for news events when you want them to truly be shown to the whole wide world.
- Structure events with clear options and effects
- **Performance:** Any events that do not have an effects in their triggered or option block do not require a log. Only log if there is something actually happening in the event.
- **Performance:** Any event that needs to be triggered by a date should be triggered via `00_yearly_effects.txt`.

### Example Event Structure

```python
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
        set_temp_variable = { temp_outlook_increase = -0.01 }
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

- Include `allowed_civil_war` for civil war tags
  - **NOTE**: `allowed_civil_war = { always = no }` is the default. There is no reason to add this since this is how they natively operate. Just dead code including it.
- Use proper logging in `on_add` where you are actually making changes via the on_add
  - You can exclude simple actions like adding or removing from an array unless you wish to log it for debug purposes
- Structure modifiers clearly
- Implement balanced effects
- **Performance**: Remove unnecessary `allowed = { always = no }` statements as they add drag to performance - since `always = no` is the default behavior, these lines provide no functional benefit while consuming processing resources
  - **NOTE**: This is still needed for any ideas that are not in the `country` or `hidden_ideas` idea categories
- **Performance**: Remove all `on_add` logs unless you need to do something in the on add like math or otherwise
- **Performance**: Do not add `cancel = { always = no }` in your ideas. This is checked hourly and will never be true.

### Example Country Idea Structure

```python
BRA_idea_higher_minimun_wage_1 = {
    name = BRA_idea_higher_minimun_wage
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

## Code Formatting Rules

### Indentation

- Increase tabulation by 1 when entering a new scope `{`
- Decrease tabulation by 1 when leaving a scope `}`
- Use tabs, not spaces
- Maintain consistent indentation

### Brackets

- Place closing brackets on the same line as the starting word
- Avoid excessive whitespace
- Keep simple checks on one line when appropriate

## Subideology Localization Format

```python
TAG.conservatism: "£PARTY_ICON (ABBRV) - NAME OF PARTY"
TAG.conservatism_icon: "£PARTY_ICON"
TAG.conservatism_desc: "(Dominant Ideology of the Party) - NAME OF PARTY (NAME OF LANGUAGES IN ALL NATIVE LANGUAGES FOR THE COUNTRY, ABBRV)\n\n(Description)"
```

Example:

```python
MOR.conservatism: "£MOR_NRI (RNI) - National Rally of Independents"
MOR.conservatism_icon: "£MOR_NRI"
MOR.conservatism_desc: "(Classic Liberalism) - National Rally of Independents (Arabic: Altajamue Alwataniu Lil'ahrar, French: Rassemblement National des Indépendants, Standard Moroccan Tamazight: Agraw Anamur y Insimann, RNI)\n\nNominally a social-democratic party, the party often cooperates with other parties with liberal orientation and is heavily described as pro-business and liberal. Formed in 1978 by then-Prime Minister Ahmed Osman the party has consistently remained a major player in Moroccan politics. Furthermore, the party is a national observer of the Liberal International and is affiliated with the Africa Liberal Network and the European People's Party."
```

## Military-Industrial Organisations (MIO)

### Guidelines on Companies

- Use one company for multiple categories.
- Add per category `5 OR 3 Task Capacity` if the company is not a national company but has factories in the country

### Example MIO Company Structure

```python
CHI_norinco_manufacturer = {
	allowed = { original_tag = CHI }
	icon = GFX_idea_Norinco_CHI

	task_capacity = 18

	equipment_type = {
		Inf_equipment
		artillery_equipment
		L_AT_Equipment
		H_AT_Equipment
		util_vehicle_equipment
		mio_cat_all_armor
		sam_missile_equipment
		guided_missile_equipment
	}

	research_categories = {
		CAT_infrastructure
		CAT_excavation_tech
		CAT_fuel_oil
		CAT_missile
		CAT_armor
		CAT_artillery
		CAT_inf
	}

	tree_header_text = {
		text = "Infantry Equipment & Mobility"
		x = 1
	}
	tree_header_text = {
		text = "Armored Vehicles & AFV Systems"
		x = 5
	}
	tree_header_text = {
		text = "Missiles, Air Defence & Drones"
		x = 8
	}

	initial_trait = {
		name = CHI_norinco_company_trait

		equipment_bonus = {
			reliability = 0.03
			build_cost_ic = -0.03
		}

		organization_modifier = {
			military_industrial_organization_research_bonus = 0.08
			military_industrial_organization_funds_gain = 0.02
		}
	}
}
```

### Guidelines on Traits

- The maximum grid is `y = 0 - 9` Don't forget this when you are using relative position.

### Example MIO Trait Structure

```python
trait = {
    token = CHI_norinco_trait_suppressed_pdw_systems
    name = CHI_norinco_trait_suppressed_pdw_systems
    icon = GFX_generic_mio_trait_icon_smallarms_attack

    relative_position_id = CHI_norinco_trait_field_proven_rifle_design
    position = { x = -1 y = 1 }
    all_parents = { CHI_norinco_trait_field_proven_rifle_design }

    limit_to_equipment_type = {
        Inf_equipment
    }

    equipment_bonus = {
        soft_attack = 0.06
        reliability = 0.02
    }

    on_complete = {
        if = {
            limit = {
                check_variable = { free_trait_picks > 0 }
            }
            add_to_variable = { free_trait_picks = -1 }
        }
        else = {
            FROM = {
                small_expenditure = yes
            }
        }
    }

    ai_will_do = {
        base = 10
        modifier = {
            factor = 0
            check_variable = { FROM.interest_rate > 8 }
        }
    }
}
```
