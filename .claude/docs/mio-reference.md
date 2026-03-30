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
		name = CHI_norinco_company_trait
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
- Set `task_capacity` proportional to nation size (typically 10-25)
- Equipment types must reference valid `equipment_type` categories
- Trait grid runs `y = 0` to `y = 9`; use relative positioning for trait layout
- Add `initial_trait` for the organization's defining bonus
