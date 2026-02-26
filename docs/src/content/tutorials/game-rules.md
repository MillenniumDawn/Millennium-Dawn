---
title: Game Rules
description: Player-oriented guide to Game Rules for Millennium Dawn
---

This guide covers all game rules available in Millennium Dawn for customizing your gameplay experience.

---

# Game Rule Groups

## AI Options (`MD_AI_RULES`)

Controls AI behavior and difficulty settings.

| Rule                                       | Options          | Default | Description                                |
| ------------------------------------------ | ---------------- | ------- | ------------------------------------------ |
| `rule_god_of_war`                          | yes/no           | no      | Enables "God of War" AI mode               |
| `rule_ai_starting_political_power`         | no/one/two/three | no      | AI starting political power (250/500/1000) |
| `rule_enable_ai_debt_war`                  | yes/no           | no      | Allow AI to take on debt for war           |
| `rule_disable_AI_using_freedom_cont_focus` | yes/no           | yes     | Enable AI use of autonomy focus            |
| `rule_enable_AI_using_attaches`            | yes/no           | yes     | Enable AI use of military attaches         |

## Peace Conferences (`MD_PEACE_DEALS`)

Controls peace conference and annexation behavior.

| Rule                  | Options | Default | Description                            |
| --------------------- | ------- | ------- | -------------------------------------- |
| `rule_md_annex`       | yes/no  | no      | Allow direct annexation in peace deals |
| `allow_chaotic_PC`    | yes/no  | no      | Enable chaotic peace conferences       |
| `allow_player_led_PC` | yes/no  | no      | Allow player-led peace conferences     |
| `allowed_CPD`         | yes/no  | yes     | Allow conditional peace deals          |

## Focus Tree Options (`MD_FOCUS_TREE_RULES`)

Country-specific focus tree options and alternate paths.

| Rule                   | Options | Default | Description                     |
| ---------------------- | ------- | ------- | ------------------------------- |
| `rule_salafist_branch` | yes/no  | no      | Enable/disable Salafist content |

## Flags & Formable Nations (`MD_FORMABLE_RULES`)

Controls special nation formation options.

| Rule                            | Options | Default | Description                    |
| ------------------------------- | ------- | ------- | ------------------------------ |
| `rule_disable_formable_nations` | yes/no  | no      | Disable all formable nations   |
| `allow_multiple_formables`      | yes/no  | no      | Allow forming multiple nations |
| `allow_edgy_flags`              | yes/no  | no      | Allow alternate flag designs   |

## Organization Options (`MD_ORGANISATION_RULES`)

Controls major international organizations.

| Rule                | Options | Default | Description            |
| ------------------- | ------- | ------- | ---------------------- |
| `rule_disable_eu`   | yes/no  | no      | Disable European Union |
| `rule_disable_nato` | yes/no  | no      | Disable NATO           |
| `rule_disable_csto` | yes/no  | no      | Disable CSTO           |

**EU Voting Rules**

- `rule_european_union_voting_limits`: Cooldown between votes (60-210 days)

## Influence System Options (`MD_INFLUENCE_RULES`)

Controls influence system mechanics.

| Rule                                             | Options               | Default | Description                        |
| ------------------------------------------------ | --------------------- | ------- | ---------------------------------- |
| `rule_spread_influence_amount_gain`              | 0.5%/1%/1.5%/2%/3%/4% | 1.5%    | Spread influence gain rate         |
| `rule_spread_influence_cooldown_limits`          | 0/14/30/60 days       | 30 days | Influence action cooldown          |
| `rule_invest_influence_amount_gain`              | 0.5%/1%/1.5%/2%       | 1.5%    | Invest influence gain rate         |
| `rule_influence_cooldown_limits`                 | 0/14/30 days          | 14 days | Invest influence cooldown          |
| `rule_monthly_domestic_independence_tick`        | yes/no                | yes     | Monthly domestic independence gain |
| `rule_monthly_domestic_independence_gain_amount` | 0.5/1.0/1.5           | 0.5     | Domestic independence amount       |
| `rule_disable_ai_influence_puppeting`            | yes/no                | no      | Disable AI influence puppeting     |
| `rule_disable_western_outlook_features`          | yes/no                | no      | Disable Western Outlook features   |

## Optimization & Performance (`MD_OPTIMISATION_RULES`)

Performance-related settings.

| Rule                                   | Options               | Default | Description                      |
| -------------------------------------- | --------------------- | ------- | -------------------------------- |
| `allow_mp_optimizations`               | yes/no                | no      | Enable multiplayer optimizations |
| `allow_division_limiter`               | yes/no/potato_edition | yes     | Division count limiter           |
| `remove_mp_states`                     | yes/no                | no      | Remove small nations             |
| `rule_disable_generals_getting_killed` | yes/no                | no      | Prevent general deaths           |
| `rule_allow_free_factories`            | yes/no                | no      | Free factories in MP             |
| `rule_allow_MP_enhancements`           | yes/no                | no      | MP enhancements                  |

## Nuclear Rules (`MD_NUCLEAR_RULES`)

Nuclear weapons settings.

| Rule                        | Options | Default | Description                        |
| --------------------------- | ------- | ------- | ---------------------------------- |
| `allow_nuclear_first_use`   | yes/no  | no      | Allow first use of nuclear weapons |
| `allow_nuclear_retaliation` | yes/no  | yes     | Allow nuclear retaliation          |

## Miscellaneous Rules (`MD_RULES`)

Miscellaneous gameplay options.

| Rule                     | Options | Default | Description               |
| ------------------------ | ------- | ------- | ------------------------- |
| `allow_enable_world_war` | yes/no  | no      | Allow world war mechanics |
| `allow_enable_ledger`    | yes/no  | yes     | Enable ledger feature     |
| `allow_colored_puppets`  | yes/no  | no      | Colored puppet borders    |
| `historic_events`        | yes/no  | no      | Enable historical events  |
| `allow_enable_help_gui`  | yes/no  | no      | Enable help GUI           |

**Energy Difficulty Rules**

- `rule_player_energy_difficulty`: Player energy difficulty (very_easy to very_hard)
- `rule_AI_energy_difficulty`: AI energy difficulty
- `rule_enable_energy_load_sharing`: Energy load sharing between states

**Economic Rules**

- `rule_starting_debt_rule`: Who gets starting debt (normal/player_only/ai_only/everyone)
- `rule_internal_faction_tick_amount`: Internal faction tick rate
- `rule_internal_faction_cost_reduction`: Faction cost reduction

## Cheat Options (`MD_CHEAT_RULES`)

Debug and cheat-related options.

| Rule                             | Options | Default | Description                    |
| -------------------------------- | ------- | ------- | ------------------------------ |
| `allow_cheat_decisions`          | yes/no  | no      | Enable cheat decisions         |
| `allow_toggling_cheat_decisions` | yes/no  | no      | Allow toggling cheats mid-game |
| `rule_disable_anti_bully`        | yes/no  | no      | Disable anti-bully protection  |

## Randomize Game Rules (`MD_RANDOM_RULES`)

Chaos mode options for randomized gameplay.

| Rule                               | Options | Default | Description                 |
| ---------------------------------- | ------- | ------- | --------------------------- |
| `rule_randomize_ideologies`        | yes/no  | no      | Randomize all ideologies    |
| `rule_randomize_religion`          | yes/no  | no      | Randomize religions         |
| `rule_randomize_internal_factions` | yes/no  | no      | Randomize internal factions |

---

# Vanilla Rules

Millennium Dawn inherits many vanilla HOI4 game rules:

## Foreign Policy

- `allow_wargoals`: Wargoal availability
- `allow_access`: Military access rules
- `allow_release_nations`: Nation release rules
- `allow_licensing`: Equipment licensing
- `allow_lend_lease`: Lend-lease rules
- `allow_volunteers`: Volunteer rules
- `allow_guarantees`: Guarantee independence

## Covert Actions

- `allow_coups`: Coup availability
- `allow_party_boosting`: Party boosting

## Gameplay

- `allow_paratroopers`: Paratrooper availability
- `maximum_fort_level`: Fort level cap
