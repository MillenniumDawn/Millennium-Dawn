---
name: additional-income
description: 'Wire a country-specific income or expense stream into the MD money system: calculation block, hidden tooltip idea, loc key, and granting effect. Use when asked to add an income or expense stream, e.g. "/additional-income GRE golden_visa income".'
---

Arguments: $ARGUMENTS, as `TAG stream_name [income|expense]`. Ask for anything missing.
Also ask what activates the stream (focus, idea, flag), whether it is GDP-scaled or
flat, its display name, and which focus, decision, or event grants it.

A stream needs four pieces. The variable name must match across all of them. For
working examples, grep `calculate_additional_income_rate` in `common/scripted_effects/`.

## 1. Calculation

In `common/scripted_effects/00_money_system.txt`, inside
`calculate_additional_income_rate` or `calculate_additional_expense_rate`:

```
if = {
    limit = { original_tag = TAG }
    if = {
        limit = { has_completed_focus = TAG_focus_name }
        set_variable = { TAG_stream_name_income = gdp_total }
        multiply_variable = { TAG_stream_name_income = 0.003 }
        add_to_variable = { additional_income_rate = TAG_stream_name_income }
    }
}
```

- Income adds to `additional_income_rate`. Expense uses a `_expense` variable and adds
  to `additional_expenses_rate`.
- Each country has one `original_tag` wrapper per effect. If one exists, nest the new
  inner `if` in it. Never add a second wrapper.
- The value is GDP-scaled as above, or flat: `set_variable = { TAG_x_income = 0.500 }`.

## 2. Hidden idea

In the country's idea file, in its `hidden_ideas` block (add the block if missing):

```
hidden_ideas = {
    TAG_stream_name_money = {
        allowed_civil_war = { always = yes }
        modifier = {
            custom_modifier_tooltip = additional_income_TAG_stream_name_TT
        }
    }
}
```

Use `additional_expense_TAG_stream_name_TT` for an expense. Do not add
`allowed = { always = no }` or an empty `on_add`.

## 3. Localisation

In `localisation/english/MD_money_l_english.yml`, beside the existing entries:

```
 additional_income_TAG_stream_name_TT: "$$[?TAG_stream_name_income|+3] from §YDisplay Name§!\n"
 additional_expense_TAG_stream_name_TT: "$$[?TAG_stream_name_expense|-3] from §YDisplay Name§!\n"
```

`|+3` formats income and `|-3` formats an expense. Keep the trailing `\n`.

## 4. Grant the idea

In the effect that unlocks the stream:

```
add_ideas = TAG_stream_name_money
```

Add `remove_ideas = TAG_stream_name_money` wherever the stream should stop.

## Report

Summarize what was added. Remind the user to check in game that the tooltip appears and
the value updates.
