# Focus Tree Reference

On-demand reference for focus tree structure, property order, and examples. For best practices, see CLAUDE.md.

## File Naming

| Prefix   | Usage                                        |
| -------- | -------------------------------------------- |
| `00_`    | System requirements only (e.g., titlebar)    |
| `01-04_` | Shared/joint trees (EU, African Union, etc.) |
| `05_`    | Country-specific trees                       |

The prefix number forces load order: shared trees load before country-specific ones.

## Focus Tree Container

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

## Required Property Order

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
10. completion_reward / select_effect / bypass_effect
11. ai_will_do                  (ALWAYS LAST)
```

## Example: Basic Focus

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

## Example: Bankruptcy Guard in `available`

High-cost focuses (cost >= 8, or cost >= 5 for military/economy/research) should block during financial collapse:

```
focus = {
	id = ISR_milk_and_honey
	icon = ISR_peace_isr

	x = 2
	y = 4
	relative_position_id = ISR_binational_state

	cost = 10

	search_filters = { FOCUS_FILTER_ISRPOLIT FOCUS_FILTER_POLITICAL }

	available = {
		NOT = { has_active_mission = bankruptcy_incoming_collapse }
		OR = {
			emerging_anarchist_communism_are_in_power = yes
			emerging_communist_state_are_in_power = yes
			# ...
		}
	}

	completion_reward = {
		log = "[GetDateText]: [This.GetName]: focus ISR_milk_and_honey executed"
		two_random_industrial_complex = yes
		two_state_infrastructure = yes
	}

	ai_will_do = {
		base = 3
	}
}
```

## Example: `available` Matching `bypass` Pattern

Never use `available = { always = no }` on a focus that also has a `bypass`. Set `available` to match or approximate the bypass condition:

```
focus = {
	id = ISR_operation_defensive_shield

	available = {
		has_country_flag = ISR_start_operation
	}

	bypass = {
		has_country_flag = ISR_start_operation
	}

	# ...
}
```

## Example: Cross-Country Event Tooltips

When a focus fires an event to another country, show both outcomes:

```
focus = {
	id = ISR_passover_massacre
	# ...
	completion_reward = {
		log = "[GetDateText]: [This.GetName]: focus ISR_passover_massacre executed"
		PAL = {
			country_event = {
				id = israel.68
				days = 1
			}
		}
		custom_effect_tooltip = TT_IF_THEY_REJECT
		effect_tooltip = {
			custom_effect_tooltip = oper_def_shiel_tt
		}
		custom_effect_tooltip = TT_IF_THEY_ACCEPT
		effect_tooltip = {
			custom_effect_tooltip = oper_city_wall_tt
		}
	}
}
```

## Example: `country_exists` Guard + Wargoal

Always check `country_exists` before targeting another country with wargoals:

```
focus = {
	id = ISR_down_with_imperialism
	# ...
	available = {
		country_exists = USA
		NOT = { has_war_with = USA }
		# ideology checks...
	}

	completion_reward = {
		log = "[GetDateText]: [This.GetName]: focus ISR_down_with_imperialism executed"
		set_temp_variable = { wargoal_on = USA }
		set_temp_variable = { wargoal_type = 1 }
		add_threat_from_wargoal_effect = yes
		create_wargoal = {
			type = topple_government
			target = USA
			expire = 365
		}
	}
}
```

## Building Effects (Scripted)

All buildings in effects need monetary cost — use scripted effects from `common/scripted_effects/00_scripted_effects.txt`, not raw `add_building_construction`.

### State Scope (predefined state)

```
117 = {
	one_state_industrial_complex = yes
}
```

### Random Scope (any owned state)

```
one_random_industrial_complex = yes
two_random_industrial_complex = yes
```

### Available Building Effects

| Building               | Random Effect                       | State Scope Effect                 |
| ---------------------- | ----------------------------------- | ---------------------------------- |
| Civilian Factory       | `one_random_industrial_complex`     | `one_state_industrial_complex`     |
| Military Factory       | `one_random_arms_factory`           | `one_state_arms_factory`           |
| Dockyard               | `one_random_dockyard`               | `one_state_dockyard`               |
| Offices                | `one_office_construction`           | `one_state_office_construction`    |
| Infrastructure         | `one_random_infrastructure`         | `one_state_infrastructure`         |
| Air Base               | `one_air_base`                      | `one_state_air_base`               |
| Network Infrastructure | `one_random_network_infrastructure` | `one_state_network_infrastructure` |
| Anti-Air/SAM           | `one_anti_air`                      | `one_state_anti_air`               |
| Radar                  | `one_radar_station`                 | `one_state_radar_station`          |
| Nuclear Reactor        | `one_random_nuclear_reactor`        | `one_state_nuclear_reactor`        |
| Agriculture District   | `one_random_agriculture_district`   | `one_state_agriculture_district`   |

### Building Costs (includes building slot at $1.00)

| Building                            | Cost   |
| ----------------------------------- | ------ |
| Civilian/Military Factory, Dockyard | $7.50  |
| Offices                             | $12.00 |
| Commercialized Agriculture          | $3.75  |
| Infrastructure                      | $3.50  |
| Air Base                            | $2.50  |
| SAM Site                            | $3.25  |
| Renewable Infrastructure            | $8.50  |
| Fuel Silo                           | $3.00  |
| Radar                               | $1.75  |
| Network Infrastructure              | $3.00  |
| Missile Site                        | $3.00  |
| Nuclear Reactor                     | $9.00  |
| Fossil Powerplant                   | $2.25  |
| Microchip Plant                     | $10.50 |
| Composite Plant                     | $7.50  |

Cost includes a building slot ($1.00). To give a building without a slot, subtract $1.00.

For the full scripted effects library (economic, political, influence, energy), see `docs/src/content/resources/code-resource.md`.
