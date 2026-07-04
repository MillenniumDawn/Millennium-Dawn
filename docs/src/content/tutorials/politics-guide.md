---
title: Politics Guide
description: Comprehensive guide to the political system in Millennium Dawn including ideologies, elections, coalitions, and government mechanics
---

# Politics Guide

Millennium Dawn features a detailed political system with 5 ideology groups, 24 subideologies, multi-party elections, coalition governments, approval ratings, and political laws. This guide explains how the political system works and how you can interact with it as a player.

## Table of Contents

- [Ideology Groups](#ideology-groups)
  - [Democratic](#democratic)
  - [Communism (Emerging)](#communism-emerging)
  - [Fascism (Salafist)](#fascism-salafist)
  - [Neutrality (Non-Aligned)](#neutrality-non-aligned)
  - [Nationalist](#nationalist)
- [Subideologies](#subideologies)
- [Government Popularity](#government-popularity)
- [Elections](#elections)
  - [How Elections Work](#how-elections-work)
  - [Calling Early Elections](#calling-early-elections)
  - [Suspending Elections](#suspending-elections)
- [Coalitions](#coalitions)
  - [Coalition Formation](#coalition-formation)
  - [Coalition Strength](#coalition-strength)
  - [Coalition Collapse](#coalition-collapse)
- [Party Management](#party-management)
  - [Boosting Parties](#boosting-parties)
  - [Attacking Parties](#attacking-parties)
  - [Banning and Legalizing Parties](#banning-and-legalizing-parties)
- [Ideology Drift](#ideology-drift)
- [Political Reform Laws](#political-reform-laws)
- [Ideological Powers](#ideological-powers)
  - [Communists](#communists)
  - [Socialists](#socialists)
  - [Conservatives](#conservatives)
  - [Liberals](#liberals)
  - [Autocrats](#autocrats)
  - [Monarchists](#monarchists)
  - [Fundamentalists](#fundamentalists)
- [Regime Change](#regime-change)
  - [Coups and Civil Wars](#coups-and-civil-wars)
  - [Leader Retirement and Term Limits](#leader-retirement-and-term-limits)
- [Strategic Tips](#strategic-tips)

---

## Ideology Groups

Millennium Dawn has five main ideology groups. Each group determines your government type, available diplomatic actions, and which subideologies can rule.

### Democratic

The Western/democratic group includes parties that support elections and democratic governance. Democratic nations follow different rules than other ideology groups:

- **Can hold elections** (automatically triggered at the end of each term)
- **Cannot declare war on other democratic nations**
- **Can only justify war goals on countries seen as a threat**
- **Can lower international tension** through diplomacy
- Elections determine which subideology leads the government

### Communism (Emerging)

The communist/emerging group covers left-wing authoritarian and revolutionary ideologies, including both secular communist states and Shiite theocratic governments (Vilayat-e Faqih). These governments:

- Can declare war on any nation, including other communist states
- Can justify war goals freely
- Cannot lower international tension
- Elections may or may not be allowed depending on the specific subideology

### Fascism (Salafist)

The fascism group in Millennium Dawn represents Salafist and theocratic monarchist ideologies rather than historical fascism. It includes pro-establishment Salafist kingdoms and Salafi jihadist movements. These governments:

- Have increased war impact on world tension (1.5x)
- Can declare war on any nation
- Typically do not hold elections

### Neutrality (Non-Aligned)

The non-aligned group is the most diverse, covering autocrats, conservatives, oligarchs, libertarians, greens, social democrats, and communists who don't fit the other categories. Non-aligned nations:

- Have reduced war impact on world tension (0.5x)
- Can declare war on any nation
- Elections may or may not be allowed depending on the subideology

### Nationalist

The nationalist group covers right-wing authoritarian movements including populists, military juntas, fascists, and monarchists. These governments:

- Have increased war impact on world tension (1.5x)
- Can declare war on any nation
- Typically do not hold elections

---

## Subideologies

Each ideology group contains several subideologies, for a total of 24. Each country has political parties corresponding to these subideologies, with varying levels of popularity. The subideology of the ruling party determines specific policy options and modifiers.

**Democratic (indices 0-3):**

| Index | Subideology       | Description                                        |
| ----- | ----------------- | -------------------------------------------------- |
| 0     | Western Autocracy | Authoritarian-leaning democrats                    |
| 1     | Conservatism      | Center-right parties                               |
| 2     | Liberalism        | Center-left and liberal parties                    |
| 3     | Socialism         | Social democratic and democratic socialist parties |

**Communism (indices 4-9):**

| Index | Subideology              | Description                              |
| ----- | ------------------------ | ---------------------------------------- |
| 4     | Communist State          | Marxist-Leninist single-party states     |
| 5     | Anarchist Communism      | Libertarian communist movements          |
| 6     | Conservative (Emerging)  | Reactionary left-wing parties            |
| 7     | Autocracy (Emerging)     | Authoritarian communist regimes          |
| 8     | Moderate Vilayat-e Faqih | Moderate Shiite revolutionary governance |
| 9     | Hardline Vilayat-e Faqih | Hardline Shiite revolutionary governance |

**Fascism (indices 10-11):**

| Index | Subideology | Description                           |
| ----- | ----------- | ------------------------------------- |
| 10    | Kingdom     | Pro-establishment Salafist monarchies |
| 11    | Caliphate   | Salafi jihadist movements             |

**Neutrality (indices 12-19):**

| Index | Subideology                | Description                           |
| ----- | -------------------------- | ------------------------------------- |
| 12    | Neutral Muslim Brotherhood | Moderate Islamist parties             |
| 13    | Neutral Autocracy          | Non-aligned autocratic governments    |
| 14    | Neutral Conservatism       | Non-aligned conservative parties      |
| 15    | Oligarchism                | Oligarchic governments                |
| 16    | Neutral Libertarian        | Libertarian parties                   |
| 17    | Neutral Green              | Green and environmentalist parties    |
| 18    | Neutral Social Democracy   | Non-aligned social democratic parties |
| 19    | Neutral Communism          | Non-aligned communist parties         |

**Nationalist (indices 20-23):**

| Index | Subideology           | Description                          |
| ----- | --------------------- | ------------------------------------ |
| 20    | National Populism     | Right-wing populist movements        |
| 21    | Military Junta        | Military dictatorships               |
| 22    | Nationalist Autocracy | Right-wing authoritarian governments |
| 23    | Monarchist            | Traditional monarchies               |

---

## Government Popularity

Government popularity (also called approval rating) is a dynamic variable that tracks how much public support your ruling coalition has. It is displayed in the Politics window and applies a dynamic modifier that affects:

| Effect                     | How It Scales                                                       |
| -------------------------- | ------------------------------------------------------------------- |
| Stability                  | Bonus at high popularity, penalty at low                            |
| Political Power Generation | Bonus at high popularity, penalty at low                            |
| Ideology Drift Defense     | Stronger defense against opposing ideology drift at high popularity |
| Immigration Rate           | Higher popularity attracts more immigrants                          |

Government popularity is calculated from the combined party popularity of all parties in your ruling coalition. Losing elections, facing economic crises, or having unpopular policies can reduce it. Winning elections, maintaining stability, and passing popular reforms increase it.

---

## Elections

### How Elections Work

Democratic nations hold elections automatically at the end of each government term. When an election is triggered:

1. An **election campaign** phase begins, allowing political decisions and events during the campaign period
2. Party popularity scores are snapshot into the election array
3. The party with the most support wins, or if no party has a majority (>50%), a **coalition** must be formed
4. The winning party (or coalition leader) becomes the new ruling party
5. A new government term begins

The election threshold is 5% -- parties below this level are not viable candidates.

### Calling Early Elections

Players can trigger early elections through the **Hold Re-elections** decision:

- **Cost**: 90 political power
- **Cooldown**: 365 days between elections
- Useful when your party's popularity has grown and you want to secure a stronger mandate, or when you want to trigger a government change

### Suspending Elections

Non-democratic governments can permanently suspend elections:

- **Cost**: 125 political power
- **Requirement**: Must be running a non-democratic government (Autocracy, Communist State, Kingdom, Caliphate, Military Junta, etc.)
- Once suspended, elections will not occur automatically and must be re-enabled manually
- Some countries have special restrictions on this decision

---

## Coalitions

### Coalition Formation

When no single party wins more than 50% in an election, a coalition must be formed. The largest party leads the coalition and can invite other parties to join.

**Inviting Coalition Partners:**

- Each of the 24 subideologies can be invited as a coalition partner
- The cost to invite a party depends on **political distance** (how ideologically far they are from you) multiplied by the party's size
- Closer ideological allies cost less to bring into coalition
- You have **30 days** to form a coalition before the mission times out

**If Coalition Formation Fails:**

- The option to **pass leadership** to the second-largest party becomes available
- If that also fails, the AI automatically forms a coalition from the most compatible available parties

### Coalition Strength

Coalition strength is displayed as a percentage and categorized into 9 tiers:

| Tier | Strength Range | Effect                                        |
| ---- | -------------- | --------------------------------------------- |
| 1    | 1-6%           | Very weak -- minimal government effectiveness |
| 2    | 7-10%          | Weak                                          |
| 3    | 11-14%         | Below average                                 |
| 4    | 15-19%         | Moderate                                      |
| 5    | 20-24%         | Average                                       |
| 6    | 25-29%         | Above average                                 |
| 7    | 30-34%         | Strong                                        |
| 8    | 35-39%         | Very strong                                   |
| 9    | 40%+           | Dominant -- maximum government effectiveness  |

Higher coalition strength provides better stability, political power, and drift defense bonuses. Weak coalitions are unstable and vulnerable to collapse.

Each ideology group has its own set of coalition ideas (Democratic, Communist, Nationalist, Salafist, Non-Aligned) that provide modifiers proportional to coalition strength.

### Coalition Collapse

Coalitions can collapse if:

- Coalition partners are removed (refunds 75% of the political power invested)
- The ruling party loses too much popularity
- Events or decisions force a government change
- The coalition leader passes leadership to another party

When a coalition collapses, a new election or coalition formation process may be triggered.

---

## Party Management

Players can actively manage political parties through several actions available in the Politics window:

### Boosting Parties

- **Cost**: 100 political power
- **Effect**: Increases the popularity of a specific party
- **Requirement**: The target ideology group must have >0% support
- Useful for strengthening your ruling party or building support for a desired coalition partner

### Attacking Parties

- **Cost**: 99 political power (49 if the party is already banned)
- **Effect**: Reduces the popularity of a target party
- Useful for weakening opposition parties before elections

### Banning and Legalizing Parties

- **Ban a Party**: 9 political power (without elections) or 99 political power (with elections active)
- **Legalize a Banned Party**: 230 political power
- Banning removes a party from elections and political competition
- Legalizing a banned party restores it but is expensive

---

## Ideology Drift

Ideology drift represents the gradual shift in public opinion toward or away from each ideology group. Several sources contribute to drift:

**Drift Sources:**

| Source                              | Effect                                                                         |
| ----------------------------------- | ------------------------------------------------------------------------------ |
| **Political Reform laws**           | Open nations drift toward democracy; censored nations resist democratic drift  |
| **Ruling party**                    | The ruling ideology naturally gains drift in its favor                         |
| **Foreign influence**               | Other countries can boost ideology drift through diplomatic actions            |
| **Neighbor effects**                | Unstable or ideologically different neighbors cause drift pressure             |
| **Economic cycle**                  | Depression and recession trigger drift toward the ruling ideology's opposition |
| **Faction and alliance membership** | NATO, SCO, GCC membership provides small drift bonuses                         |
| **Internal factions**               | Some factions (Oligarchs, Military, Communist Cadres) provide ideology drift   |

**Drift Defense:**

Government popularity provides drift defense -- the higher your approval rating, the more resistant your country is to opposing ideology drift. Political reform laws and certain national spirits also affect drift defense.

---

## Political Reform Laws

Political reform laws determine how open or closed your government is. They are found in the Politics window and affect democratic drift, political power generation, and research speed.

**Open Nation (7 tiers):**

Moving toward a more open society increases democratic drift and research speed but reduces political power generation and drift defense:

| Direction   | Democratic Drift | Research Speed | Political Power | Drift Defense |
| ----------- | ---------------- | -------------- | --------------- | ------------- |
| More Open   | Increases        | Increases      | Decreases       | Decreases     |
| More Closed | Decreases        | Decreases      | Increases       | Increases     |

Open nations are more vulnerable to ideology drift from foreign influence and neighboring countries, but benefit from higher research speed and attract more international investment.

**Censored Nation (8 tiers):**

Censored nations move in the opposite direction -- stronger censorship provides more political power and drift defense but reduces research speed and democratic influence. The most extreme censorship levels represent totalitarian information control.

The choice between openness and censorship is one of the core political tradeoffs: openness accelerates modernization but makes your government more vulnerable to ideological challenges.

---

## Ideological Powers

Every ideology has unique powers and gameplay elements that are automatically applied when that ideology is in power. You can view all ideological powers and which ones are currently active by clicking the **Ideological Powers** button in the Politics window.

The system groups the 24 subideologies into 7 ideological categories, each with distinct bonuses and penalties. These powers are applied as hidden national ideas that activate based on your ruling party.

### Communists

**Available to:** Communist State (4), Neutral Communism (19)

Communists focus on state-run industrialization, nationalization, and ideological expansion. They can use 5-Year Plans and nationalize foreign assets, but their centrally planned economy requires more workers per building.

| Power                     | Effect                                                                                                                                                                                      |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Spread the Revolution** | +25% boost ideology mission factor -- intelligence operatives are more effective at spreading communist ideology abroad                                                                     |
| **Hard Labour**           | +15% building worker requirement -- centrally planned economies are less efficient, requiring more workers per building                                                                     |
| **5-Year Plans**          | Access to decisions that provide focused bonuses to a chosen economic sector (primary, secondary, tertiary, infrastructure, military, naval, technology, or energy) for the plan's duration |
| **Means of Production**   | Access to decisions to nationalize the industries of your largest foreign influencers, seizing their factories and reducing their influence                                                 |

### Socialists

**Available to:** Socialism (3), Anarchist Communism (5), Neutral Green (17), Neutral Social Democracy (18)

Socialists focus on domestic welfare, economic interventionism, and peaceful diplomacy. They excel at internal investment but are weaker at projecting foreign influence.

| Power                        | Effect                                                                                                                                                                                                         |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Welfare State**            | -15% health spending costs, -15% social spending costs                                                                                                                                                         |
| **Economic Interventionism** | -25% internal investment political power cost, -25% internal investment money cost. Green parties instead get +50% renewable energy infrastructure construction speed                                          |
| **Peaceful Diplomacy**       | Political power bonus or penalty based on Foreign Intervention Law: +15% PP per level below Limited Interventionism, -15% PP per level above it. Isolationist socialists gain PP; interventionist ones lose it |
| **Naive Worldview**          | -15% foreign influence defense -- the focus on diplomacy over power makes the country more vulnerable to foreign ideological pressure                                                                          |

### Conservatives

**Available to:** Conservatism (1), Conservative/Emerging (6), Moderate Vilayat-e Faqih (8), Neutral Muslim Brotherhood (12), Neutral Conservatism (14), National Populism (20)

Conservatives focus on stability, national identity, and resistance to foreign influence. They are the most defensively oriented political ideology.

| Power                | Effect                                                                                                                      |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Good Old Days**    | +15% foreign influence defense -- nostalgia and tradition make the population resistant to foreign ideological pressure     |
| **Stable Society**   | +15% stability                                                                                                              |
| **Patriotism**       | +15% war support. For Moderate Vilayat-e Faqih and Muslim Brotherhood parties, this is replaced with +15% compliance growth |
| **[Country] First!** | -15% foreign influence effectiveness -- domestic focus makes it harder to project your own ideology abroad                  |

### Liberals

**Available to:** Liberalism (2), Neutral Libertarian (16), Technocrats

Liberals focus on free-market economics, investment returns, and productivity. Their market-oriented approach provides strong economic bonuses but weakens military capacity.

| Power                     | Effect                                                                                                                                             |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **High-Risk Investments** | +2% return on investment -- liberal markets take riskier but more profitable investment positions                                                  |
| **The Invisible Hand**    | -15% economic cycle costs, -15% economic cycle upgrade costs, +0.75 productivity growth -- free markets are more efficient at allocating resources |
| **Business Friendly**     | +10% corporate tax income -- pro-business policies attract more taxable economic activity                                                          |
| **Anti-Military**         | -15% military factory output, -15% dockyard output -- liberal governments deprioritize military production                                         |

### Autocrats

**Available to:** Western Autocracy (0), Autocracy/Emerging (7), Neutral Autocracy (13), Oligarchism (15), Military Junta (21), Nationalist Autocracy (22)

Autocrats focus on political control and consolidating power. Their signature mechanic is a corruption-based political power bonus: the more corrupt the nation, the more PP autocrats extract from the system through backroom deals.

| Power                      | Effect                                                                                                                                                                                                       |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Corruption PP Bonus**    | Political power bonus that scales with corruption level (11 tiers). At negligible corruption: +2.7 PP/month. At paralyzing corruption: minimal bonus. Autocrats benefit most from moderate corruption levels |
| **Power Through Strength** | +25% party popularity stability factor -- strongman governance is harder to destabilize                                                                                                                      |
| **Army of Yes-Men**        | -15% army, navy, and air experience gain -- sycophantic commanders reduce military learning                                                                                                                  |
| **Good Connections**       | +10% resource export multiplier (oligarchs only) -- personal connections facilitate resource trade                                                                                                           |

### Monarchists

**Available to:** Kingdom (10), Monarchist (23)

Monarchists concentrate power in a royal family, providing governance efficiency and military inspiration but at the cost of political flexibility.

| Power                  | Effect                                                                                                                                                                          |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Royal Decree**       | -15% cost for all law changes (economic, military, education, health, trade, nuclear, conscription, tax, and MIO laws) -- the monarch can implement policy changes more cheaply |
| **For King and Queen** | +10% army core attack, +10% army core defense -- troops fight harder for their sovereign                                                                                        |
| **Crown Estate**       | +10% population tax income -- the crown's prestige and estates generate additional revenue                                                                                      |
| **Outdated Ideals**    | -15% stability -- monarchist governance clashes with modern political expectations                                                                                              |

### Fundamentalists

**Available to:** Hardline Vilayat-e Faqih (9), Caliphate (11)

Fundamentalists are hardline religious governments that focus on ideological expansion, recruitment, and militant foreign policy, but at the cost of international isolation.

| Power                                | Effect                                                                                                                |
| ------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| **Sharia Law**                       | +10% ideology drift toward the ruling ideology (communism drift for Vilayat-e Faqih, fascism drift for Caliphate)     |
| **Foreign Fighters**                 | +300 weekly manpower -- religious recruitment draws fighters from abroad                                              |
| **Nationalist Liberation Movements** | -10% send volunteers tension, -10% lend-lease tension, +2 volunteer size -- easier to support allied movements abroad |
| **International Pariah**             | -50% minimum export -- international isolation restricts trade                                                        |

---

## Regime Change

### Coups and Civil Wars

Regime change can occur through several mechanisms:

**Civil Wars** are triggered when ideological tensions reach a breaking point. Each radical ideology has its own civil war path:

- Fascist extremist civil war
- Communist state extremist civil war
- Vilayat-e Faqih extremist civil war
- Nationalist autocracy extremist civil war
- Monarchist extremist civil war
- Caliphate extremist civil war

Civil wars split the country and its territory between the existing government and the rebel faction. When a civil war ends, the winning side determines the new government type and whether elections are allowed.

**Coups** can be triggered through diplomatic actions, focus trees, and events. Some major powers (particularly Russia and the USA) have decisions to support coups in other countries. Successful coups change the ruling party without a civil war.

### Leader Retirement and Term Limits

- **Retire Current Leader**: Costs 100 political power. Replaces the current leader with the next one from the leader pool. Some countries have restrictions (e.g., Iran's Supreme Leader, North Korea's Kim dynasty, Singapore's PAP system).
- **Term Limits**: Some countries have term limits that automatically trigger a new leader when the limit is reached. When a term expires, the game generates a new leader from the available pool and assigns the correct ideology trait.

---

## Strategic Tips

### For Democratic Nations

1. **Monitor party popularity before elections**: Boost your party or attack opposition parties to secure a majority and avoid coalition negotiations
2. **Form coalitions with ideologically close parties**: They cost less political power to invite and provide more stable governance
3. **Keep coalition strength above 20%**: Below this threshold, government effectiveness drops significantly
4. **Use political reform wisely**: Opening your society boosts research but makes you vulnerable to ideology drift

### For Authoritarian Nations

1. **Suspend elections early**: 125 political power is a small price for complete political control
2. **Invest in censorship**: Closed nation tiers provide strong political power and drift defense bonuses
3. **Watch ideology drift**: Even without elections, high drift can eventually trigger events that force government changes
4. **Use the autocrat bonus**: Autocratic governments receive double opinion changes from internal faction events, making faction management easier

### General Advice

1. **Political power is your most versatile resource**: It funds party management, elections, coalition formation, policy changes, economic laws, and more. Don't spend it frivolously.
2. **Government popularity matters more than it appears**: The stability, political power, and drift defense bonuses from high approval are substantial and compound over time
3. **Subideology policies are free bonuses**: Check what your ruling party unlocks and plan around those advantages
4. **Economic crises cause political crises**: Depression and recession trigger opposition drift, potentially destabilizing your government. Maintaining economic stability is the best political defense.

---

## Related Documentation

- [Internal Factions Guide](/player-tutorials/internal-factions) - For detailed faction mechanics, events, and decisions
- [Economy Guide](/player-tutorials/economy-guide) - For economic laws and their political interactions
- [International Systems Guide](/player-tutorials/international-systems) - For alliance membership and international political systems
- [Game Rules](/player-tutorials/game-rules)
