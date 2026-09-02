# File Encoding

All `.txt` script files are **UTF-8 without BOM** — never add `EF BB BF`. Only `.yml` localisation files use UTF-8 **with** BOM.

# HOI4 Scripting — Quick Reference

Full reference (variables, arrays, loops, collections, formatted loc): `.claude/docs/hoi4-data-structures.md`.

## Scopes

`ROOT` = original scope at block start; `FROM` = sender scope (events); `PREV` = previous scope (`PREV.PREV` chains); `OWNER`/`CAPITAL` = owner of current state / capital state of current country. `CONTROLLER` is **state-scope only** — undefined in country scope.

## Variables

- `set_variable` (persistent, on scope) / `set_temp_variable` (current block only) / `set_global_variable` (read via `global.X`)
- Arrays: `my_array^0` literal index, `my_array^i` dynamic; scope with `var:my_var = { ... }` or `var:my_array^i = { ... }` — never `var:v^i` shorthand
- Prefix country-specific variables with the tag (`ISR_operation_success`) — unprefixed names collide when another country sets the same name on a shared scope

## tag vs original_tag

`tag` = current runtime tag (civil-war split-offs become `NIG_CW_0`); `original_tag` never changes. Use `original_tag` in idea/MIO `allowed` blocks and anywhere a game object is restricted to one nation — `tag` there breaks the object for civil-war countries. `tag` is only correct when you mean the current tag literally (e.g. `trigger = { tag = ISR }`).

# Documentation Pointers

- 3D unit models, entities, landmark buildings: `.claude/docs/entity-system.md`
- Power plants / energy techs / renewable balance: `.claude/docs/energy-power-balance.md` (tools: `tools/balance/set_energy_tech_scurves.py`, `tools/analysis/renewable_power_per_cost.py`)
- Simplification & performance catalogs — required reading for hot-path code or copy-paste branching: `.claude/docs/simplification-patterns.md`, `.claude/docs/performance-patterns.md`

# Comments

Default to no comments. Add one only when the WHY is non-obvious: a hidden constraint, a subtle invariant, a deliberate engine-bug workaround, or genuinely surprising behaviour. Never comment WHAT the code does, narrate the change, reference callers, restate an effect name in prose, or justify a mechanic in flavour prose. One terse line max — if a block needs a paragraph, restructure or rename instead. When in doubt, delete the comment. (Python tooling: `tools/COMMENT_STYLE.md`)

# Scripting Patterns

## Don't seed variables to 0

Unset script variables already read as `0`. Never write `set_variable = { X = 0 }` to "initialise" a var — it is redundant. This includes dynamic-modifier vars: `add_dynamic_modifier` with its backing vars unset applies a 0-effect modifier until a focus/decision `add_to_variable`s them, so no zero-seed is needed in history. Only seed a variable when its start value is non-zero.

## Relief effects must move penalty variables the right way

Before writing an effect that "reduces" a penalty backed by a variable, check which direction the backing modifier reads. Cost-shaped keys (`receiving_investment_cost_modifier`, `consumer_goods_factor`, `*_cost_multiplier_modifier`) get _worse_ as the variable rises, so relief subtracts. Bonus-shaped keys (`return_on_investment_modifier`, `production_speed_buildings_factor`, `research_speed_factor`) get worse as it falls, so relief adds. Copying `add_to_variable = { X = 0.02 }` across a whole relief block silently deepens every cost-shaped penalty while the tooltip promises the opposite. Read the `common/dynamic_modifiers/` entry, then match the sign per variable.

## NOT blocks and "NOR"

`NOT = { A B }` means NOT(A AND B) — "not both at once", almost never intended. For "neither" write separate `NOT` blocks or `NOT = { OR = { A B } }`. `NOR` is not a HOI4 trigger keyword. Bare multi-child NOTs are flagged (warning) by `validate_simplifications.py`.

## random over two-bucket random_list

A `random_list` where one bucket is empty is `random = { chance = N }` in the wrong syntax — collapse it. Three+ buckets, or two non-empty buckets, stay `random_list` (edge cases: `.claude/docs/simplification-patterns.md`).

## Tautological OR in ai_will_do modifiers

An `OR` covering every value of a trigger (`is_historical_focus_on = yes` / `= no`) is always true — delete the modifier and fold its `add` into `base`.

## Implicit AND

Children of a trigger context are already AND-ed — never wrap them in `AND = { }`. Applies to `trigger`, `limit`, `visible`, `available`, `activation`, `cancel_trigger`, and every other trigger context.

## Modifier names

Invalid modifier names compile silently and do nothing (the game logs "Unknown modifier" but loads anyway). Never guess — verify first:

```bash
grep -r "modifier_name_here" common/ideas/*.txt common/national_focus/*.txt | head -3
```

No results = wrong name. Copy the exact spelling from an existing use, or check `.claude/docs/md-custom-modifiers.md`.

## Sprite names

Never invent a `GFX_` name. An undefined sprite is a commit-blocking error, not a silent no-op: `validate_events` reports every `picture =` that resolves to nothing as `missing-event-picture`, and MD must not fall back on vanilla event pictures. Verify before writing the reference:

```bash
grep -rn 'name = "GFX_the_name"' interface/
```

No results = the sprite does not exist. Pick an existing one (event pictures: `interface/MD_eventpictures.gfx`) or add a `spriteType` whose `texturefile` points at a texture that is actually on disk.

## Ruling-party gating

There is no `has_idea = democratic_*`. The democratic subideologies are `conservatism`, `liberalism`, `socialism`, and `Western_Autocracy` (`common/ideologies/00_ideologies.txt`); gate on the ruling party with the matching scripted trigger — `western_conservatism_are_in_power`, `western_liberals_are_in_power`, `western_social_democrats_are_in_power`, `western_autocrats_are_in_power`. List the full set for any ideology:

```bash
grep -rhoE '^[a-z_]+_are_in_power = \{' common/scripted_triggers/
```

## threat scale

`threat` is a decimal 0.0–1.0, never a percentage: `threat > 0.40`, not `threat > 40` (always false).

## check_variable comparisons

Inline accepts only `=`, `>`, `<`; `>=`/`<=` parse silently and never match. Use `compare = greater_than_or_equals` (valid: `equals`, `greater_than`, `less_than`, `greater_than_or_equals`, `less_than_or_equals`, `not_equals`).

## Math expressions parse to 0 on failure

Inside a math expression (`set_variable = { X = { value = ... } }`) a malformed statement evaluates to `0.0` and the game plays on with a dead mechanic. It only shows up as `script_math.cpp: Errors occurred while reading math expression defaulting to 0` in `error.log`, and one failure desyncs the parser for the rest of the file. `check_variable`'s comparator list does **not** carry over: inside an expression's `if`/`limit` only `greater_than` and `less_than` are safe (`equals` broke the counter-terror attack roll). Keep branches at effect level with `check_variable`, and grep MD plus vanilla for precedent before using an unfamiliar construct. Details: `.claude/docs/hoi4-data-structures.md` (Math Expressions).

## Variable and array operations do not auto-tooltip

`check_variable`, `is_in_array`, `set/add_to/subtract_from/multiply/divide/clamp_variable`, `add_to/remove_from_array` produce no tooltip — bare in `available`/`visible` the player sees nothing (triggers) or a blank line (effects). Wrap triggers in `custom_trigger_tooltip = { tooltip = key ... }` and effects with `custom_effect_tooltip`. Named scripted triggers DO auto-tooltip via their name's loc key — prefer them over raw variable checks in player-facing blocks. Bare `check_variable` in an `available` block is caught (error) by `validate_variables.py`; `visible` is exempt, since a failing `visible` hides the object outright and renders no tooltip either way.

## Faction triggers

`is_in_faction` is boolean-only (`yes`/`no`); membership with a country is `is_in_faction_with = TAG` — `is_in_faction = TAG` silently fails (caught by `check_common_mistakes.py`). `add_to_faction = TAG` adds a country to the current scope's faction; it never takes a faction name (`add_to_faction = BRICS` is wrong).

## Minimize scope expansion

Don't open a scope to check one trigger when a flat form exists — every `TAG = { ... }` is a scope switch:

| Verbose (scope expansion)       | Flat equivalent        |
| ------------------------------- | ---------------------- |
| `TAG = { exists = yes }`        | `country_exists = TAG` |
| `TAG = { is_puppet = yes }`     | `is_puppet_of = TAG`   |
| `TAG = { has_war_with = ROOT }` | `has_war_with = TAG`   |

## Never cache a boolean into a daily flag to feed the AI

Do not add an `on_daily_TAG` block that set/clears flags whose only readers are `ai_strategy` `enable` blocks or focus `ai_will_do` modifiers. Both are already evaluated lazily by the engine; a daily pass makes the check *more* expensive, not less, and lags real game state by up to a day. Write the condition inline in `enable`, the way `ALG_cancel_war_neighbours` and `BRA_cancel_war_URG` do.

`.claude/docs/performance-patterns.md` has two adjacent sections that are easy to confuse. *Cache `ai_strategy` enable Math Into a Daily Variable* covers **arithmetic chains only** (`set_temp_variable` / `multiply_temp_variable` / …). For a boolean condition the next section applies: *Prefer a Live Trigger Over a Daily-Refreshed Cached Flag*.

`on_daily_BOS` in `common/on_actions/MD_event_on_actions.txt` is a surviving example of the wrong shape. Do not copy it.

## Don't re-add per-tag war brakes

`MD_avoid_new_wars_when_outmatched` in `common/ai_strategy/MD_war_declaration_ai.txt` already brakes every country at `enemies_strength_ratio > 0.75`. A per-tag `avoid_starting_wars` on a stricter ratio is a strict subset of it and can never fire on a tick it does not already own — dead code. A per-tag brake earns its place only on a gate the strength ratio cannot express. Read `.claude/docs/ai-strategy-reference.md` before editing `common/ai_strategy/`, including when you wrote the section yourself.

## send_equipment for country-to-country transfers

Moving equipment from one country's stockpile to another is one effect, not two:

```
# Good
send_equipment = { type = infantry_weapons_type amount = 2000 target = UKR }

# Avoid — two effects, two amounts to keep in sync, and the donor can be driven negative
add_equipment_to_stockpile = { type = infantry_weapons_type amount = -2000 }
UKR = { add_equipment_to_stockpile = { type = infantry_weapons_type amount = 2000 producer = PREV } }
```

`send_equipment` transfers what the sender actually holds and carries the real producer with it, so no `producer =` override is needed. Keep `add_equipment_to_stockpile` only where nothing is being transferred: equipment bought with money, or a delivery that changes type or variant (donor gives generic airframes, recipient receives a named model).

## Case sensitivity in references

HOI4 on Linux is case-sensitive for every identifier — ideas, events, decisions, focuses, variables, flags, sprites, scripted effects/triggers. `has_idea = The_Military` will not match `the_military`; copy the definition's exact case (`validate_ideas.py` catches ideas). Namelists: `division_types` must match `common/units/MD_land_units.txt` and `ship_types` must match `common/units/MD_naval_units.txt` exactly — wrong case or removed vanilla tokens are silently dead (canonical lists: `.claude/docs/namelist-reference.md`).

## Trade agreement checks in MD

`has_trade_agreement_with` is not a valid HOI4 trigger — compiles silently, always false. MD uses `has_country_flag = trade_agreement@TAG`. Caught by `check_common_mistakes.py`.

## Decision allowed vs available

`allowed` in decisions is evaluated **once at game start** and locked. Dynamic conditions (factory counts, opinion, date) go in `available` or `visible`. Caught by `check_common_mistakes.py`.

## Guard gates on optional / elected office holders

Any gate on "the holder of office X" (elected roles, timed ideas, faction leaders) must handle the vacant case: before the first election, or after a timed idea lapses with no re-election, no holder exists and the gate is unsatisfiable — a permanent soft-lock. Always OR in a defined fallback branch with a satisfiable bar, mirror the vacant case in the tooltip, and guard `var:`-stored holder refs with `check_variable = { var:holder > 0 }` before scoping in (uninitialized reads 0). Worked example: `.claude/docs/scripting-edge-cases.md`.

## if/else over if/if

Two consecutive `if` blocks with complementary limits are a double-execution risk — use `if`/`else`.

## change_influence_percentage

Temp-var effect (`percent_change` required; `tag_index` defaults to `ROOT.id`, `influence_target` to `THIS.id`). Three silent-bug traps: redundant default setters, orphan setters with no following `change_influence_percentage = yes`, and loop-local temp vars whose invocation must sit inside the loop. Details: `.claude/docs/scripting-edge-cases.md`.

## Array index semantics

Keep an `^index` variable's meaning consistent: slot position `0..N` (`slot`, `idx`) vs lookup key `1..N` (`type`, `category`) — storing one where the other is expected reads the wrong entry. Table and rule: `.claude/docs/scripting-edge-cases.md`.

# Refactor Breaking-Change Checklist

When renaming prefixes, migrating globals to arrays, or changing signatures: grep the **entire repo** for old names (flags, variables, events, decisions, GUI, GFX), re-verify array-index semantics at every caller, check localisation for `[?global.old_name]` refs (they fail silently to 0), verify event `log =` strings match option `name =` keys after copy/rename, and confirm GUI `window_name`/button/GFX cross-references. Full checklist: `.claude/docs/refactor-checklist.md`.

# Event Patterns

## Cross-country event tooltips

When a reward/option fires an event at another country: follow the fire with `custom_effect_tooltip = TT_IF_THEY_ACCEPT` plus an `effect_tooltip = { ... }` of the acceptance outcome. Add `TT_IF_THEY_REJECT` (+ `effect_tooltip`) only when rejection has real consequences for the sender — never empty reject blocks. Inside the target's option use `TT_IF_WE_ACCEPT` / `TT_IF_WE_DECLINE`. Keys: `localisation/english/MD_tooltips_l_english.yml`; full pattern: `.claude/docs/event-reference.md`.

## Event namespace mismatch

`country_event = { id = foo.1 }` must match the events file's `add_namespace` — a mismatch silently fires nothing. Grep the namespace at the top of the file before wiring callers.

## Log message option IDs

`log =` strings inside an event option must cite the option's own ID (`foo.1.b` in option `.b` — not a copy-pasted `.a`). Log-ID mismatches in focuses, decisions, and event options are caught by `check_common_mistakes.py`; `tools/linting/fix_log_ids.py` auto-fixes them.
