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

# Comments

Default to writing **no comments**. Only add one when the WHY is non-obvious:

- A hidden constraint that isn't visible from the surrounding code (e.g., "must run before X or Y fires twice")
- A subtle invariant the reader would need to know to safely edit this block
- A deliberate workaround for a specific engine bug or parser quirk
- Behaviour that would genuinely surprise a competent reader

**Never** add comments that:

- Explain WHAT the code does — well-named effects, triggers, and variables already communicate that
- Narrate the change ("Added for the X fix", "Handles case from issue #123") — those belong in the commit message, not the script
- Reference callers or downstream consumers ("used by Y", "called from Z") — these rot as the codebase evolves
- Restate the effect name in prose (`# add stability` above `add_stability = 0.05`)

When in doubt, delete the comment. If the code is unclear without it, rename or restructure the code first.

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

## Implicit AND in triggers

Multiple conditions in a trigger block are implicitly AND-ed together. Never wrap conditions in redundant `AND = { }` blocks:

```
# Wrong — redundant AND wrapper
trigger = { AND = { A B C } }

# Correct — implicit AND
trigger = { A B C }
```

This applies to `trigger`, `limit`, `visible`, `available`, `activation`, `cancel_trigger`, and all other trigger contexts.

## threat scale

`threat` is a decimal 0.0–1.0, never a percentage. Comparisons like `threat > 10` or `threat > 40` are always false. Use `threat > 0.10`, `threat > 0.40`, etc.

## check_variable comparison operators

`check_variable` only accepts `=`, `>`, and `<` as inline operators. `>=` and `<=` are **not valid syntax** — the parser silently treats them as something else and the check never matches as intended.

```
# Wrong — >= and <= are not valid inline
check_variable = { v >= 0 }

# Correct — use compare = ...
check_variable = {
	var = v
	value = 0
	compare = greater_than_or_equals
}
```

Valid `compare` values: `equals`, `greater_than`, `less_than`, `greater_than_or_equals`, `less_than_or_equals`, `not_equals`.

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

# Array Index Semantics

When a function uses `^index` array subscripts, the **meaning of the index variable** must be obvious and consistent. Common bugs arise when two different index types are stored in similarly-named variables.

| Variable name              | Should hold                  | Must NOT hold                                   |
| -------------------------- | ---------------------------- | ----------------------------------------------- |
| `project`, `slot`, `idx`   | Slot / array position (0..N) | Building type, category ID, or other lookup key |
| `type`, `kind`, `category` | Lookup key / type ID (1..N)  | Slot index                                      |

**Rule:** When a function parameter is an array index, document it in the function comment. Verify every caller passes the right kind of index. See `.claude/docs/refactor-checklist.md` for the full verification steps.

---

## Simplification Patterns

- **Consolidate identical-body `else_if` chains:** When N consecutive `else_if` branches have the same body, collapse into one `OR` limit (or plain `else` if the preceding chain guarantees one condition is true). See `.claude/docs/simplification-patterns.md`.

Replace N parallel `if/else_if` lookup chains with array indexing:

```
# Before: 14 branches
if = { limit = { check_variable = { type = 1 } } set_variable = { cost = global.BUILD_COST_CIVILIAN_FACTORY } }
else_if = { limit = { check_variable = { type = 2 } } set_variable = { cost = global.BUILD_COST_MILITARY_FACTORY } }
# ... etc ...

# After: one array + one lookup
set_temp_variable = { idx = type }
set_variable = { cost = global.build_cost_array^idx }
```

See `.claude/docs/simplification-patterns.md` for the full set of patterns.

---

## Performance Patterns

### Hoist invariant lookups out of loops

Cache country-scope values (`num_of_factories`, `has_war`, flags, ideas) before iterating states. Each `CONTROLLER = { ... }` scope switch inside a per-state loop is expensive.

### GUI `dirty` counters

Never bind `dirty = global.date`. Use a dedicated counter incremented only on relevant state changes. See `.claude/docs/performance-patterns.md`.

---

## Refactor Breaking-Change Checklist

When renaming prefixes, migrating globals to arrays, or changing function signatures:

1. Grep the **entire repo** for old names (flags, variables, events, decisions, GUI, GFX).
2. Verify array-index semantics: trace every caller to confirm the index variable holds the expected value.
3. Check localisation for `[?global.old_name]` references — these fail silently to 0.
4. Verify event `log =` strings match option `name =` keys after any copy/rename.
5. Confirm GUI `window_name`, button names, and GFX sprite names are cross-referenced.

See `.claude/docs/refactor-checklist.md` for the full checklist.

---

# Event Patterns

## Cross-country event tooltips

When a focus `completion_reward` or event option fires an event to another country, add a `TT_IF_THEY_ACCEPT` tooltip immediately after the event fire so the player can see what happens on acceptance:

```
OTHER = { country_event = { id = foo.1 days = 1 } }
custom_effect_tooltip = TT_IF_THEY_ACCEPT
effect_tooltip = {
	# effects / tooltip keys summarising the acceptance outcome
}
```

Only add `TT_IF_THEY_REJECT` when rejection has real consequences on the sender (opinion penalty, retaliation, tariff, follow-up event chain, etc.). If rejection just means "nothing happens," omit it — the accept tooltip already implies the alternative, and empty reject blocks are redundant noise. When both branches have real outcomes, include both:

```
OTHER = { country_event = { id = foo.1 days = 1 } }
custom_effect_tooltip = TT_IF_THEY_REJECT
effect_tooltip = {
	# effects / tooltip keys summarising the rejection outcome (opinion penalty, retaliation, etc.)
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
