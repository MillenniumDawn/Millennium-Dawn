---
title: Conditional Peace Deals
description: How to negotiate peace treaties with state actions, country actions, and VP-based deal scoring
---

Conditional Peace Deals let you negotiate a custom peace treaty with an enemy country instead of fighting to total capitulation. You can demand or concede states, impose political conditions, and extract reparations — all scored through a Victory Point (VP) system that the AI uses to decide whether to accept.

This system is enabled by the **Player-Led Peace Deals** game rule (on by default).

---

## Table of Contents

- [Opening the Builder](#opening-the-builder)
- [Demands vs Concessions](#demands-vs-concessions)
- [State Actions](#state-actions)
- [Country Actions](#country-actions)
- [Deal Cost and VP](#deal-cost-and-vp)
- [Sending the Deal](#sending-the-deal)
- [AI Acceptance](#ai-acceptance)
- [Ceasefire vs White Peace](#ceasefire-vs-white-peace)

---

## Opening the Builder

While at war, open the **Diplomacy** tab for the enemy country. The **Conditional Peace Deal** action appears in the diplomatic actions list. Clicking it opens the peace deal builder GUI.

The builder has two tabs:

- **Demands**: What you want from the enemy. Costs VP.
- **Concessions**: What you offer to the enemy. Gives VP (negative cost).

Switch between them with the tabs at the top of the window.

---

## Demands vs Concessions

**Demands** are terms you impose on the enemy. They cost VP — the more you demand, the less likely the AI is to accept. You need war contribution (VP earned from battles or months at war) to make demands.

**Concessions** are terms you offer to the enemy. They give VP — offering concessions makes the AI more likely to accept. You can only concede states you own and control (you cannot offer your subjects' or allies' territory).

The deal total (shown at the bottom) is the net VP cost. A positive number means you're demanding more than you're offering. A negative number means you're offering more than you're demanding.

---

## State Actions

State actions apply to individual states on the map. Select an action type from the row of buttons, then click states in the list to add them to the deal.

| Action              | Cost Multiplier                         | Effect                                       |
| ------------------- | --------------------------------------- | -------------------------------------------- |
| **Annex**           | 1.0× (0.5× for cores, 0.33× for claims) | Transfer the state to you                    |
| **Puppet**          | 0.5×                                    | Create a puppet regime in the state          |
| **Demilitarise**    | 0.25×                                   | Set the state as a demilitarized zone        |
| **Liberate**        | 0.33×                                   | Give the state to a country with cores on it |
| **Resource Rights** | 0.15×                                   | Take resource rights without annexing        |

States you already control cost 2× more (the enemy values territory they still hold less than territory you've already taken).

Click a state in the **Current Deal** list to remove it. The cost updates automatically.

---

## Country Actions

Country actions apply to the entire enemy country. Toggle them on/off with the buttons in the builder.

| Action                | Effect                                                                                                      |
| --------------------- | ----------------------------------------------------------------------------------------------------------- |
| **Ceasefire**         | Freeze current frontlines, 2-year truce. Clears all state actions (ceasefire means no territorial changes). |
| **War Reparations**   | 0.05% of payer's GDP per week for 1 year, capped at $15B/week.                                              |
| **Forced Neutrality** | Enemy leaves their faction, cannot join factions for 5 years.                                               |
| **Regime Change**     | Installs your ruling party's subideology onto the enemy. Causes 2 years of instability.                     |
| **Military Basing**   | Grants you military access.                                                                                 |
| **Full Puppet**       | Makes the entire enemy country your puppet. Supersedes any individual puppet-in-state entries.              |

Country actions have no VP cost — their impact is handled through AI acceptance modifiers (see below).

---

## Deal Cost and VP

Each state in the deal has a VP cost based on its **strategic value** (visible in the state view) multiplied by the action's cost multiplier. The total is shown in the builder.

Your **war contribution** is tracked through two mechanisms:

- **VP from battles**: Earned by winning combats against the enemy. Visible as `CPD_VP@TAG` variables.
- **Months at war**: Simply being at war for 3+ months counts as contribution.

You need war contribution to send a deal with demands. The send button shows a green check when the deal is sendable and a red X with tooltip breakdown when it isn't.

---

## Sending the Deal

Click **Send** to deliver the deal to the enemy. The AI evaluates it immediately:

- If accepted: all terms execute, the war ends, and a truce is set (360 days normally, 720 days for ceasefires).
- If rejected: you get a 360-day cooldown before you can send another deal to the same target.

The send button's tooltip shows a full breakdown of why the AI will accept or reject, including each factor's contribution to the acceptance score.

---

## AI Acceptance

The AI decides whether to accept based on a cumulative score starting at -100. The deal is accepted if the total is positive.

### Factors that increase acceptance (AI more likely to accept)

| Factor                            | Max Effect  | Notes                                             |
| --------------------------------- | ----------- | ------------------------------------------------- |
| High interest rate / debt default | Up to +25   | Economic pressure makes peace attractive          |
| Low war support                   | Up to +100  | At 0% war support, +100; at 50%, 0; at 100%, -100 |
| Weaker than sender                | Up to +1000 | Based on enemies_strength_ratio                   |
| Close to surrender                | Up to +100  | At 50% surrender, +50; at 100%, +100              |
| Desperation to end war            | Up to +50   | +25 above 50% surrender, +50 above 75%            |
| Winning more battles than sender  | Up to +150  | Clamped to ±150                                   |
| Long war duration                 | Up to +120  | 2 points per month, capped at 120                 |
| Concessions offered               | Up to +50   | 5 points per VP of concessions                    |
| Non-power ranking                 | +15         | Minor nations more willing to accept              |
| Ceasefire (stalemate)             | +40         | When war > 18 months and surrender < 40%          |
| Low difficulty setting            | +15         | Civilian/Recruit difficulty                       |

### Factors that decrease acceptance (AI less likely to accept)

| Factor                               | Max Effect | Notes                                                                        |
| ------------------------------------ | ---------- | ---------------------------------------------------------------------------- |
| Demands with low war contribution    | Up to -100 | Penalised for demanding without earning VP                                   |
| High deal cost                       | Up to -100 | Progressive penalty above 20/40/60/100 VP                                    |
| Super power ranking                  | -60        | Major powers rarely accept dictated terms                                    |
| Great power ranking                  | -45        |                                                                              |
| Large power ranking                  | -30        |                                                                              |
| NATO/CSTO membership                 | -25        | Faction backing provides confidence                                          |
| Full puppet demanded                 | -200       | +100 if already a subject                                                    |
| Regime change demanded               | -80        | +30 if ruling party is weak (<40%)                                           |
| Forced neutrality demanded           | -60        | -20 base, -40 more if in a faction                                           |
| Military basing demanded             | -25        |                                                                              |
| Resource rights demanded (>3 states) | -40        | -15 for any, -25 more if >3 states                                           |
| War weariness (long wars)            | -60        | -15 at 12mo, -30 at 24mo, -60 at 48mo; suppressed once surrender reaches 50% |
| High difficulty setting              | -30        | -15 per step above Normal                                                    |

---

## Ceasefire vs White Peace

A **ceasefire** is a special deal type: it freezes the current frontlines (each side keeps what it controls), sets a 2-year truce, and clears all state actions. Ceasefires bypass the normal war contribution requirement — you can offer a ceasefire even with no VP.

A normal deal without a ceasefire ends with a **white peace**: all territorial transfers and country actions execute, then the war ends with a 1-year truce (360 days).

If the sender is a faction leader, the white peace applies to the entire enemy faction. If the sender is not a faction leader, they sign a separate peace and leave their faction.
