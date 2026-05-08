---
title: Investments Guide
description: Guide to the international and internal investment systems in Millennium Dawn
---

Millennium Dawn includes two distinct investment systems: **International Investments**, which let you construct buildings in foreign countries for passive income and influence, and **Internal Investments**, which let you apply temporary state-level buffs to your own territory. Both are accessed by clicking on a state and opening the investments panel.

---

## International Investments

### Overview

International investments allow you to fund the construction of buildings in foreign-controlled states. Once a project completes, the building becomes part of that state — permanently raising their production, infrastructure, or energy output. In return, you earn weekly income on the money you have spent.

**Why invest internationally?**

- Generate passive income at a 6% annual return rate (modified by national ideas and focuses)
- Gain influence over the target country
- Strengthen allies with military or energy infrastructure

### How to Use

1. Click on any state not owned or controlled by you
2. An arrow button appears at the bottom of the state panel — click it to open the investments window
3. Select a building type from the two pages of options
4. Adjust the quantity with the +/− buttons
5. Click the build button to initiate the project

The target country's government will receive an event asking them to accept or reject. If they accept, the project begins; if they reject, no money is spent.

### Project Limits

You can run up to **15 projects simultaneously** across all foreign states. Only one project per state at a time (you cannot stack investments in the same state). If you cancel a project mid-construction, you are refunded the remaining cost and the target country keeps 10% of the total as a cancellation fee.

### Buildable Types and Costs

All costs are in billions of treasury funds.

**Page 1:**

| Building         | Treasury Cost | Max Quantity | Notes                                      |
| ---------------- | ------------- | ------------ | ------------------------------------------ |
| Civilian Factory | $12.0B        | 10           | Boosts industrial output, tax income       |
| Military Factory | $12.5B        | 10           | Boosts arms production                     |
| Naval Dockyard   | $12.0B        | 10           | Boosts naval construction                  |
| Infrastructure   | $5.5B         | 5            | Boosts construction speed in state         |
| Offices          | $20.0B        | 5            | Highest tax income factor; good ROI target |
| SAM Site         | $5.5B         | 5            | Air defense                                |
| Radar Station    | $4.5B         | 6            | Detection range                            |

**Page 2:**

| Building               | Treasury Cost | Max Quantity | Notes                                      |
| ---------------------- | ------------- | ------------ | ------------------------------------------ |
| Air Base               | $5.25B        | 10           | Increases air wing capacity                |
| Fuel Silo              | $5.25B        | 5            | Increases fuel storage                     |
| Internet Station       | $4.65B        | 6            | +5% productivity growth per level in state |
| Renewable Energy       | $13.6B        | 10           | Adds 0.5 GW per level; no fuel cost        |
| Fossil Fuel Powerplant | $5.2B         | 10           | Adds 2 GW per level                        |
| Nuclear Reactor        | $14.4B        | 10           | Adds 5 GW per level; expensive             |
| Agriculture District   | $5.8B         | 10           | Adds fuel output and local supply          |

### Construction Duration

Duration is based on your construction speed modifiers and conditions in the target state. It is shortened by:

- Higher infrastructure level in the target state (+15% speed per level)
- Higher internet station level in the target state (+5% per level)
- Your own construction speed bonuses from ideas and technologies
- The target country having ideas that reduce their received investment duration
- Holding the ECB President or EU Finance Minister position when investing in EU member states
- Having a Mutual Investment Treaty with the target country (−5%)

If your nation has an active economic boycott of Israel, all your investment projects take twice as long to complete.

### Investment Returns

Your International Investments total grows every time a project completes. The system pays out a fraction of that total every week:

- **Base ROI**: 6% per year (roughly $0.115B per week per $100B invested)
- **Modifiable**: national ideas and focus tree completions can raise the ROI rate up to a cap of 20%
- **Currency effect**: a weak domestic currency makes returns worth more in local terms; a strong currency reduces their local value

Your current investment total and weekly return are displayed in the Economy window. If your country is annexed by another nation, your entire investment portfolio transfers to the annexing power.

### Cost Modifiers

The monetary cost per building is calculated when you initiate a project:

| Condition                                                        | Effect              |
| ---------------------------------------------------------------- | ------------------- |
| Target country has ideas reducing received investment cost       | Cost reduced        |
| Your nation has an active economic boycott of Israel             | +50% cost           |
| Target is EU member + you hold ECB President                     | −15% cost           |
| Target is EU member + you hold EU Finance Minister               | −5% cost            |
| France investing in a state with the Development Investment idea | −5% cost            |
| Mutual Investment Treaty with the target                         | −5% cost            |
| Your own investment cost modifiers from ideas                    | Additive adjustment |

### Influence Gain

Every accepted investment grants the investor an influence percentage over the target country. The default gain per investment is **1.5%** influence (configurable in game rules: 0.5%, 1%, 1.5%, or 2%). Canceling a project removes influence instead.

### Receiving Investments

When a foreign country offers to build in one of your states, you get an event:

- **Accept**: The investor funds the full project cost. You receive 10% of the cost added to your treasury, and the investor gains influence over you.
- **Decline**: Nothing happens. The investor cannot re-offer for a period.

Accepting investments is generally beneficial — you get a free building plus a cash payment. The main reason to decline is if you do not want a rival nation accumulating influence over you.

Some decisions and focuses can set your country to automatically reject all incoming investment offers.

---

## Internal Investments

### Overview

Internal investments are temporary state-level buffs funded by political power and treasury funds. They do not permanently build anything; instead, they apply a modifier for a fixed duration (120–180 days). All options cost **75 Political Power** (reducible by national ideas) plus a treasury payment scaled to your GDP.

### How to Use

1. Click on any state you own or control
2. Click the arrow button to open the owned-state investments panel
3. Select an investment option — each shows its duration and what it does
4. Confirm to spend PP and treasury funds

Each investment locks a **concurrent slot** for the duration. The number of available slots scales with your power rank:

| Power Rank     | Concurrent Internal Investment Slots |
| -------------- | ------------------------------------ |
| Superpower     | 6                                    |
| Great Power    | 5                                    |
| Large Power    | 4                                    |
| Regional Power | 3                                    |
| Minor Power    | 2                                    |
| Micro Power    | 2                                    |

Additional slots can be granted by national ideas and focus completions.

### Available Options

| Option                            | Duration | Treasury Cost (% of GDP)    | Effect                                                                                       |
| --------------------------------- | -------- | --------------------------- | -------------------------------------------------------------------------------------------- |
| Encourage Investments             | 160 days | ~0.6% GDP                   | Foreign investment projects in this state complete 15% faster; AI more likely to invest here |
| Encourage Productivity            | 160 days | ~0.9% GDP × state pop       | +20% productivity growth in state                                                            |
| Expand Building Capacity          | 120 days | 0.7% × (expansions + 1) GDP | +1 building slot (up to 5 expansions per state)                                              |
| Expand Renewable Capacity         | 180 days | ~0.1% GDP                   | +25% renewable energy generation in state                                                    |
| Expand Local Infrastructure       | 180 days | ~0.2% GDP                   | +20% infrastructure, internet station, and rail construction speed                           |
| Expand Military Infrastructure    | 180 days | ~0.2% GDP                   | +15% air base, SAM, radar, and rocket site construction speed                                |
| Expand Energy Infrastructure      | 180 days | ~0.3% GDP                   | +15% all energy building construction speed                                                  |
| Build Forward Logistics Base      | 180 days | ~0.4% GDP                   | −25% supply impact factor (improved logistics)                                               |
| Improve Rebuilding Efforts        | 180 days | ~0.4% GDP × state pop       | +15% compliance growth, −5% resistance activity                                              |
| Hire Extra Primary Sector Workers | 180 days | ~0.6% GDP                   | +15% state resource extraction output                                                        |
| Expand Coastal Infrastructure     | 180 days | ~0.5% GDP                   | +15% naval base, naval HQ, and naval supply hub construction speed (coastal states only)     |
| Expand Fortification Efforts      | 180 days | ~0.5% GDP                   | +15% bunker, coastal bunker, and stronghold construction speed                               |

Treasury costs are proportional to your GDP, so they scale naturally with your economy — large nations pay more in absolute terms but the same fraction as small ones. For the two population-scaled options (Encourage Productivity and Improve Rebuilding Efforts), costs are also multiplied by the state's population in millions, meaning investing in densely populated states is more expensive.

### Building Capacity Expansion

**Expand Building Capacity** is the only permanent-like option in this list: the building slot it adds stays after the 120-day investment ends. Each subsequent expansion in the same state costs more (the cost multiplier increases by 1 each time), and a state can only be expanded up to 5 times before the option is blocked permanently for that state.

This is one of the most valuable uses of internal investment, particularly in states that have run out of building slots but still have workforce and GDP potential.

---

## AI Investment Behavior

AI nations invest in foreign states automatically on a recurring pulse. The system has three stages: deciding whether to fire at all, picking a target country from a pre-set list, and then scoring every eligible building type across every state in that country to find the best project.

### Which AI Nations Invest

Not every AI nation participates in the investment system. Each country's potential investment targets are defined as a fixed list in their country history file. Only nations with a populated target list will ever invest. The nations that invest from the start of the game include:

**USA, China, Russia, UK, France, Germany, Japan, South Korea, India, Indonesia, Singapore, South Africa, Italy, Brazil, Iran, and Syria.**

Nations that complete certain focus trees can also unlock new targets or be added to other nations' target pools through mutual investment treaties and diplomatic focuses.

### When AI Will Invest

The AI pulse only fires when all of the following are true:

- Active projects fewer than 15
- Interest rate below 8%
- Debt-to-GDP ratio below 2.5
- Treasury above $5B

If any condition fails, the pulse is skipped entirely. This means AI nations in economic difficulty stop investing abroad — and struggling nations will receive less foreign capital when they most need it.

### Country Selection

From the eligible target list, the AI scores every country and picks the highest-scoring one. If the winner scores below zero the pulse is skipped and the country is flagged as a recently-failed target for 75 days.

**Positive factors** (AI more likely to invest in you):

| Factor                                                            | Weight                                |
| ----------------------------------------------------------------- | ------------------------------------- |
| Mutual influence between investor and target                      | Strong (each direction)               |
| Positive opinion                                                  | Strong (scales linearly, up to a cap) |
| Target GDP per capita below $30k                                  | Moderate to Strong                    |
| Same faction                                                      | Moderate                              |
| Trade agreement                                                   | Moderate                              |
| Mutual Investment Treaty                                          | Moderate                              |
| Same continent as investor                                        | Moderate                              |
| Investor has limited industrial capacity or runs a budget deficit | Moderate                              |
| Target is at war with an enemy of the investor                    | Moderate                              |

**Negative factors** (AI less likely to invest in you):

| Factor                                                 | Weight                                  |
| ------------------------------------------------------ | --------------------------------------- |
| Non-state actor (militia, rebel faction)               | Strong                                  |
| Recently accepted any investment (21-day cooldown)     | Strong                                  |
| Investor already has an active project in your country | Moderate (per project)                  |
| Large total GDP                                        | Moderate                                |
| Corruption level                                       | Slight to Strong (scales with severity) |
| Corporate tax above 30%                                | Slight (scales with rate)               |

A random element is also applied each pulse to prevent deterministic outcomes.

### Building and State Scoring

Once a target country is selected, the AI evaluates every building type against every eligible state in that country, picking the best combination. If no strong match is found, the target country is flagged for 75 days and the pulse ends without an offer.

**State eligibility:** Only states in the target's home territory are considered. Very small or inhospitable states (such as Sahara desert terrain) are excluded, as are states already receiving an active project from this investor.

**Investor idea gates:** Some building types are only scored if the investor nation has a specific idea or technology. The AI will not even evaluate these types otherwise:

| Building             | Required on Investor                         |
| -------------------- | -------------------------------------------- |
| Military Factory     | Defense Industry idea                        |
| Naval Dockyard       | Maritime Industry idea (coastal states only) |
| SAM Site             | Defense Industry or The Military idea        |
| Radar Station        | Military ideas or radar technology           |
| Air Base             | Military ideas                               |
| Renewable Energy     | Fuel silo technology                         |
| Nuclear Reactor      | Nuclear reactor technology                   |
| Agriculture District | **Never scored — AI does not build these**   |

**Building scoring summary:**

| Building          | What Raises It                                                              | What Suppresses It                                                        |
| ----------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Civilian Factory  | Low CIV-to-factory ratio                                                    | Existing CIVs in state; full employment; low available CIVs               |
| Military Factory  | Post-2004/2006 date; high threat; target at war                             | Peacetime; MILs already >45% of factories                                 |
| Naval Dockyard    | Low dockyard count; target at war                                           | Non-coastal state; low steel output; low GDP; high interest rate          |
| Infrastructure    | Resource-rich states                                                        | Already at level 5; pending projects will reach max                       |
| Offices           | High corporate tax (above ~22–32%)                                          | Low GDP per capita; full employment                                       |
| SAM Site          | War; high threat; capital or coastal                                        | Peacetime with low threat                                                 |
| Radar Station     | Threat; coastal; naval powers                                               | Peacetime with low threat                                                 |
| Air Base          | War; high threat; large military                                            | Peacetime; low fuel capacity                                              |
| Fuel Silo         | War; low existing fuel storage; large military                              | Already high fuel capacity                                                |
| Internet Station  | Max infrastructure level in state; large population; high GDP per capita    | Very low GDP per capita (hard blocked below $5k)                          |
| Renewable Energy  | Energy deficit; high state renewable capacity                               | Target's renewable tech below threshold (blocks entirely); energy surplus |
| Fossil Powerplant | Energy deficit                                                              | Countries with excessive consumption penalized                            |
| Nuclear Reactor   | Energy deficit; high GDP per capita; oil imports; active power restrictions | Low GDP per capita; high interest rate; energy surplus                    |

Small states (population below 100k) accumulate cumulative score penalties across all building types.

### How Targets Accept or Decline

When the AI makes an offer, the target country evaluates it with a weighted random decision. Several factors can push the result strongly in either direction:

**More likely to accept:**

- Subject or puppet of the investor
- Low GDP per capita
- Few available civilian factories
- Energy deficit and the offered building is a power plant
- Investor is among the top influencers in the country

**Hard block — will always decline:**

- Interest rate above 10%
- Already refused this investor within the last 30 days

**More likely to decline:**

- Nationalist government ideology
- Low domestic independence — the lower it falls, the more strongly the country resists accumulating more foreign influence
- Energy-constrained country offered an economic building (factory, dockyard, office, agriculture) — strongly prefers energy investment first
- Ideological mismatch with the investor

**Hardcoded rejections:**

- North Korea refuses all offers except from China
- Iran refuses offers from non-communist nations
- China and Russia refuse offers from the United States

After a decline, the target will not accept further offers from that same investor for 30 days.

### Cooldowns Summary

| Event                                        | Duration                                        |
| -------------------------------------------- | ----------------------------------------------- |
| Target accepts an investment                 | 21 days before accepting another (any investor) |
| Target declines an offer                     | 30-day lock on that specific investor           |
| No viable project found for a target country | 75-day flag; AI skips that target               |

### Attracting AI Investment

The scoring tables above show what drives AI country selection. In practice, the most actionable levers are:

- **Faction membership and trade agreements** are the easiest consistent boosts — the major investing nations favour their bloc members and trading partners
- **A Mutual Investment Treaty** is one of the highest-value diplomatic deals for investment attraction — it improves your country-selection score and reduces both cost and duration on incoming projects
- **Keep corruption low and corporate tax below 30%** — both drag your score down; corruption is especially punishing at higher levels
- **Use Encourage Investments on states you want developed** — it raises the per-state building score and speeds up incoming projects by 15%
- **Keep interest rates below 10%** — above this, the target hard-blocks acceptance regardless of how attractive your country otherwise appears

### Deterring Unwanted Investment

If a rival is accumulating influence through investments:

- **Decline their offers** — each rejection locks them out temporarily and repeated declines make them deprioritize your country over time
- **Use national decisions or focuses that auto-reject all incoming offers** — some countries have access to a blanket block
- **Raise corporate tax above 30%** — reduces your score in AI country selection, though at the cost of your own productivity

---

## Strategic Tips

**Invest in offices abroad.** Offices have the highest corporate tax factor and the highest investment cost ($20B per building), which means they grow your International Investments total the fastest. If the target accepts, offices generate the best return of any buildable type.

**Use Encourage Investments to draw in foreign capital.** This internal investment makes your state more attractive to AI investors and speeds up incoming foreign projects by 15%. If you are developing an underdeveloped state and want foreign nations to pitch in, flag it first.

**Use Expand Building Capacity before you need the slots.** Building slot expansion is the only internal investment option that outlasts its duration — the slot stays permanently. Do it early in states you intend to develop heavily rather than waiting until you are already blocked.

**Grow your investment portfolio steadily through the mid game.** Once you have $100B+ invested, the weekly passive income becomes meaningful. Nations that invest abroad consistently can self-fund their late-game military expansion from returns alone.

**Match internal investments to active construction plans.** Military Infrastructure and Energy Infrastructure options only benefit you while you are actively building in those categories. Activate them just before you start a construction queue, not months in advance.

---

## Related Documentation

- [Economy Guide](/player-tutorials/economy-guide) — Full breakdown of income, expenses, debt, and the currency system
- [Influence Guide](/player-tutorials/influence-guide) — How influence interacts with investments and diplomatic leverage
- [International Systems Guide](/player-tutorials/international-systems) — PMCs, sanctions, and other cross-border mechanics
