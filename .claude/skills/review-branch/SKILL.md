Review all changes on the current branch compared to main. Report issues across coding standards, performance, logic, and localisation.

Steps:

1. Get context and the full diff:

   ```
   git log origin/main..HEAD --oneline
   git diff origin/main...HEAD
   ```

2. Review every changed file against the rules in CLAUDE.md, `.claude/rules/localisation-rules.md`, and `.claude/docs/hoi4-data-structures.md`. Reference `docs/src/content/resources/code-resource.md` for MD-specific modifiers, scripted effects (building effects, treasury, debt, influence, political, energy), and building costs. Check for issues in five categories:

**Coding Standards** — apply all rules from CLAUDE.md. Watch especially for these commonly missed or silently broken patterns:

- Misspelled or wrong-case IDs in `has_idea`/`add_ideas`/`remove_ideas`/`has_completed_focus` — HOI4 checks are **case-sensitive** and fail silently with no error
- `ai_will_do = { factor = N }` at root — use `base = N`; `factor` at root is deprecated
- `set_cosmetic_tag = original_tag` — `original_tag` is a keyword; use `drop_cosmetic_tag = yes`
- `OR = { }` wrapping only a single condition — remove the wrapper
- Redundant `ROOT = { }` inside `completion_reward`/`complete_effect` — already ROOT scope
- `add_building_construction` for `naval_base` without `province = XXXXX` — silently misplaces the base
- GUI button with `trigger` but no `effects` block — clicking does nothing
- N separate `foo_0..foo_N` scripted effects — flag for refactor to parameterized helper + array

**Performance** — apply Performance Tips from CLAUDE.md. Watch especially for:

- `every_country`/`any_country`/`random_country` without an array — 200+ evaluations per tick
- `every_state`/`any_state` without a narrow `limit` — 800+ evaluations
- Complex triggers in decision `visible` blocks — evaluated every frame
- GUI `dirty` variable set to `global.date` or `global.num_days` — GUI redraws every tick; use a purpose-built counter incremented only on relevant state changes

**Logic & Correctness** — bugs and broken game state risks:

- Scoping into a tag without `country_exists` guard
- `clr_country_flag`/`clr_global_flag` on a flag never set
- `fire_only_once = yes` + `days_remove` (contradictory)
- `days_remove` without `remove_effect`; broad loops without `limit`
- `random_list` with all weights 0; all `ai_chance` at `base = 0`
- Event option firing the same event ID (infinite loop)
- `add_stability`/`add_war_support` outside -1.0 to 1.0
- `will_lead_to_war_with` without a wargoal in `completion_reward`
- War goal or annex without checking target exists / not already at war
- Merge conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
- **[critical]** `available = { always = no }` on a focus that also has a `bypass` — if the bypass condition never fires (e.g., due to event chain timing), the player is permanently hard-locked. `available` must match or approximate the `bypass` condition.
- Two consecutive `if = { limit = { X } }` / `if = { limit = { NOT = { X } } }` blocks — use `if/else` instead. The `if/if` pattern can produce double-execution if the engine evaluates both, and signals the author didn't know about `else`.
- Two consecutive `if` blocks with **identical** conditions — the second is dead code; remove it.
- Event option `log =` key not matching the option's own `name` key — copy-paste from option A into option B while leaving `.a` in the log string produces misleading game logs. Verify each option's log suffix matches its `name` suffix.
- `CONTROLLER` used in country scope — `CONTROLLER` is only valid inside a state scope. In country scope, first scope into the state (`var:state_var = { ... }` or `STATE_ID = { ... }`), then use `CONTROLLER`.
- `tag` instead of `original_tag` in idea `allowed` blocks — during civil wars the split-off country has `original_tag = TAG` but a different runtime tag; `allowed = { tag = TAG }` breaks for those countries. Always use `original_tag`.
- AND conditions that can never both be true simultaneously (e.g., `exists = no` AND `is_in_faction_with = X`) — a country that doesn't exist can't be in a faction. Fix to OR or rethink the logic.
- Variable-stored country reference used without a validity guard — before scoping into a variable holding a country (e.g., `cur_target_nation`), check it is valid: `check_variable = { cur_target_nation > 0 }`. Uninitialized or cleared variables default to 0 (no country) or -1.
- Division by zero risk in calculations — whenever dividing by a variable (e.g., `nuclear_fuel_consumption`, `total_population`), guard that the denominator is `> 0` before the division.
- `for_each_scope_loop` on an array of numeric indices — `for_each_scope_loop` is only for arrays of scope objects (countries, states, characters). For numeric/variable loops use `for_each_loop`; for state-scope iteration inside a country use `every_state` or `for_each_loop` + manual state scoping.
- `NOT = { condition_A condition_B }` — this means NOT(A AND B), i.e. "not both true at once". That is almost never the intended logic. Usually two separate `NOT = { condition_A }` / `NOT = { condition_B }` blocks are needed (meaning neither can be true).
- `threat > 10` / `threat > 40` — `threat` is a decimal 0.0–1.0, not a percentage. Comparisons using whole numbers (>10, >25, >50) are always false. Use `threat > 0.10`, `threat > 0.40`, etc.
- `else_if = { limit = { <same condition as preceding if> } }` — an `else_if` that repeats the parent `if`'s condition is unreachable code; the parent `if` always wins. All sub-logic for a given condition belongs inside the original `if` block.
- No-op `swap_ideas = { remove_idea = X add_idea = X }` — removing and re-adding the same idea is a no-op. This appears when an idea upgrade chain reaches its final tier; the `else` branch should omit the swap entirely.
- Non-existent scripted trigger `not_locked_faction` — the correct trigger is `is_locked_faction = no`.
- GUI `dirty` variable set to `global.date` or `global.num_days` — causes the GUI to redraw every tick. Use a purpose-built counter variable incremented only when relevant game state changes (e.g., `TAG_update_dirty_variable` scripted effect).
- Stacked multiplier overflow — when several negative `*_factor` modifiers are applied to the same variable (e.g., `migration_rate_value_multiplier`), the product can approach zero or go negative, producing division-by-near-zero results. Use `clamp_variable` / `clamp_temp_variable = { var = X min = 0.01 }` before using the variable in a calculation.

**Localisation** — apply all rules from `.claude/rules/localisation-rules.md`. Key structural checks for changed files:

- Every new script object (focus, decision, event, idea, MIO, subideology) has matching loc keys
- Events have `.t`, `.d`, and all option keys (`ID.a`, `ID.b`, …)
- No `:0`/`:1` version suffixes; subideologies have `_icon` and `_desc`; `_desc` contains `\n\n` separator
- No empty `""` or `"TODO"` strings; no undefined `[variable]` substitutions

**Content Design** — issues from `docs/src/content/resources/content-review-guide.md`:

- `add_ai_strategy` used in effects (harmful to AI performance — consult AI team)
- Free cores without a mechanic (require 80% compliance or integration system)
- Permanent effects on another nation not routed through an event (target player needs agency)
- Budget law changes alone as a focus reward (shallow filler — pair with meaningful effects)
- Trade opinion effects without a supplementary effect
- Buildings added without monetary cost (use scripted effects from Code Resource)
- High-cost focuses (cost ≥ 8, or cost ≥ 5 with military/economy/research `search_filters`) missing `NOT = { has_active_mission = bankruptcy_incoming_collapse }` in `available` — blocks AI from queueing expensive focuses during financial collapse

3. Output: list issues per file with line numbers. Flag crash/broken-state risks as **critical**. End with total count or "No issues found".
