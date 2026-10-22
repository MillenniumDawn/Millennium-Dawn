# Performance Patterns

For hot paths: daily on_actions, AI events, decision `visible` blocks, and GUI refreshes.

## Hoist invariant lookups out of loops

Cache what does not change per iteration. A `CONTROLLER = { ... }` scope switch inside a
state loop runs once per state. Repeated triggers such as `has_idea` are lookups. A
`check_variable` on a temp is a plain comparison.

```
set_temp_variable = { tgt_avail_civs = num_of_available_civilian_factories }
set_temp_variable = { tgt_has_war = 0 }
if = { limit = { has_war = yes } set_temp_variable = { tgt_has_war = 1 } }

for_each_scope_loop = {
    array = controlled_states
    if = {
        limit = {
            check_variable = { tgt_avail_civs > 15 }
            check_variable = { tgt_has_war = 0 }
        }
        # score logic
    }
}
```

## Early-out guards

Put cheap checks before a heavy loop. Skipping the whole loop saves more than any
optimization inside it.

## Engine arrays over `every_country`

`every_country` walks every tag. `neighbors`, `subjects`, `faction_members`, and `allies`
are engine-maintained. The list is in `hoi4-data-structures.md`.

```
for_each_scope_loop = {
    array = neighbors
}
```

## GUI `dirty` counters

Never bind a scripted GUI's `dirty` to `global.date`, `global.num_days`, or anything on
a timer. It redraws the GUI every tick. Bind it to a counter bumped only when the
backing data changes. Standard shape: `scripted-gui-patterns.md`.

## Decision `visible` blocks

Decision `visible` is evaluated every frame while the tab is open. Replace a loop or a
long condition list with a flag set and cleared where the precondition changes:

```
visible = { has_country_flag = TAG_my_decision_visible }
```

Character `visible` blocks run only on AI assignment pulses and UI opens. There,
`has_completed_focus` costs the same as a flag check. Do not add a flag to replace it.

## `ai_strategy` enable math

`enable` blocks are re-evaluated far more often than daily. Move heavy arithmetic into a
periodic effect that stores the result, and let `enable` read the variable:

```
division_limiter = {
    enable = { check_variable = { num_divisions > division_limiter_limit } }
}
```

This is for arithmetic only. A boolean condition is not heavy math.

## Live trigger over a daily cached flag

A flag refreshed on a daily pulse costs an on_action pass and lags game state by a day.
When the condition is a few cheap checks, use a scripted trigger (`ai_is_threatened` is
the reference). If readers sit in a hot loop, cache the result as a 0 or 1 temp first.

## Clamp before division

```
clamp_temp_variable = { var = construction_speed min = 0.01 }
divide_temp_variable = { building_cost = construction_speed }
```

## `while_loop_effect`

The `limit` is evaluated before each iteration. The engine stops at 1000 iterations and
`max_iterations` is not a valid key. Use `for_loop_effect` when the bound is known.

## No duplicated tooltip and loop

Do not repeat a loop's body in an `effect_tooltip`. The engine evaluates both. Use the
loop's `tooltip` parameter. Pattern: `simplification-patterns.md`.
