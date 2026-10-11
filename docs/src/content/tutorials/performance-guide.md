---
title: Performance Guide
description: Guide to help improve performance for players.
permalink: /player-tutorials/performance-guide/
version: "v2.0"
---

Millennium Dawn is a performance-intensive mod for Hearts of Iron IV. Its extended mechanics, numerous nations, and drive to deepen the experience demand more from your machine. The team is actively optimizing the mod, but we are limited by the game engine and what Hearts of Iron IV allows. This guide helps you tune the mod for a smoother experience without losing meaningful content.

## What this guide does not do

This guide does not recommend:

- Disabling the economic system
- Disabling the influence system
- Disabling the United Nations system
- Removing core gameplay systems

These systems are central to Millennium Dawn's geopolitical gameplay. The recommended rules below improve performance while keeping them enabled. Options that do remove content are listed apart, under [Larger Cuts That Remove Content](#larger-cuts-that-remove-content).

**NOTE**
If your computer has weak single-core performance and struggles with vanilla Hearts of Iron IV, it will struggle significantly more with Millennium Dawn. The development team cannot fix this; it must be handled by the Paradox Interactive development team.

## Game Rules

The most powerful tools for a Millennium Dawn player are the Game Rules in the "Select a Country" screen at the beginning of the game. Millennium Dawn offers multiple ways to tailor the experience, but these are the rules we recommend setting to preserve performance without losing any core gameplay.

Recommended Game Rules:

- Remove Nations: Tiny Nations (Microstates)
- Enable AI Division Limiter: Potato Edition
- Disable GDP Graph: Yes
- Enable Resource Storage System: No
- Enable MD Ledger: No

### Remove Nations: Tiny Nations (Microstates)

This rule removes nations such as Andorra, Vatican City, Nauru, St Kitts, and other small island nations included for immersion and historical accuracy. Removing them can yield a 5-6% performance improvement on weaker machines or for players who simply want the mod to run faster. Fewer nations means fewer calculations, so each tick, and every "every country" or "every other country" call, runs faster.

### Enable AI Division Limiter: Potato Edition

This rule enforces a stricter division limiter on the AI, which particularly improves late-game performance. It reduces the number of divisions the AI produces in the later years of the mod, trading some line-holding power for a more optimized run. The AI is slightly worse at handling larger frontlines, multi-faceted attacks, and large-scale conflicts, particularly during World War III.

### Disable GDP Graph: Yes

Disabling the GDP Graph stops the game from calculating the frames the graph needs. The GDP graph is purely for display and player convenience; turning it off comes at effectively no cost to the experience, though it removes historical data from the player's view.

### Enable Resource Storage System: No

The Resource Storage System is relatively minor in the grand scheme of Millennium Dawn, but disabling it reduces computational overhead on the daily tick. It removes the ability for the player or AI to store resources, avoiding the computation of storage and relative consumption.

### Enable MD Ledger: No

The Ledger, much like the GDP Graph, is purely for display and provides long-form data and information about the world at large. Disabling the MD Ledger does not reduce the gameplay experience; it only limits the easily accessible information provided to the player. Turning it off reduces the performance drain on monthly ticks, yielding around a 2-4% overall improvement.

## Larger Cuts That Remove Content

Use these only when the recommended rules are not enough. Each one switches off a whole system, so you trade content for speed. The team has not benchmarked them, so this guide gives no percentages and cannot promise a gain. Try one at a time and compare.

### Organization Options

These three rules sit under **Organization Options**. They apply once, when the game starts, and cannot be undone in that save.

- **Disable The EU: Yes** removes every country from the European Union. Members lose the European Union Member and Euro spirits and switch to the Domestic Reserve currency law. EU voting, membership applications, and the EU end-game paths are switched off.
- **Disable NATO: Yes** dissolves the NATO faction. Members lose the NATO Member spirit, NATO technology sharing, and their opinion bonus with each other. The Major Non-NATO Ally spirit is removed and the NATO decisions are hidden.
- **Disable CSTO: Yes** dissolves the CSTO faction. Members lose the CSTO Member spirit and CSTO technology sharing, and the CSTO decisions are hidden.

Focuses and decisions that depend on one of these organizations are skipped or unavailable. This matters most for European countries, the United States, and Russia, whose content leans on them. Pick a country that does not rely on the organization you disable.

### Expansions

Expansions are switched off in the Hearts of Iron IV launcher, not in Game Rules. Two of them add systems that run for the whole game:

- **La Résistance** adds intelligence agencies, operatives, and operations. Without it you lose espionage, including the Millennium Dawn operations built on it.
- **No Compromise, No Surrender** adds naval headquarters and naval supply hubs, which Millennium Dawn places in dozens of states at the start. Without it you also lose the cruise missile strike on naval headquarters and the Forbidden City and Tokyo Imperial Palace landmarks.

Millennium Dawn runs without either expansion. Change your expansions before starting a new game, not in the middle of a campaign.
