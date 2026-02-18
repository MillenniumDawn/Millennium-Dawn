---
layout: default
title: "Economy Guide"
description: "Comprehensive guide to the economy system in Millennium Dawn"
---

# Economy Guide

This guide provides an in-depth explanation of Millennium Dawn's economy system, covering revenue, expenses, debt management, and economic optimization strategies.

## Table of Contents

- [Revenue](#revenue)
  - [Tax Income](#tax-income)
  - [Corporate Tax](#corporate-tax)
  - [Population Tax](#population-tax)
  - [Additional Income](#additional-income)
- [Expenses](#expenses)
  - [Military Spending](#military-spending)
  - [Bureaucracy](#bureaucracy)
  - [Police/Security](#police-security)
  - [Education](#education)
  - [Health](#health)
  - [Social/Welfare](#socialwelfare)
- [Debt and Interest](#debt-and-interest)
  - [Interest Rate Calculation](#interest-rate-calculation)
  - [High Interest Penalties](#high-interest-penalties)
  - [Managing Debt](#managing-debt)
- [Tax Rate Changes](#tax-rate-changes)
- [Economic Indicators](#economic-indicators)
  - [GDP and GDP per Capita](#gdp-and-gdp-per-capita)
  - [Employment](#employment)
  - [Productivity](#productivity)
- [Strategic Tips](#strategic-tips)

---

## Revenue

Your country's weekly income comes from multiple sources. Understanding how each contributes helps you optimize revenue.

### Tax Income

The primary source of revenue is taxes, divided into two categories:

- **Corporate Tax**: Revenue from businesses and buildings
- **Population Tax**: Revenue from citizens

The **Average Tax Rate** is displayed in the economy UI and equals the average of your corporate and population tax rates.

### Corporate Tax

Corporate tax is calculated from multiple building types and factors:

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

**Corporate Tax Effects:**

- **Productivity Growth**: Higher taxes reduce productivity growth (20% tax = 0%, 40% tax = -10%)
- **Consumer Goods**: Each 1% corporate tax adds 0.015% to consumer goods penalty
- **Investment Cost**: Higher taxes increase the cost of receiving foreign investments

### Population Tax

Population tax scales with:

- Total population
- GDP per capita (wealthier populations pay more)
- Your chosen tax rate

Higher population taxes apply a **stability penalty** (1% tax rate = -0.01% stability).

### Additional Income

Various sources can provide supplementary revenue:

- **Foreign Aid**: Some countries receive aid (e.g., US aid to allies, Iranian aid)
- **International Investments**: Returns from investing in other countries (~6% annually)
- **Trade Routes**: Controlling strategic chokepoints (Suez, Panama, Hormuz) provides income
- **EU Subsidies**: Member states receive various subsidies
- **Country-Specific Income**: Special ideas and national foci (tourism, narcotics, etc.)

---

## Expenses

Government spending is divided into six categories. Higher spending levels provide buffs but cost more.

### Military Spending

Military spending is the most complex expense category, calculated from:

| Cost Component         | Description                                           |
| ---------------------- | ----------------------------------------------------- |
| Base Military Industry | Military factories and dockyards                      |
| Personnel Costs        | Soldiers (special forces > elite > regular > militia) |
| Equipment Costs        | Weapons, vehicles, aircraft, naval vessels            |
| Deployed vs Stockpiled | Equipment in use costs more than in storage           |

**Military Spending Levels (0-9):**

- Level 0: Minimal funding (~0.46% multiplier)
- Level 9: Maximum funding (~10% multiplier)

GDP per capita affects military costs—wealthier nations pay more to maintain their armed forces.

### Bureaucracy

Bureaucracy spending affects:

- Policy implementation speed
- National focus completion time
- Administrative efficiency

**Levels 1-5:** Costs scale from 1x to 3.4x base rate, based on population.

### Police/Security

Police spending provides:

- Stability bonuses
- Reduced crime rates
- Counter-terrorism effectiveness

**Levels 1-5:** Costs scale from 1x to 3.4x base rate, based on population.

### Education

Education spending is influenced by:

- Population size
- Number of research slots (more slots = higher costs)
- Nuclear, air, land, and naval facilities

**Levels 1-5:** Provides research speed and population growth bonuses.

### Health

Health spending scales with population and provides:

- Population growth bonuses
- Stability bonuses
- Manpower recovery rates

**Levels 1-6:** Costs scale from 1.1x to 11x base rate.

### Social/Welfare

Social spending affects:

- Stability
- Population happiness
- Unemployment impact

**Levels 1-6:** Costs scale from 1x to 9.5x base rate. High social spending reduces unemployment penalties.

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

The **Debt-to-GDP Ratio** indicates your ability to repay debt. Higher ratios mean higher interest rates.

### High Interest Penalties

When interest exceeds **15%**, severe penalties activate:

| Penalty                 | Effect                                           |
| ----------------------- | ------------------------------------------------ |
| Construction Speed      | -5% per point above 15%                          |
| Factory/Dockyard Output | -5% per point above 15%                          |
| Stability               | -2% per point above 15%                          |
| Political Drift         | -1% per point above 15% (affects all ideologies) |

### Managing Debt

**Automatic Debt:**

- If your treasury goes negative, the game automatically borrows
- Auto-borrowing takes 1% of GDP plus the deficit
- A 1% fee applies to automatically borrowed funds

**Debt Management Strategies:**

1. Maintain a positive weekly balance to pay down debt
2. Reduce military spending temporarily
3. Increase tax rates cautiously (reduces productivity)
4. Use economic foci to reduce interest rates
5. Build up treasury during economic booms

---

## Tax Rate Changes

You can adjust tax rates through the economy interface:

- **Change Limit**: Taxes can only be changed once every 5 months (250 days)
- **Corporate Tax**: Affects building output, productivity, consumer goods
- **Population Tax**: Affects stability

**Tax Rate Change Cost**: Each 1% change costs approximately 50 political power.

---

## Economic Indicators

### GDP and GDP per Capita

**GDP (Gross Domestic Product):**

- Total value of all goods and services produced
- Determined by active buildings and employment levels
- Affects: Interest rates, research slots, country rank spirits

**GDP per Capita:**

- GDP divided by population
- Affects: Research speed, construction speed, stability, population growth
- Wealthier nations have higher GDP/capita but face higher military/construction costs

### Employment

Buildings require workers to function at full efficiency:

- Each building type has a required worker count
- **Manpower fulfillment** determines output percentage
- Unfilled positions reduce building output proportionally

**Managing Employment:**

- Prioritize building types in the Economy window
- Balance civilian and military construction
- Monitor unemployment rate in the economy UI

### Productivity

**State Productivity:**

- Regional productivity affects local building output
- Starting productivity varies by region (Europe: 1000, Asia: 650, Africa/South America: 550)

**Increasing Productivity:**

- Economic Cycle upgrades
- Infrastructure investments
- Focuses and national spirits
- State-specific modifiers

---

## Strategic Tips

### Early Game Economics

1. **Balance initial taxes**: Start moderate to avoid killing productivity
2. **Build offices first**: They provide high tax income per worker
3. **Monitor employment**: Don't overbuild factories without workers

### Mid-Game Optimization

1. **Invest internationally**: Generate passive income from foreign buildings
2. **Upgrade Economic Cycle**: Major buffs for stability and construction
3. **Manage debt aggressively**: High interest cripples growth

### Late-Game Wealth

1. **Maintain high social spending**: Reduces unemployment impact
2. **Optimize tax rates**: Find the balance between revenue and growth
3. **Use aid and trade**: Leverage diplomatic relationships for income

### Common Mistakes to Avoid

- **Excessive military spending**: Bankrupts the economy
- **Ignoring unemployment**: Leads to stability penalties
- **High debt accumulation**: Interest compounds against you
- **Over-taxation**: Kills productivity and growth

---

## Related Documentation

- UI Guide (coming soon)
- Economic Cycle (coming soon)
- International Investments (coming soon)
- [Game Rules]({{ '/player-tutorials/game-rules' | relative_url }})
