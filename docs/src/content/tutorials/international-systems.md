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

The United Nations runs on two chambers that vote on resolutions affecting member states: the Security Council and the General Assembly. For the full reference (recognition and ascension, exact vote thresholds and cooldowns, all Security Council and General Assembly resolutions, vote swaying, and the aid budget), see the [United Nations Guide](/player-tutorials/united-nations/).

Every internationally recognized nation is a UN member and gets a standing bonus to stability, political power, and foreign influence. Unrecognized nations and non-state actors are locked out of the UN and pay for it:

| Status                          | Political Power | Trade Opinion | Other Penalties                           |
| ------------------------------- | --------------- | ------------- | ----------------------------------------- |
| Lacks International Recognition | -5%             | -10%          | Barred from every UN vote and program     |
| Non-State Actor                 | -10%            | -25%          | -20% research, -5% tax, -1000 ally desire |

Unrecognized nations gain full membership by building recognition from other states, then clearing a two-stage ascension vote: a Security Council recommendation (9+ yes votes, no permanent-member veto), followed by a two-thirds General Assembly admission vote.

The Security Council (5 permanent members plus 10 elected seats, elected on a yearly cycle) passes binding resolutions: pressuring a nation to end its wars, sanctions, volunteer restrictions, and arms embargoes. The General Assembly (every recognized member) confirms ascensions and Security Council seats, adjusts the UN's operating budget, sanctions raid perpetrators, and passes a rotating slate of non-binding development resolutions that grant a year of bonuses to nations that back them. Both chambers queue votes with cooldowns between them, and you can spend political power and influence to sway another nation's cast vote before it resolves.

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

**UN Security Council Sanctions (Binding):** Applied to all UN members' trade with the target. Trade and research penalties scale with the number of UN members. See the [United Nations Guide](/player-tutorials/united-nations/) for the full breakdown.

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

- [United Nations Guide](/player-tutorials/united-nations/) -- membership, recognition, ascension, voting, and the aid budget.
- [Cyberwarfare Guide](/player-tutorials/cyberwarfare/) -- offensive and defensive cyber operations.
- [Private Military Companies Guide](/player-tutorials/private-military-companies/) -- hiring and managing PMC units.
- [Economy Guide](/player-tutorials/economy-guide/) -- for details on economic mechanics including treasury and debt.
- [European Union Tutorial](/player-tutorials/eu-tutorial/) -- for EU-specific systems.
- [Game Rules](/player-tutorials/game-rules/)
