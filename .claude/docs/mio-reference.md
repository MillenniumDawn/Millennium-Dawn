# MIO Reference

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

## Rules

- Name MIOs `TAG_organization_name` and the initial trait `{org_token}_trait`.
- Always include `allowed = { original_tag = TAG }`.
- `task_capacity` defaults to 5 and most MIOs omit it. Set 2 or 3 for niche orgs, about
  10 for major-nation manufacturers, and 18 to 25 for multi-category giants.
- `on_complete = { expenditure_for_mio_upgrade = yes }` on every trait, unless it has
  custom effects.
- Localisation goes in the country's `MD_focus_TAG` loc file.

Trait layout:

- An organic network is the default: branches interleave, split, and reconverge, and
  cross-branch parents are fine. Produce a clean column layout only when asked.
- Trait x must not exceed 9. Negative x is valid. y is not capped. Use
  `relative_position_id` inside a branch.
- A child is never on or above its parent's row.
- Mutually exclusive traits sit side by side on the same row.
- A parent's line must reach its child without crossing a sibling on the same row.
- A child of two mutually exclusive parents uses `any_parent`, not `parent`, or the
  wrong pick locks it out.
- Spread `organization_modifier` and `production_bonus` traits across tree depth.

## Modifier keys

### `organization_modifier`

- `military_industrial_organization_design_team_assign_cost`: cost to assign the MIO in
  a designer.
- `military_industrial_organization_design_team_change_cost`: cost to pull the latest
  changes into an assigned design.
- `military_industrial_organization_funds_gain`: rate funds are gained.
- `military_industrial_organization_industrial_manufacturer_assign_cost`: cost to assign
  the MIO to a production line.
- `military_industrial_organization_research_bonus`: flat addition to the research
  bonus. 0.1 turns 20% into 30%.
- `military_industrial_organization_size_up_requirement`: funds needed per level.
- `military_industrial_organization_task_capacity`: flat extra parallel tasks.

### `production_bonus`

- All equipment: `production_capacity_factor`, `production_cost_factor`,
  `production_resource_need_factor`, `production_resource_penalty_factor`.
- Not ships: `production_conversion_speed_factor`, `production_efficiency_cap_factor`,
  `production_efficiency_gain_factor`. Dockyards have no production efficiency, so these
  do nothing on a naval roster.

### `equipment_bonus`

A bonus is a percentage of the equipment's declared base stat. A key the target never
declares, or declares as 0, does nothing. The lists say which keys the engine accepts,
not which ones bite. Check the archetype in `common/units/equipment/` first.

- `AA_Equipment` declares only `reliability`, `build_cost_ic`, `supply_consumption`,
  `lend_lease_cost`, and `air_attack`.
- `infantry_weapons_type` declares `ap_attack = 0` and `armor_value = 0`.
- `max_organisation` bites only on `cnc_equipment_type`, `convoy`, and ship hulls.
- When a stat bites on part of the roster, narrow the trait with
  `limit_to_equipment_type` or pick a stat every member declares. The limit also
  restricts the trait's `production_bonus`.

Keys:

- All: `build_cost_ic`, `reliability`.
- Air and missiles: `air_agility`, `air_attack`, `strategic_attack`, `air_defence`,
  `air_ground_attack`, `air_range`, `air_superiority`, `naval_strike_attack`,
  `naval_strike_targetting`, `night_penalty`, `thrust`.
- Naval: `anti_air_attack`, `armor_value`, `carrier_size`, `hg_armor_piercing`,
  `hg_attack`, `lg_armor_piercing`, `lg_attack`, `max_strength`,
  `naval_heavy_gun_hit_chance_factor`, `naval_light_gun_hit_chance_factor`,
  `naval_range`, `naval_speed`, `naval_supremacy_factor`,
  `naval_torpedo_damage_reduction_factor`,
  `naval_torpedo_enemy_critical_chance_factor`, `naval_torpedo_hit_chance_factor`,
  `sub_attack`, `sub_visibility`, `surface_visibility`, `torpedo_attack`.
- Land material, armor, and helicopters: `ap_attack`, `breakthrough`, `defense`,
  `hard_attack`, `soft_attack`. Armor and helicopters also take `armor_value`. Armor
  takes `hardness`.
- Mixed: `maximum_speed` (land and air), `mines_planting` and `mines_sweeping` (air and
  naval), `sub_detection` and `surface_detection` (carrier air and naval), `weight` (air
  and armor), `fuel_consumption` (everything but material).
