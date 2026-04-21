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

- Name MIOs with `TAG_organization_name` format
- Always include `allowed = { original_tag = TAG }` to restrict to the correct country
- Set `task_capacity` to 5 × (number of equipment categories covered). Omit the field when only one category is covered — 5 is the game default
- Equipment types must reference valid `equipment_type` categories
- Trait grid x is bounded `0..9`; y is unlimited. Use `relative_position_id` for branch internals but keep the total x-spread inside 0..9
- Children are always placed exactly one row below their parent (`y = 1` relative); never skip rows or place a child on the same row as its parent
- Mutually Exclusive needs to be on the same row (X)
- Parent line's are not allowed to cross traits. The parent needs to have a direct line towards the child
- When using mutually exclusive traits, make sure childs under it use any_parent if there is a joint trait of both traits
- Name the initial trait `{org_token}_trait` (e.g. `CHI_norinco_trait`)
- On complete always needs to be this line, unless you add custom effects (like idea switch, give a facotory, etc.): on_complete = { expenditure_for_mio_upgrade = yes }
- Localisation needs to be in the countries specific localisation file (localisation/english/MD_focus_TAG)
