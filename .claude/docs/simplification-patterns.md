# Simplification Patterns

Use a pattern only when it preserves behavior and makes the code easier to read. A
helper or lookup table must remove meaningful duplication, not just a few lines. Check
scope, evaluation order, side effects, and tooltips before calling a rewrite safe.

## Local simplifications

- Trigger contexts already AND their children. Drop a redundant `AND` wrapper.
- An AI modifier whose `OR` covers every value of a condition is unconditional. Remove
  it and fold its weight into `base` where equivalent.
- Use `if`/`else` for complementary branches. Two `if` blocks can both run when the
  first changes state the second reads. A two-state toggle is `if`/`else`, not
  `if`/`else_if`.
- Prefer flat checks that express the same relationship: `TAG = { exists = yes }` is
  `country_exists = TAG`, and `TAG = { has_war_with = ROOT }` is `has_war_with = TAG`
  from ROOT. Verify direction: `TAG = { is_puppet = yes }` checks TAG's status, while
  `is_puppet_of = TAG` checks the current country's relationship to TAG.
- Merge consecutive scope blocks on the same tag. Each `TAG = { }` adds a tooltip
  header. Do not merge across an `if`/`else` or between `effect_tooltip` and
  `hidden_effect`.
- Collapse consecutive `else_if` branches with identical bodies into one branch with an
  `OR` limit, or a bare `else` when the chain is exhaustive. Not when the branches
  scope to different targets or set variables the next branch reads.
- Multiply by a reciprocal instead of dividing by a constant:
  `multiply_variable = { var = x value = 0.01 }`. No divide-by-zero risk.
- A two-bucket `random_list` with one empty bucket is `random = { chance = N ... }`.
  `N` is the weight of the non-empty bucket.

## Array lookup tables

For N parallel values indexed by a small integer, use one array instead of N variables
and N branches.

```
set_variable = { global.build_cost_array^1 = 12 }
set_variable = { global.build_cost_array^2 = 12.50 }

set_temp_variable = { idx = type }
set_variable = { cost = global.build_cost_array^idx }
```

Arrays are zero-indexed. Reserve `^0` as a safe default so an uninitialized index reads
a known value.

## Parameterized scripted localisation

`defined_text` has no parameters. Collapse N near-identical blocks into one that reads a
temp variable the caller sets first.

```
set_temp_variable = { selected_slot_type = slot_type_array^slot }

defined_text = {
    name = my_feature_get_slot_type
    text = { trigger = { check_variable = { selected_slot_type = 1 } } localization_key = type_one_loc }
    text = { trigger = { check_variable = { selected_slot_type = 2 } } localization_key = type_two_loc }
}
```

Every reachable input needs a matching `text` or a final catch-all with no `trigger`. A
`defined_text` with no match renders blank.

## Shared tail helpers

When several effects end with the same block, extract it and pass the difference in a
temp variable:

```
set_temp_variable = { AI_score_type = 1 }
AI_record_score = yes
```

## Government-match enumerations

An `OR` of `AND`s comparing the current government to one other country, one ideology at
a time, is the engine-native comparison:

```
has_government = FROM            # same government
NOT = { has_government = FROM }  # different government
```

Collapse only when all five groups are enumerated. A partial set means something
different for the omitted groups. `validate_simplifications.py` flags the exhaustive
cases.

## `meta_effect` for static identifiers

When N decisions differ only by an index, activate them from one `meta_effect` instead
of N copies. The decisions still exist as separate objects, since decision ids are
static.

```
meta_effect = {
    text = { activate_decision = my_feature_slot_[INDEX]_decision }
    INDEX = "[?slot]"
}
```

## Runtime arrays for per-index state

`meta_effect` is the wrong tool for runtime per-index state, such as flags like
`POTEF_nominee_0..23`. Use one array indexed by the runtime value. The EU subsystem is
the reference implementation.

```
# Store the nominating country's id at the subideology slot. 0 = unset.
set_variable = { global.POTEF_nominee_country^var_gov_index = THIS.id }

NOT = { check_variable = { global.POTEF_nominee_country^var_gov_index value = 0 compare = greater_than } }
```

- A country id in a slot doubles as a set marker. Live country ids are above 0, and an
  uninitialized slot reads 0.
- Set and clear must be symmetric. Every flag or slot that gates a cycle (an election, a
  vote) needs an init at startup, a write, and a clear that is reached when the cycle
  ends. A slot that is never cleared locks the next cycle out.
- Decide whether an array is cycle state (reset each cycle) or a permanent ledger
  (append-only, never cleared, read with `is_in_array`). Say which in a one-line comment
  at its first write. A ledger that is read but never written is permanently false.
- Numeric arrays use `for_each_loop`. Scope arrays use `for_each_scope_loop`.
- Sweep what the migration orphans in the same change: `!_cwtools_dummy_effects.txt`
  stubs and English loc keys. Check for dynamically assembled keys (`tooltip_[token]`)
  before deleting.

## One loop for tooltip and effect

`for_each_scope_loop` takes a `tooltip` parameter. It replaces a `custom_effect_tooltip`,
an `effect_tooltip` copy, and a second loop:

```
for_each_scope_loop = {
    array = global.nato_members
    tooltip = TT_ALL_NATO_MEMBER_NATIONS_GAIN
    if = {
        limit = { NOT = { tag = ROOT } }
        add_opinion_modifier = { target = ROOT modifier = drama }
    }
}
```

Use `ROOT`, not `PREV`, for the acting country. `PREV` shifts when the loop is nested.

## Fold a single-use temp into the effect

A math expression is a valid value for `add_to_variable`, `subtract_from_variable`,
`multiply_variable`, and `divide_variable`, not only `set_variable`:

```
add_to_variable = {
    var = global.cumulative_world_productivity
    value = {
        value = overall_productivity
        multiply = 0.001
        multiply = population_total_m
    }
}
```

- Fold only a temp that is read exactly once.
- An effect-level `if` does not carry over. Inside an expression the `limit` is itself
  an expression: `if = { limit = { value = X equals = 0 } add = 15 }`.
- A malformed expression evaluates to 0 without an error. Verify folds by loading the
  game and reading `error.log`. Fix the first `script_math.cpp` error in a file first.
  The rest are usually cascade.

## Splitting an `every_country` with `OR`

When one loop over `OR = { A B }` becomes two loops, add exclusion limits so a country in
both groups does not receive a non-idempotent effect twice:

```
for_each_scope_loop = {
    array = global.group_A_members
    if = {
        limit = { NOT = { has_idea = group_B } }
        country_event = { id = my_event.1 days = 2 }
    }
}
every_country = {
    limit = { has_idea = group_B }
    country_event = { id = my_event.1 days = 2 }
}
```

## Bloc membership loops

When an `every_country` filters on a membership idea that a maintained array backs,
iterate the array. `check_common_mistakes.py` flags these.

| Idea                              | Array                        |
| --------------------------------- | ---------------------------- |
| `NATO_member`                     | `global.nato_members`        |
| `EU_member`                       | `global.EU_member`           |
| `CSTO_member`                     | `global.CSTO_member`         |
| `AU_member`                       | `global.AU_member`           |
| `LoAS_member` / `LoAS_member_upd` | `global.arab_league_members` |
| `OAU_member`                      | `global.OAU_member`          |
| `ecowas_member_state`             | `global.ECOWAS_member`       |
| `idea_gcc_member_state`           | `global.gcc_member_state`    |
| `faction_warsaw_pact_idea`        | `global.WARSAW_PACT_member`  |
| `RAJ_BRICS_associate`             | `global.BRICS_associates`    |
| `RAJ_BRICS_observer`              | `global.BRICS_observers`     |

- Array names are inconsistently pluralized. Copy the exact spelling.
- Ideas backed by two arrays (`p5_member`, `at_member`, `RAJ_BRICS`) do not convert.
- A LoAS member holds exactly one of the two idea variants, so a loop on
  `has_idea = LoAS_member` alone misses upgraded members. The array covers both.
- Drop the membership condition. `for_each_scope_loop` has no top-level `limit`, so
  residual conditions go in an inner `if`.
- The loop produces no automatic tooltip. In player-facing contexts add
  `tooltip = TT_ALL_*`.
- `every_other_country` needs a `NOT = { tag = ROOT }` guard, since the array includes
  the acting country.
- In triggers use `any_of_scopes` or `all_of_scopes` with `array =`. Annexed tags can
  linger in the arrays, and trigger aggregations do not skip them. Give every
  `all_of_scopes` and negated `any_of_scopes` an `exists = no` escape:

```
all_of_scopes = {
    array = global.nato_members
    OR = {
        has_country_flag = NATO_Ratified_@ROOT
        exists = no
    }
}
```

Do not convert when the idea has no `on_add`/`on_remove` array hooks, when the limit
mixes the idea with other conditions in an `OR`, or when the loop must reach non-members.

## One generic event for an event family

When N events share identical option bodies and differ only in title, description, and
`ai_chance`, collapse them into one event keyed on a type variable.

1. Verify the family: option order and option effect bodies must match. Catalog every
   `ai_chance` difference per type.
2. Keep the lowest event id. Add one triggered `title` and `desc` per type that reuses
   the existing loc keys.
3. Merge `ai_chance`: group each modifier by the set of types that carry it and gate it
   with `check_variable`. Re-expand per type and diff against the originals.
4. Replace the dispatch with one literal `country_event`, then delete the collapsed
   events. Keep their `.t` and `.d` keys.

Triggered titles and `ai_chance` evaluate when the event displays, not when it is
queued. If the event fires with `days = N` and its type lives in a global that is
cleared first, every title trigger fails and the event renders blank. Gate a delayed
event on a per-recipient variable set just before firing and cleared in every option:

```
set_variable = { my_event_type = global.current_type }
country_event = { id = foo.1 days = 1 }
```

Guard the setter with `NOT = { check_variable = { my_event_type > 0 } }` so a second
fire does not relabel an open event. Effects that take only literals (`add_ideas`,
`set_country_flag`, event ids) still need an `if`/`else_if` branch per type.
