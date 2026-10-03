# Dynamic Modifier Tooltips

When a focus, decision, or event touches a dynamic modifier, a `custom_effect_tooltip`
tells the player. Both keys are in `localisation/english/MD_dm_modifiers_l_english.yml`.

| Key                            | Renders                         | Use when                               |
| ------------------------------ | ------------------------------- | -------------------------------------- |
| `adds_dynamic_modifier_tt`     | "Adds [Modifier] which grants:" | The block calls `add_dynamic_modifier` |
| `modifies_dynamic_modifier_tt` | "Modifies [Modifier] by:"       | The block only changes its variables   |

```
# Adding the modifier
add_dynamic_modifier = { modifier = TAG_modifier_name }
custom_effect_tooltip = { localization_key = adds_dynamic_modifier_tt MODIFIER = TAG_modifier_name }

# Changing variables on an existing modifier
custom_effect_tooltip = { localization_key = modifies_dynamic_modifier_tt MODIFIER = TAG_modifier_name }
```

Each `add_to_variable` on a backing variable takes a `tooltip` with the matching `_tt`
key from the same file:

```
add_to_variable = { SOV_putin_politic_political_power_factor = 0.05 tooltip = political_power_factor_tt }
```

- When several mutually exclusive focuses each start the same modifier, all of them use
  `adds_dynamic_modifier_tt`.
- In review, flag a mismatched key and an `add_dynamic_modifier` with no
  `adds_dynamic_modifier_tt`.
