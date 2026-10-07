# Decision Reference

Use `ai_will_do = { base = N }`, not a root-level `factor`, for AI weights. Wiki:
<https://hoi4.paradoxwikis.com/Decision_modding>. Scripted effects library:
`docs/src/content/resources/scripted-effects-reference.md`.

## Icon

A decision `icon = X` takes the bare sprite stem or the full `GFX_decision_` name. The
engine prepends `GFX_decision_` to a bare name. The bare form is the codebase
convention. Do not "fix" it by adding the prefix. Flag an icon only when neither
`GFX_decision_<name>` nor `GFX_<name>` exists in `interface/*.gfx`. Category icons and
most other contexts need the explicit `GFX_` name.

## Targeted decisions

A decision is targeted when it has `targets`, `target_array`, `target_trigger`, or
`target_root_trigger`. It clones itself per valid target. `ROOT` takes the decision and
`FROM` is the target.

| Block                 | Scope       | Frequency          |
| --------------------- | ----------- | ------------------ |
| `allowed`             | ROOT        | Once at game start |
| `target_root_trigger` | ROOT only   | Daily              |
| `target_trigger`      | ROOT + FROM | Daily, per target  |
| `visible`             | ROOT + FROM | Every tick         |
| `available`           | ROOT + FROM | Every tick         |

- When `target_root_trigger` is false, the engine skips `target_trigger`, `visible`, and
  `available` for every target. Move every ROOT-only condition there from `visible`.
- Conditions that read `FROM` stay in `target_trigger` or `visible`. That includes
  dynamic flags such as `has_country_flag = flag_@FROM`.
- `hidden_trigger` and `always = yes` do nothing inside `target_root_trigger`.
- Do not restate what the target list guarantees. With an explicit `targets = { ... }`,
  `NOT = { tag = ROOT }` is a dead condition evaluated per target per day.
- Do not repeat the category's `allowed` on each decision. Restrict the nation once on
  the category and put dynamic conditions in `available` or `visible`.

```
targets = { TAG TAG ... }        # Explicit list
target_array = array_name        # Array on ROOT, or global.array_name
targets_dynamic = yes            # Include civil war tags
target_non_existing = yes        # Include non-existing countries
state_target = yes               # Target states instead of countries
```

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

A state-targeted decision adds `state_target = yes`, a state array such as
`target_array = GER.core_states`, and `on_map_mode = map_and_decisions_view`.

`war_with_on_*` does not work with `FROM`. Use `war_with_target_on_complete`,
`war_with_target_on_remove`, or `war_with_target_on_timeout`.

## Effect block logging

`complete_effect`, `remove_effect`, `timeout_effect`, and `cancel_effect` each log their
own line as the first statement, using the decision's own id:

```
 log = "[GetDateText]: [Root.GetName]: Decision DECISION_ID"
```

- A copied id from a neighboring decision is the common mistake.
  `tools/linting/fix_log_ids.py` rewrites those.
- A log nested in an `if` or `hidden_effect` records which branch ran. It does not
  replace the block's own log.
- A block whose only content is a log is dead. Delete the block.

## AI-only decisions

A decision is AI-only when a human can never see it:

- an unconditional `is_ai = yes` at brace depth zero of its own `visible`, `available`,
  or `allowed`, or
- membership in a category gated the same way.

`is_ai = yes` nested in `OR`, `AND`, `if`, or a tag scope is conditional, and the
decision is not AI-only.

An AI-only decision or category takes no localisation and no tooltip wrappers. Nothing
renders them, and a key would still have to be translated. Write the trigger bare:

```
  available = {
   nationalist_monarchists_are_in_power = no
   check_variable = { party_pop_array^23 < 0.35 }
  }
```

Exceptions: `custom_cost_text` may share a scripted-loc key with player-facing
decisions, and a category named by `unlock_decision_category_tooltip` renders its name.

## Announcing unlocks

A category gated on state that flips during play appears part-way through a game. The
effect that opens it should say so:

```
 completion_reward = {
  set_country_flag = ALG_drone_program_open
  unlock_decision_category_tooltip = ALG_drone_program_category
 }
```

- `unlock_decision_category_tooltip` takes a bare category token that must exist. A
  stale name logs `Invalid Decision Category`.
- `unlock_decision_tooltip = <decision>` announces one decision. The block form
  `{ decision = X show_effect_tooltip = yes }` also previews its effects.
- A block that announces one unlock should announce every sibling gated on the flag it
  just set.
- The gate must sit at brace depth zero of `visible` to count. Inside a `NOT` the
  meaning inverts.
- Categories with no `visible`, or gated only on tag or date, have nothing to announce.
  AI-only categories are exempt.

## Randomised effects

A repeatable decision that rolls `random_list` or `random` needs
`fixed_random_seed = no` at decision top level. The engine seeds the roll from the save
state, so without it every repeat returns the same branch. `fire_only_once = yes`
decisions are exempt. Write `fixed_random_seed = yes` when the repeat should be
deterministic.

## Formables

Every decision in `formable_nation_decisions.txt` carries the AI commitment gate, and a
new formable must wire gates, commits, a unique id, and its size. See
[formable-reference.md](formable-reference.md).

## Example: basic decision

```
URA_world_opr = {
 allowed = { original_tag = URA }
 icon = GFX_decision_sovfed_button

 cost = 50
 days_remove = 400

 visible = {
  country_exists = OPR
 }

 complete_effect = {
  log = "[GetDateText]: [Root.GetName]: Decision URA_world_opr"
  OPR = { country_event = { id = subject_rus.121 days = 1 } }
 }

 ai_will_do = { base = 10 }
}
```

## Example: mission with timeout

Missions use `activation` instead of player selection:

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
  hidden_effect = {
   clr_country_flag = ISR_start_operation
   if = {
    limit = { check_variable = { ISR_operation_success > 7 } }
    ISR = { country_event = israel.91 }
   }
   else = {
    ISR = { country_event = israel.92 }
   }
  }
 }
}
```

## Common scripted effects

```
# Spending laws, each with a decrease_ twin
increase_centralization = yes
increase_social_spending = yes
increase_education_budget = yes
increase_healthcare_budget = yes
increase_policing_budget = yes
increase_exports = yes
increase_military_spending = yes

# Party popularity. Defaults to the ruling party when party_index (0-23) is unset
set_temp_variable = { party_popularity_increase = 0.10 }
change_relative_party_popularity = yes

# Ban or unban a party
set_temp_variable = { party_index = 1 }
ban_party_scripted_call = yes

# Domestic influence
set_temp_variable = { percent_change = 10 }
change_domestic_influence_percentage = yes

# Foreign influence. tag_index defaults to ROOT.id
set_temp_variable = { percent_change = 5 }
set_temp_variable = { influence_target = GER }
change_influence_percentage = yes
```
