# Search Filter Reference

How `search_filters` work in MD focus trees, what every relevant filter means, and how to assign them.

## How Search Filters Work

Each focus can have one or more `search_filters` values. They power the filter buttons in the focus search UI: clicking a filter shows only focuses tagged with it. Every focus **must** have at least one filter.

```
search_filters = { FOCUS_FILTER_POLITICAL FOCUS_FILTER_ISRPOLIT }
```

Multiple filters are space-separated inside the braces, on a single line.

## Two-Layer Convention

Most country trees use a **two-layer** approach:

1. **Country-specific filter** — which country/faction the focus belongs to (e.g. `FOCUS_FILTER_ISRPOLIT`, `FOCUS_FILTER_RUSSIA_ECONOMY`). Always include this.
2. **Generic filter** — the broad category (e.g. `FOCUS_FILTER_POLITICAL`, `FOCUS_FILTER_INDUSTRY`). Makes the focus discoverable through global filter buttons.

Countries using only custom filters are invisible to generic searches. Always include both layers.

**Exception:** Smaller/simpler trees may use only generic filters with no custom ones — this is fine.

## Generic Filters — Full Reference

### Political & Governance

- `FOCUS_FILTER_POLITICAL` — government/ideology change, party politics, elections, constitutional reforms, power consolidation
- `FOCUS_FILTER_STABILITY` — focuses that directly raise/lower stability, suppress unrest, or deal with internal order
- `FOCUS_FILTER_INTERNAL_AFFAIRS` — domestic governance, civil service reform, bureaucracy, regional autonomy
- `FOCUS_FILTER_INTERNAL_FACTION` — managing internal party factions, coalition politics, faction-specific content
- `FOCUS_FILTER_CORRUPTION` — anti-corruption initiatives, judicial reform aimed at accountability
- `FOCUS_FILTER_PROPAGANDA` — information control, state media, ideological campaigns
- `FOCUS_FILTER_RADICALIZATION` — political radicalization events, extremist movements
- `FOCUS_FILTER_SOCIAL_CONSERVATISM` — social policy reforms, cultural legislation, religious law

### Military

- `FOCUS_FILTER_MILITARY_LAWS` — military doctrine, organisation laws, high command reforms, general military policy
- `FOCUS_FILTER_ARMY` — ground forces: infantry equipment, armour, artillery, divisions, ground XP
- `FOCUS_FILTER_AIRCRAFT` — air force: plane procurement, air squadrons, airbase upgrades, air XP, pilot training
- `FOCUS_FILTER_NAVY` — naval: ship construction, submarine programs, naval XP, fleet composition
- `FOCUS_FILTER_EQUIPMENT` — weapons systems/hardware: missile defence, precision munitions, missile programs, military exports
- `FOCUS_FILTER_MANPOWER` — conscription laws, reserve forces, mobilisation capacity, recruitment
- `FOCUS_FILTER_WAR_SUPPORT` — focuses that raise war support or prepare the public for conflict
- `FOCUS_FILTER_ARMY_XP` / `FOCUS_FILTER_AIR_XP` / `FOCUS_FILTER_NAVY_XP` — focuses whose primary effect is granting army/air/navy experience
- `FOCUS_FILTER_SPACE` — space programs, satellite launches, aerospace development
- `FOCUS_FILTER_INSURGENCY` — counter-insurgency, occupation management, conflict with non-state actors, intifada-type mechanics

### Economy & Industry

- `FOCUS_FILTER_INDUSTRY` — factory construction, infrastructure investment, industrial capacity, general economic development
- `FOCUS_FILTER_ECONOMY` — macroeconomic policy, fiscal reform, monetary policy, economic restructuring
- `FOCUS_FILTER_EXPENDITURE` — budget spending decisions, costly investment focuses; needs `ai_will_do` bankruptcy guard (below)
- `FOCUS_FILTER_RESEARCH` — technology research bonuses, university investments, R&D programs, science institutions
- `FOCUS_FILTER_RESOURCE` — natural resource extraction, energy deals, gas/oil agreements, mining
- `FOCUS_FILTER_TRADE` — trade agreements, export policy, customs union membership
- `FOCUS_FILTER_FOREIGN_INVESTMENTS` — attracting foreign capital, investment zones, privatisation
- `FOCUS_FILTER_ENVIRONMENT` — green energy, conservation, environmental policy
- `FOCUS_FILTER_RENEWABLE_ENERGY_INFRASTRUCTURE` — specifically renewable energy (solar, wind, etc.) infrastructure
- `FOCUS_FILTER_POWER_INFRASTRUCTURE` — electrical grid, power station construction
- `FOCUS_FILTER_ADD_BUILDING` — focuses whose primary effect is directly constructing a specific building type
- `FOCUS_FILTER_INFRASTRUCTURE` — road/rail/port infrastructure projects (not factory slots)

Bankruptcy guard for `FOCUS_FILTER_EXPENDITURE` focuses: a `factor = 0` / `has_active_mission = bankruptcy_incoming_collapse` modifier in `ai_will_do`.

### Diplomacy & Foreign Relations

- `FOCUS_FILTER_FOREIGN_POLICY` — general diplomatic relations, treaties, improving/worsening relations with specific countries
- `FOCUS_FILTER_DIPLOMACY` — direct diplomatic actions: guarantees, non-aggression pacts, military access
- `FOCUS_FILTER_INFLUENCE` — soft power, sphere of influence, puppet relations
- `FOCUS_FILTER_ANNEXATION` — territorial expansion, annexing nations, puppet→annex transitions
- `FOCUS_FILTER_SECTARIANISM` — religious or ethnic conflict between communities, sectarian violence mechanics
- `FOCUS_FILTER_MIGRANT_CRISIS` — refugee flows, migration pressure, border management

### Alliance & Bloc Filters

| Filter                        | When to use                                                   |
| ----------------------------- | ------------------------------------------------------------- |
| `FOCUS_FILTER_NATO`           | NATO membership, related focuses, Atlantic alliance mechanics |
| `FOCUS_FILTER_EUROPEAN_UNION` | EU integration focuses, EU membership mechanics               |
| `FOCUS_FILTER_CMW`            | Commonwealth of Nations membership and mechanics              |
| `FOCUS_FILTER_TFV_AUTONOMY`   | Autonomy within a faction or overlord relationship            |

### Meta / System Filters

| Filter                        | When to use                                                    |
| ----------------------------- | -------------------------------------------------------------- |
| `FOCUS_FILTER_COUNTER_DEBUFF` | Focuses designed to remove a starting negative national spirit |

## Israel-Specific Filters

Israel uses six custom filters. Every Israel focus needs the ISR custom filter **plus** the corresponding generic filter below.

- `FOCUS_FILTER_ISRPOLIT` (pair: `FOCUS_FILTER_POLITICAL`) — party politics, government composition, ideology changes, elections, constitutional reforms
- `FOCUS_FILTER_ISRMILITARY` (pair varies — see subcategory mapping below) — IDF doctrine, training, military organisation
- `FOCUS_FILTER_ISRFOREIGNPOL` (pair: `FOCUS_FILTER_FOREIGN_POLICY`) — diplomacy, treaties, alliances, regional relations (Abraham Accords, Arab states, USA, etc.)
- `FOCUS_FILTER_ISRECON` (pair varies — see subcategory mapping below) — Israeli economic development, fiscal policy, high-tech sector
- `FOCUS_FILTER_ISRPALSTUFF` (pair: `FOCUS_FILTER_INSURGENCY`) — Israeli-Palestinian conflict mechanics: intifada, settlements, operations, occupation
- `FOCUS_FILTER_ISRPOLICE` (pair: `FOCUS_FILTER_STABILITY`) — Israeli law enforcement, Mišmeret Yisraʾel, internal security institutions

### ISRMILITARY Subcategory Mapping

When a focus has `FOCUS_FILTER_ISRMILITARY`, choose the generic based on its content:

- `FOCUS_FILTER_AIRCRAFT` — air force doctrine, plane procurement, squadron management, pilot training, airbase upgrades. Examples: ISR_raam, ISR_sufa, ISR_adir, ISR_focus_air, ISR_lavi, ISR_shuffle_squadrons, ISR_aerospace_industries_focus
- `FOCUS_FILTER_NAVY` — naval: ships, submarines, fleet programs. Examples: ISR_focus_navy, ISR_ships_saar, ISR_dolphin_1, ISR_dakar
- `FOCUS_FILTER_SPACE` + `FOCUS_FILTER_EQUIPMENT` — space programs, satellite systems. Examples: ISR_spaceil, ISR_bereshit, ISR_kochav, ISR_ofek_satellites, ISR_ilan_ramon
- `FOCUS_FILTER_EQUIPMENT` — missile defence systems, weapons systems, military hardware, armoured vehicle programs. Examples: ISR_iron_dome, ISR_davids_sling, ISR_arrow, ISR_magic_wand, ISR_merkava_focus, ISR_fab_defense, ISR_mafat
- `FOCUS_FILTER_MILITARY_LAWS` — ground doctrine, training programs, brigade organisation, special forces. Examples: ISR_war_between_the_wars, ISR_tenufa_project, ISR_gideon_plan, ISR_focus_ground_forces, ISR_urban_warfare

### ISRECON Subcategory Mapping

- `FOCUS_FILTER_RESEARCH` + `FOCUS_FILTER_INDUSTRY` — R&D, universities, tech sector investment, innovation. Examples: ISR_ben_gurion_university, ISR_hightech_fortress, ISR_start_up_nation
- `FOCUS_FILTER_RESOURCE` + `FOCUS_FILTER_INDUSTRY` — natural resources, gas deals, energy agreements. Examples: ISR_pass_the_gas_deal, ISR_compromise_gas_deal, ISR_karish
- `FOCUS_FILTER_INDUSTRY` — general economic development, factories, fiscal policy. Examples: ISR_middle_class, ISR_israel_green_deal, ISR_diamond_district

## Other Country Custom Filters (Quick Reference)

These custom filters exist for other country trees — do not add them to Israel or unrelated trees:

| Country       | Custom Filters                                                           |
| ------------- | ------------------------------------------------------------------------ |
| Russia        | `FOCUS_FILTER_RUSSIA_ECONOMY`, `FOCUS_FILTER_RUSSIA_ARMY` (+ more below) |
| Ukraine       | `FOCUS_FILTER_UKRAINE_VSU`, `FOCUS_FILTER_UKRAINE_SECURITY` (+ below)    |
| Armenia       | `FOCUS_FILTER_ARMENIA_*` (5 filters — listed below)                      |
| Brazil        | `FOCUS_FILTER_BRAZILIAN_MERCOSUR`, `FOCUS_FILTER_UNASUL` (+2 below)      |
| Iran          | `FOCUS_FILTER_IRANIAN_NUCLEAR_DEV`, `FOCUS_FILTER_THOUSAND` (+1 below)   |
| Korea         | `FOCUS_FILTER_KOREAN_PENINSULA`, `FOCUS_FILTER_KOREAN_NUCLEAR_ISSUE`     |
| Italy         | `FOCUS_FILTER_ITA_MAFIA`                                                 |
| UK            | `FOCUS_FILTER_INNER_CIRCLE`                                              |
| Czech Rep.    | `FOCUS_FILTER_SKODA`                                                     |
| Spain         | `FOCUS_FILTER_SPR_CULTURE`                                               |
| Transnistria  | `FOCUS_FILTER_TRANSNISTRIA_*` (9 filters)                                |
| South Ossetia | `FOCUS_FILTER_OSSETIA_*` (7 filters)                                     |
| Ural          | `FOCUS_FILTER_URAL_*` (3 filters)                                        |

- Russia also: party filters (LDPR, CPRF, UNITED, etc.)
- Ukraine also: party/leader filters
- Armenia's 5: `FOCUS_FILTER_ARMENIA_POLITIC`, `FOCUS_FILTER_ARMENIA_DIPLOMACY`, `FOCUS_FILTER_ARMENIA_ECONOMY`, `FOCUS_FILTER_ARMENIA_ARMY`, `FOCUS_FILTER_ARMENIA_POLICE`
- Brazil also: `FOCUS_FILTER_OPERATION_CAR_WASH`, `FOCUS_FILTER_AMAZON_CONSERVATION`
- Iran also: `FOCUS_FILTER_COLLAPSE_ISLAMIC_REPUBLIC`

## Common Mistakes

- **Only custom filter, no generic** → always add the paired generic (see the reference above)
- **`FOCUS_FILTER_MILITARY`** → use `FOCUS_FILTER_MILITARY_LAWS` (MILITARY is a legacy/unused alias)
- **Using `FOCUS_FILTER_DIPLOMACY` for all foreign policy** → `FOCUS_FILTER_FOREIGN_POLICY`: general relations; `FOCUS_FILTER_DIPLOMACY`: diplomatic actions
- **Tagging economic investment focuses without `FOCUS_FILTER_EXPENDITURE`** → add `FOCUS_FILTER_EXPENDITURE` and an `ai_will_do` bankruptcy guard to treasury-spending focuses
- **Missing filter entirely** → every focus must have at least one filter
- **Using another country's custom filter** → custom filters (`RUSSIA_*`, `UKRAINE_*`, `ISRPOLIT`, etc.) are country-specific — never cross-assign

## Checklist When Adding a New Focus

1. Choose the **country-specific custom filter** matching the focus's branch.
2. Choose the **generic filter** from the reference above (one or two — don't over-tag).
3. For money-spending focuses, add a `factor = 0` modifier in `ai_will_do` conditioned on `has_active_mission = bankruptcy_incoming_collapse` (AI-only, not in `available`). The gate is the completion_reward's actual money cost (a negative `treasury_change` via `modify_treasury_effect` summing to ~5bn or more, or a money-costing scripted/building effect), not the focus `cost` field, which is completion time. **Why:** a reward that spends real treasury drags an AI already in collapse deeper into debt.
4. Write `search_filters` as a single line: `search_filters = { CUSTOM_FILTER GENERIC_FILTER }`.
