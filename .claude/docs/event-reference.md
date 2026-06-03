# Event Reference

On-demand reference for event structure, examples, and patterns. For best practices, see CLAUDE.md.

In every example below, replace `TAG`, `tag_ns`, and the namespace number with your event's values. `tag_ns` is whatever the file declared via `add_namespace = ...` at the top.

## Example: Basic Triggered Event

```
country_event = {
	id = tag_ns.N
	title = tag_ns.N.t
	desc = tag_ns.N.d
	picture = GFX_some_picture
	is_triggered_only = yes

	option = {
		name = tag_ns.N.a
		log = "[GetDateText]: [This.GetName]: tag_ns.N.a executed"
		set_party_index_to_ruling_party = yes
		set_temp_variable = { party_popularity_increase = -0.01 }
		add_relative_party_popularity = yes

		ai_chance = { base = 1 }
	}

	option = {
		name = tag_ns.N.b
		ai_chance = { base = 0 }
	}
}
```

## Example: Per-Option Log Messages

Each option's log must match its own ID — copy-paste errors between `.a` and `.b` (or `.b` and `.c`) are common:

```
	option = {
		name = tag_ns.N.a
		log = "[GetDateText]: [This.GetName]: tag_ns.N.a executed"  # .a not .b
	}
	option = {
		name = tag_ns.N.b
		log = "[GetDateText]: [This.GetName]: tag_ns.N.b executed"  # .b not .a
	}
```

## Example: Multi-Option Cross-Country Event

When an event fires to a different country than the one that initiated the action, AI weighting must reflect that country's situation (opinion, influence, ideology), never base-only random chance. Here `SNDR` is the sender (whoever fired the event) and the receiver is the current scope (`This`):

```
country_event = {
	id = tag_ns.N
	title = tag_ns.N.t
	desc = tag_ns.N.d
	picture = GFX_some_picture
	is_triggered_only = yes
	trigger = {
		original_tag = TAG   # narrow to receiver if needed
	}

	option = { # reject
		name = tag_ns.N.a
		log = "[GetDateText]: [This.GetName]: tag_ns.N.a executed"
		# rejection effects...
		SNDR = { country_event = { id = tag_ns.M days = 1 } }   # tell sender we rejected
		ai_chance = {
			base = 15
			modifier = {
				factor = 0
				sender_influence_higher_30 = yes
			}
			modifier = {
				add = 10
				has_opinion = { target = SNDR value < -15 }
			}
		}
	}

	option = { # accept
		name = tag_ns.N.b
		log = "[GetDateText]: [This.GetName]: tag_ns.N.b executed"
		# acceptance effects...
		SNDR = { country_event = { id = tag_ns.K days = 1 } }   # tell sender we accepted
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

## News Events

News events use `news_event` (not `country_event`) and `major = yes` so all countries see them. Separate the namespace from the parent events (e.g., `add_namespace = my_news` alongside `add_namespace = my_events`).

Use option `trigger` blocks to give different response text to involved parties, regional neighbors, and the rest of the world. Every country must match exactly one option — ensure trigger conditions are exhaustive and mutually exclusive.

```
news_event = {
	id = my_news.1
	title = my_news.1.t
	desc = my_news.1.d
	picture = GFX_some_picture
	major = yes
	is_triggered_only = yes

	option = {
		name = my_news.1.a
		trigger = { original_tag = TAG }
	}
	option = {
		name = my_news.1.b
		trigger = {
			NOT = { original_tag = TAG }
			capital_scope = { is_on_continent = CONTINENT }
		}
	}
	option = {
		name = my_news.1.c
		trigger = {
			NOT = { original_tag = TAG }
			NOT = { capital_scope = { is_on_continent = CONTINENT } }
		}
	}
}
```

## Conditional Descriptions

Use `text =` inside desc blocks for conditional descriptions, **not** `desc =`:

```
# Correct
desc = {
	text = my_event.d_variant_a
	trigger = { has_global_flag = chose_option_a }
}

# Wrong — causes "Unexpected token: desc" error
desc = {
	desc = my_event.d_variant_a
	trigger = { has_global_flag = chose_option_a }
}
```

## Cross-Country Event Chains

When firing follow-up events to other countries, wrap in `hidden_effect` so chain consequences don't appear in the firing option's tooltip:

```
option = {
	name = my_event.a
	add_war_support = 0.05
	hidden_effect = {
		OTHER = { country_event = { id = my_event.2 days = 1 } }
		news_event = { id = my_news.1 days = 1 }
	}
	ai_chance = { base = 80 }
}
```

## `random_events` Dispatch (on_actions)

Events registered inside an `on_actions` `random_events = { … }` block are picked by **weighted roll against the `0 = N` "nothing happens" slot**, not by MTTH alone:

```
random_events = {
    2500 = 0          # weight assigned to "no event fires" this tick
    100 = brotherhood.6
    100 = brotherhood.7
}
```

- A single roll runs each tick the parent `on_action` fires. Each candidate's chance is `weight / sum_of_weights`. The `0` slot exists so most ticks produce nothing.
- `is_triggered_only = yes` events selected this way still check their own `trigger = { … }` block. If the trigger fails on the rolled country, **nothing fires that tick** — the roll does not retry. Tight triggers thin out effective fire rates a lot.
- **`mean_time_to_happen` is NOT dead inside `random_events`**: the engine multiplies the candidate's effective weight by the MTTH `factor` modifiers that match the rolled scope. This lets you globally register an event but still tune per-country pacing via MTTH modifier blocks (e.g., "fire 1.5× more often when `neutrality > 0.40`"). Keep MTTH blocks on events listed in `random_events` whenever you want per-country weight tuning.
- Prefer `random_events` over hand-rolled `random_list` inside on_action effects for systems that should fire across many countries — cheaper than iterating arrays and adds a uniform global cadence.

## Content Guidelines for Events

- All events targeting another nation need AI weighting based on opinion/influence
- Aim for 10-15 flavour events per country — gameplay should not be "click focus, wait"
- Cross-nation permanent effects should come from events (give target player agency)
- Use `is_triggered_only = yes` for all triggered events — never open-fire MTTH events

For the full scripted effects library, see `docs/src/content/resources/code-resource.md`.
