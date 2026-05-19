# Idea Reference

On-demand reference for idea structure and examples. For best practices, see CLAUDE.md.

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
- Remove `allowed = { always = no }` (default, hurts performance)
- Remove `cancel = { always = no }` (checked hourly, never true)
- Remove empty `on_add = { log = "" }` unless actually doing something
- Tiered ideas use suffix numbering: `TAG_idea_name_1`, `TAG_idea_name_2`, with shared `name = TAG_idea_name` for display
- `name = X` redirects **both** name and description loc lookups — game reads `X` for the displayed name and `X_desc` for the tooltip body. The idea's own ID is no longer used for loc once `name =` is set.
- Pick a `name = X` value that no focus, decision, or other idea uses. A focus with `id = X` and an idea with `name = X` share the same `X` / `X_desc` loc keys — duplicate definitions in `.yml` resolve to the last one written, silently overwriting the other game object's text. If a tier needs unique flavor while sharing a display name with sibling tiers, give it a distinct `name =` and its own `name_desc` entry rather than reusing the shared key.
