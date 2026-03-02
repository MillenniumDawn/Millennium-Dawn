Review all changes on the current branch compared to main. Report issues across coding standards, performance, logic, and localisation.

Steps:
1. Get context and the full diff:
   ```
   git log main..HEAD --oneline
   git diff main...HEAD
   ```

2. Review every changed file for the following issues:

---

**Coding Standards**
- Focus property order violated: id → icon → x/y → relative_position_id → cost → allow_branch → prerequisite/mutually_exclusive → search_filters → available/bypass/cancel → will_lead_to_war_with → select_effect/completion_reward/bypass_effect → ai_will_do
- Missing `log =` in focus completion_reward, select_effect, bypass_effect, decision complete_effect, or event options that have effects
- Missing `search_filters` on a focus
- Missing `ai_will_do` on a focus or decision
- Missing `is_triggered_only = yes` on an event
- `allowed = { always = no }` or `cancel = { always = no }` in an idea (remove — these are defaults and hurt performance)
- Empty `on_add = { log = "" }` blocks in an idea
- Empty `available = { }` or `mutually_exclusive = { }` blocks
- Default values that should be omitted: `cancel_if_invalid = yes`, `continue_if_invalid = no`, `available_if_capitulated = no`
- Division used instead of multiplication (`/ 100` → `* 0.01`)
- Tabs replaced with spaces
- MIO missing `allowed = { original_tag = TAG }` restriction
- MIO `equipment_type` referencing a category that doesn't exist in the equipment system
- MIO trait at `y` coordinate outside the 0–9 range

---

**Performance**
- `every_country`, `any_country`, or `random_country` used instead of a specific array — iterates all 200+ countries each evaluation
- `every_state` or `any_state` without a narrow `limit` — iterates all 800+ states
- Complex triggers or scope changes inside a `visible` block on a decision — `visible` is evaluated every frame on hover; it must be cheap
- An event without `is_triggered_only = yes` — MTTH events fire continuously and create constant overhead
- `force_update_dynamic_modifier` — forces a full modifier recalculation; use sparingly
- Global on_actions (`on_daily`, `on_weekly`) used instead of tag-specific `on_daily_TAG` — global hooks run for every country
- `check_variable` or `has_variable` inside a frequently-evaluated `trigger` block without a simple early-exit guard
- `count_triggers` used inside a loop scope — expensive nested evaluation

---

**Logic & Correctness**
- Scoping into a country tag without a `country_exists` guard in `available` or `visible`
- `clr_country_flag` / `clr_global_flag` on a flag never set in the diff
- `fire_only_once = yes` combined with `days_remove` (contradictory — fire_only_once fires once, days_remove implies repeated use)
- `days_remove` without a `remove_effect` block
- Missing `limit` inside broad `every_*` or `random_*` loops
- `random_list` where all entries have weight 0 (nothing can be selected)
- All `ai_chance` blocks in an event set to `base = 0` (AI has no valid choice)
- An event option that fires the same event ID back (potential infinite loop)
- `add_stability` or `add_war_support` with a value outside the -1.0 to 1.0 range (values beyond ±1 are clamped or invalid)
- `will_lead_to_war_with` used without the focus granting an actual wargoal in completion_reward
- A war goal or annex effect added without checking the target country exists and is not already at war with the scoped country
- Merge conflict markers left in (`<<<<<<<`, `=======`, `>>>>>>>`)

---

**Localisation**
- New focus, event, decision, idea, or MIO added without matching localisation keys
- New event missing `.t`, `.d`, or option name keys
- Localisation keys with leftover `:0` or `:1` version suffixes (correct form: `key: "value"`)
- Subideology entries missing `_icon` or `_desc` keys
- Subideology `_desc` key missing the `\n\n` separator between the header and body paragraph
- Localisation strings that are empty or contain placeholder text like `"TODO"`

---

3. Output: list issues per file with line number where visible. Flag anything that could cause a crash or broken game state as **critical**. End with a total count, or "No issues found" if clean.
