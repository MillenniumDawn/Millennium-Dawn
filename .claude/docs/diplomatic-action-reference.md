# Scripted Diplomatic Actions Reference

Scripted diplomatic actions live in `common/scripted_diplomatic_actions/`. All `.txt` files in that directory are loaded by the game. Current files:

- `00_scripted_diplomatic_actions.txt` — Core diplomatic actions (trade agreements, debt assumption, enforce peace, energy load sharing, embassies, etc.)
- `01_peace_deal_diplomatic_actions.txt` — Peace deal related actions
- `02_ai_attach_diplomatic_actions.txt` — AI attach/detach actions
- `MD_missile_scripted_diplomatic_actions.txt` — Missile-related diplomatic actions

## Scope Rules

In all blocks within a scripted diplomatic action:

| Keyword | Scope                                                                                                                           |
| ------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `ROOT`  | The **sender** (country initiating the action)                                                                                  |
| `THIS`  | The **target** (country receiving the action)                                                                                   |
| `PREV`  | Context-dependent — in `visible`/`selectable`, `PREV` inside a `ROOT = { }` block refers to `THIS` (the target), and vice versa |

**Important:** `selectable` evaluates in the **target's** scope by default. Bare conditions (without explicit `ROOT = { }` or `THIS = { }`) check `THIS`. Always be explicit about scope.

## Block Order & Structure

Every diplomatic action follows this block order:

```
action_name = {
	allowed = { }          # Game rule / DLC gates — checked once at game start
	visible = { }          # Whether the button appears at all — checked dynamically
	selectable = { }       # Whether the button is clickable (greyed out if false)

	cost = N               # Political power cost
	command_power = N      # Optional command power cost
	icon = N               # Icon index

	requires_acceptance = yes/no
	show_acceptance_on_action_button = yes/no

	send_description = LOC_KEY

	on_sent_effect = { }   # Fires when the player clicks send (before acceptance)
	complete_effect = { }  # Fires on acceptance (or immediately if no acceptance needed)
	reject_effect = { }    # Fires when target rejects

	accept_title = LOC_KEY
	accept_description = LOC_KEY
	reject_title = LOC_KEY
	reject_description = LOC_KEY

	ai_acceptance = { }    # AI weighting for accepting/rejecting
	ai_desire = { }        # AI weighting for initiating the action
}
```

## Cooldown Pattern

To prevent spamming a diplomatic action, use a timed country flag. The standard pattern:

### 1. Set the flag on completion and/or rejection

In `complete_effect` and `reject_effect`, set a timed flag on ROOT (the sender) scoped to the target:

```
ROOT = {
	set_country_flag = { flag = recently_did_action_@PREV value = 1 days = 90 }
}
```

- `@PREV` resolves to the target's ID since we're inside a `ROOT = { }` block where PREV = THIS (target).
- Use `days = 90` as the standard cooldown (adjust per action — e.g., 270 for energy load sharing rejections).
- Set the flag in **both** `complete_effect` and `reject_effect` if you want the cooldown regardless of outcome.

### 2. Check the flag in `visible`

Add the cooldown check in `visible` so the action is hidden during the cooldown:

```
visible = {
	ROOT = { NOT = { has_country_flag = recently_did_action_@PREV } }
	# ... other visibility conditions
}
```

**Why `visible` and not `selectable`?** Dynamic `@PREV`/`@THIS` flag references don't resolve reliably in `selectable`. Use `visible` for cooldown checks.

### 3. Block AI desire during cooldown

In `ai_desire`, add a `factor = 0` modifier:

```
modifier = {
	factor = 0
	ROOT = { has_country_flag = recently_did_action_@PREV }
}
```

## Pending Offer Pattern

To prevent a country from sending the same action to multiple targets simultaneously:

### 1. Set a variable in `on_sent_effect`

```
on_sent_effect = {
	ROOT = { set_variable = { pending_action_offer = PREV.id } }
}
```

### 2. Clear in `complete_effect` and `reject_effect`

```
ROOT = { clear_variable = pending_action_offer }
```

### 3. Block AI in `ai_desire`

```
modifier = {
	factor = 0
	ROOT = { NOT = { check_variable = { pending_action_offer = 0 } } }
}
```

Note: `NOT = { check_variable = { var = 0 } }` means "var is set and non-zero" — this is the standard idiom for "has a pending offer".

## AI Acceptance Structure

`ai_acceptance` uses named condition blocks. Each block has a `base` and optional `modifier` entries:

```
ai_acceptance = {
	base_condition_name = {
		base = -25       # Starting disposition
	}
	condition_two = {
		base = 0
		modifier = {
			add = 5
			is_same_government = yes
		}
	}
	# Opinion scaling pattern:
	condition_three = {
		base = 0
		modifier = {
			set_temp_variable = { opinion_calculator = opinion@ROOT }
			multiply_temp_variable = { opinion_calculator = 0.05 }
			check_variable = { opinion_calculator > -60 }
			add = opinion_calculator
		}
	}
	# Power ranking comparison blocks (common for coercive actions like enforce peace)
	difference_in_power_ranking = { ... }
}
```

## AI Desire Structure

`ai_desire` controls how eagerly the AI initiates the action. Standard gates:

```
ai_desire = {
	base = N
	# Positive modifiers (faction, opinion, power status)
	modifier = { add = 10  is_in_faction_with = ROOT }
	modifier = { add = 10  is_subject_of = ROOT }

	# Economic gates (graduated)
	modifier = { factor = 0.5  ROOT = { ai_has_minor_economic_problems = yes } }
	modifier = { factor = 0.1  ROOT = { ai_has_moderate_economic_problems = yes } }
	modifier = { factor = 0    ROOT = { ai_has_major_economic_problems = yes } }

	# Hard blocks
	modifier = { factor = 0  ROOT = { has_war = yes } }
	modifier = { factor = 0  ROOT = { NOT = { check_variable = { pending_offer_var = 0 } } } }
	modifier = { factor = 0  ROOT = { has_country_flag = cooldown_flag_@PREV } }
}
```

## Common Selectable Checks

- `embassy_with_root_closed = no` — embassies must be open
- `ERI_is_not_transitional_government = yes` — blocks during Eritrea transitional government
- `has_war_with_or_allies_have_war_with_ROOT = no` — no war between the parties or their allies
- `influence_higher_40 = yes` — ROOT must have 40+ influence on THIS
- Opinion checks: `has_opinion = { target = THIS/ROOT value > N }`

## Logging

Every `on_sent_effect`, `complete_effect`, and `reject_effect` should include a log line:

```
log = "[GetDateText]: [Root.GetName]: diplomatic action {block_name} {action_name}"
```

## Existing Actions

| Action                             | Requires Acceptance | Cooldown                 | Notes                                 |
| ---------------------------------- | ------------------- | ------------------------ | ------------------------------------- |
| `recall_volunteers`                | No                  | None                     | Player-only (`is_ai = no`)            |
| `propose_improved_trade_agreement` | Yes                 | 180d on reject           | Reject flag on both ROOT and THIS     |
| `cancel_trade_agreement`           | No                  | None                     | Sets 90d `has_recently_canceled` flag |
| `diplo_action_assume_debt`         | Yes                 | 90d AI cooldown          | AI-only cooldown flag                 |
| `propose_mutual_investment_treaty` | Yes                 | Similar to trade         | —                                     |
| `overlord_subsidies`               | Yes                 | 90d on reject            | Subject/overlord only                 |
| `negotiate_release`                | Yes                 | None                     | Subject release                       |
| `enforce_peace_option`             | Yes                 | 90d                      | Cooldown in visible + reject          |
| `propose_energy_load_sharing`      | Yes                 | 90d accept / 270d reject | Neighbor + energy deficit             |
| `request_energy_load_sharing`      | Yes                 | 270d on reject           | Reverse direction                     |
| `purchase_reactor_grade_material`  | Yes                 | —                        | Nuclear material trade                |
| `close_embassy` / `reopen_embassy` | No                  | —                        | Embassy management                    |
