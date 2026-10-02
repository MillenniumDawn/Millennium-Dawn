---
title: Cyberwarfare
description: How the cyberwarfare system works in Millennium Dawn. Offensive operations, defensive operations, decryption, and strategy.
---

Cyberwarfare allows countries to conduct digital operations against rivals through a slot-based system where you assign targets and launch operations. Operations cost command power, take time to execute, and can succeed or fail based on your offensive capability versus the target's defenses.

## Cyber Capability

Your cyber program is defined by four statistics:

| Stat                  | Range    | Effect                                                                                        |
| --------------------- | -------- | --------------------------------------------------------------------------------------------- |
| **Capability Level**  | 0-5      | Determines which operations you can launch and how many simultaneous targets you can maintain |
| **Offense Power**     | Variable | Increases the success chance of your operations                                               |
| **Defense Rating**    | Variable | Reduces the success chance of incoming operations against you                                 |
| **Attribution Bonus** | 0-100    | Increases the chance of successfully false-flagging your attacks (blaming another nation)     |

**Simultaneous Targets:** You can maintain up to `(capability × 0.5) + 1` targets at once (maximum 10). Each target can have one active operation at a time, and you must wait 90 days between attacks on the same target.

Capability, offense, and defense are improved through technologies, intelligence agency upgrades, and investment decisions. The AI invests in offense and defense automatically.

## Cyber Operations

Operations are divided into four tiers based on capability level. Higher tiers require more capability and cost more command power.

**Tier 1 (Capability > 0) -- 5 Command Power:**

| Operation             | Duration | Effect                                                                            |
| --------------------- | -------- | --------------------------------------------------------------------------------- |
| GPS Jamming           | 60 days  | Military movement debuffs for 90 days                                             |
| Economic Disruption   | 120 days | Economic penalties for 120 days                                                   |
| Propaganda Operations | 120 days | Political penalties for 120 days + reduces ruling party popularity by 3%          |
| Infrastructure Attack | 180 days | Infrastructure penalties for 180 days + damages 1 infrastructure building         |
| Critical Strike       | 365 days | Severe penalties for 365 days + damages 1 industrial complex and 1 infrastructure |

**Tier 2 (Capability > 3) -- 5-10 Command Power:**

| Operation                | Duration | CP Cost | Effect                                                                             |
| ------------------------ | -------- | ------- | ---------------------------------------------------------------------------------- |
| SIGINT Surveillance      | 180 days | 5       | Intelligence penalties for 180 days + grants tracking access for future operations |
| Radar Spoofing           | 30 days  | 5       | Air detection penalties for 30 days                                                |
| Election Interference    | 180 days | 10      | Political instability for 180 days + reduces ruling party popularity by 4%         |
| Industrial Espionage     | 120 days | 10      | Economic penalties for 120 days + grants tracking access                           |
| Communications Intercept | 180 days | 10      | Intelligence penalties for 180 days + grants tracking access                       |

**Tier 3 (Capability > 7) -- 20 Command Power:**

| Operation                    | Duration | Effect                                                                 |
| ---------------------------- | -------- | ---------------------------------------------------------------------- |
| Financial System Attack      | 150 days | Severe economic penalties for 150 days                                 |
| Logistics Disruption         | 90 days  | Military logistics penalties for 90 days                               |
| Sleeper Networks             | 365 days | Long-term infiltration penalties for 365 days + grants tracking access |
| Strategic Deception Campaign | 180 days | Intelligence penalties for 180 days + boosts false flag chance by 25%  |

**Tier 4 (Capability > 11) -- 35 Command Power:**

| Operation       | Duration | Effect                                                                                           |
| --------------- | -------- | ------------------------------------------------------------------------------------------------ |
| Zero-Day Strike | 60 days  | Devastating short-term penalties for 60 days + damages 1 industrial complex and 1 infrastructure |

## Operation Success and Detection

When an operation completes, two rolls determine the outcome:

**Success Roll:** Your effective offense power is compared against the target's defense. Base success chance is your offense power, modified by:

- +10% if you have SIGINT surveillance on the target
- +15% if you have sleeper network access
- +8% if you have communications intercept access
- +5% if you have industrial espionage access
- -10% if the target has Network Hardening active
- -5% if the target has an Attribution Hunt active
- Decryption progress against the target adds a significant bonus

The final success chance is clamped between 5% and 95%. A failed operation wastes the command power and time invested.

**Detection Roll:** If the operation succeeds, a separate stealth roll determines whether you are identified. Base stealth chance starts at 80%, modified by:

- Your attribution bonus (higher = stealthier)
- Decryption progress against the target
- -15% if the target has Counter-Intrusion active
- -20% if the target has an Attribution Hunt active
- -5% if you are at war

**Possible Outcomes:**

1. **Success, Undetected**: The attack lands and the target does not know who did it.
2. **Success, Detected**: The attack lands but the target identifies you as the attacker.
3. **Success, False Flagged**: The attack lands and another nation is blamed instead (chance based on attribution bonus + deception campaign).
4. **Failure**: The operation fails entirely.

## Decryption

Decryption progress is tracked per target nation and represents your accumulated intelligence against their systems. Higher decryption provides:

- **+30% per point** to effective offense power
- **+15% per point** to stealth chance

This makes sustained cyber campaigns against the same target increasingly effective over time. Decryption progress persists between operations.

## Defensive Operations

Three defensive operations are available to protect against incoming attacks:

| Defense                     | Tier | CP Cost | Duration | Effect                                                                                                   |
| --------------------------- | ---- | ------- | -------- | -------------------------------------------------------------------------------------------------------- |
| **Network Hardening**       | 1    | 5       | 120 days | Reduces enemy offense power by 10. Requires being at war.                                                |
| **Counter-Intrusion Sweep** | 2    | 10      | 30 days  | Reduces enemy stealth by 15. Requires active cyber damage (SIGINT, comms intercept, or sleeper network). |
| **Attribution Hunt**        | 3    | 20      | 60 days  | Reduces enemy stealth by 20 and offense by 5. Can be triggered reactively when damaged.                  |

Defensive operations stack with your base defense rating. A country running all three simultaneously is significantly harder to attack and much more likely to identify the attacker.

## Operation Effects

Successful cyber attacks apply timed national ideas (debuffs) to the target. If the same attack is repeated while a previous debuff is still active, the duration refreshes to 75% of the original (preventing indefinite stacking but rewarding sustained campaigns).

The most damaging operations (Critical Strike, Zero-Day Strike) also physically destroy buildings in the target country, making them the only cyber operations with permanent consequences beyond the timed debuff.

**Tracking Access:** Several Tier 2-3 operations (SIGINT, Industrial Espionage, Communications Intercept, Sleeper Networks) grant persistent tracking access flags that boost the success and stealth of all future operations against that target. Building up tracking access before launching high-tier attacks is the optimal strategy.

## Strategic Tips

1. **Build tracking access first**: Use SIGINT, Communications Intercept, and Industrial Espionage to gain tracking access before launching high-tier attacks. Each one adds a significant bonus to future operations.
2. **Invest in defense**: Protecting your own systems is cheaper than recovering from attacks. Network Hardening, Counter-Intrusion, and Attribution Hunts stack with your base defense.
3. **Use Strategic Deception before major attacks**: The +25% false flag bonus makes it much harder for the target to identify you.
4. **Save Zero-Day Strikes for critical moments**: At 35 command power and Tier 4 capability, these are expensive but devastating. The only 60-day operation that destroys buildings.
5. **Sustain campaigns against key targets**: Decryption progress accumulates over time, making repeated attacks against the same target increasingly effective.

## Related Resources

- [International Systems](/player-tutorials/international-systems/) -- the full list of international orgs and systems.
- [Economy Guide](/player-tutorials/economy-guide/) -- for the economic effects of cyber operations.
