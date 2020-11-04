# Effects

## Table of Content

* [COUNTRY](#effects-for-scope-country)
* [OPERATION](#effects-for-scope-operation)
* [STATE](#effects-for-scope-state)
* [STRATEGIC_REGION](#effects-for-scope-strategic_region)
* [UNIT_LEADER](#effects-for-scope-unit_leader)
* [any](#effects-for-scope-any)

## Effects for scope COUNTRY

* [activate_decision](#activate_decision)
* [activate_mission](#activate_mission)
* [activate_mission_tooltip](#activate_mission_tooltip)
* [activate_targeted_decision](#activate_targeted_decision)
* [add_ace](#add_ace)
* [add_ai_strategy](#add_ai_strategy)
* [add_autonomy_ratio](#add_autonomy_ratio)
* [add_autonomy_score](#add_autonomy_score)
* [add_civil_war_target](#add_civil_war_target)
* [add_collaboration](#add_collaboration)
* [add_command_power](#add_command_power)
* [add_country_leader_trait](#add_country_leader_trait)
* [add_days_mission_timeout](#add_days_mission_timeout)
* [add_days_remove](#add_days_remove)
* [add_decryption](#add_decryption)
* [add_dynamic_modifier](#add_dynamic_modifier)
* [add_equipment_production](#add_equipment_production)
* [add_equipment_to_stockpile](#add_equipment_to_stockpile)
* [add_fuel](#add_fuel)
* [add_ideas](#add_ideas)
* [add_intel](#add_intel)
* [add_legitimacy](#add_legitimacy)
* [add_manpower](#add_manpower)
* [add_mines](#add_mines)
* [add_named_threat](#add_named_threat)
* [add_nuclear_bombs](#add_nuclear_bombs)
* [add_offsite_building](#add_offsite_building)
* [add_operation_token](#add_operation_token)
* [add_opinion_modifier](#add_opinion_modifier)
* [add_political_power](#add_political_power)
* [add_popularity](#add_popularity)
* [add_relation_modifier](#add_relation_modifier)
* [add_research_slot](#add_research_slot)
* [add_resource](#add_resource)
* [add_scaled_political_power](#add_scaled_political_power)
* [add_stability](#add_stability)
* [add_state_claim](#add_state_claim)
* [add_state_core](#add_state_core)
* [add_tech_bonus](#add_tech_bonus)
* [add_threat](#add_threat)
* [add_timed_idea](#add_timed_idea)
* [add_to_faction](#add_to_faction)
* [add_to_tech_sharing_group](#add_to_tech_sharing_group)
* [add_to_war](#add_to_war)
* [add_war_support](#add_war_support)
* [ai_message](#ai_message)
* [air_experience](#air_experience)
* [annex_country](#annex_country)
* [army_experience](#army_experience)
* [become_exiled_in](#become_exiled_in)
* [capture_operative](#capture_operative)
* [clr_country_flag](#clr_country_flag)
* [complete_national_focus](#complete_national_focus)
* [country_event](#country_event)
* [country_lock_all_division_template](#country_lock_all_division_template)
* [create_corps_commander](#create_corps_commander)
* [create_country_leader](#create_country_leader)
* [create_equipment_variant](#create_equipment_variant)
* [create_faction](#create_faction)
* [create_field_marshal](#create_field_marshal)
* [create_import](#create_import)
* [create_intelligence_agency](#create_intelligence_agency)
* [create_navy_leader](#create_navy_leader)
* [create_operative_leader](#create_operative_leader)
* [create_production_license](#create_production_license)
* [create_ship](#create_ship)
* [create_wargoal](#create_wargoal)
* [declare_war_on](#declare_war_on)
* [delete_unit](#delete_unit)
* [delete_unit_template_and_units](#delete_unit_template_and_units)
* [delete_units](#delete_units)
* [destroy_ships](#destroy_ships)
* [diplomatic_relation](#diplomatic_relation)
* [dismantle_faction](#dismantle_faction)
* [division_template](#division_template)
* [drop_cosmetic_tag](#drop_cosmetic_tag)
* [effect_tooltip](#effect_tooltip)
* [end_exile](#end_exile)
* [end_puppet](#end_puppet)
* [every_army_leader](#every_army_leader)
* [every_controlled_state](#every_controlled_state)
* [every_country_with_original_tag](#every_country_with_original_tag)
* [every_enemy_country](#every_enemy_country)
* [every_navy_leader](#every_navy_leader)
* [every_neighbor_country](#every_neighbor_country)
* [every_occupied_country](#every_occupied_country)
* [every_operative](#every_operative)
* [every_owned_state](#every_owned_state)
* [every_unit_leader](#every_unit_leader)
* [force_update_dynamic_modifier](#force_update_dynamic_modifier)
* [free_operative](#free_operative)
* [free_random_operative](#free_random_operative)
* [get_highest_scored_country](#get_highest_scored_country)
* [get_highest_scored_country_temp](#get_highest_scored_country_temp)
* [get_sorted_scored_countries](#get_sorted_scored_countries)
* [get_sorted_scored_countries_temp](#get_sorted_scored_countries_temp)
* [give_guarantee](#give_guarantee)
* [give_military_access](#give_military_access)
* [give_resource_rights](#give_resource_rights)
* [global_every_army_leader](#global_every_army_leader)
* [goto_province](#goto_province)
* [hidden_effect](#hidden_effect)
* [hold_election](#hold_election)
* [inherit_technology](#inherit_technology)
* [kill_country_leader](#kill_country_leader)
* [kill_ideology_leader](#kill_ideology_leader)
* [kill_operative](#kill_operative)
* [launch_nuke](#launch_nuke)
* [leave_faction](#leave_faction)
* [load_focus_tree](#load_focus_tree)
* [load_oob](#load_oob)
* [mark_focus_tree_layout_dirty](#mark_focus_tree_layout_dirty)
* [modify_building_resources](#modify_building_resources)
* [modify_country_flag](#modify_country_flag)
* [modify_tech_sharing_bonus](#modify_tech_sharing_bonus)
* [modify_timed_idea](#modify_timed_idea)
* [navy_experience](#navy_experience)
* [news_event](#news_event)
* [print_variables](#print_variables)
* [puppet](#puppet)
* [random_army_leader](#random_army_leader)
* [random_controlled_state](#random_controlled_state)
* [random_enemy_country](#random_enemy_country)
* [random_navy_leader](#random_navy_leader)
* [random_neighbor_country](#random_neighbor_country)
* [random_occupied_country](#random_occupied_country)
* [random_operative](#random_operative)
* [random_owned_controlled_state](#random_owned_controlled_state)
* [random_owned_state](#random_owned_state)
* [random_unit_leader](#random_unit_leader)
* [recall_attache](#recall_attache)
* [recall_volunteers_from](#recall_volunteers_from)
* [release](#release)
* [release_autonomy](#release_autonomy)
* [release_on_controlled](#release_on_controlled)
* [release_puppet](#release_puppet)
* [release_puppet_on_controlled](#release_puppet_on_controlled)
* [remove_building](#remove_building)
* [remove_country_leader_trait](#remove_country_leader_trait)
* [remove_decision](#remove_decision)
* [remove_dynamic_modifier](#remove_dynamic_modifier)
* [remove_from_faction](#remove_from_faction)
* [remove_from_tech_sharing_group](#remove_from_tech_sharing_group)
* [remove_ideas](#remove_ideas)
* [remove_ideas_with_trait](#remove_ideas_with_trait)
* [remove_mission](#remove_mission)
* [remove_operation_token](#remove_operation_token)
* [remove_opinion_modifier](#remove_opinion_modifier)
* [remove_relation_modifier](#remove_relation_modifier)
* [remove_resource_rights](#remove_resource_rights)
* [remove_state_claim](#remove_state_claim)
* [remove_state_core](#remove_state_core)
* [remove_targeted_decision](#remove_targeted_decision)
* [remove_unit_leader](#remove_unit_leader)
* [reserve_dynamic_country](#reserve_dynamic_country)
* [retire_country_leader](#retire_country_leader)
* [retire_ideology_leader](#retire_ideology_leader)
* [reverse_add_opinion_modifier](#reverse_add_opinion_modifier)
* [scoped_sound_effect](#scoped_sound_effect)
* [send_equipment](#send_equipment)
* [send_equipment_fraction](#send_equipment_fraction)
* [set_autonomy](#set_autonomy)
* [set_capital](#set_capital)
* [set_collaboration](#set_collaboration)
* [set_cosmetic_tag](#set_cosmetic_tag)
* [set_country_flag](#set_country_flag)
* [set_country_leader_description](#set_country_leader_description)
* [set_country_leader_ideology](#set_country_leader_ideology)
* [set_country_leader_name](#set_country_leader_name)
* [set_country_leader_portrait](#set_country_leader_portrait)
* [set_division_template_lock](#set_division_template_lock)
* [set_equipment_fraction](#set_equipment_fraction)
* [set_faction_leader](#set_faction_leader)
* [set_faction_name](#set_faction_name)
* [set_faction_spymaster](#set_faction_spymaster)
* [set_fuel](#set_fuel)
* [set_fuel_ratio](#set_fuel_ratio)
* [set_keyed_oob](#set_keyed_oob)
* [set_legitimacy](#set_legitimacy)
* [set_major](#set_major)
* [set_naval_oob](#set_naval_oob)
* [set_oob](#set_oob)
* [set_party_name](#set_party_name)
* [set_political_party](#set_political_party)
* [set_political_power](#set_political_power)
* [set_politics](#set_politics)
* [set_popularities](#set_popularities)
* [set_province_controller](#set_province_controller)
* [set_research_slots](#set_research_slots)
* [set_rule](#set_rule)
* [set_stability](#set_stability)
* [set_state_controller](#set_state_controller)
* [set_state_owner](#set_state_owner)
* [set_technology](#set_technology)
* [set_truce](#set_truce)
* [set_war_support](#set_war_support)
* [show_ideas_tooltip](#show_ideas_tooltip)
* [start_civil_war](#start_civil_war)
* [state_event](#state_event)
* [steal_random_tech_bonus](#steal_random_tech_bonus)
* [swap_ideas](#swap_ideas)
* [swap_ruler_traits](#swap_ruler_traits)
* [transfer_navy](#transfer_navy)
* [transfer_ship](#transfer_ship)
* [transfer_state](#transfer_state)
* [transfer_units_fraction](#transfer_units_fraction)
* [turn_operative](#turn_operative)
* [unlock_decision_category_tooltip](#unlock_decision_category_tooltip)
* [unlock_decision_tooltip](#unlock_decision_tooltip)
* [unlock_national_focus](#unlock_national_focus)
* [upgrade_intelligence_agency](#upgrade_intelligence_agency)
* [white_peace](#white_peace)

## Effects for scope OPERATION

* [every_operative](#every_operative)
* [execute_operation_coordinated_strike](#execute_operation_coordinated_strike)
* [random_operative](#random_operative)

## Effects for scope STATE

* [activate_targeted_decision](#activate_targeted_decision)
* [add_building_construction](#add_building_construction)
* [add_claim_by](#add_claim_by)
* [add_compliance](#add_compliance)
* [add_core_of](#add_core_of)
* [add_dynamic_modifier](#add_dynamic_modifier)
* [add_extra_state_shared_building_slots](#add_extra_state_shared_building_slots)
* [add_manpower](#add_manpower)
* [add_province_modifier](#add_province_modifier)
* [add_resistance](#add_resistance)
* [add_resistance_target](#add_resistance_target)
* [add_resource](#add_resource)
* [add_state_modifier](#add_state_modifier)
* [cancel_resistance](#cancel_resistance)
* [clr_state_flag](#clr_state_flag)
* [damage_building](#damage_building)
* [effect_tooltip](#effect_tooltip)
* [every_neighbor_state](#every_neighbor_state)
* [force_disable_resistance](#force_disable_resistance)
* [force_enable_resistance](#force_enable_resistance)
* [force_update_dynamic_modifier](#force_update_dynamic_modifier)
* [hidden_effect](#hidden_effect)
* [modify_state_flag](#modify_state_flag)
* [print_variables](#print_variables)
* [random_neighbor_state](#random_neighbor_state)
* [remove_building](#remove_building)
* [remove_claim_by](#remove_claim_by)
* [remove_core_of](#remove_core_of)
* [remove_dynamic_modifier](#remove_dynamic_modifier)
* [remove_province_modifier](#remove_province_modifier)
* [remove_resistance_target](#remove_resistance_target)
* [remove_targeted_decision](#remove_targeted_decision)
* [reset_state_name](#reset_state_name)
* [set_border_war](#set_border_war)
* [set_building_level](#set_building_level)
* [set_compliance](#set_compliance)
* [set_demilitarized_zone](#set_demilitarized_zone)
* [set_faction_name](#set_faction_name)
* [set_garrison_strength](#set_garrison_strength)
* [set_resistance](#set_resistance)
* [set_state_category](#set_state_category)
* [set_state_flag](#set_state_flag)
* [set_state_name](#set_state_name)
* [set_state_province_controller](#set_state_province_controller)
* [start_resistance](#start_resistance)
* [state_event](#state_event)
* [teleport_armies](#teleport_armies)

## Effects for scope STRATEGIC_REGION

* [add_region_efficiency](#add_region_efficiency)

## Effects for scope UNIT_LEADER

* [add_attack](#add_attack)
* [add_coordination](#add_coordination)
* [add_defense](#add_defense)
* [add_dynamic_modifier](#add_dynamic_modifier)
* [add_logistics](#add_logistics)
* [add_maneuver](#add_maneuver)
* [add_max_trait](#add_max_trait)
* [add_nationality](#add_nationality)
* [add_planning](#add_planning)
* [add_random_trait](#add_random_trait)
* [add_skill_level](#add_skill_level)
* [add_temporary_buff_to_units](#add_temporary_buff_to_units)
* [add_timed_unit_leader_trait](#add_timed_unit_leader_trait)
* [add_unit_leader_trait](#add_unit_leader_trait)
* [boost_planning](#boost_planning)
* [capture_operative](#capture_operative)
* [clr_unit_leader_flag](#clr_unit_leader_flag)
* [demote_leader](#demote_leader)
* [force_operative_leader_into_hiding](#force_operative_leader_into_hiding)
* [force_update_dynamic_modifier](#force_update_dynamic_modifier)
* [free_operative](#free_operative)
* [gain_xp](#gain_xp)
* [harm_operative_leader](#harm_operative_leader)
* [kill_operative](#kill_operative)
* [modify_unit_leader_flag](#modify_unit_leader_flag)
* [operative_leader_event](#operative_leader_event)
* [print_variables](#print_variables)
* [promote_leader](#promote_leader)
* [remove_dynamic_modifier](#remove_dynamic_modifier)
* [remove_exile_tag](#remove_exile_tag)
* [remove_unit_leader](#remove_unit_leader)
* [remove_unit_leader_trait](#remove_unit_leader_trait)
* [replace_unit_leader_trait](#replace_unit_leader_trait)
* [retire](#retire)
* [set_leader_description](#set_leader_description)
* [set_leader_name](#set_leader_name)
* [set_leader_portrait](#set_leader_portrait)
* [set_nationality](#set_nationality)
* [set_unit_leader_flag](#set_unit_leader_flag)
* [supply_units](#supply_units)
* [turn_operative](#turn_operative)
* [unit_leader_event](#unit_leader_event)

## Effects for scope any

* [add_namespace](#add_namespace)
* [add_to_array](#add_to_array)
* [add_to_temp_array](#add_to_temp_array)
* [add_to_temp_variable](#add_to_temp_variable)
* [add_to_variable](#add_to_variable)
* [cancel_border_war](#cancel_border_war)
* [change_tag_from](#change_tag_from)
* [clamp_temp_variable](#clamp_temp_variable)
* [clamp_variable](#clamp_variable)
* [clear_array](#clear_array)
* [clear_global_event_target](#clear_global_event_target)
* [clear_global_event_targets](#clear_global_event_targets)
* [clear_temp_array](#clear_temp_array)
* [clear_variable](#clear_variable)
* [clr_global_flag](#clr_global_flag)
* [create_dynamic_country](#create_dynamic_country)
* [create_unit](#create_unit)
* [custom_effect_tooltip](#custom_effect_tooltip)
* [divide_temp_variable](#divide_temp_variable)
* [divide_variable](#divide_variable)
* [every_country](#every_country)
* [every_other_country](#every_other_country)
* [every_state](#every_state)
* [finalize_border_war](#finalize_border_war)
* [find_highest_in_array](#find_highest_in_array)
* [find_lowest_in_array](#find_lowest_in_array)
* [for_each_loop](#for_each_loop)
* [for_each_scope_loop](#for_each_scope_loop)
* [for_loop_effect](#for_loop_effect)
* [goto_state](#goto_state)
* [if](#if)
* [log](#log)
* [meta_effect](#meta_effect)
* [modify_global_flag](#modify_global_flag)
* [modulo_temp_variable](#modulo_temp_variable)
* [modulo_variable](#modulo_variable)
* [multiply_temp_variable](#multiply_temp_variable)
* [multiply_variable](#multiply_variable)
* [random](#random)
* [random_country](#random_country)
* [random_country_with_original_tag](#random_country_with_original_tag)
* [random_list](#random_list)
* [random_other_country](#random_other_country)
* [random_scope_in_array](#random_scope_in_array)
* [random_state](#random_state)
* [randomize_temp_variable](#randomize_temp_variable)
* [randomize_variable](#randomize_variable)
* [randomize_weather](#randomize_weather)
* [remove_from_array](#remove_from_array)
* [remove_from_temp_array](#remove_from_temp_array)
* [reset_province_name](#reset_province_name)
* [resize_array](#resize_array)
* [resize_temp_array](#resize_temp_array)
* [round_temp_variable](#round_temp_variable)
* [round_variable](#round_variable)
* [save_event_target_as](#save_event_target_as)
* [save_global_event_target_as](#save_global_event_target_as)
* [set_border_war_data](#set_border_war_data)
* [set_global_flag](#set_global_flag)
* [set_province_name](#set_province_name)
* [set_temp_variable](#set_temp_variable)
* [set_temp_variable_to_random](#set_temp_variable_to_random)
* [set_variable](#set_variable)
* [set_variable_to_random](#set_variable_to_random)
* [sound_effect](#sound_effect)
* [start_border_war](#start_border_war)
* [subtract_from_temp_variable](#subtract_from_temp_variable)
* [subtract_from_variable](#subtract_from_variable)
* [while_loop_effect](#while_loop_effect)

## All Effects

### activate_decision

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Activates specified decision for scope country
```

### activate_mission

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Activates mission, ignoring its normal trigger conditions. Cannot activate a mission that is already active. 
Example: activate_mission = some_mission_here
```

### activate_mission_tooltip

* Supported Scopes: COUNTRY
* Supported Targets: none

```
shows mission will activate and name. Activation needs to be handled manually, effect is just an easier way to display name of mission.
Example: unlock_mission_tooltip = some_mission_here
```

### activate_targeted_decision

* Supported Scopes: STATE, COUNTRY
* Supported Targets: none

```
Activates targeted decisions or mission, ignoring its normal trigger conditions, cooldown and fire only once. Cannot activate if active in interface. 
Example: activate_targeted_decision = { target = TAG/STATE decision = decision_id_here
```

### add_ace

* Supported Scopes: COUNTRY
* Supported Targets: none

```
adds an air ace
```

### add_ai_strategy

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Adds strategy entry to country AI
```

### add_attack

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Adds attack skill to a unit leader
Example: add_attack = 1
```

### add_autonomy_ratio

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Adds % freedom score to the autonomy.
Example:
add_autonomy_ratio={
value=0.005
localization="LOC_KEY"
}
```

### add_autonomy_score

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Adds exact freedom score to the autonomy.
Example:
add_autonomy_score={
value=50
localization="LOC_KEY"
}
```

### add_building_construction

* Supported Scopes: STATE
* Supported Targets: none

```
Starts building construction for amount of levels in specified state or province
```

### add_civil_war_target

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Adds a civil war target to a specific country
 Usage: add_civil_war_target = TAG
```

### add_claim_by

* Supported Scopes: STATE
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Add state claim by country.
```

### add_collaboration

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Adds the collaboration in a target country with our currently scoped country
GER = {
  add_collaboration = {
    target = POL
    value = 0.3
  }
}

```

### add_command_power

* Supported Scopes: COUNTRY
* Supported Targets: none

```
add command power to country
```

### add_compliance

* Supported Scopes: STATE
* Supported Targets: any

```
add compliance to a state. Example: add_compliance = 30
```

### add_coordination

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Adds maneuver skill to a unit leader
Example: add_coordination = 1
```

### add_core_of

* Supported Scopes: STATE
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Add state as core of country
```

### add_country_leader_trait

* Supported Scopes: COUNTRY
* Supported Targets: none

```
add trait to active country leader
```

### add_days_mission_timeout

* Supported Scopes: COUNTRY
* Supported Targets: none

```
add days to 'mission_timeout' value of a mission
Example:
add_days_mission_timeout  = {
    mission = <some_mission>
    days = 30
}

```

### add_days_remove

* Supported Scopes: COUNTRY
* Supported Targets: none

```
adds/removes days to 'days_remove' value of a decision
Example:
add_days_remove  = {
    decision = <some_decision>
    days = 30
}

```

### add_decryption

* Supported Scopes: COUNTRY
* Supported Targets: none

```
add decryption against a target country. Example:
add_decryption = { 
 target = GER 
 # pick one amount = 1000 # a flat amount to be added
 ratio = 0.3 # a ratio of crypto defense of target to be added

```

### add_defense

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Adds defense skill to a unit leader
Example: add_defense = 1
```

### add_dynamic_modifier

* Supported Scopes: STATE, COUNTRY, UNIT_LEADER
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
adds a dynamic modifier to country/state/unit leader. Updates the cooldown if exists:
add_dynamic_modifier = {
    modifier = dynamic_modifier_name
    days = 42 #will be temporary if specified    scope = GER #optional, state or country tag or a variable contains that. if specified the dynamic variable will target that scope
}

```

### add_equipment_production

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Adds an equipment production
```

### add_equipment_to_stockpile

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Adds equipment to the countries stockpiles. Amount can be a variable. if it is negative it will remove equipment instead. if producer tag is not specified it will remove from all creators. 
Example: add_equipment_to_stockpile = { type = strat_bomber_equipment_2 amount = 100 producer = USA }
```

### add_extra_state_shared_building_slots

* Supported Scopes: STATE
* Supported Targets: none

```
add extra shared building slot to state
```

### add_fuel

* Supported Scopes: COUNTRY
* Supported Targets: none

```
add fuel to the country
```

### add_ideas

* Supported Scopes: COUNTRY
* Supported Targets: none

```
add idea(s) to country
```

### add_intel

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Add the specified amount of intel over a specified country
GER = {
  add_intel = {
    target = POL
    civilian_intel = 3
    army_intel = 1
    # zero field can be omitted
    # navy_intel = 0
    # airforce_intel = 0
  }
}

```

### add_legitimacy

* Supported Scopes: COUNTRY
* Supported Targets: none

```
add_legitimacy = 10. Adds legitimacy to scope country. Value has to be 0-100.
```

### add_logistics

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Adds logistics skill to a unit leader
Example: add_logistics = 1
```

### add_maneuver

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Adds maneuver skill to a unit leader
Example: add_maneuver = 1
```

### add_manpower

* Supported Scopes: STATE, COUNTRY
* Supported Targets: none

```
Adds manpower to the country in scope or locally on a state if in state scope
```

### add_max_trait

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Adds a max assignable trait slot for a general
Example: add_max_trait = 1
```

### add_mines

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Add mines to a strategic region for scoped country.
 add_mines = { region = 42 mines = 100 }
```

### add_named_threat

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Adds country threat
```

### add_namespace

* Supported Scopes: any
* Supported Targets: none

```
adds new namespace
```

### add_nationality

* Supported Scopes: UNIT_LEADER
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Add the specified nationalty to the scoped-in operative. Examples:
add_nationality = ROOT
add_nationality = FRA

```

### add_nuclear_bombs

* Supported Scopes: COUNTRY
* Supported Targets: none

```
add nukes to country
```

### add_offsite_building

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Add an offsite building to a country
```

### add_operation_token

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Adds a specific token against against another country
add_operation_token = {
	tag = GER
	token = some_token_id
}
```

### add_opinion_modifier

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Add opinion modifier(s) to target(s)
```

### add_planning

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Adds planning skill to a unit leader
Example: add_planning = 1
```

### add_political_power

* Supported Scopes: COUNTRY
* Supported Targets: none

```
add political power to country
```

### add_popularity

* Supported Scopes: COUNTRY
* Supported Targets: none

```
add popularity to an ideology in a country

Example:
add_popularity = {
	ideology = neutrality
	popularity = 0.05
}
```

### add_province_modifier

* Supported Scopes: STATE
* Supported Targets: none

```
Adds static modifiers to specified province.
add_province_modifier = {
	static_modifiers = { mod_1 mod_2 }
Select 1 province:
	province = 500
Or use:
	province = {
		id = 500 id = 501 id = 502 (evaluate for specified provinces)
		all_provinces (includes all in current state)
		limit_to_coastal (only coastal provinces)
		limit_to_border (only provinces bordering different country)
		limit_to_naval_base (only provinces with a naval base)
		limit_to_victory_point (only provinces with a VP)
	}
}
```

### add_random_trait

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
add random trait from specified list to unit leader. add_random_trait = { old_guard brilliant_strategist inflexible_strategist }
```

### add_region_efficiency

* Supported Scopes: STRATEGIC_REGION
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
add efficiency factor to strategic region for from country
```

### add_relation_modifier

* Supported Scopes: COUNTRY
* Supported Targets: THIS

```
Adds a static modifier between current scope and target
Example: add_relation_modifier = {
	target = TAG # target of the relation
	modifier = static_modifier_name_here #Name of the modifier added
	}
}
```

### add_research_slot

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Adds a research slot (negative values subtracts)
```

### add_resistance

* Supported Scopes: STATE
* Supported Targets: any

```
add resistance to a state. Example: add_resistance = 30
```

### add_resistance_target

* Supported Scopes: STATE
* Supported Targets: any

```
adds resistance target to the scoped state :
add_resistance_target = 10
add_resistance_target = { 
  id = 123 #if set, id can be used for removing an added resistance target using remove_resistance_target effect  amount = 10 #original tag of new country
  occupied = GER #if set, the resistance target will only apply if the occupied country is GER
  occupier = ENG #if set, the resistance target will only apply if the occupier country is ENG
  days = 42 #if set the newly added resistance target will be only active for this many days
  tooltip = "BLABLA" #tooltip loc key to display in resistance target tooltips
}
```

### add_resource

* Supported Scopes: STATE, COUNTRY
* Supported Targets: none

```
Adds/removes resource production to state

Example:
add_resource = {
  type = steel #resource type to add/destroy  amount = 5 #amount to add
  state = 42 #can be also read from scope
  days = 60 #a resource can be added/removed temporarily}

```

### add_scaled_political_power

* Supported Scopes: COUNTRY
* Supported Targets: none

```
add political power to country scaled by the difference in IC between the receiver and another country
```

### add_skill_level

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Adds a skill level to a unit leader
Example: add_skill_level = 1
```

### add_stability

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Adds the stability to the country in scope. Example: add_stability = 5
```

### add_state_claim

* Supported Scopes: COUNTRY
* Supported Targets: none

```
add claim on state
```

### add_state_core

* Supported Scopes: COUNTRY
* Supported Targets: none

```
add core on state
```

### add_state_modifier

* Supported Scopes: STATE
* Supported Targets: none

```
Adds a modifier to the state
Example: add_state_modifier = { modifier = { local_non_core_manpower = 0.2 } }
```

### add_tech_bonus

* Supported Scopes: COUNTRY
* Supported Targets: none

```
adds a limited use tech bonus
```

### add_temporary_buff_to_units

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Add buffs to units that are belongs to the army group/navy of this unit leader
```

### add_threat

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Adds country threat
```

### add_timed_idea

* Supported Scopes: COUNTRY
* Supported Targets: none

```
add time limited idea to country idea, add_timed_idea = { idea = id days = number_of_days }
```

### add_timed_unit_leader_trait

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
add a timed trait to unit leader
```

### add_to_array

* Supported Scopes: any
* Supported Targets: none

```
Adds an element to an array
Example: add_to_array = {
	array = array_name
	value = 42 #optional, if not defined adds scope
	index = 3 #optional, default is end. otherwise elements are shifted
}
#shorter usage: add_to_array = { array_name = 42 }
```

### add_to_faction

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
adds specified country to faction
```

### add_to_tech_sharing_group

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Adds country to technology sharing group of specified name.
Example: add_to_tech_sharing_group = commonwealth_research
```

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
Adds a value or a variable to a temp variable
Example: add_to_temp_variable = {
var = num_dogs
	value = 42
	tooltip = loc_str_id_with_LEFT_and_RIGHT  #localized text with LEFT and RIGHT tokens in it, tokens will replaced by values
}
```

### add_to_variable

* Supported Scopes: any
* Supported Targets: none

```
Adds a value or a variable to another one
Example: add_to_variable = {
var = num_dogs
	value = 42
	tooltip = loc_str_id_with_LEFT_and_RIGHT  #localized text with LEFT and RIGHT tokens in it, tokens will replaced by values
}
```

### add_to_war

* Supported Scopes: COUNTRY
* Supported Targets: none

```
adds country to the specified war
```

### add_unit_leader_trait

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
add trait to unit leader
```

### add_war_support

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Adds the war support to the country in scope. Example: add_war_support = 5
```

### ai_message

* Supported Scopes: COUNTRY
* Supported Targets: none

```
ai message... ?
```

### air_experience

* Supported Scopes: COUNTRY
* Supported Targets: none

```
add air experience for country
```

### annex_country

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL
### army_experience

* Supported Scopes: COUNTRY
* Supported Targets: none

```
add army experience for country
```

### become_exiled_in

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Become exile in target nation. become_exiled_in = { target = TAG legitimacy = 0-100 (optional) }
```

### boost_planning

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Boost planning of units that are belongs to the army group/navy of this unit leader
```

### cancel_border_war

* Supported Scopes: any
* Supported Targets: none

```
cancel border war between two states
```

### cancel_resistance

* Supported Scopes: STATE
* Supported Targets: any

```
cancels resistance activity for a core country.
use along with force_disable_resistance to disable resistance forever
Example : cancel_resistance = yes
```

### capture_operative

* Supported Scopes: COUNTRY, UNIT_LEADER
* Supported Targets: THIS, ROOT, PREV, FROM

```
Capture an operative
Can be used from a scope and a target that is either a country or a unit leader.
Examples:
GER = {
    capture_operative = PREV  # where PREV is an operative (unit leader)
    # or    capture_operative = {
        operative = PREV
        ignore_death_chance = yes  # optional: whether the death chance on capture should be ignored
    }
}

capture_operative = { captured_by = GER } # where the scope is an unit leader

```

### change_tag_from

* Supported Scopes: any
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Changes player to other country
```

### clamp_temp_variable

* Supported Scopes: any
* Supported Targets: none

```
Clamps a temp variable a variable bet ween two a values or another variables
Example: clamp_temp_variable = {
var = num_dogs
min = 0
max = num_cats
}
```

### clamp_variable

* Supported Scopes: any
* Supported Targets: none

```
Clamps a variable between two values or variables.
Note that either min or max can be omitted.
The order in which the operations are applied is Max( Min( var, max ), min ).
An error will be logged if max < min as the result will be more often than not undesired (requires the game to run in debug mode).
Example: clamp_variable = {
    var = num_dogs
    min = 0
    max = num_cats
}

```

### clear_array

* Supported Scopes: any
* Supported Targets: none

```
Clears the contents of array
Example: clear_array = array_name
```

### clear_global_event_target

* Supported Scopes: any
* Supported Targets: none

```
clear a global event target
```

### clear_global_event_targets

* Supported Scopes: any
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
clear all global event targets
```

### clear_temp_array

* Supported Scopes: any
* Supported Targets: none

```
Clears the contents of a temporary array
Example: clear_temp_array = array_name
```

### clear_variable

* Supported Scopes: any
* Supported Targets: none

```
Clears a variable
Example: clear_variable = num_dogs
```

### clr_country_flag

* Supported Scopes: COUNTRY
* Supported Targets: none

```
clear country flag
```

### clr_global_flag

* Supported Scopes: any
* Supported Targets: none

```
clear global flag
```

### clr_state_flag

* Supported Scopes: STATE
* Supported Targets: none

```
clear state flag
```

### clr_unit_leader_flag

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
clear unit leader flag
```

### complete_national_focus

* Supported Scopes: COUNTRY
* Supported Targets: none

```
unlocks a focus for a country
```

### country_event

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Fires a country event.
Example:
country_event = {
	id = germany.75 # The event to fire.
	# Optional Fields:
	hours = 12 # The number of hours to wait before firing the event.
	days = 5 # The number of days to wait before firing the event.
	months = 1 # The number of months to wait before firing the event, where a month is treated as 30 days.
	# Note:  hours, days, and months can all be used and will simply be added together.
	random_hours = 18 # A random amount of hours to be added to the delay before firing, from 0 up to but not including random_hours.
	random_days = 2 # A random amount of days to be added to the delay before firing, from 0 up to but one hour less than random_days.
	# Note:  random_hours and random_days can both be used and will simply be added together.
	random = 6 # Equivalent to random_hours; preserverd for backwards compatibility.
	random = { chance = 50 ... } # Specify a set of child effects to execute as part of this effect, with a percentage chance of randomly happening or not (as a group, not individually).
	tooltip = germany.75.t # Manually specify which tooltip to use for this effect.
}

```

### country_lock_all_division_template

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Lock all the division template at the country level. Note that you need to unlock them in the same way (You can't use 'set_division_template_lock' individually, because the lock at the country level will not be removed)
```

### create_corps_commander

* Supported Scopes: COUNTRY
* Supported Targets: none

```
create corps commander for country
```

### create_country_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
creates a leader and adds it to proper party in country

Example:
create_country_leader = {
	name = "Leader Name"
	desc = "LEADER_DESC_LOCALIZATION_TAG"
	picture = "Portrait_leader_name.dds" # picture = "...." also supported for backwards compatibility
	expire = "1965.1.1"
	ideology = despotism
	traits = {
		the_director
	}
}
```

### create_dynamic_country

* Supported Scopes: any
* Supported Targets: any

```
creates a dynamic country and runs child effects on it. example :
create_dynamic_country = { 
  original_tag = ITA #original tag of new country
  copy_tag = ITA # if set, it will copy stuff from copy tag instead of original_tag
 #...effects to run on new country}
```

### create_equipment_variant

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Creates a new equipment variant.
Example:
create_equipment_variant = {
	name = "Yorktown Class"
	type = ship_hull_carrier_2
	parent_version = 1  #default = 0
	obsolete = yes      #default = no
	name_group = ship_name_group_name      #default = empty/none
	role_icon_index = 3      #default just inherits from parent or remains unset
	role_icon_index = 0      #alternative, explicitly unset
	role_icon_index = auto   #uses AI design logic to pick
	upgrades = {        #optional, inherits from parent
		ship_deckspace_upgrade = 1
		carrier_armor_upgrade = 2
	}
	modules = {         #optional, inherits from parent
		fixed_ship_deck_slot_1 = ship_deck_space
		front_1_custom_slot = ship_armor_carrier_deck
		fixed_ship_deck_slot_2 = empty #overrides parent
	}
}
```

### create_faction

* Supported Scopes: COUNTRY
* Supported Targets: none

```
create faction of specified name
```

### create_field_marshal

* Supported Scopes: COUNTRY
* Supported Targets: none

```
create field marshal for country
```

### create_import

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Creates trade between two countries
```

### create_intelligence_agency

* Supported Scopes: COUNTRY
* Supported Targets: none

```
create an Intelligence Agency for the country, if it is not already done. Example: 
create_intelligence_agency = yes # creates with historical ones, if exists. 
create_intelligence_agency = { 
  name = "M.I.B." 
  icon = "GFX_intelligence_agency_logo_ita" 
}
```

### create_navy_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
create navy leader for country
```

### create_operative_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
create operative for country
create_operative_leader = {
	bypass_recruitment = no # whether the operative is directly added to the list of available operatives 
	available_to_spy_master = yes # whether the operative can be recruited by the spy master. Only makes sense if bypass_recruitment is 'no'.
	portrait_tag_override = TAG # when selectiong the portrait for the operative, consider that tag instead of the country the operative will operate for	# Additionally supports the common token to other create_x_leader effects
}

```

### create_production_license

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Creates production license
Example: create_production_license = {
	target = TAG # target for licensing
	cost_factor = 1.0 # cost factor for the deal
	equipment = { # classical equipment reference
		type = light_tank_equipment_2
		version = 0
	}
}
```

### create_ship

* Supported Scopes: COUNTRY
* Supported Targets: none

```
create a ship from another country and assign it to the reserve fleet.
'creator' is optional. If not set, it will be the scoped country.
'name' is optional.
FRA = {
  create_ship = {
    type = ship_hull_submarine_1
    equipment_variant = "S Class"
    creator = ENG
    name = "My ship name"
  }
}

```

### create_unit

* Supported Scopes: any
* Supported Targets: none

```
Create unit effect, just like in OOB, example: 
create_unit = { 
	# unit detauls 
	division = "name = \"1. Northern Redemption Army\" division_template = \"Redemption Army\" start_experience_factor = 0.5" 
	# country to spawn unit for 
	owner = MAN 
	 
	 
	# a prov id can be specified 
	prioritize_location = 12406 
	 
	# can be set to yes to be able to spawn units on enemy provs. 
	allow_spawning_on_enemy_provs = no 
	# province controllers can be scored using this scorer. otherwise it will prio your owned provs first, friendly provs second.  
	# it will also prio provs with scores and less units firstl 
	country_score = { 
		base = 100 
		 
		modifier = { 
			tag = MAN 
			add = 100 
		} 
	} 
   count = 1 # can be specified to spawn more than one units 
   id = 42 # an id can be given to delete units later on}
```

### create_wargoal

* Supported Scopes: COUNTRY
* Supported Targets: none

```
creates wargoal for country in scope
```

### custom_effect_tooltip

* Supported Scopes: any
* Supported Targets: none

```
Shows just a custom tooltip
```

### damage_building

* Supported Scopes: STATE
* Supported Targets: any

```
Damages buildings in the current state.
Example: damage_building = { type = industrial_complex damage = 2.4 }
Also has the variable province = x when targeting provincial buildings.
```

### declare_war_on

* Supported Scopes: COUNTRY
* Supported Targets: none

```
declares war on specified country
```

### delete_unit

* Supported Scopes: COUNTRY
* Supported Targets: none

```
delete units of a country. no tooltip is generated. example: 

Example:
delete_unit = { 
	template = template_name # can be filtered a specific template 
	id = 42 # can be filtered to a given id in create unit effect 
	state = 64 # can be filtered by a given state 
	disband = yes # default is no. if set to yes the game will refund equipment/manpower
}
```

### delete_unit_template_and_units

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Delete a template and its units
Example: delete_unit_template_and_units = { 
division_template = <name> 
disband = no #if yes, will refund equipment/manpower. default is no
}
```

### delete_units

* Supported Scopes: COUNTRY
* Supported Targets: any

```
deletes units that uses a specific template :
delete_units = { 
  division_template = "Template Name"
  disband = no # if yes, equipment will be returned to country equipment. default is no
}
```

### demote_leader

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Demotes field marshal to general
```

### destroy_ships

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Destroys ships of specified country and amount
Example: 
ENG={ 
	destroy_ships = {
		type=light_cruiser
		count=all #or number
	}
}
```

### diplomatic_relation

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Set up a diplomatic relation between two nations. Example: 
diplomatic_relation = { 
	country = POR #target country
	relation = military_access #type of relation
	active = yes #yes to add relation, no to cancel existing one
}
```

### dismantle_faction

* Supported Scopes: COUNTRY
* Supported Targets: none

```
dismantle faction led by the current country
```

### divide_temp_variable

* Supported Scopes: any
* Supported Targets: none

```
Divies a temp variable to a value or another variable
Example: divide_temp_variable = {
var = num_dogs
	value = 42
	tooltip = loc_str_id_with_LEFT_and_RIGHT  #localized text with LEFT and RIGHT tokens in it, tokens will replaced by values
	if_zero = 0 # the value to assign if the divisor is zero (default is zero)
}
```

### divide_variable

* Supported Scopes: any
* Supported Targets: none

```
Divies a variable to a value or another variable
Example: divide_variable = {
var = num_dogs
	value = 42
	tooltip = loc_str_id_with_LEFT_and_RIGHT  #localized text with LEFT and RIGHT tokens in it, tokens will replaced by values
}
```

### division_template

* Supported Scopes: COUNTRY
* Supported Targets: none

```
add a division template to country
```

### drop_cosmetic_tag

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Drops country cosmetic tag.
Example: INS = { drop_cosmetic_tag }
```

### effect_tooltip

* Supported Scopes: STATE, COUNTRY
* Supported Targets: any

```
Shows just tooltip of effects
```

### end_exile

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Ends the exile of of the current scope's country
```

### end_puppet

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Stops specefied country being a puppet of current country
```

### every_army_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Executes children effects on army leaders that fulfills the "limit" trigger. tooltip=key can be added to override tooltip title
```

### every_controlled_state

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Executes children effects on every controlled state that fulfills the "limit" trigger. tooltip=key can be added to override tooltip title
```

### every_country

* Supported Scopes: any
* Supported Targets: none

```
Executes children effects on every country that fulfills the "limit" trigger. tooltip=key can be defined to override tooltip title.
```

### every_country_with_original_tag

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Executes children effects on a all countries with original tag. tooltip=key can be defined to override tooltip title. Example:
every_country_with_original_tag = { 
  original_tag_to_check = ENG # the effect will only run on countries that has this original tag 
  limit = { always = yes } # a limit can be defined to limit scopes
  # ... effects to execute 
}
```

### every_enemy_country

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Executes children effects on random enemy country that fulfills the "limit" trigger. tooltip=key can be defined to override tooltip title
```

### every_navy_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Executes children effects on navy leaders that fulfills the "limit" trigger. tooltip=key can be added to override tooltip title
```

### every_neighbor_country

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Executes children effects on every neighbor country that fulfills the "limit" trigger. tooltip=key can be defined to override tooltip title
```

### every_neighbor_state

* Supported Scopes: STATE
* Supported Targets: none

```
Executes children effects on every neighbor state that fulfills the "limit" trigger. tooltip=key can be added to override tooltip title
```

### every_occupied_country

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Executes children effects on every occupied country that fulfills the "limit" trigger. tooltip=key can be defined to override tooltip title
```

### every_operative

* Supported Scopes: COUNTRY, OPERATION
* Supported Targets: none

```
Executes children effects on operatives that fulfills the "limit" trigger. tooltip=key can be added to override tooltip title
```

### every_other_country

* Supported Scopes: any
* Supported Targets: none

```
Executes children effects on every other country that fulfills the "limit" trigger. Excludes current country. tooltip=key can be defined to override tooltip title
```

### every_owned_state

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Executes children effects on every owned state that fulfills the "limit" trigger. tooltip=key can be added to override tooltip title
```

### every_state

* Supported Scopes: any
* Supported Targets: none

```
Executes children effects on every state that fulfills the "limit" trigger. tooltip=key can be added to override tooltip title
```

### every_unit_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Executes children effects on unit leaders that fulfills the "limit" trigger. tooltip=key can be added to override tooltip title
```

### execute_operation_coordinated_strike

* Supported Scopes: OPERATION
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Special effect for executing the Coordinated Strike Operation. amount determines how often the simulation is run
```

### finalize_border_war

* Supported Scopes: any
* Supported Targets: none

```
finalizes border war between two states, wins or cancels it
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

### for_each_loop

* Supported Scopes: any
* Supported Targets: any

```
Runs a loop on for each element of an array
Example: for_each_loop = {
	array = array_name
	value = value_name #optional (default 'v') current value in array will be stored in this temp variable
	index = index_name #optional (default 'i') current index in array will be stored in this temp variable
	break = break_name #optional (default 'break') set this temp variable to non zero to break the loop
 #effect 1
 #effect 2 ...
}
```

### for_each_scope_loop

* Supported Scopes: any
* Supported Targets: any

```
Runs a loop on for each element of an array and changes scope to current element in each iteration
Example: for_each_scope_loop = {
	array = array_name
	break = break_name #optional (default 'break') set this temp variable to non zero to break the loop
	tooltip = loc #if defined, the effect will output a tooltip for sub effects using this localization as title
 #effect 1
 #effect 2 ...
}
```

### for_loop_effect

* Supported Scopes: any
* Supported Targets: any

```
Runs a same effects through a loop. example will run the effects for value_name = -3, 0, 3, 6, 9 and then terminate
Example: for_loop_effect = {
	start = -3 (default 0) start value of loop
	end = 10 (default 0) end value of loop
	compare_type = less_than_or_equals (default less_than) comparison type between start and end val
	add = 3 (default 1) value to add to current value after each iteration
	value = value_name #optional (default 'v') current value of iteration will be stored in this temp variable
	break = break_name #optional (default 'break') set this temp variable to non zero to break the loop
 #effect 1
 #effect 2 ...
}
```

### force_disable_resistance

* Supported Scopes: STATE
* Supported Targets: any

```
force disables resistance for scoped state.  :
force_disable_resistance = GER # same as occupier = GER 
force_disable_resistance = { 
  clear = no #if yes, will clear previously disabled resistance
  occupier = GER #if set, the resistance will be disabled when the occupier is GER
  occupied = ENG #if set, the resistance will be disabled if the occupier country is target
}
```

### force_enable_resistance

* Supported Scopes: STATE
* Supported Targets: any

```
force enables resistance for scoped state. the resistance will be active even if other conditions doesn't satisfy (even if it is core or resistance check trigger is false)  :
force_enable_resistance = GER # same as occupier = GER 
force_enable_resistance = { 
  clear = no #if yes, will clear previously set resistance
  occupier = GER #if set, the resistance will be enabled when the occupier is GER
  occupied = ENG #if set, the resistance will be enabled if the occupier country is target
}
```

### force_operative_leader_into_hiding

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Force an operative into hiding, preventing him from performing mission. The specified values is subject to modifiers
force_operative_leader_into_hiding = 12

```

### force_update_dynamic_modifier

* Supported Scopes: STATE, COUNTRY, UNIT_LEADER
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
updates the modifiers in current scope (use if you don't want to wait for daily update to update them):
force_update_dynamic_modifier = yes

```

### free_operative

* Supported Scopes: COUNTRY, UNIT_LEADER
* Supported Targets: THIS, ROOT, PREV, FROM

```
Free an operative
Can be used from a scope and a target that is either a country or a unit leader.
GER = { free_operative = PREV } # where PREV is an operative (unit leader)
free_operative = { captured_by = GER } # where the scope is an unit leader

```

### free_random_operative

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Free a random captured operative of a certain tag by a certain tag
Can be used from a country scope of the operative in question.
`all` is optional, default value is no - if set to yes it will free all operatives captured by the target country
GER = { free_random_operative = { all = yes captured_by = ENG } }

```

### gain_xp

* Supported Scopes: UNIT_LEADER
* Supported Targets: any

```
Grant experience to the scoped in unit leader. Cannot be used to remove experience.
The unit leader is promoted to the next skill level if applicable.
Example:
gain_xp = 5

```

### get_highest_scored_country

* Supported Scopes: COUNTRY
* Supported Targets: none

```
calculates the highest scored country that is defined in a country scorer and sets it to a temp variable. Example: 
get_highest_scored_country = { 
  scorer = scorer_id 
  var = var_name # temp variable name that the result will be stored. default is highest_scored_country 
}
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

### get_sorted_scored_countries

* Supported Scopes: COUNTRY
* Supported Targets: none

```
calculates & sorts all countries in a country scorer and stores them and their scores in arrays. Example: 
get_sorted_scored_countries = { 
  scorer = scorer_id # id that is used in country scorer  array = array_name # a name to store sorted countries as an array (default to sorted_country_list) 
  scores = array_name # corresponding score array for countries stored in array (default to country_list_scores) 
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

### give_guarantee

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
guarantees specified country
```

### give_military_access

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
gives military access to the specified country
```

### give_resource_rights

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Gives rights to take resources from specified state. give_resource_rights = { receiver = <TAG> state = <id> }
```

### global_every_army_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Executes children effects on army leaders for every country in the world that fulfills the "limit" trigger. Better to use every_army_leader if you know the country. tooltip=key can be added to override tooltip title
```

### goto_province

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Goes to stated province.
```

### goto_state

* Supported Scopes: any
* Supported Targets: none

```
Goes to stated state.
```

### harm_operative_leader

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Harm an operative. The specified value is subject to modifiers.
harm_operative_leader = 12

```

### hidden_effect

* Supported Scopes: STATE, COUNTRY
* Supported Targets: none

```
Effect not shown in tooltips
```

### hold_election

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Immediately holds an election in the target country
```

### if

* Supported Scopes: any
* Supported Targets: none

```
a conditional effect
```

### inherit_technology

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Copies over technology state from target
```

### kill_country_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
kills a country leader and removes him completely, making the next in line the new party and country leader
```

### kill_ideology_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
removes a ideology leader as leader of his party, making the next in line the new party leader
```

### kill_operative

* Supported Scopes: COUNTRY, UNIT_LEADER
* Supported Targets: THIS, ROOT, PREV, FROM

```
Kills an operative. This will temporarily lock the slot they occupy
Examples:
GER = {
    kill_operative = PREV  # where PREV is an operative (unit leader)
    # or
    kill_operative = {
        operative = PREV
    }
}

kill_operative = { killed_by = GER } # where the scope is an unit leader

```

### launch_nuke

* Supported Scopes: COUNTRY
* Supported Targets: none

```
launch nuke at a state. usage : 
launch_nuke = { 
   provinve = 42 #will nuke this province if specified
   state = 42 #use either province or state. if state is used it will prefer enemies first while picking a province to nuke. otherwise it will pick one of the neutrals
   controller = GER #if state and controller is specified, the effect will pick a province that is controlled by this tag
   use_nuke = yes #will consume nuke if specified
} 

```

### leave_faction

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Country leaves the faction
```

### load_focus_tree

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Sets what focus tree a country uses, retains finished shared focuses.
```

### load_oob

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Immediately loads an Order of Battle (OOB) file.

Example:
load_oob = "ENG_1936"
```

### log

* Supported Scopes: any
* Supported Targets: none

```
Print message to game.log, console (if visible) and history logger (if running. you can use category|log to specify a category), Can be localized
```

### mark_focus_tree_layout_dirty

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Forces the refresh of the tree layout for the scoped country
mark_focus_tree_layout_dirty = yes

```

### meta_effect

* Supported Scopes: any
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
meta effects can be used for building effects from strings and running them. following example will give Germany 42 pp:
meta_effect = {
    text = {
        [COUNTRY] = {
            add_political_power = [POW]
        }
    }
    COUNTRY = "GER"
    POW = 42
    debug = no #set to yes if you want to see what game actually executes
}

```

### modify_building_resources

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Modifies resource output of specific building for this country only
Example: modify_building_resources = {
	building = radar_station
	resource = oil
	amount = 2
}
```

### modify_country_flag

* Supported Scopes: COUNTRY
* Supported Targets: none

```
modify country flag. Only modifies if flag already exists.
Example: modify_country_flag = { flag = <name> value = <number> }
```

### modify_global_flag

* Supported Scopes: any
* Supported Targets: none

```
modify global flag. Only modifies if flag already exists.
Example: modify_global_flag = { flag = <name> value = <number> }
```

### modify_state_flag

* Supported Scopes: STATE
* Supported Targets: none

```
modify state flag. Only modifies if flag already exists.
Example: modify_state_flag = { flag = <name> value = <number> }
```

### modify_tech_sharing_bonus

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Modify country bonus for specified technology sharing group.
Example: modify_tech_sharing_bonus  = { id = commonwealth_research bonus = 0.2 }
```

### modify_timed_idea

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Modify amount of days of a timed idea.
 Example: modify_timed_idea = { idea = my_idea_id days = 5 } Adds 5 more days to the idea my_idea_id.
```

### modify_unit_leader_flag

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
modify unit leader flag. Only modifies if flag already exists.
Example: _modify_unit_leader_flag_ = { flag = <name> value = <number> }
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

### modulo_variable

* Supported Scopes: any
* Supported Targets: none

```
modulos a variable with another. Example: 
modulo_variable = { 
  var = variable_to_modulo 
  value = divisior 
}
```

### multiply_temp_variable

* Supported Scopes: any
* Supported Targets: none

```
Multiplies a temp variable to a value or another variable
Example: set_temp_variable = {
var = num_dogs
	value = 42
	tooltip = loc_str_id_with_LEFT_and_RIGHT  #localized text with LEFT and RIGHT tokens in it, tokens will replaced by values
}
```

### multiply_variable

* Supported Scopes: any
* Supported Targets: none

```
Multiplies a variable to a value or another variable
Example: set_variable = {
var = num_dogs
	value = 42
	tooltip = loc_str_id_with_LEFT_and_RIGHT  #localized text with LEFT and RIGHT tokens in it, tokens will replaced by values
}
```

### navy_experience

* Supported Scopes: COUNTRY
* Supported Targets: none

```
add naval experience for country
```

### news_event

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Fires a news event.
Example:
news_event = {
	id = news.251 # The event to fire.
	# Optional Fields:
	hours = 12 # The number of hours to wait before firing the event.
	days = 5 # The number of days to wait before firing the event.
	months = 1 # The number of months to wait before firing the event, where a month is treated as 30 days.
		# Note:  hours, days, and months can all be used and will simply be added together.
	random_hours = 18 # A random amount of hours to be added to the delay before firing, from 0 up to but not including random_hours.
	random_days = 2 # A random amount of days to be added to the delay before firing, from 0 up to but one hour less than random_days.
		# Note:  random_hours and random_days can both be used and will simply be added together.
	random = 6 # Equivalent to random_hours; preserverd for backwards compatibility.
	random = { chance = 50 ... } # Specify a set of child effects to execute as part of this effect, with a percentage chance of randomly happening or not (as a group, not individually).
	tooltip = news.251.t # Manually specify which tooltip to use for this effect.
}

```

### operative_leader_event

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Fires a operative leader event for owner country.
Example:
operative_leader_event = {
	id = generic.17 # The event to fire.
	# Optional Fields:
	originator = TAG # The originator of the event (default to the owner of the operative)
	recipient = TAG # The recipient of the event (default to the owner of the operative)
	hours = 12 # The number of hours to wait before firing the event.
	days = 5 # The number of days to wait before firing the event.
	months = 1 # The number of months to wait before firing the event, where a month is treated as 30 days.
		# Note:  hours, days, and months can all be used and will simply be added together.
	random_hours = 18 # A random amount of hours to be added to the delay before firing, from 0 up to but not including random_hours.
	random_days = 2 # A random amount of days to be added to the delay before firing, from 0 up to but one hour less than random_days.
		# Note:  random_hours and random_days can both be used and will simply be added together.
	random = 6 # Equivalent to random_hours; preserverd for backwards compatibility.
	random = { chance = 50 ... } # Specify a set of child effects to execute as part of this effect, with a percentage chance of randomly happening or not (as a group, not individually).
	tooltip = generic.17.t # Manually specify which tooltip to use for this effect.
	set_from = TAG # Set the scope of the From in the scripted localization
	set_from_from = TAG # Set the scope of the From.From in the scripted localization
	set_root = TAG # Set the scope of the Root in the scripted localization
}

```

### print_variables

* Supported Scopes: STATE, COUNTRY, UNIT_LEADER
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

### promote_leader

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
promotes general to field marshal
```

### puppet

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
puppets specified country
```

### random

* Supported Scopes: any
* Supported Targets: none

```
a random effect
```

### random_army_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Executes children effects on random army leader that fulfills the "limit" trigger.
```

### random_controlled_state

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Executes children effects on random controlled state that fulfills the "limit" trigger. 
prioritize = { <stateID> <stateID> } to pick those states first if they fulfull the limit
```

### random_country

* Supported Scopes: any
* Supported Targets: none

```
Executes children effects on random country that fulfills the "limit" trigger.
```

### random_country_with_original_tag

* Supported Scopes: any
* Supported Targets: none

```
Executes children effects on a random country with original tag. Example:
random_country_with_original_tag = { 
  original_tag_to_check = ENG # the effect will only run on countries that has this original tag 
  limit = { always = yes } # a limit can be defined to limit scopes
  # ... effects to execute 
}
```

### random_enemy_country

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Executes children effects on random enemy country that fulfills the "limit" trigger.
```

### random_list

* Supported Scopes: any
* Supported Targets: none

```
Picks a random effect from the list based on the weight associated.
The weight can be a variable valid in the current scope.
Example:
random_list = {
	# enable logging the dice role in game.log
	log = yes
	seed = var_name/const/random #if specified, it will use this seed instead of scope seed for picking a random
	# some effect with an associated weight
	10 = { add_political_power=10 }
	10 = { add_political_power=100 }
	some_var = { add_political_power=1000 }
}
```

### random_navy_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Executes children effects on random navy leader that fulfills the "limit" trigger.
```

### random_neighbor_country

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Executes children effects on random neighbor country that fulfills the "limit" trigger.
```

### random_neighbor_state

* Supported Scopes: STATE
* Supported Targets: none

```
Executes children effects on random neighbor state that fulfills the "limit" trigger.
```

### random_occupied_country

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Executes children effects on random occupied country that fulfills the "limit" trigger.
```

### random_operative

* Supported Scopes: COUNTRY, OPERATION
* Supported Targets: none

```
Executes children effects on a random operatives that fulfills the "limit" trigger.
```

### random_other_country

* Supported Scopes: any
* Supported Targets: none

```
Executes children effects on random country that fulfills the "limit" trigger. Excludes current country
```

### random_owned_controlled_state

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Executes children effects on random owned and controlled state that fulfills the "limit" trigger.
prioritize = { <stateID> <stateID> } to pick those states first if they fulfull the limit
```

### random_owned_state

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Executes children effects on random owned state that fulfills the "limit" trigger. 
prioritize = { <stateID> <stateID> } to pick those states first if they fulfull the limit
```

### random_scope_in_array

* Supported Scopes: any
* Supported Targets: any

```
Runs the effect for a random element in array
Example: random_scope_in_array = {
	array = array_name
	limit = { ... trigger ... } a trigger to limit scopes
	break = break_name #optional (default 'break') set this temp variable to non zero to break the loop
 #effect 1
 #effect 2 ...
}
```

### random_state

* Supported Scopes: any
* Supported Targets: none

```
Executes children effects on a random state that fulfills the "limit" trigger.
State ids can be specified with the "prioritize" attribute and they will be
picked first if they fulfill the trigger.

```

### random_unit_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Executes children effects on random unit leader that fulfills the "limit" trigger.
```

### randomize_temp_variable

* Supported Scopes: any
* Supported Targets: none

```
Randomize a temporary variable
randomize_temp_variable = num_dogs
# which is equivalient to
randomize_temp_variable = {
  var = num_dogs
  distribution = uniform
}
# which is equivalent to
randomize_temp_variable = {
  var = num_dogs
  distribution = uniform
  min = 0
  max = 1
}
# also allow for binomial distribution (with N=2)randomize_temp_variable = {
  var = num_dogs
  distribution = binomial
  min = 0               # optional
  max = 10              # required if min is specified
}
# also allow for the poisson distributionrandomize_temp_variable = {
  var = num_dogs
  distribution = poisson
  lambda = 10           # required
  min = 10              # optional
}

```

### randomize_variable

* Supported Scopes: any
* Supported Targets: none

```
refer to randomize_temp_variable
```

### randomize_weather

* Supported Scopes: any
* Supported Targets: any

```
Randomize weather effect
```

### recall_attache

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Scope country recalls attache from target country. Example: GER = { recall_attache = CHI } means Germany recalls attache from China.
```

### recall_volunteers_from

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
The scoped in country recall the volunteers sent to the target country.
Example:
# FRA recalls the volunteers it sent to SPR
FRA = { recall_volunteers_from = SPR }

```

### release

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
releases specified country as a puppet using your owned states
```

### release_autonomy

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
releases specified country with specified level of autonomy.
Example:
ENG = { 
 release_autonomy = { 
  target = RAJ 
  autonomy_state = autonomy_puppet 
  freedom_level = 0.5 
  release_non_owned_controlled = yes # default no. if yes you will release states you only control as well  force_change_controller_for_non_ally_controlled = yes # default = no. if yes it will change the controller of the states you or your allies don't control (ie if an enemy occupying it, the ownership will change but not controller) }
}
```

### release_on_controlled

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
releases specified country as a puppet using your owned or controlled states
```

### release_puppet

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
releases specified country as puppet using states you own
```

### release_puppet_on_controlled

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
releases specified country as puppet using states you own or control
```

### remove_building

* Supported Scopes: STATE, COUNTRY
* Supported Targets: none

```
Removes specified building in specified state or province
```

### remove_claim_by

* Supported Scopes: STATE
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Removes state claim by country.
```

### remove_core_of

* Supported Scopes: STATE
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Removes state as core of country
```

### remove_country_leader_trait

* Supported Scopes: COUNTRY
* Supported Targets: none

```
remove trait from active country leader
```

### remove_decision

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Remove specified active decision for scope country - Does not run the remove_effect or put the decision on cooldown. Ignores fire_only_once
```

### remove_dynamic_modifier

* Supported Scopes: STATE, COUNTRY, UNIT_LEADER
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
removes a dynamic modifier from country/state/unit leader:
remove_dynamic_modifier = {
    modifier = dynamic_modifier_name
    scope = GER #optional, specify if it is specified while adding the modifier
}

```

### remove_exile_tag

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
remove exile tag from scope unit leader. remove_exile_tag = yes
```

### remove_from_array

* Supported Scopes: any
* Supported Targets: none

```
Removes an element from an array using value or index
Example: remove_from_array = {
	array = array_name
	value = 42 #optional, use index or this. if neither it removes last element
	index = 3 #optional, use value or this. if neither it removes last element
}
#shorter usage: remove_from_array = { array_name = 42 }
```

### remove_from_faction

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
removes specified country from faction
```

### remove_from_tech_sharing_group

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Removes country from technology sharing group of specified name.
Example: remove_from_tech_sharing_group = commonwealth_research
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

### remove_ideas

* Supported Scopes: COUNTRY
* Supported Targets: none

```
remove idea(s) from country
```

### remove_ideas_with_trait

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Remove all ideas with specified trait from country
```

### remove_mission

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Removes mission without running complete or timeout effects. 
Example: remove_mission = some_mission_here
```

### remove_operation_token

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Remove a specific token against against another country
remove_operation_token = {
	tag = GER
	token = some_token_id
}
```

### remove_opinion_modifier

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Remove opinion modifier from target
```

### remove_province_modifier

* Supported Scopes: STATE
* Supported Targets: none

```
Removes a static modifiers to specified province
remove_province_modifier = {
	static_modifiers = { mod_1 mod_2 }
Select 1 province:
	province = 500
Or use:
	province = {
		id = 500 id = 501 id = 502 (evaluate for specified provinces)
		all_provinces (includes all in current state)
		limit_to_coastal (only coastal provinces)
		limit_to_border (only provinces bordering different country)
		limit_to_naval_base (only provinces with a naval base)
		limit_to_victory_point (only provinces with a VP)
	}
}
```

### remove_relation_modifier

* Supported Scopes: COUNTRY
* Supported Targets: THIS

```
Removes a static modifier between current scope and target
Example: add_relation_modifier = {
	target = TAG # target of the relation
	modifier = static_modifier_name_here #Name of the modifier added
	}
}
```

### remove_resistance_target

* Supported Scopes: STATE
* Supported Targets: any

```
removes a previously added resistance target using its id. No tooltips are generated.:
remove_resistance_target = 42

```

### remove_resource_rights

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Remove resource right to state for scope country. remove_resource_rights = ID
```

### remove_state_claim

* Supported Scopes: COUNTRY
* Supported Targets: none

```
remove claim on state
```

### remove_state_core

* Supported Scopes: COUNTRY
* Supported Targets: none

```
remove core on state
```

### remove_targeted_decision

* Supported Scopes: STATE, COUNTRY
* Supported Targets: none

```
Removes targeted decisions or mission. 
Example: remove_targeted_decision = { target = TAG decision = decision_id_here
```

### remove_unit_leader

* Supported Scopes: COUNTRY, UNIT_LEADER
* Supported Targets: none

```
remove a unit leader ( remove_unit_leader=ID )
```

### remove_unit_leader_trait

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
remove trait from unit leader
```

### replace_unit_leader_trait

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
add trait to unit leader
```

### reserve_dynamic_country

* Supported Scopes: COUNTRY
* Supported Targets: any

```
reserves a dynamic country so it won't be recycled for civil wars. A dynamic country with no owned states must be reserved after it is created and unreserved once it is no longer going to be used. example :
reserve_dynamic_country = yes
reserve_dynamic_country = no

```

### reset_province_name

* Supported Scopes: any
* Supported Targets: none

```
reset name of a province back to localization one.
```

### reset_state_name

* Supported Scopes: STATE
* Supported Targets: none

```
reset_state_name = yes - Resets the current states name to the original one
```

### resize_array

* Supported Scopes: any
* Supported Targets: none

```
Resizes array
Example: resize_array = {
	array = array_name
	value = 42 #optional, if not specified and array grows the new elements are set to this (default 0)
	size = 3 #if higher than old size, new elements are added to end. otherwise last elements are removed to match to new size
}
#shorter usage: resize_array = { array_name = 3 }
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

### retire

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Retires scope unit leader
```

### retire_country_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
retires a country leader and removes him as leader of his party, making the next in line the new party and country leader
```

### retire_ideology_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
kills a ideology leader and removes him completely, making the next in line the new party leader
```

### reverse_add_opinion_modifier

* Supported Scopes: COUNTRY
* Supported Targets: any

```
Add opinion modifier(s) to target(s)
```

### round_temp_variable

* Supported Scopes: any
* Supported Targets: none

```
Rounds a temporary variable
Example: round_temp_variable = num_dogs
```

### round_variable

* Supported Scopes: any
* Supported Targets: none

```
Rounds a variable
Example: round_variable = num_dogs
```

### save_event_target_as

* Supported Scopes: any
* Supported Targets: none

```
save an event target
```

### save_global_event_target_as

* Supported Scopes: any
* Supported Targets: none

```
save a global event target
```

### scoped_sound_effect

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Plays sound effect only on in current scope's player
```

### send_equipment

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Sends to target scope specified amount of equipment.
```

### send_equipment_fraction

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Sends to target scope specified fraction of equipment.
_send_equipment_fraction_ = {
  target = FROM
  value = 0.3    # clamped in code to the range [0,1]
}
```

### set_autonomy

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
makes autonomy of specified level and country.
Example:
set_autonomy = {
target=ENG
autonomy_state = nautonomy_puppet
freedom_level=0.5
}
```

### set_border_war

* Supported Scopes: STATE
* Supported Targets: none

```
starts a border war in a state with neighbouring state that also has border war
```

### set_border_war_data

* Supported Scopes: any
* Supported Targets: none

```
update border war properties
```

### set_building_level

* Supported Scopes: STATE
* Supported Targets: none

```
Sets specific level of a building construction for amount of levels in specified state or province
```

### set_capital

* Supported Scopes: COUNTRY
* Supported Targets: none

```
move capital to state
```

### set_collaboration

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Sets the collaboration in a target country with our currently scoped country
GER = {
  set_collaboration = {
    target = POL
    value = 0.3
  }
}

```

### set_compliance

* Supported Scopes: STATE
* Supported Targets: any

```
set compliance of a state. Example: set_compliance = 30
```

### set_cosmetic_tag

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Sets country cosmetic tag.
Example: INS = { set_cosmetic_tag = IN1 }
```

### set_country_flag

* Supported Scopes: COUNTRY
* Supported Targets: none

```
set country flag
```

### set_country_leader_description

* Supported Scopes: COUNTRY
* Supported Targets: any

```
changes the description of country leader. no tooltip is generated
set_country_leader_name = {
  ideology = neutrality # can be ommitted. if so it will change the portrait of current ruler
  desc = "DESC_KEY"
}
```

### set_country_leader_ideology

* Supported Scopes: COUNTRY
* Supported Targets: none

```
change the ideology of active leader
```

### set_country_leader_name

* Supported Scopes: COUNTRY
* Supported Targets: any

```
changes the name of country leader. no tooltip is generated
set_country_leader_name = {
  ideology = neutrality # can be ommitted. if so it will change the name of current ruler
  name = "James Boned"
}
```

### set_country_leader_portrait

* Supported Scopes: COUNTRY
* Supported Targets: any

```
changes the portrait of country leader. no tooltip is generated
set_country_leader_name = {
  ideology = neutrality # can be ommitted. if so it will change the portrait of current ruler
  portrait = "GFX_portrait_italy_emperor_mussolini"
}
```

### set_demilitarized_zone

* Supported Scopes: STATE
* Supported Targets: none

```
sets the demilitarized status for currently scoped state
```

### set_division_template_lock

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Set lock status for a division template
Example: set_division_template_lock = { division_template = <name> is_locked = <bool (default:true)> }
```

### set_equipment_fraction

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Modify all equipments by factor
```

### set_faction_leader

* Supported Scopes: COUNTRY
* Supported Targets: none

```
set current country as leader of its faction
```

### set_faction_name

* Supported Scopes: STATE, COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
set_faction_name = NEW_LOC_KEY. Sets the faction name to whatever the new key localises to.
```

### set_faction_spymaster

* Supported Scopes: COUNTRY
* Supported Targets: none

```
set current country as spy master of its faction
```

### set_fuel

* Supported Scopes: COUNTRY
* Supported Targets: none

```
set fuel for country
```

### set_fuel_ratio

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Set country's current fuel ratio relative to its capacity
```

### set_garrison_strength

* Supported Scopes: STATE
* Supported Targets: any

```
set initial garrison strength. Example: set_garrison_strength = 0.5
```

### set_global_flag

* Supported Scopes: any
* Supported Targets: none

```
set global flag
```

### set_keyed_oob

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Registers an Order of Battle (OOB) file to be loaded for a country at game start, replacing any previously registered OOB (with the given key) on that country.
Only intended to be used within history files.

Example:
set_keyed_oob = {
	key = naval
	name = "ENG_1936_Naval"
}
```

### set_leader_description

* Supported Scopes: UNIT_LEADER
* Supported Targets: any

```
changes the description of unit leader. no tooltip is generated
set_leader_description = "DESC_KEY"

```

### set_leader_name

* Supported Scopes: UNIT_LEADER
* Supported Targets: any

```
changes the name of unit leader. no tooltip is generated
set_leader_name = "James Boned"

```

### set_leader_portrait

* Supported Scopes: UNIT_LEADER
* Supported Targets: any

```
changes the portrait of unit leader. no tooltip is generated
set_leader_portrait = "GFX_portrait_italy_emperor_mussolini"

```

### set_legitimacy

* Supported Scopes: COUNTRY
* Supported Targets: none

```
set_legitimacy = 10. Sets legitimacy on scope country to specified value. Value has to be 0-100.
```

### set_major

* Supported Scopes: COUNTRY
* Supported Targets: none

```
sets mandatory major country flag
```

### set_nationality

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Set the new country owner for the scoped in unit leader.
Note that this is not related to operative nationalities added via add_nationality.
Note that for operative, this will temporarily lock their slot on the country of origin.

```

### set_naval_oob

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Registers an Order of Battle (OOB) file to be loaded for a country at game start, replacing any previously registered OOB (with key "naval") on that country.
Only intended to be used within history files.

Example:
set_naval_oob = "ENG_1936_Naval"
```

### set_oob

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Registers an Order of Battle (OOB) file to be loaded for a country at game start, replacing any previously registered OOB (with no key) on that country.
Only intended to be used within history files.

Example:
set_oob = "ENG_1936"
```

### set_party_name

* Supported Scopes: COUNTRY
* Supported Targets: none

```
change partyname for an ideology in a country
```

### set_political_party

* Supported Scopes: COUNTRY
* Supported Targets: none

```
set popularity of a political party

Example:
set_political_party = {
	ideology = neutrality
	popularity = 50
}
```

### set_political_power

* Supported Scopes: COUNTRY
* Supported Targets: none

```
set political power for country
```

### set_politics

* Supported Scopes: COUNTRY
* Supported Targets: none

```
set country political status
```

### set_popularities

* Supported Scopes: COUNTRY
* Supported Targets: none

```
set popularities for all ideologies in a country. If an ideology is not specified its popularity will be set to zero. The popularities specified must add up to exactly 100

Example:
set_popularities = {
	neutrality = 54.5
	fascism = 45.5
}
```

### set_province_controller

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
set controller for province
```

### set_province_name

* Supported Scopes: any
* Supported Targets: none

```
set_province_name = { id = <province id> name = <string> } - Set name for a province
```

### set_research_slots

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Sets the number of research slots
```

### set_resistance

* Supported Scopes: STATE
* Supported Targets: any

```
set resistance of a state. Example: set_resistance = 30
```

### set_rule

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Adds rule to country
```

### set_stability

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Sets the stability to the country in scope. Example: set_stability = 80
```

### set_state_category

* Supported Scopes: STATE
* Supported Targets: none

```
Sets the category of a state
Example: set_state_category = large_town
```

### set_state_controller

* Supported Scopes: COUNTRY
* Supported Targets: none

```
set controller for state
```

### set_state_flag

* Supported Scopes: STATE
* Supported Targets: none

```
set state flag
```

### set_state_name

* Supported Scopes: STATE
* Supported Targets: none

```
set_state_name = <string> - Set the current states name
```

### set_state_owner

* Supported Scopes: COUNTRY
* Supported Targets: none

```
set owner for state
```

### set_state_province_controller

* Supported Scopes: STATE
* Supported Targets: any

```
sets the controller of provinces belong to a state and fullfils a condition. no tooltip is built
set_state_province_controller = { 
 controller = ITA
  limit = { 
     # will be checked old controller of each province. will only update controller if true
  } 
}
```

### set_technology

* Supported Scopes: COUNTRY
* Supported Targets: none

```
sets technology level(s) on country. example : set_technology = { 
	infantry_weapons = 1 
	infantry_weapons1 = 1 
	infantry_weapons2 = 1 
	improved_infantry_weapons = 1 
	popup = no # default is yes. if set to no, no pop up will display for player 
}
```

### set_temp_variable

* Supported Scopes: any
* Supported Targets: none

```
Sets a temp variable to a value or another variable
Example: set_temp_variable = {
var = num_dogs
	value = 42
	tooltip = loc_str_id_with_LEFT_and_RIGHT  #localized text with LEFT and RIGHT tokens in it, tokens will replaced by values
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

### set_truce

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Sets a truce between scope country and target for days duration. 
Example set_truce = { target = GER days = 90 }
```

### set_unit_leader_flag

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
set unit leader flag
```

### set_variable

* Supported Scopes: any
* Supported Targets: none

```
Sets a variable to a value or another variable
Example: set_variable = {
var = num_dogs
	value = 42
	tooltip = loc_str_id_with_LEFT_and_RIGHT  #localized text with LEFT and RIGHT tokens in it, tokens will replaced by values
}
```

### set_variable_to_random

* Supported Scopes: any
* Supported Targets: none

```
sets a variable to a random value. example 
set_variable_to_random = num_dogs #sets num_dogs a random value between [0, 1) 
set_variable_to_random = { 
	var = num_dogs #variable to set 
	min = 5 #default 0. value will be set in between [min, max) 
	max = 10 #default 1. value will be set in between [min, max) 
	integer = yes #default no. if yes the number value will be an integer 
} 

```

### set_war_support

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Sets the war support to the country in scope. Example: set_war_support = 80
```

### show_ideas_tooltip

* Supported Scopes: COUNTRY
* Supported Targets: none

```
show what idea does
```

### sound_effect

* Supported Scopes: any
* Supported Targets: none

```
Plays sound effect
```

### start_border_war

* Supported Scopes: any
* Supported Targets: none

```
start a border war between two states. Example:
start_border_war = {
	change_state_after_war = no #overrides the transfer of state at the end of war
	combat_width = 80 #combat width for border war
	minimum_duration_in_days = 14 #minimum duration for combat
	attacker = {
		state = 527 # state to start border war
		num_provinces = 4 #number of provinces we want border war to be
		on_win = japan_border_conflict.2 #effect to call if wins
		on_lose = japan_border_conflict.3 #effect to call if loses
		on_cancel = japan_border_conflict.4 #effect to call if cancels
		leader_score = { #score for selecting a leader
			base = 1
			modifier = {
				check_variable = { likes_border_wars = 1 }
				add = 2
			}
		}
		modifier = 0.5 #combat modifier
		dig_in_factor = 0.5 #dig in modifier factor
		terrain_factor = 0.5 #terrain modifier factor
	}
	
	defender = {
		state = 408 # state to start border war
		num_provinces = 4 #number of provinces we want border war to be
		on_win = japan_border_conflict.2 #effect to call if wins
		on_lose = japan_border_conflict.3 #effect to call if loses
		on_cancel = japan_border_conflict.4 #effect to call if cancels
	}
}

```

### start_civil_war

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Given ideology starts a civil war in the country.
start_civil_war = {
	ideology = revolting ideology
	ruling party = ruling party for country
	size = 0-1 Size modifier of the revolt. Affects stockpile, army, air and navy as well
	army_ratio = 0-1 Overrides size modifier for army
	navy_ratio = 0-1 Overrides size modifier for navy
	air_ratio = 0-1 Overrides size modifier for air
	keep_unit_leaders specify ID of unit leaders that remain with the original country
	keep_unit_leaders_trigger Trigger for unit leaders to remain with the original country
	states States that go to the revolter. Use "all" to include all states.
	states_filter States that go to the revolter. Filtering trigger on the states scripted to go to the revolter.
	 ... effect list ... # you can list effects that will run on civil war country
}
```

### start_resistance

* Supported Scopes: STATE
* Supported Targets: any

```
starts resistance activity for a core country. 
Use along with force_enable_resistance if you are enabling resistance
in a state that is not possible (ie core).
Example : start_resistance = POL or start_resistance = yes
```

### state_event

* Supported Scopes: STATE, COUNTRY
* Supported Targets: none

```
Fires a state event.
Example:
state_event = {
	id = usa.61 # The event to fire.
	# Optional Fields:
	hours = 12 # The number of hours to wait before firing the event.
	days = 5 # The number of days to wait before firing the event.
	months = 1 # The number of months to wait before firing the event, where a month is treated as 30 days.
		# Note:  hours, days, and months can all be used and will simply be added together.
	random_hours = 18 # A random amount of hours to be added to the delay before firing, from 0 up to but not including random_hours.
	random_days = 2 # A random amount of days to be added to the delay before firing, from 0 up to but one hour less than random_days.
		# Note:  random_hours and random_days can both be used and will simply be added together.
	random = 6 # Equivalent to random_hours; preserverd for backwards compatibility.
	random = { chance = 50 ... } # Specify a set of child effects to execute as part of this effect, with a percentage chance of randomly happening or not (as a group, not individually).
	tooltip = usa.61.t # Manually specify which tooltip to use for this effect.
	trigger_for = GER # Indicate which country this state effect applies to. Value can be any of the following:
		# controller - The country that currently controls the state.
		# owner - The country that currently owns the state.
		# occupied - The country that has been occupied in the state by the current controller.
		# from - The country of the from scope.
		# prev - The country of the prev scope.
		# root - The country of the root scope.
		# TAG - A hard-coded country tag such as GER or ENG.
}

```

### steal_random_tech_bonus

* Supported Scopes: COUNTRY
* Supported Targets: none

```
adds a random limited use tech bonus from country of categories that is it ahead in compared to you.
it must have atleast one category or folder. But it can contain any number of them in any combination
Note: if a country does not have a tech to be stolen a random tech bonus will be applied based on base_bonus 
Example: steal_random_tech_bonus = {
	category = air_equipment
	folder = naval_folder
	ahead_reduction = ???
	bonus = ???
	base_bonus = 0.05
	instant = yes # instant unlock instead of bonus
	dynamic = yes # swaps bonus types from instant to category dependig on type as well as uses weights on tech progress
	name = ???
	target = ???
	uses = 1
}

```

### subtract_from_temp_variable

* Supported Scopes: any
* Supported Targets: none

```
Subtracts a value or a variable to a temp variable
Example: subtract_from_temp_variable = {
var = num_dogs
	value = 42
	tooltip = loc_str_id_with_LEFT_and_RIGHT  #localized text with LEFT and RIGHT tokens in it, tokens will replaced by values
}
```

### subtract_from_variable

* Supported Scopes: any
* Supported Targets: none

```
Subtracts a value or a variable to another one
Example: subtract_from_variable = {
var = num_dogs
	value = 42
	tooltip = loc_str_id_with_LEFT_and_RIGHT  #localized text with LEFT and RIGHT tokens in it, tokens will replaced by values
}
```

### supply_units

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Give supply to units being controlled by this leader. 
Example supply_units = 24
```

### swap_ideas

* Supported Scopes: COUNTRY
* Supported Targets: none

```
swap 2 ideas. 
 Syntax: swap_idea = {
  remove_idea = <idea>
  add_idea = <idea>
  add_days = 10 #optional, will add/subtract duration for new idea that replaces the old one with duration
  days = 25 #optional, will set the duration for the new idea
}
```

### swap_ruler_traits

* Supported Scopes: COUNTRY
* Supported Targets: none

```
swap 2 traits on current ruler. 
 Syntax: swap_ruler_traits = { remove = <trait> add = <trait> }
```

### teleport_armies

* Supported Scopes: STATE
* Supported Targets: any

```
teleport armies in state to another state or province. example :
teleport_armies = { 
  #only define one. if neither is defined will teleport to unit to their capital  to_state = 123 #id of the state to teleport
  to_state_array = array_name #an array of states to teleport (will be randomly picked)
  to_province = 123 #id of the province to teleport

  limit = { 
     # trigger will be checked for owner of armies and will only teleport if true. scope if the owner of the army and prev is the scope that calls teleport_armies
  } 
}
```

### transfer_navy

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Transfers the entire navy from scope country to target country. Does not support carriers!
Example:
ENG={
	target = NZL
	is_government_in_exile = yes #optional, default is no; the navy will be tagged as exile if this is yes so that it will return to owner if they return from exile.
}
```

### transfer_ship

* Supported Scopes: COUNTRY
* Supported Targets: none

```
Transfers ship from scope country to target country.
Example:
ENG={
  transfer_ship={
    prefer_name = "HMS Achilles"
    type = light_cruiser
    target = NZL
  }
}
```

### transfer_state

* Supported Scopes: COUNTRY
* Supported Targets: none

```
set owner and controller for state
```

### transfer_units_fraction

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
Transfer units (air, army, navy) to another country.
Also transfer the stockiled equipment (you can set it to zero if it is undesired) as well as unit leaders.
transfer_units_fraction = {
	target = ROOT          # the recipient
	size = 0.4             # [0,1] Default value for the ratio below if they are not specified
	stockpile_ratio = 0.3  # [0,1] Overrides size modifier for the stockpiled equipment and fuel
	army_ratio = 0.1       # [0,1] Overrides size modifier for army
	navy_ratio = 0.2       # [0,1] Overrides size modifier for navy
	air_ratio = 0.4        # [0,1] Overrides size modifier for air
	keep_unit_leaders = {  # specify IDs of unit leaders that remain with the original country
		700 701
	}
	keep_unit_leaders_trigger = { # Trigger for unit leaders to remain with the original country
		...                         # the scope is the unit leader being evaluated
		...                         # ROOT is the recipient
		...                         # FROM is the sender
		...                         # PREV is unset
	}
}
```

### turn_operative

* Supported Scopes: COUNTRY, UNIT_LEADER
* Supported Targets: THIS, ROOT, PREV, FROM

```
An operative is turned by the specified country.
This transfers the operative to the target country and make it appear as killed to the country of origin (increases the death counter and lock the slot).
This fires the on_action on_operative_death with as killer the target country.
If the target country is the owner of the operative, this has no effect and an error is logged.

WARN: the on_action might execute immediatly, before any effect listed after the occurence of turn_operative.

Examples:
GER = {
    turn_operative = PREV  # where PREV is an operative (unit leader)
    # or
    turn_operative = {
        operative = PREV
    }
}

turn_operative = { turned_by = GER } # where the scope is an unit leader

```

### unit_leader_event

* Supported Scopes: UNIT_LEADER
* Supported Targets: none

```
Fires a unit leader event for owner country.
Example:
unit_leader_event = {
	id = generic.17 # The event to fire.
	# Optional Fields:
	hours = 12 # The number of hours to wait before firing the event.
	days = 5 # The number of days to wait before firing the event.
	months = 1 # The number of months to wait before firing the event, where a month is treated as 30 days.
		# Note:  hours, days, and months can all be used and will simply be added together.
	random_hours = 18 # A random amount of hours to be added to the delay before firing, from 0 up to but not including random_hours.
	random_days = 2 # A random amount of days to be added to the delay before firing, from 0 up to but one hour less than random_days.
		# Note:  random_hours and random_days can both be used and will simply be added together.
	random = 6 # Equivalent to random_hours; preserverd for backwards compatibility.
	random = { chance = 50 ... } # Specify a set of child effects to execute as part of this effect, with a percentage chance of randomly happening or not (as a group, not individually).
	tooltip = generic.17.t # Manually specify which tooltip to use for this effect.
}

```

### unlock_decision_category_tooltip

* Supported Scopes: COUNTRY
* Supported Targets: none

```
localizes name of category and displays tooltip that shows it will be unlocked
```

### unlock_decision_tooltip

* Supported Scopes: COUNTRY
* Supported Targets: none

```
show what decision does
Example: unlock_decision_tooltip = some_decision_here
Example:
unlock_decision_tooltip = {
    decision = <some_decision>
    show_effect_tooltip = yes # default is no
    show_modifiers = yes # default is no
}

```

### unlock_national_focus

* Supported Scopes: COUNTRY
* Supported Targets: none

```
unlocks a focus for a country
```

### upgrade_intelligence_agency

* Supported Scopes: COUNTRY
* Supported Targets: none

```
add an upgrade to the Intelligence Agency (must be created):
upgrade_intelligence_agency = upgrade_army_department
```

### while_loop_effect

* Supported Scopes: any
* Supported Targets: any

```
Runs the effect as long as a trigger is true
Example: while_loop_effect = {
	limit = { ... trigger ... } a trigger to test before each iteration
	break = break_name #optional (default 'break') set this temp variable to non zero to break the loop
 #effect 1
 #effect 2 ...
}
```

### white_peace

* Supported Scopes: COUNTRY
* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL

```
white peaces the two countries if at war
```

