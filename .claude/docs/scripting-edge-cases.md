# Scripting Edge Cases

Engine traps and state checks for script authors and reviewers. Read the sections
relevant to the effects and triggers you are changing.

## Identifiers and Trigger Semantics

- Verify effects, modifiers, sprites, and triggers against their definitions. Existing
  usage alone is not proof that a name is valid. Match exact case, including file paths
  and unit names, for Linux compatibility.
- `NOT = { A B }` means not both, not neither. Use separate `NOT` blocks or
  `NOT = { OR = { A B } }` for neither. `NOR` is not a HOI4 trigger, and `NRY` is
  Norway's country tag, not a logical operator.
- `threat` uses a 0.0 to 1.0 scale. Write `threat > 0.40`, not `threat > 40`.
- `is_in_faction` accepts `yes` or `no`. Membership with a country uses
  `is_in_faction_with = TAG`. `add_to_faction = TAG` takes a country, not a faction name.
- MD trade agreements use `has_country_flag = trade_agreement@TAG`.
  `has_trade_agreement_with` is not a valid trigger.
- There is no `has_idea = democratic_*`. Check the ruling subideology through the
  matching scripted trigger: `western_conservatism_are_in_power`,
  `western_liberals_are_in_power`, `western_social_democrats_are_in_power`, or
  `western_autocrats_are_in_power`. Verify other parties in `common/scripted_triggers/`.
- Modifier names: use the engine reference or [MD Custom Modifiers](md-custom-modifiers.md).
  Sprites: resolve the `name` in `interface/*.gfx` and check its texture exists.

## Relief Must Reduce the Actual Penalty

Read the backing entry in `common/dynamic_modifiers/` before changing a penalty
variable. Cost-shaped keys get worse as the variable rises, so relief subtracts.
Bonus-shaped keys get worse as it falls, so relief adds. Do not copy one sign across
a mixed block of cost and bonus modifiers.

## Transfer Equipment Without Duplicating the Stockpile Writes

Use `send_equipment = { type = infantry_weapons_type amount = 2000 target = UKR }`
for a country-to-country transfer. It transfers what the sender holds and preserves
the producer. Subtracting and adding stockpiles separately duplicates the amount and
can overdraw the donor. Keep `add_equipment_to_stockpile` for purchases or deliveries
that deliberately change equipment type or variant.

## change_influence_percentage

| Temp variable      | Required | Default   |
| ------------------ | -------- | --------- |
| `percent_change`   | yes      |           |
| `tag_index`        | no       | `ROOT.id` |
| `influence_target` | no       | `THIS.id` |

- Do not write the defaults. `set_temp_variable = { tag_index = ROOT.id }` is a no-op.
- A setter with no following `change_influence_percentage = yes` does nothing.
- The call must sit in the same scope as the temp-var writes. Setters inside
  `random_other_country` with the call outside the block run the effect on stale values:

```
random_other_country = {
    limit = { ... }
    set_temp_variable = { percent_change = 3 }
    set_temp_variable = { tag_index = THIS.id }
    set_temp_variable = { influence_target = PREV.id }
    change_influence_percentage = yes
}
```

- A typo in the temp-var name sets a variable nothing reads, and the effect uses the
  default target.

## Array Index Semantics

Keep the two kinds of index apart. A slot variable (`project`, `slot`, `idx`) holds an
array position from 0. A type variable (`type`, `kind`, `category`) holds a lookup key
from 1. Neither may hold the other's. Document an array-index parameter in the effect's
comment and verify every caller passes the right kind. Steps:
`refactor-checklist.md`.

## damage_building / remove_building Need a Matching Presence Guard

Against a state that lacks the building, the engine logs an error and does nothing. At
raid and `random_list` scale the log spam costs performance. The guard must name the
same building as the effect:

```
# Wrong: guarded on an idea
if = {
    limit = { has_idea = SOV_foreign_cars_idea1 }
    652 = { remove_building = { type = industrial_complex level = 2 } }
}

# Correct: the building's own count trigger, in state scope
if = {
    limit = { fuel_silo > 0 }
    damage_building = { type = fuel_silo damage = 1 }
}
```

Also accepted: `non_damaged_building_level = { building = X level > 0 }` when damage
matters, a `random_list` bucket zeroed by `modifier = { factor = 0  X < 1 }`, and an
`any_core_state = { X > N }` pre-selection before a `random_core_state` pick.

## remove_dynamic_modifier Needs a Matching Presence Guard

Removing a dynamic modifier the scope does not carry logs an error and does nothing.
The guard must name the same modifier. A flag, idea, or variable proxy proves nothing:

```
if = { limit = { has_dynamic_modifier = { modifier = CHI_HKG_sinicization_modifier } } remove_dynamic_modifier = { modifier = CHI_HKG_sinicization_modifier } }
```

For a cross-scope removal, put the trigger inside the state the effect runs in:
`limit = { 215 = { has_dynamic_modifier = { modifier = X } } }`. A decision `available`
or an event `trigger` is not a guard.

## EU Game-Rule Guard on europeanism_change Calls

`europeanism_change`, `EU_europeanism_change`, and `EU_potential_europeanism_change`
carry the `GAME_RULE_eu_disabled` guard themselves. Call them with no wrapper:

```
set_temp_variable = { modify_europeanism = ... }
europeanism_change = yes
```

## Guard Gates on Optional or Elected Office Holders

A gate on an office holder needs a satisfiable branch for the vacant case, including
before the first election or after a timed idea expires. Otherwise the path locks while
nobody holds the office.

```
available = {
 OR = {
  AND = {
   any_of_scopes = { array = global.EU_potential  is_leader_of_EU_foreign_policy = yes }
   # requirement on the holder
  }
  AND = {
   NOT = { any_of_scopes = { array = global.EU_potential  is_leader_of_EU_foreign_policy = yes } }
   # broad fallback
  }
 }
}
```

Mirror the vacant case in the tooltip. Guard a `var:`-stored country with
`check_variable = { var:holder > 0 }` before scoping in, since an unset holder reads 0.

## Effect Scope Interpolation

Whether `target =` accepts `event_target:` is per effect.

| Effect                         | `target =` accepts `event_target:`? |
| ------------------------------ | ----------------------------------- |
| `add_to_war`                   | yes                                 |
| `add_opinion_modifier`         | yes                                 |
| `reverse_add_opinion_modifier` | yes                                 |
| `send_equipment`               | yes                                 |
| `add_relation_modifier`        | no, tag literal only                |

For `add_relation_modifier`, enter the scope:
`event_target:X = { add_relation_modifier = { target = ROOT modifier = foo } }`. When the
executor and the target must differ, open a scope block on the side whose `target =`
would need a non-tag token.

## FROM in Events Fired From On Actions and `random_scope_in_array`

A `country_event` fired from an on_action block or a `random_scope_in_array` has no
explicit `FROM`. Inside the event, `FROM` falls back to the country that fired it, not
the counterpart you meant. Effects using `FROM` there apply to the wrong country.

Two fixes:

1. Fire a `hidden = yes` routing event on the right scope and save global event targets
   first. Its `immediate` picks the recipient and fires the visible event. Reference:
   `department_of_state.1000` and `department_of_state.232` in
   `events/United States.txt`.
2. In the option, use `event_target:X = { ... }` blocks instead of `target = FROM`.

```
event_target:mnna_defender = {
    add_opinion_modifier = { target = ROOT modifier = usa_fp_major_alliance_support }
    add_relation_modifier = { target = ROOT modifier = generic_increased_military_support }
    hidden_effect = {
        event_target:mnna_aggressor = {
            ROOT = {
                add_to_war = {
                    targeted_alliance = PREV.PREV   # defender
                    enemy = PREV                    # aggressor
                }
            }
        }
    }
}
```

When auditing such an event, confirm every `FROM` means the firing scope, and that
`add_to_war` resolves executor, `targeted_alliance`, and `enemy` to three countries.
