# Decision Reference

On-demand reference for decision structure and examples. For best practices, see AGENTS.md.

Full HOI4 wiki reference: https://hoi4.paradoxwikis.com/Decision_modding

## Icon Field

The decision `icon = X` field accepts **either** the bare sprite stem **or** the fully-qualified `GFX_decision_` name — the engine auto-prepends `GFX_decision_` when resolving a bare name. Both render identically:

```
icon = generic_political_discourse              # resolves to GFX_decision_generic_political_discourse
icon = GFX_decision_generic_political_discourse # explicit, same result
```

The bare form is the dominant convention in this codebase (e.g. `generic_decision`, `political_actions`, `generic_nationalism`). **Do not "fix" a bare decision icon by adding the `GFX_decision_` prefix — it is not broken.** Only flag an icon when neither `GFX_decision_<name>` nor `GFX_<name>` exists in any `interface/*.gfx` file. (Decision **category** icons and most other contexts still require the explicit `GFX_` sprite name — this auto-prefix shortcut is specific to the decision `icon` field.)

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

**Don't repeat the category's `allowed` on each decision.** A decision's `allowed` is redundant when it just duplicates the parent category's `allowed` (e.g. both are `original_tag = TAG`) — the category gate already applies to every decision inside it. Restrict the nation once on the category; put dynamic conditions in `available`/`visible` (since `allowed` is locked at game start).

### Performance Optimization

**Always move ROOT-only conditions from `visible` to `target_root_trigger`.** Single most impactful decision optimization:

- `visible` runs every tick, for every target — O(ticks × targets)
- `target_root_trigger` runs once daily, ROOT only — O(1/day)

When `target_root_trigger` is false, the engine skips `target_trigger`, `visible`, and `available` entirely for all targets.

**Rules:**

- Conditions that only check ROOT (flags, focuses, ideas, original_tag) belong in `target_root_trigger`
- Conditions that reference `FROM` must stay in `target_trigger` or `visible`
- Dynamic flags like `has_country_flag = flag_@FROM` reference FROM to build the name — these need `target_trigger` (not `target_root_trigger`)
- `hidden_trigger` is redundant inside `target_root_trigger` — it never generates tooltips
- `always = yes` inside `target_root_trigger` is a no-op — remove it
- Never restate what the target list already guarantees: with an explicit `targets = { ... }`, `NOT = { tag = ROOT }` and `NOT = { original_tag = X }` for a tag outside the list are dead conditions evaluated once per target per day

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
		FROM = { has_idea = my_idea }
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

## Effect Block Logging

The engine runs four blocks as a decision's effects: `complete_effect` (player takes it), `remove_effect` (`days_remove` timer expires or `remove_trigger` fires), `timeout_effect` (mission `days_mission_timeout` expires) and `cancel_effect` (`cancel_trigger` fires). Each one logs its own line, as the block's first statement:

```
	log = "[GetDateText]: [Root.GetName]: Decision DECISION_ID"
```

Log first so the game log reads in firing order, and use the decision's own ID: a copied ID from a neighbouring decision is the most common mistake here (`tools/linting/fix_log_ids.py` rewrites those). A log nested inside an `if` / `else` / `hidden_effect` records which branch ran, so it belongs where it sits and does not substitute for the block's own log line.

`validate_decisions.py` reports a block with no log as `missing-decision-log` and a block-level log that is not first as `decision-log-not-first`. A log that is the _only_ content of a `complete_effect` is a separate mistake: `check_common_mistakes.py` rejects it, because the block does nothing but log. Delete the dead block instead.

## AI-Only Decisions

A decision is **AI-only** when the engine can never show it to a human player. Two forms count:

- an unconditional `is_ai = yes` at the top level of the decision's own `visible`, `available` or `allowed` block, or
- membership in a decision **category** whose `visible` / `available` / `allowed` carries that same unconditional `is_ai = yes`.

```
	SOV_nuke_europe = {
		allowed = { original_tag = SOV }

		visible = {
			is_ai = yes
		}
```

"Unconditional" means the token sits at brace depth zero of the trigger block. Nested inside `OR`, `AND`, `if = { limit = }` or a scoped `TAG = { }` it is conditional and the decision is **not** AI-only — `allowed = { OR = { is_ai = yes  is_debug = yes } }` still shows to a player in debug, and `GRE = { is_ai = yes }` asks about a different country entirely.

**An AI-only decision takes no localisation.** Nothing renders its name or tooltip, so a key for it is dead weight that later has to be translated. The raw ID surfacing in the decision UI is harmless because no human ever opens that tab. `validate_decisions.py` enforces both directions: an AI-only decision is exempt from `missing-decision-localisation`, and a key that does exist for one is reported as `ai-only-decision-localisation`. Both are WARNING-severity. `custom_cost_text` is exempt from the reverse check, since it can point at a scripted-loc key shared with player-facing decisions.

Decision **categories** are not covered — nothing validates category localisation at all, in either direction.

## Randomised Effects

A decision that can fire more than once and rolls randomness (`random_list = { ... }` or `random = { chance = N ... }`) needs `fixed_random_seed = no` at decision top level:

```
	days_re_enable = 180

	fixed_random_seed = no

	remove_effect = {
```

The engine seeds the roll from the save state, so without it every repeat of the decision returns the same branch. `fire_only_once = yes` decisions are exempt, since their roll only ever resolves once. Write `fixed_random_seed = yes` when the repeat _should_ be deterministic; `validate_decisions.py` treats an explicit value either way as intentional and only flags the field being absent.

## Formable Commitment Ratchet

The AI commits to one formable at a time via two country variables: `formable_committed_id` (unique ordinal per formable) and `formable_committed_size` (that formable's full `update_flag` state count). Without this, a country holding territory for two formables alternates their zero-cost `update_flag` decisions forever.

Every decision in `common/decisions/formable_nation_decisions.txt` carries an AI-only `ai_will_do` gate — *blocked when committed to a different formable that is not strictly smaller*:

```
	modifier = {
		factor = 0
		NOT = { check_variable = { formable_committed_id = <ID> } }
		check_variable = {
			var = formable_committed_size
			value = <SIZE>
			compare = greater_than_or_equals
		}
	}
```

Commit writes (`hidden_effect` setting both variables) live in every `integrate_start` and `update_flag` `complete_effect`; IBR/ANZ (which have no `integrate_start`) commit from their integrate decisions' `remove_effect`, and Spain's `SPR_solidify_the_iberian_union` focus commits IBR — those delayed/ungated sites guard the write with `compare = less_than` so they never downgrade a larger commitment. NORDEM/AVG/ANZ gates carry an extra exemption so a CANZUK commitment stranded by the EU guard cannot block its fallback formables, and `CANZUK_integrate_start` is AI-blocked while EU-blocked.

A **new formable** must wire all of this: gate on every decision, commit in `integrate_start`/`update_flag`, a fresh unique id, and size = its `update_flag` state-list count. **Editing an `update_flag` state list requires updating that formable's size literal at every gate/commit site.** `validate_decisions.py` (`validate_formable_commitment_sync`) recomputes the counts and gates on any drift, missing gate, or id collision — including the Spain focus literals.

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

	ai_will_do = { base = 10 }
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
		log = "[GetDateText]: [Root.GetName]: Decision ISR_pal_rooting_terrorists"
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
# Party popularity — defaults to the ruling party when party_index is unset
set_temp_variable = { party_popularity_increase = 0.10 }
change_relative_party_popularity = yes

# Or target a specific party by index (0-23)
set_temp_variable = { party_index = 2 }
set_temp_variable = { party_popularity_increase = 0.10 }
change_relative_party_popularity = yes

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

# Foreign influence (requires target; tag_index defaults to ROOT.id)
set_temp_variable = { percent_change = 5 }
set_temp_variable = { influence_target = GER }
change_influence_percentage = yes
```

For the full scripted effects library, see `docs/src/content/resources/scripted-effects-reference.md`.
