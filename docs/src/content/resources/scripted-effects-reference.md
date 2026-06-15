---
title: Scripted Effects Reference
description: Millennium Dawn scripted effects for buildings, economy, factions, influence, politics, and special systems
---

All scripted effects automatically generate tooltips. **Do not** add extra localization for these.

---

# Building Effects

> **Location**: `common/scripted_effects/00_scripted_effects.txt`

Buildings can be added using state scope or random scope:

### State Scope (Predefined State)

```hoiscript
117 = {
    one_state_industrial_complex = yes
}
```

### Random Scope (Picks a Valid State)

```hoiscript
random_controlled_state = {
    one_random_industrial_complex = yes
}
```

### Building Table

| Building               | State Scope                        | Random Scope                        |
| ---------------------- | ---------------------------------- | ----------------------------------- |
| Civilian Factory       | `one_state_industrial_complex`     | `one_random_industrial_complex`     |
| Military Factory       | `one_state_arms_factory`           | `one_random_arms_factory`           |
| Dockyard               | `one_state_dockyard`               | `one_random_dockyard`               |
| Offices                | `one_office_construction`          | `one_office_construction`           |
| Infrastructure         | `one_state_infrastructure`         | `one_random_infrastructure`         |
| Air Base               | `one_air_base`                     | `one_air_base`                      |
| Network Infrastructure | `one_state_network_infrastructure` | `one_random_network_infrastructure` |
| Anti-Air/SAM           | `one_anti_air`                     | `one_anti_air`                      |
| Radar                  | `one_radar_station`                | `one_radar_station`                 |
| Nuclear Reactor        | `one_state_nuclear_reactor`        | `one_random_nuclear_reactor`        |
| Agriculture District   | `one_state_agriculture_district`   | `one_random_agriculture_district`   |

### Building Costs (State-Level)

The cost implies the INCLUSION of a building slot.

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

---

# Economic Effects

> **Location**: `common/scripted_effects/00_scripted_effects.txt`

## Treasury Management

```hoiscript
# Modify treasury
set_temp_variable = { treasury_change = -10.00 }
modify_treasury_effect = yes

# Preset expenditures
small_expenditure = yes    # medium_expenditure, large_expenditure
```

## Debt Management

```hoiscript
# Modify debt
set_temp_variable = { debt_change = 0.1 }
modify_debt_effect = yes
```

## Productivity

```hoiscript
# Adjust productivity (flat value)
set_temp_variable = { temp_productivity_change = 0.025 }
flat_productivity_change_effect = yes
```

## Budget Effects

```hoiscript
# Bureaucracy
set_temp_variable = { bureau_change = 1 }
modify_bureaucracy_effect = yes

# Social Spending
set_temp_variable = { social_change = 1 }
modify_social_spending_effect = yes

# Education
set_temp_variable = { education_change = 1 }
modify_education_spending_effect = yes

# Healthcare
set_temp_variable = { health_change = 1 }
modify_health_spending_effect = yes

# Policing
set_temp_variable = { police_change = 1 }
modify_police_spending_effect = yes

# Trade Law
increase_exports = yes / decrease_exports = yes

# Military Spending
increase_military_spending = yes / decrease_military_spending = yes
```

---

# Internal Faction Effects

> **Location**: `common/scripted_effects/00_scripted_effects.txt`

```hoiscript
# Change faction opinion
set_temp_variable = { labour_unions_opinion = 5 }
change_labour_unions_opinion = yes

# Available factions:
# labour_unions, the_clergy, small_and_medium_business_owners,
# landowners, military_industrial_complex, intelligence_community,
# organized_crime
```

---

# Influence Effects

> **Location**: `common/scripted_effects/00_influence_scripted_effects.txt`

```hoiscript
# Domestic influence
set_temp_variable = { percent_change = 10 }
change_domestic_influence_percentage = yes

# General influence (requires target)
set_temp_variable = { percent_change = 5 }
set_temp_variable = { tag_index = ROOT }
set_temp_variable = { influence_target = GER }
change_influence_percentage = yes

# Current influencer index
set_temp_variable = { percent_change = 5 }
set_temp_variable = { influencer_index = 0 }
change_current_influencer_index_percentage = yes
```

---

# Political Effects

> **Location**: `common/scripted_effects/00_scripted_effects.txt`

## Party Popularity

```hoiscript
# Add relative popularity to the ruling party (default)
set_temp_variable = { party_popularity_increase = 0.10 }
add_relative_party_popularity = yes

# Or target a specific party by index (0-23)
set_temp_variable = { party_index = 2 }
set_temp_variable = { party_popularity_increase = 0.10 }
add_relative_party_popularity = yes
```

## Ruling Party Changes

```hoiscript
# Set ruling party
set_temp_variable = { rul_party_temp = 20 }
change_ruling_party_effect = yes
set_politics = {
    ruling_party = nationalist
    elections_allowed = no
}
```

## Coalition Management

```hoiscript
# Add to coalition
set_temp_variable = { add_col_one = 5 }
add_coalition_members_effect = yes

# Remove from coalition
set_temp_variable = { remove_col_one = 5 }
remove_coalition_members_effect = yes
```

## Party Bans

```hoiscript
# Ban party
set_temp_variable = { party_index = 1 }
ban_party_scripted_call = yes

# Allow party
set_temp_variable = { party_index = 1 }
unban_party_scripted_call = yes
```

---

# Special System Effects

> **Location**: Various files in `common/scripted_effects/`

## EU Effects

```hoiscript
# Single country
set_temp_variable = { eu_influence_change = 5 }
modify_eu_influence_effect = yes

# All EU members
every_country = {
    limit = { has_country_flag = EU_member }
    add_stability = 0.05
}
```

## Energy Effects

```hoiscript
# Build enrichment facilities (cost: 25.00 each)
set_temp_variable = { build_count = 3 }
build_enrichment_facilities = yes

# Build battery parks (cost: 100.00 each)
set_temp_variable = { build_count = 2 }
build_battery_parks = yes
```

## Cartel Effects

```hoiscript
# Modify cartel variables
set_temp_variable = { cartel_strength_change = 0.1 }
modify_cartel_strength = yes
```

---

# How-To Guides

## Adding Subideology Parties

To add a new subideology party to a country:

1. Find an available party slot in the ideology group.
2. Add the party to the country's history file.
3. Register the party in `common/scripted_localisation/00_subideology_scripted_localisation.txt`.

Consult the [Subideology Slots table](/dev-resources/code-resource/#subideology-slots) below to pick the subideology key and its index for the ideology group your party belongs to. Note both -- you will need the key for localisation and the index for the history file.

### Subideology Slots

Each ideology group has a fixed number of party slots. The index is 0-based within each group:

| Ideology Group | Slots | Example Subideologies                              |
| -------------- | ----- | -------------------------------------------------- |
| Western Left   | 6     | social_democracy, democratic_socialism, ...        |
| Western Right  | 6     | conservatism, liberalism, christian_democracy, ... |
| Eastern        | 6     | communist, marxist_leninist, maoist, ...           |
| Non-Aligned    | 6     | neutral_green, neutral_libertarian, ...            |
| Nationalist    | 6     | fascist, national_socialist, ultranationalist, ... |

Each slot has a fixed index (0-5) within its group. The subideology key is a string like `social_democracy`; the index is a number like `2`. Both must match the country history file and the localisation.

## Historical Events (ETD System)

Trigger date-based events via `common/scripted_effects/00_yearly_effects.txt`:

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

When the intended recipient may no longer own the target state, use the owner-guard pattern (check expected owner, fall back to `random_country = { limit = { owns_state = X } }`).

## Variable Basics

```hoiscript
# Set variable
set_variable = { my_var = 5 }

# Add to variable
add_to_variable = { my_var = 2 }

# Set bounds
clamp_variable = { var = my_var min = 0 max = 100 }
```

## Energy Configuration

> **Location**: `common/scripted_effects/00_energy_effects.txt`

```hoiscript
# Hydroelectric/Geothermal/Renewable/Productivity Configuration
set_variable = { renewable_capacity_factor = 0.45 }
# Capacity factor = (Atlas value) - 0.25
# This adjusts the output of renewable energy sources based on geographic data
```

## Unique Terrain Photos

Terrain photos are province-specific cosmetic overrides. The system uses `common/scripted_effects/00_terrain_photos.txt`:

```hoiscript
# State ID 50, province ID 516
set_province_terrain_photo = {
    province = 516
    state = 50
    terrain = forest
}
```

---

# Related Resources

- [Code Resource](/dev-resources/code-resource/) -- modifier reference.
- [Code Stylization Guide](/dev-resources/code-stylization-guide/) -- formatting and code structure.
- [Dynamic Modifiers](/dev-resources/dynamic-modifiers/) -- dynamic modifier tooltip usage.
