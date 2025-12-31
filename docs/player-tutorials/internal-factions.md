---
layout: default
title: "Internal Faction Tutorial"
description: "Tutorial for the Internal Factions for Millennium Dawn: A Modern Day mod."
---

# Internal Factions Guide

## Overview

Internal Factions represent powerful interest groups within your country that can provide significant bonuses or penalties based on their opinion of your government. Each faction has an opinion score ranging from 0-100, with 50 being neutral. Higher opinion grants better bonuses, while lower opinion reduces or reverses these benefits.

---

## How Opinion Works

Opinion represents how happy the current internal faction is with the ruling party. Ideas that modify the minimum value of an internal faction it will also increase the minimum opinion the faction's opinion will tick to via the monthly internal faction tick.

- **Starting Opinion**: 60 when you first add a faction (50 for some nations)
- **Monthly Decay**: Opinion naturally decays toward the minimum threshold each month
- **Opinion Ranges**:
  - **Hostile**: 0-30
  - **Negative**: 31-49
  - **Indifferent**: 50-69
  - **Positive**: 70-89
  - **Enthusiastic**: 90-100

- **Autocrat Bonus**: Autocratic governments (Western Autocrats, Emerging Autocrats, Neutral Autocrats, Fascists, Military Junta) receive **double opinion changes** from events and decisions

---

## Economic Factions

### Small & Medium Business Owners
**Dynamic Bonuses** (scale with opinion):
- Industrial Complex construction speed (max +15%)
- Stability (max +10%)
- Consumer goods factor (max -10%)
- Civilian factory tax income (max +20%)
- Internet station construction speed (max +15%)
- Civilian factory productivity (max +15%)

**Events**:
- Tax cut demands (if opinion >60)
- Foreign company buyouts
- Bureaucracy complaints
- Startup funding requests
- Banking disputes
- Fossil fuel industry conflicts
- Harassment by large companies
- Labor union disputes
- Religious day business conflicts

**Decisions**:
- **Raise Wages**: +5 opinion (also affects Labour Unions, Communist Cadres)
- **Subsidize Small Businesses**: +5 opinion, -4% corporate tax income for 120 days

---

### International Bankers
**Static Bonuses**:
- Interest rate multiplier: -1
- Expected education modifier: +0.5

**Dynamic Bonuses** (scale with opinion):
- Office construction speed (max +15%)
- Local resources factor (max +10%)
- Trade opinion factor (max +20%)
- Democratic acceptance (max +25)
- Democratic drift (max +0.05)
- Investment duration (max -10%)
- Investment cost (max -10%)
- Office park tax income (max +15%)

**Events**:
- Refusing loans to small businesses
- Foreign company buyouts
- Grain silo purchases by bankers

**Decisions**:
- **Cut Taxes on the Rich**: +5 opinion (also affects Landowners, Oligarchs)

---

### Fossil Fuel Industry
**Dynamic Bonuses** (scale with opinion):
- Local resources factor (max +20%)
- Fuel gain factor (max +25%)
- Justify war goal time (max -15%)
- Oil export multiplier (max +20%)
- Fuel silo construction speed (max +15%)

**Events**:
- Clean energy campaigns
- Biofuel investment conflicts with Farmers
- Fuel silo proposals

**Decisions**:
- **Encourage Additional Resource Production**: +5 opinion, +15% local resources, -5% corporate tax income for 90 days
- **Cut Backs on Regulations**: +5 opinion, +30% resource export multiplier, -0.001 stability/week for 180 days
- **Cut Taxes on Industry**: +5 opinion (also affects Defense Industry, Maritime Industry, Industrial Conglomerates)

---

### Industrial Conglomerates
**Static Bonuses**:
- Investment duration: -25%
- Expected administration modifier: +0.5

**Dynamic Bonuses** (scale with opinion):
- Infrastructure construction speed (max +15%)
- Local resources factor (max +10%)
- Communist acceptance (max +25)
- Communist drift (max +0.05)
- Civilian factory tax income (max +20%)

**Events**:
- Foreign company buyouts
- Harassment of small businesses
- Labor union disputes
- Agrarian change resistance
- Agricultural complex conversions

**Decisions**:
- **Raise Wages**: +5 opinion (shared with SMBO)
- **Subsidize Small Businesses**: +5 opinion (shared with SMBO)
- **Cut Taxes on Industry**: +5 opinion

---

### Oligarchs
**Static Bonuses**:
- Corruption cost factor: +25%
- Expected education modifier: -0.5

**Dynamic Bonuses** (scale with opinion):
- Industrial complex construction speed (max +15%)
- Local resources factor (max +20%)
- Communist acceptance (max +25)
- Communist drift (max +0.05)

**Events**:
- Foreign company buyouts
- Harassment of small businesses
- Intelligence service investigations
- Tax cut demands
- Migrant labor abuse

**Decisions**:
- **Cut Taxes on the Rich**: +5 opinion
- **Encourage Additional Resource Production**: +5 opinion
- **Sell Political Positions**: +5 opinion, gain treasury income, risk increasing corruption

---

## Militaristic Factions

### Maritime Industry
**Static Bonus**:
- Expected military budget modifier: +0.5

**Dynamic Bonuses** (scale with opinion):
- Dockyard construction speed (max +20%)
- Naval base construction speed (max +20%)
- Dockyard industrial capacity (max +20%)
- Navy max range factor (max +20%)
- Dockyard productivity (max +20%)
- Dockyard tax income (max +20%)

**Events**:
- Subsidy requests
- Convoy production subsidies
- Warehouse purchases in coastal areas

**Decisions**:
- **Cut Taxes on Industry**: +5 opinion

---

### Defense Industry (Military-Industrial Complex)
**Static Bonus**:
- Expected military budget modifier: +0.5

**Dynamic Bonuses** (scale with opinion):
- Military factory construction speed (max +10%)
- Factory efficiency gain (max +15%)
- Factory base efficiency (max +15%)
- Military factory productivity (max +15%)
- Military factory tax income (max +20%)

**Events**:
- SAM site demands after border incursions
- Military industry thriving (if opinion >80)
- Labor union disputes

**Decisions**:
- **Cut Taxes on Industry**: +5 opinion

---

### The Military
**Static Bonuses**:
- Nationalist drift: +0.02
- Expected military budget modifier: +0.5

**Dynamic Bonuses** (scale with opinion):
- Army organization (max +5%)
- Army morale (max +10%)
- Training time (max -20%)
- Air base construction speed (max +25%)
- Personnel cost multiplier (max -25%)

**Minimum Opinion Bonuses**:
- Defense spending level increases minimum opinion (+5% per tier from "Reasonable Defense" to "Total War Economy")

**Events**:
- SAM site demands
- Government opposition (if you're liberal/progressive)
- Ideological conflicts with Communist Cadres
- Foreign nationals in military

**Decisions**:
- **Allow Foreign Nationals**: -5 opinion, +5% conscription factor, +15% migration rate
- **Repeal Foreign Nationals**: +5 opinion

---

### Intelligence Community
**Static Bonus**:
- Expected police budget modifier: +0.5

**Dynamic Bonuses** (scale with opinion):
- **With La Resistance DLC**: Civilian/Army/Navy/Airforce intel factor (max +15% each)
- **Without DLC**: Decryption/Encryption factor (max +20% each)
- Radar station construction speed (max +25%)
- Foreign subversive activities cost (max -20%)
- Foreign influence effectiveness (max +15%)

**Events**:
- Citizen surveillance scandals
- Oligarch investigations
- Religious institution surveillance

---

## Special Interest Factions

### Labour Unions
**Static Bonuses**:
- Expected military budget modifier: -0.5
- Expected healthcare modifier: +0.5

**Dynamic Bonuses** (scale with opinion):
- Factory start efficiency (max +10%)
- Factory efficiency gain (max +10%)
- Political power factor (max +25%)
- Healthcare cost multiplier (max -15%)
- Social spending cost multiplier (max -15%)

**Events**:
- Work contract disputes
- Pay increase demands from businesses
- Healthcare spending requests
- Social spending demands
- Migration protests

**Decisions**:
- **Tax Labour Unions**: -10 opinion, -10% consumer goods, +5% population tax income for 90 days
- **Raise Wages**: +10 opinion (also affects SMBO and Industrial Conglomerates)

---

### Landowners
**Static Bonuses**:
- Corruption cost factor: +15%
- Expected welfare modifier: -0.5

**Dynamic Bonuses** (scale with opinion):
- Local resources factor (max +15%)
- Conscription factor (max +15%)
- Industrial complex construction speed (max +15%)
- Office park tax income (max +15%)
- Political power factor (max +15%)

**Events**:
- Tax cut demands
- Agrarian change resistance
- Religious institution funding
- Migrant labor abuse

**Decisions**:
- **Cut Taxes on the Rich**: +5 opinion
- **Encourage Additional Resource Production**: +5 opinion
- **Sell Political Positions**: +5 opinion

---

### Farmers
**Static Bonuses**:
- Agriculture workers modifier: +5%
- Agriculture district worker requirement: +5%

**Dynamic Bonuses** (scale with opinion):
- Conscription factor (max +10%)
- Consumer goods factor (max -10%)
- Monthly population growth (max +20%)
- Agricultural district construction speed (max +15%)
- Agriculture district tax income (max +20%)

**Special**: Opinion changes are **doubled** if you have increased agricultural subsidies (Syria-specific)

**Events**:
- Agrarian change resistance
- Losing ground / subsidy requests
- Biofuel investment proposals
- Renewable energy investments
- Tax cut demands
- Agricultural complex conversions

**Decisions**:
- **Agricultural District Tax Credits**: +5 opinion, -10% agriculture district tax income for 120 days

---

### Communist Cadres
**Static Bonus**:
- Expected administration modifier: +0.5

**Dynamic Bonuses** (scale with opinion):
- Army organization regain (max +20%)
- Consumer goods factor (max -5%)
- Army core defense factor (max +10%)
- Mobilization speed (max +25%)
- Bureaucracy cost multiplier (max -15%)

**Events**:
- Ideological conflicts with Military
- Governmental concession requests
- Taxing religious institutions (positive)

**Decisions**:
- **Encourage Party Propaganda**: +5 opinion (doubled if no elections), costs 0.2% of GDP
- **Sell Political Positions**: +5 opinion
- **Raise Wages**: +5 opinion (shared with Labour Unions)

---

## Religious Factions

### The Priesthood
**Static Bonus**:
- Expected military budget modifier: -0.5

**Dynamic Bonuses** (scale with opinion):
- Stability factor (max +15%)
- Monthly population growth (max +25%)
- Political power (max +30%)
- Education cost multiplier (max -10%)

**Available for**: Buddhism, Hinduism, Shinto, Cheondo

**Events**:
- Business on religious days
- Representation requests
- Education board input requests

**Decisions**:
- **Encourage Religion in Government**: +5 opinion, +5% ruling outlook popularity
- **Impose Taxes on Religious Institutions**: -15 opinion, +10 opinion for Communist Cadres
- **Repeal Religious Taxes**: +5 opinion

---

### The Ulema
**Static Bonus**:
- Expected military budget modifier: -0.5

**Dynamic Bonuses** (same as The Priesthood)

**Available for**: Sunni, Ibadi, Sufi Islam, Shia

**Events**:
- Friday sermon political debates
- Education system disputes
- Mosque funding requests
- Religious collaboration with neighbors
- Political edicts

**Decisions**: Same as The Priesthood

---

### The Clergy
**Static Bonus**:
- Expected military budget modifier: -0.5

**Dynamic Bonuses** (same as The Priesthood)

**Available for**: Orthodox Christian, Christian, Eastern Church variants

**Events**: Same as The Priesthood

**Decisions**: Same as The Priesthood

---

### Wahabi Ulema
**Static Bonus**:
- Expected military budget modifier: +0.5 (opposite of other religious factions)

**Dynamic Bonuses** (scale with opinion):
- Stability factor (max +15%)
- Monthly population growth (max +25%)
- Political power (max +30%)
- Fascism drift (max +0.25%)
- Education cost multiplier (max -10%)

**Available for**: Saudi Arabia, Qatar, UAE, certain Islamic extremist nations

**Events**:
- Shia/Sufi crackdown demands
- Anti-women work policies
- Morality patrol requests

**Decisions**: Same as other religious factions

---

## Nation-Specific Factions

### The Donju (North Korea)
**Static Bonuses**:
- Corruption cost factor: +30%
- Interest rate multiplier: -1

**Dynamic Bonuses** (scale with opinion):
- Industrial complex construction speed (max +15%)
- Stability (max +15%)
- Consumer goods factor (max -5%)
- Infrastructure construction speed (max +15%)

**Events**: Similar to Small & Medium Business Owners

---

### Saudi Royal Family
**Available for**: Saudi Arabia, Qatar, Bahrain, Oman, Kuwait

**Dynamic Bonuses** (scale with opinion):
- Political power factor (max +25%)
- Ideology drift defense (max +25%)
- Stability factor (max +15%)

**Events**:
- Extended family jet airliner requests
- Prince arguments
- Prince defections

---

### Iranian Quds Force
**Static Bonus**:
- Send volunteer size: +2
- Expected military budget modifier: +0.5

**Dynamic Bonuses** (scale with opinion):
- Communist drift (max +0.10%)
- Offensive influence operations (max +1.75%)

**Available for**: Iraq, Hamas, Hezbollah, Syria, Houthis, Yemen, Kurdistan, and other Iranian proxies

**Events**: Limited specific events

---

### Foreign Jihadis
**Static Bonuses**:
- Send volunteer size: +1
- Surrender limit: +0.2
- Expected military budget modifier: +0.5
- Weekly manpower: +100
- Adds 7,500 manpower on activation

**Dynamic Bonuses** (scale with opinion):
- Fascism drift (max +0.10%)
- Non-core manpower (max +10%)
- Special forces cap (max +20%)

**Available for**: Islamic extremist factions

---

### Wall Street (USA)
**Static Bonuses**:
- Economic cycles cost factor: -25%
- Democratic drift: +0.02
- Interest rate multiplier: -1
- Expected welfare modifier: -0.25
- Expected healthcare modifier: -0.25

**Dynamic Bonuses** (scale with opinion):
- Local resources factor (max +5%)
- Trade opinion factor (max +20%)
- Industrial complex construction speed (max +10%)
- Office park tax income (max +15%)
- Investment cost (max -10%)
- Investment duration (max -10%)

**Events**: Similar to International Bankers

---

### Chaebols (South Korea)
**Static Bonuses**:
- Corruption cost factor: +25%
- Receiving investment duration: -25%
- Interest rate multiplier: -1

**Dynamic Bonuses** (scale with opinion):
- Industrial complex construction speed (max +15%)
- Infrastructure construction speed (max +15%)
- Local resources factor (max +15%)

**Events**: Similar to Industrial Conglomerates

---

## Strategic Tips

1. **Prioritize High-Value Factions**: Focus on factions that align with your playstyle (military for conquest, economic for buildup)

2. **Use Autocratic Governments**: The doubled opinion gain makes managing factions much easier

3. **Monitor Opinion Decay**: Opinion naturally decays toward minimum thresholds monthly, so regular maintenance is needed

4. **Stack Related Decisions**: Many decisions affect multiple factions simultaneously

5. **Plan for Events**: Keep 75-150 political power available for faction-related decisions

6. **Balance Conflicting Factions**: Some factions (Labour Unions vs. Business Owners) have opposing interests

7. **Time Your Tax Changes**: Use tax decisions to boost faction opinion before major events

8. **Religious Faction Power**: Religious factions provide significant stability and population growth bonuses

9. **Economic Factions for Building**: High opinion with economic factions dramatically speeds construction

10. **Military Factions for War**: Essential for extended conflicts due to organization, morale, and cost bonuses

---

## Common Event Chains

**Business vs. Labor**: Events often force you to choose between business interests (SMBO, Industrial Conglomerates) and worker interests (Labour Unions)

**Religious vs. Secular**: Religious factions request government influence, education control, and funding

**Resource Extraction**: Fossil Fuel Industry, Oligarchs, and Landowners push for deregulation and tax cuts

**Military Spending**: The Military pushes for increased budgets and foreign recruitment

**Corruption Opportunities**: Oligarchs, Landowners, and Communist Cadres offer treasury income in exchange for increased corruption

---

## Quick Reference Table

| Faction | Best For | Key Bonus | Cost |
|---------|----------|-----------|------|
| Small & Medium Business Owners | Civilian economy | +15% civ construction | 1500 PP |
| International Bankers | Trade & investment | -1 interest rate | 1500 PP |
| Fossil Fuel Industry | Resource production | +25% fuel gain | 1500 PP |
| Industrial Conglomerates | Infrastructure | +15% infra construction | 1500 PP |
| Oligarchs | Communist nations | +20% local resources | 1500 PP |
| Maritime Industry | Naval powers | +20% dockyard speed | 1500 PP |
| Defense Industry | Military production | +15% mil factory productivity | 1500 PP |
| The Military | Combat effectiveness | +10% army morale | 1500 PP |
| Intelligence Community | Espionage | +15% intel factors | 1500 PP |
| Labour Unions | Social policies | +25% political power | 1500 PP |
| Landowners | Resource exploitation | +15% local resources | 1500 PP |
| Farmers | Agriculture | +20% population growth | 1500 PP |
| Communist Cadres | Communist nations | +25% mobilization speed | 1500 PP |
| Religious Factions | Stability & growth | +30% political power | 1500 PP |

---

*Last Updated: December 2025 (Based on mod version)*
