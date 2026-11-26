# MD Custom Modifiers

MD's non-vanilla modifier keys are defined in `common/modifier_definitions/`. Search that
directory for a key before using it. The definition files are the list.

- They work wherever vanilla modifiers do: ideas, dynamic modifiers, focus rewards, and
  decision effects.
- They are not valid inside MIO `equipment_bonus` or `production_bonus` blocks. Use
  `organization_modifier`.
- Country-specific keys (`CZE_`, `ITA_`, `JAP_`, `CHI_`) belong only in that country's
  content.

| File                                         | Domain                                     |
| -------------------------------------------- | ------------------------------------------ |
| `money_modifier_definitions.txt`             | Tax, costs, productivity, workforce, trade |
| `modifier_definitions.txt`                   | Army and general economy                   |
| `energy_modifier_definitions.txt`            | Energy gain, use, and fuel                 |
| `expected_spending.txt`                      | Expected spending                          |
| `influence_modifier_definitions.txt`         | Foreign influence                          |
| `internal_factions_modifier_definitions.txt` | Internal faction opinion                   |
| `political_modifier_definitions.txt`         | Political                                  |
| `migration_modifier_definitions.txt`         | Migration                                  |
| `missile_modifier_definitions.txt`           | Missiles, satellites, reactor fuel         |
| `cyber_modifier_definitions.txt`             | Cyber                                      |
| `counter_terror_modifier_definitions.txt`    | Counter-terror                             |
| `EH_modifier_definitions.txt`                | Event Horizon                              |

## Internal factions

Three number modifiers per faction, where `<faction>` is the faction idea name
(`oligarchs`, `the_military`, `labour_unions`, `wall_street`, and so on):

| Modifier                       | Effect                                                              |
| ------------------------------ | ------------------------------------------------------------------- |
| `if_<faction>_monthly_opinion` | Added to opinion every month, even with the no-decay game rule on   |
| `if_<faction>_minimum_opinion` | Sets the monthly target to 50 + value and the hard floor to value |
| `if_<faction>_maximum_opinion` | Ceiling becomes 100 + value. Use negative values                    |

- Opinion above the target decays toward it. A positive minimum also lets opinion
  below the target recover at the same rate. A zero tick rate disables both, but
  the separate monthly-opinion modifier and clamps still apply. A negative minimum
  lowers the target without enabling recovery. Opinion never goes above 100.
- Values stack across every source. `change_<faction>_opinion` and
  `monthly_tick_internal_factions_opinion` in `00_internal_faction_effects.txt` read
  them. The Wahhabi Ulema effect is `change_the_wahabi_ulema_opinion`.
- Put a faction floor or cap on the idea as one of these modifiers. Do not set
  `<faction>_opinion_min` or add a `custom_modifier_tooltip` for it.

## Other notes

- `general_death_chance_modifier` is set on officer corps ideas and read as
  `FROM.modifier@general_death_chance_modifier` in the `on_army_leader_*` on_actions.
