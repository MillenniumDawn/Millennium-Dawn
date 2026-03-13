---
title: International Systems Guide
description: Guide to international organizations and systems in Millennium Dawn including the UN, NATO, cyberwarfare, PMCs, and more
---

# International Systems Guide

Millennium Dawn features a range of international organizations, alliances, and systems that shape diplomacy, security, and economics on the world stage. This guide covers how each system works and how you can interact with it as a player.

## Table of Contents

- [United Nations](#united-nations)
  - [Security Council](#security-council)
  - [General Assembly](#general-assembly)
  - [Enforcement](#enforcement)
- [NATO](#nato)
  - [Membership](#membership)
  - [F-35 Joint Strike Fighter Program](#f-35-joint-strike-fighter-program)
  - [Leaving NATO](#leaving-nato)
- [Cyberwarfare](#cyberwarfare)
  - [Cyber Capability](#cyber-capability)
  - [Operations](#operations)
  - [Defense](#defense)
- [Private Military Companies (PMCs)](#private-military-companies-pmcs)
  - [Available PMCs](#available-pmcs)
  - [Hiring Units](#hiring-units)
  - [Costs and Management](#costs-and-management)
- [African Union](#african-union)
- [War on Terror](#war-on-terror)
- [International Financial Institutions](#international-financial-institutions)
- [Monetary Policy](#monetary-policy)
- [Sanctions](#sanctions)
- [Strategic Tips](#strategic-tips)

---

## United Nations

The United Nations operates through two main bodies in Millennium Dawn: the Security Council (UNSC) and the General Assembly (UNGA). Both use voting systems to pass resolutions that affect member states.

### Security Council

The UNSC handles the most consequential resolutions, particularly those involving peace and security. When a Security Council vote is initiated:

- Member states with the `has_sc_mission` flag are presented with a voting mission
- The vote resolves after 5 days
- After a vote concludes, there is a 45-day cooldown before another Security Council vote can occur
- Permanent members can veto resolutions

### General Assembly

The General Assembly handles broader resolutions. Key differences from the Security Council:

- Requires a two-thirds majority to pass
- No veto power
- Covers a wider range of topics

### Enforcement

The Security Council can compel nations to comply with resolutions. For example, the `UNSC_end_all_offensive_wars` mission gives targeted countries 210 days to end all offensive wars. Failure to comply can result in further international consequences.

---

## NATO

NATO is one of the most important military alliances in the game, providing security guarantees and military cooperation to member states.

### Membership

NATO membership is represented by the `NATO_member` national idea. Members gain access to NATO-specific decisions and cooperation programs. Countries can also hold the status of Major Non-NATO Ally, which grants access to some NATO programs without full membership.

### F-35 Joint Strike Fighter Program

One of NATO's key cooperative programs is the F-35 Joint Strike Fighter:

- The USA must first open the F-35 program (to NATO allies or globally)
- NATO members and Major Non-NATO Allies can apply to join the program (costs 50 political power)
- Application takes 30 days to process, with a 270-day cooldown between attempts
- The USA can blacklist countries from the program
- Membership grants access to advanced F-35 aircraft production

### Leaving NATO

Any NATO member can choose to leave the alliance:

- Costs 100 political power
- Non-democratic governments are more likely to leave
- Some countries have special AI behavior regarding NATO membership (Turkey stays if led by certain governments, for example)

---

## Cyberwarfare

The cyberwarfare system allows countries to conduct digital operations against rivals. It operates through a slot-based system where you assign targets and launch operations.

### Cyber Capability

Your cyber capability is determined by several factors:

- **Cyber Capability Level** (0-5): The overall tier of your cyber program, derived from technologies and agency upgrades
- **Offense Power**: Your ability to successfully execute operations, boosted by investment
- **Defense Rating**: Your protection against incoming operations, boosted by investment
- **Attribution Bonus**: Your ability to identify who is attacking you

The number of simultaneous targets you can maintain equals roughly half your capability level plus one (capped at 10).

### Operations

There are five types of cyber operations, each with different durations and effects:

| Operation               | Duration    | Description                                  |
| ----------------------- | ----------- | -------------------------------------------- |
| GPS Tracking            | 60 days     | Intelligence gathering on military movements |
| Economic Tracking       | 60-120 days | Economic espionage and disruption            |
| Propaganda              | 60-120 days | Influence operations and information warfare |
| Infrastructure Attack   | 180 days    | Disruption of critical infrastructure        |
| Critical Systems Attack | 365 days    | Major attack on critical national systems    |

Operations are assigned to slots (one per target). Once launched, they run as timed missions that resolve automatically.

### Defense

Invest in cyber defense to protect your own infrastructure. Countries with higher defense ratings are harder to successfully attack. Technologies and national focuses can improve both offensive and defensive cyber capabilities.

---

## Private Military Companies (PMCs)

PMCs allow you to hire professional military units for treasury funds rather than using your own manpower and equipment. They are available to any country (except special tags).

### Available PMCs

There are five PMC organizations, each with different equipment profiles and alignments:

| PMC        | Equipment Base     | Alignment      | Government-Tied |
| ---------- | ------------------ | -------------- | --------------- |
| Blackwater | USA                | USA-aligned    | No              |
| Wagner     | Soviet             | Soviet-aligned | Yes             |
| Aegis      | British            | UK-aligned     | No              |
| Constellis | Mostly US          | Non-aligned    | No              |
| MD         | Mixed EU/US/Soviet | Non-aligned    | No              |

### Hiring Units

Each PMC offers several unit types:

| Unit Type           | Description                                       |
| ------------------- | ------------------------------------------------- |
| Light Infantry      | Basic infantry battalions with artillery support  |
| Motorized Infantry  | Motorized battalions with recon and armor support |
| Mechanized Infantry | Heavier mechanized forces                         |
| Heavy Mechanized    | Heavy armor and mechanized combined               |
| Special Unit        | Unique specialist forces                          |
| Tank Unit           | Armored formations                                |
| Special Forces      | Elite special operations units                    |

Hiring takes 20 days per unit. Units spawn with locked templates that cannot be modified.

### Costs and Management

- **Upfront Cost**: Each unit has a one-time hiring fee paid from your treasury
- **Weekly Maintenance**: Ongoing treasury expense for deployed PMC units
- **Overlord Discount**: The PMC's home country (e.g., USA for Blackwater) receives a 20% discount on all costs
- **Disbanding**: You can disband PMC units to stop weekly costs

PMC expenses are tracked separately from your regular military budget. Monitor them through the PMC decisions interface.

---

## African Union

The African Union (AU) is available to African nations and provides membership benefits through the `AU_member` / `OAU_member` national idea.

### Joining and Leaving

- **Join**: Costs 100 political power. Requires no active wars, no jihadist government, and no military junta
- **Leave**: Costs 100 political power with no restrictions
- Morocco has special AI behavior (historically boycotted the AU)

### Benefits

AU membership provides diplomatic and economic benefits. The AU also has a shared focus tree that can unlock an African Investment Fund, providing cheap loans to member states as an alternative to the IMF.

---

## War on Terror

The War on Terror is primarily a USA-focused system that activates around the events of September 11, 2001. Key features:

- **Intelligence Spending**: The USA can increase intelligence spending to detect terrorist threats (costs treasury funds and political power)
- **Afghanistan Storyline**: After 9/11, the USA can demand extradition of Bin Laden, leading to potential military intervention
- **Counter-Terrorism Operations**: Various decisions for conducting counter-terrorism operations globally

Other nations can participate through their own focus trees and decisions related to terrorism and security.

---

## International Financial Institutions

### IMF Loans

When your economy struggles, you can request cheap loans from the IMF:

- Costs 50 political power
- Requires GDP per capita above $5,000
- Interest rate must be below 15%
- Cannot have severe corruption
- Provides a loan at reduced interest rates
- Can only be requested once per year (365-day cooldown)

### African Investment Fund

African nations that have completed the relevant AU focus can access the African Investment Fund as an alternative to the IMF, with potentially better terms.

---

## Monetary Policy

Countries have access to monetary policy decisions that affect their currency and economy:

### Expand Money Supply

- Injects liquidity into the economy
- Increases seigniorage income by 25%
- Weakens currency strength by 5%
- Lasts 180 days with a 365-day cooldown
- Cannot be used alongside austerity measures
- Reserve currency issuers benefit most

### Austerity Measures

- Tightens fiscal discipline
- Strengthens currency by 4%
- Lasts 120 days with a 180-day cooldown
- Cannot be used alongside money supply expansion

---

## Sanctions

Sanctions appear throughout the mod as a diplomatic tool used by major powers and international organizations. They can be imposed through:

- UN Security Council resolutions
- Unilateral decisions by major powers (particularly the USA, EU, Russia, China)
- Country-specific focus trees and events

Sanctions typically apply economic penalties to the target nation, reducing trade income, investment returns, and sometimes restricting access to international markets. EU environmental sanctions can target countries that fail to meet renewable energy standards.

---

## Strategic Tips

### General Diplomacy

1. **Join alliances early**: NATO and AU membership provide tangible benefits and protection
2. **Monitor UN votes**: Security Council resolutions can force you into unwanted situations
3. **Build cyber capability**: Even a modest cyber program provides intelligence advantages

### PMC Usage

1. **Use PMCs for small wars**: They avoid using your own manpower and equipment
2. **Watch the costs**: PMC weekly maintenance adds up quickly
3. **Hire the right PMC**: Choose one aligned with your geopolitical position for potential discounts

### Cyberwarfare

1. **Invest in defense first**: Protecting your own systems is cheaper than recovering from attacks
2. **Start with GPS tracking**: Short duration, useful intelligence
3. **Save critical attacks for wartime**: The 365-day duration is a major commitment

---

## Related Documentation

- [Economy Guide](/player-tutorials/economy-guide) - For details on economic mechanics including treasury and debt
- [European Union Tutorial](/player-tutorials/eu-tutorial) - For EU-specific systems
- [Game Rules](/player-tutorials/game-rules)
