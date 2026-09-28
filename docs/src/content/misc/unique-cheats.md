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

Open the console and type `effect <name> = yes`. The cheat runs on the country you are playing. To use it on another country, switch with `tag <TAG>` first.

### Economy

| Command                                      | What it does                                                                   |
| -------------------------------------------- | ------------------------------------------------------------------------------ |
| `effect cheat_reset_economy = yes`           | Runs all four resets below.                                                    |
| `effect cheat_reset_inflation = yes`         | Sets inflation to 0% and clears the last four quarters of inflation history.   |
| `effect cheat_clear_debt = yes`              | Sets debt to 0, which also clears interest payments.                           |
| `effect cheat_reset_treasury = yes`          | Sets the treasury to 0. Use `set_var treasury <amount>` for a specific amount. |
| `effect cheat_reset_currency_strength = yes` | Sets currency strength to 1.0 (par) and removes the inflation it was adding.   |

The economy panel updates right away. The normal weekly and monthly updates keep running, so inflation and currency strength start moving again from the reset value.

### Equipment

| Command                                 | What it adds                                                                                                                                                                                            |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `effect cheat_add_land_equipment = yes` | 10,000 infantry weapons, 5,000 utility vehicles, 2,500 each of command and control, light anti-tank and anti-air, and 1,000 each of heavy anti-tank, artillery, heavy utility vehicles and land drones. |
| `effect cheat_add_convoys = yes`        | 500 convoys.                                                                                                                                                                                            |
| `effect cheat_add_trains = yes`         | 200 trains.                                                                                                                                                                                             |

These grant each equipment type by archetype, so the game picks the model. Tanks, aircraft and ships are designs, so use the vanilla `add_equipment <amount> <equipment>` command with a specific variant instead.
