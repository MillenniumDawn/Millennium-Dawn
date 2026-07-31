# Scripting Edge Cases

Niche scripting pitfalls moved out of the always-loaded `general-rules.md`. Read this when editing influence code (`change_influence_percentage`), any function that uses `^index` array subscripts, or gates on elected/optional office holders.

## change_influence_percentage

The scripted effect uses temp-variable arguments with these defaults:

| Temp variable      | Required | Default   |
| ------------------ | -------- | --------- |
| `percent_change`   | yes      | —         |
| `tag_index`        | no       | `ROOT.id` |
| `influence_target` | no       | `THIS.id` |

Three pitfalls:

1. **Don't write redundant defaults.** `set_temp_variable = { tag_index = ROOT.id }` and `set_temp_variable = { influence_target = THIS.id }` are no-ops. Leave them out.
2. **Orphan setters are silent bugs.** A `percent_change` / `tag_index` / `influence_target` triple with no following `change_influence_percentage = yes` does nothing. When auditing influence code, grep for `percent_change` setters and confirm each has a matching invocation in the same scope.
3. **Loop-local temp vars need the call inside the loop.** Setting temp vars inside `random_other_country` / `random_country` / `every_country` then calling `change_influence_percentage = yes` outside the block runs the effect once with stale or undefined values. The invocation must live in the same scope as the temp-var writes.

```
# Wrong — call runs outside the loop; tag_index/influence_target resolve to outer scope
random_other_country = {
    limit = { ... }
    set_temp_variable = { percent_change = 3 }
    set_temp_variable = { tag_index = THIS.id }
    set_temp_variable = { influence_target = PREV.id }
}
change_influence_percentage = yes

# Correct — call inside the loop with the loop-local scopes
random_other_country = {
    limit = { ... }
    set_temp_variable = { percent_change = 3 }
    set_temp_variable = { tag_index = THIS.id }
    set_temp_variable = { influence_target = PREV.id }
    change_influence_percentage = yes
}
```

Also watch for typos in the temp-var name itself (e.g., `influence_tBRAet` from a botched search-and-replace) — the engine accepts any name, so a typo silently sets a never-read variable and the influence change uses the default `THIS.id` target.

## Array Index Semantics

When a function uses `^index` array subscripts, the **meaning of the index variable** must be obvious and consistent. Bugs arise when two different index types are stored in similarly-named variables.

| Variable name              | Should hold                  | Must NOT hold                                   |
| -------------------------- | ---------------------------- | ----------------------------------------------- |
| `project`, `slot`, `idx`   | Slot / array position (0..N) | Building type, category ID, or other lookup key |
| `type`, `kind`, `category` | Lookup key / type ID (1..N)  | Slot index                                      |

**Rule:** Document an array-index parameter in the function comment. Verify every caller passes the right kind of index. See `.claude/docs/refactor-checklist.md` for the full verification steps.

## Guard Gates on Optional / Elected Office Holders — Worked Example

The rule (`general-rules.md`): any gate on "the holder of office X" needs a defined branch for the vacant case, or it is unsatisfiable while nobody holds the office.

```
# Wrong — un-completable while every office holder is vacant
available = {
 any_of_scopes = { array = global.EU_potential  is_leader_of_EU_foreign_policy = yes }
 # ...influence requirement on the holder...
}

# Correct — fall back to a satisfiable bar when no holder exists
available = {
 OR = {
  AND = {
   any_of_scopes = { array = global.EU_potential  is_leader_of_EU_foreign_policy = yes }
   # ...influence requirement on the holder...
  }
  AND = {
   NOT = { any_of_scopes = { array = global.EU_potential  is_leader_of_EU_foreign_policy = yes } }
   # ...broad fallback so the path is never hard-locked...
  }
 }
}
```

Mirror the vacant case in the tooltip (e.g. "if no office is filled, this requires X instead"), and guard `var:`-stored country refs with `check_variable = { var:holder > 0 }` before scoping in — an uninitialized holder reads 0.

## Effect Scope Interpolation

Some effects accept `event_target:` / `tag` / scope tokens directly in their parameters; others require you to enter the target country as the current scope (typically `event_target:X = { ... }`) and reference the other party as `ROOT` / `PREV` / `THIS` inside the block. The behavior is per-effect, not per-mod.

| Effect                              | `target =` accepts `event_target:`? | Pattern                                                                 |
| ----------------------------------- | ----------------------------------- | ----------------------------------------------------------------------- |
| `add_to_war`                        | yes                                 | `add_to_war = { targeted_alliance = event_target:X enemy = event_target:Y }` at executor scope |
| `add_opinion_modifier`              | yes (in practice)                   | `add_opinion_modifier = { target = event_target:X modifier = foo }`     |
| `reverse_add_opinion_modifier`      | yes (in practice)                   | `reverse_add_opinion_modifier = { target = event_target:X modifier = foo }` |
| `add_relation_modifier`             | **no — tag literal only**          | enter scope: `event_target:X = { add_relation_modifier = { target = ROOT modifier = foo } }` |
| `send_equipment`                    | yes                                 | `send_equipment = { target = event_target:X ... }`                      |

**Rule of thumb:** when an effect has both an executor side and a `target =` side and the two countries must differ, open a scope block on the side whose `target =` would otherwise need a non-tag token. The executor side becomes `ROOT` / `PREV` from inside the block; the `target =` field takes the simple `TAG` form and is unambiguous.

## FROM in Events Fired From On Actions and `random_scope_in_array`

`country_event = { id = ... }` fired from inside an `on_declare_war` / `on_weekly_X` block or a `random_scope_in_array` has no explicit `FROM`. Inside the event, `FROM` falls back to the country that fired it — the executor (NATO leader, the on_action's ROOT, the looping scope) — not the country you actually want to reference. Effects that use `FROM` in this position silently no-op against self or self-apply opinion modifiers.

**Two fixes; pick by what reads cleanest:**

1. **Hidden routing dummy event.** Fire a `hidden = yes` event on the right scope (e.g. fire on the defender from the on_action) and let the dummy's `immediate` run the scope-selection logic and fire the visible event. The visible event's `FROM` is now the dummy's host (the defender) and the global event targets (`event_target:mnna_defender` etc.) carry the identity unambiguously. The on_action can also stamp a `custom_effect_tooltip` for the user.
2. **Defensive scope block in the option.** Even with a clean `FROM`, prefer `event_target:X = { ... }` blocks over `target = FROM` in effect calls — it works regardless of the firing chain and makes the relationship direction obvious to a reviewer.

Worked example (MNNA dilemma, `events/United States.txt` `department_of_state.232.a` + dummy `department_of_state.1000`):

```
# On-action (common/on_actions/99_USA_on_actions.txt on_declare_war)
if = {
    limit = {
        NOT = { has_global_flag = GAME_RULE_nato_disabled }
        FROM = { has_idea = Major_Non_NATO_Ally NOT = { is_subject_of = ROOT } }
        NOT = { has_government = democratic }
        NOT = { has_idea = NATO_member }
        NOT = { has_idea = Major_Non_NATO_Ally }
        any_of_scopes = { array = global.nato_members is_faction_leader = yes ... }
    }
    custom_effect_tooltip = MNNA_nato_may_intervene_in_this_conflict_tt
    hidden_effect = {
        save_global_event_target_as = mnna_aggressor
        FROM = {
            save_global_event_target_as = mnna_defender
            country_event = { id = department_of_state.1000 days = 3 }
        }
    }
}

# Hidden dummy (events/United States.txt)
country_event = {
    id = department_of_state.1000
    hidden = yes
    is_triggered_only = yes
    immediate = {
        random_scope_in_array = {
            array = global.nato_members
            limit = { is_faction_leader = yes NOT = { has_country_flag = collapsed_nation } ... }
            set_country_flag = { flag = mnna_event_cooldown days = 7 value = 1 }
            country_event = { id = department_of_state.232 days = 2 }
        }
    }
}

# Visible dilemma option .a — chained-PREV add_to_war + scope-block modifiers
option = {
    name = department_of_state.232.a
    add_war_support = 0.05
    add_political_power = -50
    event_target:mnna_defender = {
        add_opinion_modifier      = { target = ROOT modifier = usa_fp_major_alliance_support }
        reverse_add_opinion_modifier = { target = ROOT modifier = usa_fp_major_alliance_support }
        add_relation_modifier     = { target = ROOT modifier = generic_increased_military_support }
        hidden_effect = {
            event_target:mnna_aggressor = {
                ROOT = {
                    add_to_war = {
                        targeted_alliance = PREV.PREV   # = defender
                        enemy = PREV                    # = aggressor
                    }
                }
            }
        }
    }
}
```

Walking the chain: outer scope `THIS` = defender, `PREV` = ROOT. `event_target:mnna_aggressor = { ... }` re-points: `THIS` = aggressor, `PREV` = defender. `ROOT = { ... }` re-points again: `THIS` = ROOT (executor of `add_to_war`), `PREV` = aggressor, `PREV.PREV` = defender. Executor joins defender's war against aggressor. Correct.

**Audit checklist for any event fired from an on_action or `random_scope_in_array` (no explicit `FROM`):**

- `FROM` references — confirm they intend the firing scope, not a counterpart. If they intend a counterpart, switch to event targets.
- `add_to_war` calls — confirm executor vs. `targeted_alliance` vs. `enemy` resolves to three different countries where intended.
- `add_relation_modifier` — open a scope block; `target =` must be a tag literal.
- Mixed `add_opinion_modifier` + `add_relation_modifier` — open a scope block; works for both, clearer for the reviewer.
