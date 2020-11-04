# Triggers

## Table of Content

* [ACE](#triggers-for-scope-ace)
* [COMBATANT](#triggers-for-scope-combatant)
* [COUNTRY](#triggers-for-scope-country)
* [OPERATION](#triggers-for-scope-operation)
* [STATE](#triggers-for-scope-state)
* [STRATEGIC_REGION](#triggers-for-scope-strategic_region)
* [UNIT_LEADER](#triggers-for-scope-unit_leader)
* [any](#triggers-for-scope-any)

## Triggers for scope ACE

* [hidden_trigger](#hidden_trigger)
* [is_female](#is_female)
* [meta_trigger](#meta_trigger)

## Triggers for scope COMBATANT

* [armor](#armor)
* [attack_skill_level](#attack_skill_level)
* [average_stats](#average_stats)
* [can_select_trait](#can_select_trait)
* [defense_skill_level](#defense_skill_level)
* [dig_in](#dig_in)
* [fastest_unit](#fastest_unit)
* [frontage_full](#frontage_full)
* [hardness](#hardness)
* [has_carrier_airwings_in_own_combat](#has_carrier_airwings_in_own_combat)
* [has_carrier_airwings_on_mission](#has_carrier_airwings_on_mission)
* [has_cavalry_ratio](#has_cavalry_ratio)
* [has_combat_modifier](#has_combat_modifier)
* [has_flanked_opponent](#has_flanked_opponent)
* [has_max_planning](#has_max_planning)
* [has_reserves](#has_reserves)
* [has_trait](#has_trait)
* [hidden_trigger](#hidden_trigger)
* [is_amphibious_invasion](#is_amphibious_invasion)
* [is_attacker](#is_attacker)
* [is_border_war](#is_border_war)
* [is_defender](#is_defender)
* [is_fighting_air_units](#is_fighting_air_units)
* [is_fighting_in_terrain](#is_fighting_in_terrain)
* [is_fighting_in_weather](#is_fighting_in_weather)
* [is_winning](#is_winning)
* [less_combat_width_than_opponent](#less_combat_width_than_opponent)
* [logistics_skill_level](#logistics_skill_level)
* [meta_trigger](#meta_trigger)
* [min_planning](#min_planning)
* [night](#night)
* [phase](#phase)
* [planning_skill_level](#planning_skill_level)
* [recon_advantage](#recon_advantage)
* [reserves](#reserves)
* [skill](#skill)
* [skill_advantage](#skill_advantage)
* [tag](#tag)
* [temperature](#temperature)

## Triggers for scope COUNTRY

* [agency_upgrade_number](#agency_upgrade_number)
* [ai_has_role_division](#ai_has_role_division)
* [ai_has_role_template](#ai_has_role_template)
* [ai_irrationality](#ai_irrationality)
* [ai_liberate_desire](#ai_liberate_desire)
* [ai_wants_divisions](#ai_wants_divisions)
* [all_allied_country](#all_allied_country)
* [all_army_leader](#all_army_leader)
* [all_controlled_state](#all_controlled_state)
* [all_enemy_country](#all_enemy_country)
* [all_guaranteed_country](#all_guaranteed_country)
* [all_navy_leader](#all_navy_leader)
* [all_neighbor_country](#all_neighbor_country)
* [all_occupied_country](#all_occupied_country)
* [all_operative_leader](#all_operative_leader)
* [all_owned_state](#all_owned_state)
* [all_unit_leader](#all_unit_leader)
* [alliance_naval_strength_ratio](#alliance_naval_strength_ratio)
* [alliance_strength_ratio](#alliance_strength_ratio)
* [amount_manpower_in_deployment_queue](#amount_manpower_in_deployment_queue)
* [amount_research_slots](#amount_research_slots)
* [amount_taken_ideas](#amount_taken_ideas)
* [any_allied_country](#any_allied_country)
* [any_army_leader](#any_army_leader)
* [any_claim](#any_claim)
* [any_controlled_state](#any_controlled_state)
* [any_enemy_country](#any_enemy_country)
* [any_guaranteed_country](#any_guaranteed_country)
* [any_home_area_neighbor_country](#any_home_area_neighbor_country)
* [any_navy_leader](#any_navy_leader)
* [any_neighbor_country](#any_neighbor_country)
* [any_occupied_country](#any_occupied_country)
* [any_operative_leader](#any_operative_leader)
* [any_owned_state](#any_owned_state)
* [any_unit_leader](#any_unit_leader)
* [any_war_score](#any_war_score)
* [army_manpower_in_state](#army_manpower_in_state)
* [can_declare_war_on](#can_declare_war_on)
* [can_research](#can_research)
* [casualties](#casualties)
* [casualties_inflicted_by](#casualties_inflicted_by)
* [casualties_k](#casualties_k)
* [civilwar_target](#civilwar_target)
* [command_power](#command_power)
* [command_power_daily](#command_power_daily)
* [compare_autonomy_progress_ratio](#compare_autonomy_progress_ratio)
* [compare_autonomy_state](#compare_autonomy_state)
* [compare_intel_with](#compare_intel_with)
* [conscription_ratio](#conscription_ratio)
* [controls_province](#controls_province)
* [controls_state](#controls_state)
* [convoy_threat](#convoy_threat)
* [core_compliance](#core_compliance)
* [core_resistance](#core_resistance)
* [current_conscription_amount](#current_conscription_amount)
* [days_since_capitulated](#days_since_capitulated)
* [decryption_progress](#decryption_progress)
* [divisions_in_border_state](#divisions_in_border_state)
* [divisions_in_state](#divisions_in_state)
* [enemies_naval_strength_ratio](#enemies_naval_strength_ratio)
* [enemies_strength_ratio](#enemies_strength_ratio)
* [estimated_intel_max_armor](#estimated_intel_max_armor)
* [estimated_intel_max_piercing](#estimated_intel_max_piercing)
* [exists](#exists)
* [focus_progress](#focus_progress)
* [foreign_manpower](#foreign_manpower)
* [fuel_ratio](#fuel_ratio)
* [garrison_manpower_need](#garrison_manpower_need)
* [get_highest_scored_country_temp](#get_highest_scored_country_temp)
* [get_sorted_scored_countries_temp](#get_sorted_scored_countries_temp)
* [gives_military_access_to](#gives_military_access_to)
* [has_active_mission](#has_active_mission)
* [has_added_tension_amount](#has_added_tension_amount)
* [has_air_experience](#has_air_experience)
* [has_allowed_idea_with_traits](#has_allowed_idea_with_traits)
* [has_annex_war_goal](#has_annex_war_goal)
* [has_any_license](#has_any_license)
* [has_army_experience](#has_army_experience)
* [has_army_manpower](#has_army_manpower)
* [has_army_size](#has_army_size)
* [has_attache](#has_attache)
* [has_attache_from](#has_attache_from)
* [has_autonomy_state](#has_autonomy_state)
* [has_available_idea_with_traits](#has_available_idea_with_traits)
* [has_border_war](#has_border_war)
* [has_border_war_with](#has_border_war_with)
* [has_built](#has_built)
* [has_capitulated](#has_capitulated)
* [has_captured_operative](#has_captured_operative)
* [has_civil_war](#has_civil_war)
* [has_collaboration](#has_collaboration)
* [has_completed_focus](#has_completed_focus)
* [has_core_occupation_modifier](#has_core_occupation_modifier)
* [has_cosmetic_tag](#has_cosmetic_tag)
* [has_country_custom_difficulty_setting](#has_country_custom_difficulty_setting)
* [has_country_flag](#has_country_flag)
* [has_country_leader](#has_country_leader)
* [has_country_leader_with_trait](#has_country_leader_with_trait)
* [has_damaged_buildings](#has_damaged_buildings)
* [has_decision](#has_decision)
* [has_defensive_war](#has_defensive_war)
* [has_defensive_war_with](#has_defensive_war_with)
* [has_deployed_air_force_size](#has_deployed_air_force_size)
* [has_done_agency_upgrade](#has_done_agency_upgrade)
* [has_dynamic_modifier](#has_dynamic_modifier)
* [has_elections](#has_elections)
* [has_equipment](#has_equipment)
* [has_finished_collecting_for_operation](#has_finished_collecting_for_operation)
* [has_focus_tree](#has_focus_tree)
* [has_fuel](#has_fuel)
* [has_full_control_of_state](#has_full_control_of_state)
* [has_government](#has_government)
* [has_guaranteed](#has_guaranteed)
* [has_idea](#has_idea)
* [has_idea_with_trait](#has_idea_with_trait)
* [has_intelligence_agency](#has_intelligence_agency)
* [has_legitimacy](#has_legitimacy)
* [has_license](#has_license)
* [has_manpower](#has_manpower)
* [has_manpower_for_recruit_change_to](#has_manpower_for_recruit_change_to)
* [has_military_access_to](#has_military_access_to)
* [has_mined](#has_mined)
* [has_mines](#has_mines)
* [has_navy_experience](#has_navy_experience)
* [has_navy_size](#has_navy_size)
* [has_non_aggression_pact_with](#has_non_aggression_pact_with)
* [has_offensive_war](#has_offensive_war)
* [has_offensive_war_with](#has_offensive_war_with)
* [has_operation_token](#has_operation_token)
* [has_opinion](#has_opinion)
* [has_opinion_modifier](#has_opinion_modifier)
* [has_political_power](#has_political_power)
* [has_relation_modifier](#has_relation_modifier)
* [has_resources_amount](#has_resources_amount)
* [has_stability](#has_stability)
* [has_subject](#has_subject)
* [has_tech](#has_tech)
* [has_tech_bonus](#has_tech_bonus)
* [has_template](#has_template)
* [has_template_ai_majority_unit](#has_template_ai_majority_unit)
* [has_template_containing_unit](#has_template_containing_unit)
* [has_template_majority_unit](#has_template_majority_unit)
* [has_unit_leader](#has_unit_leader)
* [has_volunteers_amount_from](#has_volunteers_amount_from)
* [has_war](#has_war)
* [has_war_support](#has_war_support)
* [has_war_together_with](#has_war_together_with)
* [has_war_with](#has_war_with)
* [has_wargoal_against](#has_wargoal_against)
* [hidden_trigger](#hidden_trigger)
* [ic_ratio](#ic_ratio)
* [intel_level_over](#intel_level_over)
* [is_active_decryption_bonuses_enabled](#is_active_decryption_bonuses_enabled)
* [is_ai](#is_ai)
* [is_ally_with](#is_ally_with)
* [is_cryptology_department_active](#is_cryptology_department_active)
* [is_decrypting](#is_decrypting)
* [is_exile_host](#is_exile_host)
* [is_exiled_in](#is_exiled_in)
* [is_faction_leader](#is_faction_leader)
* [is_female](#is_female)
* [is_fully_decrypted](#is_fully_decrypted)
* [is_government_in_exile](#is_government_in_exile)
* [is_guaranteed_by](#is_guaranteed_by)
* [is_hosting_exile](#is_hosting_exile)
* [is_in_faction](#is_in_faction)
* [is_in_faction_with](#is_in_faction_with)
* [is_in_peace_conference](#is_in_peace_conference)
* [is_in_tech_sharing_group](#is_in_tech_sharing_group)
* [is_justifying_wargoal_against](#is_justifying_wargoal_against)
* [is_lend_leasing](#is_lend_leasing)
* [is_licensing_any_to](#is_licensing_any_to)
* [is_licensing_to](#is_licensing_to)
* [is_major](#is_major)
* [is_neighbor_of](#is_neighbor_of)
* [is_owner_neighbor_of](#is_owner_neighbor_of)
* [is_preparing_operation](#is_preparing_operation)
* [is_puppet](#is_puppet)
* [is_puppet_of](#is_puppet_of)
* [is_researching_technology](#is_researching_technology)
* [is_running_operation](#is_running_operation)
* [is_spymaster](#is_spymaster)
* [is_staging_coup](#is_staging_coup)
* [is_subject](#is_subject)
* [is_subject_of](#is_subject_of)
* [is_target_of_coup](#is_target_of_coup)
* [land_doctrine_level](#land_doctrine_level)
* [manpower_per_military_factory](#manpower_per_military_factory)
* [meta_trigger](#meta_trigger)
* [mine_threat](#mine_threat)
* [naval_strength_comparison](#naval_strength_comparison)
* [naval_strength_ratio](#naval_strength_ratio)
* [network_national_coverage](#network_national_coverage)
* [network_strength](#network_strength)
* [num_divisions](#num_divisions)
* [num_faction_members](#num_faction_members)
* [num_fake_intel_divisions](#num_fake_intel_divisions)
* [num_finished_operations](#num_finished_operations)
* [num_free_operative_slots](#num_free_operative_slots)
* [num_occupied_states](#num_occupied_states)
* [num_of_available_civilian_factories](#num_of_available_civilian_factories)
* [num_of_available_military_factories](#num_of_available_military_factories)
* [num_of_available_naval_factories](#num_of_available_naval_factories)
* [num_of_civilian_factories](#num_of_civilian_factories)
* [num_of_civilian_factories_available_for_projects](#num_of_civilian_factories_available_for_projects)
* [num_of_controlled_states](#num_of_controlled_states)
* [num_of_factories](#num_of_factories)
* [num_of_military_factories](#num_of_military_factories)
* [num_of_naval_factories](#num_of_naval_factories)
* [num_of_nukes](#num_of_nukes)
* [num_of_operatives](#num_of_operatives)
* [num_operative_slots](#num_operative_slots)
* [num_researched_technologies](#num_researched_technologies)
* [num_subjects](#num_subjects)
* [num_tech_sharing_groups](#num_tech_sharing_groups)
* [original_research_slots](#original_research_slots)
* [original_tag](#original_tag)
* [owns_state](#owns_state)
* [political_power_daily](#political_power_daily)
* [political_power_growth](#political_power_growth)
* [received_expeditionary_forces](#received_expeditionary_forces)
* [ships_in_area](#ships_in_area)
* [ships_in_state_ports](#ships_in_state_ports)
* [stockpile_ratio](#stockpile_ratio)
* [strength_ratio](#strength_ratio)
* [surrender_progress](#surrender_progress)
* [tag](#tag)
* [target_conscription_amount](#target_conscription_amount)

## Triggers for scope OPERATION

* [all_operative_leader](#all_operative_leader)
* [any_operative_leader](#any_operative_leader)
* [hidden_trigger](#hidden_trigger)
* [is_operation_type](#is_operation_type)
* [meta_trigger](#meta_trigger)

## Triggers for scope STATE

* [all_neighbor_state](#all_neighbor_state)
* [any_neighbor_state](#any_neighbor_state)
* [any_province_building_level](#any_province_building_level)
* [area](#area)
* [compliance](#compliance)
* [compliance_speed](#compliance_speed)
* [days_since_last_strategic_bombing](#days_since_last_strategic_bombing)
* [distance_to](#distance_to)
* [free_building_slots](#free_building_slots)
* [has_active_resistance](#has_active_resistance)
* [has_border_war](#has_border_war)
* [has_border_war_with](#has_border_war_with)
* [has_claimed_state_in_peace_conference](#has_claimed_state_in_peace_conference)
* [has_dynamic_modifier](#has_dynamic_modifier)
* [has_occupation_modifier](#has_occupation_modifier)
* [has_resistance](#has_resistance)
* [has_resources_amount](#has_resources_amount)
* [has_state_category](#has_state_category)
* [has_state_flag](#has_state_flag)
* [hidden_trigger](#hidden_trigger)
* [impassable](#impassable)
* [is_border_conflict](#is_border_conflict)
* [is_capital](#is_capital)
* [is_claimed_by](#is_claimed_by)
* [is_coastal](#is_coastal)
* [is_controlled_by](#is_controlled_by)
* [is_core_of](#is_core_of)
* [is_demilitarized_zone](#is_demilitarized_zone)
* [is_fully_controlled_by](#is_fully_controlled_by)
* [is_in_home_area](#is_in_home_area)
* [is_island_state](#is_island_state)
* [is_on_continent](#is_on_continent)
* [is_owned_and_controlled_by](#is_owned_and_controlled_by)
* [is_owned_by](#is_owned_by)
* [meta_trigger](#meta_trigger)
* [non_damaged_building_level](#non_damaged_building_level)
* [num_claimed_peace_conference_neighbour_states](#num_claimed_peace_conference_neighbour_states)
* [num_owned_neighbour_states](#num_owned_neighbour_states)
* [occupation_law](#occupation_law)
* [occupied_country_tag](#occupied_country_tag)
* [region](#region)
* [resistance](#resistance)
* [resistance_speed](#resistance_speed)
* [resistance_target](#resistance_target)
* [state](#state)
* [state_and_terrain_strategic_value](#state_and_terrain_strategic_value)
* [state_population](#state_population)
* [state_population_k](#state_population_k)
* [state_strategic_value](#state_strategic_value)

## Triggers for scope STRATEGIC_REGION

* [hidden_trigger](#hidden_trigger)
* [meta_trigger](#meta_trigger)

## Triggers for scope UNIT_LEADER

* [attack_skill_level](#attack_skill_level)
* [average_stats](#average_stats)
* [can_select_trait](#can_select_trait)
* [defense_skill_level](#defense_skill_level)
* [has_ability](#has_ability)
* [has_dynamic_modifier](#has_dynamic_modifier)
* [has_id](#has_id)
* [has_nationality](#has_nationality)
* [has_trait](#has_trait)
* [has_unit_leader_flag](#has_unit_leader_flag)
* [hidden_trigger](#hidden_trigger)
* [is_assigned](#is_assigned)
* [is_border_war](#is_border_war)
* [is_exiled_leader](#is_exiled_leader)
* [is_exiled_leader_from](#is_exiled_leader_from)
* [is_female](#is_female)
* [is_field_marshal](#is_field_marshal)
* [is_leading_army](#is_leading_army)
* [is_leading_army_group](#is_leading_army_group)
* [is_operative_captured](#is_operative_captured)
* [logistics_skill_level](#logistics_skill_level)
* [meta_trigger](#meta_trigger)
* [num_units](#num_units)
* [operative_leader_mission](#operative_leader_mission)
* [operative_leader_operation](#operative_leader_operation)
* [planning_skill_level](#planning_skill_level)
* [skill](#skill)

## Triggers for scope any

* [add_to_temp_array](#add_to_temp_array)
* [add_to_temp_variable](#add_to_temp_variable)
* [all_country](#all_country)
* [all_country_with_original_tag](#all_country_with_original_tag)
* [all_of](#all_of)
* [all_of_scopes](#all_of_scopes)
* [all_other_country](#all_other_country)
* [all_state](#all_state)
* [always](#always)
* [and](#and)
* [any_country](#any_country)
* [any_country_with_original_tag](#any_country_with_original_tag)
* [any_of](#any_of)
* [any_of_scopes](#any_of_scopes)
* [any_other_country](#any_other_country)
* [any_state](#any_state)
* [check_variable](#check_variable)
* [clamp_temp_variable](#clamp_temp_variable)
* [clear_temp_array](#clear_temp_array)
* [count_triggers](#count_triggers)
* [country_exists](#country_exists)
* [custom_trigger_tooltip](#custom_trigger_tooltip)
* [date](#date)
* [difficulty](#difficulty)
* [divide_temp_variable](#divide_temp_variable)
* [find_highest_in_array](#find_highest_in_array)
* [find_lowest_in_array](#find_lowest_in_array)
* [game_rules_allow_achievements](#game_rules_allow_achievements)
* [has_any_custom_difficulty_setting](#has_any_custom_difficulty_setting)
* [has_border_war_between](#has_border_war_between)
* [has_custom_difficulty_setting](#has_custom_difficulty_setting)
* [has_dlc](#has_dlc)
* [has_event_target](#has_event_target)
* [has_game_rule](#has_game_rule)
* [has_global_flag](#has_global_flag)
* [has_rule](#has_rule)
* [has_start_date](#has_start_date)
* [has_variable](#has_variable)
* [if](#if)
* [is_debug](#is_debug)
* [is_historical_focus_on](#is_historical_focus_on)
* [is_in_array](#is_in_array)
* [is_ironman](#is_ironman)
* [is_tutorial](#is_tutorial)
* [log](#log)
* [modulo_temp_variable](#modulo_temp_variable)
* [multiply_temp_variable](#multiply_temp_variable)
* [not](#not)
* [or](#or)
* [print_variables](#print_variables)
* [remove_from_temp_array](#remove_from_temp_array)
* [resize_temp_array](#resize_temp_array)
* [round_temp_variable](#round_temp_variable)
* [set_temp_variable](#set_temp_variable)
* [set_temp_variable_to_random](#set_temp_variable_to_random)
* [subtract_from_temp_variable](#subtract_from_temp_variable)
* [threat](#threat)

## All Triggers

### add_to_temp_array

* Supported Scopes: any
* Supported Targets: none

```
Adds an element to a temporary array
Example: add_to_temp_array = {
	array = array_name
	value = 42 #optional, if not defined adds scope
	index = 3 #optional, default is end. otherwise elements are shifted
}
#shorter usage: add_to_temp_array = { array_name = 42 }
```

### add_to_temp_variable

* Supported Scopes: any
* Supported Targets: none

```
Adds a value or a variable to a temporary variable
Example: add_to_temp_variable = {
var = num_dogs
	value = 42
	tooltip = loc_str_id_with_LEFT_and_RIGHT  #localized text with LEFT and RIGHT tokens in it, tokens will replaced by values. _NOT is added to end for negative trigger
}
```

### agency_upgrade_number

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks the number of upgrade done in the intelligence agency. 
agency_upgrade_number > 4
```

### ai_has_role_division

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if the ai controlled country has any fielded divisions for a specific role
```

### ai_has_role_template

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if the ai controlled country has any template for a specific role
```

### ai_irrationality

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check the ai irrationality value
```

### ai_liberate_desire

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check what liberation desire the country has towards a specified country
```

### ai_wants_divisions

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Will compare towards the amount of divisions an ai wants to have.
```

### all_allied_country

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Check if all allied countries meet the trigger. Does not include the country itself. tooltip=key can be defined to override title
```

### all_army_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if all unit leaders meets the trigger. tooltip=key can be defined to override title
```

### all_controlled_state

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if all of the states controlled by the scope country meets the trigger. tooltip=key can be defined to override title
```

### all_country

* Supported Scopes: any
* Supported Targets: none

```
check if all countries meets the trigger. tooltip=key can be defined to override title
```

### all_country_with_original_tag

* Supported Scopes: any
* Supported Targets: none

```
check if all country with current scope's original tag meets the trigger. Example:
all_country_with_original_tag = { 
  original_tag_to_check = ENG # the trigger check all countries that has this original tag 
  # ... triggers to check 
}
```

### all_enemy_country

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if all enemy countries meet the trigger. tooltip=key can be defined to override title
```

### all_guaranteed_country

* Supported Scopes: COUNTRY
* Supported Targets: THIS

```
check if every country with current scoped country guarantees. Example:
all_country_with_original_tag = { 
  # ... triggers to check 
}
```

### all_navy_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if all unit leaders meets the trigger. tooltip=key can be defined to override title
```

### all_neighbor_country

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if all neighbor countries meet the trigger. tooltip=key can be defined to override title
```

### all_neighbor_state

* Supported Scopes: STATE
* Supported Targets: none

```
check if all neighbor states meets the trigger. tooltip=key can be defined to override title
```

### all_occupied_country

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if all occupied countries meets the trigger. tooltip=key can be defined to override title
```

### all_of

* Supported Scopes: any
* Supported Targets: any

```
Runs a loop on an array and check a trigger for each value, if any false returns false. otherwise returns true
Example: all_of = {
	array = array_name
	value = value_name #optional (default 'v') current value in array will be stored in this temp variable
	index = index_name #optional (default 'i') current index in array will be stored in this temp variable
 #trigger 1
 #trigger 2 ...
}
```

### all_of_scopes

* Supported Scopes: any
* Supported Targets: any

```
Runs a loop on an array and check a trigger for each scope in it, if any false returns false. otherwise returns true
Example: all_of_scopes = {
	array = array_name
	tooltip = loc #if defined the trigger will output tooltip using this title. loc_NOT will be used if trigger is inside a NOT
 #trigger 1
 #trigger 2 ...
}
```

### all_operative_leader

* Supported Scopes: COUNTRY, OPERATION
* Supported Targets: none

```
check if all operatives meets the trigger. tooltip=key can be defined to override title
```

### all_other_country

* Supported Scopes: any
* Supported Targets: none

```
check if all other countries meets the trigger. Excludes current country. tooltip=key can be defined to override title
```

### all_owned_state

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if all owned states meets the trigger. tooltip=key can be defined to override title
```

### all_state

* Supported Scopes: any
* Supported Targets: none

```
check if all states meets the trigger. tooltip=key can be defined to override title
```

### all_unit_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if all unit leaders meets the trigger. tooltip=key can be defined to override title
```

### alliance_naval_strength_ratio

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Compares the estimated naval strength between the scope country, his allies and his enemies.
```

### alliance_strength_ratio

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Compares the estimated army strength between the scope country, his allies and his enemies.
```

### always

* Supported Scopes: any
* Supported Targets: any

```
always returns specified value
```

### amount_manpower_in_deployment_queue

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks for amount manpower currently in deploymentview. amount_manpower_in_training > 10
```

### amount_research_slots

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check number of research current research slots 
 amount_research_slots > 2
```

### amount_taken_ideas

* Supported Scopes: COUNTRY
* Supported Targets: none

```
has current country picked specified amount of ideas. Category and slot is optional.
Excludes national_spirit, hidden, law = yes
amount_taken_ideas = {
	amount < <int> (mandatory)
	category = { military_staff } (optional)
	slot = { army_chief political_advisor } (optional)
}
```

### and

* Supported Scopes: any
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
all inside trigger must be true
```

### any_allied_country

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Check if any allied country meets the trigger. Does not include the country itself. tooltip=key can be defined to override title
```

### any_army_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if any unit leader meets the trigger. tooltip=key can be defined to override title
```

### any_claim

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check if there is a claim between a country and all others
```

### any_controlled_state

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if any of the states controlled by the scope country meets the trigger. tooltip=key can be defined to override title
```

### any_country

* Supported Scopes: any
* Supported Targets: none

```
check if any country meets the trigger
```

### any_country_with_original_tag

* Supported Scopes: any
* Supported Targets: none

```
check if any country with current scope's original tag meets the trigger. Example:
any_country_with_original_tag = { 
  original_tag_to_check = ENG # the trigger check all countries that has this original tag 
  # ... triggers to check 
}
```

### any_enemy_country

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if any enemy country meets the trigger. tooltip=key can be defined to override title
```

### any_guaranteed_country

* Supported Scopes: COUNTRY
* Supported Targets: THIS

```
check if any country with current scoped country guarantees. Example:
any_guaranteed_country = { 
  # ... triggers to check 
}
```

### any_home_area_neighbor_country

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if any neighbor country in the home area meets the trigger. tooltip=key can be defined to override title
```

### any_navy_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if any unit leader meets the trigger. tooltip=key can be defined to override title
```

### any_neighbor_country

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if any neighbor country meets the trigger. tooltip=key can be defined to override title
```

### any_neighbor_state

* Supported Scopes: STATE
* Supported Targets: none

```
check if any neighbor state meets the trigger. tooltip=key can be defined to override title
```

### any_occupied_country

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if any any occupied meets the trigger. tooltip=key can be defined to override title
```

### any_of

* Supported Scopes: any
* Supported Targets: any

```
Runs a loop on an array and check a trigger for each value, if any true returns true. otherwise returns false
Example: any_of = {
	array = array_name
	value = value_name #optional (default 'value') current value in array will be stored in this temp variable
	index = index_name #optional (default 'index') current index in array will be stored in this temp variable
 #trigger 1
 #trigger 2 ...
}
```

### any_of_scopes

* Supported Scopes: any
* Supported Targets: any

```
Runs a loop on an array and check a trigger for each scope in it, if any true returns true. otherwise returns false
Example: any_of_scopes = {
	array = array_name
	tooltip = loc #if defined the trigger will output tooltip using this title. loc_NOT will be used if trigger is inside a NOT
 #trigger 1
 #trigger 2 ...
}
```

### any_operative_leader

* Supported Scopes: COUNTRY, OPERATION
* Supported Targets: none

```
check if any operatives meets the trigger. tooltip=key can be defined to override title
```

### any_other_country

* Supported Scopes: any
* Supported Targets: none

```
check if any other country meets the trigger. Excludes current country. tooltip=key can be defined to override title
```

### any_owned_state

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if any owned state meets the trigger. tooltip=key can be defined to override title
```

### any_province_building_level

* Supported Scopes: STATE
* Supported Targets: any

```
In the current state, checks if any province within the specified limit has a building of the specified level.
```

### any_state

* Supported Scopes: any
* Supported Targets: none

```
check if any state meets the trigger. tooltip=key can be defined to override title
```

### any_unit_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if any unit leader meets the trigger. tooltip=key can be defined to override title
```

### any_war_score

* Supported Scopes: COUNTRY
* Supported Targets: none

```
compares the warscore of all wars in a country to see if any fullfills the comparison condition 0-100 - Example: any_war_score > 40
```

### area

* Supported Scopes: STATE
* Supported Targets: none

```
check state's strategic area id
```

### armor

* Supported Scopes: COMBATANT
* Supported Targets: none

```
Check that average armor level of combatant is over a certain level
```

### army_manpower_in_state

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks for amount manpower currently the target state with option to specify a type.
Example:
army_manpower_in_state = {
	state = <id> (variables supported)
	amount < <int> (variables supported)
	type > <equipment_type> (armor, infantry, etc.)
```

### attack_skill_level

* Supported Scopes: UNIT_LEADER, COMBATANT
* Supported Targets: none

```
Compares attack skill level of a unit leader.
Example: attack_skill_level > 5
```

### average_stats

* Supported Scopes: UNIT_LEADER, COMBATANT
* Supported Targets: none

```
Compares the average stats for a unit leader.
Example: average_stats > 10
```

### can_declare_war_on

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
checks if the country could potentially declare a war on the target ( according to game rules, relationship, etc... ). Example can_declare_war_on = GER
```

### can_research

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if country can research technology
```

### can_select_trait

* Supported Scopes: UNIT_LEADER, COMBATANT
* Supported Targets: none

```
check if leader can select a trait
```

### casualties

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Check the amount of casualties a country has suffered in all of it's wars
```

### casualties_inflicted_by

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Checks the casualties infliced by the speficied country to the scopped country.
E.g. true if Germany has been inflicted more than 200k casualties by Poland:
GER = {
  casualties_inflicted_by = {
    opponent = POL
    thousands > 200
  }
}
```

### casualties_k

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Check the amount of casualties in thousands a country has suffered in all of it's wars
```

### check_variable

* Supported Scopes: any
* Supported Targets: any

```
Compares a variable to a number
```

### civilwar_target

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
civilwar target is ( for civil wars checks )
```

### clamp_temp_variable

* Supported Scopes: any
* Supported Targets: none

```
clamps a temp variable between two values/variables
```

### clear_temp_array

* Supported Scopes: any
* Supported Targets: none

```
Clears the contents of a temporary array
Example: clear_temp_array = array_name
```

### command_power

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks if available command power is more or less that specified value 
 command_power > 1.5
```

### command_power_daily

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks if daily command power increase is more or less that specified value 
 command_power_daily > 1.5
```

### compare_autonomy_progress_ratio

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if autonomy progress ratio is higher than value, example:
compare_autonomy_progress_ratio > 0.5
```

### compare_autonomy_state

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if autonomy state is higher than other one, example:
compare_autonomy_state > puppet
```

### compare_intel_with

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Compare the intel of the scoped country with the specified one:
GER = {
  # is true if all predicates are satisfied
  compare_intel_with = { 
    target = POL
    civilian_intel > 0.5  # GER has at least 0.5 more civ. intel than POL
    army_intel = 0  # GER has as much army intel as POL
    navy_intel < 0  # POL has more navy intel than GER
    # airforce_intel is not specified and thus ignored in the comparison
  }
}

```

### compliance

* Supported Scopes: STATE
* Supported Targets: any

```
Compares the current compliance level of a state to a value. Example: compliance > 50 
```

### compliance_speed

* Supported Scopes: STATE
* Supported Targets: any

```
Compares the current compliance speed of a state to a value. Example: compliance_speed > 50 
```

### conscription_ratio

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks  conscription ratio of the country compared to target conscription ratio.

```

### controls_province

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check controller for province
```

### controls_state

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check controller for state(s)
```

### convoy_threat

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
A trigger to check convoy threat for a country. Controlled by NAVAL_CONVOY_DANGER defines. Returns a value between 0 and 1. Example convoy_threat > 0.5 
```

### core_compliance

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Compares the core (average of all occupied states) compliance value of occupied_country_tag that is occuppied by the country in current scope.
Example: 
core_compliance = { 
 occupied_country_tag = ITA 
 value > 35 
}
```

### core_resistance

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Compares the core (average of all occupied states) resistance value of occupied_country_tag that is occuppied by the country in current scope.
Example:
core_resistance = { 
 occupied_country_tag = ITA 
 value > 35 
}
```

### count_triggers

* Supported Scopes: any
* Supported Targets: none

```
Returns true if the specified number of sub-triggers return true
count_triggers = { amount = 2 <trigger> <trigger> <trigger> }
```

### country_exists

* Supported Scopes: any
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check if the specified country exist
```

### current_conscription_amount

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks the current conscription amount of the country.

```

### custom_trigger_tooltip

* Supported Scopes: any
* Supported Targets: none

```
Works as an and-trigger with a custom tooltip. will check if KEY_NOT first if it is inside NOT = { }
```

### date

* Supported Scopes: any
* Supported Targets: none

```
checks for a specific date
```

### days_since_capitulated

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks the number of days since the country last capitulated, even if it is no longer capitulated.
	If it has not ever capitulated, the value is extremely large.
	It is recommended to combine this with has_capitulated = yes when you specifically want to ignore non-active capitulations.
Examples:
	HOL = { has_capitulated = yes days_since_capitulated > 60 } # The Netherlands has been capitulated for more than two months
	FRA = { has_capitulated = yes days_since_capitulated < 21 } # France has capitulated sometime within the past three weeks
	GER = { OR = { has_capitulated = no days_since_capitulated > 14 } } # Germany is not both actively and recently capitulated

```

### days_since_last_strategic_bombing

* Supported Scopes: STATE
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Checks the days since last strategic bombing.
days_since_last_strategic_bombing < 10

```

### decryption_progress

* Supported Scopes: COUNTRY
* Supported Targets: none

```
checks decryption ratio against a country. Example: 
decryption_progress = { 
 target = GER
 value > 0.5
} 
#or decryption_progress@GER as variable

```

### defense_skill_level

* Supported Scopes: UNIT_LEADER, COMBATANT
* Supported Targets: none

```
Compares defense skill level of a unit leader.
Example: defense_skill_level > 5
```

### difficulty

* Supported Scopes: any
* Supported Targets: none

```
check if the difficulty is above or below specified value 0-2 (difficulty enum). Example: difficulty > 0 (above easy)
```

### dig_in

* Supported Scopes: COMBATANT
* Supported Targets: none

```
check if we have digin level (lowest)
```

### distance_to

* Supported Scopes: STATE
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check distance between two states
```

### divide_temp_variable

* Supported Scopes: any
* Supported Targets: none

```
Divies a temporary variable by a value or another variable
Example: divide_temp_variable = {
var = num_dogs
	value = 42
	tooltip = loc_str_id_with_LEFT_and_RIGHT  #localized text with LEFT and RIGHT tokens in it, tokens will replaced by values. _NOT is added to end for negative trigger
}
```

### divisions_in_border_state

* Supported Scopes: COUNTRY
* Supported Targets: none

```
checks for amount of divisions in specified state owned by current country.
```

### divisions_in_state

* Supported Scopes: COUNTRY
* Supported Targets: none

```
checks for amount of divisions in specified state owned by current country.
```

### enemies_naval_strength_ratio

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Compares the estimated navy strength between the scope country and all its enemies
```

### enemies_strength_ratio

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Compares the estimated army strength between the scope country and all its enemies
```

### estimated_intel_max_armor

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Compares estimated max armor based on intel. Example: estimated_intel_max_armor = { tag = ITA value > 1 }
```

### estimated_intel_max_piercing

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Compares estimated max armor based on intel. Example: estimated_intel_max_piercing = { tag = ITA value > 1 }
```

### exists

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Check if the current country exist. The country of the scope you are in. Example: DEN = { exists = yes }
```

### fastest_unit

* Supported Scopes: COMBATANT
* Supported Targets: none

```
check if fastest unit of combatant is over this limit
```

### find_highest_in_array

* Supported Scopes: any
* Supported Targets: any

```
Runs a loop on for each element of an array, finds the highest value and stores result in temp variables
Example: find_highest_in_array = {
	array = array_name
	value = value_name #optional (default 'v') highest value in array will be stored in this temp variable
	index = index_name #optional (default 'i') index of highest value in array will be stored in this temp variable
}
```

### find_lowest_in_array

* Supported Scopes: any
* Supported Targets: any

```
Runs a loop on for each element of an array, finds the lowest value and stores result in temp variables
Example: find_lowest_in_array = {
	array = array_name
	value = value_name #optional (default 'v') lowest value in array will be stored in this temp variable
	index = index_name #optional (default 'i') index of lowest value in array will be stored in this temp variable
}
```

### focus_progress

* Supported Scopes: COUNTRY
* Supported Targets: none

```
checks focus progress example:
 focus_progress = { focus = id progress > 0.5 }
```

### foreign_manpower

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check the amount of foreign garrison manpower we have
```

### free_building_slots

* Supported Scopes: STATE
* Supported Targets: none

```
checks building for available construction levels 
free_building_slots = { 
	building = building_type 
	size > 5 
	include_locked = yes 
	province = 42 #will check province buildings if specified 
}
```

### frontage_full

* Supported Scopes: COMBATANT
* Supported Targets: none

```
check if sides front is full or can get more reinforcements
```

### fuel_ratio

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Compares the fuel ratio to a variable.
Example: fuel_ratio > 0.5
```

### game_rules_allow_achievements

* Supported Scopes: any
* Supported Targets: none

```
Returns true if all of the active game rule options allow achievements.
```

### garrison_manpower_need

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check the amount of manpower needed by garrisons
```

### get_highest_scored_country_temp

* Supported Scopes: COUNTRY
* Supported Targets: none

```
calculates the highest scored country that is defined in a country scorer and sets it to a variable. Example: 
get_highest_scored_country_temp = { 
  scorer = scorer_id 
  var = var_name # variable name that the result will be stored. default is highest_scored_country 
}
```

### get_sorted_scored_countries_temp

* Supported Scopes: COUNTRY
* Supported Targets: none

```
calculates & sorts all countries in a country scorer and stores them and their scores in temp arrays. Example: 
get_sorted_scored_countries_temp = { 
  scorer = scorer_id # id that is used in country scorer  array = array_name # a name to store sorted countries as a temp array (default to sorted_country_list) 
  scores = array_name # corresponding score temp array for countries stored in array (default to country_list_scores) 
}
```

### gives_military_access_to

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check if country gives military access to specified country
```

### hardness

* Supported Scopes: COMBATANT
* Supported Targets: none

```
check lowest/highest hardness level on combatant
```

### has_ability

* Supported Scopes: UNIT_LEADER
* Supported Targets: any

```
does unit leader have the abilityCheck if a unit leader has the ability.
Example: has_ability = force_attack
```

### has_active_mission

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if country has an active mission with specified ID. has_active_mission = my_test_mission
```

### has_active_resistance

* Supported Scopes: STATE
* Supported Targets: any

```
returns true if state has an active resistance (above zero)
```

### has_added_tension_amount

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Compare if the country has added above or below the specified ammount of tension
```

### has_air_experience

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Compares current country's air experience with right side value.
 has_air_experience < <value>
```

### has_allowed_idea_with_traits

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks if country has allowed ideas with specific traits more than limit. Example: 
has_available_idea_with_traits = { 
	idea = head_of_intelligence # trait names. can be a list of traits in { } 
	limit = 1 
	ignore = generic_head_of_intelligence # if specified, these ideas will be ignored. can be a list of ideas in { }
} 

```

### has_annex_war_goal

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Checks a country has annex war goal on another country
```

### has_any_custom_difficulty_setting

* Supported Scopes: any
* Supported Targets: any

```
Returns true if the game has any custom difficulty on
```

### has_any_license

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Country has any active licenses
Example: has_any_license = yes
```

### has_army_experience

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Compares current country's army experience with right side value.
 has_army_experience < <value>
```

### has_army_manpower

* Supported Scopes: COUNTRY
* Supported Targets: none

```
checks for amount of manpower of selected type, additionally of a specified type
```

### has_army_size

* Supported Scopes: COUNTRY
* Supported Targets: none

```
checks for amount of divisions, additionally of a specified type
```

### has_attache

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Has attaché from any other country
```

### has_attache_from

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Has attaché from specified country
```

### has_autonomy_state

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if country currently has an autonomy state, example:
has_autonomy_state = puppet
```

### has_available_idea_with_traits

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks if country has available ideas with specific traits more than limit. Example: 
has_available_idea_with_traits = { 
	idea = head_of_intelligence # trait names. can be a list of traits in { } 
	limit = 1 
	ignore = generic_head_of_intelligence # if specified, these ideas will be ignored. can be a list of ideas in { }
} 

```

### has_border_war

* Supported Scopes: STATE, COUNTRY
* Supported Targets: any

```
Checks if a there is any border wars for country/state
```

### has_border_war_between

* Supported Scopes: any
* Supported Targets: any

```
Checks if a there is a border war between two states
```

### has_border_war_with

* Supported Scopes: STATE, COUNTRY
* Supported Targets: any

```
Checks if a there is a border against a state/country
```

### has_built

* Supported Scopes: COUNTRY
* Supported Targets: none

```
checks country has built a set number (at least) of a certain type of building since taking goal 
has_built = { 
  type = building_type 
  value = 42 
}
```

### has_capitulated

* Supported Scopes: COUNTRY
* Supported Targets: none

```
checks if the country has capitulated
```

### has_captured_operative

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Checks if a country has a captured an operative ( supports scoped variables )
has_captured_operative = GER/yes/no

```

### has_carrier_airwings_in_own_combat

* Supported Scopes: COMBATANT
* Supported Targets: none

```
Check if carrier has airplanes that are part of the current combat
```

### has_carrier_airwings_on_mission

* Supported Scopes: COMBATANT
* Supported Targets: none

```
check if side has a career with air wings on a mission
```

### has_cavalry_ratio

* Supported Scopes: COMBATANT
* Supported Targets: none

```
Check that ratio of cavalry brigades in the composition of a side of combating troops are over a certain level
```

### has_civil_war

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if participant in civil war as revolter or target
```

### has_claimed_state_in_peace_conference

* Supported Scopes: STATE
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Checks if a state has been claimed by target country in an ongoing peace conference
```

### has_collaboration

* Supported Scopes: COUNTRY
* Supported Targets: none

```
checks the collaboration in a target country with our currently scoped country. Example: 
has_collaboration = { 
 target = GER
 value > 0.5
} 
#or has_collaboration@GER as variable

```

### has_combat_modifier

* Supported Scopes: COMBATANT
* Supported Targets: none

```
check if combatant has modifier
```

### has_completed_focus

* Supported Scopes: COUNTRY
* Supported Targets: none

```
has country completed focus
```

### has_core_occupation_modifier

* Supported Scopes: COUNTRY
* Supported Targets: any

```
has an occupation modifier that applies to average resistance/compliance
Example: 
has_core_occupation_modifier = { 
 occupied_country_tag = ITA 
 modifier = token 
}
```

### has_cosmetic_tag

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks if country has specific cosmetic tag set.
Example: INS = { has_cosmetic_tag = INS1 }
```

### has_country_custom_difficulty_setting

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Returns true if the game has any custom difficulty on the scope nation
```

### has_country_flag

* Supported Scopes: COUNTRY
* Supported Targets: any

```
has country flag been set.Check flag val date set and days since set.
Example: has_country_flag = test_flag
has_country_flag = { 
	flag = <name> (mandatory)
	value < <int> (optional)
	date > <date> (optional)
	days > <int> (optional)
}
```

### has_country_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if country has leader with specified ID. Don't localize this. Tooltip only for debug.
has_country_leader = {
	id = <ID>
	ruling_only = yes/no (default = yes)
	name = <string>
}
```

### has_country_leader_with_trait

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if current country has specified trait.
has_country_leader_with_trait = big_fat_idiot
```

### has_custom_difficulty_setting

* Supported Scopes: any
* Supported Targets: any

```
Returns true if the game has the specified custom difficulty on: 
Example: has_custom_difficulty_setting = TheAxisIndustry
```

### has_damaged_buildings

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check for damaged buildings of nation
```

### has_decision

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if country has active selected decision
```

### has_defensive_war

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
is country at defensive war
```

### has_defensive_war_with

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
One country has defensive war against other country.
```

### has_deployed_air_force_size

* Supported Scopes: COUNTRY
* Supported Targets: none

```
checks for amount of aircrafts, additionally of a specified type
```

### has_dlc

* Supported Scopes: any
* Supported Targets: none

```
Checks if player has a DLC.
Example: has_dlc = "name of the dlc"
```

### has_done_agency_upgrade

* Supported Scopes: COUNTRY
* Supported Targets: none

```
has country done this intelligence agency upgrade (to its highest level)
```

### has_dynamic_modifier

* Supported Scopes: STATE, COUNTRY, UNIT_LEADER
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Checks if scope has a dynamic modifier.
has_dynamic_modifier = {
    modifier = dynamic_modifier_name
    scope = GER #optional, if the original modifier has been targeted
}

```

### has_elections

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Checks the country's politics on allowing elections. has_elections = yes
```

### has_equipment

* Supported Scopes: COUNTRY
* Supported Targets: none

```
checks for amount of equipment stored
```

### has_event_target

* Supported Scopes: any
* Supported Targets: any

```
checks if current scope or global scope has the specified event target saved
```

### has_finished_collecting_for_operation

* Supported Scopes: COUNTRY
* Supported Targets: any

```
checks if finished collecting of resources for an operation.
Example: 
has_finished_collecting_for_operation = { 
 target = ITA 
 operation = operation_infiltrate_armed_forces_navy}
```

### has_flanked_opponent

* Supported Scopes: COMBATANT
* Supported Targets: none

```
check if side has flanked their opponent
```

### has_focus_tree

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Does current country have the specified focus tree.
```

### has_fuel

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check amount of fuel
example:
has_fuel > 500
```

### has_full_control_of_state

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check controller for state(s)
```

### has_game_rule

* Supported Scopes: any
* Supported Targets: none

```
Checks if a game rule is set to a particular option.
Example:
has_game_rule = {
	rule = GER_can_remilitarize_rhineland
	option = yes
}
```

### has_global_flag

* Supported Scopes: any
* Supported Targets: any

```
has global flag been set.Check flag val date set and days since set.
Example: has_global_flag = test_flag
has_global_flag = { 
	flag = <name> (mandatory)
	value < <int> (optional)
	date > <date> (optional)
	days > <int> (optional)
}
```

### has_government

* Supported Scopes: COUNTRY
* Supported Targets: none

```
does country government (ruling party) belong to ideology group
```

### has_guaranteed

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check if country has guaranteed specified country
```

### has_id

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
check unit leader has specified ID. Don't localize this. Tooltip only for debug.
```

### has_idea

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if country has idea
```

### has_idea_with_trait

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if country has idea with specified trait
```

### has_intelligence_agency

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
has country created an Intelligence Agency
```

### has_legitimacy

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Check scope country legitimacy 0-100: Example has_legitimacy < 60
```

### has_license

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Country has specific active license
Example: has_license = {
	from = TAG # has license from this country, optional
	 #if archetype is specified equipment should not be specified
	archetype = light_tank_equipment #any armor license
	equipment = { # classical equipment reference
		type = light_tank_equipment_2
		version = 0
	}
}
```

### has_manpower

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check amount of manpower
```

### has_manpower_for_recruit_change_to

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if manpower is enough to switch recruitment laws not to be negative
```

### has_max_planning

* Supported Scopes: COMBATANT
* Supported Targets: none

```
check if side has maximal planning bonus
```

### has_military_access_to

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check country has military access to specified country
```

### has_mined

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Checks the mines planted by the country of the parent scope on the coastline of the target countryE.g. true if Germany has more than 1000 mines around Poland coast:
GER = {
  has_mined = {
    target = POL
    value > 1000
  }
}
```

### has_mines

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Checks if a region has amount of mines.
has_mines = {
    region = region_id
    amount = amount_of_mines
}

```

### has_nationality

* Supported Scopes: UNIT_LEADER
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Checks whether the operative has the specified nationality.
NOTE: this is invalid on non-operatives.
Examples:
has_nationality = GER

```

### has_navy_experience

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Compares current country's navy experience with right side value.
 has_navy_experience < <value>
```

### has_navy_size

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks for amount of ships, additionally of a specified type, archetype, or sub unit definition.

Examples:
	has_navy_size = { size > 10 type = convoy } # Must have more than 10 convoys.
	has_navy_size = { size < 1 archetype = ship_hull_light } # Must not have any ships with light hulls.
	has_navy_size = { size > 39 unit = heavy_cruiser } # Must have 40 or more heavy cruisers.
	has_navy_size = { size < 100 } # Must have fewer than 100 ships of any type.
```

### has_non_aggression_pact_with

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Check if country has non aggression pact with the specified country
```

### has_occupation_modifier

* Supported Scopes: STATE
* Supported Targets: any

```
compares occupied country that creates resistance to a tag. Example: has_occupation_modifier = modifier_name
```

### has_offensive_war

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
is country at offensive war
```

### has_offensive_war_with

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
One country has offensive war against other country.
```

### has_operation_token

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Checks if a country has a specific token against another country
has_operation_token = {
	tag = GER
	token = some_token_id
}
```

### has_opinion

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check what opinion the country has towards a specified country
```

### has_opinion_modifier

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if a country has the opinion modifier
```

### has_political_power

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check amount of political power
```

### has_relation_modifier

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Country has specified relation modifier when dealing with _target_ county
Example: has_relation_modifier = {
	target = TAG # has license from this country, optional
	modifier = static_modifier_here
	}
}
```

### has_reserves

* Supported Scopes: COMBATANT
* Supported Targets: none

```
check if side has reserves waiting
```

### has_resistance

* Supported Scopes: STATE
* Supported Targets: any

```
returns true if state has a resistance
```

### has_resources_amount

* Supported Scopes: STATE, COUNTRY
* Supported Targets: none

```
checks for amount of resources in specified state
Example:
has_resources_amount = {
	resource = chromium
	amount > 10
	delivered = no #check the delivered amount, where all modifiers apply
	state = 31 (optional - can be used in state scope instead)
```

### has_rule

* Supported Scopes: any
* Supported Targets: none

```
Checks if a rule set for a country.
Example: has_rule = can_puppet
```

### has_stability

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check value of stability 0-1: Example has_stability < 0.6
```

### has_start_date

* Supported Scopes: any
* Supported Targets: none

```
Compare the initial start date of current game.
```

### has_state_category

* Supported Scopes: STATE
* Supported Targets: none

```
Check if state has a specific state category
```

### has_state_flag

* Supported Scopes: STATE
* Supported Targets: any

```
has state flag been setCheck flag val date set and days since set.
Example: has_state_flag = test_flag
has_state_flag = { 
	flag = <name> (mandatory)
	value < <int> (optional)
	date > <date> (optional)
	days > <int> (optional)
}
```

### has_subject

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Checks if the country has for subject the given country
```

### has_tech

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if country has technology
```

### has_tech_bonus

* Supported Scopes: COUNTRY
* Supported Targets: any

```
checks if the country has a bonus for the specified technology or category
Example:
has_tech_bonus = {
	technology =  <tech>
	category = <tech cat>
	}
```

### has_template

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Check if country has a division template of specific name
```

### has_template_ai_majority_unit

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if country has a division template that is majority of specific unit using AI's priorities rather than visual
```

### has_template_containing_unit

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if country has a division template that contains a specific unit
```

### has_template_majority_unit

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if country has a division template that is majority of specific unit
```

### has_trait

* Supported Scopes: UNIT_LEADER, COMBATANT
* Supported Targets: none

```
check if sides leader has trait
```

### has_unit_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if country has unit leader with specified ID. Don't localize this. Tooltip only for debug.
```

### has_unit_leader_flag

* Supported Scopes: UNIT_LEADER
* Supported Targets: any

```
has unit leader flag been setCheck flag val date set and days since set.
Example: has_unit_leader_flag = test_flag
has_unit_leader_flag = { 
	flag = <name> (mandatory)
	value < <int> (optional)
	date > <date> (optional)
	days > <int> (optional)
}
```

### has_variable

* Supported Scopes: any
* Supported Targets: any

```
Checks if a variable exists in a scope
```

### has_volunteers_amount_from

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Compares number of volunteers from the country. Example: has_volunteers_amount_from = { tag = ITA count > 1 }
```

### has_war

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
is country at war
```

### has_war_support

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check value of war_support 0-1: Example has_war_support < 0.6
```

### has_war_together_with

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Are the countries fighting on the same side of a war
```

### has_war_with

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
is countries at war
```

### has_wargoal_against

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Checks if country has a wargoal against the target. 
Example: ENG = { has_wargoal_against = GER }
```

### hidden_trigger

* Supported Scopes: STATE, COUNTRY, UNIT_LEADER, COMBATANT, ACE, STRATEGIC_REGION, OPERATION
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
a hidden trigger, anything in it not shown in tooltips
```

### ic_ratio

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Compares the ratio of total industrial capacity between the scope country and the one set with 'tag'
```

### if

* Supported Scopes: any
* Supported Targets: none

```
if_, CIfTrigger, A conditional trigger
if = { limit = { <triggers> } <trigger> }
```

### impassable

* Supported Scopes: STATE
* Supported Targets: any

```
checks if a state is impassable
```

### intel_level_over

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Compare the absolute, percentage based, intel level the scoped country has over
the specified one:
GER = {
  # is true if all predicates are satisfied
  intel_level_over = { 
    target = POL
    civilian_intel > 0.5  # GER has more than 50% civ. intel over POL
    army_intel = 0  # GER has no army intel over POL
    navy_intel > 0  # GER has at least some navy intel over POL
    # airforce_intel is not specified and thus ignored in the comparison

    # NOTE: since we are comparing the intel level of a country over another,
    # checking for values less than 0 does not make sense
    # NOTE: since we are comparing percentages, using values greater than 1
    # does not make sense.
  }
}

```

### is_active_decryption_bonuses_enabled

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
checks if the country activated their active cipher decryption bonuses. Example is_active_decryption_bonuses_enabled = GER
```

### is_ai

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks if country is AI controlled.
```

### is_ally_with

* Supported Scopes: COUNTRY
* Supported Targets: any

```
checks if a country is ally with another country. will check if two countries are same/in same faction/has subject master relation
Example: is_ally_with = ITA 

```

### is_amphibious_invasion

* Supported Scopes: COMBATANT
* Supported Targets: none

```
check if combat is at night
```

### is_assigned

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
is_assigned = yes/no - Checks if the current unit leader is assigned to command an army/navy
```

### is_attacker

* Supported Scopes: COMBATANT
* Supported Targets: none

```
check if attacker side in combat
```

### is_border_conflict

* Supported Scopes: STATE
* Supported Targets: any

```
checks if a state is in border conflict
```

### is_border_war

* Supported Scopes: UNIT_LEADER, COMBATANT
* Supported Targets: any

```
Checks if a the combatant or leader has a border war
```

### is_capital

* Supported Scopes: STATE
* Supported Targets: none

```
Is scope state a capital. 169 = { is_capital = yes }
```

### is_claimed_by

* Supported Scopes: STATE
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Checks if state is claimed by country
```

### is_coastal

* Supported Scopes: STATE
* Supported Targets: none

```
check if state is coastal
```

### is_controlled_by

* Supported Scopes: STATE
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check if state is controlled by
```

### is_core_of

* Supported Scopes: STATE
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Checks if state is core of country
```

### is_cryptology_department_active

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
has country an active cryptology department
```

### is_debug

* Supported Scopes: any
* Supported Targets: any

```
returns true if game is in debug mode (launched with -debug argument)
```

### is_decrypting

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
checks if is currently decrypting a cipher. Example is_decrypting = GER
```

### is_defender

* Supported Scopes: COMBATANT
* Supported Targets: none

```
check if defender side in combat
```

### is_demilitarized_zone

* Supported Scopes: STATE
* Supported Targets: any

```
checks if a state is a demilitarized zone
```

### is_exile_host

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Checks if scope country is hosting an exile. is_exile_host = yes
```

### is_exiled_in

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Checks if scope country is a government in exile in target tag. is_exiled_in = ENG
```

### is_exiled_leader

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Checks if scope leader is from an exiled government. is_exiled_leader = yes
```

### is_exiled_leader_from

* Supported Scopes: UNIT_LEADER
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Checks if scope leader is from specified exiled government. is_exiled_leader_from = FRA
```

### is_faction_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if country leads a faction
```

### is_female

* Supported Scopes: COUNTRY, UNIT_LEADER, ACE
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
checks if scoped unit leader, ace or country is female
```

### is_field_marshal

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
is_field_marshal = yes/no - Checks if the current unit leader is a field marshall
```

### is_fighting_air_units

* Supported Scopes: COMBATANT
* Supported Targets: none

```
check if side is fighting air units
```

### is_fighting_in_terrain

* Supported Scopes: COMBATANT
* Supported Targets: none

```
check what terrain is in combat
```

### is_fighting_in_weather

* Supported Scopes: COMBATANT
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Checks the weather on a combat
Example:
# true if weather is artic water
is_fighting_in_weather = artic_water
# true if weather is either artic_water or snow
is_fighting_in_weather = { artic_water snow }

```

### is_fully_controlled_by

* Supported Scopes: STATE
* Supported Targets: any

```
Checks if state is fully controlled by specified tag
```

### is_fully_decrypted

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
checks if fully decrypted a cipher. Example is_fully_decrypted = GER
```

### is_government_in_exile

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Checks if scope country an exiled government. is_government_in_exile = yes
```

### is_guaranteed_by

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check if guaranteed by specified country
```

### is_historical_focus_on

* Supported Scopes: any
* Supported Targets: none

```
check if the historical focus is active
```

### is_hosting_exile

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Checks if scope country is hosting target tag as an exile. is_hosting_exile = FRA
```

### is_in_array

* Supported Scopes: any
* Supported Targets: none

```
Checks if an element is in array
Example: is_in_array = {
	array = array_name
	value = 42
}
#shorter usage: is_in_array = { array_name = 42 }
```

### is_in_faction

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if member of any faction
```

### is_in_faction_with

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check if member of same faction as specified country
```

### is_in_home_area

* Supported Scopes: STATE
* Supported Targets: any

```
Checks if the first province in the state is connected to the capital of its owner
```

### is_in_peace_conference

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks if the country is currently in a peaceconference
```

### is_in_tech_sharing_group

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks if country is member specified technology sharing group.
Example: is_in_technology_sharing_group = commonwealth_research
```

### is_ironman

* Supported Scopes: any
* Supported Targets: none

```
Check if current game is ironman.
```

### is_island_state

* Supported Scopes: STATE
* Supported Targets: any

```
always returns specified value
```

### is_justifying_wargoal_against

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Checks if country is justifying a wargoal against the target. 
Example: ENG = { is_justifying_wargoal_against = GER }
```

### is_leading_army

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
is_leading_army = yes/no - Checks if the current unit leader is leading a single army (not army group)
```

### is_leading_army_group

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
is_leading_army_group = yes/no - Checks if the current unit leader is leading an army group (not single army)
```

### is_lend_leasing

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
is lend-leasing country
```

### is_licensing_any_to

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Current country is licensing something to target country
Example: is_licensing_any_to = ENG
```

### is_licensing_to

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Country is licensing specific equipment to target. License is active
Example: is_licensing_to = {
	target = TAG # licensing to this country
	 #if archetype is specified equipment should not be specified
	archetype = light_tank_equipment #any armor license
	equipment = { # classical equipment reference
		type = light_tank_equipment_2
		version = 0
	}
}
```

### is_major

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if country is a major
```

### is_neighbor_of

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check if neighbor ( controlled territory ) with specified country
```

### is_on_continent

* Supported Scopes: STATE
* Supported Targets: none

```
is state located on continent
```

### is_operation_type

* Supported Scopes: OPERATION
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
checks the type of operation
```

### is_operative_captured

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Checks whether the operative has the matching captured status

```

### is_owned_and_controlled_by

* Supported Scopes: STATE
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check if state is owned by
```

### is_owned_by

* Supported Scopes: STATE
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check if state is owned by
```

### is_owner_neighbor_of

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check if neighbor ( owned territory ) with specified country
```

### is_preparing_operation

* Supported Scopes: COUNTRY
* Supported Targets: any

```
checks if preparing a specific operation.
Example: 
is_preparing_operation = { 
 target = ITA 
 operation = operation_infiltrate_armed_forces_navy}
```

### is_puppet

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Checks if the country is puppet of any other country
```

### is_puppet_of

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Checks if the country is puppet of specified country
```

### is_researching_technology

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks if the country is currently researching a specific technology.
Example: is_researching_technology = mechanised_infantry
```

### is_running_operation

* Supported Scopes: COUNTRY
* Supported Targets: any

```
checks if running a specific operation. operation can be ommitted to check for any operation
Example: 
is_running_operation = { 
 target = ITA 
 operation = operation_infiltrate_armed_forces_navy}
```

### is_spymaster

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check if country is Spy Master
```

### is_staging_coup

* Supported Scopes: COUNTRY
* Supported Targets: none

```
is_staging_coup = yes - Returns true if current country is staging a coup in another any country.
```

### is_subject

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Checks if the country is subject of any other country
```

### is_subject_of

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Checks if the country is subject of specified country
```

### is_target_of_coup

* Supported Scopes: COUNTRY
* Supported Targets: none

```
is_target_of_coup = yes - Returns true if current country is being targeted by a coup from any country.
```

### is_tutorial

* Supported Scopes: any
* Supported Targets: none

```
check if the tutorial is active
```

### is_winning

* Supported Scopes: COMBATANT
* Supported Targets: none

```
check if defender side in combat
```

### land_doctrine_level

* Supported Scopes: COUNTRY
* Supported Targets: none

```
checks researched land doctrine level
```

### less_combat_width_than_opponent

* Supported Scopes: COMBATANT
* Supported Targets: none

```
check if side has more combat width than their opponent
```

### log

* Supported Scopes: any
* Supported Targets: none

```
Print message to game.log - Can be localized
```

### logistics_skill_level

* Supported Scopes: UNIT_LEADER, COMBATANT
* Supported Targets: none

```
Compares logistics skill level of a unit leader.
Example: logistics_skill_level > 5
```

### manpower_per_military_factory

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Number of available manpower per factory the country has. Excluding dockyards.
manpower_per_military_factory < 1000
```

### meta_trigger

* Supported Scopes: STATE, COUNTRY, UNIT_LEADER, COMBATANT, ACE, STRATEGIC_REGION, OPERATION
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
meta triggers can be used for building triggers from strings and running them. following example will test if Germany has 42 pp:
meta_trigger = {
    text = {
        [COUNTRY] = {
            political_power > [POW]
        }
    }
    COUNTRY = "GER"
    POW = 42
    debug = no #set to yes if you want to see what game actually executes
}

```

### min_planning

* Supported Scopes: COMBATANT
* Supported Targets: none

```
check if side has maximal planning bonus
```

### mine_threat

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
A trigger to check how dangerous enemy mines are for a country. Controlled by NAVAL_MINE_DANGER defines. Returns a value between 0 and 1. Example mine_threat > 0.5 
```

### modulo_temp_variable

* Supported Scopes: any
* Supported Targets: none

```
modulos a temp variable with another. Example: 
modulo_temp_variable = { 
  var = variable_to_modulo 
  value = divisior 
}
```

### multiply_temp_variable

* Supported Scopes: any
* Supported Targets: none

```
Multiplies a temporary variable by a value or another variable
Example: multiply_temp_variable = {
var = num_dogs
	value = 42
	tooltip = loc_str_id_with_LEFT_and_RIGHT  #localized text with LEFT and RIGHT tokens in it, tokens will replaced by values. _NOT is added to end for negative trigger
}
```

### naval_strength_comparison

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Compares navies of two sides.
naval_strength_comparison = {
	other = GER # by default compares to the from scope
  tooltip = 'key' #tooltip is 'navy strength' by default, the key can be overridden if wanted 
	ratio > 1.5   # default is 1
	sub_unit_def_weights = { # if not specified, it will weigh all ships as 1. otherwise only specified sub unit types will be counted
		carrier = 1
		battleship = 2
	}
}

```

### naval_strength_ratio

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Compares the estimated navy strength between the scope country and the one set with 'tag' 
naval_strength_ratio = { 
  tag = GER 
  ratio > 0.5 
}
```

### network_national_coverage

* Supported Scopes: COUNTRY
* Supported Targets: none

```
checks network national coverage you have over a country. Example: 
network_national_coverage = { 
 target = GER
 value > 0.5
} 

```

### network_strength

* Supported Scopes: COUNTRY
* Supported Targets: none

```
checks network strength you have in a country. Examples: 
# country has a network strength greater than 50% over germany
network_strength = { 
 target = GER
 value > 50
}

# country has a network strength greater than 50% over germany in state 53
network_strength = { 
 target = GER
 state = 53 value > 50
}

# country has a network strength greater than 50% in state 53, regardless of the target
network_strength = { 
 state = 53
 value > 50
}


```

### night

* Supported Scopes: COMBATANT
* Supported Targets: none

```
check if combat is at night
```

### non_damaged_building_level

* Supported Scopes: STATE
* Supported Targets: none

```
check if a state has enough non damaged buildings


Example:
non_damaged_building_level = {
	building = arms_factory
	level = 5
}
```

### not

* Supported Scopes: any
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
negates content of trigger
```

### num_claimed_peace_conference_neighbour_states

* Supported Scopes: STATE
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Checks if a country owns the amount of states neighbouring the scoped state.
```

### num_divisions

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Will compare towards the amount of divisions a country has control over, if strength matters use has_army_size.
```

### num_faction_members

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Compares the number of members in the faction for the current country. 
 Example: num_faction_members > 10
```

### num_fake_intel_divisions

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Will compare towards the amount of fake intel divisions a country has control over. .
```

### num_finished_operations

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Compares number of completed operations.
Example: 
num_finished_operations = { 
 target = ITA 
 operation = operation_infiltrate_armed_forces_navy value > 35 
}
```

### num_free_operative_slots

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks the number of operative a country can recruit right now.
Note that this is not necessarily greater than zero if num_operative_slots returned a number greater than the number of operative.
```

### num_occupied_states

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check the number of states occupied by nation
```

### num_of_available_civilian_factories

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check amount of available civilian factories
```

### num_of_available_military_factories

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check amount of available military factories
```

### num_of_available_naval_factories

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check amount of available naval factories
```

### num_of_civilian_factories

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check amount of civilian factories
```

### num_of_civilian_factories_available_for_projects

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check amount of civilian factories available for a new project to use
```

### num_of_controlled_states

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check amount of controlled stats
```

### num_of_factories

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check amount of total factories
```

### num_of_military_factories

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check amount of military factories
```

### num_of_naval_factories

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check amount of naval factories
```

### num_of_nukes

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check amount of nukes
```

### num_of_operatives

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks the number of operatives the country controls
```

### num_operative_slots

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks the number of available operative slots a country has.
If this differs from the number of operative, this does not mean the country can recruit an operative, but that it will eventually be able to.
```

### num_owned_neighbour_states

* Supported Scopes: STATE
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Checks if a country owns the amount of states neighbouring the scoped state
```

### num_researched_technologies

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Number of researched technologies
```

### num_subjects

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check the number of subjects of nation
```

### num_tech_sharing_groups

* Supported Scopes: COUNTRY
* Supported Targets: none

```
checks how many groups a nation is a member of
```

### num_units

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Check number of units commanded by the unit leader 
 num_units > 2
```

### occupation_law

* Supported Scopes: STATE
* Supported Targets: any

```
checks occupation law of state. Example: occupation_law = brutally_oppressive_occupation
```

### occupied_country_tag

* Supported Scopes: STATE
* Supported Targets: any

```
compares occupied country that creates resistance to a tag. Example: occupied_country_tag = ITA
```

### operative_leader_mission

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Checks whether the operative is performing the given mission:
operative_leader_mission = build_intel_network
```

### operative_leader_operation

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Checks whether the operative is performing the given operation:
operative_leader_operation = operation_rescue_operative
```

### or

* Supported Scopes: any
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
at least one entry inside trigger must be true
```

### original_research_slots

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check number of research slots at start of game
```

### original_tag

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
original tag is ( for civil wars checks )
```

### owns_state

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check owner for state(s)
```

### phase

* Supported Scopes: COMBATANT
* Supported Targets: none

```
check if we are in this combat phase
```

### planning_skill_level

* Supported Scopes: UNIT_LEADER, COMBATANT
* Supported Targets: none

```
Compares planning skill level of a unit leader.
Example: planning_skill_level > 5
```

### political_power_daily

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks if daily political power increase is more or less that specified value 
 political_power_daily > 1.5
```

### political_power_growth

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Check the value of political power daily growth.Exacmple: political_power_growth > 0
```

### print_variables

* Supported Scopes: any
* Supported Targets: none

```
prints all variables in scope and temp variables to a file
Example: print_variables = {
file = log_file
text = header_text
append = yes
print_global = yes
var_list = { a b c } #optional
}
```

### received_expeditionary_forces

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Checks that the country in scope has received the specified amount of expeditionary forces from the specified country
E.g. true if Germany is commaning more than 100 expeditionary forces from Poland:
GER = {
  received_expeditionary_forces = {
    sender = POL
    value > 100
  }
}
```

### recon_advantage

* Supported Scopes: COMBATANT
* Supported Targets: none

```
checks if side has an advantage in recon level
```

### region

* Supported Scopes: STATE
* Supported Targets: none

```
check state's strategic area id
```

### remove_from_temp_array

* Supported Scopes: any
* Supported Targets: none

```
Removes an element from a temporary array using value or index
Example: remove_from_temp_array = {
	array = array_name
	value = 42 #optional, use index or this. if neither it removes last element
	index = 3 #optional, use value or this. if neither it removes last element
}
#shorter usage: remove_from_temp_array = { array_name = 42 }
```

### reserves

* Supported Scopes: COMBATANT
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
check amount of reserves
```

### resistance

* Supported Scopes: STATE
* Supported Targets: any

```
Compares the current resistance level of a state to a value. Example: resistance > 50 
```

### resistance_speed

* Supported Scopes: STATE
* Supported Targets: any

```
Compares the current resistance speed of a state to a value. Example: resistance_speed > 50 
```

### resistance_target

* Supported Scopes: STATE
* Supported Targets: any

```
Compares the target resistance level of a state to a value. Example: resistance_target > 50 
```

### resize_temp_array

* Supported Scopes: any
* Supported Targets: none

```
Resizes a temp array
Example: resize_temp_array = {
	array = array_name
	value = 42 #optional, if not specified and array grows the new elements are set to this (default 0)
	size = 3 #if higher than old size, new elements are added to end. otherwise last elements are removed to match to new size
}
#shorter usage: resize_temp_array = { array_name = 3 }
```

### round_temp_variable

* Supported Scopes: any
* Supported Targets: none

```
Rounds a temporary variable
Example: round_temp_variable = num_dogs
```

### set_temp_variable

* Supported Scopes: any
* Supported Targets: none

```
Sets a temporary variable to a value or another variable
Example: set_temp_variable = {
var = num_dogs
	value = 42
	tooltip = loc_str_id_with_LEFT_and_RIGHT  #localized text with LEFT and RIGHT tokens in it, tokens will replaced by values. _NOT is added to end for negative trigger
}
```

### set_temp_variable_to_random

* Supported Scopes: any
* Supported Targets: none

```
sets a temp variable to a random value. example 
set_temp_variable_to_random = num_dogs #sets num_dogs a random value between [0, 1) 
set_temp_variable_to_random = { 
	var = num_dogs #variable to set 
	min = 5 #default 0. value will be set in between [min, max) 
	max = 10 #default 1. value will be set in between [min, max) 
	integer = yes #default no. if yes the number value will be an integer 
} 

```

### ships_in_area

* Supported Scopes: COUNTRY
* Supported Targets: none

```
checks for amount of ships in specified area
```

### ships_in_state_ports

* Supported Scopes: COUNTRY
* Supported Targets: none

```
checks for amount of ships in specified state's ports. 
ships_in_state_ports = { 
  type = ship_category 
  state = state_id 
  size = 42 
}
```

### skill

* Supported Scopes: UNIT_LEADER, COMBATANT
* Supported Targets: none

```
compare leader skill levels
```

### skill_advantage

* Supported Scopes: COMBATANT
* Supported Targets: none

```
compare leader skill levels
```

### state

* Supported Scopes: STATE
* Supported Targets: none

```
check state id
```

### state_and_terrain_strategic_value

* Supported Scopes: STATE
* Supported Targets: none

```
Checks for state strategic value
```

### state_population

* Supported Scopes: STATE
* Supported Targets: none

```
check the population in the state
```

### state_population_k

* Supported Scopes: STATE
* Supported Targets: none

```
check the population in the state in thousands (use to avoid variable overflows)
```

### state_strategic_value

* Supported Scopes: STATE
* Supported Targets: none

```
Checks for state strategic value
```

### stockpile_ratio

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Compares the ratio of equipment archetype in stockpile vs used. a value of 2 means we have double in stockpile of what is fielded or in training.
```

### strength_ratio

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Compares the estimated army strength between the scope country and the one set with 'tag'
```

### subtract_from_temp_variable

* Supported Scopes: any
* Supported Targets: none

```
Subtracts a value or a variable to a temporary variable
Example: subtract_from_temp_variable = {
var = num_dogs
	value = 42
	tooltip = loc_str_id_with_LEFT_and_RIGHT  #localized text with LEFT and RIGHT tokens in it, tokens will replaced by values. _NOT is added to end for negative trigger
}
```

### surrender_progress

* Supported Scopes: COUNTRY
* Supported Targets: none

```
check if a country is close to surrendering
```

### tag

* Supported Scopes: COUNTRY, COMBATANT
* Supported Targets: any

```
country tag trigger
```

### target_conscription_amount

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Checks the target conscription amount of the country.

```

### temperature

* Supported Scopes: COMBATANT
* Supported Targets: none

```
check combat province temperature
```

### threat

* Supported Scopes: any
* Supported Targets: none

```
check the global threat value. 0-1 value
```

