# Scripted Diplomatic Actions Reference

Files live in `common/scripted_diplomatic_actions/`.

## Scope

| Keyword | Scope                                                                |
| ------- | -------------------------------------------------------------------- |
| `ROOT`  | The sender                                                           |
| `THIS`  | The target                                                           |
| `PREV`  | Inside `ROOT = { }` it is the target, inside `THIS = { }` the sender |

`selectable` evaluates in the target's scope, so bare conditions check `THIS`. Always
write the scope explicitly.

## Structure

```
action_name = {
	allowed = { }          # Game rule and DLC gates, checked once at game start
	visible = { }          # Whether the button appears
	selectable = { }       # Whether the button is clickable

	cost = N               # Political power
	command_power = N      # Optional
	icon = N

	requires_acceptance = yes/no
	show_acceptance_on_action_button = yes/no

	send_description = LOC_KEY

	on_sent_effect = { }   # On send, before acceptance
	complete_effect = { }  # On acceptance, or at once when none is needed
	reject_effect = { }

	accept_title = LOC_KEY
	accept_description = LOC_KEY
	reject_title = LOC_KEY
	reject_description = LOC_KEY

	ai_acceptance = { }
	ai_desire = { }
}
```

Every `on_sent_effect`, `complete_effect`, and `reject_effect` logs:

```
log = "[GetDateText]: [Root.GetName]: diplomatic action {block_name} {action_name}"
```

## Cooldown

Set a timed flag on the sender, keyed to the target, in both `complete_effect` and
`reject_effect`:

```
ROOT = {
	set_country_flag = { flag = recently_did_action_@PREV value = 1 days = 90 }
}
```

Check it in `visible`, not `selectable`. Dynamic `@PREV` flag names do not resolve
reliably in `selectable`:

```
visible = {
	ROOT = { NOT = { has_country_flag = recently_did_action_@PREV } }
}
```

Block the AI in `ai_desire`:

```
modifier = {
	factor = 0
	ROOT = { has_country_flag = recently_did_action_@PREV }
}
```

## Pending offer

To stop the same action going to several targets at once, set a variable on send, clear
it on completion and rejection, and block the AI while it is set:

```
on_sent_effect = {
	ROOT = { set_variable = { pending_action_offer = PREV.id } }
}

ROOT = { clear_variable = pending_action_offer }

modifier = {
	factor = 0
	ROOT = { NOT = { check_variable = { pending_action_offer = 0 } } }
}
```

## AI acceptance

`ai_acceptance` holds named condition blocks, each with a `base` and optional
`modifier` entries:

```
ai_acceptance = {
	base_condition_name = {
		base = -25
	}
	condition_two = {
		base = 0
		modifier = {
			add = 5
			has_government = ROOT
		}
	}
	condition_three = {
		base = 0
		modifier = {
			check_opinion_calculation = yes
			add = opinion_calculator
		}
	}
}
```

### Mirror rule

The engine reads `ai_acceptance`. A scripted GUI cannot, so a GUI that shows the player
an acceptance breakdown mirrors the math by hand. Each new modifier needs three updates,
or the displayed score diverges from the real one:

1. The `ai_acceptance` block in the action file.
2. The mirror scripted trigger, which accumulates into a temp variable:

```
set_temp_variable = { X_factor_temp = 0 }
if = {
    limit = { ...same conditions as the engine modifier... }
    set_temp_variable = { X_factor_temp = N }
}
add_to_temp_variable = { X_acceptance_temp = X_factor_temp }
```

3. The breakdown line: a `defined_text`, its loc string
   (`X_ai_accept_factor_tt: "Factor Name: [?X_factor_temp|0+]\n"`), and a reference in
   the headline tooltip key.

Reference: `CPD_AI_will_accept_calculation` in `00_peace_deal_triggers.txt` and the
`CPD_ai_accept_*` texts.

## AI desire

```
ai_desire = {
	base = N
	modifier = { add = 10  is_in_faction_with = ROOT }

	modifier = { factor = 0.5  ROOT = { ai_has_minor_economic_problems = yes } }
	modifier = { factor = 0.1  ROOT = { ai_has_moderate_economic_problems = yes } }
	modifier = { factor = 0    ROOT = { ai_has_major_economic_problems = yes } }

	modifier = { factor = 0  ROOT = { has_war = yes } }
}
```

## Common `selectable` checks

- `embassy_with_root_closed = no`
- `ERI_is_not_transitional_government = yes`
- `has_war_with_or_allies_have_war_with_ROOT = no`
- `influence_higher_40 = yes`: ROOT has 40 or more influence on THIS.
- `has_opinion = { target = THIS value > N }`
