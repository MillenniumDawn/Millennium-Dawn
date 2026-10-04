# HOI4 Data Structures

Full lists of effects, triggers, modifiers, math statements, collections, and dynamic
variables are in `resources/documentation/`. This doc covers the shapes and the traps.

## Scopes and identity

`ROOT` is the original scope, `FROM` the event sender, and `PREV` the previous scope
(`PREV.PREV` chains). `OWNER` and `CAPITAL` select the state's owner and country's
capital. `CONTROLLER` is state-scope only. Event dispatch can change what `FROM`
means; see [Effect Scope Interpolation](scripting-edge-cases.md#effect-scope-interpolation).

`tag` is the runtime tag; civil-war countries get a new one. `original_tag` retains
national identity. Use `original_tag` for nation-restricted objects such as MIOs and
slotted ideas; use `tag` only when the literal current tag matters. Unslotted ideas
have separate rules in [Idea Reference](idea-reference.md).

## State and naming

- Prefix country-specific variables and flags with `TAG_`, globals with `GLOBAL_`,
  and shared-system state with its domain prefix. Use `snake_case` after the prefix;
  keep system acronyms uppercase.
- Query existing ideas, focus completion, ideology, subjects, factions, variables,
  or event targets instead of adding a flag that mirrors them. A flag is appropriate
  for otherwise unavailable state or a historical transition.
- Unset numeric variables read as zero. Do not seed them to zero at startup, including
  dynamic-modifier backing variables. Resetting a used variable to zero is different.
- Keep array slot indices distinct from type IDs. See
  [Array Index Semantics](scripting-edge-cases.md#array-index-semantics).

## Variables

```
my_var                    # variable on the current scope, survives saves
ROOT.my_var               # variable on ROOT
GER.my_var                # variable on a specific country
global.my_var             # global variable
my_array^0                # array element, zero-indexed
my_array^i                # element at a dynamic index
var:my_var = { ... }      # scope into the country or state stored in my_var
var:my_array^i = { ... }  # scope into the country stored at index i
```

- Temp variables (`set_temp_variable`) exist only for the current scripted block and
  belong to no scope. Read, write, and check them by bare name from any scope. A `ROOT.`
  or `PREV.` prefix breaks the read, and a `ROOT = { check_variable = ... }` wrapper
  adds nothing.
- Arrays cap at 1000 elements. `add_to_array` past index 999 silently does nothing.
- In a loop, `value = v` holds the scalar element, not an array reference. Scope with
  `var:v = { ... }` or `var:ARRAY^i = { ... }`. Never `var:v^i`.

Effects use `{ var = X value = Y }` and have `_temp_` equivalents:

- Variables: `set_variable`, `add_to_variable`, `subtract_from_variable`,
  `multiply_variable`, `divide_variable`, `modulo_variable`, `round_variable`,
  `clamp_variable`, `set_variable_to_random`.
- Arrays: `add_to_array`, `remove_from_array`, `clear_array`, `resize_array`,
  `find_highest_in_array`, `find_lowest_in_array`, `random_scope_in_array`.
- Short forms: `add_to_array = { my_array = 42 }`, `is_in_array = { my_array = 42 }`.

## Math expressions

Use a math expression instead of a chain of `set_temp_variable`, `add_to_variable`, and
`multiply_variable` when the goal is a calculated value. The engine evaluates it in one
pass, which matters most on hot paths. Keep a temp only when an intermediate is reused,
or for `modulo_variable` and `clamp_variable`, which do not take expressions.

The expression is the value of the effect: a base `value = ...` followed by statements
that mutate an accumulator. Two equivalent shapes:

```
set_temp_variable = {
    foo = {
        value = bar
        multiply = 2
        add = baz
    }
}

set_temp_variable = {
    var = foo
    value = {
        value = bar
        multiply = 2
        add = baz
    }
}
```

It is also valid as the value of `add_to_variable`, `subtract_from_variable`,
`multiply_variable`, and `divide_variable`. A self-referencing
`set_variable = { X = { value = X  add = { ... } } }` reads the pre-write value.

Traps:

- Statements written as siblings of `var = X` silently evaluate to 0:

```
# WRONG
set_variable = {
    var = combined_units
    value = num_cavalry
    add = num_motorized
}
```

- `FROM.<var>` reads return 0 inside an expression and zero the whole result. Copy the
  value to a temp first: `set_temp_variable = { bailout_cost = FROM.debt_bailout }`.
  Only `FROM.` needs the copy.
- A malformed expression evaluates to 0 with no in-game sign. It logs at load:
  `script_math.cpp:350: Errors occurred while reading math expression defaulting to 0`.
- One bad expression cascades. The parser reads the rest of the file one brace level
  off, so later blocks report bogus errors. Fix the first `script_math` error in a file
  and rerun. Brace counts still balance.
- An `if` inside an expression takes an expression as its `limit`:
  `if = { limit = { value = x  equals = 0 }  add = 15 }`.

Statements: `add`, `subtract`, `multiply`, `divide`, `mod`, `pow`, `root`, `log`, `min`,
`max`, `clamp = { min = X max = Y }`, `lerp = { to = X alpha = Y }`, `round = yes`, the
trigonometry functions, the comparators (`equals`, `not_equals`, `greater_than`,
`less_than`, and the `_or_equals` forms), `and`, `or`, `xor`, `not = yes`, `if`/`else`,
and `every_collection`. Comparators and boolean operators return 1 or 0. Each argument
is itself an expression, so they nest. Full list:
`resources/documentation/script_math_functions.md`.

A statement in that file is valid. For anything else, grep MD and vanilla for precedent,
since the engine silently zeroes what it cannot parse. Operands confirmed working:
`array^i`, `array^num`, nested operand blocks, `ROOT.`/`THIS.`/`PREV.` reads, and
targeted game variables (`opinion@PREV`, `building_level@X`, `modifier@X`). Those are
plain variables: use them directly, with no temp copy.

`validate_math_expressions.py` warns in CI on the sibling form and on `FROM` reads.

## Loops

```
for_each_loop = {
    array = my_array
    value = v               # element value (default 'v')
    index = i               # index (default 'i')
    break = brk             # set non-zero to break (default 'break')
}

for_each_scope_loop = {     # scopes into each element
    array = my_array
    tooltip = loc_key       # optional
}

for_loop_effect = {
    start = 0
    end = 10
    compare = less_than     # default
    add = 1
    value = v
}

while_loop_effect = {
    limit = { check_variable = { counter < target } }
}
```

- Numeric arrays use `for_each_loop`. Country and state arrays use
  `for_each_scope_loop`. Mismatching them silently misbehaves.
- `for_each_scope_loop` has no top-level `limit`. Use an inner `if`.
- `while_loop_effect` hard-caps at 1000 iterations. `max_iterations` is not a valid key.

## Triggers

```
any_of = {
    array = my_array
    value = v               # default 'value'
    index = i               # default 'index'
}

any_of_scopes = {           # scopes into each element
    array = my_array
}
```

- `all_of` and `all_of_scopes` take the same syntax and require every element to match.
  `any_of` returns false on an empty array.
- `check_variable = { my_var > 12 }` accepts `=`, `<`, and `>` inline. Inline `>=` and
  `<=` do not work. Use the explicit form with `var`, `value`, and
  `compare = greater_than_or_equals`. Compare values: `less_than`,
  `less_than_or_equals`, `greater_than`, `greater_than_or_equals`, `equals`,
  `not_equals`.
- `is_in_array = { my_array = 42 }` checks membership.
- `var:my_var = { exists = yes }` checks that the stored country exists.

## Tooltips

Bare variable checks, array checks, and variable writes produce no useful tooltip. Give
visible requirements a `custom_trigger_tooltip` and summarize effects with
`custom_effect_tooltip`, or use an effect's `tooltip = KEY` form. Verify the rendered
tooltip of a localised scripted trigger before relying on it.

A failing `visible` hides the object, so it needs no requirement tooltip. AI-only
decisions need neither tooltip wrappers nor localisation. See
[Decision Reference](decision-reference.md) for the AI-only gate rules, and
[Dynamic Modifier Tooltips](dynamic-modifier-tooltips.md) for dynamic-modifier writes.

## Built-in arrays

Engine-maintained and usable anywhere an array name is accepted, including
`target_array` on decisions. Read-only game variables are listed in
`resources/documentation/dynamic_variables_documentation.md`.

- Global: `global.countries` (includes non-existing dynamic tags), `global.majors`,
  `global.states`, `global.ideology_groups`, `global.operations`, `global.technology`,
  `global.province_controllers`.
- Country: `allies` (faction members, subjects, and overlord), `faction_members`,
  `subjects`, `occupied_countries`, `enemies`, `potential_and_current_enemies` (enemies,
  their allies, and countries with wargoals), `enemies_of_allies`, `neighbors` (by
  controlled provinces), `neighbors_owned` (by owned states), `owned_states`,
  `controlled_states`, `owned_controlled_states`, `core_states`, `army_leaders`,
  `navy_leaders`, `operatives`, `researched_techs`, `exiles`.
- State: `core_countries`.

Prefer a narrow array over `global.countries` plus a filter, which walks every country:

```
target_array = subjects
target_trigger = {
    FROM = { influence_higher_5 = yes }
}
```

## Collections and constants

```
collection_size = {
    input = {
        input = game:scope
        operators = { faction_members owned_states }
    }
    value > 42
}
```

Inputs: `game:all_countries`, `game:all_possible_countries`, `game:all_states`,
`game:scope`, `collection:NAME`, `constant:NAME`. Operators: `faction_members`,
`owned_states`, `controlled_states`, `country_and_all_subjects`, and
`trigger = { ... }` inside `limit`. See `script_collection_input.md` and
`script_collection_operator.md`.

Script constants (`constant:numeric_constants.pi`) are reusable across files, unlike
file-local `@` macros. See `script_concept_documentation.md`.

## Formatted localisation

```
custom_effect_tooltip = MY_TOOLTIP
custom_effect_tooltip = idea_desc|canadian_pacific_railway
custom_effect_tooltip = {
    localization_key = MY_TOOLTIP
    PARAM_NAME = OTHER_LOC_KEY
}
```

Formatters: `idea_desc`, `idea_name`, `tech_effect`, `advisor_desc`,
`country_leader_desc`, `character_name`, `country_culture`, `building_state_modifier`.
See `loc_formatter_documentation.md`.

Loc strings read scope objects as `[ROOT.GetName]` or `[ROOT.Capital.GetName]`.
Promotions: `Owner`, `Capital`, `OriginalCapital`, `Overlord`, `FactionLeader`,
`Controller`, `Occupied`. See `loc_objects_documentation.md`.
