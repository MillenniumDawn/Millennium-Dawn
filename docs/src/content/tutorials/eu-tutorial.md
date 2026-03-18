---
title: European Union Tutorial
description: Updated guide to the European Union in Millennium Dawn
---

The following guide is a comprehensive tutorial for the European Union system in Millennium Dawn. It covers the EU's mechanics, institutions, decision categories, focus trees, and strategic tips for players.

# Table of Contents

- [Table of Contents](#table-of-contents)
  - [Chapter 1 - The European Union](#chapter-1---the-european-union)
  - [Chapter 1.1 - The European Union in Millennium Dawn](#chapter-11---the-european-union-in-millennium-dawn)
  - [Chapter 1.2 - The European Institutions](#chapter-12---the-european-institutions)
    - [The European Union has six main institutions:](#the-european-union-has-six-main-institutions)
    - [In the EU's unique institutional set-up:](#in-the-eus-unique-institutional-set-up)

The European Union (EU) is a unique supranational organization in Millennium Dawn. Unlike most organizations in Hearts of Iron IV, the EU is not a playable country tag (although an internal `EUU` tag exists for background processing). Instead, the EU is played through its member states. Players control their nation's role within the EU through influence, euroscepticism, shared focus trees, parliamentary votes, council decisions, EU offices, and the fiscal system.

Two main paths of deep integration exist:

- **United States of Europe (USoE)** -- A federal union that annexes all EU member states under a single country.
- **President of the European Federation (POTEF)** -- A confederation where an elected EU President leads shared military doctrines, environmental policies, and EU-wide projects while member states retain sovereignty.

The EU can be disabled entirely via game rules at the start of a campaign.

## 2. EU Membership

### 2.1 Membership Status

Countries interact with the EU at three levels:

- **EU Potential** -- Countries that are geographically and politically eligible to join the EU. This includes most European nations, the Caucasus states (Armenia, Azerbaijan, Georgia), Turkey, and others. These countries appear in the `global.EU_potential` array and can see parts of the EU decision interface.
- **EU Candidate** -- Countries with the `EU_candidate` flag that are actively working toward membership. Candidates receive the "Pre-Accession Assistance" idea, which provides Political Power, tax bonuses, and reduced corruption costs.
- **EU Member** -- Countries with the `EU_member` idea. Full members gain access to the EU shared focus tree, can vote on EU laws, hold EU offices, participate in the single market, and join the Eurozone.

### 2.2 Joining the EU

To apply for membership (via the "EU Apply for Membership" decision), a candidate country must meet these requirements:

- Hold the `EU_candidate` country flag (typically gained through national focus trees or events).
- Have a breach of EU values score below 3.
- Not be at war.
- Have no significant external influence from Russia or China (less than 15% influence from either).
- Have euroscepticism below 15%.
- Spend 50 Political Power.

Upon joining, the new member receives the `EU_member` idea, is added to the `global.EU_member` array, and gains opinion modifiers with all other EU members. If the European Defence Union (EDU) exists, the new member also joins that military alliance.

### 2.3 Pre-Accession Assistance

Candidate countries that have not yet joined can receive a Pre-Accession Assistance program. This is a timed mission that, upon completion, triggers an event from the country that sponsored the candidate's application. Successful completion grants 400 Political Power. The program requires reduced corruption levels to complete.

## 3. Euroscepticism

Euroscepticism is one of the two central variables driving the EU. Each EU potential country has an `eurosceptic` variable ranging from 0.0 (fully pro-European) to 1.0 (maximum euroscepticism). This value determines:

- Whether the government is classified as eurosceptical.
- Whether a country's government supports EU exit.
- How AI nations vote on EU laws.
- Whether certain EU focuses and decisions are available.

### 3.1 Euroscepticism Thresholds

The euroscepticism thresholds vary by ruling ideology:

| Ruling Ideology         | Eurosceptical Threshold | EU Exit Threshold |
| ----------------------- | ----------------------- | ----------------- |
| Conservative            | 0.50                    | 0.60              |
| Liberal                 | 0.60                    | 0.70              |
| Social Democrat / Green | 0.60                    | 0.70              |
| Communist               | 0.60                    | 0.70              |
| Nationalist (any)       | Always                  | Always            |
| Other                   | 0.50                    | 0.60              |

Nationalist governments (National Populism, Fascism, Autocracy, Monarchist) are always considered eurosceptical, regardless of the eurosceptic variable.

### 3.2 Changing Euroscepticism

Euroscepticism changes through several mechanisms:

- **Pro-European campaigns** -- Available through the EU GUI, these spend Political Power to reduce euroscepticism in your country or in a target member state. Success is not guaranteed.
- **Euroscepticism campaigns** -- The reverse: spend Political Power to increase euroscepticism. Useful if you want to leave the EU.
- **Focus tree effects** -- Many EU shared focuses and national focuses modify euroscepticism.
- **Single market investments** -- Investing in another EU member's economy (building civilian industry or infrastructure) reduces euroscepticism by 0.03 in both the investor and the target country.
- **EU law votes** -- Passing or failing laws can shift euroscepticism.
- **Breach of EU values** -- Being found in breach increases euroscepticism by 0.15; having that determination revoked decreases it by the same amount.
- **Voting rights suspension** -- Increases euroscepticism by 0.30.

### 3.3 Europeanism

Europeanism (`global.var_europeanism`) is the aggregate pro-European sentiment across all EU member states, weighted by population. It is calculated as: for each member, `(1 - eurosceptic) * population`, summed and divided by total EU population. This global variable gates certain EU focuses and AI behavior. When Europeanism is high (above 0.85), the AI slows further integration; when it is low, the AI becomes more cautious about ambitious EU projects.

## 4. EU Influence

Influence is a core mechanic in Millennium Dawn, and it plays a critical role within the EU. Each country has an `influence_array` that tracks which countries have the most influence over them, along with corresponding percentage values.

### 4.1 How Influence Matters for the EU

- **Proposing and passing EU laws** -- Many EU focus tree actions require that the proposing country has a minimum level of influence over all other EU members (typically 3%, 5%, 10%, 25%, or 50% on all members).
- **Holding EU offices** -- Influence determines eligibility for leadership positions.
- **EU foreign policy** -- The country holding the EU Foreign Minister office (or, failing that, the Commission President) leads EU foreign policy. Passing international treaties requires either 5% influence on all members or a combination of 3% influence alongside the policy leader also having 3%.
- **Treaty ratification** -- Trade agreements and international treaties require similar influence thresholds.
- **Blocking external powers** -- If Russia or China has more than 15% influence on an EU member, that member cannot join the EU or may oppose integration measures. The AI heavily penalizes votes for integration if external powers have 5%, 10%, or 15%+ influence.

### 4.2 Building Influence

Within the EU, influence can be built through:

- **Investing in the single market** -- Building factories or infrastructure in other member states boosts influence and reduces euroscepticism.
- **Monetary transfers** -- The `EU_money_for_influence` effect grants treasury to the target and 1% influence.
- **Holding EU offices** -- Certain offices provide diplomatic bonuses that make maintaining influence easier.
- **Focus tree completion** -- Specific EU shared focuses grant influence.

## 5. EU Institutions and Offices

The EU has a system of offices that member states can hold. Each office provides unique modifiers and confers responsibilities. A country can only hold one EU office at a time and cannot immediately take a new office after leaving one (a cooldown flag prevents this).

### 5.1 Available Offices

| Office                         | Key Modifier                                                                        | Special Role                                    |
| ------------------------------ | ----------------------------------------------------------------------------------- | ----------------------------------------------- |
| European Commission President  | +0.30 Political Power/day                                                           | Leads EU trade policy (fallback)                |
| European Council President     | +0.15 Political Power/day                                                           | Ceremonial leadership                           |
| European Parliament President  | +0.10 Political Power/day                                                           | Parliamentary leadership                        |
| Frontex Executive Director     | +0.10 Political Power/day                                                           | Controls EU Border Guard Teams                  |
| EU Foreign Minister            | +0.05 Foreign Influence, +25% Opinion Gain, +25% Trade Opinion, -50% Relations Cost | Leads EU foreign policy                         |
| ECB President                  | -15% Economic Cycle Upgrade Cost, +0.10 Political Power/day                         | Manages Eurozone monetary policy, budget drafts |
| EU Finance Minister            | +0.10 Political Power/day, -10% Tax Rate Change Cost                                | Fiscal management                               |
| EU Ambassador to UNSC          | +0.15 Political Power/day                                                           | UN representation                               |
| EU Army Supreme Commander      | -10% Army Personnel Cost, +10% Mil Factory Productivity, +10% Army Org/Morale       | Commands the EuroArmy                           |
| EU Navy Supreme Commander      | -10% Navy Personnel Cost, +10% Dockyard Productivity, +10% Naval Coordination/Range | Commands the EuroNavy                           |
| EU President (Federation only) | +0.50 Political Power/day                                                           | Leads the European Federation                   |

### 5.2 Office Eligibility

To hold an office, a country must:

- Be an EU member (`has_idea = EU_member`).
- Not currently hold another EU office.
- Not have a `recently_retired_from_an_eu_office` cooldown flag.
- For major offices, human players and nations with more than 5% of total EU population are prioritized.

When an officeholder loses EU membership, the office is automatically vacated and an election event fires for all members.

## 6. The EU Shared Focus Tree

The main EU shared focus tree is divided into multiple branches that govern EU legislation and deep integration. All EU potential countries can see this tree, but most focuses require EU membership to take.

### 6.1 Legislative Process

EU laws follow a two-stage process:

1. **European Parliament Vote** -- A law is placed on the EP agenda. MEP (Member of European Parliament) support is calculated based on party group influence. The vote runs as a timed mission (14 days). If the EP approves (majority of MEP support), the law advances to the Council.
2. **European Council Vote (QMV)** -- The law is then voted on by member states using Qualified Majority Voting. QMV requires 55% of member states representing at least 65% of the EU population to vote in favor. Each member state votes yes or no based on influence, euroscepticism, external power influence, and AI difficulty settings.

If either vote fails, the law does not pass, and the parliamentary agenda resets after a delay.

For the complete flowchart of EU law progression, see the [EU Law Flowchart](/player-tutorials/eu-law-flowchart/).

### 6.2 Focus Categories

The EU focus tree is organized by law number prefixes:

- **EU1xx** -- Foundational integration (single market reforms, treaty changes, QMV expansion).
- **EU2xx** -- Economic and fiscal union (banking union, Eurobonds, stability mechanisms, fiscal union, economic government).
- **EU3xx** -- Justice and home affairs (data protection, copyright, migration, asylum).
- **EU4xx** -- Security and defense (defence fund, security council, Frontex, military cooperation).
- **EU5xx** -- External relations and expansion.
- **EU6xx** -- Advanced integration (deeper treaty revision, federation path).
- **EU7xx** -- Exit and withdrawal provisions.
- **EU110/111/112** -- Includes the critical QMV expansion vote and the vote to form the United States of Europe.

### 6.3 Key Focus Milestones

- **EU111 (QMV Reform)** -- Expands qualified majority voting. Passing this focus unlocks the USoE branch of the focus tree.
- **EU112 (Toward a Federal Europe)** -- The vote to establish the European Federation. Sets the `european_federation` global flag and unlocks the POTEF focus tree branch.
- **EU703 (Prepared Exit)** -- Reduces the penalty duration for a no-deal exit from 5 years to 2 years.

## 7. The European Parliament

The European Parliament operates through the scripted GUI system. The EP votes on legislation proposed through the shared focus tree. Key mechanics include:

- **MEP Support** -- Calculated based on party group representation and influence. Different political groups (Social Democrats, Conservatives, Liberals, Greens, etc.) have varying support levels for different types of legislation.
- **Parliamentary Sessions** -- The EP has a cooldown between sessions. Budget drafts and Multi-annual Financial Framework (MFF) drafts can block other parliamentary business.
- **Budget Drafts** -- Annual budget votes that the ECB President (if held) can influence. The budget determines allocation ratios between global expenditure, growth expenditure, and natural resource expenditure.
- **MFF Drafts** -- Multi-year financial framework votes that occur approximately every 3.4 years (1,237 days). These set long-term budget call rates and minimum call rates.

## 8. The European Council

The European Council is the body where member states vote on proposed EU laws using Qualified Majority Voting.

### 8.1 Voting Mechanics

- Each member state casts one vote (yes or no).
- QMV requires 55% of member states AND their combined population must represent at least 65% of total EU population.
- AI voting is influenced by: influence of the proposing country (5-50% thresholds add positive modifiers), euroscepticism (below 20% adds +40; above thresholds progressively subtracts), external power influence from Russia/China (heavy penalties), and AI difficulty settings.
- Players vote manually through the decision interface.

### 8.2 Breach of EU Values

The Council can take action against member states that violate EU values:

- **Determine a Serious Breach** (requires breach score > 3): Costs 100 Political Power. Increases the target's euroscepticism by 0.15. Requires the proposing country to be in the top 3 influencers of all other members, or to hold the Commission Presidency.
- **Suspend Voting Rights** (requires breach score > 4): The target country receives the `EUU_voting_rights_suspended` idea (-10% Political Power, -10% Stability) and euroscepticism increases by 0.30.
- **Suspend Subsidies** (requires breach score > 4): The target receives the `EUU_subsidies_suspended` idea (-5% Political Power, -5% Stability).
- Each of these actions can be revoked if the breach score drops below the required threshold.

## 9. Eurozone and Economic Integration

### 9.1 Joining the Euro

EU members who do not already have the Euro can adopt it through the "Join the Euro" decision. Requirements:

- Interest rate below 3.5%.
- Corruption at "modest" level or better.
- Economy in "stable growth," "fast growth," or "economic boom."
- GDP per capita above 10,000.
- Costs 100 Political Power.
- Some countries (Denmark, UK, Sweden) have additional historical prerequisites or are AI-reluctant unless Europeanism is very high (above 0.95).

Adopting the Euro grants the `euro` idea, which integrates the country into the ECB's monetary policy system. This also allows you to use the Euro as a foreign reserve currency.

### 9.2 ECB Monetary Policy

The ECB President has special powers:

- **Outright Monetary Transactions (OMT)** -- The ECB can purchase sovereign debt from Eurozone members with high interest rates (above 4.0%), reducing their debt and interest rates. This is capped by a global OMT size limit.
- **Zero Interest Rate Policy** -- An idea that reduces interest rate multiplier by 50%, boosts construction speed by 10%, but reduces stability by 5%.
- **Budget and MFF management** -- The ECB President gets enhanced versions of budget draft missions.

### 9.3 Eurozone Reforms and Crises

If certain economic laws have been passed (European Banking Union, Eurobonds/European Stability Mechanism), a Eurozone Reforms mission activates. If not completed within 900 days, a European Debt Crisis event fires, adding crisis ideas to all Eurozone members. Members with high interest rates and unfavorable debt ratios also receive a National Debt Crisis idea.

Countries in a National Debt Crisis face a Troika Reforms mission: they must improve their economic fundamentals (reduce interest rates, lower corruption, improve growth, reduce spending levels) within 730 days or face further consequences.

### 9.4 Fiscal System

The EU fiscal system includes:

- **Single Market Investment** -- EU members can invest in each other's economies, building civilian industry and infrastructure in other member states. This strengthens influence and reduces euroscepticism.
- **EU Budget** -- Annual budget drafts determine how EU funds are allocated.
- **Multi-annual Financial Framework (MFF)** -- Long-term budget planning that sets call rates for member contributions.
- **Fiscal Union** -- An advanced idea (unlocked through EU laws) that provides +5% tax gain, +15% productivity growth, and +5% stability.
- **European Economic Government** -- Provides tax gain, reduced economic cycle costs, and construction speed bonuses.
- **Euro Bonds** -- Provides return on investment bonuses, eliminates interest rate impact, and boosts construction and stability.

## 10. Leaving the EU

Any EU member can begin the process of leaving the EU.

### 10.1 Invoking Article 50

The exit process begins with invoking Article 50 (setting the `Article_50` flag, triggered through country-specific focuses or events). Once invoked:

1. A 730-day (2-year) exit mission begins.
2. During this period, the country has several options:

### 10.2 Exit Options

- **Negotiate a Withdrawal Treaty** -- Requires 5% influence on all other EU members. If successful, the country leaves with the `withdrawal_treaty` idea (reduced penalties: +0.15 Political Power, -5% Stability, -10% Trade Opinion, +10% Foreign Influence Defense).
- **Prepared No-Deal Exit** -- Costs 150 Political Power. If the exit mission times out, the no-deal penalty lasts only 2 years instead of 5.
- **Unprepared No-Deal Exit** -- If the mission times out without preparation, the country receives the `no_deal_exit` idea for 5 years (Nationalist Drift +5%, -0.25 Political Power, -15% Stability, -25% Trade Opinion).
- **Revoke Article 50** -- Cancel the exit process entirely. This triggers a 180-day cooldown before Article 50 can be invoked again.
- **Extend Article 50** -- Reset the exit timer, buying more time for negotiations. Requires 5% influence on all other members.

### 10.3 Consequences of Leaving

When a country leaves the EU:

- The `EU_member` idea is removed.
- The Euro is removed (if held).
- All EU laws, offices, and associated ideas are stripped.
- Opinion modifiers with other EU members are removed.
- The country leaves the EDU faction (if it exists).
- Focus flags for EU laws are transferred to a remaining member.
- Tech sharing with the EU group ends.

## 11. United States of Europe (USoE)

The United States of Europe is the deepest integration path, representing the full political union of EU members into a single federal state.

### 11.1 Prerequisites

- EU law EU111 (QMV Reform) must have been voted through and passed.
- The country must have the `USoE` flag (set through the focus tree).
- Focus USoE001 ("Constitute the New European Nation") costs 26 focus weeks and requires the EU111 vote to have passed.

### 11.2 Formation Process

Upon completing USoE001:

- The `EU_member` idea is removed (you are now the EU).
- +100 Political Power is granted.
- The USoE shared focus tree branch unlocks.

The "Integrate New Members" decision (costing 1,500 Political Power and requiring 25% influence on all EU members) then allows the USoE leader to annex all remaining EU member states:

- All EU member technologies are shared.
- Unit leaders from annexed states transfer to the USoE.
- European territory from annexed states becomes core territory.
- The annexation event fires for each member.

### 11.3 USoE Focus Tree Branches

After formation, the USoE tree offers three mutually exclusive geopolitical paths:

- **A Game of Spheres (USoE100)** -- Aggressive: war goals against the USA, Russia, and China. Culminates in "A Heart of Iron."
- **Peaceful Coexistence (USoE200)** -- Diplomatic: alliance offers to the USA, Russia, China, and creation of a "Eurosphere" influence bloc.
- **Clash of Civilizations (USoE300)** -- Cultural/religious: expand European influence into the Middle East, Central Asia, and beyond through cultural domination, Crusader imagery, and westernization of allied nations.

Additional USoE decisions include:

- **Capital of Europe** -- Move the capital to Brussels (state 51).
- **Create Eurosphere** -- Extend influence over neighboring countries in Europe, Africa, and the Middle East.
- **Westernize** -- Target non-democratic neighbors for puppeting or democratic integration.

## 12. President of the European Federation (POTEF)

The POTEF path represents a confederal model where EU members remain sovereign but elect a shared President who directs collective policy.

### 12.1 Prerequisites

- EU law EU112 must pass, setting the `european_federation` global flag.
- The country must be an EU member and hold the `EU_president` office.
- Focus POTEF001 costs 10 focus weeks and grants +150 Political Power.

### 12.2 POTEF Mechanics

The EU President is elected by member states through a two-round voting system:

- **First round** -- Absolute majority of member states AND absolute majority of the popular vote required.
- **Second round** -- Relative majority if no absolute majority is achieved.

Population ratio determines each member's weight in the popular vote.

### 12.3 POTEF Focus Tree

The POTEF tree is organized around regional military doctrines and EU-wide policies. Each doctrine provides bonuses to all EU members through dynamic modifiers, with enhanced bonuses if the President belongs to the relevant regional group:

| Doctrine                                                                                        | Region                           | Base Bonus                                            | Enhanced Bonus (if President is from region)          |
| ----------------------------------------------------------------------------------------------- | -------------------------------- | ----------------------------------------------------- | ----------------------------------------------------- |
| Alpine Doctrine (POTEF100)                                                                      | Austria, Switzerland             | +20% Infantry Defense, +10% Terrain Penalty Reduction | +30% Infantry Defense, +20% Terrain Penalty Reduction |
| Benelux Doctrine                                                                                | Belgium, Netherlands, Luxembourg | Trade and economic bonuses                            | Enhanced trade bonuses                                |
| Nordic Doctrine                                                                                 | Scandinavia                      | Naval and cold-weather bonuses                        | Enhanced naval bonuses                                |
| Mediterranean Doctrine                                                                          | Italy, Greece, Cyprus, Malta     | Naval and defensive bonuses                           | Enhanced bonuses                                      |
| And others for Iberian, British, Balkan, Black Sea, Caucasus, Visegrad, Baltic, Eastern regions |                                  |                                                       |                                                       |

Additional POTEF focuses include:

- **Environmental Imperialism (POTEF102)** -- Unlocks decisions to sanction countries on every continent that fail to develop renewable energy infrastructure. Environmental sanctions can be applied globally.
- **Regional environmental targets** -- Separate focuses for North America, South America, Europe, Africa, Asia, Middle East, Pacific, and Oceania.

## 13. EU Military Cooperation

The EU has several layers of military cooperation, all requiring EU membership.

### 13.1 European Defence Fund

An idea granted through the focus tree that provides:

- +5% Military/Dockyard Productivity
- +10% Factory/Dockyard Output

### 13.2 European Security Council

Prevents member states from creating separate factions and provides:

- +25% Political Power
- +25% Max Planning and Planning Speed

This is a prerequisite for creating the European Defence Union (EDU).

### 13.3 European Defence Union (EDU)

Created through the "Create EDU" decision, which requires:

- Holding the EU Foreign Minister office.
- 25% influence on all other EU members.
- The European Security Council idea being active.

When formed:

- All EU members with NATO membership lose it.
- A new EU military faction is created.
- All EU members join the faction.

### 13.4 Military Units

- **Frontex Border Guard Teams** -- Controlled by the Frontex Executive Director. Can be deployed along external EU borders.
- **EuroArmy Brigades** -- Controlled by the EU Army Supreme Commander. A standing European army.
- **EuroNavy** -- Controlled by the EU Navy Supreme Commander. Provides shared naval technology and capabilities.

### 13.5 Military Exercises

If the European Security Council exists, the EU Foreign Minister can conduct military exercises against non-EU (and non-NATO, if the exerciser is in NATO) neighbors:

- Costs 40 Command Power.
- Select a target country and then request an EU member on the border to host the exercise.
- Successfully deploying divisions to the host state earns Army Experience and Command Power (scaled by number of divisions: 1-5 gives 10, 6-10 gives 50, 11+ gives 100).
- Target countries are notified and can run counter-exercises.

## 14. EU Decision Categories

Here is a summary of all EU decision categories available to member states:

| Category                     | Description                                                                            |
| ---------------------------- | -------------------------------------------------------------------------------------- |
| EU Voting                    | Parliamentary and Council vote missions for EU laws                                    |
| EU Offices                   | Apply for and manage EU institutional positions                                        |
| EU Fiscal                    | Single market investments, budget drafts, MFF drafts, Eurozone reforms, Troika reforms |
| EU Defence                   | Frontex control, EuroArmy/EuroNavy control, EDU creation, military exercises           |
| EU Exit                      | Article 50 invocation, revocation, extension, withdrawal treaty, prepared no-deal exit |
| EU Apply for Membership      | Membership application, Euro adoption, Pre-Accession Assistance                        |
| EU USoE                      | USoE-specific decisions (capital, integration, westernization, Eurosphere)             |
| EU Environmental Imperialism | POTEF environmental sanction decisions                                                 |

## 15. Tips for Playing as an EU Member

### 15.1 Building Influence Early

Influence is the single most important lever in EU politics. Without sufficient influence over other member states, you cannot propose laws, hold offices, ratify treaties, or negotiate exits. Prioritize building influence through diplomacy, investments, and trade.

### 15.2 Managing Euroscepticism

Keep your own euroscepticism low if you want to pursue integration. Use pro-European campaigns and single market investments. Be aware that nationalist governments spike euroscepticism regardless of the variable value.

### 15.3 Holding Key Offices

The most impactful offices are:

- **EU Commission President** -- Best Political Power gain, fallback trade policy leader.
- **EU Foreign Minister** -- Best diplomatic modifiers, leads foreign policy, required for EDU creation.
- **ECB President** -- Controls monetary policy, budget drafts, and Eurozone stability.
- **EU Army Supreme Commander** -- Strong military bonuses, controls the EuroArmy.

### 15.4 Timing EU Laws

Do not rush EU law proposals. Each law requires both a parliamentary majority and a QMV majority. If Europeanism is low or euroscepticism is high across member states, laws will fail. Build influence and reduce euroscepticism across the bloc before proposing ambitious integration measures.

### 15.5 Watching External Powers

Russia and China can undermine EU integration by building influence over member states. If either has more than 15% influence on a member, that member will be very unlikely to support EU measures. Use the EU Foreign Minister's diplomatic bonuses and Frontex to counter external influence.

### 15.6 Playing for Exit

If you want to leave the EU:

- Elect a nationalist government or raise euroscepticism above 0.60.
- Invoke Article 50 through your national focus tree or events.
- Consider spending 150 Political Power on the Prepared No-Deal Exit to reduce the penalty from 5 years to 2 years.
- Alternatively, build enough influence (5% on all members) to negotiate a Withdrawal Treaty for reduced penalties.

### 15.7 Pursuing USoE vs POTEF

- **USoE** is best for players who want total control -- you literally annex every other EU member. It requires passing the QMV Reform law (EU111) and having 25% influence over all members for the integration decision.
- **POTEF** preserves member sovereignty but grants the EU President powerful doctrinal bonuses and environmental imperialism capabilities. It requires passing EU112 (European Federation) and winning the presidential election.

Both paths are endgame content that requires significant time investment in building influence and passing EU laws.
