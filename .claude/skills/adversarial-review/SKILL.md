Run an adversarial edge-case review on the current branch diff or a single file. Actively challenge every change by asking "what could go wrong?" and hunt for unhandled scenarios, silent failures, and logic gaps that rule-based reviews miss.

**Syntax:** `/adversarial-review [file_path]`

- With `file_path`: adversarial review on that file.
- Without argument: adversarial review on all changed files on the current branch vs `main`.

## Role

You are the adversarial reviewer. Don't verify compliance against known rules. Imagine every way the change could break in practice and force the author to defend or fix it.

## Execution

### 1. Gather context

- `git log origin/main..HEAD --oneline`
- `git diff origin/main...HEAD`
- Identify changed files and their types.

### 1a. Dispatch tools-reviewer for any tools/\*\* changes

If `git diff --name-only origin/main...HEAD` includes any path under `tools/` (linting, validation, standardization, shared_utils, etc.), dispatch the `tools-reviewer` subagent in parallel with your own review of content files. Pass it the list of changed tooling files.

The tools-reviewer covers Python-specific concerns (Correctness, Duplication, Performance, Robustness, Consistency, Style, Wiring) that this skill's HOI4-scripting checklists do not. Fold its findings into your final report for a single combined review.

Skip this step when no `tools/**` files changed.

### 2. Challenge every changed block

Ask these questions systematically. If the answer is "no, it's not handled", flag it.

**Existence & Scope Guards**

- Scope into a tag (`TAG = { ... }`): guarded by `country_exists = TAG` or equivalent? Unscoped access to a non-existent country is a silent crash or no-op.
- Variable-stored country reference scoped into (`var:target = { ... }`): is there a `check_variable = { var:target > 0 }` guard first? Uninitialized variables default to 0 or -1.
- `FROM` used as a sender-country reference in a non-targeted decision or focus: there `FROM` falls back to `ROOT`. If the code assumes `FROM` is a different country, it silently targets itself.
- `CONTROLLER` used in country scope: only valid inside a state scope. Undefined in country scope.

**Timing & State Transitions**

- `available = { always = no }` paired with a `bypass`: if the bypass trigger is unreachable (e.g., depends on a skipped event chain), the player is permanently hard-locked. Verify the bypass can actually fire.
- `fire_only_once = yes` combined with `days_remove` on the same decision: the engine handles this inconsistently; one clause usually silently overrides the other.
- Event fired to another country (`country_event = { id = X days = N }`): what if the target no longer exists when the delay expires? What if already at war with ROOT?
- `on_action` events referencing scoped variables from the triggering context: verify the variable is still valid in the event's scope.

**Variable & Array Safety**

- Division by any variable: denominator clamped or guarded `> 0`? Near-zero denominators silently produce extreme values.
- Dynamic array subscript (`array^i`): is `i` bounded? Negative or out-of-range indices silently read garbage or the last element.
- Variable read before write in all paths: any `var:X` consumed before `set_variable` in every execution path.
- `for_each_scope_loop` used on an array of numeric indices: only works on arrays of scope objects (countries, states). Numeric arrays need `for_each_loop`.

**Silent NOPs & Dead Logic**

- `swap_ideas = { remove_idea = X add_idea = X }`: no-op, usually signals the final tier of an upgrade chain still running the swap unnecessarily.
- `clr_country_flag` / `clr_global_flag` on a flag never set: harmless, but signals the author did not trace the flag lifecycle.
- `NOT = { A B }`: means NOT(A AND B), "not both simultaneously". Almost never intended; usually wants two separate `NOT` blocks.
- `else_if` that repeats the exact condition of the parent `if`: unreachable; parent always wins.
- Tautological `OR` inside `ai_will_do` modifiers: `OR = { is_historical_focus_on = yes is_historical_focus_on = no }` is always true, making the modifier unconditional dead weight.

**Cross-Country Mechanics**

- Permanent effects applied directly to another nation (not via event): target player has no agency. Includes `add_timed_idea` to a tag, force-joining factions, etc.
- `will_lead_to_war_with = TAG` without an actual wargoal granted in the same `completion_reward`: the tooltip lies.
- `has_trade_agreement_with = TAG`: **not** a valid HOI4 trigger in MD; compiles silently and always returns false. MD uses `has_country_flag = trade_agreement@TAG`.

**GUI & Script-Glue Edge Cases**

- GUI button with `trigger` but no `effects` block: button renders but clicking does nothing.
- `dirty` variable set to `global.date` or `global.num_days`: forces GUI redraw every tick.
- Scripted GUI `context_type = diplomatic_action`: verify it is wired to a real diplomatic action token; miswired ones silently fail.

**Content Edge Cases**

- Cores added without 80% compliance or an integration system: free cores are banned.
- Buildings added without monetary cost in a focus/decision: use scripted treasury effects.
- Focus rewards granting effects to a country that may not exist by the time the focus completes.

### 3. Output

For each file reviewed, report:

1. **File** — path and type.
2. **Issues** — numbered list with category labels (`[Scope]`, `[Timing]`, `[Variable]`, `[Silent]`, `[Cross-Country]`, `[GUI]`, `[Content]`) and line numbers.
3. **Edge case** — the exact scenario that breaks.
4. **Impact** — what happens to the player or game state when it hits.
5. **Suggested defense** — guard, rewrite, or note if the omission is intentional.

Mark anything that could corrupt save state, soft-lock the player, or crash the GUI as **[critical]**.

End with total count or "No adversarial issues found — the author handled all edge cases."
