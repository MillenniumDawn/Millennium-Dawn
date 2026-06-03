# MIO Modifiers Reference

Valid modifier keys per block type for Military-Industrial Organizations. Use to verify which keys are legal for a given equipment category.

## Organisation modifiers

Used inside `organization_modifier = { ... }` blocks.

| Key                                                                    | Description                                                                                                                      | Example                                                                       |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `military_industrial_organization_design_team_assign_cost`             | Cost to assign an MIO in the Tank/Aircraft/Ship designer.                                                                        | `military_industrial_organization_design_team_assign_cost = -0.2`             |
| `military_industrial_organization_design_team_change_cost`             | Cost to pull the latest changes from an already-assigned MIO for a given Tank/Aircraft/Ship design.                              | `military_industrial_organization_design_team_change_cost = -0.1`             |
| `military_industrial_organization_funds_gain`                          | Rate at which funds are obtained (funds level the MIO and unlock traits). Another lever for the levelling rate.                  | `military_industrial_organization_funds_gain = 0.2`                           |
| `military_industrial_organization_industrial_manufacturer_assign_cost` | Cost to assign a MIO to an industrial (non-designer) production line.                                                            | `military_industrial_organization_industrial_manufacturer_assign_cost = -0.2` |
| `military_industrial_organization_research_bonus`                      | Flat increase to the research bonus percentage the MIO applies. If it gave 20% and receives "0.1" here, it then gives 30%.       | `military_industrial_organization_research_bonus = 0.1`                       |
| `military_industrial_organization_size_up_requirement`                 | Modifies funds needed to level up, accelerating trait unlocks. Use when designing an MIO with an above-average number of traits. | `military_industrial_organization_size_up_requirement = -0.1`                 |
| `military_industrial_organization_task_capacity`                       | Flat increase to the number of tasks an MIO can be assigned in parallel.                                                         | `military_industrial_organization_task_capacity = 5`                          |

## Production modifiers

Used inside `production_bonus = { ... }` blocks.

| Key                                  | Equipment types | Description                                                                      | Example                                     |
| ------------------------------------ | --------------- | -------------------------------------------------------------------------------- | ------------------------------------------- |
| `production_capacity_factor`         | All             | Increases production output (items produced per day).                            | `production_capacity_factor = 0.1`          |
| `production_conversion_speed_factor` | non-naval       | Speed at which equipment conversions are performed.                              | `production_conversion_speed_factor = 0.5`  |
| `production_cost_factor`             | All             | Reduces production cost.                                                         | `production_cost_factor = 0.05`             |
| `production_efficiency_cap_factor`   | non-naval       | Increase max production efficiency. Ships have no production efficiency cap.     | `production_efficiency_cap_factor = 0.2`    |
| `production_efficiency_gain_factor`  | non-naval       | Increase the rate efficiency increases. Ships have no production efficiency cap. | `production_efficiency_gain_factor = 0.24`  |
| `production_resource_need_factor`    | All             | Change raw resources needed (Iron, Tungsten, Chromium, etc.).                    | `production_resource_need_factor = -0.1`    |
| `production_resource_penalty_factor` | All             | Modify the penalty from not having enough resources.                             | `production_resource_penalty_factor = -0.1` |

## Equipment modifiers

Used inside `equipment_bonus = { ... }` blocks.

### All equipment

| Key                |
| ------------------ |
| `build_cost_ic`    |
| `reliability`      |
| `max_organisation` |

### Air and Missiles

| Key                       |
| ------------------------- | --- |
| `air_agility`             |
| `air_attack`              |
| `strategic_attack`        |
| `air_defence`             |
| `air_ground_attack`       |
| `air_range`               |
| `air_superiority`         | Air |
| `naval_strike_attack`     |
| `naval_strike_targetting` |
| `night_penalty`           | Air |
| `thrust`                  | Air |

### Naval

| Key                                          |
| -------------------------------------------- |
| `anti_air_attack`                            |
| `armor_value`                                |
| `carrier_size`                               |
| `hg_armor_piercing`                          |
| `hg_attack`                                  |
| `lg_armor_piercing`                          |
| `lg_attack`                                  |
| `max_strength`                               |
| `naval_heavy_gun_hit_chance_factor`          |
| `naval_light_gun_hit_chance_factor`          |
| `naval_range`                                |
| `naval_speed`                                |
| `naval_supremacy_factor`                     |
| `naval_torpedo_damage_reduction_factor`      |
| `naval_torpedo_enemy_critical_chance_factor` |
| `naval_torpedo_hit_chance_factor`            |
| `sub_attack`                                 |
| `sub_visibility`                             |
| `surface_visibility`                         |
| `torpedo_attack`                             |

### Land (Material / Armor / Helicopter)

| Key            | Notes                     |
| -------------- | ------------------------- |
| `ap_attack`    | Material/Armor/Helicopter |
| `armor_value`  | Armor/Helicopter only     |
| `breakthrough` | Material/Armor/Helicopter |
| `defense`      | Material/Armor/Helicopter |
| `hard_attack`  | Material/Armor/Helicopter |
| `soft_attack`  | Material/Armor/Helicopter |
| `hardness`     | Armor                     |

### Mixed / multi-category

| Key                 | Equipment types               |
| ------------------- | ----------------------------- |
| `maximum_speed`     | Material/Armor/Helicopter/Air |
| `mines_planting`    | Air/Naval                     |
| `mines_sweeping`    | Air/Naval                     |
| `sub_detection`     | CV Air/Naval                  |
| `surface_detection` | CV Air/Naval                  |
| `weight`            | Air/Armor                     |
| `fuel_consumption`  | non-material                  |
