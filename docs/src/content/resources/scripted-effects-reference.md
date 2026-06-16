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
| Offices                | `one_state_office_construction`    | `one_office_construction`           |
| Infrastructure         | `one_state_infrastructure`         | `one_random_infrastructure`         |
| Air Base               | `one_state_air_base`               | `one_air_base`                      |
| Network Infrastructure | `one_state_network_infrastructure` | `one_random_network_infrastructure` |
| Anti-Air/SAM           | `one_state_anti_air`               | `one_anti_air`                      |
| Radar                  | `one_state_radar_station`          | `one_radar_station`                 |
| Nuclear Reactor        | `one_state_nuclear_reactor`        | `one_random_nuclear_reactor`        |
| Agriculture District   | `one_state_agriculture_district`   | `one_random_agriculture_district`   |

### Building Costs (State-Level)

The cost implies the INCLUSION of a building slot. A single building slot is $1.00 so if you want to give a **Civilian Industry** it's $6.50 without a building slot.

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

Adding a new party requires edits to four files. Follow the steps below in order.

### Step 1: Choose a Slot

Consult the [Subideology Slots table](#subideology-slots) below to pick the subideology key and its index for the ideology group your party belongs to. Note both -- you will need the key for localisation and the index for the history file.

### Step 2: Add Localisation

In `localisation/english/MD_subideology_parties_l_english.yml`, add three entries for the party using the format below:

```yaml
TAG.subideology: "£TAG_icon_name (ABBRV) - Party Name"
TAG.subideology_icon: "£TAG_icon_name"
TAG.subideology_desc: "(Dominant Ideology) - Party Name (Native name, ABBRV)\n\nDescription"
```

If the party changes over time (e.g. a coalition partner becomes dominant), add `_alt` variants:

```yaml
TAG.subideology_alt: "£TAG_icon_name_alt (ABBRV) - Alternate Party Name"
TAG.subideology_icon_alt: "£TAG_icon_name_alt"
TAG.subideology_desc_alt: "(Dominant Ideology) - Alternate Party Name (Native name, ABBRV)\n\nDescription"
```

### Step 3: Register the Icon

**a) Add the GFX entry** to `interface/MD_parties_icons.gfx`, keeping entries sorted alphabetically by tag:

```hoiscript
spriteType = {
	name = "GFX_TAG_icon_name"
	texturefile = "gfx/texticons/parties_icons/country_name_lowercase/TAG_icon_name.dds"
	legacy_lazy_load = no
}
```

The `name` value must match the icon referenced in localisation (without the `£` prefix, prefixed with `GFX_`).

**b) Place the DDS file** at `gfx/texticons/parties_icons/{country_name_lowercase}/TAG_icon_name.dds`. Party icon DDS files are typically 20x20 px text icons.

### Step 4: Set Starting Popularity

In `history/countries/TAG - Country.txt`, set the party's starting popularity using its slot index. A comment with the party abbreviation is required:

```hoiscript
set_variable = { party_pop_array^N = 0.15 } # Party Abbreviation
```

Where `N` is the slot index from the slots table. Only set slots for parties that actually exist in the country -- leave unused slots unset (they default to 0).

If the party holds government or is a coalition partner at game start, also add:

```hoiscript
add_to_array = { ruling_party = N }          # if this party governs alone or leads the coalition
add_to_array = { gov_coalition_array = N }   # if this party is a junior coalition partner
```

For countries with elections, set the most recent election results separately:

```hoiscript
set_variable = { party_pop_elect_array^N = 0.15 } # Party Abbreviation - election result
```

### Step 5: Add Leaders (Optional)

If the country has scripted leader rotation, add the leader's `create_country_leader` block inside the appropriate `if = { limit = { has_country_flag = set_subideology } }` block in `common/scripted_effects/TAG_political_leaders.txt`. Create the file if it doesn't yet exist for this tag.

### Subideology Slots

| Index | Slot                         | Ideology Group            |
| ----- | ---------------------------- | ------------------------- |
| 0     | `Western_Autocracy`          | Pro-Western (democratic)  |
| 1     | `conservatism`               | Pro-Western (democratic)  |
| 2     | `liberalism`                 | Pro-Western (democratic)  |
| 3     | `socialism`                  | Pro-Western (democratic)  |
| 4     | `Communist-State`            | Emerging (communism)      |
| 5     | `anarchist_communism`        | Emerging (communism)      |
| 6     | `Conservative`               | Emerging (communism)      |
| 7     | `Autocracy`                  | Emerging (communism)      |
| 8     | `Mod_Vilayat_e_Faqih`        | Emerging (communism)      |
| 9     | `Vilayat_e_Faqih`            | Emerging (communism)      |
| 10    | `Kingdom`                    | Salafist (fascism)        |
| 11    | `Caliphate`                  | Salafist (fascism)        |
| 12    | `Neutral_Muslim_Brotherhood` | Non-Aligned (neutrality)  |
| 13    | `Neutral_Autocracy`          | Non-Aligned (neutrality)  |
| 14    | `Neutral_conservatism`       | Non-Aligned (neutrality)  |
| 15    | `oligarchism`                | Non-Aligned (neutrality)  |
| 16    | `Neutral_Libertarian`        | Non-Aligned (neutrality)  |
| 17    | `Neutral_green`              | Non-Aligned (neutrality)  |
| 18    | `neutral_Social`             | Non-Aligned (neutrality)  |
| 19    | `Neutral_Communism`          | Non-Aligned (neutrality)  |
| 20    | `Nat_Populism`               | Nationalist (nationalist) |
| 21    | `Nat_Fascism`                | Nationalist (nationalist) |
| 22    | `Nat_Autocracy`              | Nationalist (nationalist) |
| 23    | `Monarchist`                 | Nationalist (nationalist) |

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

Set these state-scoped variables in the state history file.

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

# Related Resources

- [Code Resource](/dev-resources/code-resource/) -- modifier reference.
- [Code Stylization Guide](/dev-resources/code-stylization-guide/) -- formatting and code structure.
- [Dynamic Modifiers](/dev-resources/dynamic-modifiers/) -- dynamic modifier tooltip usage.
