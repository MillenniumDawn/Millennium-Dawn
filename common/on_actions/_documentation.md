# List of possible on-actions and/or known on actions

### General

- `on_startup`
- `on_daily`
- `on_daily_TAG`
- `on_weekly`
- `on_weekly_TAG`
- `on_monthly`
- `on_monthly_TAG`
- `on_nuke_drop`
- `on_naval_invasion`
- `on_units_paradropped_in_state`

### Politics

- `on_coup_succeeded`
- `on_government_change`
- `on_ruling_party_change`
- `on_new_term_election`
- `on_before_peace_conference_start` - ROOT is winner, FROM is loser (called for all winners against all losers)
- `on_peaceconference_ended` - ROOT is winner, FROM is loser (called for all winners against all losers)

### Diplomacy/War

- `on_send_volunteers`
- `on_war_relation_added`
- `on_declare_war`
- `on_war`
- `on_capitulation`
- `on_capitulation_immediate`
- `on_annex`
- `on_civil_war_end_before_annexation`
- `on_civil_war_end`
- `on_puppet`
- `on_force_government`
- `on_liberate`
- `on_release_as_free`
- `on_release_as_puppet`
- `on_guarantee`
- `on_improve_relation`
- `on_military_access`
- `on_offer_military_access`
- `on_peace_proposal`
- `on_stage_coup`

### Faction

- `on_offer_join_faction`
- `on_join_faction`
- `on_leave_faction`

### Autonomy

- `on_subject_annexed`
- `on_subject_free`

### States

- `on_state_control_changed`

### Wargoals

- `on_justifying_wargoal_pulse`

### Unit Leader

- `on_unit_leader_created`
- `on_army_leader_won_combat`
- `on_army_leader_lost_combat`
- `on_unit_leader_level_up`

### Aces

- `on_ace_promoted`
- `on_ace_killed`
- `on_ace_killed_by_ace`
- `on_ace_killed_other_ace`
- `on_aces_killed_each_other`

### La Resistance

- `on_operation_completed`
- `on_operative_detected_during_operation`
- `on_operative_on_mission_spotted`
- `on_operative_captured`
- `on_operative_death`

### Market Contracts (MD)

- `on_contract_started`
- `on_contract_finished`
- `on_contract_cancelled`
