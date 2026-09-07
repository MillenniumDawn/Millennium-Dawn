---
title: Performance Guide
description: Guide to help improve performance for players.
permalink: /player-tutorials/performance-guide/
version: "v2.0"
---

# Performance Guide

Millennium Dawn, by its nature, is a performance-intensive mod for Hearts of Iron IV due to its extended mechanics, numerous nations, and drive to deepen the Hearts of Iron IV experience. This guide seeks to help players make changes to the mod without losing meaningful content while delivering a solid experience. The team is striving to optimize the mod and the experience while providing the targeted gameplay; this is a focal point for the team. However, we are limited by the game engine and the interactions that Hearts of Iron IV allows.

## What this guide does not do

This guide does not serve the following, nor will it recommend the following:

- Disabling the economic system
- Disabling the influence system
- Disabling the United Nation system
- Changing anything that compromises the Millennium Dawn experience in any shape or form

The mod is targeted at players looking for a deeper experience and a more geopolitically heavy game; without these systems to facilitate that aim, the mod falls flat. The guide's entire purpose is to deliver a more streamlined experience for your machine without compromising that aim. The recommendations are tailored to that aim, listed by impact with explanations as to why.

**NOTE**
If your computer has weak single-core performance and struggles with vanilla Hearts of Iron IV, you will struggle significantly more while playing Millennium Dawn. The development team is unable to fix this, as it must be handled by the Paradox Interactive development team.

## Game Rules

The most powerful tools for a Millennium Dawn player are the Game Rules in the "Select a Country" screen at the beginning of the game. Millennium Dawn provides you with multiple options to tailor your experience to your preference, but these are the game rules we recommend setting to preserve performance without losing any core gameplay.

Recommended Game Rules:

- Remove Nations: Tiny Nations (Microstates)
- Enable AI Division Limiter: Potato Edition
- Disable GDP Graph: Yes
- Enable Resource Storage System: No
- Enable MD Ledger: No

### Remove Nations: Tiny Nations (Microstates)

The "Remove Nations - Tiny Nations (Microstates)" game rule removes nations such as Andorra, Vatican City, Nauru, St Kitts, and other small island nations included for immersion and historical accuracy. Removing them can yield a 5-6% performance improvement for weaker machines or for players who simply want the mod to run faster. The removal of these nations reduces overall calculations and makes each tick faster when the game runs "every country" or "every other country" calls.

### Enable AI Division Limiter: Potato Edition

The "Enable AI Division Limiter - Potato Edition" game rule enforces a stricter division limiter on the AI, which particularly improves late-game performance. Enabling this game rule reduces the number of divisions the AI produces in the later years of the mod, providing a more optimized experience at the cost of fewer units available for the AI to hold lines. This trade-off means the AI is slightly worse at handling situations with larger frontlines, multi-faceted attacks, or larger-scale conflicts, particularly during World War III.

### Disable GDP Graph: Yes

Disabling the GDP Graph simply stops the game from calculating the needed frames for the GDP graph. The GDP graph is purely for display and player convenience; removing this feature comes at effectively no cost to the experience, although it removes historical data from the player's view.

### Enable Resource Storage System: No

The Resource Storage System is relatively minor in the grand scheme of Millennium Dawn, but disabling it reduces computational overhead on the daily tick. It disables the ability for the player or AI to store resources, avoiding the computation of storage and relative consumption.

### Enable MD Ledger: No

The Ledger, much like the GDP Graph, is purely for display and provides long-form data and information about the world at large. Disabling the MD Ledger does not reduce the gameplay experience, but it does limit the easily accessible information provided to the player. It is recommended to turn this off to reduce the performance drain on monthly ticks, yielding around a 2-4% overall improvement.
