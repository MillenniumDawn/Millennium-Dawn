# Dynamic Modifier Tooltip Reference

Dynamic modifiers are variable-driven national modifiers defined in `common/dynamic_modifiers/`. Two tooltip keys control how they display to the player:

- **`adds_dynamic_modifier_tt`** — "Adds [Modifier] which grants:" — used when the block contains `add_dynamic_modifier` (first-time add). Mutually exclusive entry points that each add the same modifier ALL use this.
- **`modifies_dynamic_modifier_tt`** — "Modifies [Modifier] by:" — used when only variables are changed (no `add_dynamic_modifier`).

Both defined in `localisation/english/MD_dm_modifiers_l_english.yml`.

## Syntax

```
# Adding:
add_dynamic_modifier = { modifier = TAG_modifier_name }
custom_effect_tooltip = { localization_key = adds_dynamic_modifier_tt MODIFIER = TAG_modifier_name }

# Modifying:
custom_effect_tooltip = { localization_key = modifies_dynamic_modifier_tt MODIFIER = TAG_modifier_name }
```

Each `add_to_variable` changing a dynamic modifier variable should include a `tooltip` pointing to the `_tt` key from `MD_dm_modifiers_l_english.yml`:

```
add_to_variable = { SOV_putin_politic_political_power_factor = 0.05 tooltip = political_power_factor_tt }
```

For valid modifier names, check `resources/documentation/modifiers_documentation.md`.

## Auditing Dynamic Modifier Tooltips

When reviewing or fixing tooltip usage:

1. Find all `custom_effect_tooltip` lines referencing `adds_dynamic_modifier_tt` or `modifies_dynamic_modifier_tt`.
2. Validate: block has `add_dynamic_modifier` → should use `adds_`; no `add_dynamic_modifier` → should use `modifies_`.
3. Check for missing tooltips: `add_dynamic_modifier` without any corresponding `adds_dynamic_modifier_tt`.
