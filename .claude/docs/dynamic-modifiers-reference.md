# Dynamic Modifiers Reference

Dynamic modifiers are variable-driven national modifiers defined in `common/dynamic_modifiers/`. When a focus, decision, or event interacts with a dynamic modifier, a `custom_effect_tooltip` shows the player what is happening. There are two tooltip keys:

- `adds_dynamic_modifier_tt` — renders as **"Adds [Modifier] which grants:"**. Used when the modifier is being **added for the first time** (the same block contains `add_dynamic_modifier`).
- `modifies_dynamic_modifier_tt` — renders as **"Modifies [Modifier] by:"**. Used when the modifier **already exists** and variables controlling it are being changed.

Both are defined in `localisation/english/MD_dm_modifiers_l_english.yml`.

## Tooltip Syntax

```
# When ADDING a dynamic modifier for the first time:
add_dynamic_modifier = { modifier = TAG_modifier_name }
custom_effect_tooltip = { localization_key = adds_dynamic_modifier_tt MODIFIER = TAG_modifier_name }

# When MODIFYING variables on an already-existing dynamic modifier:
custom_effect_tooltip = { localization_key = modifies_dynamic_modifier_tt MODIFIER = TAG_modifier_name }
```

## Variable Tooltips

Each `add_to_variable` that changes a dynamic modifier's backing variable should include a `tooltip` pointing to the matching `_tt` key from `MD_dm_modifiers_l_english.yml`:

```
add_to_variable = { SOV_putin_politic_political_power_factor = 0.05 tooltip = political_power_factor_tt }
add_to_variable = { SOV_putin_politic_communism_drift = 0.05 tooltip = communism_drift_tt }
```

## Choosing the Right Tooltip

1. **`adds_dynamic_modifier_tt`** — the block contains `add_dynamic_modifier = { modifier = ... }`, meaning the modifier is being created on the country for the first time.
   - If multiple focuses are mutually exclusive entry points for the same modifier (e.g. three leader paths each starting the same modifier), ALL should use `adds_dynamic_modifier_tt` since each is a first-add in its own branch.

2. **`modifies_dynamic_modifier_tt`** — the block only changes variables (via `add_to_variable` or `set_variable`) that feed into an already-existing modifier. No `add_dynamic_modifier` call is present.

## Checking for Errors

When reviewing files that use dynamic modifiers:

1. Find all `custom_effect_tooltip` lines referencing `adds_dynamic_modifier_tt` or `modifies_dynamic_modifier_tt`.
2. For each: check whether the surrounding block contains `add_dynamic_modifier` for that modifier.
   - Contains `add_dynamic_modifier` → must use `adds_dynamic_modifier_tt`
   - Only changes variables → must use `modifies_dynamic_modifier_tt`
3. Also flag focuses/decisions that call `add_dynamic_modifier` with no corresponding `adds_dynamic_modifier_tt` tooltip.
