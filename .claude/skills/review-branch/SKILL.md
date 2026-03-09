Review all changes on the current branch compared to main. Report issues across coding standards, performance, logic, and localisation.

Steps:

1. Get context and the full diff:

   ```
   git log origin/main..HEAD --oneline
   git diff origin/main...HEAD
   ```

2. Review every changed file against the rules in CLAUDE.md, localisation.md, and hoi4-data-structures.md. Check for issues in four categories:

**Coding Standards** — violations of CLAUDE.md conventions:

- Focus property order, missing `log =`, missing `search_filters`, missing `ai_will_do`
- Missing `is_triggered_only = yes` on events
- Idea anti-patterns: `allowed = { always = no }`, `cancel = { always = no }`, empty `on_add = { log = "" }`
- Empty blocks (`available = { }`, `mutually_exclusive = { }`)
- Default values that should be omitted (`cancel_if_invalid = yes`, `continue_if_invalid = no`, `available_if_capitulated = no`)
- Division instead of multiplication (`/ 100` → `* 0.01`); spaces instead of tabs
- MIO: missing `allowed = { original_tag = TAG }`, invalid `equipment_type`, trait `y` outside 0–9

**Performance** — patterns that cause unnecessary computation:

- `every_country`/`any_country`/`random_country` instead of arrays (200+ countries per eval)
- `every_state`/`any_state` without a narrow `limit` (800+ states)
- Complex triggers in decision `visible` blocks (evaluated every frame)
- Events without `is_triggered_only = yes` (MTTH overhead)
- `force_update_dynamic_modifier`; global on_actions instead of `on_daily_TAG`

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

**Localisation** — missing or malformed loc keys per localisation.md rules:

- New game objects without matching loc keys
- Events missing `.t`, `.d`, or option keys
- `:0`/`:1` version suffixes; missing `_icon`/`_desc` for subideologies
- Subideology `_desc` missing `\n\n` separator
- Empty or `"TODO"` placeholder strings

3. Output: list issues per file with line numbers. Flag crash/broken-state risks as **critical**. End with total count or "No issues found".
