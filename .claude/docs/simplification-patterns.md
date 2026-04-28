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

## Consolidate Identical-Body `else_if` Chains into `OR`

When N consecutive `else_if` branches all execute the same effects, collapse them into one branch with an `OR` limit.

### Before (N branches, same body)

```
else_if = {
    limit = { has_country_flag = flag_A }
    add_stability = 0.05
}
else_if = {
    limit = { has_country_flag = flag_B }
    add_stability = 0.05
}
else_if = {
    limit = { has_country_flag = flag_C }
    add_stability = 0.05
}
else_if = {
    limit = { has_country_flag = flag_D }
    add_stability = 0.05
}
else_if = {
    limit = { has_country_flag = flag_E }
    add_stability = 0.05
}
```

### After (one branch, OR'd conditions)

```
else_if = {
    limit = {
        OR = {
            has_country_flag = flag_A
            has_country_flag = flag_B
            has_country_flag = flag_C
            has_country_flag = flag_D
            has_country_flag = flag_E
        }
    }
    add_stability = 0.05
}
```

**Go a step further — use `else` when exhaustive:** If the preceding `if/else_if` chain already guarantees at least one condition must be true (e.g., the earlier branches covered all lower values of a sequential range), use a bare `else = { ... }` instead of the `OR` block — it's shorter and can't drift.

**Why:** Eliminates copy-paste drift — adding a new condition doesn't risk forgetting to update one branch. Reduces script size. If the body needs changing, it's one edit instead of N.

**When NOT to use:** If the branches have side effects that interact (e.g., scoping to different targets, setting variables the next branch reads), or if evaluation order matters between conditions that could both be true. `OR` short-circuits logic — all conditions are effectively equal.

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

---

## Consolidate `custom_effect_tooltip` + `effect_tooltip` + `for_each_scope_loop`

When a focus, decision, or event shows a tooltip for effects applied to every member of an array, the old pattern duplicated the same logic twice — once in `effect_tooltip` (for display) and once in `for_each_scope_loop` (for execution). The `for_each_scope_loop` block accepts a `tooltip` parameter, which combines both.

### Before (self-targeting effects)

```
custom_effect_tooltip = TT_ALL_NATO_MEMBER_NATIONS_GAIN
effect_tooltip = {
    add_popularity = { ideology = nationalist popularity = 0.05 }
    add_war_support = -0.10
    add_stability = -0.05
}
for_each_scope_loop = {
    array = global.nato_members
    add_popularity = { ideology = nationalist popularity = 0.05 }
    add_war_support = -0.10
    add_stability = -0.05
}
```

### After (self-targeting effects)

```
for_each_scope_loop = {
    array = global.nato_members
    tooltip = TT_ALL_NATO_MEMBER_NATIONS_GAIN
    add_popularity = { ideology = nationalist popularity = 0.05 }
    add_war_support = -0.10
    add_stability = -0.05
}
```

### Before (opinion modifiers with explicit target)

```
custom_effect_tooltip = TT_ALL_NATO_MEMBER_NATIONS_GAIN
effect_tooltip = {
    add_opinion_modifier = { target = DEN modifier = drama }
}
for_each_scope_loop = {
    array = global.nato_members
    add_opinion_modifier = { target = DEN modifier = drama }
}
```

### After (opinion modifiers with explicit target)

```
for_each_scope_loop = {
    array = global.nato_members
    tooltip = TT_ALL_NATO_MEMBER_NATIONS_GAIN
    if = {
        limit = { NOT = { tag = ROOT } }
        add_opinion_modifier = { target = ROOT modifier = drama }
    }
}
```

**Key differences:**

- `tooltip = TT_ALL_*` replaces both `custom_effect_tooltip` and `effect_tooltip`.
- The effects live in one place: inside the `for_each_scope_loop`.
- When opinion modifiers target the focus-completing country, add `NOT = { tag = ROOT }` to prevent self-targeting. Use `ROOT` (not `PREV`) — `ROOT` is the fixed original scope, while `PREV` shifts if the loop is nested inside another scope change.

**Why:** Eliminates ~4–8 lines of duplication per call site. Across ~50+ EU/NATO/CSTO/AU focus trees, scripted effects, and GUI buttons, this removes hundreds of redundant lines and prevents drift between tooltip text and real execution. See `.claude/docs/performance-patterns.md` for the performance impact of double-evaluation.

---

## Merge Consecutive Same-Tag Scope Blocks

When two or more scope blocks target the same country tag in sequence, merge them into one. Each scope switch adds a nesting level to the in-game tooltip, making it harder to read.

### Before

```
ALG = {
    country_event = nuclear_algeria.19
}
ALG = {
    add_opinion_modifier = {
        target = ROOT
        modifier = sanctioned_us
    }
}
```

### After

```
ALG = {
    country_event = nuclear_algeria.19
    add_opinion_modifier = {
        target = ROOT
        modifier = sanctioned_us
    }
}
```

**Why:** Each `TAG = { }` scope switch creates a separate indented block in the player-facing tooltip. Two consecutive `ALG = { }` blocks show the ALG header twice, making the tooltip noisy and harder to scan. Merging produces a single clean block.

**When NOT to merge:** If the two blocks are separated by an `if`/`else` that conditionally gates one of them, or if the second block is inside a different trigger/effect context (e.g., one is in `effect_tooltip` and the other is in `hidden_effect`), they cannot be merged.

---

## Prefer `multiply_variable` Over `divide_variable`

Division is more expensive than multiplication and carries a divide-by-zero risk. When dividing by a constant, multiply by its reciprocal instead.

### Before

```
divide_variable = { var = my_ratio value = 100 }
```

### After

```
multiply_variable = { var = my_ratio value = 0.01 }
```

**Why:** `multiply_variable` is a single engine operation with no zero-division risk. `0.01` is the exact reciprocal of `100`, so the result is identical. Prefer multiplication for all constant divisors.

---

## Add Mutual Exclusion Guards When Splitting `every_country` with `OR`

When converting a single `every_country = { limit = { OR = { A B } } }` into separate loops (e.g., one per array), add exclusion limits so countries matching multiple conditions don't receive effects twice.

### Before (single loop)

```
every_country = {
    limit = { OR = { has_idea = group_A has_idea = group_B } }
    country_event = { id = my_event.1 days = 2 }
}
```

### After (split loops with exclusion)

```
for_each_scope_loop = {
    array = global.group_A_members
    limit = { NOT = { has_idea = group_B } }
    country_event = { id = my_event.1 days = 2 }
}
every_country = {
    limit = { has_idea = group_B }
    country_event = { id = my_event.1 days = 2 }
}
```

**Why:** The original single loop guaranteed each country received the effect exactly once. Splitting without guards causes countries in both groups to fire or receive the effect multiple times. This silently introduces double-firing events, stacked opinion modifiers, or duplicated resource transfers.

Apply the same pattern whenever a non-idempotent effect (opinion modifiers, variable changes, events, etc.) is split across multiple loops.
