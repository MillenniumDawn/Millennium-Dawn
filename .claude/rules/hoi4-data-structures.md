# HOI4 Data Structures — Comprehensive Reference

For full lists of effects, triggers, modifiers, and dynamic variables, see the corresponding files in `resources/documentation/`.

---

## Scope References

These keywords refer to countries/states relative to the current execution context:

| Keyword      | Meaning                                                                     |
| ------------ | --------------------------------------------------------------------------- |
| `THIS`       | The current scope (usually implicit; rarely written explicitly)             |
| `ROOT`       | The original scope at the start of the block (event, focus, decision, etc.) |
| `PREV`       | The previous scope before the most recent scope change                      |
| `FROM`       | The sender scope (used in events: `FROM` is the event sender)               |
| `OWNER`      | The owner of the current state scope                                        |
| `CONTROLLER` | The controller of the current state scope                                   |
| `OCCUPIED`   | The occupied country in the current state scope                             |
| `CAPITAL`    | The capital state of the current country scope                              |

`PREV` chains: inside a nested scope, `PREV` = the immediate prior scope, `PREV.PREV` = the one before that.

---

## Variable Types

### Persistent variables

Stored on a scope (country, state, unit leader). Survive saves.

```
SOV = { set_variable = { var = my_var value = 5 } }
SOV.my_var         # read from another scope
```

### Temporary variables

Exist only for the duration of the current scripted block. Prefixed with `temp_` in effects but accessed by name.

```
set_temp_variable = { var = my_temp value = 10 }
```

### Global variables

Stored globally, not on any scope.

```
set_global_variable = { var = global_my_var value = 1 }
global.global_my_var   # read globally
```

### Array elements

Accessed via `^` subscript (zero-indexed):

```
my_array^0       # first element
my_array^3       # fourth element
my_array^i       # element at index i (dynamic index from a loop variable)
```

---

## Variable Access Syntax

```
my_var                          # local variable on current scope
ROOT.my_var                     # variable on ROOT scope
GER.my_var                      # variable on specific country
my_array^0                      # array element by literal index
my_array^i                      # array element by dynamic loop index
var:my_var = { ... }            # scope into the country/state stored in my_var
var:my_array^i = { ... }        # scope into the country stored at array[i]  ← CORRECT
var:v = { ... }                 # scope into the country stored in loop value v ← CORRECT
var:v^i = { ... }               # WRONG — v is a scalar value, not an array
```

**Key rule:** `value = v` in a loop stores the **scalar element** (e.g. a country tag number) into `v`. It is NOT an array reference. To scope into the country at position `i`, use either:

- `var:v = { ... }` (v holds the country reference directly)
- `var:ARRAYNAME^i = { ... }` (explicit array name + dynamic index)

Never use `var:v^i` — `v` is a scalar and `^i` subscripting does not apply.

---

## Variable & Array Effects

All use `{ var = X value = Y }` syntax. All have `_temp_` equivalents (e.g. `add_to_temp_variable`).

**Variables:** `set_variable`, `add_to_variable`, `subtract_from_variable`, `multiply_variable`, `divide_variable`, `modulo_variable`, `round_variable`, `clamp_variable` (min/max), `set_variable_to_random`

**Arrays:** `add_to_array`, `remove_from_array` (by value or index), `clear_array`, `resize_array`, `find_highest_in_array`, `find_lowest_in_array`, `random_scope_in_array`

Short forms: `add_to_array = { my_array = 42 }`, `remove_from_array = { my_array = 42 }`, `is_in_array = { my_array = 42 }`

---

## Loop Effects

### `for_each_loop` — iterate over values

```
for_each_loop = {
    array = my_array
    value = v               # current element value (default 'v')
    index = i               # current index (default 'i')
    break = brk             # set this var to non-zero to break (default 'break')
    # effects...
}
```

`v` = the scalar value at position `i`. To scope into a country stored at `i`:

```
var:my_array^i = { ... }   # recommended — uses array name
var:v = { ... }            # also valid — v holds the country reference
```

### `for_each_scope_loop` — iterate and auto-scope

```
for_each_scope_loop = {
    array = my_array
    break = brk             # optional
    tooltip = loc_key       # optional tooltip
    # effects run inside each element's scope automatically
}
```

### `for_loop_effect` — numeric counter loop

```
for_loop_effect = {
    start = 0               # default 0
    end = 10
    compare = less_than     # default less_than; also: less_than_or_equals, greater_than, etc.
    add = 1                 # step (default 1)
    value = v               # loop counter variable (default 'v')
    break = brk             # optional break variable
    # effects...
}
```

---

## Array / Variable Triggers

### `any_of` — loop, return true if any match

```
any_of = {
    array = my_array
    value = v               # current element scalar (default 'value')
    index = i               # current index (default 'index')
    # triggers — returns true if ALL triggers true for at least one element
}
```

Returns `false` if array is empty or no element satisfies all triggers.

### `all_of` / `any_of_scopes` / `all_of_scopes`

`all_of` — same syntax as `any_of`, returns true only if ALL elements match.

`any_of_scopes` / `all_of_scopes` — auto-scope into each element (no `value`/`index` variables):

```
any_of_scopes = {
    array = my_array
    # triggers evaluated inside each element's scope
}
```

**`any_of` vs `any_of_scopes`:** `any_of` stays in current scope (access via `var:v`); `any_of_scopes` auto-scopes into each element (simpler for country/state arrays).

### `check_variable`

```
check_variable = { my_var > 12 }         # shorthand (also =, <)
check_variable = { var = my_var value = 12 compare = greater_than }  # explicit
```

Compare values: `less_than`, `less_than_or_equals`, `greater_than`, `greater_than_or_equals`, `equals`, `not_equals`.

### Other triggers

- `is_in_array = { my_array = 42 }` — check membership
- `var:my_var = { exists = yes }` — check if country in variable actually exists in-game

---

## Dynamic Variables (Read-Only)

Computed by the game engine. Full list in `resources/documentation/dynamic_variables_documentation.md`.

Common: `global.countries`, `global.majors`, `global.states`, `global.year`, `global.threat`, `num_of_civilian_factories`, `num_of_military_factories`, `stability`, `war_support`, `political_power`, `manpower`, `faction_members`, `allies`, `subjects`.

---

## Script Collections

Collections are sets of game objects that support chained operators for filtering and expansion — more efficient than manual array loops for many use cases.

### Structure

```
collection_size = {
    input = {
        input = game:scope              # base input
        operators = { faction_members owned_states }  # chained operators
        name = "States owned by faction" # optional display name
    }
    value > 42
}
```

### Inputs

| Input                         | Description                                            |
| ----------------------------- | ------------------------------------------------------ |
| `game:all_countries`          | All existing countries (including government in exile) |
| `game:all_possible_countries` | All countries (including non-existing)                 |
| `game:all_states`             | All existing states                                    |
| `game:scope`                  | Current scope object                                   |
| `collection:NAME`             | Named collection                                       |
| `constant:NAME`               | Script constant                                        |

### Operators

| Operator                   | Description                                           |
| -------------------------- | ----------------------------------------------------- |
| `faction_members`          | All faction members of the country (including itself) |
| `owned_states`             | All states owned by the country                       |
| `controlled_states`        | All states controlled by the country                  |
| `country_and_all_subjects` | The country and all its subjects                      |
| `trigger = { ... }`        | Filter by trigger (used inside `limit`)               |

### Shorthand

```
my_collection = game:all_states   # equivalent to { input = game:all_states }
```

For full collection docs, see `resources/documentation/script_collection_input.md` and `script_collection_operator.md`.

---

## Script Constants

Reusable constants usable across all script files (unlike file-local `@` macros). No runtime cost. Usage: `constant:numeric_constants.pi`. See `resources/documentation/script_concept_documentation.md`.

---

## Formatted Localization

Used in `custom_effect_tooltip` and other bindable-loc contexts. Three forms:

```
# Simple loc key
custom_effect_tooltip = MY_TOOLTIP

# Formatter (generates text from game data — e.g., idea description)
custom_effect_tooltip = idea_desc|canadian_pacific_railway

# Bound localization (parameter injection)
custom_effect_tooltip = {
    localization_key = MY_TOOLTIP
    PARAM_NAME = OTHER_LOC_KEY
}
```

Available formatters: `idea_desc`, `idea_name`, `tech_effect`, `advisor_desc`, `country_leader_desc`, `character_name`, `country_culture`, `building_state_modifier`. See `resources/documentation/loc_formatter_documentation.md` for parameters and scope requirements.

### Contextual Localization in Strings

Access scope objects in loc strings using `[Object.Property]` syntax:

```
"[Root.GetName] has signed a treaty with [FROM.GetName]"
"[Root.Capital.GetName] is under threat"
"[This.GetLeader] addresses the nation"
```

Object promotions (scope changes): `Owner`, `Capital`, `OriginalCapital`, `Overlord`, `FactionLeader`, `Controller`, `Occupied`.
Common properties: `GetName`, `GetTag`, `GetFlag`, `GetAdjective`, `GetLeader`, `GetFactionName`.

For full object/property lists, see `resources/documentation/loc_objects_documentation.md`.
