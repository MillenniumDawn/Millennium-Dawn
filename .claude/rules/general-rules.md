# File Encoding

- All `.txt` files (focus trees, events, decisions, ideas, etc.) must be **UTF-8 without BOM**. Never add a BOM byte sequence (`EF BB BF`).
- Only `.yml` localisation files use UTF-8 **with** BOM.

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
- **Naming:** Always prefix country-specific variables with the country tag (e.g., `ISR_operation_success`, not `oper_succ_var`). Unprefixed names risk collision when another country sets the same name on a shared scope.

## tag vs original_tag

- `tag` = current runtime tag (changes for civil war split-offs like `NIG_CW_0`)
- `original_tag` = base tag that never changes (`NIG`)
- Always use `original_tag` in idea `allowed` blocks, MIO `allowed` blocks, and anywhere you restrict a game object to a specific nation. Using `tag` breaks those objects for civil war countries.
- `tag` is only correct when you explicitly want the _current_ tag (e.g., `trigger = { tag = ISR }` to check if the current scope IS ISR, not a civil war copy).

# Documentation References

For more comprehensive HOI4 scripting docs (effects, triggers, modifiers, wiki links), read `.claude/docs/documentation-references.md`.

For 3D unit models — the mesh/entity/animation chain, the `<TAG>` → `<graphical_culture>` → generic entity lookup, and `gfx/entities/` organisation — read `.claude/docs/entity-system.md`. That doc also covers landmark buildings (state-file placement, `map/buildings.txt` spawn points, `provinces.bmp` validation, heightmap-calibrated `y`, and common rendering gotchas).

For **power / energy work** — power-plant buildings (renewable / nuclear / fossil), energy technologies in `common/technologies/industry.txt`, the power-per-build-cost balance, and the renewable-hotspot state factor — read `.claude/docs/energy-power-balance.md`. It documents the S-curve tech design and points at the two tools that own it: `tools/balance/set_energy_tech_scurves.py` (re-tunes/writes the tech buffs) and `tools/analysis/renewable_power_per_cost.py` (charts/verifies the crossovers).

# Comments

Default to writing **no comments**. Only add one when the WHY is non-obvious:

- A hidden constraint not visible from surrounding code (e.g., "must run before X or Y fires twice")
- A subtle invariant the reader needs to safely edit this block
- A deliberate workaround for a specific engine bug or parser quirk
- Behaviour that would genuinely surprise a competent reader

**Never** add comments that:

- Explain WHAT the code does — well-named effects, triggers, and variables already communicate that
- Narrate the change ("Added for the X fix", "Handles case from issue #123") — that belongs in the commit message
- Reference callers or downstream consumers ("used by Y", "called from Z") — these rot over time
- Restate the effect name in prose (`# add stability` above `add_stability = 0.05`)
- Justify a mechanic in flavour or game-world prose — the trigger and modifier already say what it models
- Span multiple lines to walk through a block — if a block needs a paragraph, restructure or rename instead

Keep any surviving comment to a single terse line. A comment that needs a paragraph is a sign the code, not the prose, needs work.

```
# Wrong — flavour narration restating the trigger/modifier in prose
# Nationalised healthcare extends coverage to the worst-affected
if = { limit = { has_idea = fully_nationalized_healthcare } add_to_variable = { hiv_improve_weight = 15 } }

# Correct — no comment; the trigger and variable already read clearly
if = { limit = { has_idea = fully_nationalized_healthcare } add_to_variable = { hiv_improve_weight = 15 } }
```

When in doubt, delete the comment. If the code is unclear without it, rename or restructure the code first.

# Scripting Patterns

## NOT block scope

`NOT = { condition_A condition_B }` means NOT(A **AND** B), "not both true at once". Almost never intended. Write separate blocks when you mean "neither can be true":

```
# Wrong — only blocks when both are true simultaneously
NOT = { has_idea = foo has_idea = bar }

# Correct — blocks each independently
NOT = { has_idea = foo }
NOT = { has_idea = bar }
```

## NOR is not a valid trigger

`NOR` is **not** a HOI4 trigger keyword — it is Norway's country tag. `NOR = { ... }` opens a country scope for Norway, not a logical NOR block. Express "none of these" as separate `NOT` blocks or `NOT = { OR = { ... } }`:

```
# Wrong — this scopes into Norway, not a logical NOR
NOR = { has_government = democratic has_idea = social_05 }

# Correct — separate NOT blocks
NOT = { has_government = democratic }
NOT = { has_idea = social_05 }

# Also correct — NOT wrapping an OR
NOT = { OR = { has_government = democratic has_idea = social_05 } }
```

## Use `random` over two-bucket `random_list`

A `random_list` with two buckets where one is empty is a Bernoulli trial in the wrong syntax. Collapse it:

```
# Heavier — placeholder bucket
random_list = { 50 = { add_to_variable = { my_counter = 1 } } 50 = {} }

# Lighter — direct probability roll
random = { chance = 50 add_to_variable = { my_counter = 1 } }
```

Three+ buckets, or two non-empty buckets with different effects, must stay as `random_list`. See `.claude/docs/simplification-patterns.md` for edge cases.

## Tautological OR in ai_will_do modifiers

An `OR` block inside an `ai_will_do modifier` that covers all possible values of a trigger is always true and does nothing:

```
# Wrong — OR(yes, no) is always true; modifier fires unconditionally
modifier = { add = 1 OR = { is_historical_focus_on = yes is_historical_focus_on = no } }
```

Remove the entire modifier block and fold the `add` amount into `base = N`. If a real condition was intended (e.g., add only when historical focus is on), write it without the tautological OR.

## Implicit AND in triggers

Multiple conditions in a trigger block are implicitly AND-ed. Never wrap them in redundant `AND = { }`:

```
# Wrong — redundant AND wrapper
trigger = { AND = { A B C } }

# Correct — implicit AND
trigger = { A B C }
```

Applies to `trigger`, `limit`, `visible`, `available`, `activation`, `cancel_trigger`, and all other trigger contexts.

## Modifier names

Invalid modifier names compile silently and do nothing — the game logs "Unknown modifier" but loads the idea/focus anyway. **Never guess a modifier name.** Verify it exists first:

```bash
grep -r "modifier_name_here" common/ideas/*.txt common/national_focus/*.txt | head -3
```

No results means the name is wrong. Check the wiki or copy the exact spelling from a similar modifier in the codebase.

## threat scale

`threat` is a decimal 0.0–1.0, never a percentage. `threat > 10` or `threat > 40` are always false. Use `threat > 0.10`, `threat > 0.40`, etc.

## check_variable comparison operators

`check_variable` only accepts `=`, `>`, and `<` inline. `>=` and `<=` are **not valid syntax** — the parser silently treats them as something else and the check never matches.

```
# Wrong — >= and <= are not valid inline
check_variable = { v >= 0 }

# Correct — use compare = ...
check_variable = { var = v value = 0 compare = greater_than_or_equals }
```

Valid `compare` values: `equals`, `greater_than`, `less_than`, `greater_than_or_equals`, `less_than_or_equals`, `not_equals`.

## Variable and array operations do not auto-tooltip

These operations produce **no automatic tooltip text**: `check_variable`, `is_in_array`, `add_to_variable`, `subtract_from_variable`, `set_variable`, `multiply_variable`, `divide_variable`, `clamp_variable`, `set_temp_variable`, `add_to_temp_variable`, `add_to_array`, `remove_from_array`. Used bare in `available`, `visible`, or trigger blocks the player sees nothing (triggers) or a blank line (effects).

If the player needs to see why a focus/decision is locked or what an effect does, wrap the operation:

- **Triggers:** use `custom_trigger_tooltip` with a loc key
- **Effects:** use `custom_effect_tooltip` before or after the operation

```
# Wrong — no explanation for why the focus is unavailable
available = { check_variable = { my_var > 10 } }

# Correct — player sees the loc string
available = {
	custom_trigger_tooltip = { tooltip = my_requirement_tt check_variable = { my_var > 10 } }
}
```

Named scripted triggers (e.g., `my_trigger = yes`) **do** auto-tooltip using the trigger's name as a loc key, so they are safe bare in player-facing blocks. Prefer named triggers over raw variable checks in `available`/`visible` when the player needs feedback.

## is_in_faction vs is_in_faction_with

`is_in_faction` is a **boolean** trigger (`yes`/`no`). To check membership with a specific country, use `is_in_faction_with = TAG`. `is_in_faction = TAG` silently fails. **Caught by `check_common_mistakes.py`.**

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

| Verbose (scope expansion)       | Flat equivalent        |
| ------------------------------- | ---------------------- |
| `TAG = { exists = yes }`        | `country_exists = TAG` |
| `TAG = { is_puppet = yes }`     | `is_puppet_of = TAG`   |
| `TAG = { has_war_with = ROOT }` | `has_war_with = TAG`   |

Apply everywhere — focuses, events, decisions, scripted triggers. If a flat trigger exists, prefer it.

## Case sensitivity in references

HOI4 on Linux is **case-sensitive** for all identifiers — ideas, events, decisions, focuses, variables, flags, GFX sprites, scripted effects/triggers. `has_idea = The_Military` will NOT match `the_military`. Always match the definition's exact case. **Caught by `validate_ideas.py` for ideas.**

Also applies inside namelist files:

- `division_types = { ... }` in `common/units/names_divisions/*.txt` must match the canonical sub-unit names in `common/units/MD_land_units.txt` exactly. Typical case-typo patterns: lowercase prefixes (`arm_inf_bat` vs `Arm_Inf_Bat`), mid-token capitalisation (`mech_inf_Bat` vs `Mech_Inf_Bat`), single-letter slips (`Assault` vs `assault`). Wrong case = the namelist silently never matches the template.
- `ship_types = { ... }` in `common/units/names_ships/*.txt` must match `common/units/MD_naval_units.txt`. Legacy vanilla tokens (`submarine`, `light_cruiser`, `ship_hull_*`, `battleship_hull_0`, etc.) were removed by MD — entries using them are silently dead. See `.claude/docs/namelist-reference.md` for the canonical lists.

## Trade agreement checks in MD

`has_trade_agreement_with` is **not a valid HOI4 trigger** — compiles silently, always false. MD uses `has_country_flag = trade_agreement@TAG`. **Caught by `check_common_mistakes.py`.**

## Decision allowed vs available

`allowed` in decisions is evaluated **once at game start** and locked. Dynamic conditions (factory counts, opinion, date) must go in `available` or `visible`. **Caught by `check_common_mistakes.py`** for clearly-dynamic triggers.

## if/else over if/if

When two consecutive `if` blocks cover complementary conditions, always use `if/else`:

```
# Wrong — double-execution risk if conditions overlap
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

Three pitfalls:

1. **Don't write redundant defaults.** `set_temp_variable = { tag_index = ROOT.id }` and `set_temp_variable = { influence_target = THIS.id }` are no-ops. Leave them out.
2. **Orphan setters are silent bugs.** A `percent_change` / `tag_index` / `influence_target` triple with no following `change_influence_percentage = yes` does nothing. When auditing influence code, grep for `percent_change` setters and confirm each has a matching invocation in the same scope.
3. **Loop-local temp vars need the call inside the loop.** Setting temp vars inside `random_other_country` / `random_country` / `every_country` then calling `change_influence_percentage = yes` outside the block runs the effect once with stale or undefined values. The invocation must live in the same scope as the temp-var writes.

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

When a function uses `^index` array subscripts, the **meaning of the index variable** must be obvious and consistent. Bugs arise when two different index types are stored in similarly-named variables.

| Variable name              | Should hold                  | Must NOT hold                                   |
| -------------------------- | ---------------------------- | ----------------------------------------------- |
| `project`, `slot`, `idx`   | Slot / array position (0..N) | Building type, category ID, or other lookup key |
| `type`, `kind`, `category` | Lookup key / type ID (1..N)  | Slot index                                      |

**Rule:** Document an array-index parameter in the function comment. Verify every caller passes the right kind of index. See `.claude/docs/refactor-checklist.md` for the full verification steps.

## Simplification & Performance Patterns

Dedicated catalogs, both required reading whenever you touch hot-path code or a file with copy-paste branching:

- `.claude/docs/simplification-patterns.md` — array lookup tables, parameterized scripted loc, collapsing parallel `if/else_if` chains, etc.
- `.claude/docs/performance-patterns.md` — hoist invariants out of loops, GUI `dirty` counters, engine arrays vs `every_country`, clamp-before-divide, etc.

Do not duplicate the principles here — they drift. Cite the canonical doc.

## Refactor Breaking-Change Checklist

When renaming prefixes, migrating globals to arrays, or changing function signatures:

1. Grep the **entire repo** for old names (flags, variables, events, decisions, GUI, GFX).
2. Verify array-index semantics: trace every caller to confirm the index variable holds the expected value.
3. Check localisation for `[?global.old_name]` references — these fail silently to 0.
4. Verify event `log =` strings match option `name =` keys after any copy/rename.
5. Confirm GUI `window_name`, button names, and GFX sprite names are cross-referenced.

See `.claude/docs/refactor-checklist.md` for the full checklist.

# Event Patterns

## Cross-country event tooltips

When a focus `completion_reward` or event option fires an event to another country, add a `TT_IF_THEY_ACCEPT` tooltip immediately after the event fire so the player sees what happens on acceptance:

```
OTHER = { country_event = { id = foo.1 days = 1 } }
custom_effect_tooltip = TT_IF_THEY_ACCEPT
effect_tooltip = { # acceptance outcome }
```

Only add `TT_IF_THEY_REJECT` when rejection has real consequences on the sender (opinion penalty, retaliation, tariff, follow-up event chain, etc.). If rejection just means "nothing happens," omit it — empty reject blocks are redundant noise. When both branches have real outcomes, include both:

```
OTHER = { country_event = { id = foo.1 days = 1 } }
custom_effect_tooltip = TT_IF_THEY_ACCEPT
effect_tooltip = { # acceptance outcome }
custom_effect_tooltip = TT_IF_THEY_REJECT
effect_tooltip = { # rejection outcome (sanctions, opinion hit, etc.) }
```

Keys are in `localisation/english/MD_tooltips_l_english.yml`:

- `TT_IF_THEY_ACCEPT` / `TT_IF_THEY_REJECT` — outcomes of YOUR action firing to THEM
- `TT_IF_WE_ACCEPT` / `TT_IF_WE_DECLINE` — inside the target's event option

## Event namespace mismatch

Event IDs in `country_event = { id = foo.1 }` must match the namespace declared at the top of the events file (`add_namespace = foo`). If the file uses `add_namespace = bar`, the correct ID is `bar.1` — a mismatch silently fires nothing.

Check: grep `add_namespace` at the top of the events file, then verify every caller uses that exact prefix.

## Log message option IDs

Log messages inside event options must match the option's own ID exactly:

```
option = {
	name = foo.1.b
	log = "[GetDateText]: [This.GetName]: foo.1.b executed"  # .b, not .a
```

Copy-pasting from option A and forgetting to update to `.b` is a common source of misleading logs.

## Ignore Resources folder

When making a plan or change, ignore any files in `resources/`.
