# File Encoding

- All `.txt` files (focus trees, events, decisions, ideas, etc.) must be saved as **UTF-8 without BOM**.
- Only `.yml` localisation files use UTF-8 **with** BOM.
- When creating or editing `.txt` files, never add a BOM byte sequence (`EF BB BF`).

# HOI4 Scripting — Quick Reference

For the full reference (variables, arrays, loops, collections, formatted loc), read `.claude/docs/hoi4-data-structures.md`.

## Scope Keywords

| Keyword      | Meaning                                                                              |
| ------------ | ------------------------------------------------------------------------------------ |
| `THIS`       | Current scope (usually implicit)                                                     |
| `ROOT`       | Original scope at block start (event, focus, decision)                               |
| `PREV`       | Previous scope before last scope change (`PREV.PREV` chains)                         |
| `FROM`       | Sender scope (in events: `FROM` = event sender)                                      |
| `OWNER`      | Owner of current state scope                                                         |
| `CONTROLLER` | Controller of current state scope — **state scope only**; undefined in country scope |
| `CAPITAL`    | Capital state of current country scope                                               |

## Variables (basics)

- **Persistent:** `set_variable = { var = X value = Y }` — stored on scope, survives saves
- **Temporary:** `set_temp_variable = { var = X value = Y }` — current block only
- **Global:** `set_global_variable = { var = X value = Y }` — read via `global.X`
- **Arrays:** `my_array^0` (literal index), `my_array^i` (dynamic index)
- **Scoping:** `var:my_var = { ... }` or `var:my_array^i = { ... }` — never `var:v^i`
- **Naming:** Always prefix country-specific variables with the country tag (e.g., `ISR_operation_success`, not `oper_succ_var`). Unprefixed variable names risk collision if another country's script sets the same name on a shared scope.

## tag vs original_tag

- `tag` = the country's current runtime tag (changes for civil war split-offs like `NIG_CW_0`)
- `original_tag` = the base tag that never changes (`NIG`)
- Always use `original_tag` in idea `allowed` blocks, MIO `allowed` blocks, and anywhere you are restricting a game object to a specific nation. Using `tag` breaks those objects for civil war countries.
- The only place `tag` is correct is when you explicitly want to target the _current_ tag (e.g., `trigger = { tag = ISR }` to check if the current scope IS ISR — not a civil war copy).

# Documentation References

For more comprehensive HOI4 scripting docs (effects, triggers, modifiers, wiki links), read `.claude/docs/documentation-references.md`.

# Scripting Patterns

## NOT block scope

`NOT = { condition_A condition_B }` means NOT(A **AND** B) — "not both true at once". This is almost never intended. Write two separate blocks when you mean "neither can be true":

```
# Wrong — only blocks when both are true simultaneously
NOT = { has_idea = foo has_idea = bar }

# Correct — blocks each independently
NOT = { has_idea = foo }
NOT = { has_idea = bar }
```

## threat scale

`threat` is a decimal 0.0–1.0, never a percentage. Comparisons like `threat > 10` or `threat > 40` are always false. Use `threat > 0.10`, `threat > 0.40`, etc.

## if/else over if/if

When two consecutive `if` blocks cover complementary conditions, always use `if/else`:

```
# Wrong — double-execution risk if conditions overlap; signals missing else-awareness
if = { limit = { check_variable = { X > 7 } } ... }
if = { limit = { check_variable = { X < 7 } } ... }

# Correct
if = { limit = { check_variable = { X > 7 } } ... }
else = { ... }
```

# Event Patterns

## Cross-country event tooltips

When a focus `completion_reward` or event option fires an event to another country, add `TT_IF` tooltips immediately after the event fire to show the player both outcomes:

```
OTHER = { country_event = { id = foo.1 days = 1 } }
custom_effect_tooltip = TT_IF_THEY_REJECT
effect_tooltip = {
	# effects / tooltip keys summarising the rejection outcome
}
custom_effect_tooltip = TT_IF_THEY_ACCEPT
effect_tooltip = {
	# effects / tooltip keys summarising the acceptance outcome
}
```

Keys are in `localisation/english/MD_tooltips_l_english.yml`:

- `TT_IF_THEY_ACCEPT` / `TT_IF_THEY_REJECT` — used when describing outcomes of YOUR action firing to THEM
- `TT_IF_WE_ACCEPT` / `TT_IF_WE_DECLINE` — used inside the target's event option

## Event namespace mismatch

Event IDs used in `country_event = { id = foo.1 }` must match the namespace declared at the top of the events file (`add_namespace = foo`). If the file uses `add_namespace = bar`, the correct ID is `bar.1` — a namespace mismatch silently fires nothing.

Check: grep `add_namespace` at the top of the events file, then verify every caller uses that exact prefix.

## Log message option IDs

Log messages inside event options must match the option's own ID exactly:

```
option = {
	name = foo.1.b
	log = "[GetDateText]: [This.GetName]: foo.1.b executed"  # .b, not .a
```

Copy-pasting from option A and forgetting to update to `.b` is a common source of misleading logs.

# AI System Rules

## Unit name case sensitivity

Unit type names in OOB files (`history/units/`), AI templates (`common/ai_templates/`), and scripted division templates (`common/scripted_effects/00_AI_templates.txt`) are **case-sensitive**. A typo like `Armor_Bat` (capital A) instead of `armor_Bat` silently fails — the battalion slot is left empty. The `validate_oob_units` pre-commit hook catches these.

Common case-sensitivity traps:

| Wrong              | Correct            |
| ------------------ | ------------------ |
| `Armor_Bat`        | `armor_Bat`        |
| `armor_Recce_comp` | `armor_Recce_Comp` |
| `SP_AA_battery`    | `SP_AA_Battery`    |

## AI strategy role names

`role_ratio id = X` and `build_army id = X` in strategy files must match a `role = X` declared in `common/ai_templates/*.txt`. Orphaned references are silently ignored — the AI wastes production weight on a void. The `validate_ai_roles` pre-commit hook catches these.

Common role name traps:

| Wrong        | Correct                              |
| ------------ | ------------------------------------ |
| `mechanized` | `apc_mechanized` or `ifv_mechanized` |
| `armored`    | `armor`                              |

## AI equipment roles

When a nation is added to a `blocked_for` list in `common/ai_equipment/generic_tank.txt` (or generic_plane/generic_naval), it MUST have coverage for all required equipment roles in a custom or shared file. Missing coverage means the AI cannot produce that equipment type at all.

CAS aircraft designs must use `roles = { medium_cas_fighter }`, not `medium_as_fighter`. Using the wrong role causes the AI to deploy CAS planes as air superiority fighters.
