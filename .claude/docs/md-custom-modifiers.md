# Millennium Dawn — Custom Modifier Definitions

All modifiers in this file are defined in `common/modifier_definitions/` and are **not** part of vanilla HOI4. Use them anywhere vanilla modifiers are valid: `idea` blocks, `dynamic_modifier` blocks, `national_focus completion_reward`, and `decision` effects. They are **not** valid inside MIO `equipment_bonus` or `production_bonus` blocks — only in `organization_modifier` or standalone idea/modifier contexts.

Country-tag-specific modifiers (prefixed `CZE_`, `ITA_`, `JAP_`) must only appear in content for those countries.

---

## Counter-Terror (`counter_terror_modifier_definitions.txt`) — country scope

| Modifier | Notes |
|---|---|
| `terror_threat_detection_modifier` | percentage |
| `terror_threat_base_detect_modifier` | number |
| `terror_threat_base_defense_modifier` | number |

---

## Cyber (`cyber_modifier_definitions.txt`) — country scope

| Modifier | Notes |
|---|---|
| `cyber_offense_power_modifier` | number |
| `cyber_defense_rating_modifier` | number |
| `cyber_attribution_bonus_modifier` | number |
| `cyber_capability_modifier` | number |

---

## Energy (`energy_modifier_definitions.txt`) — country scope unless noted

| Modifier | Scope |
|---|---|
| `energy_gain` | country |
| `energy_gain_multiplier` | country |
| `renewable_energy_gain` | country |
| `renewable_energy_gain_multiplier` | country |
| `resource_storage_gain` | country |
| `energy_use` | country |
| `energy_use_multiplier` | country |
| `pop_energy_use_multiplier` | country |
| `non_electric_fuel_consumption_modifier` | country |
| `fossil_energy_gain` | country |
| `fossil_pp_energy_generation_modifier` | country |
| `fossil_fuel_consumption` | country |
| `fossil_pp_fuel_consumption_modifier` | country |
| `nuclear_energy_gain` | country |
| `nuclear_fuel_consumption` | country |
| `nuclear_energy_generation_modifier` | country |
| `nuclear_fuel_consumption_modifier` | country |
| `energy_use_modifier_civs` | country |
| `energy_use_modifier_offices` | country |
| `energy_use_modifier_agriculture_district` | country |
| `energy_use_modifier_mils` | country |
| `energy_use_modifier_microchip_plant` | country |
| `energy_use_modifier_composite_plant` | country |
| `energy_use_modifier_synthetic_refinery` | country |
| `battery_park_construction_cost` | country |
| `battery_park_storage_size_modifier` | country |
| `hydroelectric_energy_storage` | country |
| `hydroelectric_power_generation_modifier` | country |
| `geothermal_power_generation_modifier` | country |
| `state_renewable_capacity_factor_modifier` | **state** |
| `state_renewable_energy_generation_modifier` | **state** |

---

## Expected Spending (`expected_spending.txt`) — country scope

| Modifier |
|---|
| `expected_welfare_modifier` |
| `expected_healthcare_modifier` |
| `expected_education_modifier` |
| `expected_police_modifier` |
| `expected_adm_modifier` |
| `expected_mil_modifier` |

---

## Foreign Influence (`influence_modifier_definitions.txt`) — country scope

| Modifier |
|---|
| `foreign_influence_defense_modifier` |
| `foreign_influence_modifier` |
| `foreign_influence_auto_influence_cap_modifier` |
| `influence_coup_modifier` |
| `foreign_influence_continent_modifier` |
| `foreign_influence_home_continent_modifier` |
| `foreign_influence_monthly_domestic_independence_gain_modifier` |
| `foreign_influence_monthly_domestic_independence_gain_factor` |

---

## Migration (`migration_modifier_definitions.txt`) — country scope

| Modifier |
|---|
| `base_migration_rate_value` |
| `maximum_migration_rate_value` |
| `migration_rate_value_factor` |

---

## Missiles & Space (`missile_modifier_definitions.txt`) — country scope

| Modifier |
|---|
| `olv_production_speed_modifier` |
| `gnss_production_speed_modifier` |
| `comsat_production_speed_modifier` |
| `spysat_production_speed_modifier` |
| `killsat_production_speed_modifier` |
| `nuclear_reactor_fuel_production` |

---

## Economy — General (`modifier_definitions.txt`) — country scope

| Modifier |
|---|
| `investment_duration_modifier` |
| `receiving_investment_duration_modifier` |
| `investment_cost_modifier` |
| `receiving_investment_cost_modifier` |
| `literacy_rate_education_modifier` |
| `internal_investment_slot_number` |

---

## Economy — Money & Industry (`money_modifier_definitions.txt`) — country scope unless noted

### Tax & Revenue
| Modifier |
|---|
| `tax_gain_multiplier_modifier` |
| `tax_rate_change_multiplier_modifier` |
| `population_tax_income_multiplier_modifier` |
| `corporate_tax_income_multiplier_modifier` |
| `return_on_investment_modifier` |
| `seigniorage_income_modifier` |
| `currency_strength_modifier` |
| `interest_rate_multiplier_modifier` |
| `office_park_income_tax_modifier` |
| `agriculture_district_income_tax_modifier` |
| `microchip_plant_income_tax_modifier` |
| `composite_plant_income_tax_modifier` |
| `synthetic_refinery_income_tax_modifier` |
| `dockyard_income_tax_modifier` |
| `military_industry_tax_modifier` |
| `civilian_industry_tax_modifier` |
| `agriculture_tax_modifier` |
| `microchip_plant_tax_modifier` |
| `composite_plant_tax_modifier` |
| `synthetic_plant_tax_modifier` |
| `infrastructure_tax_gain_multiplier_modifier` |
| `international_market_income_modifier` |

### Costs & Spending
| Modifier |
|---|
| `personnel_cost_multiplier_modifier` |
| `army_personnel_cost_multiplier_modifier` |
| `navy_personnel_cost_multiplier_modifier` |
| `airforce_personnel_cost_multiplier_modifier` |
| `equipment_cost_multiplier_modifier` |
| `bureaucracy_cost_multiplier_modifier` |
| `police_cost_multiplier_modifier` |
| `education_cost_multiplier_modifier` |
| `health_cost_multiplier_modifier` |
| `social_cost_multiplier_modifier` |
| `econ_cycle_upg_cost_multiplier_modifier` |
| `cyber_cost_multiplier_modifier` |
| `inflation_cost_multiplier_modifier` |
| `infrastructure_cost_multiplier_modifier` |
| `projects_cost_modifier` |
| `internal_investments_pp_cost_modifier` |
| `internal_investments_money_cost_modifier` |
| `international_market_purchase_modifier` |
| `border_control_multiplier_modifier` |

### Productivity
| Modifier |
|---|
| `agricolture_productivity_modifier` |
| `microchip_plant_productivity_modifier` |
| `composite_plant_productivity_modifier` |
| `synthetic_refinery_productivity_modifier` |
| `civilian_factories_productivity` |
| `military_factories_productivity` |
| `dockyard_productivity` |
| `offices_productivity` |
| `productivity_growth_modifier` |
| `country_productivity_growth_modifier` |
| `state_productivity_growth_modifier` **(state)** |

### Workforce
| Modifier |
|---|
| `total_workforce_modifier` |
| `high_unemployment_threshold_modifier` |
| `agriculture_workers_modifier` |
| `resource_sector_workers_modifier` |
| `gdp_from_resource_sector_modifier` |
| `civ_facs_worker_requirement_modifier` |
| `mil_facs_worker_requirement_modifier` |
| `offices_worker_requirement_modifier` |
| `agriculture_district_worker_requirement_modifier` |
| `microchip_plant_worker_requirement_modifier` |
| `composite_plant_worker_requirement_modifier` |
| `synthetic_refinery_worker_requirement_modifier` |
| `buildings_worker_requirement_modifier` |
| `healthcare_workforce_requirement_modifier` |
| `resource_extraction_workforce_requirement_modifier` |
| `infrastructure_workforce_requirement_modifier` |

### Exports & Trade
| Modifier |
|---|
| `resource_export_multiplier_modifier` |
| `oil_export_multiplier_modifier` |
| `steel_export_multiplier_modifier` |
| `aluminium_export_multiplier_modifier` |
| `tungsten_export_multiplier_modifier` |
| `chromium_export_multiplier_modifier` |
| `rubber_export_multiplier_modifier` |
| `microchip_export_multiplier_modifier` |
| `composite_export_multiplier_modifier` |

### Healthcare
| Modifier |
|---|
| `healthcare_income_multiplier_modifier` |

### Chip Consumption
| Modifier |
|---|
| `civilian_chip_consumption_modifier` |
| `industry_chip_consumption_modifier` |

### Outlook Campaign Costs
| Modifier |
|---|
| `salafist_outlook_campaign_cost_modifier` |
| `nonaligned_outlook_campaign_cost_modifier` |
| `western_outlook_campaign_cost_modifier` |
| `emerging_outlook_campaign_cost_modifier` |
| `nationalist_outlook_campaign_cost_modifier` |
| `propaganda_campaign_cost_modifier` |

### Misc
| Modifier |
|---|
| `un_aid_leased_civs_tracker_modifier` |

---

## Political (`political_modifier_definitions.txt`) — country scope

| Modifier |
|---|
| `popularity_attack_modifier` |
| `popularity_boost_modifier` |

---

## Country-Tag-Specific

These modifiers exist only for a single country. Only use them in content for that country.

| Modifier | Country | File |
|---|---|---|
| `CZE_skoda_superb_productivity_modifier` | CZE | `CZE_modifier_definitions.txt` |
| `ITA_ageing_population_drift_modifier` | ITA | `ITA_modifier_definitions.txt` |
| `ITA_reform_expectance_drift` | ITA | `ITA_modifier_definitions.txt` |
| `JAP_declining_birthrate_measures_modifier` | JAP | `JAP_modifier_definitions.txt` |

---

## Special

| Modifier | File | Notes |
|---|---|---|
| `mech_production_speed_multiplier_modifier` | `EH_modifier_definitions.txt` | EH mechanic |
| `randallite_resource_cost_modifier` | `EH_modifier_definitions.txt` | EH mechanic |
| `MD_auto_agency_in_progress_boolean` | `MD_auto_agency_modifier_definitions.txt` | boolean flag |