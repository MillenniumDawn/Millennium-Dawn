Add an additional income or expense stream for a country in Millennium Dawn.

Arguments: $ARGUMENTS (expected format: `TAG stream_name [income|expense]`, e.g. `GRE golden_visa income` or `IRQ war_compensation expense`)

If $ARGUMENTS is empty or incomplete, ask the user for the country TAG, a short snake_case name, and whether it is an income or expense.

## Background

The Millennium Dawn money system calculates weekly finances for every country via `common/scripted_effects/00_money_system.txt`. Country-specific additional incomes and expenses are added inside the `calculate_additional_income_rate` and `calculate_additional_expense_rate` scripted effects respectively. To make the stream visible to the player, a **hidden idea** with a `custom_modifier_tooltip` is granted by the focus/decision/event that unlocks it.

## The Three-Part Pattern

Every additional income or expense requires exactly three things:

### 1. Money System Calculation (`common/scripted_effects/00_money_system.txt`)

**For income** — add a block inside `calculate_additional_income_rate` under the country's `original_tag` section:

```
if = {
    limit = { original_tag = TAG }
    if = {
        limit = { has_completed_focus = TAG_focus_name }  # or has_idea, has_country_flag, etc.
        set_variable = { TAG_stream_name_income = gdp_total }
        multiply_variable = { TAG_stream_name_income = 0.003 }
        add_to_variable = { additional_income_rate = TAG_stream_name_income }
    }
}
```

**For expense** — add a block inside `calculate_additional_expense_rate` under the country's `original_tag` section:

```
if = {
    limit = { original_tag = TAG }
    if = {
        limit = { has_completed_focus = TAG_focus_name }
        set_variable = { TAG_stream_name_expense = gdp_total }
        multiply_variable = { TAG_stream_name_expense = 0.002 }
        add_to_variable = { additional_expenses_rate = TAG_stream_name_expense }
    }
}
```

**Multiple streams per country** — When a country has 2+ streams, they all go inside a single `original_tag` wrapper to avoid redundant tag checks every tick. Only add the outer `if = { limit = { original_tag = TAG } }` if one doesn't already exist; otherwise nest the new inner `if` block alongside the existing ones:

```
# Single wrapper for all TAG incomes
if = {
    limit = { original_tag = TAG }
    if = {
        limit = { has_completed_focus = TAG_focus_a }
        set_variable = { TAG_stream_a_income = gdp_total }
        multiply_variable = { TAG_stream_a_income = 0.003 }
        add_to_variable = { additional_income_rate = TAG_stream_a_income }
    }
    if = {
        limit = { has_idea = TAG_stream_b_idea }
        set_variable = { TAG_stream_b_income = 0.200 }
        add_to_variable = { additional_income_rate = TAG_stream_b_income }
    }
}
```

The same wrapper pattern applies to expenses inside `calculate_additional_expense_rate`.

Key rules:

- The variable name (e.g. `TAG_stream_name_income` or `TAG_stream_name_expense`) is what the tooltip will display
- Income adds to `additional_income_rate`; expense adds to `additional_expenses_rate`
- **Never create a duplicate `original_tag` wrapper** — always check if one exists and nest inside it
- The condition (`has_completed_focus`, `has_idea`, `has_country_flag`, `has_decision`) determines when the stream is active
- Value can be GDP-scaled (`gdp_total * factor`) or flat (`set_variable = { var = 0.500 }`)

### 2. Hidden Idea (`common/ideas/<Country>.txt`)

Add a hidden idea that carries the `custom_modifier_tooltip`. This makes the stream visible in the country's national spirit panel.

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

For expenses, use `additional_expense_` prefix instead:

```
hidden_ideas = {
    TAG_stream_name_money = {
        allowed_civil_war = { always = yes }
        modifier = {
            custom_modifier_tooltip = additional_expense_TAG_stream_name_TT
        }
    }
}
```

Key rules:

- Place in the `hidden_ideas` block of the country's idea file — create one if it doesn't exist
- Include `allowed_civil_war = { always = yes }`
- The `custom_modifier_tooltip` key must match the localisation key exactly
- Do NOT add `allowed = { always = no }` (anti-pattern) or empty `on_add` blocks

### 3. Localisation (`localisation/english/MD_money_l_english.yml`)

Add a tooltip key that renders the amount using the variable from step 1.

**For income** (use `|+3` for positive green formatting):

```
 additional_income_TAG_stream_name_TT: "$$[?TAG_stream_name_income|+3] from §YDisplay Name§!\n"
```

**For expense** (use `|-3` for negative red formatting):

```
 additional_expense_TAG_stream_name_TT: "$$[?TAG_stream_name_expense|-3] from §YDisplay Name§!\n"
```

Key rules:

- The variable inside `[?...|+3]` or `[?...|-3]` must exactly match the variable name from the money system
- `+3` = positive with 3 decimal places (income); `-3` = negative with 3 decimal places (expense)
- Use `§Y...§!` for yellow highlighting on the source name
- End with `\n` for proper tooltip line spacing
- Use 1 space indent (not tabs) — this is a `.yml` file

### 4. Grant the Idea

In the focus/decision/event that unlocks the stream, add `add_ideas = TAG_stream_name_money`:

```
completion_reward = {
    log = "[GetDateText]: [Root.GetName]: Focus TAG_focus_name"
    add_ideas = TAG_stream_name_money
    # ... other effects
}
```

If the stream should stop at some point, add `remove_ideas = TAG_stream_name_money` in the appropriate removal path.

## Steps

1. Parse TAG, stream name, and type (income/expense) from $ARGUMENTS. If ambiguous, ask.

2. **Money system** — Open `common/scripted_effects/00_money_system.txt`:
   - For income: find `calculate_additional_income_rate` and check if the TAG already has a section
   - For expense: find `calculate_additional_expense_rate` and check if the TAG already has a section
   - Add the calculation block. Ask the user what the condition is (focus, idea, flag) and whether it should be GDP-scaled or flat.

3. **Hidden idea** — Find the country's idea file by grepping for ideas with the TAG prefix in `common/ideas/`. Check if a `hidden_ideas` block exists; if not, add one before the final closing `}`. Add the hidden idea.

4. **Localisation** — Open `localisation/english/MD_money_l_english.yml` and add the tooltip key near existing `additional_income_` or `additional_expense_` entries. Ask the user for the display name if not obvious.

5. **Grant the idea** — Ask the user which focus/decision/event should grant the idea, then add `add_ideas = TAG_stream_name_money` to its effect block.

6. Summarize what was added and remind the user:
   - The variable name must be consistent across all three files
   - Test in-game that the tooltip appears and the value updates
   - If the stream should stop, ensure `remove_ideas` is called in the removal path

## Existing Examples

### Incomes

| Country | Stream                 | Variable                            | Condition                                     | Location                           |
| ------- | ---------------------- | ----------------------------------- | --------------------------------------------- | ---------------------------------- |
| GRE     | Golden Visa Programme  | `GRE_golden_visa_income`            | `has_completed_focus = GRE_golden_visa_deals` | `calculate_additional_income_rate` |
| ENG     | Aston Martin           | (flat)                              | `has_idea = ENG_aston_martin_money`           | `calculate_additional_income_rate` |
| ENG     | Visit Britain Tourism  | (flat)                              | `has_idea = ENG_visit_britain_idea`           | `calculate_additional_income_rate` |
| HEZ     | South American Cartels | `HEZ_south_american_cartels_income` | `has_idea = HEZ_our_cartels_in_south_america` | `calculate_additional_income_rate` |

### Expenses

| Country | Stream                   | Variable                                   | Condition                                                             | Location                            |
| ------- | ------------------------ | ------------------------------------------ | --------------------------------------------------------------------- | ----------------------------------- |
| Generic | Pro-Western Propaganda   | `promote_outlook_western_costs`            | `has_decision = promote_outlook_decision_support_pro_western_parties` | `calculate_additional_expense_rate` |
| IRQ     | War Compensation to Iran | `additional_expense_iraq_war_compensation` | (country-specific)                                                    | `calculate_additional_expense_rate` |
