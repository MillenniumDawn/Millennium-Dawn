---
title: Italy
slug: italy
unique_focus_tree: true
grid_order: 36
flag_image: /assets/images/flags/italy.png
infobox:
  - section: Overview
    stats:
      - label: Tag
        value: ITA
  - section: Military & Industry
    stats:
      - label: Divisions
        value: "14"
      - label: Total Factories
        value: "56"
      - label: Military Ind.
        value: "15"
      - label: Civilian Ind.
        value: "32"
      - label: Naval Dockyards
        value: "9"
  - section: Economy
    stats:
      - label: Treasury
        value: $69 Billions
      - label: Debt
        value: $2606 Billions
      - label: Investments
        value: $100 Billions
---

Italy in 2000 is a G7 economy with a fragile coalition government, a heavy public debt, and a north-south development gap entrenched since unification. It sits in the centre of NATO and the European Union, but its domestic politics are dominated by reform expectancy from Brussels, organised crime in the south, and a chronic mistrust of the political class. The country borders France, Switzerland, Austria, Slovenia, and Croatia, and contains the microstates of San Marino and Vatican City. Population: 57.11 million.

## Basic Information

### Factories

Italy starts with 56 Factories: 32 Civilian Industries, 15 Military Industries, and 9 Naval Dockyards. The civilian base is large but unevenly distributed; the bulk of usable construction capacity is in the north, while southern states host smaller, less productive industry.

### Economy

Italy starts with $69 Billions in the Treasury, $2606 Billions in Debt, and $100 Billions in International Investments. Debt service is the dominant fiscal pressure: the starting interest-rate multiplier modifier is substantially negative, meaning every percentage point above 3% costs the budget more than it would for a less indebted nation.

### Military

Italy starts with 14 Divisions covering the Esercito Italiano. The army is organised around mechanised and motorised brigades with limited modern armour. The navy starts with cruisers, frigates, and submarines distributed across several Mediterranean fleets. The air force operates Tornados and early Eurofighter Typhoons. The volunteer army law is active.

### Resources

Italy is resource-poor: small domestic oil, steel, and aluminium reserves. Energy independence is structurally constrained by the nuclear ban.

### Diplomacy

Italy is a NATO Member, European Union Member, and G7 Member. It maintains close ties to the United States, France, Germany, and the United Kingdom, and is a major participant in EU council voting. It hosts the Vatican and influences the wider Mediterranean.

### Initial Government

Western Left-Wing (Olive Tree / centre-left coalition) holds 34.5% popularity. Western Right-Wing Conservative (Forza Italia and allies) is at 18.9%. Western Liberalism at 15.8%. The remainder is split across Non-Aligned, Nationalistic, and Emerging outlooks. Elections are enabled.

### Domestic Situation

- Economic Cycle: Stagnation
- Corruption Level: Systematic Corruption
- Internal Factions:
  - Labour Unions
  - The Clergy
  - Small and Medium Business Owners
- Police budget tier: Police 03
- Healthcare budget tier: Health 05 (full coverage, costly)
- Social spending tier: Social 05 (maximum, costly)

## Initial National Spirits

In addition to NATO, G7, and EU membership, Italy has 19 unique national spirits at game start:

- **Traditional Education System** — Outdated curriculum and inflexible institutions reduce research and growth.
- **Southern Question** — The Mezzogiorno's underdevelopment depresses national productivity.
- **Brain Drain** — Highly educated workers emigrate, weakening growth and innovation.
- **Tax Evasion** — Widespread informal economy erodes tax receipts.
- **Inefficient Administration** — Bureaucracy slows construction and policy execution.
- **Inefficient Judicial System** — Slow courts hinder enforcement and investor confidence.
- **Building Abuse** — Unregulated construction harms infrastructure speed and stability.
- **Wasted Foreign Funds** — Misallocated EU and international aid drags on the south.
- **Unsustainable Pension System** — High pension expenses crowd out public investment.
- **Legacy of the PCI** — The Italian Communist Party's tradition keeps left-wing drift elevated.
- **Legacy of Fascism** — The post-war republic still wrestles with the MSI's neo-fascist inheritance.
- **Controlled Media (RAI Lotting)** — Political control of state media distorts public discourse.
- **Radio Radicale** — Liberal media keeps a small but active counter-voice in policy debate.
- **Banned Nuclear Power** — The 1987 referendum permanently blocks reactor construction.
- **Major Tourist Destination** — Service income contribution from heritage and culture.
- **Illegal Immigration from Africa** — Migration pressure adds stability and integration challenges.
- **Small and Medium Business** — Italy's SME-dominated economy underpins industrial output but limits scale.
- **World-Renown Cuisine** — Food, wine, and gastronomy add a soft-power and export contribution.
- **The Mafia** — Four organised-crime networks holding territorial influence in the south.

Italy also has three dynamic modifiers always active in the background:

- **Ageing Population** — Negative monthly population growth weighs on every long-term plan.
- **Reforms Expectancy** — A monthly drift mechanic representing pressure from the EU and markets.
- **NIMBY's Influence** — Local opposition slows large-scale infrastructure construction.

## Unique National Features

### The Mafia System

Italy tracks four distinct organisations, each with its own strength variable (0.0 to 1.0):

- **Cosa Nostra** in Sicily (starting strength 0.180)
- **Camorra** in Campania
- **'Ndrangheta** in Calabria
- **Sacra Corona Unita** in Puglia

Strength tiers (matching the in-game display):

| Tier       | Range        |
| ---------- | ------------ |
| Negligible | < 0.10       |
| Low        | 0.10 – 0.40  |
| Medium     | 0.40 – 0.666 |
| Endemic    | > 0.666      |

Each organisation contributes to overall `mafia_strength` (the average of the four). Strength drives:

- **Stability drain** — proportional to strength.
- **Construction speed penalty** — heavy at high strength.
- **Pizzo (protection-money) income** — once you opt into the relevant decision, you collect from controlled regions.
- **Lega party drift** — mafia strength quietly raises the right-wing populist Lega's popularity weekly.
- **Mafia event spam** — regional events fire periodically. Pushing an organisation to Negligible silences its events; Low tier suppresses them to ~25% of baseline rate. A 14-day global cooldown bounds total event frequency even at Endemic strength.

You influence mafia strength through:

- **Pizzo decisions** — pay protection or refuse; refusal raises strength.
- **Police focuses and decisions** — undercover agents, anti-mafia education, judicial reform.
- **Concentration flags** — focus all police on one organisation for a 50% regional bonus but a national penalty.

### Reform Expectancy

A monthly drift representing Brussels and markets demanding economic and social reform. The expectancy variable trends upward from five sources:

- **Stability** — when stability is low, pressure rises. The stability term is clamped to a 30% input floor so a stability spiral can't compound reform pressure indefinitely.
- **Interest rate** — every percentage point above 3% adds pressure proportionally.
- **Social/Health/Education laws** — more generous laws raise pressure; austere laws lower it.
- **War** — being at war with low war-support raises pressure.
- **Taxes** — high tax rates add modest pressure.

A `western_technocrat` country leader adds a fixed bonus to satisfaction.

To satisfy expectancy you accept reforms when the Reforms Expectance event fires, accepting a temporary penalty in exchange for policy changes. Refusing causes coalition friction and drift toward opposition parties.

### Party Popularity Drift

A weekly recalculation of every party's popularity based on:

- Ideology drift modifiers from ideas and focuses.
- Coalition propaganda once you opt to use it.
- Mafia influence quietly feeding the Lega populist party (~3.5% of mafia strength per week, halved for balance).
- Underdeveloped south ideas adding extra southern Lega support.

Ruling-party popularity also influences stability. A coalition that collapses below the abandon threshold (half its current popularity) breaks, triggering a government crisis.

### Regional Development

Italy is divided into northern, central, southern, island, and Roma-municipal focus subtrees. The south carries dedicated deficit ideas (`ITA_underdeveloped_south_1`, `ITA_outdated_education_1`, `ITA_wasted_foreign_funds`) that you peel back through targeted focuses. The Mezzogiorno is also where the four mafias operate, so southern development paths interlock with the mafia mechanic.

### Nuclear Ban

Italy holds `ITA_nuclear_power_banned` from game start, representing the 1987 referendum. The ban prevents any nuclear reactor from being built — by Italy, by allies investing in Italian states, or by the AI as part of its energy planning. To remove the ban you must complete a specific focus path that overturns the referendum politically. Until you do, Italy's energy planning is restricted to fossil and renewable sources.

### EU Membership and Council Voting

Italy is a founding-era EU member and participates in council voting on EU laws (Banking Union, Eurobonds, fiscal union, ESM, and the broader European Stability framework). EU laws granted to Italy provide stability, return-on-investment, and modifier bonuses — they also lock you into eurozone fiscal discipline, which interacts with your interest rate and reform expectancy.

The EU Breach of Values system tracks democratic backsliding. Civil-war participation no longer counts as an "offensive war" against EU members, so internal Italian crises will not trigger automatic expulsion.

### Civil War Path

The italy_md.69 event chain can trigger a civil war from sustained low stability and protest accumulation. Padania secession is the most common branch. After the rebalance, the accumulated stability drift is clamped to ±0.2, the reform-expectancy stability component is held to a 30% input floor, and the party-popularity-to-stability feedback is less aggressive, so getting all the way to a civil war takes deliberate misplay rather than a normal run of bad luck.

## National Focus

### Political and Ideology Branches

The `ITA_what_we_are` focus chooses your political ideology branch. Major sub-branches:

- **Centre-left (Democratic Party / Olive Tree)** — historical default. Stability, EU integration, gradual reform.
- **Centre-right (Forza Italia / National Alliance)** — historical alternative. Pro-business, deregulation, atlanticist defence.
- **Liberals (Social Liberalism / Radical Party)** — civil-rights focus, EU federalism.
- **Left-wing Populism (M5S)** — anti-establishment, basic income, EU sceptical.
- **Right-wing Populism (Lega / National Alliance)** — anti-immigration, EU sceptical, regional autonomy.
- **Greens / LEU** — environmental and social-democratic alternatives to the main centre-left.
- **Italian Communist Party (PCI restoration)** — far-left, eastern alignment.
- **Non-Aligned Communism (PRC)** — democratic socialist, EU sceptical.
- **Fascism** — authoritarian restoration via MSI legacy.
- **Monarchy** — Savoy house restoration.

### Diplomatic Branch

`ITA_diplomatic_focus` leads to alignment paths. The western alignment branch (`ITA_strenghten_ties_with_west`) is the historical default; `ITA_abandon_the_west` opens eastern (Russia, China) or non-aligned (Mediterranean, Africa) paths. Bilateral focuses cover Japan, Israel, Taiwan, the broader Middle East, Southeast Asia, Africa, and the Americas.

### Economic Branches

Regional development: north, central, south, islands, and Rome-municipal. Infrastructure: TAV (high-speed rail), MOSE (Venice flood barriers), hydrogeological safety. Energy: renewables, hydrogen, and the nuclear-ban-overturn path. Industry: tourism, automotive, defence (Leonardo, Fincantieri, Beretta), shipbuilding.

### Judicial, Media, and Church Branches

Anti-corruption reforms, factchecking, media decontrol, church relations, Vatican concordat updates, and the secularism path.

### Military Branch

Army modernisation, NATO partnership deepening, navy expansion in the Mediterranean, and the Carabinieri / police modernisation that loops back into the mafia mechanic.

## Q&A

### How do I stop the stability spiral?

After the rebalance, the accumulated stability drift modifier is clamped to ±0.2 (so the drain can't run away), and the reform-expectancy stability component is clamped at a 30% input floor. To recover from a low-stability state:

1. Take focuses that explicitly add `stability_factor` or `stability_weekly` modifiers.
2. Accept reform events even at temporary popularity cost — refusing compounds pressure.
3. Avoid concentrating police on a single mafia organisation when stability is already low (it adds a national penalty).
4. Keep the ruling coalition above its abandon threshold by spending political power on propaganda when popularity dips.

### How do I push a mafia organisation to Negligible?

Repeated decisions and focuses chip away at strength:

- **Anti-mafia education** focus — reduces all four organisations.
- **Seek support of the Church** focus — moderate hit to all four.
- **Turn the population against them** focus — strongest reduction across the board.
- **Concentration decisions** — pick one organisation, focus all police on it.
- **Legalised drugs laws** — large hit on 'Ndrangheta especially (drug trafficking).
- **Pizzo refusal** decisions — accept stability cost to refuse the protection deal in each region.

Once an organisation drops below 0.10, its regional events stop firing entirely. Below 0.40 they drop to ~25% of the baseline rate. Pushing one organisation does not affect the others; clean each region individually.

### Why won't my ally build nuclear reactors in my territory?

Italy holds the nuclear ban (`ITA_nuclear_power_banned`). The investment system and AI scoring both check the ban — neither players nor AI can construct reactors in Italian states until the ban is repealed via the appropriate focus path. The same gate also applies to Germany (carbon-neutral path).

### What happens during a civil war?

The italy_md.69 chain triggers from the `stability_protests_counter` hitting -15 (about 45 weeks at 0% stability, longer once the rebalanced clamps slow drift). The split is most often Padania secession. Civil-war participation no longer counts as an "offensive war" against allies, so:

- NATO will not dismiss you for fighting your other half.
- The EU breach-of-values system ignores civil-war combatants when scoring offensive-war flags.
- Both halves can retain EU and NATO membership while the war runs.

### How does the Eurobonds idea work?

Once Eurobonds passes the EU Council (a multi-step EU voting process), every eurozone member gains a positive `return_on_investment_modifier`, an interest-rate-multiplier reduction, and stability bonus. Combined with Italy's own ASTRA-tier MIO bonuses, ROI can stack to several percentage points. After an election the dynamic modifier may briefly show a stale value before the weekly refresh recalculates — the underlying modifier is unchanged.

### Should I take the historical or alt-history path?

For first-time Italy players, the historical centre-left (Democratic Party) or centre-right (Forza Italia) paths are the most forgiving — the rebalanced stability-drift clamp and reform-expectancy clamp mean these can be played without aggressive optimisation. Populist and authoritarian branches (Lega, M5S, fascism, communism) demand more careful coalition management because they amplify drift modifiers; only attempt them once you understand the popularity feedback.

### How do I deal with reform expectancy?

Watch the monthly drift display. Sources you can cut:

- **Interest rate** — the largest contributor when debt is high. Pay down debt with treasury surplus, take focuses that lower the interest-rate multiplier.
- **Stability** — keep stability above 30%; below that, the contribution is clamped, but recovering matters for other systems.
- **Generous social laws** — lowering social spending tier reduces pressure but hits popularity.
- **War** — make peace if at war with low war-support.

Accept reform events when they fire. Refusing them once is fine; refusing repeatedly drifts the coalition toward break-up.
