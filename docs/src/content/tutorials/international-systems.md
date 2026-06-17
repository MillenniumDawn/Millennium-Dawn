---
title: International Systems Guide
description: Guide to international organizations and systems in Millennium Dawn including the UN, NATO, cyberwarfare, PMCs, and more
---

Millennium Dawn features a range of international organizations, alliances, and systems that shape diplomacy, security, and economics on the world stage. This guide covers how each system works and how you can interact with it as a player.

## Table of Contents

- [United Nations](#united-nations)
- [NATO](#nato)
- [Cyberwarfare](#cyberwarfare)
- [Private Military Companies](#private-military-companies)
- [African Union](#african-union)
- [War on Terror](#war-on-terror)
- [International Financial Institutions](#international-financial-institutions)
- [Monetary Policy](#monetary-policy)
- [Sanctions](#sanctions)
- [Strategic Tips](#strategic-tips)

---

## United Nations

The United Nations operates through two main bodies in Millennium Dawn: the Security Council (UNSC) and the General Assembly (UNGA). Both use voting systems to pass resolutions that affect member states. The UN also manages international recognition, aid programs, and a sanctions regime.

### Membership and Recognition

All internationally recognized nations are UN members. Unrecognized nations and non-state actors face significant penalties:

| Status                          | Political Power | Trade Opinion | Other Penalties                           |
| ------------------------------- | --------------- | ------------- | ----------------------------------------- |
| Lacks International Recognition | -5%             | -10%          | Cannot participate in UN votes            |
| Non-State Actor                 | -10%            | -25%          | -20% research, -5% tax, -1000 ally desire |

**UN Ascension Process**: Unrecognized nations can gain full membership through a two-stage voting process:

1. The Security Council votes to recommend ascension (requires 9+ yes votes, no P5 veto).
2. The General Assembly votes to confirm (requires two-thirds majority).

On success, the nation gains full UN membership with stability, political power, influence, and investment bonuses.

### Security Council

The UNSC is the most powerful body in the UN. It has 15 members: 5 permanent (P5) and 10 elected.

**Permanent Members (P5):** China, France, Russia, United States, United Kingdom.

**Elected Members:** 10 seats distributed by region. Elected members rotate through General Assembly votes, with regional allocation ensuring representation from the Americas, Europe, Africa, and Asia.

**Key Rules:**

- Votes resolve after 5 days.
- 45-day cooldown between Security Council votes.
- Requires 9+ yes votes (out of 15) to pass.
- **Any P5 member voting "No" vetoes the entire resolution**, regardless of other votes.
- Votes can be queued if multiple are pending.
- Players can spend political power and influence to sway other members' votes.

### Security Council Resolutions

The Security Council can pass five types of binding resolutions:

| Resolution                    | Effect                                                                                                                                                      |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Pressure to End War**       | Target nation receives a 210-day mission to end all offensive wars. Failure triggers automatic sanctions.                                                   |
| **Establish Sanctions**       | Applies binding UNSC sanctions with trade and research penalties that scale with the number of UN members (up to -100% trade opinion, -50% research speed). |
| **Restrict Volunteer Forces** | Target nation is blocked from sending volunteer units to other countries.                                                                                   |
| **Arms Embargo**              | Target nation cannot buy or sell weapons on the international market and cannot send or receive lend-lease.                                                 |
| **Recommend UN Ascension**    | Forwards a recognition vote to the General Assembly for an unrecognized nation.                                                                             |

UNSC sanctions are binding on all nations and remain in effect until the Security Council votes to lift them or the target nation's world tension drops sufficiently.

### General Assembly

The General Assembly includes all recognized UN member states. It handles a wider range of topics than the Security Council but its resolutions are non-binding (except for membership and budget votes).

**Key Rules:**

- Most resolutions require a simple majority to pass.
- Membership confirmation and budget changes require a two-thirds majority.
- No veto power.
- Players can set their vote stance to auto-accept or auto-reject all GA votes.
- Players can spend political power and influence to sway votes.

### General Assembly Resolutions

The General Assembly votes on the following:

**Membership and Governance:**

| Resolution                    | Majority Required | Effect                                                                          |
| ----------------------------- | ----------------- | ------------------------------------------------------------------------------- |
| Confirm UN Ascension          | Two-thirds        | Admits unrecognized nation as full UN member                                    |
| Confirm Security Council Seat | Two-thirds        | Confirms elected SC member; failed votes trigger a re-roll from the same region |
| Increase UN Budget            | Two-thirds        | Increases member contribution percentage                                        |
| Decrease UN Budget            | Two-thirds        | Decreases member contribution percentage                                        |

**Non-Binding Sanctions:**

The GA can vote to impose non-binding sanctions, applying trade opinion and research speed penalties that scale with the number of UN members. These are weaker than UNSC sanctions and only apply to nations that voted in favor.

**Non-Binding Resolutions (1-year duration):**

The GA can pass thematic resolutions that grant temporary bonuses to all nations that voted in favor:

| Resolution           | Theme                     |
| -------------------- | ------------------------- |
| Poverty Reduction    | Welfare and development   |
| Food Security        | Agricultural support      |
| Global Health        | Public health initiatives |
| Education Initiative | Literacy and research     |
| Clean Energy         | Renewable energy          |
| Economic Growth      | GDP and construction      |
| Infrastructure       | Building and connectivity |
| Reduced Inequality   | Social equity             |
| Climate Action       | Environmental policy      |
| Peace & Institutions | Governance and stability  |
| Trade Partnerships   | Commerce and trade        |
| Digital Development  | Internet and technology   |

These resolutions last one year and provide passive bonuses related to their theme. Voting in favor of a resolution grants your nation the associated bonus for the duration.

### Voting Mechanics

**How Votes Work:**

1. A vote is queued (triggered by events, decisions, or diplomatic actions).
2. All eligible members receive a voting event with Yes, No, and Abstain options.
3. The vote resolves after 5 days.
4. Results are tallied and the resolution passes or fails based on the required majority.
5. Effects are applied immediately to affected nations.

**Influencing Votes:**

Players can spend political power and influence to sway other nations' votes before they resolve. This is particularly important for Security Council votes where a single P5 veto can block a resolution. You can also reorder the vote queue to prioritize or delay specific resolutions.

### UN Aid Programs

UN membership provides access to several aid and development programs through a dynamic modifier:

| Program | Benefit                                                                                            |
| ------- | -------------------------------------------------------------------------------------------------- |
| UNESCO  | Political power and research speed bonuses                                                         |
| UNIDO   | Construction speed and investment cost bonuses; can lease civilian factories to developing nations |
| UNCDF   | Productivity growth bonuses; reduced internet station and office construction costs                |

The strength of these benefits scales with your participation and the overall UN budget.

### Sanctions

**UNSC Sanctions (Binding):**

- Apply to ALL UN members' trade with the target.
- Trade penalty: -0.5% per UN member (capped at -100%).
- Research penalty: -0.3% per UN member (capped at -50%).
- Remain until the Security Council votes to lift them.

**UNGA Non-Binding Sanctions:**

- Apply only to nations that voted in favor.
- Same penalty formula as UNSC sanctions but narrower scope.
- Can also be applied in response to raid/counter-terror operations.

---

## NATO

NATO is one of the most important military alliances in the game, providing security guarantees and military cooperation to member states.

### Membership

NATO membership is represented by the `NATO_member` national idea. Members gain access to NATO-specific decisions and cooperation programs. Countries can also hold the status of Major Non-NATO Ally, which grants access to some NATO programs without full membership.

### F-35 Joint Strike Fighter Program

One of NATO's key cooperative programs is the F-35 Joint Strike Fighter:

- The USA must first open the F-35 program (to NATO allies or globally).
- NATO members and Major Non-NATO Allies can apply to join the program (costs 50 political power).
- Application takes 30 days to process, with a 270-day cooldown between attempts.
- The USA can blacklist countries from the program.
- Membership grants access to advanced F-35 aircraft production.

### Leaving NATO

Any NATO member can choose to leave the alliance:

- Costs 100 political power.
- Non-democratic governments are more likely to leave.
- Some countries have special AI behavior regarding NATO membership (Turkey stays if led by certain governments, for example).

---

## Cyberwarfare

The cyberwarfare system allows countries to conduct digital operations against rivals. For the full reference (capability levels, operation tiers, success/detection rolls, decryption, defensive operations, and strategy), see the [Cyberwarfare Guide](/player-tutorials/cyberwarfare/).

---

## Private Military Companies

PMCs allow you to hire professional military units for treasury funds rather than using your own manpower and equipment. For the full reference (available PMCs, unit types, costs, and management), see the [Private Military Companies Guide](/player-tutorials/private-military-companies/).

---

## African Union

The African Union (AU) is available to African nations and provides membership benefits through the `AU_member` / `OAU_member` national idea.

### Joining and Leaving

- **Join**: Costs 100 political power. Requires no active wars, no jihadist government, and no military junta.
- **Leave**: Costs 100 political power with no restrictions.
- Morocco has special AI behavior (historically boycotted the AU).

### Benefits

AU membership provides diplomatic and economic benefits. The AU also has a shared focus tree that can unlock an African Investment Fund, providing cheap loans to member states as an alternative to the IMF.

---

## War on Terror

The War on Terror is primarily a USA-focused system that activates around the events of September 11, 2001. Key features:

- **Intelligence Spending**: The USA can increase intelligence spending to detect terrorist threats (costs treasury funds and political power).
- **Afghanistan Storyline**: After 9/11, the USA can demand extradition of Bin Laden, leading to potential military intervention.
- **Counter-Terrorism Operations**: Various decisions for conducting counter-terrorism operations globally.

Other nations can participate through their own focus trees and decisions related to terrorism and security.

---

## International Financial Institutions

### IMF Loans

When your economy struggles, you can request cheap loans from the IMF:

- Costs 50 political power.
- Requires GDP per capita above $5,000.
- Interest rate must be below 15%.
- Cannot have severe corruption.
- Provides a loan at reduced interest rates.
- Can only be requested once per year (365-day cooldown).

### African Investment Fund

African nations that have completed the relevant AU focus can access the African Investment Fund as an alternative to the IMF, with potentially better terms.

---

## Monetary Policy

For full details on monetary policy (Expand Money Supply, Austerity Measures, central bank policy rate, currency backing, and reserve currencies), see the [Economy Guide](/player-tutorials/economy-guide/#currency-and-monetary-policy/).

---

## Sanctions

Sanctions appear throughout the mod at multiple levels:

**UN Security Council Sanctions (Binding):** Applied to all UN members' trade with the target. Trade and research penalties scale with the number of UN members. See [UN Sanctions](#sanctions-1) above.

**UN General Assembly Sanctions (Non-Binding):** Only affect nations that voted in favor. Same scaling formula but narrower scope.

**Unilateral Sanctions:** Major powers (USA, EU, Russia, China) can impose sanctions through their own focus trees and decisions. These come in tiers of increasing severity:

| Tier                            | Construction | Stability | Trade Opinion | Other Effects                     |
| ------------------------------- | ------------ | --------- | ------------- | --------------------------------- |
| Reduced Western Sanctions       | -20%         | -1%       | -10%          | -20% resource exports             |
| Western Sanctions               | -40%         | -2%       | -50%          | -50% resource exports             |
| International Sanctions         | -10%         | -10%      | -50%          | Blocked from international market |
| Massive International Sanctions | -60%         | -10%      | -75%          | -75% resource exports             |

At the International Sanctions level and above, countries are locked out of the international market entirely.

**Raid Sanctions:** Counter-terror and raid operations can trigger separate economic sanctions on target nations, applying trade and research penalties.

Sanctions can be increased or decreased through diplomatic events, focus trees, and international negotiations.

---

## Strategic Tips

### General Diplomacy

1. **Join alliances early**: NATO and AU membership provide tangible benefits and protection.
2. **Monitor UN votes**: Security Council resolutions can force you into unwanted situations. A war pressure resolution gives you only 210 days to comply.
3. **Build cyber capability**: Even a modest cyber program provides intelligence advantages.
4. **Cultivate P5 relationships**: A single P5 veto can block any Security Council resolution, so having a permanent member on your side is invaluable.
5. **Vote on GA resolutions**: Non-binding resolutions provide free bonuses for a year if you vote in favor.

---

## Related Documentation

- [Cyberwarfare Guide](/player-tutorials/cyberwarfare/) -- offensive and defensive cyber operations.
- [Private Military Companies Guide](/player-tutorials/private-military-companies/) -- hiring and managing PMC units.
- [Economy Guide](/player-tutorials/economy-guide/) -- for details on economic mechanics including treasury and debt.
- [European Union Tutorial](/player-tutorials/eu-tutorial/) -- for EU-specific systems.
- [Game Rules](/player-tutorials/game-rules/)
