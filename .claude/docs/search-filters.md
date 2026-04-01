# Search Filter Reference

This document covers how `search_filters` work in Millennium Dawn focus trees, what every relevant filter means, and the conventions for assigning them correctly.

---

## How Search Filters Work

Each focus can have one or more `search_filters` values. These power the filter buttons in the focus search UI — clicking a filter shows only focuses tagged with it. Every focus **must** have at least one filter.

```
search_filters = { FOCUS_FILTER_POLITICAL FOCUS_FILTER_ISRPOLIT }
```

Multiple filters are space-separated inside the braces and written on a single line.

---

## Two-Layer Convention

Most country trees in MD use a **two-layer** approach:

1. **Country-specific filter** — identifies which country/faction the focus belongs to (e.g. `FOCUS_FILTER_ISRPOLIT`, `FOCUS_FILTER_RUSSIA_ECONOMY`). Always include this.
2. **Generic filter** — the broad category it falls into (e.g. `FOCUS_FILTER_POLITICAL`, `FOCUS_FILTER_INDUSTRY`). Makes the focus discoverable through the global filter buttons.

Countries that use only custom filters (no generic layer) are invisible to generic filter searches. Always include both layers.

**Exception:** Smaller or simpler trees may use only generic filters with no custom ones — this is fine.

---

## Generic Filters — Full Reference

### Political & Governance

| Filter                             | When to use                                                                                                        |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `FOCUS_FILTER_POLITICAL`           | Government system changes, ideology shifts, party politics, elections, constitutional reforms, power consolidation |
| `FOCUS_FILTER_STABILITY`           | Focuses that directly raise/lower stability, suppress unrest, or deal with internal order                          |
| `FOCUS_FILTER_INTERNAL_AFFAIRS`    | Domestic governance, civil service reform, bureaucracy, regional autonomy                                          |
| `FOCUS_FILTER_INTERNAL_FACTION`    | Managing internal party factions, coalition politics, faction-specific content                                     |
| `FOCUS_FILTER_CORRUPTION`          | Anti-corruption initiatives, judicial reform aimed at accountability                                               |
| `FOCUS_FILTER_PROPAGANDA`          | Information control, state media, ideological campaigns                                                            |
| `FOCUS_FILTER_RADICALIZATION`      | Political radicalization events, extremist movements                                                               |
| `FOCUS_FILTER_SOCIAL_CONSERVATISM` | Social policy reforms, cultural legislation, religious law                                                         |

### Military

| Filter                       | When to use                                                                                                     |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `FOCUS_FILTER_MILITARY_LAWS` | Military doctrine, organisation laws, high command reforms, general military policy                             |
| `FOCUS_FILTER_ARMY`          | Ground forces: infantry equipment, armour, artillery, divisions, ground XP                                      |
| `FOCUS_FILTER_AIRCRAFT`      | Air force: plane procurement, air squadrons, airbase upgrades, air XP, pilot training                           |
| `FOCUS_FILTER_NAVY`          | Naval: ship construction, submarine programs, naval XP, fleet composition                                       |
| `FOCUS_FILTER_EQUIPMENT`     | Weapons systems and military hardware: missile defence, precision munitions, missile programs, military exports |
| `FOCUS_FILTER_MANPOWER`      | Conscription laws, reserve forces, mobilisation capacity, recruitment                                           |
| `FOCUS_FILTER_WAR_SUPPORT`   | Focuses that raise war support or prepare the public for conflict                                               |
| `FOCUS_FILTER_ARMY_XP`       | Focuses whose primary effect is granting army experience                                                        |
| `FOCUS_FILTER_AIR_XP`        | Focuses whose primary effect is granting air experience                                                         |
| `FOCUS_FILTER_NAVY_XP`       | Focuses whose primary effect is granting navy experience                                                        |
| `FOCUS_FILTER_SPACE`         | Space programs, satellite launches, aerospace development                                                       |
| `FOCUS_FILTER_INSURGENCY`    | Counter-insurgency, occupation management, conflict with non-state actors, intifada-type mechanics              |

### Economy & Industry

| Filter                                         | When to use                                                                                                                                   |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `FOCUS_FILTER_INDUSTRY`                        | Factory construction, infrastructure investment, industrial capacity, general economic development                                            |
| `FOCUS_FILTER_ECONOMY`                         | Macroeconomic policy, fiscal reform, monetary policy, economic restructuring                                                                  |
| `FOCUS_FILTER_EXPENDITURE`                     | Budget spending decisions, costly investment focuses (pair with `NOT = { has_active_mission = bankruptcy_incoming_collapse }` in `available`) |
| `FOCUS_FILTER_RESEARCH`                        | Technology research bonuses, university investments, R&D programs, science institutions                                                       |
| `FOCUS_FILTER_RESOURCE`                        | Natural resource extraction, energy deals, gas/oil agreements, mining                                                                         |
| `FOCUS_FILTER_TRADE`                           | Trade agreements, export policy, customs union membership                                                                                     |
| `FOCUS_FILTER_FOREIGN_INVESTMENTS`             | Attracting foreign capital, investment zones, privatisation                                                                                   |
| `FOCUS_FILTER_ENVIRONMENT`                     | Green energy, conservation, environmental policy                                                                                              |
| `FOCUS_FILTER_RENEWABLE_ENERGY_INFRASTRUCTURE` | Specifically renewable energy (solar, wind, etc.) infrastructure                                                                              |
| `FOCUS_FILTER_POWER_INFRASTRUCTURE`            | Electrical grid, power station construction                                                                                                   |
| `FOCUS_FILTER_ADD_BUILDING`                    | Focuses whose primary effect is directly constructing a specific building type                                                                |
| `FOCUS_FILTER_INFRASTRUCTURE`                  | Road/rail/port infrastructure projects (not factory slots)                                                                                    |

### Diplomacy & Foreign Relations

| Filter                        | When to use                                                                                   |
| ----------------------------- | --------------------------------------------------------------------------------------------- |
| `FOCUS_FILTER_FOREIGN_POLICY` | General diplomatic relations, treaties, improving/worsening relations with specific countries |
| `FOCUS_FILTER_DIPLOMACY`      | Direct diplomatic actions: guarantees, non-aggression pacts, military access                  |
| `FOCUS_FILTER_INFLUENCE`      | Soft power, sphere of influence, puppet relations                                             |
| `FOCUS_FILTER_ANNEXATION`     | Territorial expansion, annexing nations, puppet→annex transitions                             |
| `FOCUS_FILTER_SECTARIANISM`   | Religious or ethnic conflict between communities, sectarian violence mechanics                |
| `FOCUS_FILTER_MIGRANT_CRISIS` | Refugee flows, migration pressure, border management                                          |

### Alliance & Bloc Filters

| Filter                        | When to use                                                        |
| ----------------------------- | ------------------------------------------------------------------ |
| `FOCUS_FILTER_NATO`           | NATO membership, NATO-related focuses, Atlantic alliance mechanics |
| `FOCUS_FILTER_EUROPEAN_UNION` | EU integration focuses, EU membership mechanics                    |
| `FOCUS_FILTER_CMW`            | Commonwealth of Nations membership and mechanics                   |
| `FOCUS_FILTER_TFV_AUTONOMY`   | Autonomy within a faction or overlord relationship                 |

### Meta / System Filters

| Filter                        | When to use                                                                 |
| ----------------------------- | --------------------------------------------------------------------------- |
| `FOCUS_FILTER_COUNTER_DEBUFF` | Focuses specifically designed to remove a starting negative national spirit |

---

## Israel-Specific Filters

Israel uses six custom filters. Every Israel focus should have the ISR custom filter **plus** the corresponding generic filter from the table below.

| ISR Filter                   | Purpose                                                                                               | Paired Generic Filter         |
| ---------------------------- | ----------------------------------------------------------------------------------------------------- | ----------------------------- |
| `FOCUS_FILTER_ISRPOLIT`      | Party politics, government composition, ideology changes, electoral mechanics, constitutional reforms | `FOCUS_FILTER_POLITICAL`      |
| `FOCUS_FILTER_ISRMILITARY`   | IDF doctrine, training, military organisation — see subcategory table below                           | varies (see below)            |
| `FOCUS_FILTER_ISRFOREIGNPOL` | Diplomacy, treaties, alliances, regional relations (Abraham Accords, Arab states, USA, etc.)          | `FOCUS_FILTER_FOREIGN_POLICY` |
| `FOCUS_FILTER_ISRECON`       | Israeli economic development, fiscal policy, high-tech sector — see subcategory table                 | varies (see below)            |
| `FOCUS_FILTER_ISRPALSTUFF`   | Israeli-Palestinian conflict mechanics: intifada, settlements, operations, occupation                 | `FOCUS_FILTER_INSURGENCY`     |
| `FOCUS_FILTER_ISRPOLICE`     | Israeli law enforcement, Mišmeret Yisraʾel, internal security institutions                            | `FOCUS_FILTER_STABILITY`      |

### ISRMILITARY Subcategory Mapping

When a focus has `FOCUS_FILTER_ISRMILITARY`, choose the generic based on its content:

| Content type                                                                                 | Generic to add                                  | Example focuses                                                                                              |
| -------------------------------------------------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Air force doctrine, plane procurement, squadron management, pilot training, airbase upgrades | `FOCUS_FILTER_AIRCRAFT`                         | ISR_raam, ISR_sufa, ISR_adir, ISR_focus_air, ISR_lavi, ISR_shuffle_squadrons, ISR_aerospace_industries_focus |
| Naval: ships, submarines, fleet programs                                                     | `FOCUS_FILTER_NAVY`                             | ISR_focus_navy, ISR_ships_saar, ISR_dolphin_1, ISR_dakar                                                     |
| Space programs, satellite systems                                                            | `FOCUS_FILTER_SPACE` + `FOCUS_FILTER_EQUIPMENT` | ISR_spaceil, ISR_bereshit, ISR_kochav, ISR_ofek_satellites, ISR_ilan_ramon                                   |
| Missile defence systems, weapons systems, military hardware, armoured vehicle programs       | `FOCUS_FILTER_EQUIPMENT`                        | ISR_iron_dome, ISR_davids_sling, ISR_arrow, ISR_magic_wand, ISR_merkava_focus, ISR_fab_defense, ISR_mafat    |
| Ground doctrine, training programs, brigade organisation, special forces                     | `FOCUS_FILTER_MILITARY_LAWS`                    | ISR_war_between_the_wars, ISR_tenufa_project, ISR_gideon_plan, ISR_focus_ground_forces, ISR_urban_warfare    |

### ISRECON Subcategory Mapping

| Content type                                           | Generic to add                                    | Example focuses                                                       |
| ------------------------------------------------------ | ------------------------------------------------- | --------------------------------------------------------------------- |
| R&D, universities, tech sector investment, innovation  | `FOCUS_FILTER_RESEARCH` + `FOCUS_FILTER_INDUSTRY` | ISR_ben_gurion_university, ISR_hightech_fortress, ISR_start_up_nation |
| Natural resources, gas deals, energy agreements        | `FOCUS_FILTER_RESOURCE` + `FOCUS_FILTER_INDUSTRY` | ISR_pass_the_gas_deal, ISR_compromise_gas_deal, ISR_karish            |
| General economic development, factories, fiscal policy | `FOCUS_FILTER_INDUSTRY`                           | ISR_middle_class, ISR_israel_green_deal, ISR_diamond_district         |

---

## Other Country Custom Filters (Quick Reference)

These custom filters exist for other country trees — do not add them to Israel or other unrelated trees:

| Country       | Custom Filters                                                                                                                                               |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Russia        | `FOCUS_FILTER_RUSSIA_ECONOMY`, `FOCUS_FILTER_RUSSIA_ARMY`, party filters (LDPR, CPRF, UNITED, etc.)                                                          |
| Ukraine       | `FOCUS_FILTER_UKRAINE_VSU`, `FOCUS_FILTER_UKRAINE_SECURITY`, party/leader filters                                                                            |
| Armenia       | `FOCUS_FILTER_ARMENIA_POLITIC`, `FOCUS_FILTER_ARMENIA_DIPLOMACY`, `FOCUS_FILTER_ARMENIA_ECONOMY`, `FOCUS_FILTER_ARMENIA_ARMY`, `FOCUS_FILTER_ARMENIA_POLICE` |
| Brazil        | `FOCUS_FILTER_BRAZILIAN_MERCOSUR`, `FOCUS_FILTER_UNASUL`, `FOCUS_FILTER_OPERATION_CAR_WASH`, `FOCUS_FILTER_AMAZON_CONSERVATION`                              |
| Iran          | `FOCUS_FILTER_IRANIAN_NUCLEAR_DEV`, `FOCUS_FILTER_COLLAPSE_ISLAMIC_REPUBLIC`, `FOCUS_FILTER_THOUSAND`                                                        |
| Korea         | `FOCUS_FILTER_KOREAN_PENINSULA`, `FOCUS_FILTER_KOREAN_NUCLEAR_ISSUE`                                                                                         |
| Italy         | `FOCUS_FILTER_ITA_MAFIA`                                                                                                                                     |
| UK            | `FOCUS_FILTER_INNER_CIRCLE`                                                                                                                                  |
| Czech Rep.    | `FOCUS_FILTER_SKODA`                                                                                                                                         |
| Spain         | `FOCUS_FILTER_SPR_CULTURE`                                                                                                                                   |
| Transnistria  | `FOCUS_FILTER_TRANSNISTRIA_*` (9 filters)                                                                                                                    |
| South Ossetia | `FOCUS_FILTER_OSSETIA_*` (7 filters)                                                                                                                         |
| Ural          | `FOCUS_FILTER_URAL_*` (3 filters)                                                                                                                            |

---

## Common Mistakes

| Wrong                                                                  | Correct                                                                                                                  |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Only custom filter, no generic                                         | Always add the paired generic (see tables above)                                                                         |
| `FOCUS_FILTER_MILITARY`                                                | Use `FOCUS_FILTER_MILITARY_LAWS` (MILITARY is a legacy/unused alias)                                                     |
| Using `FOCUS_FILTER_DIPLOMACY` for all foreign policy                  | Use `FOCUS_FILTER_FOREIGN_POLICY` for general relations; `FOCUS_FILTER_DIPLOMACY` for specific diplomatic actions        |
| Tagging economic investment focuses without `FOCUS_FILTER_EXPENDITURE` | Add `FOCUS_FILTER_EXPENDITURE` to high-cost industrial/economic focuses, and pair with a bankruptcy guard in `available` |
| Missing filter entirely                                                | Every focus must have at least one filter                                                                                |
| Using another country's custom filter                                  | Custom filters (RUSSIA*\*, UKRAINE*\*, ISRPOLIT, etc.) are country-specific — never cross-assign                         |

---

## Checklist When Adding a New Focus

1. Choose the **country-specific custom filter** that matches the focus's branch
2. Choose the **generic filter** from the tables above (one or two — don't over-tag)
3. For high-cost focuses (`cost >= 8`, or `cost >= 5` for military/economy/research focuses): add `NOT = { has_active_mission = bankruptcy_incoming_collapse }` to `available`
4. Write the `search_filters` line as a single line: `search_filters = { CUSTOM_FILTER GENERIC_FILTER }`
