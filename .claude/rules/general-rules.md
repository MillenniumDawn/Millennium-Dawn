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

## Tautological OR in ai_will_do modifiers

An `OR` block inside an `ai_will_do modifier` that covers all possible values of a trigger is always true and does nothing useful:

```
# Wrong — OR(yes, no) is always true; modifier fires unconditionally
modifier = {
    add = 1
    OR = {
        is_historical_focus_on = yes
        is_historical_focus_on = no
    }
}

# Correct — if you want an unconditional bonus, remove the OR entirely
# and fold the value into base = N, or remove the modifier block
```

Remove the entire modifier block and increase `base` by the `add` amount instead. If a real condition was intended (e.g., add only when historical focus is on), write it without the tautological OR.

## Implicit AND in triggers

Multiple conditions in a trigger block are implicitly AND-ed together. Never wrap conditions in redundant `AND = { }` blocks:

```
# Wrong — redundant AND wrapper
trigger = { AND = { A B C } }

# Correct — implicit AND
trigger = { A B C }
```

This applies to `trigger`, `limit`, `visible`, `available`, `activation`, `cancel_trigger`, and all other trigger contexts.

## Modifier names

Invalid modifier names compile silently and do nothing — the game logs an "Unknown modifier" error but loads the idea/focus anyway. **Never guess a modifier name.** Always verify it exists first:

```bash
grep -r "modifier_name_here" common/ideas/*.txt common/national_focus/*.txt | head -3
```

If no results, the name is wrong. Check the wiki or find a similar modifier in the codebase and use the exact same spelling.

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

## is_in_faction vs is_in_faction_with

`is_in_faction` is a **boolean** trigger (`yes`/`no`). To check faction membership with a specific country, use `is_in_faction_with = TAG`. Using `is_in_faction = TAG` silently fails. **Caught by `check_common_mistakes.py`.**

## add_to_faction scope

`add_to_faction` adds a **country** to the **current scope's faction**. It takes a country tag or scope, not a faction name. `add_to_faction = BRICS` is wrong — use `add_to_faction = TAG`.

## Minimize scope expansion

Avoid opening a scope just to check a single boolean or trigger when a flat equivalent exists. Every `TAG = { ... }` is a scope switch the engine must resolve.

```
# Wrong — unnecessary scope expansion
NOT = { PAK = { exists = no } }
PAK = { exists = yes }

# Correct — flat trigger, no scope switch
country_exists = PAK
```

Other common patterns:

| Verbose (scope expansion)       | Flat equivalent        |
| ------------------------------- | ---------------------- |
| `TAG = { exists = yes }`        | `country_exists = TAG` |
| `TAG = { is_puppet = yes }`     | `is_puppet_of = TAG`   |
| `TAG = { has_war_with = ROOT }` | `has_war_with = TAG`   |

Apply this principle everywhere — focuses, events, decisions, scripted triggers. If a flat trigger exists, prefer it.

## Case sensitivity in references

HOI4 on Linux is **case-sensitive** for all identifiers — ideas, events, decisions, focuses, variables, flags, GFX sprites, and scripted effects/triggers. `has_idea = The_Military` will NOT match a definition `the_military`. Always match the exact case of the definition. **Caught by `validate_ideas.py` for ideas.**

This also applies inside namelist files:

- `division_types = { ... }` in `common/units/names_divisions/*.txt` must match the canonical sub-unit names in `common/units/MD_land_units.txt` exactly — the case of every letter matters. Typical case-typo patterns: lowercase prefixes (`arm_inf_bat` vs canonical `Arm_Inf_Bat`), mid-token capitalisation (`mech_inf_Bat` vs `Mech_Inf_Bat`), or single-letter case slips (`Assault` vs `assault`). When the case is wrong the namelist silently never matches the template.
- `ship_types = { ... }` in `common/units/names_ships/*.txt` must match `common/units/MD_naval_units.txt`. Legacy vanilla tokens (`submarine`, `light_cruiser`, `ship_hull_*`, `battleship_hull_0`, etc.) were removed by MD — entries using them are silently dead. See `.claude/docs/namelist-reference.md` for the canonical lists.

## Trade agreement checks in MD

`has_trade_agreement_with` is **not a valid HOI4 trigger** — compiles silently, always evaluates false. MD uses `has_country_flag = trade_agreement@TAG`. **Caught by `check_common_mistakes.py`.**

## Decision allowed vs available

`allowed` in decisions is evaluated **once at game start** and locked. Dynamic conditions (factory counts, opinion, date) must go in `available` or `visible`. **Caught by `check_common_mistakes.py`** for clearly-dynamic triggers.

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

## change_influence_percentage

The scripted effect uses temp-variable arguments with these defaults:

| Temp variable      | Required | Default   |
| ------------------ | -------- | --------- |
| `percent_change`   | yes      | —         |
| `tag_index`        | no       | `ROOT.id` |
| `influence_target` | no       | `THIS.id` |

Three pitfalls to avoid:

1. **Don't write redundant defaults.** `set_temp_variable = { tag_index = ROOT.id }` and `set_temp_variable = { influence_target = THIS.id }` are no-ops — the call already uses those defaults. Leave them out.

2. **Orphan setters are silent bugs.** A `percent_change` / `tag_index` / `influence_target` triple with no following `change_influence_percentage = yes` does nothing — the temp vars get set and discarded. When auditing influence code, grep for `percent_change` setters and confirm each has a matching invocation in the same scope.

3. **Loop-local temp vars need the call inside the loop.** Setting temp vars inside `random_other_country` / `random_country` / `every_country` and then calling `change_influence_percentage = yes` outside the block runs the effect once with stale or undefined values. The invocation must live in the same scope as the temp-var writes.

```
# Wrong — call runs outside the loop; tag_index/influence_target resolve to outer scope
random_other_country = {
    limit = { ... }
    set_temp_variable = { percent_change = 3 }
    set_temp_variable = { tag_index = THIS.id }
    set_temp_variable = { influence_target = PREV.id }
}
change_influence_percentage = yes

# Correct — call inside the loop with the loop-local scopes
random_other_country = {
    limit = { ... }
    set_temp_variable = { percent_change = 3 }
    set_temp_variable = { tag_index = THIS.id }
    set_temp_variable = { influence_target = PREV.id }
    change_influence_percentage = yes
}
```

Also watch for typos in the temp-var name itself (e.g., `influence_tBRAet` from a botched search-and-replace) — the engine accepts any name, so a typo silently sets a never-read variable and the influence change uses the default `THIS.id` target.

# Array Index Semantics

When a function uses `^index` array subscripts, the **meaning of the index variable** must be obvious and consistent. Common bugs arise when two different index types are stored in similarly-named variables.

| Variable name              | Should hold                  | Must NOT hold                                   |
| -------------------------- | ---------------------------- | ----------------------------------------------- |
| `project`, `slot`, `idx`   | Slot / array position (0..N) | Building type, category ID, or other lookup key |
| `type`, `kind`, `category` | Lookup key / type ID (1..N)  | Slot index                                      |

**Rule:** When a function parameter is an array index, document it in the function comment. Verify every caller passes the right kind of index. See `.claude/docs/refactor-checklist.md` for the full verification steps.

---

## Simplification & Performance Patterns

These have dedicated catalogs — both are required reading whenever you touch hot-path code or a file with copy-paste branching:

- `.claude/docs/simplification-patterns.md` — array lookup tables, parameterized scripted loc, collapsing parallel `if/else_if` chains, etc.
- `.claude/docs/performance-patterns.md` — hoist invariants out of loops, GUI `dirty` counters, engine arrays vs `every_country`, clamp-before-divide, etc.

Do not duplicate the principles here — they drift. Cite the canonical doc.

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
	# effects summarising the acceptance outcome
}
# Only add the reject block if rejection has actual consequences:
custom_effect_tooltip = TT_IF_THEY_REJECT
effect_tooltip = {
	# effects summarising the rejection outcome (sanctions, opinion hit, etc.)
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
