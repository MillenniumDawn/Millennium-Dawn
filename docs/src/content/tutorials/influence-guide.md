---
title: Influence Guide
description: Guide to the influence system in Millennium Dawn
---

# Influence Guide

Influence is one of the core diplomatic mechanics in Millennium Dawn. It represents the political, economic, and cultural leverage that countries hold over one another. By building influence in a target nation, you can shape its politics, extract economic benefits, and ultimately turn it into a subject state.

---

## How Influence Works

Every country has a pool of influence that totals 100%. This is divided between **domestic independence** (the country's own sovereignty) and the influence shares held by foreign nations. A country with 80% domestic independence has 20% of its influence held by other countries.

You can view the influence breakdown of any country by opening the **Influence Decisions** category in the Decisions panel. This shows which nations hold influence, the percentage each holds, and your own influence-related modifiers.

---

## Gaining Influence

There are two main ways to gain influence over another country:

### Manual Influence (Spread Influence)

Right-click the influence button on a target country's decision screen to manually spread influence. Each manual action costs **50 Political Power** and has a cooldown (default: 30 days). The amount of influence gained per action is configurable in game rules (default: 1.5%).

### Auto-Influence

Left-click the influence button to set a country as an **auto-influence target**. Auto-influencing applies influence at the end of every month but costs **-1.50 daily Political Power** per target. You have a limited number of auto-influence slots determined by your power ranking:

| Rank           | Base Slots           |
| -------------- | -------------------- |
| Superpower     | 7 (base 3 + 4 bonus) |
| Great Power    | 6 (base 3 + 3 bonus) |
| Large Power    | 5 (base 3 + 2 bonus) |
| Regional Power | 4 (base 3 + 1 bonus) |
| Minor Power    | 3 (base)             |

Auto-influencing cancels automatically if your Political Power drops below -100. You must wait 30 days before cancelling a newly set auto-influence target.

Use **Shift + Left-Click** to clear all auto-influence targets at once.

---

## Influence Modifiers

Several modifiers affect your ability to project influence:

| Modifier                                  | Effect                                              |
| ----------------------------------------- | --------------------------------------------------- |
| Foreign Influence Modifier                | General bonus/penalty to influence gain             |
| Foreign Influence Defense Modifier        | Resistance to being influenced by others            |
| Foreign Influence Continent Modifier      | Penalty when influencing outside your continent     |
| Foreign Influence Home Continent Modifier | Bonus when influencing on your home continent       |
| Monthly Domestic Independence Gain        | How quickly a country recovers its own independence |

These modifiers come from your power ranking national spirit, national focuses, ideas, and other sources.

---

## What Influence Unlocks

As your influence percentage in a target country grows, new actions become available:

### Economic Aid

At moderate influence levels, you can provide economic aid to the target, strengthening your relationship and further increasing influence.

### Manipulate Politics

You can interfere in the target's internal politics, pushing ideology drift toward your own World Outlook. Higher influence makes this more effective.

### Coup

At high influence levels (above ~50%), you can attempt to stage a coup in the target country. Success depends on your influence share and modifiers. A successful coup installs a friendly government; a failed coup damages your influence and relations.

### Make Puppet (Satellite State)

At very high influence (above ~81%), you can force a country into becoming your **satellite state**. This turns them into a subject that sends a portion of their industrial output and trade to you. See the [Satellite States](#satellite-states) section below for a summary, or the [Mechanics Guide](/player-tutorials/mechanics-guide#subject-states) for the full autonomy level comparison.

### Economic Exploitation

Once a country is your subject, you can apply economic exploitation, extracting tribute income from the target at the cost of their economic growth.

---

## Defending Against Influence

Countries can fight back against foreign influence through decisions in the Influence category:

- **Combat Foreign Influence**: Spend Political Power to reduce the influence of the largest foreign influencer.
- **Propaganda Campaign**: Assert domestic independence and reduce foreign influence.
- **Attack Specific Influencer**: Target the 1st, 2nd, or 3rd largest influencer directly.

Domestic independence also recovers naturally over time, modified by the Monthly Domestic Independence Gain modifier.

---

## Satellite States

When your influence over a country exceeds approximately 81%, you can make them a satellite state. Satellite states are a form of subject status with the following characteristics:

| Property             | Satellite State                   |
| -------------------- | --------------------------------- |
| Freedom Level        | 0.50 (moderate autonomy)          |
| CIC to Overlord      | 25% of civilian factories         |
| MIC to Overlord      | 25% of military factories         |
| Trade to Overlord    | 40% extra trade sent              |
| Trade Cost Reduction | -40% for overlord                 |
| Manpower Share       | 70%                               |
| Can Declare War      | No (requires overlord permission) |

As overlord, you can further reduce a satellite's autonomy through the **Reduce Autonomy** decision, though this costs influence.

There are also **Associated States** (higher autonomy, fewer restrictions) and **Puppet States** (lower autonomy, more restrictions) representing different levels of the subject hierarchy. For a full comparison of all autonomy levels, see the [Mechanics Guide](/player-tutorials/mechanics-guide#subject-states).

### Reducing Autonomy

Once a country is your subject, you can further tighten control through the **Reduce Autonomy** decision. This costs **50 Political Power**, has a 30-day duration and 15-day cooldown, and reduces the subject's autonomy by 12%. You must hold at least 5% influence over the subject.

Reducing autonomy enough will transition a subject through the hierarchy: Associated State → Satellite State → Puppet State → Autonomous State.

---

## Influence and Power Ranking

Your power ranking directly affects your influence capabilities. Higher-ranked nations project influence more effectively and resist foreign influence better:

- **Influence Modifier**: Ranges from +50% (Superpower) to -25% (Non-Power)
- **Influence Defense**: Ranges from +50% (Superpower) to -25% (Non-Power)
- **Auto-Influence Slots**: Superpowers get 7 slots; Minor Powers get only 3

Influence also feeds back into power ranking — countries with low domestic independence (heavily influenced by others) receive a penalty to their power ranking calculation, even if their GDP is high. This creates a cycle where losing influence makes it harder to recover.

For full power ranking details, see the [Mechanics Guide](/player-tutorials/mechanics-guide#power-ranking).

---

## Strategic Tips

1. **Focus on high-value targets**: Influence in resource-rich or strategically located countries pays off more than spreading thin.
2. **Use auto-influence for long-term targets**: Manual influence is better for quick pushes; auto-influence is more efficient over time.
3. **Watch your Political Power**: Auto-influencing multiple nations drains PP quickly. Balance influence spending with domestic needs.
4. **Defend your own independence**: If major powers are influencing you, use combat influence decisions before you lose too much sovereignty.
5. **Higher power ranking = better influence**: Superpowers and Great Powers have significant bonuses to influence projection and defense.

---

## Related Documentation

- [Economy Guide](/player-tutorials/economy-guide)
- [Mechanics Guide](/player-tutorials/mechanics-guide)
- [Game Rules](/player-tutorials/game-rules)
