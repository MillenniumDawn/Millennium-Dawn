# Performance Patterns for HOI4 Scripted Effects

Patterns for reducing CPU overhead in HOI4's script engine, especially daily-pulse code (on_actions, AI events, decision `visible` blocks).

## Hoist Invariant Lookups Out of Loops

When iterating states, countries, or any collection, cache values that don't change per-iteration.

### Before (per-state loop)

```
for_each_scope_loop = {
    array = controlled_states
    if = {
        limit = {
            CONTROLLER = {
                num_of_available_civilian_factories > 15
                num_of_military_factories < 10
                has_war = no
                has_country_flag = AI_is_threatened
            }
        }
        # ... score logic ...
    }
}
```

### After (hoisted before loop)

```
set_temp_variable = { tgt_avail_civs = num_of_available_civilian_factories }
set_temp_variable = { tgt_num_mils = num_of_military_factories }
set_temp_variable = { tgt_has_war = 0 }
if = { limit = { has_war = yes } set_temp_variable = { tgt_has_war = 1 } }
set_temp_variable = { tgt_AI_threatened = 0 }
if = { limit = { has_country_flag = AI_is_threatened } set_temp_variable = { tgt_AI_threatened = 1 } }

for_each_scope_loop = {
    array = controlled_states
    if = {
        limit = {
            check_variable = { tgt_avail_civs > 15 }
            check_variable = { tgt_num_mils < 10 }
            check_variable = { tgt_has_war = 0 }
            check_variable = { tgt_AI_threatened = 1 }
        }
        # ... score logic ...
    }
}
```

**Why:** `CONTROLLER = { ... }` is a scope switch, evaluated by iterating objects. Doing it once per target country instead of once per state eliminates hundreds of evaluations per pulse.

## Use Temp-Variable Booleans in Hot Loops

Repeated trigger checks (`has_war = yes`, `has_country_flag = X`, `has_idea = Y`) inside loops are expensive. Cache them as 0/1 temp variables.

```
set_temp_variable = { tgt_has_maritime_industry = 0 }
if = { limit = { has_idea = maritime_industry } set_temp_variable = { tgt_has_maritime_industry = 1 } }

# Inside loop:
if = { limit = { check_variable = { tgt_has_maritime_industry = 1 } } ... }
```

**Why:** `check_variable` is a raw numeric comparison. `has_idea` triggers a lookup through the country's idea list. The difference is measurable in tight loops.

## GUI `dirty` Counters Over Date Variables

Never bind a scripted GUI's `dirty` variable to `global.date` or `global.num_days`.

### Wrong

```
dirty = global.date
```

### Right

```
refresh_my_gui = {
    if = { limit = { check_variable = { global.refresh_my_gui = 500000 } }
        set_variable = { global.refresh_my_gui = 1 }
    }
    else = { add_to_variable = { global.refresh_my_gui = 1 } }
}
```

Bind `dirty = global.refresh_my_gui`. Call `refresh_my_gui = yes` only when the backing data actually changes (a record added, removed, edited; a relevant button clicked). The counter is a monotonically-increasing token — the engine redraws whenever it changes.

**Why:** `global.date` changes every tick, so the GUI redraws every frame, causing lag on slower machines.

### Also applies to incrementing globals

`global.num_days`, `global.date`, and any variable that changes on a fixed timer (daily, hourly, etc.) are just as bad. Same fix: a dedicated counter incremented only when the backing data changes.

## `while_loop_effect` — Limit Semantics and the 1000-Iteration Cap

`while_loop_effect` re-evaluates its `limit` block before each iteration (not mid-execution). The body runs only if the limit passes; the loop exits as soon as the limit fails or after **1000 iterations** — the engine's hard cap, not configurable.

`max_iterations` is **not** a valid HOI4 scripting key. Don't add it; the engine ignores it silently.

### Correct pattern

```
while_loop_effect = {
    limit = { check_variable = { counter < target } }
    # body must advance the condition on every pass or the loop exits at 1000
}
```

**Why this matters:** If the body never advances the condition the engine silently stops at 1000 rather than hanging. Design loops so the realistic worst case stays well below 1000; if logic could ever need more, restructure (e.g. `for_loop_effect` with a known bound).

## Prefer Engine Arrays Over `every_country` / `any_country`

### Wrong

```
every_country = {
    limit = { is_neighbor_of = ROOT }
    # ...
}
```

### Right

```
for_each_scope_loop = {
    array = neighbors
    # ...
}
```

**Why:** `every_country` iterates all 200+ tags. `neighbors` is an engine-maintained array of only bordering countries. Same applies to `subjects`, `faction_members`, `allies`, etc.

See `.claude/docs/hoi4-data-structures.md` for the full list of engine arrays.

## Avoid Complex Triggers in Decision `visible` Blocks

Decision `visible` is evaluated **every frame** while the decision tab is open.

### Wrong

```
visible = {
    any_country = {
        is_neighbor_of = ROOT
        has_war = no
        # ... 10 more conditions ...
    }
}
```

### Right

```
visible = { has_country_flag = TAG_my_decision_visible }

# Set/clear the flag in a daily on_action or the event that creates/removes the precondition:
set_country_flag = TAG_my_decision_visible   # when precondition is met
clr_country_flag = TAG_my_decision_visible   # when it ceases to be met
```

**Why:** A flag check is O(1). An `any_country` loop is O(N) per frame, N = every country. Push the cost to the moment the precondition changes, not to every frame.

**Note:** This applies to decision `visible` blocks (per-frame). For character `visible` blocks (evaluated only during AI assignment pulses and UI opens), `has_completed_focus` is equivalent to `has_country_flag` — both are hash-table lookups. Do **not** add country flags solely to replace `has_completed_focus` in character `visible` blocks; the extra flag persists in saves and bloats them for no benefit.

## Clamp Before Division

Always clamp denominators to a safe minimum before dividing.

```
set_temp_variable = { construction_speed = 1 }
# ... modifiers ...
clamp_temp_variable = { var = construction_speed min = 0.01 }
divide_temp_variable = { building_cost = construction_speed }
```

**Why:** If `construction_speed` reaches 0 (e.g., stacked negative modifiers), division produces infinity/undefined behavior. A clamp guarantees a sane fallback.

## Early-Out Guards Before Heavy Loops

Add cheap pre-checks before expensive loops to skip work when preconditions aren't met.

```
# Cheap guards — any one failing skips the entire loop below
check_variable = { treasury > 5 }
check_variable = { active_records < 15 }
check_variable = { my_ratio < 2.50 }

# Heavy loop only runs if guards pass
for_each_scope_loop = {
    array = my_candidate_array
    # ... expensive scoring ...
}
```

**Why:** Skipping an entire `every_country` / `for_each_scope_loop` pulse saves more CPU than any micro-optimization inside the loop.

## Prefer `random` Over Two-Bucket `random_list`

`random_list = { N = { effect } M = {} }` (or empty-first variant) is a weighted-dispatch list with one real outcome — overkill for a Bernoulli trial. Use `random = { chance = N effect }`: same probability, one less dispatch layer, fewer lines.

```
# Heavier — weighted list with placeholder bucket
random_list = {
    50 = { add_to_variable = { my_counter = 1 } }
    50 = {}
}

# Lighter — direct probability trial
random = {
    chance = 50
    add_to_variable = { my_counter = 1 }
}
```

**Why:** `random_list` constructs and resolves a weighted list every call; `random = { chance = N }` is a single roll. For hot paths (on_weekly counters, AI scoring, GUI dirty triggers) savings compound. See `.claude/docs/simplification-patterns.md` for the full pattern and edge cases.

## Avoid `effect_tooltip` + `for_each_scope_loop` Duplication

Never duplicate the same logic in an `effect_tooltip` block and a `for_each_scope_loop` block. Use the loop's built-in `tooltip` parameter instead.

**Why:** HOI4 evaluates both `effect_tooltip` (display) and `for_each_scope_loop` (execution). For a faction/EU/alliance array of N members, the duplication doubles the per-trigger cost — each scope switch and modifier evaluation runs twice. With many such calls per focus branch, the wasted work compounds. `tooltip =` on the loop displays the tooltip and executes the body in one pass — a measurable win on any frequently-fired path.

For the before/after migration, see `.claude/docs/simplification-patterns.md`.
