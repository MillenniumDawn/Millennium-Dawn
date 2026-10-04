---
title: Unique Cheats
description: "Unique Cheats and commands for Millennium Dawn: A Modern Day Mod"
---

# Purpose of this Page

WIP: This is a living document. We will add things in here as they come up or as Bird remembers this exists.

This page is a list of all of the documented cheats from Millennium Dawn. We do also provide a basic cheat decision category. This is merely to help those who are looking for some more granular Millennium Dawn debug commands.

[Vanilla Console Commands](https://hoi4.paradoxwikis.com/Console_commands)

## How to Enable Cheat Decisions

You have to enable it via the in game "Game Rules" section.

## Political Cheats

This section handles all of our political cheats/debugging effects.

Outlook Keys:

- nationalist (Nationalist Outlook)
- fascism (Salafist Outlook)
- communism (Emerging Outlook)
- democratic (Western Outlook)
- neutrality (Non-Aligned Outlook)

The vanilla command `add_party_popularity` does work with Millennium Dawn. The subideology party section does not immediately update. You can just wait a day or open the subideology screen to see the update.

## Economic System Cheats

This section handles all of our economic system cheats/debugging effects.

### Economic Variables

`set_var treasury 10000` - Sets the countries current treasury to 10000

`set_var debt 0` - Sets the countries current debt to 0

`set_var int_investments 10000` - Sets the countries international investments to 10000

## Console Effect Cheats

Open the console and type `effect <name>`. Country-specific cheats run on the country you are playing. To use one on another country, switch with `tag <TAG>` first. Cheats described as affecting every country run globally.

### Economy

| Command                                | What it does                                                                   |
| -------------------------------------- | ------------------------------------------------------------------------------ |
| `effect cheat_motherlode`              | Adds 10,000 to the treasury.                                                   |
| `effect cheat_reset_economy`           | Runs all four resets below.                                                    |
| `effect cheat_reset_inflation`         | Sets inflation to 0% and clears the last four quarters of inflation history.   |
| `effect cheat_clear_debt`              | Sets debt to 0, which also clears interest payments.                           |
| `effect cheat_reset_treasury`          | Sets the treasury to 0. Use `set_var treasury <amount>` for a specific amount. |
| `effect cheat_reset_currency_strength` | Sets currency strength to 1.0 (par) and removes the inflation it was adding.   |

The economy panel updates right away. The normal weekly and monthly updates keep running, so inflation and currency strength start moving again from the reset value.

### Offsite Factories

Each command adds the same number of offsite civilian and military factories to your country:

- `effect cheat_add_offsite_factories_1`: one of each.
- `effect cheat_add_offsite_factories_2`: two of each.
- `effect cheat_add_offsite_factories_3`: three of each.
- `effect cheat_add_offsite_factories_5`: five of each.

The free factories game rule calls these effects for every human player at startup. Console use affects only the country you control and can be repeated.

### Equipment

| Command                           | What it adds                                                                                                                                                                                            |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `effect cheat_add_land_equipment` | 10,000 infantry weapons, 5,000 utility vehicles, 2,500 each of command and control, light anti-tank and anti-air, and 1,000 each of heavy anti-tank, artillery, heavy utility vehicles and land drones. |
| `effect cheat_add_convoys`        | 500 convoys.                                                                                                                                                                                            |
| `effect cheat_add_trains`         | 200 trains.                                                                                                                                                                                             |

These grant each equipment type by archetype, so the game picks the model. Tanks, aircraft and ships are designs, so use the vanilla `add_equipment <amount> <equipment>` command with a specific variant instead.

### AI Political Power

Use `effect cheat_add_ai_political_power_250`, `effect cheat_add_ai_political_power_500` or `effect cheat_add_ai_political_power_1000` to grant that much political power to every current AI country. The AI starting political power game rule calls the same effects. Repeating a command grants the amount again; newly created AI countries are unaffected until you run it again.

### Voting

| Command                       | What it does                                                                                                                         |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `effect cheat_eu_ai_vote_yes` | Every AI member votes yes on every EU council vote. This is the same switch as the EU cheat decision.                                |
| `effect cheat_un_ai_vote_yes` | AI voters vote yes in UN General Assembly and Security Council votes, including recognition votes. Permanent members no longer veto. |

These apply to every vote, not only the ones you propose, so AI proposals pass too. The subject of a Security Council vote does not vote. A permanent-seat applicant abstains in the General Assembly vote on its own application. Neither cheat has an off switch. Countries that appear after you run `cheat_un_ai_vote_yes` vote normally until you run it again.

### Factions and Satellites

These match the cheat decisions, which call the same effects.

| Command                                  | What it does                                                   |
| ---------------------------------------- | -------------------------------------------------------------- |
| `effect cheat_dismantle_all_factions`    | Dismantles every faction.                                      |
| `effect cheat_dismantle_nato`            | Dismantles NATO and removes NATO membership from every member. |
| `effect cheat_dismantle_russian_faction` | Dismantles Russia's faction.                                   |
| `effect cheat_dismantle_iranian_faction` | Dismantles Iran's faction.                                     |
| `effect cheat_dismantle_saudi_faction`   | Dismantles Saudi Arabia's faction.                             |
| `effect cheat_add_satellites`            | Adds 20 of every satellite model.                              |

### Ruling Party

Each command makes that subideology your ruling party and adds 50% to its popularity and its outlook. The party cheat decisions call the same effects.

| Outlook     | Command                                         | Generic party                 |
| ----------- | ----------------------------------------------- | ----------------------------- |
| Western     | `effect cheat_party_western_autocracy`          | Pro-Western Autocrats         |
| Western     | `effect cheat_party_conservatism`               | Conservatives                 |
| Western     | `effect cheat_party_liberalism`                 | Liberals                      |
| Western     | `effect cheat_party_socialism`                  | Social Democrats              |
| Emerging    | `effect cheat_party_communist_state`            | Communists                    |
| Emerging    | `effect cheat_party_anarchist_communism`        | Left-Wing Radicals            |
| Emerging    | `effect cheat_party_conservative`               | Reactionaries                 |
| Emerging    | `effect cheat_party_autocracy`                  | Autocrats                     |
| Emerging    | `effect cheat_party_mod_vilayat_e_faqih`        | Moderate Shiite Revolutionary |
| Emerging    | `effect cheat_party_vilayat_e_faqih`            | Hardline Shiite Revolutionary |
| Salafist    | `effect cheat_party_kingdom`                    | Pro-Establishment Salafism    |
| Salafist    | `effect cheat_party_caliphate`                  | Salafi Jihadism               |
| Non-Aligned | `effect cheat_party_neutral_muslim_brotherhood` | Moderate Islamists            |
| Non-Aligned | `effect cheat_party_neutral_autocracy`          | Non-Aligned Autocrats         |
| Non-Aligned | `effect cheat_party_neutral_conservatism`       | Conservatives                 |
| Non-Aligned | `effect cheat_party_oligarchism`                | Oligarchs                     |
| Non-Aligned | `effect cheat_party_neutral_libertarian`        | Libertarians                  |
| Non-Aligned | `effect cheat_party_neutral_green`              | Greens                        |
| Non-Aligned | `effect cheat_party_neutral_social`             | Socialist Democrats           |
| Non-Aligned | `effect cheat_party_neutral_communism`          | Communists                    |
| Nationalist | `effect cheat_party_nat_populism`               | Right Wing Populists          |
| Nationalist | `effect cheat_party_nat_fascism`                | Fascists                      |
| Nationalist | `effect cheat_party_nat_autocracy`              | Military Junta                |
| Nationalist | `effect cheat_party_monarchist`                 | Monarchists                   |

Countries rename many of these parties, so the name in your politics screen may differ from the generic one.

### Other Cheat Decisions

The rest of the cheat decisions already have a console command:

- Manpower: `manpower <amount>`.
- Operatives: `add_ideas operatives1`, `add_ideas operatives5` or `add_ideas operatives10`.
- Max internal faction opinion: `effect set_to_max_internal_faction_opinions`.
- Cheaper internal faction changes: `add_ideas GAME_RULE_reduce_internal_factions_cost`.
