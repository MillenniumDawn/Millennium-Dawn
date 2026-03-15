---
title: Economy Guide
description: Comprehensive guide to the economy system in Millennium Dawn
---

Millennium Dawn includes a detailed modern economy system covering revenue, government expenditure, debt, employment, electricity, and more. This guide explains each element and how they interact.

## Table of Contents

- [UI](#ui)
- [GDP and GDP per Capita](#gdp-and-gdp-per-capita)
- [Revenue](#revenue)
  - [Tax Income](#tax-income)
  - [Corporate Tax](#corporate-tax)
  - [Population Tax](#population-tax)
  - [Resource Exports](#resource-exports)
  - [Dynamic Resource Pricing](#dynamic-resource-pricing)
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
  - [What Drives Inflation](#what-drives-inflation)
  - [The Inflation Formula](#the-inflation-formula)
  - [Central Bank Policy Rate](#central-bank-policy-rate)
  - [Currency and Inflation](#currency-and-inflation)
  - [Effects of Inflation](#effects-of-inflation)
  - [Managing Inflation](#managing-inflation)
- [Economic Indicators](#economic-indicators)
  - [Employment](#employment)
  - [Productivity](#productivity)
- [Economic Cycle](#economic-cycle)
- [Trade Laws](#trade-laws)
- [Economic Laws](#economic-laws)
  - [Employment Pressure](#employment-pressure)
  - [Healthcare Privatization](#healthcare-privatization)
  - [Mining Policies](#mining-policies)
  - [Critical Infrastructure](#critical-infrastructure)
- [Literacy](#literacy)
- [Internal Factions](#internal-factions)
- [Sanctions](#sanctions)
- [Electricity](#electricity)
- [Buildings](#buildings)
  - [Offices](#offices)
  - [Internet Stations](#internet-stations)
  - [Agriculture Districts](#agriculture-districts)
  - [Energy Infrastructure](#energy-infrastructure)
  - [Industrial Infrastructure](#industrial-infrastructure)

- [Advanced Industrial Buildings](#advanced-industrial-buildings)
  - [Microchip Plants](#microchip-plants)
  - [Composite Plants](#composite-plants)
  - [Synthetic Refineries](#synthetic-refineries)
  - [Input Resource Shortages](#input-resource-shortages)
  - [Civilian Microchip Consumption](#civilian-microchip-consumption)
  - [Military Equipment Requirements](#military-equipment-requirements)
  - [Building Employment Values](#building-employment-values)
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

**GDP per Capita** is GDP divided by total population, and indicates the wealth of a nation's population. A dynamic modifier applies scaling bonuses and penalties based on your GDP/C level:

| Effect                         | How It Scales                                                                      |
| ------------------------------ | ---------------------------------------------------------------------------------- |
| Construction Speed             | Penalty increases with wealth — rich nations build slower                          |
| Population Growth              | Bonus for poor nations, penalty for wealthy nations (break-even around $60k GDP/C) |
| Research Speed                 | Bonus increases with wealth (kicks in above ~$51k GDP/C)                           |
| Stability                      | Small bonus that increases with wealth (kicks in above ~$100k GDP/C)               |
| Workforce Costs                | Wealthy nations require more workers per building                                  |
| Fossil Fuel Plant Construction | Cheaper for poor nations, expensive for rich ones                                  |

This means poor nations grow their population faster and build cheaply, but have lower research speed. Rich nations research faster and are more stable, but face higher costs for construction and workforce.

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

### Dynamic Resource Pricing

Resource export prices are not fixed — they fluctuate globally based on worldwide supply and demand. Prices are recalculated periodically using the following formula:

```
Price = (Global Demand / Global Supply) × 2 × Starting Price
```

When global demand exceeds half of global supply (demand/supply ratio > 0.5), prices rise above the starting price. When demand falls below that ratio, prices drop. Each resource has a hard floor and ceiling that prices cannot exceed:

| Resource   | Starting Price | Price Floor | Price Ceiling |
| ---------- | -------------- | ----------- | ------------- |
| Oil        | 6.80           | 1.36        | 34.00         |
| Steel      | 0.024          | 0.005       | 0.120         |
| Aluminium  | 0.21           | 0.042       | 1.05          |
| Tungsten   | 0.28           | 0.056       | 1.40          |
| Chromium   | 0.18           | 0.036       | 0.90          |
| Rubber     | 0.09           | 0.018       | 0.45          |
| Microchips | 8.00           | 1.58        | 36.20         |
| Composites | 7.40           | 1.42        | 35.40         |

**Strategic implications:**

- Countries that control large shares of a scarce resource (e.g., tungsten, chromium, microchips) can indirectly benefit from high prices if global supply is tight.
- Building Microchip Plants and Composite Plants across many nations increases global supply of those resources, driving their prices down over the course of a game.
- Microchips and composites have the highest price ceilings by far — a global shortage of either resource can make them extremely valuable exports.
- Oil prices are the most volatile in practice, as fuel demand is high and supply is concentrated in relatively few states.

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

Police spending provides stability bonuses and counter-terrorism effectiveness.

**Levels 1–5:** Costs scale from 1× to 3.4× base rate, based on population.

### Education

Education spending is influenced by population size, number of research slots, and nuclear, air, land, and naval facilities.

**Levels 1–5:** Provides research speed and population growth bonuses.

### Health

Health spending scales with population and provides population growth, stability, and manpower recovery bonuses. The cost and effectiveness of health spending is modified by your **Healthcare Privatization** law.

**Levels 1–6:** Costs scale from 1.1× to 11× base rate.

### Social/Welfare

Social spending affects stability and the impact of unemployment.

**Levels 1–6:** Costs scale from 1× to 9.5× base rate. High social spending reduces the penalties from unemployment.

---

## Debt and Interest

### Interest Rate Calculation

Your interest rate is determined by:

```
Interest Rate = (Debt / GDP) × 10 + (Central Bank Policy Rate × 0.5) + modifiers
```

- **Minimum interest rate**: 0.8%
- **Maximum interest rate**: 50%
- Modified by national spirits and modifiers

The central bank policy rate contributes half its value to the interest rate. This means raising the policy rate to fight inflation also increases the cost of servicing debt — a tradeoff between controlling inflation and managing debt.

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

Inflation is one of the most important economic variables in Millennium Dawn. It is recalculated every quarter (months 3, 6, 9, and 12) and applies broad modifiers to nearly every part of your economy. Unlike a simple currency effect, inflation is driven by the interaction of GDP per capita growth, tax policy, the central bank policy rate, the economic cycle, budget balance, and currency strength.

### What Drives Inflation

Six factors feed into the quarterly inflation calculation:

| Factor                       | Effect on Inflation                                                                                                                                     |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **GDP/C Growth**             | Higher GDP per capita growth directly increases inflation pressure. A rapidly growing economy generates demand that pushes prices up.                   |
| **Tax Rate**                 | Higher average tax rates reduce inflation pressure. Taxes act as a fiscal brake on the economy -- they pull money out of circulation.                   |
| **Central Bank Policy Rate** | The _real_ policy rate (policy rate minus current inflation) is what matters. A positive real rate suppresses inflation; a negative real rate fuels it. |
| **Economic Cycle**           | Boom and fast growth stages add inflationary pressure. Depression and recession stages reduce it. Stable growth is neutral.                             |
| **Budget Balance**           | A budget deficit increases inflation (simulating money printing to cover the gap). A budget surplus decreases it.                                       |
| **Currency Strength**        | A weak currency (below 1.0) feeds additional inflation pressure through higher import costs. A strong currency suppresses it.                           |

### The Inflation Formula

Each quarter, the game calculates an inflation adjustment from the factors above, then averages the last four quarters to produce the annual inflation rate. This averaging smooths out short-term spikes.

**Step-by-step:**

1. **GDP/C growth contribution**: The base adjustment starts from last quarter's GDP per capita growth rate, scaled by your GDP per capita level. Higher GDP/C amplifies the effect of growth on prices.
2. **Tax dampening**: The adjustment is reduced proportionally to your average tax rate. At higher tax rates, more of the growth-driven inflation is absorbed.
3. **Policy rate effect**: The real central bank rate (policy rate minus inflation, with a 2% floor on inflation for this calculation) is subtracted. A tight monetary policy (real rate > 0) pulls inflation down; loose policy (real rate < 0) lets it rise.
4. **Economic cycle**: The current cycle stage applies an additional adjustment, scaled by total government spending:

| Cycle Stage   | Inflation Adjustment |
| ------------- | -------------------- |
| Depression    | -0.035               |
| Recession     | -0.025               |
| Stagnation    | -0.015               |
| Stable Growth | 0                    |
| Fast Growth   | +0.015               |
| Economic Boom | +0.025               |

5. **Budget balance**: A deficit adds inflationary pressure proportional to the shortfall. A surplus has the opposite effect.
6. **Money printing multiplier**: If the Expand Money Supply decision is active, the entire adjustment is amplified.

The quarterly result is stored and averaged with the previous three quarters. The rate is clamped to prevent wild swings: no more than +/-10 percentage points change per quarter, and a hard cap of +/-200% total.

### Central Bank Policy Rate

The **Central Bank Policy Rate** is a manually adjustable interest rate (0-20%) that represents your country's monetary policy stance. It starts at 3% for all countries.

What matters for inflation is the **real rate** -- the difference between the policy rate and the current inflation rate. For example:

- Policy rate 5%, inflation 3% = real rate +2% (tight, reduces inflation)
- Policy rate 3%, inflation 5% = real rate -2% (loose, increases inflation)
- Policy rate 2%, inflation 2% = real rate 0% (neutral)

The AI adjusts the policy rate automatically based on inflation:

| Condition           | AI Action                     |
| ------------------- | ----------------------------- |
| Inflation above 10% | Raises policy rate toward 20% |
| Inflation above 5%  | Raises policy rate toward 15% |
| Inflation below 1%  | Lowers policy rate toward 1%  |

Players can adjust the policy rate manually to respond faster or pursue different monetary strategies than the AI default.

### Currency and Inflation

Currency strength has a separate, additive effect on inflation costs. When your currency is weak (below 1.0), the gap between 1.0 and your currency strength feeds into a **currency inflation component**:

```
Currency Inflation = (1.0 / Currency Strength - 1.0) × 0.05
```

This is added on top of the base inflation rate to produce the **combined inflation cost** that the dynamic modifier uses. A currency at 0.5 strength adds roughly 5% additional inflation pressure. A currency at 1.0 or above adds nothing.

This means inflation has two independent sources: the quarterly macroeconomic calculation and the currency channel. You can have low base inflation but still suffer high effective inflation if your currency has collapsed.

### Effects of Inflation

Inflation applies a dynamic modifier that scales with the inflation rate. The effects are proportional -- higher inflation means stronger penalties:

| Effect                       | Multiplier                          | Example at 10% Inflation |
| ---------------------------- | ----------------------------------- | ------------------------ |
| Overall cost multiplier      | 1.0× inflation rate                 | +10% costs               |
| Project costs                | 1.0× inflation rate                 | +10% project costs       |
| Economic cycle upgrade costs | 1.25× inflation rate                | +12.5% cycle costs       |
| Corruption costs             | Scaled by inflation                 | Increased                |
| Productivity growth          | 1.3× inflation rate (penalty)       | -13% productivity growth |
| Construction speed           | 2.0× inflation rate (bonus to cost) | +20% construction costs  |
| Factory/dockyard output      | -1.25× inflation rate               | -12.5% output            |
| Political power              | -1.3× inflation rate                | -13% PP generation       |
| Consumer goods               | -0.5× inflation rate                | +5% consumer goods need  |
| Trade law change costs       | 1.5× inflation rate                 | +15% trade law costs     |

**Deflation** (negative inflation) reverses most of these: costs decrease but output penalties still apply in the opposite direction. Mild deflation can be beneficial, but severe deflation signals economic contraction.

### Managing Inflation

Inflation responds to multiple levers. Here are the main strategies:

**Raise the central bank policy rate.** The most direct tool. Increasing the policy rate above the inflation rate creates a positive real rate, which suppresses inflation over the following quarters. The tradeoff is that high rates also slow economic growth.

**Raise taxes.** Higher tax rates dampen inflation by pulling money out of the economy. However, high corporate taxes reduce productivity growth, so this is a short-term fix with long-term costs.

**Run a budget surplus.** Spending less than you earn reduces inflationary pressure. Cut military spending or unnecessary government programs to bring the budget into surplus.

**Strengthen the currency.** Use Austerity Measures, reduce debt, or improve stability to push currency strength above 1.0. This eliminates the currency inflation channel.

**Adopt a hard-money standard.** Gold and silver backing dampen currency volatility and pull it toward 1.0 over time, which indirectly reduces currency-driven inflation. However, hard-money standards restrict your ability to use the Expand Money Supply decision.

**Avoid the Expand Money Supply decision during high inflation.** This decision amplifies the inflation adjustment and weakens the currency -- useful during deflation but dangerous during inflation.

**Upgrade the economic cycle cautiously.** While a booming economy is desirable, the Fast Growth and Economic Boom stages add inflationary pressure. If inflation is already high, pushing for a higher cycle stage can make it worse.

---

## Economic Indicators

### Employment

Buildings require workers to function at full efficiency. Each facility has a required worker count, and you must allocate a portion of the national population to fill those positions. Allocation is automatic, but buildings without enough workers have reduced output.

If all buildings are fully staffed and workers remain, those workers become unemployed. The unemployment rate is shown in the Economy window.

If unemployment exceeds the **Unemployment Threshold** shown in the Economy window, debuffs apply: a stability penalty and increased social spending. These debuffs grow stronger as unemployment rises.

You can prioritize which building types receive workers first from the Economy window.

### Productivity

**State Productivity** is a per-state variable that directly scales building output and GDP. Each state has its own productivity value, and the country-level overall productivity is calculated as the population-weighted average across all states.

**What Productivity Affects:**

- **Military factory output**: Higher productivity increases factory production efficiency
- **Dockyard output**: Naval construction speed and output
- **Construction speed**: All building construction is faster in high-productivity states
- **Agriculture district output**: Farming yields scale with productivity
- **GDP**: Overall productivity multiplies your total GDP (approximately 0.1% per productivity point)

**Starting Values by Region:**

| Region                                     | Starting Productivity |
| ------------------------------------------ | --------------------- |
| Europe                                     | 1,000                 |
| Asia & Oceania                             | 650                   |
| Africa, Middle East, North & South America | 550                   |

There is no maximum cap on productivity — it can grow indefinitely. The minimum floor is 100; it cannot fall below this.

**Catch-Up Mechanic:**

Productivity growth uses a catch-up mechanism: states with productivity below the global average grow faster than those above it. This means poorer regions naturally converge toward wealthier ones over time, though wealthy states still grow — just more slowly relative to their starting advantage.

**Factors That Increase Productivity Growth:**

| Factor                         | Growth Bonus                                         |
| ------------------------------ | ---------------------------------------------------- |
| Railway infrastructure level 1 | +4%                                                  |
| Railway infrastructure level 2 | +8%                                                  |
| Railway infrastructure level 3 | +12%                                                 |
| Railway infrastructure level 4 | +16%                                                 |
| Railway infrastructure level 5 | +20%                                                 |
| Railway infrastructure level 6 | +24%                                                 |
| Internal investment (state)    | +20% growth in that state while investment is active |
| Economic Cycle (Fast Growth)   | +2.0 monthly productivity growth                     |
| Economic Cycle (Economic Boom) | +3.5 monthly productivity growth                     |
| National focuses and spirits   | Varies                                               |

**Corporate Tax and Productivity:**

Corporate tax directly suppresses productivity growth. The relationship is linear:

- At 20% corporate tax: no productivity growth penalty
- At 40% corporate tax: −10% productivity growth

High taxes generate revenue but slow long-term growth. Finding a balance between revenue needs and long-term productivity is one of the core tensions in economic management.

---

## Economic Cycle

The Economic Cycle represents the overall state of a country's economy. It is displayed as the second icon from the left in the National Statistics and Internal Factions section of the Politics window.

There are six stages, each with distinct modifiers:

| Stage         | Construction Speed | Stability | Productivity Growth | Migration Rate |
| ------------- | ------------------ | --------- | ------------------- | -------------- |
| Depression    | --                 | -10%      | -4.0                | -0.25          |
| Recession     | +20%               | -5%       | -2.5                | -0.15          |
| Stagnation    | +30%               | -2%       | -1.0                | -0.05          |
| Stable Growth | +35%               | --        | +0.5                | +0.05          |
| Fast Growth   | +45%               | +2%       | +2.0                | +0.15          |
| Economic Boom | +55%               | +4%       | +3.5                | +0.25          |

**Upgrading the Economic Cycle** costs both political power and treasury funds. The political power cost increases with each upgrade, and a treasury payment is deducted when the new stage is adopted. Depression is the worst state, reducing productivity growth severely and preventing immigration.

**Changing the Economic Cycle:**

- Spend political power and treasury funds to manually upgrade it
- Some national focuses advance the Economic Cycle directly
- Random events tied to high GDP growth rates can raise it
- Negative events -- such as a housing bubble burst, stock market crash, or banking crisis -- can lower it by one or two levels

---

## Trade Laws

Trade laws control how much of your resource production is exported versus consumed domestically. They are changed through the Politics window and cost 150 political power per change. You can only move one tier at a time (no skipping levels), and certain restrictions apply -- Rentier States (oil-dependent economies) cannot adopt Closed Economy or Consumption Economy, and reducing trade openness may be blocked by international obligations or sanctions.

| Tier | Law                     | Min Export | Consumer Goods | Resource Export Multiplier | Trade Opinion |
| ---- | ----------------------- | ---------- | -------------- | -------------------------- | ------------- |
| 1    | Closed Economy          | 10%        | +8%            | --                         | -30%          |
| 2    | Consumption Economy     | 20%        | +6%            | +4%                        | -20%          |
| 3    | Semi-Consumption        | 40%        | +3%            | +8%                        | -10%          |
| 4    | Mixed Economy (default) | 50%        | --             | +12%                       | +10%          |
| 5    | Export Economy          | 65%        | -3%            | +16%                       | +20%          |
| 6    | Globalized Trade        | 80%        | -6%            | +20%                       | +30%          |

**Key tradeoffs:**

- **Closed/Consumption**: Keeps resources at home for domestic industry. Useful when at war or when you consume more than you produce. Reduces export income and trade opinion. Closed Economy requires either an autocratic government or being at war with a stronger enemy while short on resources.
- **Mixed**: The default starting position. Balanced exports and domestic supply.
- **Export/Globalized**: Maximizes resource export income and trade opinion but forces most production onto the international market, leaving less for domestic use. Reduces consumer goods costs, reflecting the income benefits of open trade.

Inflation increases the cost of changing trade laws (via the `trade_laws_cost_factor` modifier), so adjusting trade policy during high inflation is more expensive.

---

## Economic Laws

Several law categories in the Politics window allow you to fine-tune your economic policies. Each law has multiple tiers that can be changed by spending political power.

### Employment Pressure

Controls how many workers each building requires. Adjusting this law helps manage unemployment:

| Level                     | Worker Requirement | Unemployment Threshold |
| ------------------------- | ------------------ | ---------------------- |
| Comprehensive Regulations | +25%               | -5%                    |
| Strong Regulations        | +12%               | -2%                    |
| Standard Regulations      | Baseline           | Baseline               |
| Light Regulations         | -12%               | +2%                    |
| Minimal Regulations       | -25%               | +5%                    |

Higher regulations force buildings to hire more workers (reducing unemployment) but increase costs. Lower regulations reduce staffing needs, which can help during labor shortages but raises the threshold before unemployment penalties kick in.

### Healthcare Privatization

Determines whether healthcare is publicly or privately run, affecting both health spending costs and health-related income:

| Level                  | Health Cost | Healthcare Income | Workforce Requirement |
| ---------------------- | ----------- | ----------------- | --------------------- |
| Fully Privatized       | -35%        | -40%              | -15%                  |
| Partially Privatized   | -15%        | -20%              | -8%                   |
| Partially Nationalized | +15%        | +15%              | +8%                   |
| Fully Nationalized     | +35%        | +30%              | +15%                  |

Privatized healthcare is cheaper for the government but generates less income and employs fewer workers. Nationalized healthcare costs more but provides greater health coverage and employs more people.

### Mining Policies

Controls resource extraction rates and environmental impact:

| Level                          | Resource Output | Export Multiplier | Stability |
| ------------------------------ | --------------- | ----------------- | --------- |
| Full Environmental Protections | -20%            | -15%              | +15%      |
| Partial Protections            | -10%            | -5%               | +10%      |
| Balanced Protections           | +5%             | --                | +5%       |
| Economic Motivated Mining      | +15%            | +5%               | --        |
| Strip Mining                   | +25%            | +15%              | --        |

Resource-rich nations benefit from looser mining policies but sacrifice stability. Nations with few natural resources lose little from strict protections.

### Critical Infrastructure

Determines the level of infrastructure maintenance spending:

| Level                 | Infrastructure Cost | Infrastructure Tax Income | Energy Output |
| --------------------- | ------------------- | ------------------------- | ------------- |
| Minimal Maintenance   | -25%                | -15%                      | -15%          |
| Standard Maintenance  | -5%                 | --                        | -1.5%         |
| Extensive Maintenance | +25%                | +35%                      | +15%          |

Wealthy nations benefit from extensive maintenance, which boosts both infrastructure tax income and energy generation. Poorer nations may prefer minimal maintenance to conserve funds.

---

## Literacy

Literacy represents the education level of your population and applies a dynamic modifier that scales with your country's literacy rate. It is primarily improved through education spending and national focuses.

| Effect                    | How It Scales                                                                                      |
| ------------------------- | -------------------------------------------------------------------------------------------------- |
| Research Speed            | Higher literacy increases research speed                                                           |
| Productivity Growth       | Higher literacy improves long-term productivity                                                    |
| Education Costs           | Higher literacy increases the cost of maintaining education systems                                |
| Office Productivity       | Educated populations are more productive in office buildings                                       |
| Agricultural Productivity | Higher literacy _reduces_ agricultural output (workers shift away from farming into other sectors) |

The literacy-agriculture tradeoff is most relevant for agrarian economies. Investing heavily in education shifts workers out of the fields, reducing agricultural output even as it boosts research and office productivity. Countries that still rely on farming income need to balance literacy growth against agricultural needs.

---

## Internal Factions

Internal factions represent competing economic and political interest groups within your country. Each faction applies a dynamic modifier that scales with the faction's influence level. Factions can be empowered or weakened through decisions, events, and national focuses.

The main factions with economic effects include:

| Faction                            | Key Economic Effects                                                                        |
| ---------------------------------- | ------------------------------------------------------------------------------------------- |
| **Small & Medium Business Owners** | Construction speed, stability, consumer goods, civilian factory tax income and productivity |
| **International Bankers**          | Office construction, resource output, trade opinion, investment cost and duration           |
| **Fossil Fuel Industry**           | Resource output, fuel production, oil export income                                         |
| **Industrial Conglomerates**       | Infrastructure construction, resource output, civilian industry tax income                  |
| **Oligarchs**                      | Factory construction, resource output                                                       |
| **Defense Industry**               | Military factory construction speed, military factory productivity and tax income           |
| **Maritime Industry**              | Dockyard construction, dockyard output and productivity, dockyard tax income                |
| **Labour Unions**                  | Factory efficiency, political power, health and social spending costs                       |
| **Landowners**                     | Resource output, factory construction, office tax income                                    |
| **Farmers**                        | Consumer goods, population growth, agricultural productivity and construction               |
| **Communist Cadres**               | Consumer goods, bureaucracy costs                                                           |
| **The Priesthood**                 | Stability, political power, education costs                                                 |

Each faction's effects can be positive or negative depending on their influence level and your government's relationship with them. Strong factions aligned with your policies provide bonuses; powerful factions that oppose your government can impose penalties. Managing faction influence is part of the political game but has direct economic consequences.

---

## Sanctions

International sanctions are applied to countries through events, UN votes, and diplomatic actions. Sanctions come in four tiers of increasing severity:

| Tier                            | Construction | Stability | PP        | Trade Opinion | Other Effects                     |
| ------------------------------- | ------------ | --------- | --------- | ------------- | --------------------------------- |
| Reduced Western Sanctions       | -20%         | -1%       | -0.05/day | -10%          | -20% resource exports             |
| Western Sanctions               | -40%         | -2%       | -0.1/day  | -50%          | -50% resource exports             |
| International Sanctions         | -10%         | -10%      | -10%      | -50%          | Blocked from international market |
| Massive International Sanctions | -60%         | -10%      | -0.25/day | -75%          | -75% resource exports             |

At the **International Sanctions** level and above, countries are locked out of resource exports entirely and lose access to international trade benefits.

Sanctions can be increased or decreased through diplomatic events. Reducing sanctions typically requires diplomatic alignment changes, completing certain focuses, or negotiation through international bodies.

---

## Electricity

Countries must supply electricity as part of their infrastructure. Power is generated by constructing specific buildings:

| Building                        | Fuel Source            | Output (base) |
| ------------------------------- | ---------------------- | ------------- |
| Fossil Fuel Powerplant          | Fuel                   | 2 GW          |
| Nuclear Reactor                 | Reactor-Grade Material | 5 GW          |
| Renewable Energy Infrastructure | None                   | 0.5 GW        |

Reactor-Grade Material can be produced at Enrichment Facilities (built from the electricity panel) or purchased from other countries via decisions. States with Geothermal Infrastructure or Hydroelectric Infrastructure modifiers provide additional power.

Electricity consumption is calculated from active buildings and population. Insufficient power generation triggers a dynamic modifier that scales with the size of the shortfall:

| Penalty                 | Effect                                                  |
| ----------------------- | ------------------------------------------------------- |
| Construction Speed      | Reduced proportionally to energy deficit                |
| Factory/Dockyard Output | Reduced proportionally to energy deficit                |
| Research Speed          | Reduced proportionally to energy deficit                |
| Tax Income              | Reduced (businesses produce less revenue without power) |
| Stability               | Penalty from energy shortages                           |

Countries that share power via **Energy Load Sharing** agreements can offset some of their deficit by importing electricity from neighbors, but at a cost.

Additionally, fossil fuel powerplants consume fuel to operate. If your country runs out of fuel, a separate **fuel shortage penalty** applies:

- Reduced tax income
- Stability penalty

This is independent of the electricity shortfall penalty — you can have enough generating capacity but still suffer if you lack the fuel to run your plants.

View your country's electricity situation by clicking the electricity icon in the construction window to open the Electricity Panel. Energy output can be further improved through the **Critical Infrastructure** law.

---

## Buildings

Millennium Dawn replaces or supplements many standard HOI4 buildings with modern equivalents. Beyond the standard civilian and military factories, the following buildings play key roles in the economy.

### Offices

Offices are the backbone of a modern service economy. They employ the most workers per level of any building (0.473 million per level) and generate the highest corporate tax income factor (5.0), making them the single best building for tax revenue. Building offices is the primary way to grow GDP and reduce unemployment in developed nations.

| Property               | Value                   |
| ---------------------- | ----------------------- |
| Base Construction Cost | 40,000                  |
| Max Per State          | 50                      |
| Shares Building Slots  | Yes                     |
| Corporate Tax Factor   | 5.0                     |
| Base Workers           | 0.473 million per level |

Offices also drive civilian microchip consumption — each staffed office consumes microchips proportional to its worker fulfillment, so nations with many offices need corresponding microchip production.

### Internet Stations

Internet stations represent a country's digital infrastructure. Each level provides a **+5% state productivity growth modifier**, making them a long-term multiplier on economic output. They are cheap to build and employ few workers, making them an efficient early investment.

| Property               | Value                                   |
| ---------------------- | --------------------------------------- |
| Base Construction Cost | 5,000 (+1,450 per additional level)     |
| Max Per State          | 6                                       |
| Shares Building Slots  | No                                      |
| Base Workers           | 0.012 million per level                 |
| Effect                 | +5% state productivity growth per level |

### Agriculture Districts

Agriculture districts represent organized commercial farming. They produce **fuel** (8 units per hour per level, representing ethanol/biofuel) and provide **local supply** (+0.015 per level) to the state. They are important for agrarian economies and for nations looking to supplement their fuel supply without relying on fossil fuel imports.

| Property               | Value                                |
| ---------------------- | ------------------------------------ |
| Base Construction Cost | 15,000 (+1,250 per additional level) |
| Max Per State          | 10                                   |
| Shares Building Slots  | Yes                                  |
| Base Workers           | 0.188 million per level              |
| Fuel Output            | 8 per hour per level                 |
| Local Supply           | +0.015 per level                     |

Agriculture districts also interact with the Farmers internal faction — their construction speed and tax income can be boosted by maintaining high faction opinion.

### Energy Infrastructure

Energy Infrastructure is a **keystone building** — each state can have at most one, and it competes with Industrial Infrastructure for the same keystone slot. It boosts energy-related construction and provides additional building slots.

| Property               | Value                                                                                                                    |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Base Construction Cost | 33,000                                                                                                                   |
| Max Per State          | 1 (keystone slot)                                                                                                        |
| Effect                 | +5% building slots, +10% renewable energy generation, +10% nuclear reactor construction speed, +10% factory repair speed |

### Industrial Infrastructure

Industrial Infrastructure is the alternative keystone building. It increases the efficiency of resource extraction in the state.

| Property               | Value                                                  |
| ---------------------- | ------------------------------------------------------ |
| Base Construction Cost | 36,000                                                 |
| Max Per State          | 1 (keystone slot)                                      |
| Effect                 | +15% resource gain efficiency per infrastructure level |

Choose between Energy and Industrial Infrastructure based on the state's role: energy-producing states benefit from the Energy keystone, while resource-rich states benefit from the Industrial keystone.

---

## Advanced Industrial Buildings

Millennium Dawn introduces three advanced building types that produce strategic resources essential for modern military equipment and high-tech industry. These buildings share state building slots with other industrial buildings and scale in cost with each additional level.

### Microchip Plants

Microchip plants produce **microchips**, a strategic resource required for advanced electronics, guided munitions, and modern military systems.

| Property               | Value                                |
| ---------------------- | ------------------------------------ |
| Base Construction Cost | 45,000 (+2,500 per additional level) |
| Resource Output        | 20 microchips per level              |
| Resource Input         | 2 tungsten + 1 chromium per level    |
| Max Per State          | 5                                    |
| Shares Building Slots  | Yes                                  |
| Corporate Tax Factor   | 4.0                                  |
| Base Workers           | 0.0375 million per level             |

Microchip plants have the second-highest corporate tax factor in the game (behind offices), making them a strong source of tax revenue. However, they require a steady supply of tungsten and chromium to operate -- countries without domestic access to these resources will need to import them.

### Composite Plants

Composite plants produce **composites**, a strategic resource used in advanced armor, aircraft construction, and modern naval vessels.

| Property               | Value                                   |
| ---------------------- | --------------------------------------- |
| Base Construction Cost | 45,000 (+2,500 per additional level)    |
| Resource Output        | 16 composites per level                 |
| Resource Input         | 1 rubber + 1 chromium + 1 oil per level |
| Max Per State          | 5                                       |
| Shares Building Slots  | Yes                                     |
| Corporate Tax Factor   | 3.5                                     |
| Base Workers           | 0.0375 million per level                |

Composite plants require three different input resources (rubber, chromium, and oil), making them the most resource-intensive building to sustain. Countries with limited resource access should secure trade agreements or invest in synthetic refineries to supply the rubber component.

### Synthetic Refineries

Synthetic refineries produce both **rubber** (3 per level) and **fuel** (2 per hour per level), making them a dual-purpose strategic building.

| Property               | Value                                      |
| ---------------------- | ------------------------------------------ |
| Base Construction Cost | 32,000                                     |
| Resource Output        | 3 rubber per level + 2 fuel/hour per level |
| Max Per State          | 2                                          |
| Shares Building Slots  | Yes                                        |
| Corporate Tax Factor   | 3.0                                        |
| Base Workers           | 0.184 million per level                    |

Synthetic refineries are the most labor-intensive advanced building by far, employing nearly 5 times as many workers per level as microchip or composite plants. They are critical for resource-poor nations that need rubber for composite production and fuel for mechanized and naval operations. Researching advanced refinery technologies increases rubber output by +1 per level per tech tier.

### Input Resource Shortages

Microchip and composite plants require input resources to operate. If you run short of these inputs, production is reduced proportionally -- up to a maximum penalty of -95%.

**Microchip Plants** check tungsten and chromium supply weekly:

- Tungsten shortages are weighted 1.25x heavier than chromium shortages
- If both inputs are completely exhausted, microchip output drops to 5% of normal

**Composite Plants** check rubber, chromium, and oil supply weekly:

- Rubber shortages are weighted 1.5x heavier than chromium shortages
- All three inputs must be available for full production

**Energy shortages** also reduce microchip and composite production. If your country has an electricity deficit, plant output is further penalized on top of any input resource shortages. Production line technology research reduces the energy demand of both plant types.

Securing a stable supply of input resources -- through domestic mining, trade agreements, or synthetic refineries (for rubber) -- is essential before investing heavily in advanced plants.

### Civilian Microchip Consumption

Beyond military equipment, microchips are consumed by the civilian economy. This consumption is recalculated monthly and scales with two factors:

- **Population consumption**: Based on total population multiplied by GDP per capita. Wealthier, larger nations consume far more civilian microchips.
- **Office park consumption**: Each staffed office building consumes additional microchips proportional to its worker fulfillment.

The combined civilian demand is subtracted from available microchip supply. If demand exceeds supply:

- **At war**: Military equipment production takes priority. The civilian sector receives whatever is left, and shortfalls apply a stability penalty (up to -15%).
- **At peace**: The civilian sector takes priority. Military production may suffer instead.

This means rapidly industrializing nations that build many offices and grow their GDP per capita will face increasing microchip demand even without expanding their military. Countries should plan microchip plant construction to stay ahead of both military and civilian consumption.

### Military Equipment Requirements

Microchips and composites are required to produce modern military equipment. The main categories include:

**Microchip-dependent equipment:**

| Equipment Type             | Microchips Required                   |
| -------------------------- | ------------------------------------- |
| Electronic warfare systems | 1-3 per unit (scales with tech level) |
| SAM missile systems        | 1 per unit                            |
| Guided missiles            | 1 per unit                            |
| Ballistic missiles         | 2 per unit                            |
| Nuclear missiles           | 2 per unit                            |
| Advanced artillery         | 4-8 per unit                          |
| Anti-air systems           | 1-2 per unit                          |
| Anti-tank (ATGM) systems   | 1-2 per unit                          |
| Advanced tank chassis      | 1-2 per unit                          |
| Advanced aircraft          | 1-2 per unit                          |
| Ship combat modules        | 1-4 per module (scales with level)    |

**Composite-dependent equipment:**

| Equipment Type       | Composites Required                  |
| -------------------- | ------------------------------------ |
| Advanced artillery   | 2 per unit                           |
| Advanced aircraft    | 1-2 per unit                         |
| Modern naval vessels | 1-6 per ship (scales with ship type) |

Without sufficient microchip or composite stockpiles, production of these equipment types will stall or slow significantly. Nations planning a modern military buildup should establish microchip and composite production well before they need to ramp up equipment manufacturing.

### Building Employment Values

Every building in Millennium Dawn requires workers from your population. The base worker requirement per level (in millions) is multiplied by a GDP-dependent factor -- wealthier nations need more workers per building due to higher service-sector overhead. The worker requirement can be further modified by the **Employment Pressure** law and building-specific modifiers.

| Building                | Base Workers (millions per level) |
| ----------------------- | --------------------------------- |
| Offices                 | 0.473                             |
| Civilian Factories      | 0.206                             |
| Agriculture Districts   | 0.188                             |
| Synthetic Refineries    | 0.184                             |
| Nuclear Reactors        | 0.148                             |
| Microchip Plants        | 0.0375                            |
| Composite Plants        | 0.0375                            |
| Renewable Energy        | 0.0225                            |
| Military Factories      | 0.0188                            |
| Dockyards               | 0.0188                            |
| Internet Stations       | 0.012                             |
| Fossil Fuel Powerplants | 0.0075                            |

When planning your economy, consider the employment impact of your building choices. Offices and civilian factories employ the most people per level, which helps reduce unemployment but requires a large working-age population. Microchip and composite plants employ relatively few workers, making them efficient for smaller nations that need high-value output without straining their labor pool. Synthetic refineries sit in the middle, employing significantly more than other advanced buildings.

If buildings cannot be fully staffed, their output is reduced proportionally to the manpower fulfillment ratio.

---

## Immigration

Immigration is one way to grow your population. Migration happens automatically, but you can adjust the acceptance level by changing the stage of **Migration Laws** (found at the far right of Policies in the Politics window).

Immigration control costs money. Stricter restrictions cost more to enforce. The immigration rate is calculated from factors including national productivity, unemployment rate, and war status, and is further modified by national spirits and other sources. The Economic Cycle also affects migration: higher growth stages attract more immigrants, while depression and recession drive emigration.

---

## International Investments

You can construct buildings in foreign countries through International Investments. This requires spending treasury funds and takes time, but provides:

- **Investment returns**: approximately 6% annually, paid as weekly income, subject to modification by national spirits and currency strength
- **Influence**: gaining leverage over the receiving country

Some countries will refuse international investments. AI-controlled countries may also offer to invest in yours.

To initiate an international investment, click on a foreign state, then click the arrow button to open the interface and proceed. Investment returns are denominated in the reserve currency, so a weak domestic currency increases the local value of returns.

---

## Internal Investment

Internal investments work like international investments but target your own states. Click on a domestic state, then click the arrow button to open the interface.

Internal investments can:

- Increase a state's productivity growth rate
- Add building slots
- Apply temporary modifiers for a limited period

Each investment costs political power and treasury funds. Investment costs are increased by inflation.

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
4. **Check your reserve currency**: Ensure you are using a currency appropriate to your faction alignment

### Mid Game

1. **Invest internationally**: Generate passive income from foreign buildings
2. **Upgrade the Economic Cycle**: Major buffs for stability and construction speed
3. **Manage debt aggressively**: High interest cripples long-term growth
4. **Adjust economic laws**: Tune employment pressure, mining policies, and healthcare privatization to match your situation
5. **Watch your currency strength**: A collapsing currency feeds inflation and increases debt burden

### Late Game

1. **Maintain high social spending**: Reduces unemployment impact
2. **Optimize tax rates**: Find the balance between revenue and productivity
3. **Use aid and trade**: Leverage diplomatic relationships for supplementary income
4. **Consider monetary policy**: Use Expand Money Supply during deficits or Austerity during inflation

### Common Mistakes to Avoid

- **Excessive military spending**: The fastest way to bankrupt your economy
- **Ignoring unemployment**: Leads to compounding stability penalties
- **High debt accumulation**: Interest costs compound and eventually trigger crisis events
- **Over-taxation**: Kills productivity growth and long-term revenue
- **Ignoring currency strength**: A weak currency spirals into inflation, higher debt costs, and economic instability
- **Neglecting bailout options**: Request IMF or influencer bailouts before interest rates exceed 15%
- **Ignoring electricity**: An energy deficit silently drags down construction, factory output, research, and tax income
- **Fighting inflation with only one tool**: Inflation responds to policy rate, taxes, budget balance, and currency together — relying on a single lever is less effective
- **Raising the policy rate without considering debt**: The policy rate contributes to your interest rate, so hiking it while heavily indebted can worsen a debt spiral even as it controls inflation

---

## Related Documentation

- [International Systems Guide](/player-tutorials/international-systems) - For PMCs, sanctions, and other international economic systems
- [European Union Tutorial](/player-tutorials/eu-tutorial) - For EU-specific economic mechanics (Eurozone, ECB, single market)
- [Game Rules](/player-tutorials/game-rules)
