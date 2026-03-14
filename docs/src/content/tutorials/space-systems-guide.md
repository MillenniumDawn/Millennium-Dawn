---
title: Space Systems Guide
description: Guide to satellite systems, space programs, and orbital mechanics in Millennium Dawn
---

# Space Systems Guide

Millennium Dawn features a comprehensive space program and satellite system. Countries can develop space programs, research satellite technologies, build and launch satellites into orbit, and gain powerful military and civilian bonuses from orbital coverage. This guide covers every aspect of the system.

---

## Table of Contents

- [Getting Started: The Space Program](#getting-started-the-space-program)
- [Technology Tree](#technology-tree)
  - [GNSS (Navigation Satellites)](#gnss-navigation-satellites)
  - [COMSAT (Communications Satellites)](#comsat-communications-satellites)
  - [SPYSAT (Reconnaissance Satellites)](#spysat-reconnaissance-satellites)
  - [KILLSAT (Anti-Satellite Weapons)](#killsat-anti-satellite-weapons)
  - [OLV (Orbital Launch Vehicles)](#olv-orbital-launch-vehicles)
- [Building Satellites](#building-satellites)
  - [Production Costs and Duration](#production-costs-and-duration)
  - [Reusable Launch Vehicles](#reusable-launch-vehicles)
- [Satellite Constellations and Coverage](#satellite-constellations-and-coverage)
  - [How Coverage Works](#how-coverage-works)
  - [Constellation Tiers](#constellation-tiers)
  - [SBAS (Augmentation from Other Satellites)](#sbas-augmentation-from-other-satellites)
  - [Degradation](#degradation)
- [Satellite Bonuses](#satellite-bonuses)
  - [GNSS Military Bonuses](#gnss-military-bonuses)
  - [GNSS Civilian Bonuses](#gnss-civilian-bonuses)
  - [COMSAT Military Bonuses](#comsat-military-bonuses)
  - [COMSAT Civilian Bonuses](#comsat-civilian-bonuses)
  - [SPYSAT Military Bonuses](#spysat-military-bonuses)
  - [SPYSAT Civilian Bonuses](#spysat-civilian-bonuses)
- [Spy Satellite Missions](#spy-satellite-missions)
- [Advanced Space Projects](#advanced-space-projects)
  - [Space-Based Weapons](#space-based-weapons)
  - [Space-Based Solar Farms](#space-based-solar-farms)
  - [Orbital Fire Support](#orbital-fire-support)
- [Strategic Tips](#strategic-tips)

---

## Getting Started: The Space Program

Before you can research any satellite technology, you must complete the **Space Program** special project. This is a major undertaking:

| Property    | Value                                                  |
| ----------- | ------------------------------------------------------ |
| Duration    | 180 months (15 years)                                  |
| Requirement | Must have ballistic missile technology                 |
| Unlocks     | GNSS, COMSAT, SPYSAT, and OLV technology lines         |
| Follow-up   | Unlocks the Space-Based Weapons project (for KILLSATs) |

The AI prioritizes space programs heavily for Superpowers and Great Powers, moderately for Large and Regional Powers, and rarely for Non-Powers.

Some countries can access the space program through national focuses (e.g., South Korea, Brazil, India, France, Israel, Poland) which may provide shortcuts or bonuses.

---

## Technology Tree

The space technology tree has five branches, each representing a different type of orbital system. All satellite technologies advance in generational tiers, with each generation available roughly every 10 years.

### GNSS (Navigation Satellites)

Global Navigation Satellite Systems provide precision positioning for both military targeting and civilian infrastructure.

| Generation | Available | Research Cost |
| ---------- | --------- | ------------- |
| GNSS1      | 1965      | 1.5           |
| GNSS2      | 1975      | 1.5           |
| GNSS3      | 1985      | 1.5           |
| GNSS4      | 1995      | 1.5           |
| GNSS5      | 2005      | 1.5           |
| GNSS6      | 2015      | 1.5           |
| GNSS7      | 2025      | 1.5           |
| GNSS8      | 2035      | 1.5           |

Each generation unlocks the ability to build that tier of GNSS satellite. Higher tiers provide better maximum bonuses when deployed in sufficient numbers.

### COMSAT (Communications Satellites)

Communications satellites enhance command and control for military forces and provide political/intelligence bonuses for civilian use.

| Generation | Available | Research Cost |
| ---------- | --------- | ------------- |
| COMSAT1    | 1965      | 1.7           |
| COMSAT2    | 1975      | 1.7           |
| COMSAT3    | 1985      | 1.7           |
| COMSAT4    | 1995      | 1.7           |
| COMSAT5    | 2005      | 1.7           |
| COMSAT6    | 2015      | 1.7           |
| COMSAT7    | 2025      | 1.7           |
| COMSAT8    | 2035      | 1.7           |

COMSAT systems also account for ground-based receiver technology. Even with full satellite coverage, insufficient receivers reduce the effective bonus.

### SPYSAT (Reconnaissance Satellites)

Spy satellites provide intelligence gathering, weather prediction for air operations, and naval detection capabilities.

| Generation | Available | Research Cost |
| ---------- | --------- | ------------- |
| SPYSAT1    | 1965      | 1.7           |
| SPYSAT2    | 1975      | 1.7           |
| SPYSAT3    | 1985      | 1.7           |
| SPYSAT4    | 1995      | 1.7           |
| SPYSAT5    | 2005      | 1.7           |
| SPYSAT6    | 2015      | 1.7           |
| SPYSAT7    | 2025      | 1.7           |
| SPYSAT8    | 2035      | 1.7           |

Spy satellites that are not assigned to the military or civilian constellation can be deployed on dedicated espionage missions.

### KILLSAT (Anti-Satellite Weapons)

Anti-satellite weapons allow you to target enemy satellites and, at higher tiers, unlock orbital fire support. This branch starts later and has stricter requirements.

| Generation | Available | Research Cost |
| ---------- | --------- | ------------- |
| KILLSAT1   | 1985      | 2.0           |
| KILLSAT2   | 1995      | 2.0           |
| KILLSAT3   | 2005      | 2.0           |
| KILLSAT4   | 2015      | 2.0           |
| KILLSAT5   | 2025      | 2.0           |
| KILLSAT6   | 2035      | 2.0           |

**Requirements**: KILLSAT technologies require both the Space Program **and** the Space-Based Weapons project to be completed. KILLSAT3 additionally unlocks the Space Artillery special project.

### OLV (Orbital Launch Vehicles)

Orbital Launch Vehicles are the rockets used to deliver satellites (and other payloads) into orbit. Higher tiers cost more but are necessary for deploying advanced satellite generations.

| Generation | Available | Research Cost |
| ---------- | --------- | ------------- |
| OLV1       | 1965      | 2.0           |
| OLV2       | 1975      | 2.0           |
| OLV3       | 1985      | 2.0           |
| OLV4       | 1995      | 2.0           |
| OLV5       | 2005      | 2.0           |
| OLV6       | 2015      | 2.0           |
| OLV7       | 2025      | 2.0           |
| OLV8       | 2035      | 2.0           |

Starting with OLV6, the tech tree branches into reusable variants that reduce costs and build time.

---

## Building Satellites

Satellites are built through the missile/space production system. Each satellite type has a production cost (as a percentage of GDP) and a build duration in days.

### Production Costs and Duration

**OLV (Launch Vehicles)**

| Model | Cost (% GDP) | Duration (days) |
| ----- | ------------ | --------------- |
| OLV1  | 0.6%         | 240             |
| OLV2  | 0.8%         | 260             |
| OLV3  | 1.0%         | 280             |
| OLV4  | 1.4%         | 300             |
| OLV5  | 2.8%         | 320             |
| OLV6  | 6.0%         | 340             |
| OLV7  | 14.0%        | 360             |
| OLV8  | 28.0%        | 380             |

**GNSS Satellites**

| Model | Cost (% GDP) | Duration (days) |
| ----- | ------------ | --------------- |
| GNSS1 | 2.0%         | 80              |
| GNSS2 | 5.0%         | 100             |
| GNSS3 | 10.0%        | 120             |
| GNSS4 | 20.0%        | 140             |
| GNSS5 | 30.0%        | 160             |
| GNSS6 | 40.0%        | 180             |
| GNSS7 | 50.0%        | 200             |
| GNSS8 | 60.0%        | 220             |

**COMSAT Satellites**

| Model   | Cost (% GDP) | Duration (days) |
| ------- | ------------ | --------------- |
| COMSAT1 | 10.0%        | 120             |
| COMSAT2 | 20.0%        | 140             |
| COMSAT3 | 30.0%        | 160             |
| COMSAT4 | 40.0%        | 140             |
| COMSAT5 | 50.0%        | 200             |
| COMSAT6 | 60.0%        | 220             |
| COMSAT7 | 70.0%        | 240             |
| COMSAT8 | 80.0%        | 260             |

**SPYSAT Satellites**

| Model   | Cost (% GDP) | Duration (days) |
| ------- | ------------ | --------------- |
| SPYSAT1 | 10.0%        | 100             |
| SPYSAT2 | 20.0%        | 120             |
| SPYSAT3 | 30.0%        | 140             |
| SPYSAT4 | 40.0%        | 160             |
| SPYSAT5 | 60.0%        | 180             |
| SPYSAT6 | 80.0%        | 200             |
| SPYSAT7 | 90.0%        | 220             |
| SPYSAT8 | 100.0%       | 240             |

**KILLSAT Weapons**

| Model    | Cost (% GDP) | Duration (days) |
| -------- | ------------ | --------------- |
| KILLSAT1 | 60.0%        | 120             |
| KILLSAT2 | 80.0%        | 120             |
| KILLSAT3 | 90.0%        | 140             |
| KILLSAT4 | 100.0%       | 160             |
| KILLSAT5 | 110.0%       | 180             |
| KILLSAT6 | 120.0%       | 200             |

### Reusable Launch Vehicles

Starting at OLV6, you can research reusable variants that reduce costs and production time:

| Technology              | Available | Cost Reduction | Time Reduction |
| ----------------------- | --------- | -------------- | -------------- |
| Partially Reusable OLV6 | 2020      | -0.5% GDP      | -10 days       |
| Fully Reusable OLV7     | 2030      | -1.0% GDP      | -25 days       |
| Fully Reusable OLV8     | 2040      | -3.0% GDP      | -45 days       |

Reusable technology is critical for making late-game space programs economically viable, especially for nations without massive GDPs.

---

## Satellite Constellations and Coverage

Satellites are not useful individually. They must be deployed in **constellations** — groups of satellites working together to provide coverage. Each satellite type (GNSS, COMSAT, SPYSAT) operates as both a **military** and **civilian** system, each tracked separately.

### How Coverage Works

Coverage is calculated as a ratio:

**Coverage = Active Satellites / Maximum Capacity**

Coverage ranges from 0% (no satellites) to 100% (constellation fully populated). Bonuses scale linearly with coverage — 50% coverage gives 50% of the maximum bonus.

### Constellation Tiers

Each system has 8 tiers corresponding to the 8 satellite technology generations. Higher tiers provide stronger maximum bonuses but require more satellites to maintain:

| Tier | Minimum Satellites | Maximum Capacity |
| ---- | ------------------ | ---------------- |
| 1    | 0                  | 25               |
| 2    | 5                  | 30               |
| 3    | 10                 | 35               |
| 4    | 15                 | 40               |
| 5    | 20                 | 45               |
| 6    | 25                 | 50               |
| 7    | 30                 | 55               |
| 8    | 35                 | 60               |

The **minimum** is the number of satellites required to sustain the current tier. If your constellation drops below this number, the system automatically downgrades.

### SBAS (Augmentation from Other Satellites)

For GNSS systems, satellites that are not assigned to the active constellation can act as augmentation. Each auxiliary satellite provides up to **+1% bonus** to fill the gap between current coverage and 100%. This means even if your constellation is not fully populated, surplus satellites from other generations can partially compensate.

### Degradation

If the number of satellites in your constellation falls below the minimum for the current tier (due to enemy action, decay, or reallocation), the system automatically **downgrades one tier**. When this happens:

- A news event notifies you of the degradation
- All bonuses recalculate based on the new, lower tier
- The system can degrade all the way to Tier 1 (which has no minimum requirement)

Maintaining your satellite count above the minimums is essential to preserving your space-based advantages.

---

## Satellite Bonuses

All satellite bonuses are applied through the `satellite_system` dynamic modifier. The actual bonus value is: **coverage percentage x maximum value for the current tier**. All three satellite systems (GNSS, COM, SPY) scale identically: Tier 1 caps at 5% for most modifiers, scaling linearly up to 40% at Tier 8.

### GNSS Military Bonuses

Navigation satellites improve precision targeting and movement for all military branches.

| Modifier                         | Tier 1 Max | Tier 4 Max | Tier 8 Max |
| -------------------------------- | ---------- | ---------- | ---------- |
| Army Speed                       | +5%        | +20%       | +40%       |
| Air Close Air Support Efficiency | +5%        | +20%       | +40%       |
| Air Naval Strike Efficiency      | +5%        | +20%       | +40%       |
| Strategic Bomber Bombing Factor  | +5%        | +20%       | +40%       |
| Positioning                      | +2.5%      | +10%       | +20%       |
| Naval Hit Chance                 | +5%        | +20%       | +40%       |

### GNSS Civilian Bonuses

Civilian GNSS improves construction efficiency and resource extraction through precision surveying and logistics.

| Modifier                            | Tier 1 Max | Tier 4 Max | Tier 8 Max |
| ----------------------------------- | ---------- | ---------- | ---------- |
| Building Construction Speed         | +5%        | +20%       | +40%       |
| Infrastructure Construction Speed   | +5%        | +20%       | +40%       |
| Local Resource Gain (all resources) | +5%        | +20%       | +40%       |

### COMSAT Military Bonuses

Communications satellites enhance command structure, coordination, and air defense.

| Modifier                 | Tier 1 Max | Tier 4 Max | Tier 8 Max |
| ------------------------ | ---------- | ---------- | ---------- |
| Max Command Power        | +5         | +20        | +40        |
| Army Organization Factor | +5%        | +20%       | +40%       |
| Planning Speed           | +5%        | +20%       | +40%       |
| Air Escort Efficiency    | +5%        | +20%       | +40%       |
| Air Intercept Efficiency | +5%        | +20%       | +40%       |
| Naval Coordination       | +5%        | +20%       | +40%       |

### COMSAT Civilian Bonuses

Civilian communications improve governance, intelligence operations, and diplomatic reach.

| Modifier               | Tier 1 Max | Tier 4 Max | Tier 8 Max |
| ---------------------- | ---------- | ---------- | ---------- |
| Political Power Factor | +5%        | +20%       | +40%       |
| Decryption Factor      | +5%        | +20%       | +40%       |
| Encryption Factor      | +5%        | +20%       | +40%       |
| Intel Network Gain     | +5%        | +20%       | +40%       |
| Operation Outcome      | +5%        | +20%       | +40%       |

### SPYSAT Military Bonuses

Reconnaissance satellites provide battlefield intelligence, weather data, and naval tracking.

| Modifier                      | Tier 1 Max | Tier 4 Max | Tier 8 Max |
| ----------------------------- | ---------- | ---------- | ---------- |
| Max Planning Factor           | +5%        | +20%       | +40%       |
| Recon Factor                  | +5%        | +20%       | +40%       |
| Air Weather Penalty Reduction | -5%        | -20%       | -40%       |
| Spotting Chance               | +5%        | +20%       | +40%       |
| Convoy Raiding Efficiency     | +5%        | +20%       | +40%       |
| Convoy Escort Efficiency      | +5%        | +20%       | +40%       |

### SPYSAT Civilian Bonuses

Civilian reconnaissance provides research benefits and comprehensive intelligence coverage.

| Modifier                          | Tier 1 Max | Tier 4 Max | Tier 8 Max |
| --------------------------------- | ---------- | ---------- | ---------- |
| Research Speed                    | +5%        | +20%       | +40%       |
| Civilian Intel Factor             | +5%        | +20%       | +40%       |
| Army Intel Factor                 | +5%        | +20%       | +40%       |
| Navy Intel Factor                 | +5%        | +20%       | +40%       |
| Airforce Intel Factor             | +5%        | +20%       | +40%       |
| Root Out Resistance Effectiveness | +5%        | +20%       | +40%       |

---

## Spy Satellite Missions

Spy satellites that are not assigned to your military or civilian constellations can be deployed on dedicated espionage missions against other countries. The number of available mission slots is:

**Available Missions = Total SPY Satellites - Military Constellation - Civilian Constellation - Active Missions**

This means you must balance your spy satellite allocation between passive constellation bonuses and active intelligence-gathering missions.

---

## Advanced Space Projects

### Space-Based Weapons

The Space-Based Weapons project unlocks after completing the Space Program:

| Property    | Value                                            |
| ----------- | ------------------------------------------------ |
| Duration    | 180 months (15 years)                            |
| Requirement | Completed Space Program                          |
| Unlocks     | KILLSAT technology line (anti-satellite weapons) |

The AI prioritizes this for Superpowers and Great Powers that have already completed the space program.

### Space-Based Solar Farms

A civilian application of space technology that provides energy bonuses:

| Property    | Value                                 |
| ----------- | ------------------------------------- |
| Duration    | 180 months (15 years)                 |
| Requirement | Advanced Modern Renewables technology |
| Resources   | 3 tungsten + 2 chromium               |
| Reward      | Space-based solar farms national idea |

An improved version is also available:

| Property    | Value                                 |
| ----------- | ------------------------------------- |
| Duration    | 90 months (7.5 years)                 |
| Requirement | Improved Modern Renewables technology |
| Resources   | 4 tungsten + 2 chromium               |
| Reward      | Improved space-based solar farms idea |

### Orbital Fire Support

The most advanced space weapon system, unlocked at KILLSAT3:

| Property    | Value                                                         |
| ----------- | ------------------------------------------------------------- |
| Duration    | 180 months (15 years)                                         |
| Requirement | KILLSAT3 technology + advanced artillery technology           |
| Visibility  | Only available if futuristic special projects are enabled     |
| Reward      | Unlocks the Space Artillery support company and its equipment |

This provides a support company that can be attached to divisions for orbital precision strikes.

---

## Strategic Tips

1. **Prioritize the Space Program early**: The 15-year duration means you should start as soon as you have ballistic missile technology. Delaying costs you years of satellite coverage.

2. **GNSS first for most nations**: The military bonuses (army speed, CAS efficiency, naval hit chance) and civilian bonuses (construction speed, resource gain) are universally useful. GNSS satellites are also the cheapest to build.

3. **Match your tier to your budget**: You do not need to push to Tier 8 immediately. A Tier 4 constellation at full coverage (40 satellites, +20% bonuses) is often more practical than a Tier 8 at partial coverage.

4. **Watch your minimums**: If your constellation drops below the minimum satellite count for your current tier, the system downgrades automatically. Build replacement satellites before your older ones degrade.

5. **COMSAT receivers matter**: Unlike GNSS and SPYSAT, COMSAT effectiveness depends on ground-based receiver capacity. Even full satellite coverage gives reduced bonuses without sufficient receivers.

6. **Use surplus spy satellites for missions**: Any SPYSAT not needed for your military or civilian constellation can be assigned to espionage missions. This is effectively free intelligence gathering.

7. **Research reusable OLVs**: The cost savings from reusable launch vehicles are substantial at higher tiers. OLV7 and OLV8 are extremely expensive without reusability tech.

8. **KILLSAT is a luxury**: Unless you are a Superpower or Great Power expecting to fight another space-capable nation, the Space Weapons project and KILLSAT line are lower priority than filling your GNSS/COMSAT/SPYSAT constellations.

9. **Space-based solar farms**: If you have renewable energy infrastructure, the solar farm project provides a permanent energy bonus that helps with late-game electricity demands.

---

## Related Documentation

- [Economy Guide](/player-tutorials/economy-guide) - For electricity and building systems
- [Mechanics Guide](/player-tutorials/mechanics-guide) - For power ranking bonuses
- [Military Tutorial](/player-tutorials/military-tutorial) - For how satellite bonuses affect combat
