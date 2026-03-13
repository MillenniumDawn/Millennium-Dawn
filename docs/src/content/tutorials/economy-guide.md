---
title: Economy Guide
description: Comprehensive guide to the economy system in Millennium Dawn
---

# Economy Guide

Millennium Dawn includes a detailed modern economy system covering revenue, government expenditure, debt, employment, electricity, currency, inflation, and more. This guide explains each element and how they interact.

## Table of Contents

- [UI](#ui)
- [GDP and GDP per Capita](#gdp-and-gdp-per-capita)
- [Revenue](#revenue)
  - [Tax Income](#tax-income)
  - [Corporate Tax](#corporate-tax)
  - [Population Tax](#population-tax)
  - [Resource Exports](#resource-exports)
  - [Seigniorage Income](#seigniorage-income)
  - [Additional Income](#additional-income)
- [Expenses](#expenses)
  - [Military Spending](#military-spending)
  - [Bureaucracy](#bureaucracy)
  - [Police/Security](#policesecurity)
  - [Education](#education)
  - [Health](#health)
  - [Social/Welfare](#socialwelfare)
- [Debt and Interest](#debt-and-interest)
  - [Interest Rate Calculation](#interest-rate-calculation)
  - [High Interest Penalties](#high-interest-penalties)
  - [Managing Debt](#managing-debt)
- [Tax Rate Changes](#tax-rate-changes)
- [Currency and Monetary Policy](#currency-and-monetary-policy)
  - [Reserve Currency](#reserve-currency)
  - [Currency Strength](#currency-strength)
  - [Currency Backing](#currency-backing)
  - [Monetary Policy Decisions](#monetary-policy-decisions)
- [Inflation](#inflation)
- [Economic Indicators](#economic-indicators)
  - [Employment](#employment)
  - [Productivity](#productivity)
- [Economic Cycle](#economic-cycle)
- [Economic Laws](#economic-laws)
  - [Employment Pressure](#employment-pressure)
  - [Healthcare Privatization](#healthcare-privatization)
  - [Mining Policies](#mining-policies)
  - [Critical Infrastructure](#critical-infrastructure)
- [Sanctions](#sanctions)
- [Electricity](#electricity)
- [Immigration](#immigration)
- [International Investments](#international-investments)
- [Internal Investment](#internal-investment)
- [Agrarian Economy](#agrarian-economy)
- [IMF and Bailouts](#imf-and-bailouts)
- [Strategic Tips](#strategic-tips)

---

## UI

To view a country's economic information, click the graph icon in the bottom right corner to open the Economic Preview. This window shows your weekly income and expenses, tax rates, debt, employment, and key economic indicators at a glance.

---

## GDP and GDP per Capita

**GDP (Gross Domestic Product)** is calculated from active buildings and other factors. It represents the size of a country's economy and affects:

- Country rank national spirits (Superpower, Great Power, Minor Power, etc.)
- Number of research slots
- Interest rates (via the debt-to-GDP ratio)

**GDP per Capita** is GDP divided by total population, and indicates the wealth of a nation's population. It affects:

- Research speed and construction speed
- Stability and population growth
- Military and construction costs (wealthier nations pay more)

---

## Revenue

Your country's weekly income comes from multiple sources.

### Tax Income

The primary source of revenue is taxes, divided into two categories:

- **Corporate Tax**: Revenue from businesses and buildings
- **Population Tax**: Revenue from citizens

The **Average Tax Rate** shown in the economy UI is the average of your corporate and population tax rates.

### Corporate Tax

Corporate tax is calculated from multiple building types:

| Building Type         | Base Tax Factor |
| --------------------- | --------------- |
| Civilian Factories    | 2.5             |
| Offices               | 5.0             |
| Microchip Plants      | 4.0             |
| Composite Plants      | 3.5             |
| Synthetic Refineries  | 3.0             |
| Agriculture Districts | 2.6             |
| Military Factories    | 0.2             |
| Dockyards             | 0.2             |

**Corporate Tax side effects:**

- **Productivity Growth**: Higher taxes reduce productivity growth (20% tax = 0%, 40% tax = -10%)
- **Consumer Goods**: Each 1% corporate tax adds 0.015% to the consumer goods penalty
- **Investment Cost**: Higher taxes increase the cost of receiving foreign investments

### Population Tax

Population tax scales with:

- Total population
- GDP per capita (wealthier populations pay more)
- Your chosen tax rate

Higher population taxes apply a **stability penalty** (1% tax rate = -0.01% stability).

### Resource Exports

Countries earn income from exporting surplus resources on the international market. The following resources generate export revenue:

- Oil, Steel, Aluminium, Tungsten, Chromium, Rubber, Microchips, and Composites

Export income is affected by your trade law (which controls the minimum export percentage), mining policies, and currency strength. A weaker domestic currency makes resource exports more valuable in local terms, while a stronger currency reduces their local value.

### Seigniorage Income

Reserve currency issuers (the countries controlling USD, EUR, CNY, RUB, JPY, GBP, and CHF) earn passive seigniorage income proportional to how many other nations have adopted their currency. The more countries that hold your currency as their reserve, the more seigniorage you earn.

Non-issuer countries can earn a smaller seigniorage income by activating the **Expand Money Supply** monetary policy decision, which provides a fraction of tax income as additional revenue at the cost of weakening the currency.

### Additional Income

Various sources provide supplementary revenue:

- **Foreign Aid**: Some countries receive aid (e.g., US aid to allies, Iranian aid to partners)
- **International Investments**: Returns from investing in other countries (~6% annually)
- **Trade Routes**: Controlling strategic chokepoints (Suez, Panama, Hormuz) provides income
- **EU Subsidies**: Member states receive various subsidies
- **Country-Specific Income**: Special ideas and national foci (tourism, narcotics, etc.)

---

## Expenses

Government spending is divided into six categories. Higher spending levels provide buffs but cost more.

### Military Spending

Military spending is the most complex expense category:

| Cost Component         | Description                                           |
| ---------------------- | ----------------------------------------------------- |
| Base Military Industry | Military factories and dockyards                      |
| Personnel Costs        | Soldiers (special forces > elite > regular > militia) |
| Equipment Costs        | Weapons, vehicles, aircraft, naval vessels            |
| Deployed vs Stockpiled | Equipment in use costs more than in storage           |

**Military Spending Levels (0–9):**

- Level 0: Minimal funding (~0.46× multiplier)
- Level 9: Maximum funding (~10× multiplier)

GDP per capita affects military costs — wealthier nations pay more to maintain their armed forces.

### Bureaucracy

Bureaucracy spending affects policy implementation speed, national focus completion time, and administrative efficiency.

**Levels 1–5:** Costs scale from 1× to 3.4× base rate, based on population.

### Police/Security

Police spending provides stability bonuses, reduced crime rates, and counter-terrorism effectiveness.

**Levels 1–5:** Costs scale from 1× to 3.4× base rate, based on population.

### Education

Education spending is influenced by population size, number of research slots, and nuclear, air, land, and naval facilities.

**Levels 1–5:** Provides research speed and population growth bonuses.

### Health

Health spending scales with population and provides population growth, stability, and manpower recovery bonuses. The cost and effectiveness of health spending is modified by your **Healthcare Privatization** law.

**Levels 1–6:** Costs scale from 1.1× to 11× base rate.

### Social/Welfare

Social spending affects stability, population happiness, and the impact of unemployment.

**Levels 1–6:** Costs scale from 1× to 9.5× base rate. High social spending reduces the penalties from unemployment.

---

## Debt and Interest

### Interest Rate Calculation

Your interest rate is determined by:

```
Interest Rate = (Debt / GDP) × 10
```

- **Minimum interest rate**: 0.8%
- **Maximum interest rate**: 50%
- Modified by national spirits and modifiers

If your weekly balance is negative, or if a national focus or event causes you to spend more than your current funds, debt is automatically issued. The game borrows 1% of GDP plus the deficit, with a 1% fee applied to automatically borrowed funds.

For countries whose debt is denominated in a foreign reserve currency (USD, EUR, CNY, etc.), a weak domestic currency increases the real burden of debt repayment, while a strong currency reduces it.

### High Interest Penalties

When interest exceeds **15%**, severe penalties activate:

| Penalty                 | Effect                                           |
| ----------------------- | ------------------------------------------------ |
| Construction Speed      | -5% per point above 15%                          |
| Factory/Dockyard Output | -5% per point above 15%                          |
| Stability               | -2% per point above 15%                          |
| Political Drift         | -1% per point above 15% (affects all ideologies) |

If debt continues to spiral, the consequences become severe: debtor nations can gain war justifications against you for defaulting, opposition parties may demand elections, and in extreme cases civil war can occur.

### Managing Debt

1. Maintain a positive weekly balance to pay down debt naturally
2. Reduce military spending temporarily
3. Increase tax rates cautiously (reduces productivity)
4. Use economic foci to reduce interest rates
5. Build up treasury reserves during economic upturns
6. Request bailouts before interest rates spiral above 15% (see [IMF and Bailouts](#imf-and-bailouts))
7. Strengthen your currency to reduce foreign-denominated debt burden

---

## Tax Rate Changes

Tax rates are adjusted through the economy interface:

- **Change Limit**: Taxes can only be changed once every 5 months (250 days)
- **Corporate Tax**: Affects building output, productivity, consumer goods
- **Population Tax**: Affects stability

**Tax Rate Change Cost**: Each 1% change costs approximately 50 political power.

---

## Currency and Monetary Policy

Millennium Dawn models a currency system where each country has a **currency strength** variable that affects income, debt costs, and inflation.

### Reserve Currency

Every country denominates its debt and trade in a reserve currency, chosen via the **Reserve Currency** law in the Politics window. The available options are:

| Currency             | Typical Adopters                           |
| -------------------- | ------------------------------------------ |
| US Dollar (USD)      | Default for most nations                   |
| Euro (EUR)           | EU member states                           |
| Chinese Yuan (CNY)   | Chinese faction members and aligned states |
| Japanese Yen (JPY)   | Japanese faction members                   |
| Russian Rouble (RUB) | Russian faction members                    |
| British Pound (GBP)  | UK faction members                         |
| Swiss Franc (CHF)    | Switzerland and Liechtenstein only         |
| No Foreign Reserve   | Isolated or autarkic states                |

Choosing **No Foreign Reserve** eliminates foreign debt denomination effects and grants a small political power bonus, but removes the reserve currency ROI and trade bonuses that come from being part of a major currency network.

### Currency Strength

Currency strength is recalculated monthly based on three factors:

1. **Budget Balance**: A budget surplus appreciates your currency; a deficit depreciates it
2. **Debt-to-GDP Ratio**: High debt weakens your currency
3. **Stability**: Political instability drives capital flight and currency depreciation

Currency strength ranges from 0.15 (extremely weak) to 2.0 (extremely strong), with 1.0 as neutral. Its effects include:

- **Weak currency** (below 1.0): Resource exports and international investment returns are worth more in local terms, but foreign-denominated debt costs more and inflation pressure increases
- **Strong currency** (above 1.0): Foreign-denominated debt is cheaper and inflation is suppressed, but export income and investment returns decrease in local terms

Reserve currency issuers (USD, EUR, etc.) have dampened volatility -- their currencies cannot swing as dramatically as smaller nations.

### Currency Backing

The **Currency Backing** law determines how your currency is anchored:

| Backing           | Stability | Trade Opinion | Other Effects                            |
| ----------------- | --------- | ------------- | ---------------------------------------- |
| Gold Standard     | +6%       | +4%           | -5% political power; low volatility      |
| Silver Standard   | +3%       | +2%           | -2% political power; moderate volatility |
| Bi-Metal Standard | +2%       | +1%           | Moderate volatility                      |
| Fiat Currency     | -2%       | --            | +0.03 daily PP; highest flexibility      |

Hard-money standards (gold, silver) dampen currency volatility and pull currency strength toward par (1.0) over time. However, they restrict monetary policy flexibility -- you cannot use the Expand Money Supply decision while on the gold standard.

### Monetary Policy Decisions

Two monetary policy decisions are available (AI-controlled nations use these automatically):

- **Expand Money Supply**: Increases seigniorage income by 25% and weakens currency strength by 0.05. Cannot be used alongside Austerity Measures or while on the gold standard. Lasts 180 days with a 365-day cooldown.
- **Austerity Measures**: Strengthens currency by 0.04. Lasts 120 days with a 180-day cooldown. Cannot be used alongside Expand Money Supply.

---

## Inflation

Inflation is modeled through a dynamic modifier that applies broad economic effects. The inflation rate is driven by currency weakness -- when currency strength drops below 1.0, the difference feeds into inflation pressure.

Inflation affects nearly every part of the economy:

| Effect                  | Impact                                                 |
| ----------------------- | ------------------------------------------------------ |
| Cost Multiplier         | Increases costs across the board                       |
| Construction Speed      | Reduced building construction speed                    |
| Factory/Dockyard Output | Reduced industrial output                              |
| Productivity Growth     | Slower long-term productivity gains                    |
| Political Power         | Reduced political power generation                     |
| Consumer Goods          | Increased consumer goods requirement                   |
| Investment Costs        | Higher costs for both domestic and foreign investments |
| Trade Law Changes       | More expensive to adjust trade laws                    |

Inflation can be managed by strengthening your currency (via austerity, reducing debt, or improving stability) or by adopting a hard-money currency backing standard.

---

## Economic Indicators

### Employment

Buildings require workers to function at full efficiency. Each facility has a required worker count, and you must allocate a portion of the national population to fill those positions. Allocation is automatic, but buildings without enough workers have reduced output.

If all buildings are fully staffed and workers remain, those workers become unemployed. The unemployment rate is shown in the Economy window.

If unemployment exceeds the **Unemployment Threshold** shown in the Economy window, debuffs apply: a stability penalty and increased social spending. These debuffs grow stronger as unemployment rises.

You can prioritize which building types receive workers first from the Economy window.

### Productivity

**State Productivity** affects local building output. Starting productivity varies by region:

- Europe: ~1000
- Asia: ~650
- Africa / South America: ~550

**Increasing Productivity:**

- Economic Cycle upgrades
- Infrastructure investments
- National focuses and spirits
- State-specific modifiers and internal investments

---

## Economic Cycle

The Economic Cycle represents the overall state of a country's economy. It is displayed as the second icon from the left in the National Statistics and Internal Factions section of the Politics window.

There are six stages. A better stage grants buffs to stability, construction speed, immigration rate, and productivity growth.

**Changing the Economic Cycle:**

- Spend political power and treasury funds to manually upgrade it
- Some national focuses advance the Economic Cycle directly
- Random events tied to high GDP growth rates can raise it
- Negative events — such as a bubble burst — can lower it

---

## Electricity

Countries must supply electricity as part of their infrastructure. Power is generated by constructing specific buildings:

| Building                        | Fuel Source            | Output (base) |
| ------------------------------- | ---------------------- | ------------- |
| Fossil Fuel Powerplant          | Fuel                   | 2 GW          |
| Nuclear Reactor                 | Reactor-Grade Material | 5 GW          |
| Renewable Energy Infrastructure | None                   | 0.5 GW        |

Reactor-Grade Material can be produced at Enrichment Facilities (built from the electricity panel) or purchased from other countries via decisions. States with Geothermal Infrastructure or Hydroelectric Infrastructure modifiers provide additional power.

Electricity consumption is calculated from active buildings and population. Insufficient power generation applies debuffs to stability, facility output, and research speed.

View your country's electricity situation by clicking the electricity icon in the construction window to open the Electricity Panel.

---

## Immigration

Immigration is one way to grow your population. Migration happens automatically, but you can adjust the acceptance level by changing the stage of **Migration Laws** (found at the far right of Policies in the Politics window).

Immigration control costs money. Stricter restrictions cost more to enforce. The immigration rate is calculated from factors including national productivity, unemployment rate, and war status, and is further modified by national spirits and other sources.

---

## International Investments

You can construct buildings in foreign countries through International Investments. This requires spending treasury funds and takes time, but provides:

- **Investment returns**: approximately 6% annually, paid as weekly income, subject to modification by national spirits
- **Influence**: gaining leverage over the receiving country

Some countries will refuse international investments. AI-controlled countries may also offer to invest in yours.

To initiate an international investment, click on a foreign state, then click the arrow button to open the interface and proceed.

---

## Internal Investment

Internal investments work like international investments but target your own states. Click on a domestic state, then click the arrow button to open the interface.

Internal investments can:

- Increase a state's productivity growth rate
- Add building slots
- Apply temporary modifiers for a limited period

Each investment costs political power and treasury funds.

---

## Agrarian Economy

The Agrarian Economy is a special economic system for very poor nations, represented by the **Agrarian Based Economy** national idea. Countries with this idea have a GDP per capita below $20,000 and rely heavily on agricultural output for income.

Once a country reaches $20,000 GDP per capita, it is considered industrialized and loses the agrarian economy idea.

### Crop Allocation

Agrarian countries manage two crop types:

- **Basic Crops**: Subsistence-oriented; provides stable income
- **Cash Crops**: Export-oriented; higher value but more volatile

Field allocation between basic and cash crops can be adjusted via the Agricultural Economy window. Allocation can be shifted in 1%, 5%, or 10% increments by clicking or using Ctrl/Shift+Click. Each reallocation costs political power.

Changes are **banked** and applied together when you click "Make Changes", rather than taking effect immediately.

### Agricultural Workers

The number of workers available for agriculture is determined by **literacy rate**. A lower literacy rate means more workers are available for the fields, producing more agricultural output — but at the cost of reduced research speed. Higher literacy shifts workers toward other sectors.

### Drought Events

Agrarian countries are vulnerable to drought events, which reduce agricultural output:

| Drought Type       | Scope                | Neighbor Impact |
| ------------------ | -------------------- | --------------- |
| Localised Drought  | Specific areas       | Unlikely        |
| Regional Drought   | Whole regions        | Likely          |
| Widespread Drought | Vast swathes of land | Almost certain  |

Drought protections can be built up through decisions and national focuses to reduce severity.

---

## Monetary Policy

Countries have access to monetary policy decisions that affect currency strength and fiscal strategy. These two policies are mutually exclusive -- you cannot run both at the same time.

### Expand Money Supply

Directs the central bank to inject liquidity into the economy:

- **Duration**: 180 days, with a 365-day cooldown
- **Effect**: +25% seigniorage income modifier
- **Side effect**: Weakens currency strength by 5%
- **Requires**: No gold standard and a functioning foreign reserve

Reserve currency issuers benefit most, as their base seigniorage income scales up significantly. Non-issuers earn a smaller fraction of tax income but pay the same currency weakness cost.

### Austerity Measures

Tightens the money supply and imposes fiscal discipline:

- **Duration**: 120 days, with a 180-day cooldown
- **Effect**: Strengthens currency by 4%
- **Best used**: When currency is weak but the treasury is stable

---

## IMF and Bailouts

When your economy is struggling, several bailout options are available:

### Cheap Loans from the IMF

- **Cost**: 50 political power
- **Requirements**: GDP per capita above $5,000, interest rate below 15%, expenses exceeding income, no severe corruption
- **Cooldown**: 365 days
- **Effect**: Provides a subsidized loan to stabilize your economy

### African Investment Fund Loans

Available to African nations that have completed the AU shared focus to create the monetary fund:

- **Requirements**: Interest rate below 15%
- **Effect**: Reduces interest rate multiplier by 3 while active
- **Benefit**: An alternative to the IMF with potentially better terms for African economies

### Bailout Requests

When the economy is in severe distress (interest above 15%), countries can request bailouts from:

1. **IMF** (cheap loans, first resort)
2. **Neighboring countries** (diplomatic requests)
3. **Second-most influential country** (less diplomatic damage)
4. **Most influential country** (last resort, most influence cost)

If interest exceeds 25% and the country is not at war, the AI will default on its debt, triggering severe consequences.

---

## Strategic Tips

### Early Game

1. **Balance initial taxes**: Start moderate to avoid killing productivity
2. **Build offices first**: They provide high tax income per worker
3. **Monitor employment**: Don't overbuild factories without workers to staff them

### Mid Game

1. **Invest internationally**: Generate passive income from foreign buildings
2. **Upgrade the Economic Cycle**: Major buffs for stability and construction speed
3. **Manage debt aggressively**: High interest cripples long-term growth

### Late Game

1. **Maintain high social spending**: Reduces unemployment impact
2. **Optimize tax rates**: Find the balance between revenue and productivity
3. **Use aid and trade**: Leverage diplomatic relationships for supplementary income

### Common Mistakes to Avoid

- **Excessive military spending**: The fastest way to bankrupt your economy
- **Ignoring unemployment**: Leads to compounding stability penalties
- **High debt accumulation**: Interest costs compound and eventually trigger crisis events
- **Over-taxation**: Kills productivity growth and long-term revenue

---

## Related Documentation

- [International Systems Guide](/player-tutorials/international-systems) - For PMCs, sanctions, and other international economic systems
- [European Union Tutorial](/player-tutorials/eu-tutorial) - For EU-specific economic mechanics (Eurozone, ECB, single market)
- [Game Rules](/player-tutorials/game-rules)
