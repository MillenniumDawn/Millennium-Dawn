---
title: Code Resources
description: Millennium Dawn unique modifiers, effects and tutorials for modders
---

This is the hub for Millennium Dawn's unique systems. The custom modifier reference lives here; scripted effects, how-to guides, and the deeper subsystems each have their own page, linked below.

> **Note**: This is not fully up-to-date. For the latest systems, check the codebase directly.

---

# Quick Reference

## Custom Modifier Categories

The full modifier tables are on this page:

- [Economic Modifiers](#economic-modifiers) - Money, taxes, productivity, trade
- [Law Modifiers](#law-modifiers) - Government spending, law costs
- [Migration Modifiers](#migration-modifiers) - Population migration
- [Influence Modifiers](#influence-modifiers) - Foreign influence mechanics
- [Energy Modifiers](#energy-modifiers) - Power generation and consumption
- [Political Modifiers](#political-modifiers) - Party popularity mechanics
- [Counter-Terror Modifiers](#counter-terror-modifiers) - Counter-terrorism
- [Missile & Space Modifiers](#missile--space-modifiers) - Missile/satellite production
- [Nation-Specific Modifiers](#nation-specific-modifiers) - Country unique modifiers

## Scripted Effects

Effect snippets (treasury, debt, buildings, factions, influence, party management) live in the [Scripted Effects Reference](/dev-resources/scripted-effects-reference/):

- [Building Effects](/dev-resources/scripted-effects-reference/#building-effects) - Add buildings with costs
- [Economic Effects](/dev-resources/scripted-effects-reference/#economic-effects) - Treasury, debt, productivity
- [Internal Faction Effects](/dev-resources/scripted-effects-reference/#internal-faction-effects) - Faction opinions
- [Influence Effects](/dev-resources/scripted-effects-reference/#influence-effects) - Influence actions
- [Political Effects](/dev-resources/scripted-effects-reference/#political-effects) - Party management
- [Special System Effects](/dev-resources/scripted-effects-reference/#special-system-effects) - EU, Energy, Cartels

## How-To Guides

- [Add Subideology Parties](/dev-resources/scripted-effects-reference/#adding-subideology-parties)
- [Historical Events](/dev-resources/scripted-effects-reference/#historical-events-etd-system)
- [Variables](/dev-resources/scripted-effects-reference/#variable-basics)
- [Energy Configuration](/dev-resources/scripted-effects-reference/#energy-configuration)
- [Unique Terrain Photos](/dev-resources/scripted-effects-reference/#unique-terrain-photos)

## Related References

- [Scripted Effects Reference](/dev-resources/scripted-effects-reference/) - the full effects library and how-to guides
- [Dynamic Modifiers](/dev-resources/dynamic-modifiers/) - applying modifiers through tooltips and dynamic systems
- [Code Stylization Guide](/dev-resources/code-stylization-guide/) - formatting and code structure
- [Search Filters](/dev-resources/search-filters/) - focus `search_filters` reference

---

# Modifiers

Modifiers in Millennium Dawn follow standard HOI4 syntax but include many unique economic, political, and energy systems.

## Economic Modifiers

These modifiers affect the economy, taxes, trade, and productivity.

### General Economic

| Modifier                                           | Description                  | Notes                           |
| -------------------------------------------------- | ---------------------------- | ------------------------------- |
| `interest_rate_multiplier_modifier`                | Adjusts interest rate        | Whole numbers only              |
| `personnel_cost_multiplier_modifier`               | Military wages               |                                 |
| `army_personnel_cost_multiplier_modifier`          | Army wages                   |                                 |
| `navy_personnel_cost_multiplier_modifier`          | Navy wages                   |                                 |
| `airforce_personnel_cost_multiplier_modifier`      | Airforce wages               |                                 |
| `equipment_cost_multiplier_modifier`               | Equipment upkeep             |                                 |
| `bureaucracy_cost_multiplier_modifier`             | Bureaucracy spending         |                                 |
| `police_cost_multiplier_modifier`                  | Police spending              |                                 |
| `education_cost_multiplier_modifier`               | Education spending           |                                 |
| `health_cost_multiplier_modifier`                  | Healthcare spending          |                                 |
| `social_cost_multiplier_modifier`                  | Social spending              |                                 |
| `tax_rate_change_multiplier_modifier`              | Tax law change PP cost       |                                 |
| `projects_cost_modifier`                           | Economic project costs       |                                 |
| `civ_facs_worker_requirement_modifier`             | Civilian factory workers     |                                 |
| `mil_facs_worker_requirement_modifier`             | Military factory workers     |                                 |
| `offices_worker_requirement_modifier`              | Office workers               |                                 |
| `agriculture_district_worker_requirement_modifier` | Agriculture workers          |                                 |
| `microchip_plant_worker_requirement_modifier`      | Microchip plant workers      |                                 |
| `composite_plant_worker_requirement_modifier`      | Composite plant workers      |                                 |
| `synthetic_refinery_worker_requirement_modifier`   | Synthetic refinery workers   |                                 |
| `buildings_worker_requirement_modifier`            | All building workers         |                                 |
| `tax_gain_multiplier_modifier`                     | All tax income               |                                 |
| `population_tax_income_multiplier_modifier`        | Population taxes             |                                 |
| `corporate_tax_income_multiplier_modifier`         | Corporate taxes              |                                 |
| `return_on_investment_modifier`                    | International investment ROI | Use decimals (0.02 = 2%)        |
| `productivity_growth_modifier`                     | National productivity        | Keep small to avoid snowballing |
| `state_productivity_growth_modifier`               | Per-state productivity       |                                 |
| `country_productivity_growth_modifier`             | Country productivity growth  |                                 |
| `international_market_income_modifier`             | Equipment sales income       |                                 |
| `international_market_purchase_modifier`           | Equipment purchase costs     |                                 |
| `inflation_cost_multiplier_modifier`               | Inflation costs              |                                 |

### Exports & Resources

| Modifier                               | Description          |
| -------------------------------------- | -------------------- |
| `resource_export_multiplier_modifier`  | All resource exports |
| `oil_export_multiplier_modifier`       | Oil exports          |
| `steel_export_multiplier_modifier`     | Steel exports        |
| `aluminium_export_multiplier_modifier` | Aluminium exports    |
| `tungsten_export_multiplier_modifier`  | Tungsten exports     |
| `chromium_export_multiplier_modifier`  | Chromium exports     |
| `rubber_export_multiplier_modifier`    | Rubber exports       |
| `microchip_export_multiplier_modifier` | Microchip exports    |
| `composite_export_multiplier_modifier` | Composite exports    |

### Industry Productivity

| Modifier                                   | Description                     |
| ------------------------------------------ | ------------------------------- |
| `agricolture_productivity_modifier`        | Agriculture productivity        |
| `microchip_plants_productivity_modifier`   | Microchip plant productivity    |
| `composite_plants_productivity_modifier`   | Composite plant productivity    |
| `synthetic_refinery_productivity_modifier` | Synthetic refinery productivity |
| `civilian_factories_productivity`          | Civilian factory productivity   |
| `military_factories_productivity`          | Military factory productivity   |
| `dockyard_productivity`                    | Dockyard productivity           |
| `offices_productivity`                     | Office productivity             |

### Industry Income Taxes

| Modifier                                   | Description                   |
| ------------------------------------------ | ----------------------------- |
| `office_park_income_tax_modifier`          | Office tax income             |
| `agriculture_district_income_tax_modifier` | Agriculture tax income        |
| `microchip_plant_income_tax_modifier`      | Microchip plant tax income    |
| `composite_plant_income_tax_modifier`      | Composite plant tax income    |
| `synthetic_refinery_income_tax_modifier`   | Synthetic refinery tax income |
| `dockyard_income_tax_modifier`             | Dockyard tax income           |
| `military_industry_tax_modifier`           | Military industry tax         |
| `civilian_industry_tax_modifier`           | Civilian industry tax         |
| `agriculture_tax_modifier`                 | Agriculture tax               |
| `microchip_plant_tax_modifier`             | Microchip plant tax           |
| `composite_plant_tax_modifier`             | Composite plant tax           |
| `synthetic_plant_tax_modifier`             | Synthetic plant tax           |

### Campaign Costs

| Modifier                                     | Description               |
| -------------------------------------------- | ------------------------- |
| `salafist_outlook_campaign_cost_modifier`    | Salafist campaign cost    |
| `nonaligned_outlook_campaign_cost_modifier`  | Nonaligned campaign cost  |
| `western_outlook_campaign_cost_modifier`     | Western campaign cost     |
| `emerging_outlook_campaign_cost_modifier`    | Emerging campaign cost    |
| `nationalist_outlook_campaign_cost_modifier` | Nationalist campaign cost |
| `propaganda_campaign_cost_modifier`          | Propaganda campaign cost  |

### Investment Modifiers

| Modifier                                   | Description                 |
| ------------------------------------------ | --------------------------- |
| `investment_duration_modifier`             | Your project duration       |
| `receiving_investment_duration_modifier`   | Foreign project duration    |
| `investment_cost_modifier`                 | Your project costs          |
| `receiving_investment_cost_modifier`       | Foreign project costs       |
| `internal_investments_pp_cost_modifier`    | Internal investment PP cost |
| `internal_investments_money_cost_modifier` | Internal investment money   |

### Workforce & Labor

| Modifier                               | Description                  |
| -------------------------------------- | ---------------------------- |
| `total_workforce_modifier`             | Total workforce              |
| `high_unemployment_threshold_modifier` | Unemployment threshold       |
| `agriculture_workers_modifier`         | Agriculture workers %        |
| `resource_sector_workers_modifier`     | Resource sector workers %    |
| `gdp_from_resource_sector_modifier`    | GDP from resources           |
| `border_control_multiplier_modifier`   | Border control effectiveness |
| `civilian_chip_consumption_modifier`   | Civilian microchip use       |
| `industry_chip_consumption_modifier`   | Industry microchip use       |

### Upgrade & Special Costs

| Modifier                                  | Description                 |
| ----------------------------------------- | --------------------------- |
| `econ_cycle_upg_cost_multiplier_modifier` | Economic cycle upgrade cost |
| `cyber_cost_multiplier_modifier`          | Cyber system cost           |

### Education

| Modifier                           | Description             |
| ---------------------------------- | ----------------------- |
| `literacy_rate_education_modifier` | Literacy/education rate |

## Law Modifiers

These modify political power costs for changing government laws.

| Modifier                        | Description                  |
| ------------------------------- | ---------------------------- |
| `expected_adm_modifier`         | Bureau/Government spending   |
| `expected_police_modifier`      | Internal Security spending   |
| `expected_education_modifier`   | Education spending           |
| `expected_healthcare_modifier`  | Healthcare spending          |
| `expected_welfare_modifier`     | Social Spending              |
| `expected_mil_modifier`         | Military spending            |
| `corruption_cost_factor`        | Corruption change cost       |
| `economic_cycles_cost_factor`   | Economic cycle change cost   |
| `internal_factions_cost_factor` | Internal faction change cost |
| `bureaucracy_cost_factor`       | Bureaucracy change cost      |
| `trade_laws_cost_factor`        | Trade law change cost        |
| `Conscription_Law_cost_factor`  | Conscription change cost     |
| `migration_rate_value_factor`   | Migration law cost           |

## Migration Modifiers

These affect population migration.

| Modifier                       | Description                       |
| ------------------------------ | --------------------------------- |
| `base_migration_rate_value`    | Base migration rate (law only)    |
| `maximum_migration_rate_value` | Maximum migration rate (law only) |
| `migration_rate_value_factor`  | Migration rate multiplier         |

## Influence Modifiers

These affect the foreign influence system.

| Modifier                                                        | Description                    |
| --------------------------------------------------------------- | ------------------------------ |
| `foreign_influence_modifier`                                    | Influence action effectiveness |
| `foreign_influence_defense_modifier`                            | Defense against influence      |
| `foreign_influence_auto_influence_cap_modifier`                 | Auto-influence slots           |
| `influence_coup_modifier`                                       | Coup success rate              |
| `foreign_influence_continent_modifier`                          | Cross-continent influence      |
| `foreign_influence_home_continent_modifier`                     | Home continent influence       |
| `foreign_influence_monthly_domestic_independence_gain_modifier` | Monthly independence gain      |
| `foreign_influence_monthly_domestic_independence_gain_factor`   | Independence gain factor       |

## Energy Modifiers

These control power generation and consumption.

### General Energy

| Modifier                           | Description                   |
| ---------------------------------- | ----------------------------- |
| `energy_gain`                      | Flat energy gain              |
| `energy_gain_multiplier`           | Percentage energy gain        |
| `energy_use`                       | Static energy use             |
| `energy_use_multiplier`            | Total energy consumption      |
| `renewable_energy_gain`            | Renewable energy specifically |
| `renewable_energy_gain_multiplier` | Solar/wind energy multiplier  |
| `resource_storage_gain`            | Energy storage gain           |

### Population Energy

| Modifier                                 | Description             |
| ---------------------------------------- | ----------------------- |
| `pop_energy_use_multiplier`              | Population energy use   |
| `non_electric_fuel_consumption_modifier` | Direct fuel consumption |

### Fossil Fuels

| Modifier                               | Description              |
| -------------------------------------- | ------------------------ |
| `fossil_energy_gain`                   | Fossil fuel energy gain  |
| `fossil_pp_energy_generation_modifier` | Fossil fuel plant output |
| `fossil_fuel_consumption`              | Fossil fuel consumption  |
| `fossil_pp_fuel_consumption_modifier`  | Fossil plant fuel use    |

### Nuclear Energy

| Modifier                             | Description                 |
| ------------------------------------ | --------------------------- |
| `nuclear_energy_gain`                | Nuclear energy gain         |
| `nuclear_energy_generation_modifier` | Nuclear reactor output      |
| `nuclear_fuel_consumption`           | Nuclear fuel consumption    |
| `nuclear_fuel_consumption_modifier`  | Nuclear fuel use multiplier |

### Building Energy Use

| Modifier                                   | Description                   |
| ------------------------------------------ | ----------------------------- |
| `energy_use_modifier_civs`                 | Civilian factory energy use   |
| `energy_use_modifier_mils`                 | Military factory energy use   |
| `energy_use_modifier_offices`              | Office energy use             |
| `energy_use_modifier_agriculture_district` | Agriculture energy use        |
| `energy_use_modifier_microchip_plants`     | Microchip plant energy use    |
| `energy_use_modifier_composite_plants`     | Composite plant energy use    |
| `energy_use_modifier_synthetic_refinery`   | Synthetic refinery energy use |

### Renewable Infrastructure

| Modifier                                     | Description                |
| -------------------------------------------- | -------------------------- |
| `hydroelectric_energy_storage`               | Hydroelectric storage      |
| `hydroelectric_power_generation_modifier`    | Hydroelectric output       |
| `geothermal_power_generation_modifier`       | Geothermal output          |
| `state_renewable_capacity_factor_modifier`   | State renewable capacity   |
| `state_renewable_energy_generation_modifier` | State renewable generation |

### Battery & Storage

| Modifier                             | Description          |
| ------------------------------------ | -------------------- |
| `battery_park_construction_cost`     | Battery park costs   |
| `battery_park_storage_size_modifier` | Battery storage size |

## Political Modifiers

These affect internal politics.

| Modifier                     | Description                | Notes                     |
| ---------------------------- | -------------------------- | ------------------------- |
| `popularity_attack_modifier` | Party attack effectiveness | Not percentage (2.0 = 2x) |
| `popularity_boost_modifier`  | Party boost effectiveness  | Not percentage (2.0 = 2x) |

## Counter-Terror Modifiers

These affect the counter-terrorism system.

| Modifier                              | Description             |
| ------------------------------------- | ----------------------- |
| `terror_threat_detection_modifier`    | Threat detection chance |
| `terror_threat_base_detect_modifier`  | Base detection value    |
| `terror_threat_base_defense_modifier` | Base defense value      |

## Missile & Space Modifiers

These affect missile and satellite production.

| Modifier                            | Description               |
| ----------------------------------- | ------------------------- |
| `olv_production_speed_modifier`     | Orbital launch vehicle    |
| `gnss_production_speed_modifier`    | Navigation satellites     |
| `comsat_production_speed_modifier`  | Communications satellites |
| `spysat_production_speed_modifier`  | Spy satellites            |
| `killsat_production_speed_modifier` | Kill satellites           |
| `nuclear_reactor_fuel_production`   | Nuclear fuel production   |

## Nation-Specific Modifiers

### Czech Republic

| Modifier                                 | Description        |
| ---------------------------------------- | ------------------ |
| `CZE_skoda_superb_productivity_modifier` | Škoda productivity |

### Italy

| Modifier                               | Description              |
| -------------------------------------- | ------------------------ |
| `ITA_ageing_population_drift_modifier` | Aging population drift   |
| `ITA_reform_expectance_drift`          | Reform expectation drift |

---
