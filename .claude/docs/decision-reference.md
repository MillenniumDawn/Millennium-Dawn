# Decision Reference

On-demand reference for decision structure and examples. For best practices, see CLAUDE.md.

Full HOI4 wiki reference: https://hoi4.paradoxwikis.com/Decision_modding

## Targeted Decisions

A decision becomes targeted when it includes `targets`, `target_array`, `target_trigger`, or `target_root_trigger`. The decision clones itself for each valid target. `ROOT` is the country taking the decision; `FROM` is the target.

### Trigger Evaluation Order & Frequency

| Block                 | Scope       | Frequency                                    | Purpose                                       |
| --------------------- | ----------- | -------------------------------------------- | --------------------------------------------- |
| `allowed`             | ROOT        | Once (game start/load)                       | Permanent gate                                |
| `target_root_trigger` | ROOT only   | Daily                                        | Fast pre-filter — if false, skips all targets |
| `target_trigger`      | ROOT + FROM | Daily (only if `target_root_trigger` passes) | Per-target daily filter                       |
| `visible`             | ROOT + FROM | Every tick                                   | UI visibility (most expensive)                |
| `available`           | ROOT + FROM | Every tick                                   | Clickability gate                             |

### Performance Optimization

**Always move ROOT-only conditions from `visible` to `target_root_trigger`.** This is the single most impactful decision optimization:

- `visible` runs every tick, for every target — O(ticks × targets)
- `target_root_trigger` runs once daily, ROOT only — O(1/day)

When `target_root_trigger` is false, the engine skips `target_trigger`, `visible`, and `available` entirely for all targets.

**Rules:**

- Conditions that only check ROOT (flags, focuses, ideas, original_tag) belong in `target_root_trigger`
- Conditions that reference `FROM` must stay in `target_trigger` or `visible`
- Dynamic flags like `has_country_flag = flag_@FROM` reference FROM to build the name — these need `target_trigger` (not `target_root_trigger`)
- `hidden_trigger` is redundant inside `target_root_trigger` — it never generates tooltips
- `always = yes` inside `target_root_trigger` is a no-op — remove it

### Target Selection

```
targets = { TAG TAG ... }        # Explicit list of country tags
target_array = array_name        # Array on ROOT scope
target_array = global.array_name # Global array
targets_dynamic = yes            # Include civil war tags
target_non_existing = yes        # Include non-existing countries
state_target = yes               # Target states instead of countries
```

### Targeted Decision Example

```
my_targeted_decision = {
	target_root_trigger = {
		has_completed_focus = my_focus
	}
	targets = { BHR QAT SAU OMA YEM IRQ SYR LEB ISR PAL }
	targets_dynamic = yes
	target_trigger = {
		FROM = {
			has_idea = my_idea
		}
	}
	icon = my_icon
	cost = 20
	war_with_target_on_complete = yes
	complete_effect = {
		create_wargoal = {
			target = FROM
			type = annex_everything
		}
	}
}
```

### State-Targeted Decision Example

```
my_state_targeted_decision = {
	state_target = yes
	target_root_trigger = {
		has_completed_focus = my_focus
	}
	target_array = GER.core_states
	target_trigger = {
		FROM = { is_owned_by = ROOT }
	}
	on_map_mode = map_and_decisions_view
	icon = my_icon
	cost = 20
	complete_effect = {
		FROM = { remove_core_of = GER }
	}
}
```

### War with Target

Regular `war_with_on_*` does not work with FROM. Use these instead:

- `war_with_target_on_complete = yes`
- `war_with_target_on_remove = yes`
- `war_with_target_on_timeout = yes`

## Example: Basic Decision

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

## Example: Mission with Timeout (if/else Pattern)

Missions use `activation` instead of player selection, with `days_mission_timeout` and `timeout_effect`:

```
ISR_pal_rooting_terrorists = {
	available = { always = no }
	activation = {
		has_country_flag = ISR_start_operation
	}
	days_mission_timeout = 60
	is_good = no
	icon = GFX_decision_category_taliban_insurgency

	visible = {
		has_country_flag = ISR_start_operation
	}
	cancel_if_not_visible = yes

	timeout_effect = {
		custom_effect_tooltip = ISR_operation_result_outcome_tt
		custom_effect_tooltip = ISR_operation_failed_root_terr_tt
		hidden_effect = {
			clr_country_flag = ISR_start_operation
			if = {
				limit = {
					check_variable = { ISR_operation_success > 7 }
				}
				ISR = { country_event = israel.91 }
				PAL = { country_event = israel.91 }
			}
			else = {
				ISR = { country_event = israel.92 }
				PAL = { country_event = israel.92 }
			}
		}
	}
}
```

## Economic Scripted Effects

Commonly used in decision effects:

### Government Spending Laws

```
# Bureaucracy
increase_centralization = yes / decrease_centralization = yes

# Social Spending
increase_social_spending = yes / decrease_social_spending = yes

# Education
increase_education_budget = yes / decrease_education_budget = yes

# Healthcare
increase_healthcare_budget = yes / decrease_healthcare_budget = yes

# Policing
increase_policing_budget = yes / decrease_policing_budget = yes

# Trade Law
increase_exports = yes / decrease_exports = yes

# Military Spending
increase_military_spending = yes / decrease_military_spending = yes
```

### Political Effects

```
# Party popularity (index 0-23)
set_temp_variable = { party_index = 2 }
set_temp_variable = { party_popularity_increase = 0.10 }
add_relative_party_popularity = yes

# Or set to ruling party automatically
set_party_index_to_ruling_party = yes

# Ban/unban party
set_temp_variable = { party_index = 1 }
ban_party_scripted_call = yes
unban_party_scripted_call = yes
```

### Influence Effects

```
# Domestic influence
set_temp_variable = { percent_change = 10 }
change_domestic_influence_percentage = yes

# Foreign influence (requires target)
set_temp_variable = { percent_change = 5 }
set_temp_variable = { tag_index = ROOT }
set_temp_variable = { influence_target = GER }
change_influence_percentage = yes
```

For the full scripted effects library, see `docs/src/content/resources/code-resource.md`.
