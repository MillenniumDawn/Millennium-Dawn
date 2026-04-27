# Simplification Patterns for HOI4 Scripted Effects

Patterns for reducing complexity, eliminating copy-paste drift, and making scripts easier to maintain.

---

## Array Lookup Tables

When you have N parallel values indexed by a small integer type (1..N), use an array instead of N individual variables.

### Before (14 globals + 14 branches)

```
set_variable = { global.BUILD_COST_CIVILIAN_FACTORY = 12 }
set_variable = { global.BUILD_COST_MILITARY_FACTORY = 12.50 }
# ... 12 more ...

if = { limit = { check_variable = { type = 1 } }
    set_variable = { cost = global.BUILD_COST_CIVILIAN_FACTORY }
}
else_if = { limit = { check_variable = { type = 2 } }
    set_variable = { cost = global.BUILD_COST_MILITARY_FACTORY }
}
# ... 12 more ...
```

### After (one array + one lookup)

```
set_variable = { global.build_cost_array^1 = 12 }
set_variable = { global.build_cost_array^2 = 12.50 }
# ... 12 more ...

set_temp_variable = { idx = type }
set_variable = { cost = global.build_cost_array^idx }
```

**Why:** Eliminates copy-paste drift, reduces script size by ~80%, and adding a new type is one line instead of two.

**Caveat:** HOI4 arrays are zero-indexed. Reserve `^0` as a safe default (set to 0 or a sentinel) so an uninitialized index doesn't read garbage.

---

## Parameterized Scripted Localisation

Scripted localisation (`defined_text`) has no function parameters. Use a temp variable as a "parameter" to collapse N near-identical blocks.

### Before (15 blocks, one per slot)

```
defined_text = {
    name = AC_GetProjectText0
    text = { trigger = { check_variable = { project_array^0 = 1 } } localization_key = cancelled }
    text = { localization_key = AC_project_0_text }
}
defined_text = {
    name = AC_GetProjectText1
    # ... identical structure, different index ...
}
# ... 13 more ...
```

### After (one block reading a temp var)

```
# Caller sets the temp variable before using the loc key
set_temp_variable = { completed_project_building_type = project_building_type^project }

defined_text = {
    name = investments_get_completed_building_type
    text = { trigger = { check_variable = { completed_project_building_type = 1 } } localization_key = industrial_complex }
    text = { trigger = { check_variable = { completed_project_building_type = 2 } } localization_key = arms_factory }
    # ... etc ...
}
```

**Why:** Scripted loc has no arrays or parameterized blocks. A temp variable set by the caller is the only way to share logic across slots.

---

## Extract Repeated Tail Blocks into Helpers

When multiple functions end with identical logic, extract the tail into a helper.

### Before

Every `AI_get_*_score` ended with:

```
set_temp_variable_to_random = { var = state_randomizer min = -15 max = 15 integer = yes }
add_to_temp_variable = { AI_score = state_randomizer }
if = { limit = { check_variable = { AI_score > AI_best_score } }
    set_temp_variable = { AI_best_score = AI_score }
    set_temp_variable = { AI_best_target = THIS.id }
    set_temp_variable = { AI_best_type = 1 }
}
```

### After

```
AI_record_score = {
    set_temp_variable_to_random = { var = state_randomizer min = -15 max = 15 integer = yes }
    add_to_temp_variable = { AI_score = state_randomizer }
    if = { limit = { check_variable = { AI_score > AI_best_score } }
        set_temp_variable = { AI_best_score = AI_score }
        set_temp_variable = { AI_best_target = THIS.id }
        set_temp_variable = { AI_best_type = AI_score_type }
    }
}
```

Each caller now ends with:

```
set_temp_variable = { AI_score_type = 1 }  # or 2, 3, etc.
AI_record_score = yes
```

**Why:** ~40 lines of duplication removed per score function. If the randomization range needs tuning, one change updates every score type.

---

## Replace Nested `if` Toggle with `if/else`

### Before

```
if = { limit = { check_variable = { page = 1 } } add_to_variable = { page = 1 } }
else_if = { limit = { check_variable = { page = 2 } } set_variable = { page = 1 } }
```

### After

```
if = { limit = { check_variable = { page = 1 } } set_variable = { page = 2 } }
else = { set_variable = { page = 1 } }
```

**Why:** Two-state toggles are cleaner with `if/else`. The `else` branch is guaranteed to execute when the `if` doesn't, removing the need for a second trigger check.

---

## Consolidate Decision Templates with `meta_effect`

When you have N decisions that differ only by an index, use `meta_effect` rather than N copies.

```
meta_effect = {
    text = {
        activate_decision = investments_project_[INDEX]_decision
        var:project_target_country^project = {
            set_variable = { project_target_construction_duration = PREV.project_construction_duration^PREV.project }
            activate_targeted_decision = { target = PREV decision = investments_project_[INDEX]_target_decision }
        }
    }
    INDEX = "[?project]"
}
```

**Why:** 15 investor + 15 target decisions still exist as separate objects (engine requirement), but their activation logic is a single block.

**Caveat:** `meta_effect` runs at parse time, not runtime. It cannot reference runtime variables in its parameter substitution — only static text or `[]`-formatted variables.
