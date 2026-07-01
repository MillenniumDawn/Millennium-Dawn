# MIO Reference

On-demand reference for Military-Industrial Organization structure and examples. For best practices, see CLAUDE.md.

## Example MIO

```
CHI_norinco_manufacturer = {
	allowed = { original_tag = CHI }
	icon = GFX_idea_Norinco_CHI

	task_capacity = 18

	equipment_type = {
		infantry_weapons_type
		artillery_equipment
		mio_cat_all_armor
	}

	research_categories = {
		CAT_infrastructure
		CAT_armor
		CAT_artillery
	}

	initial_trait = {
		name = CHI_norinco_trait
		equipment_bonus = {
			reliability = 0.03
			build_cost_ic = -0.03
		}
	}
}
```

## Key Points

- Name MIOs `TAG_organization_name`
- Always include `allowed = { original_tag = TAG }` to restrict to the correct country
- Set `task_capacity` to 5 × (number of equipment categories covered). Omit when only one category is covered — 5 is the game default
- Equipment types must reference valid `equipment_type` categories
- Trait grid x is bounded `0..9`; y is unlimited. Use `relative_position_id` for branch internals but keep total x-spread inside 0..9
- Children sit exactly one row below their parent (`y = 1` relative); never skip rows or place a child on the parent's row
- Mutually exclusive traits must be on the same row (X)
- A parent's connecting line must reach its child without crossing sibling traits on the same row. If it would cross, reposition the child or nudge with `relative_position_id`.
- Children that should inherit from either of two mutually exclusive parents must use `any_parent` (not `parent`) — otherwise picking the "wrong" parent locks the child out
- Name the initial trait `{org_token}_trait` (e.g. `CHI_norinco_trait`)
- `on_complete` always needs `on_complete = { expenditure_for_mio_upgrade = yes }`, unless you add custom effects (idea switch, give a factory, etc.)
- Localisation goes in the country-specific loc file (`localisation/english/MD_focus_TAG`)
