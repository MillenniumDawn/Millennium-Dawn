# Bug Patterns

Deduplicated catalog of known MD/HOI4 bug patterns. Two sections: **Scan patterns** are greppable signatures for codebase sweeps (`/fix-issue` idle scans); **Adversarial questions** are what-could-go-wrong checks for reviewing a diff (`/adversarial-review`, `/audit`). Reviewers apply both sections.

Plus every pattern in `.claude/rules/general-rules.md` § Scripting Patterns — always loaded, not repeated here.

## Scan patterns

- `swap_ideas` where `remove_idea` and `add_idea` are the same (no-op — usually the final tier of an upgrade chain still running the swap), or `remove_idea` doesn't match the `limit` condition
- Event options with `name =` referencing a different event's ID, or duplicate option names within one event (copy-paste errors)
- `give_resource_rights` / `transfer_state` targeting wrong state IDs
- Variables accumulated monthly without being reset first
- Events sending responses to the wrong country (wrong FROM/PREV/ROOT scope)
- `else_if` with the same `limit` as the preceding `if` (unreachable — lives in the `if`'s shadow)
- `tag` instead of `original_tag` in idea `allowed` blocks (breaks civil war tags)
- `set_cosmetic_tag = original_tag` (should be `drop_cosmetic_tag = yes`)
- Missing `country_exists` guard before firing an event to a potentially non-existent tag
- `AND` of conditions that can never be simultaneously true (e.g. `exists = no` + `is_in_faction_with = X`) in `cancel` or `available` — rethink as `OR` or fix the logic
- `for_each_scope_loop` iterating a numeric-index array (only works on scope objects; use `for_each_loop`)
- GUI buttons with a `trigger` block but no `effects` block (button renders, clicking does nothing)
- OOB templates using equipment variants the country cannot have at game start (wrong tech level or missing DLC variant)
- Wrong capitalisation in `has_idea` / `add_ideas` / `remove_ideas` — case-sensitive, fails silently
- `not_locked_faction` trigger in faction rules (non-existent; use `is_locked_faction = no`)
- Stacked multipliers producing near-zero denominators (clamp before division)
- `add_building_construction` for `naval_base` missing `province`
- Scripted trigger defined twice in the same file (second definition silently overwrites the first)
- New subideology parties missing registration in `common/scripted_localisation/00_MD_politicsview_scripted_localisation.txt`

## Adversarial questions

Ask these systematically against every changed block. If the answer is "no, it's not handled", flag it.

**Existence & Scope Guards**

- Scope into a tag (`TAG = { ... }`) or grant focus rewards to another country: guarded by `country_exists` or equivalent? The target may be dead by the time the effect runs.
- Variable-stored country reference scoped into (`var:target = { ... }`): is there a `check_variable = { var:target > 0 }` guard first? Uninitialized variables default to 0 or -1.
- `FROM` used as a sender-country reference in a non-targeted decision or focus: there `FROM` falls back to `ROOT`. If the code assumes `FROM` is a different country, it silently targets itself.

**Timing & State Transitions**

- `available = { always = no }` paired with a `bypass`: if the bypass trigger is unreachable (e.g., depends on a skipped event chain), the player is permanently hard-locked. Verify the bypass can actually fire.
- `fire_only_once = yes` combined with `days_remove` on the same decision: the engine handles this inconsistently; one clause usually silently overrides the other.
- Event fired to another country (`country_event = { id = X days = N }`): what if the target no longer exists when the delay expires? What if already at war with ROOT?
- `on_action` events referencing scoped variables from the triggering context: verify the variable is still valid in the event's scope.
- Event option firing its own event ID: infinite loop.
- `days_remove` without a paired `remove_effect`: the idea/modifier lapses on the timer but its effect never reverses.

**Variable & Array Safety**

- Division by any variable: denominator clamped or guarded `> 0`? Near-zero denominators silently produce extreme values.
- Dynamic array subscript (`array^i`): is `i` bounded? Negative or out-of-range indices silently read garbage or the last element.
- Variable read before write in all paths: any `var:X` consumed before `set_variable` in every execution path.
- `add_stability` / `add_war_support` given a value outside `-1.0`..`1.0`: silently clamped (a `5` means `1.0`), usually a mistake.

**Silent NOPs & Dead Logic**

- `clr_country_flag` / `clr_global_flag` on a flag never set: harmless, but signals the author did not trace the flag lifecycle.
- `random_list` with all weights 0, or every `ai_chance` at `base = 0`: nothing is ever selected.

**Cross-Country Mechanics**

- Permanent effects applied directly to another nation (not via event): target player has no agency. Includes `add_timed_idea` to a tag, force-joining factions, etc.
- `will_lead_to_war_with = TAG` without an actual wargoal granted in the same `completion_reward`: the tooltip lies.

**GUI & Script-Glue Edge Cases**

- `dirty` variable set to `global.date` or `global.num_days`: forces GUI redraw every tick.
- Scripted GUI `context_type = diplomatic_action`: verify it is wired to a real diplomatic action token; miswired ones silently fail.

**Content Edge Cases**

- Cores added without 80% compliance or an integration system: free cores are banned.
- Buildings added without monetary cost in a focus/decision: use scripted treasury effects.
