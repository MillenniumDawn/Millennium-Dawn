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
- [Influence Modifiers](#influence-modifiers) - Foreign influence mechanics
- [Energy Modifiers](#energy-modifiers) - Power generation and consumption
- [Political Modifiers](#political-modifiers) - Party popularity mechanics

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

| Modifier                                                                  | Category  | Description                  | Notes                           |
| ------------------------------------------------------------------------- | --------- | ---------------------------- | ------------------------------- |
| `interest_rate_multiplier_modifier`                                       | Economic  | Adjusts interest rate        | Whole numbers only              |
| `personnel_cost_multiplier_modifier`                                      | Economic  | Military wages               |                                 |
| `army/navy/airforce_personnel_cost_multiplier_modifier`                   | Economic  | Branch-specific wages        |                                 |
| `equipment_cost_multiplier_modifier`                                      | Economic  | Equipment upkeep             |                                 |
| `bureaucracy_cost_multiplier_modifier`                                    | Economic  | Bureaucracy spending         |                                 |
| `tax_rate_change_multiplier_modifier`                                     | Economic  | Tax law change PP cost       |                                 |
| `projects_cost_modifier`                                                  | Economic  | Economic project costs       |                                 |
| `civ_facs_worker_requirement_modifier`                                    | Economic  | Civilian factory workers     |                                 |
| `mil_facs_worker_requirement_modifier`                                    | Economic  | Military factory workers     |                                 |
| `tax_gain_multiplier_modifier`                                            | Economic  | All tax income               |                                 |
| `population_tax_income_multiplier_modifier`                               | Economic  | Population taxes             |                                 |
| `corporate_tax_income_multiplier_modifier`                                | Economic  | Corporate taxes              |                                 |
| `resource_export_multiplier_modifier`                                     | Economic  | All resource exports         |                                 |
| `oil/steel/tungsten/aluminium/chromium/rubber_export_multiplier_modifier` | Economic  | Specific exports             |                                 |
| `return_on_investment_modifier`                                           | Economic  | International investment ROI | Use decimals (0.02 = 2%)        |
| `productivity_growth_modifier`                                            | Economic  | National productivity        | Keep small to avoid snowballing |
| `state_productivity_growth_modifier`                                      | Economic  | Per-state productivity       |                                 |
| `migration_rate_value_factor`                                             | Migration | Net migration rate           |                                 |
| `international_market_income_modifier`                                    | Economic  | Equipment sales income       |                                 |
| `international_market_purchase_modifier`                                  | Economic  | Equipment purchase costs     |                                 |

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

## Energy Modifiers

These control power generation and consumption.

| Modifier                                  | Description                   |
| ----------------------------------------- | ----------------------------- |
| `energy_gain`                             | Flat energy gain              |
| `energy_gain_multiplier`                  | Percentage energy gain        |
| `renewable_energy_gain`                   | Renewable energy specifically |
| `pop_energy_use_multiplier`               | Population energy use         |
| `fossil_pp_energy_generation_modifier`    | Fossil fuel plant output      |
| `nuclear_energy_generation_modifier`      | Nuclear reactor output        |
| `hydroelectric_power_generation_modifier` | Hydroelectric output          |
| `geothermal_power_generation_modifier`    | Geothermal output             |
| `energy_use_multiplier`                   | Total energy consumption      |
| `battery_park_construction_cost`          | Battery park costs            |

## Political Modifiers

These affect internal politics.

| Modifier                     | Description                | Notes                     |
| ---------------------------- | -------------------------- | ------------------------- |
| `popularity_attack_modifier` | Party attack effectiveness | Not percentage (2.0 = 2x) |
| `popularity_boost_modifier`  | Party boost effectiveness  | Not percentage (2.0 = 2x) |

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

### Counter-Terror (Radicalization)

```hoiscript
set_temp_variable = { rad_change = -5 }
modify_radicalization_effect = yes

set_temp_variable = { threat_change = 2 }
modify_terror_threat_effect = yes
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
