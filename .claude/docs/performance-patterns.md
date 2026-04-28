# Performance Patterns for HOI4 Scripted Effects

Patterns for reducing CPU overhead in HOI4's script engine, especially in daily-pulse code (on_actions, AI events, decision `visible` blocks).

---

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

**Why:** `CONTROLLER = { ... }` is a scope switch. HOI4's script engine evaluates scope switches by iterating objects. Doing this once per target country instead of once per state eliminates hundreds of evaluations per pulse.

---

## Use Temp-Variable Booleans in Hot Loops

Repeated trigger checks like `has_war = yes`, `has_country_flag = X`, `has_idea = Y` inside loops are expensive. Cache them as 0/1 temp variables.

```
set_temp_variable = { tgt_has_maritime_industry = 0 }
if = { limit = { has_idea = maritime_industry } set_temp_variable = { tgt_has_maritime_industry = 1 } }

# Inside loop:
if = { limit = { check_variable = { tgt_has_maritime_industry = 1 } } ... }
```

**Why:** `check_variable` is a raw numeric comparison. `has_idea` triggers a lookup through the country's idea list. The difference is measurable in tight loops.

---

## GUI `dirty` Counters Over Date Variables

Never bind a scripted GUI's `dirty` variable to `global.date` or `global.num_days`.

### Wrong

```
dirty = global.date
```

### Right

```
refresh_investment_gui = {
    if = { limit = { check_variable = { global.refresh_investment_gui = 500000 } }
        set_variable = { global.refresh_investment_gui = 1 }
    }
    else = { add_to_variable = { global.refresh_investment_gui = 1 } }
}
```

Bind `dirty = global.refresh_investment_gui`. Call `refresh_investment_gui = yes` only when investment state actually changes (project started, completed, cancelled, GUI button clicked).

**Why:** `global.date` changes every tick. The GUI would redraw every frame, causing noticeable lag on slower machines.

### Also applies to incrementing globals

`global.num_days`, `global.date`, and any other variable that changes on a fixed timer (daily, hourly, etc.) are just as bad. The same fix applies: create a dedicated counter and increment it only when the data that backs the GUI actually changes.

---

## Always Add `max_iterations` to `while_loop_effect`

Unbounded loops are a crash risk. If the body fails to advance the loop condition, the engine hangs inside a single tick.

### Wrong

```
while_loop_effect = {
    limit = { check_variable = { counter < target } }
    # ... body ...
}
```

### Right

```
while_loop_effect = {
    max_iterations = 500
    limit = { check_variable = { counter < target } }
    # ... body ...
}
```

**Why:** A missing guard means an edge-case bug becomes a hard freeze. Pick a ceiling well above the realistic worst case but low enough that a runaway loop exits before the player notices lag. A good rule of thumb is 10× the expected iteration count.

---

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

---

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
visible = { has_country_flag = has_valid_investment_target }

# Set/clear the flag in a daily on_action or event:
set_country_flag = has_valid_investment_target   # when target found
clr_country_flag = has_valid_investment_target   # when no targets
```

**Why:** A simple flag check is O(1). An `any_country` loop is O(N) per frame.

---

## Clamp Before Division

Always clamp denominators to a safe minimum before dividing.

```
set_temp_variable = { construction_speed = 1 }
# ... modifiers ...
clamp_temp_variable = { var = construction_speed min = 0.01 }
divide_temp_variable = { building_cost = construction_speed }
```

**Why:** If `construction_speed` reaches 0 (e.g., stacked negative modifiers), division produces infinity/undefined behavior in HOI4's engine. A clamp guarantees a sane fallback.

---

## Early-Out Guards Before Heavy Loops

Add cheap pre-checks before expensive loops to skip work when preconditions aren't met.

```
# Cheap guard: broke AI can't fund anything
check_variable = { treasury > 5 }
check_variable = { active_projects < 15 }
check_variable = { debt_ratio < 2.50 }

# Heavy loop only runs if guards pass
for_each_scope_loop = {
    array = investment_targets
    # ... expensive scoring ...
}
```

**Why:** Skipping an entire `every_country` / `for_each_scope_loop` pulse saves more CPU than any micro-optimization inside the loop.

---

## Avoid `effect_tooltip` + `for_each_scope_loop` Duplication

Never duplicate the same logic in an `effect_tooltip` block and a `for_each_scope_loop` block. Use the loop's built-in `tooltip` parameter instead.

**Why:** HOI4 evaluates both `effect_tooltip` (for tooltip display) and `for_each_scope_loop` (for effect execution). With ~27 EU members, each duplication costs ~27 extra scope switches and ~54 extra opinion modifier evaluations per trigger. In focus trees with 50+ such calls, that's thousands of wasted evaluations per campaign. `tooltip =` tells the engine to display the tooltip once and execute the loop once — a measurable performance win on any frequently-fired code path.

For the before/after migration pattern, see `.claude/docs/simplification-patterns.md`.
