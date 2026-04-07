# Event Reference

On-demand reference for event structure, examples, and patterns. For best practices, see CLAUDE.md.

## Example: Basic Triggered Event

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

## Example: Per-Option Log Messages

Each option's log must match its own ID — copy-paste errors are common:

```
country_event = {
	id = israel.66
	title = israel.66.t
	desc = israel.66.d
	picture = GFX_report_event_Arrest_3
	is_triggered_only = yes

	option = {
		name = israel.66.a
		log = "[GetDateText]: [This.GetName]: israel.66.a executed"  # .a not .b
		# ...
	}

	option = {
		name = israel.66.b
		log = "[GetDateText]: [This.GetName]: israel.66.b executed"  # .b not .a
		# ...
	}
}
```

## Example: Multi-Option Cross-Country Event

Events fired to another country should have AI weighting based on opinion/influence, not random chance:

```
country_event = {
	id = israel.68
	title = israel.68.t
	desc = israel.68.d
	picture = GFX_specops_isr
	is_triggered_only = yes
	trigger = {
		original_tag = PAL
	}

	option = { # reject
		name = israel.68.a
		log = "[GetDateText]: [This.GetName]: israel.68.a executed"
		# rejection effects...
		ISR = {
			country_event = { id = israel.70 days = 1 }
		}
		ai_chance = {
			base = 15
			modifier = {
				factor = 0
				sender_influence_higher_30 = yes
			}
			modifier = {
				add = 10
				has_opinion = { target = ISR value < -15 }
			}
		}
	}

	option = { # accept
		name = israel.68.b
		log = "[GetDateText]: [This.GetName]: israel.68.b executed"
		# acceptance effects...
		ISR = {
			country_event = { id = israel.69 days = 1 }
		}
		ai_chance = {
			base = 0
			modifier = {
				add = 5
				factor = 2
				sender_influence_higher_5 = yes
			}
		}
	}
}
```

## Historical Events (ETD System)

Trigger date-based events via `common/scripted_effects/00_yearly_effects.txt`:

```
# First year events
MD_event_on_startup_events = {
	CAM = { country_event = { id = Cameroon.1 days = 50 random_days = 50 } }
}

# Specific year events
trigger_year_2067_events = {
	USA = { country_event = { id = collapse_event.1 days = 30 random_days = 336 } }
}
```

When the intended recipient may no longer own the target state, use the owner-guard pattern (check expected owner, fall back to `random_country = { limit = { owns_state = X } }`).

## Treasury/Debt/Productivity Effects

Commonly used in event options:

```
# Modify treasury
set_temp_variable = { treasury_change = -10.00 }
modify_treasury_effect = yes

# Preset expenditures
small_expenditure = yes    # medium_expenditure, large_expenditure

# Modify debt
set_temp_variable = { debt_change = 0.1 }
modify_debt_effect = yes

# Adjust productivity
set_temp_variable = { temp_productivity_change = 0.025 }
flat_productivity_change_effect = yes
```

## Content Guidelines for Events

- All events targeting another nation need AI weighting based on opinion/influence
- Aim for 10-15 flavour events per country — gameplay should not be "click focus, wait"
- Cross-nation permanent effects should come from events (give target player agency)
- Use `is_triggered_only = yes` for all triggered events — never open-fire MTTH events

For the full scripted effects library, see `docs/src/content/resources/code-resource.md`.
