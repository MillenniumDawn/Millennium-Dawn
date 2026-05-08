---
title: Dynamic Modifiers
description: How to use dynamic modifiers and their tooltips correctly in Millennium Dawn
---

Dynamic modifiers are variable-driven national modifiers defined in `common/dynamic_modifiers/`. Unlike static ideas, their values change at runtime based on scripted variables — so a single modifier can produce different in-game effects depending on what a country has researched, built, or chosen.

---

## How Dynamic Modifiers Work

A dynamic modifier is declared in `common/dynamic_modifiers/` with variables as its values:

```
TAG_economy_modifier = {
    political_power_factor = var:TAG_economy_pp_bonus
    stability_factor = var:TAG_economy_stability_bonus
}
```

The modifier is then added to a country via `add_dynamic_modifier`, and its backing variables are changed throughout the game via `add_to_variable` or `set_variable` in focuses, decisions, and events.

---

## Tooltip Keys

When a focus, decision, or event interacts with a dynamic modifier, a `custom_effect_tooltip` tells the player what is happening. There are two distinct keys:

| Key                            | Renders as                      | When to use                                                                                        |
| ------------------------------ | ------------------------------- | -------------------------------------------------------------------------------------------------- |
| `adds_dynamic_modifier_tt`     | "Adds [Modifier] which grants:" | The block **also contains** `add_dynamic_modifier` — this is the first application of the modifier |
| `modifies_dynamic_modifier_tt` | "Modifies [Modifier] by:"       | The block only changes variables — the modifier already exists on the country                      |

Both keys are defined in `localisation/english/MD_dm_modifiers_l_english.yml`.

---

## Syntax Examples

### Adding a modifier for the first time

```
add_dynamic_modifier = { modifier = TAG_economy_modifier }
custom_effect_tooltip = { localization_key = adds_dynamic_modifier_tt MODIFIER = TAG_economy_modifier }
```

### Modifying an already-existing modifier

```
add_to_variable = { TAG_economy_pp_bonus = 0.05 tooltip = political_power_factor_tt }
custom_effect_tooltip = { localization_key = modifies_dynamic_modifier_tt MODIFIER = TAG_economy_modifier }
```

### Variable tooltip keys

Each `add_to_variable` that changes a backing variable should include a `tooltip` attribute pointing to the matching `_tt` key in `MD_dm_modifiers_l_english.yml`. These keys are organized by category (Political, Economy, Army, Navy, Air, MD Specific):

```
add_to_variable = { SOV_putin_politic_political_power_factor = 0.05 tooltip = political_power_factor_tt }
add_to_variable = { SOV_putin_politic_communism_drift = 0.05 tooltip = communism_drift_tt }
```

---

## Mutually Exclusive Entry Points

When multiple focuses are mutually exclusive paths that each add the same modifier for the first time (e.g. three different leaders each starting a unique modifier path), **all** of them should use `adds_dynamic_modifier_tt`. Each is a first-add within its own branch, even though only one branch will ever execute.

---

## Common Mistakes

| Wrong                                                                                | Correct                                                                  |
| ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| Using `modifies_dynamic_modifier_tt` in a block that contains `add_dynamic_modifier` | Use `adds_dynamic_modifier_tt` when the modifier is being added          |
| Using `adds_dynamic_modifier_tt` in a block that only sets variables                 | Use `modifies_dynamic_modifier_tt` when the modifier already exists      |
| Calling `add_dynamic_modifier` with no tooltip at all                                | Always pair every `add_dynamic_modifier` with `adds_dynamic_modifier_tt` |
| Adding variables without per-variable `tooltip` attributes                           | Add `tooltip = <key>_tt` on each `add_to_variable` line                  |

---

## Performance Notes

Dynamic modifiers update every tick. Keep the following in mind:

- Use dynamic modifiers sparingly. A large number of dynamic modifiers on many countries is expensive.
- **Never** use `force_update_dynamic_modifier` — it forces a recalculation every frame and causes significant lag.
- Prefer a smaller number of modifiers with many variables over many separate modifiers with few variables each.

---

## Related Resources

- [Code Stylization Guide](/dev-resources/code-stylization-guide)
- [Code Resource](/dev-resources/code-resource)
