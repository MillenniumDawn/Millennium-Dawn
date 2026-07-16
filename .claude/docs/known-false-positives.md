# Known False Positives — Do NOT Flag

These patterns look like bugs but are intentional. All review/fix/simplify agents must skip them.

- **`custom_trigger_tooltip` without `hidden_trigger`**: already suppresses child tooltips. `hidden_trigger` inside it is redundant — do not add it.
- **GRE defer payments dual building call**: Greek focuses with `GRE_defer_payments_flag` intentionally call the building effect BOTH inside an `if` (with `skip_payment = 1`) AND outside it. Not duplication.
- **Building scripted effects without manual treasury charge**: `one_random_*` and `two_random_*` effects charge treasury internally. Adding `treasury_change`/`modify_treasury_effect` would double-charge.
- **`num_of_factories`**: valid HOI4 trigger (total = civilian + military). Not a typo for `num_of_civilian_factories`.
- **`MAX_CIV_FACTORIES_PER_CONTRACT = 1`** and **`EQUIPMENT_MARKET_MAX_CIVS_FOR_PURCHASES_RATIO = 0.05`** in MD defines: intentional AI market caps.
- **`context_type = diplomatic_action`** on scripted_guis: parser warns but works at runtime. Required for diplomatic-action hook.
- **`EH_scenario_enabled = yes`** in raid category `visible` blocks: scope warning is noise, resolves correctly at runtime.
- **Unscoped `FROM` in non-targeted country-scoped decisions**: resolves to ROOT/THIS as fallback. Redundant/misleading, not broken. Cleanup = drop `FROM.` prefix.
- **Bare decision `icon = <name>` (no `GFX_decision_` prefix)**: the decision `icon` field auto-prepends `GFX_decision_`, so `icon = generic_political_discourse` resolves to `GFX_decision_generic_political_discourse` and renders identically. It is the dominant convention. Do not add the prefix. Only flag if neither `GFX_decision_<name>` nor `GFX_<name>` exists in any `interface/*.gfx`. See `decision-reference.md` → Icon Field.
- **`set_leader_<TAG>` scripted effects with no literal caller**: the per-country files `common/scripted_effects/<TAG>_political_leaders.txt` (e.g. `BOS_political_leaders.txt` → `set_leader_BOS`) are dispatched via `meta_effect` in `common/scripted_effects/99_election_effects.txt` (`text = { set_leader_[TAG] = yes }`, `TAG = "[?original_tag.GetTag]"`), so a grep for `set_leader_BOS` finds only the definition, never a call site. They are LIVE, not dead code — the election system invokes `set_leader_<current tag>` for every non-dynamic country. Rule of thumb: any effect whose name is assembled inside a `meta_effect` text block is invisible to name-grep; trace the dispatcher before calling it dead. See `meta-effect-patterns.md`.
