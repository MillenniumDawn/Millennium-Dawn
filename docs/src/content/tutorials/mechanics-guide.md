---
title: Mechanics Guide
description: Guide to power ranking, satellite states, and other core mechanics in Millennium Dawn
---

# Mechanics Guide

This guide covers core Millennium Dawn mechanics that affect every country: power rankings, the autonomy system, and the naval power system.

---

## Table of Contents

- [Power Ranking](#power-ranking)
  - [How Ranking is Calculated](#how-ranking-is-calculated)
  - [Rank Tiers](#rank-tiers)
  - [Rank Benefits](#rank-benefits)
  - [Regional Powers](#regional-powers)
- [Naval Power of the Continent](#naval-power-of-the-continent)
- [Subject States](#subject-states)
  - [Autonomy Levels](#autonomy-levels)
  - [Changing Autonomy](#changing-autonomy)

---

## Power Ranking

Every country in Millennium Dawn is assigned a **power ranking** national spirit that reflects its position on the world stage. This ranking determines your Political Power generation, influence capabilities, law change costs, interest rates, and more.

### How Ranking is Calculated

Power ranking is recalculated twice per year and is based on two factors:

1. **GDP**: Your total economic output from buildings and other sources.
2. **Domestic Independence**: The portion of your influence pool you control (not held by foreign powers).

The formula combines these into a **power ranking contribution**: the higher your GDP and the more independent you are from foreign influence, the higher your ranking. Countries that are heavily influenced by others will have lower rankings even if they have large economies.

### Rank Tiers

There are six tiers of power ranking:

| Rank           | Threshold                         | Can Create Factions |
| -------------- | --------------------------------- | ------------------- |
| Superpower     | >15% of global factory share      | Yes                 |
| Great Power    | >6.5% of global factory share     | Yes                 |
| Large Power    | >2.5% of global factory share     | Yes                 |
| Regional Power | Top nations per region (0.2-2.5%) | No                  |
| Minor Power    | <0.2% but notable                 | No                  |
| Non-Power      | Negligible share                  | No                  |

### Rank Benefits

Each rank provides scaling bonuses and penalties. Higher ranks get better modifiers but also face higher costs for government spending.

| Modifier                   | Superpower | Great Power | Large Power | Regional Power | Minor Power | Non-Power |
| -------------------------- | ---------- | ----------- | ----------- | -------------- | ----------- | --------- |
| Political Power Gain       | +0.6       | +0.5        | +0.4        | +0.2           | --          | --        |
| Political Power Factor     | +60%       | +50%        | +40%        | +20%           | --          | -20%      |
| Influence Modifier         | +50%       | +40%        | +30%        | +20%           | +10%        | -25%      |
| Influence Defense          | +50%       | +40%        | +30%        | +20%           | +10%        | -25%      |
| Auto-Influence Cap Bonus   | +4         | +3          | +2          | +1             | --          | --        |
| Interest Rate Reduction    | -1.5%      | -1.25%      | -1.0%       | -0.5%          | --          | --        |
| Immigration Rate Bonus     | +20%       | +15%        | +10%        | +5%            | --          | --        |
| Law Change Cost Factor     | +80%       | +45%        | +30%        | +20%           | --          | -20%      |
| Expected Military Modifier | --         | --          | --          | --             | --          | -2        |
| Join Faction Tension       | --         | --          | --          | --             | 0.20        | 0.25      |

**Key takeaways:**

- **Superpowers and Great Powers** receive massive Political Power and influence bonuses but pay significantly more for law changes and government spending.
- **Non-Powers** receive reduced Political Power and influence but pay less for government administration.
- **Interest rate reductions** from higher ranks help manage debt more effectively.
- All ranks from Large Power and above can **create factions** (alliances).

### Regional Powers

Within each geographic region, the top countries by contribution are designated as Regional Powers (if they don't already qualify for a higher tier). The number of regional power slots varies by region:

| Region             | Regional Power Slots |
| ------------------ | -------------------- |
| Europe             | 7                    |
| Asia               | 7                    |
| Americas           | 4                    |
| Middle East        | 3                    |
| Sub-Saharan Africa | 3                    |

Regional Power status provides moderate bonuses and represents being a dominant force within your part of the world, even if your global share is small.

---

## Naval Power of the Continent

The country with the most deployed naval manpower in each continent receives the **Naval Power of the Continent** national spirit. This provides:

- **+5% Home Continent Influence**: Bonus to influence projection on your home continent.
- **-5% Navy Personnel Cost**: Reduced upkeep for naval forces.

This spirit is recalculated periodically and can shift between countries as naval deployments change.

---

## Subject States

Countries can become subjects of other nations through the influence system, wartime annexation, or specific event chains. The subject system uses four core autonomy levels with increasing degrees of overlord control.

### Autonomy Levels

| Property                      | Associated State | Satellite State | Puppet State | Autonomous State |
| ----------------------------- | ---------------- | --------------- | ------------ | ---------------- |
| Freedom Level                 | 0.75             | 0.50            | 0.25         | 0.00             |
| CIC to Overlord               | 0%               | 25%             | 50%          | 75%              |
| MIC to Overlord               | 0%               | 25%             | 50%          | 75%              |
| Trade to Overlord             | 20%              | 40%             | 60%          | 80%              |
| Overlord Trade Cost Reduction | -20%             | -40%            | -60%         | -80%             |
| Manpower Share                | 100%             | 70%             | 40%          | 10%              |
| Research Sharing Penalty      | -20%             | -40%            | -60%         | -80%             |
| Can Declare War               | Yes              | No              | No           | No               |
| Can Decline Call to War       | Yes              | Yes             | No           | No               |
| Overlord Controls Units       | No               | No              | No           | Yes              |

**Associated States** are the most independent — they retain full war declaration rights, keep all their factory output, and only send 20% extra trade to the overlord. This is closer to a diplomatic partnership than true subjugation.

**Satellite States** are the default autonomy level when making a new subject through the influence system. The overlord receives 25% of the subject's factory output and 40% extra trade, but the subject cannot declare its own wars.

**Puppet States** give the overlord half of all factory output and require the subject to answer every call to war. This level significantly limits the subject's independence.

**Autonomous States** represent near-total subjugation — 75% of all factories go to the overlord, 80% of trade is redirected, and the overlord directly controls the subject's military units.

### Changing Autonomy

As an overlord, you can reduce a subject's autonomy through the **Reduce Autonomy** decision in the Influence category. This costs 50 Political Power and reduces the subject's autonomy by 12%. You must hold at least 5% influence over the subject.

Some subjects are exempt from autonomy manipulation, including Special Administrative Regions (Hong Kong, Macao, Taiwan), Tibet, East Turkestan, Mongolia, Wagner PMC members, CIS member states, Warsaw Pact members, and Russian federal subjects.

Several nation-specific systems use custom autonomy hierarchies. Russia has a federal subject system with its own promotion chain (Governorate, Okrug, Oblast, Kray, Republic, State). Britain has a devolution system for constituent countries.

---

## Related Documentation

- [Economy Guide](/player-tutorials/economy-guide)
- [Influence Guide](/player-tutorials/influence-guide)
- [Game Rules](/player-tutorials/game-rules)
