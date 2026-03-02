Audit and fix dynamic modifier tooltip usage in focus trees, decisions, and events.

Requested arguments: $ARGUMENTS

## Context

Dynamic modifiers in HOI4 are variable-driven national modifiers defined in `common/dynamic_modifiers/`. When a focus, decision, or event interacts with a dynamic modifier, a `custom_effect_tooltip` is used to show the player what is happening. There are two tooltip keys:

- `adds_dynamic_modifier_tt` — renders as **"Adds [Modifier] which grants:"**. Used when the modifier is being **added for the first time** (the same block contains `add_dynamic_modifier`).
- `modifies_dynamic_modifier_tt` — renders as **"Modifies [Modifier] by:"**. Used when the modifier **already exists** and variables controlling it are being changed.

Both are defined in `localisation/english/MD_dm_modifiers_l_english.yml`.

### Tooltip Syntax

```
# When ADDING a dynamic modifier for the first time:
add_dynamic_modifier = { modifier = TAG_modifier_name }
custom_effect_tooltip = { localization_key = adds_dynamic_modifier_tt MODIFIER = TAG_modifier_name }

# When MODIFYING variables on an already-existing dynamic modifier:
custom_effect_tooltip = { localization_key = modifies_dynamic_modifier_tt MODIFIER = TAG_modifier_name }
```

### Variable Tooltips

Each `add_to_variable` that changes a dynamic modifier's backing variable should include a `tooltip` pointing to the matching `_tt` key from `MD_dm_modifiers_l_english.yml`:

```
add_to_variable = { SOV_putin_politic_political_power_factor = 0.05 tooltip = political_power_factor_tt }
add_to_variable = { SOV_putin_politic_communism_drift = 0.05 tooltip = communism_drift_tt }
```

The full list of available tooltip keys is in `localisation/english/MD_dm_modifiers_l_english.yml`, organized by category (Political, Economy, Army, Navy, Air, MD Specific).

## How To Determine Which Tooltip To Use

1. **`adds_dynamic_modifier_tt`** — The focus/decision/event block contains `add_dynamic_modifier = { modifier = ... }`, meaning the modifier is being created on the country for the first time.
   - If multiple focuses are **mutually exclusive entry points** for the same modifier (e.g. three different leaders who each start a path), ALL of them should use `adds_dynamic_modifier_tt` since each is the first-add in its respective branch.

2. **`modifies_dynamic_modifier_tt`** — The focus/decision/event block only changes variables (via `add_to_variable` or `set_variable`) that feed into an already-existing dynamic modifier. No `add_dynamic_modifier` call is present.

## Steps

1. Determine scope from arguments:
   - If a specific file is given, audit only that file
   - If a country tag is given, find the relevant focus tree and decision files
   - If no argument, audit all files changed in the current branch (`git diff main`)

2. For each file in scope, find all `custom_effect_tooltip` lines referencing either `adds_dynamic_modifier_tt` or `modifies_dynamic_modifier_tt`.

3. For each tooltip found, check the surrounding focus/decision/event block:
   - If the block contains `add_dynamic_modifier` for that modifier → should use `adds_dynamic_modifier_tt`
   - If the block only modifies variables (no `add_dynamic_modifier`) → should use `modifies_dynamic_modifier_tt`

4. Report mismatches in a table:
   | File | Focus/Decision ID | Modifier | Current | Should Be |
   |------|-------------------|----------|---------|-----------|

5. After reporting, fix all mismatches by editing the files.

6. Also check for missing tooltips: focuses/decisions that call `add_dynamic_modifier` but have no corresponding `adds_dynamic_modifier_tt` tooltip at all.
