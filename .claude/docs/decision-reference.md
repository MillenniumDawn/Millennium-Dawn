# Decision Reference

On-demand reference for decision structure and examples. For best practices, see CLAUDE.md.

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
