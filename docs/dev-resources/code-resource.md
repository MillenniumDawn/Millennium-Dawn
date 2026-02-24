---
layout: default
title: "Code Resources"
description: "Millennium Dawn unique modifiers, effects and tutorials for modders"
---

This document provides reference documentation for Millennium Dawn's unique systems, including custom modifiers, scripted effects, and how-to guides for common modding tasks.

> **Note**: This is not fully up-to-date. For the latest systems, check the codebase directly.

---

# Quick Reference

## Custom Modifier Categories

- [Economic Modifiers](#economic-modifiers) - Money, taxes, productivity, trade
- [Law Modifiers](#law-modifiers) - Government spending, law costs
- [Migration Modifiers](#migration-modifiers) - Population migration
- [Influence Modifiers](#influence-modifiers) - Foreign influence mechanics
- [Energy Modifiers](#energy-modifiers) - Power generation and consumption
- [Political Modifiers](#political-modifiers) - Party popularity mechanics
- [Counter-Terror Modifiers](#counter-terror-modifiers) - Counter-terrorism
- [Missile & Space Modifiers](#missile--space-modifiers) - Missile/satellite production
- [Nation-Specific Modifiers](#nation-specific-modifiers) - Country unique modifiers

## Scripted Effects Categories

- [Building Effects](#md-building-effects) - Add buildings with costs
- [Economic Effects](#md-economic-effects) - Treasury, debt, productivity
- [Internal Faction Effects](#md-internal-faction-effects) - Faction opinions
- [Influence Effects](#md-influence-effects) - Influence actions
- [Political Effects](#md-political-effects) - Party management
- [Special System Effects](#special-system-effects) - EU, Energy, Counter-Terror, Cartels

## How-To Guides

- [Add Subideology Parties](#md-how-to-add-subideology-parties)
- [Historical Events](#historical-eventsexact-date-trigger-etd-events)
- [Variables](#variable-guideexplanation)
- [Energy Configuration](#hydroelectricgeothermalrenewableproductivity-configuration-guide)
- [Unique Terrain Photos](#unique-terrain-photos)

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

# Scripted Effects

All scripted effects automatically generate tooltips. **Do not** add extra localization for these.

## Building Effects

> **Location**: `common/scripted_effects/00_scripted_effects.txt`

Buildings can be added using state scope or random scope:

### State Scope (Predefined State)

```hoiscript
117 = {
    one_state_industrial_complex = yes
}
```

### Random Scope (Any Owned State)

```hoiscript
one_random_industrial_complex = yes
two_random_industrial_complex = yes
three_random_industrial_complex = yes
four_random_industrial_complex = yes
```

### Available Building Effects

| Building               | Random Effects                      | State Scope Effects                |
| ---------------------- | ----------------------------------- | ---------------------------------- |
| Civilian Factory       | `one_random_industrial_complex`     | `one_state_industrial_complex`     |
| Military Factory       | `one_random_arms_factory`           | `one_state_arms_factory`           |
| Dockyard               | `one_random_dockyard`               | `one_state_dockyard`               |
| Offices                | `one_office_construction`           | `one_state_office_construction`    |
| Infrastructure         | `one_random_infrastructure`         | `one_state_infrastructure`         |
| Air Base               | `one_air_base`                      | `one_state_air_base`               |
| Network Infrastructure | `one_random_network_infrastructure` | `one_state_network_infrastructure` |
| Anti-Air/SAM           | `one_anti_air`                      | `one_state_anti_air`               |
| Radar                  | `one_radar_station`                 | `one_state_radar_station`          |
| Nuclear Reactor        | `one_random_nuclear_reactor`        | `one_state_nuclear_reactor`        |
| Agriculture District   | `one_random_agriculture_district`   | `one_state_agriculture_district`   |

### Building Costs (State-Level)

| Building                            | Cost   |
| ----------------------------------- | ------ |
| Civilian/Military Factory, Dockyard | $7.50  |
| Offices                             | $12.00 |
| Commercialized Agriculture          | $3.75  |
| Infrastructure                      | $3.50  |
| Air Base                            | $2.50  |
| SAM Site                            | $3.25  |
| Renewable Infrastructure            | $8.50  |
| Fuel Silo                           | $3.00  |
| Radar                               | $1.75  |
| Network Infrastructure              | $3.00  |
| Missile Site                        | $3.00  |
| Nuclear Reactor                     | $9.00  |
| Fossil Powerplant                   | $2.25  |
| Microchip Plant                     | $10.50 |
| Composite Plant                     | $7.50  |

## Economic Effects

### Treasury Management

```hoiscript
# Modify treasury
set_temp_variable = { treasury_change = -10.00 }
modify_treasury_effect = yes

# Preset expenditures
small_expenditure = yes
medium_expenditure = yes
large_expenditure = yes
```

### Debt Management

```hoiscript
set_temp_variable = { debt_change = 0.1 }
modify_debt_effect = yes
```

### Productivity

```hoiscript
# Adjust productivity (flat value)
set_temp_variable = { temp_productivity_change = 0.025 }
flat_productivity_change_effect = yes
```

### Economic Cycles

```hoiscript
increase_economic_growth = yes
decrease_economic_growth = yes
depression = yes
recession = yes
stagnation = yes
stable_growth = yes
fast_growth = yes
economic_boom = yes
```

### Government Spending Laws

```hoiscript
# Bureaucracy
increase_centralization = yes
decrease_centralization = yes

# Social Spending
increase_social_spending = yes
decrease_social_spending = yes

# Education
increase_education_budget = yes
decrease_education_budget = yes

# Healthcare
increase_healthcare_budget = yes
decrease_healthcare_budget = yes

# Policing
increase_policing_budget = yes
decrease_policing_budget = yes

# Trade Law
increase_exports = yes
decrease_exports = yes

# Military Spending
increase_military_spending = yes
decrease_military_spending = yes
```

## Internal Faction Effects

### Changing Faction Opinions

```hoiscript
set_temp_variable = { temp_opinion = 5 }
change_small_medium_business_owners_opinion = yes
```

### Available Faction Effects

| Category         | Effects                                                                                                                                                                                                               |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Economic         | `change_small_medium_business_owners_opinion`, `change_industrial_conglomerates_opinion`, `change_fossil_fuel_industry_opinion`, `change_international_bankers_opinion`, `change_oligarchs_opinion`                   |
| Militaristic     | `change_defense_industry_opinion`, `change_maritime_industry_opinion`, `change_the_military_opinion`, `change_intelligence_community_opinion`                                                                         |
| Special Interest | `change_labour_unions_opinion`, `change_landowners_opinion`, `change_farmers_opinion`, `change_communist_cadres_opinion`                                                                                              |
| Religious        | `change_the_clergy_opinion`, `change_the_ulema_opinion`, `change_the_priesthood_opinion`, `change_the_wahabi_ulema_opinion`                                                                                           |
| Nation-Specific  | `change_the_bazaar_opinion` (Iran), `change_the_donju_opinion` (North Korea), `change_saudi_royal_family_opinion`, `change_irgc_opinion`, `change_chaebols_opinion` (South Korea), `change_wall_street_opinion` (USA) |

## Influence Effects

### Basic Influence

```hoiscript
# Domestic influence
set_temp_variable = { percent_change = 10 }
change_domestic_influence_percentage = yes

# General influence (requires target)
set_temp_variable = { percent_change = 5 }
set_temp_variable = { tag_index = ROOT }
set_temp_variable = { influence_target = GER }
change_influence_percentage = yes
```

### Index-Based Influence

```hoiscript
set_temp_variable = { percent_change = 5 }
set_temp_variable = { influencer_index = 0 }
change_current_influencer_index_percentage = yes
```

## Political Effects

### Party Popularity

```hoiscript
# Set party index (0-23) and change popularity
set_temp_variable = { party_index = 2 }
set_temp_variable = { party_popularity_increase = 0.10 }  # 10% = 0.10
add_relative_party_popularity = yes

# Or set to ruling party automatically
set_party_index_to_ruling_party = yes
```

### Ruling Party Changes

```hoiscript
# Set ruling party
set_temp_variable = { rul_party_temp = 20 }
change_ruling_party_effect = yes
set_politics = {
    ruling_party = nationalist
    elections_allowed = no
}
```

### Coalition Management

```hoiscript
# Add to coalition
set_temp_variable = { add_col_one = 5 }
add_coalition_members_effect = yes

# Remove from coalition
set_temp_variable = { remove_col_one = 5 }
remove_coalition_members_effect = yes
```

### Ban/Allow Parties

```hoiscript
# Ban party
set_temp_variable = { party_index = 1 }
ban_party_scripted_call = yes

# Allow party
set_temp_variable = { party_index = 1 }
unban_party_scripted_call = yes
```

## Special System Effects

### Euroscepticism (EU)

```hoiscript
# Single country
set_temp_variable = { modify_eurosceptic = 0.05 }
set_temp_variable = { modify_eurosceptic_target = GER }
eurosceptic_change = yes

# All EU members
set_temp_variable = { modify_eurosceptic = -0.05 }
EU_eurosceptic_change = yes
```

### Energy Systems

```hoiscript
# Build enrichment facilities (cost: 25.00 each)
set_temp_variable = { temp_change = 2 }
build_enrichment_facilities_effect = yes

# Build battery parks (cost: 100.00 each)
set_temp_variable = { temp_change = 2 }
build_battery_park_effect = yes
```

### Cartel Effects

Handles cartel strength and political influence changes.

```hoiscript
# Modify cartel variables
set_temp_variable = { cart_strength_change = 2 }
set_temp_variable = { cart_influence_change = 2 }
modify_cartel_variables_effect = yes
```

---

# How-To Guides

## Adding Subideology Parties

Political parties require edits to multiple files:

1. **Party Definition**: `localisation/english/MD_subideology_parties_l_english.yml`
2. **Icons**: `interface/MD_parties_icons.gfx` + `gfx/texticons/parties_icons/{tag}/`
3. **Localization**: `common/scripted_localisation/subideology_scripted_localization.txt`
4. **Leaders** (optional): `common/scripted_effects/{TAG}_political_leaders.txt`

### Subideology Slots

| Ideology Group | Available Slots                                                 |
| -------------- | --------------------------------------------------------------- |
| Western        | `conservatism`, `liberalism`, `socialism`                       |
| Emerging       | `Communist-State`, `anarchist_communism`, `Mod_Vilayat_e_Faqih` |
| Salafism       | `Kingdom`, `Caliphate`                                          |
| Non-Aligned    | `oligarchism`, `Neutral_Libertarian`, `Neutral_green`           |
| Nationalist    | `Nat_Populism`, `Nat_Fascism`, `Nat_Autocracy`, `Monarchist`    |

## Historical Events (ETD System)

Events should use the yearly effects system in `common/scripted_effects/00_yearly_effects.txt`:

```hoiscript
# First year events
MD_event_on_startup_events = {
    CAM = { country_event = { id = Cameroon.1 days = 50 random_days = 50 } }
}

# Specific year events
trigger_year_2067_events = {
    USA = { country_event = { id = collapse_event.1 days = 30 random_days = 336 } }
}
```

## Variable Basics

```hoiscript
# Set variable
set_variable = { var = example_var value = 1 }

# Add to variable
add_to_variable = { var = example_var value = 1 }

# Set bounds
set_variable = { var = example_var value = 50 max = 100 min = 0 }
```

## Energy Configuration

### Hydroelectric/Geothermal

```hoiscript
set_variable = { hydroelectric_energy_production_var = 5.636 }
set_variable = { hydroelectric_energy_storage_var = 300 }
add_dynamic_modifier = { modifier = hydroelectric_infrastructure_in_state }
```

### Renewable Capacity (from Global Wind Atlas)

```hoiscript
# Capacity factor = (Atlas value) - 0.25
set_variable = { state_renewable_capacity_factor_modifier_var = 0.55 }
```

## Unique Terrain Photos

Adds custom terrain photos to specific provinces.

### Step 1: Create Image

- Size: **413x70px**
- Format: DDS
- Location: `gfx/interface/terrain/`

### Step 2: Register in GFX File

File: `interface/MD_terrain_cities.gfx`

```hoiscript
spriteType = {
    name = "GFX_terrain_brussels"
    textureFile = "gfx/interface/terrain/your_image.dds"
}
```

### Step 3: Create GUI Icon

File: `interface/countrystateview.gui`

```hoiscript
iconType = {
    name = "terrain_brussels_icon"
    spriteType = "GFX_terrain_brussels"
    alwaystransparent = yes
}
```

### Step 4: Create Empty Modifier

File: `common/modifiers/01_province_modifiers.txt`

```hoiscript
terrain_brussels = { }
```

### Step 5: Add to Startup Effects

File: `common/scripted_effects/00_startup_effects.txt`

```hoiscript
# State ID 50, province ID 516
50 = {
    add_province_modifier = {
        static_modifiers = { terrain_brussels }
        province = { id = 516 }
    }
}
```

> **Tip**: Use `Tdebug` console command in-game to find state and province IDs.

---

# Additional Resources

- **Discord**: @AngriestBird for questions
- **Error Codes**: See `docs/dev-resources/error-debug-codes.md`
- **Focus Trees**: See `.cursor/.ai-guides/code_styling.md`
