# Idea Reference

On-demand reference for idea structure and examples. For best practices, see AGENTS.md.

## Example Idea

```
BRA_idea_higher_minimum_wage_1 = {
 name = BRA_idea_higher_minimum_wage
 allowed_civil_war = { always = yes }

 picture = gold

 modifier = {
  political_power_factor = 0.1
  stability_factor = 0.05
  consumer_goods_factor = 0.075
  population_tax_income_multiplier_modifier = 0.05
 }
}
```

## Key Points

- Always include `picture = sprite_name` — without it the idea shows a blank icon in-game. Find an existing sprite by searching the codebase: `grep "picture = " common/ideas/*.txt | sed 's/.*picture = //' | sort -u`
- Include `allowed_civil_war = { always = yes }` for civil war tags
- Use `original_tag` not `tag` in `allowed` blocks
- Drop the `allowed` block entirely in a category with no slot (`country`, `hidden_ideas`). Nothing picks from those, so `add_idea` is the only way in and it never consults `allowed` — the gate is dead either way. A category that has a slot draws from a pool `allowed` filters, so keep it there. Flagged by `validate_ideas.py` (`allowed-in-slotless-category`); `tools/standardization/strip_idea_allowed_gates.py` removes them in bulk
- Drop the `available` block entirely in a category with no slot (`country`, `hidden_ideas`). Same reason: nothing picks from those, so `available` is never consulted. Use `cancel` if the idea should remove itself. Flagged by `validate_ideas.py` (`available-in-slotless-category`); the same stripper removes them in bulk
- Keep `allowed = { always = no }` on slotted ideas that must not appear in the picker (religion, other laws). `add_idea` still applies them. Do not use it in slotless categories (`country`, `hidden_ideas`); that gate is dead and the validator flags it
- Remove `cancel = { always = no }` (checked hourly, never true)
- Remove empty `on_add = { log = "" }` unless actually doing something
- Tiered ideas use suffix numbering: `TAG_idea_name_1`, `TAG_idea_name_2`, with shared `name = TAG_idea_name` for display
- `name = X` redirects **both** name and description loc lookups — game reads `X` for the displayed name and `X_desc` for the tooltip body. The idea's own ID is no longer used for loc once `name =` is set.
- Pick a `name = X` value that no focus, decision, or other idea uses. A focus with `id = X` and an idea with `name = X` share the same `X` / `X_desc` loc keys — duplicate definitions in `.yml` resolve to the last one written, silently overwriting the other game object's text. If a tier needs unique flavor while sharing a display name with sibling tiers, give it a distinct `name =` and its own `name_desc` entry rather than reusing the shared key.
