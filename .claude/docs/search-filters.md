# Search Filter Reference

Every focus needs at least one `search_filters` value, written on one line:

```
search_filters = { FOCUS_FILTER_ISRPOLIT FOCUS_FILTER_POLITICAL }
```

Most country trees use two layers: the country's custom filter for the branch, plus one
or two generic filters so the focus shows up in global searches. A tree with only custom
filters is invisible to generic searches. Small trees may use generic filters alone.

## Generic filters

Political:

- `FOCUS_FILTER_POLITICAL`: government and ideology change, parties, elections,
  constitutional reform.
- `FOCUS_FILTER_STABILITY`: stability changes, unrest, internal order.
- `FOCUS_FILTER_INTERNAL_AFFAIRS`: domestic governance, bureaucracy, regional autonomy.
- `FOCUS_FILTER_INTERNAL_FACTION`: internal party factions and coalition politics.
- `FOCUS_FILTER_CORRUPTION`: anti-corruption and judicial accountability.
- `FOCUS_FILTER_PROPAGANDA`: information control, state media.
- `FOCUS_FILTER_RADICALIZATION`: radicalization and extremist movements.
- `FOCUS_FILTER_SOCIAL_CONSERVATISM`: social policy, cultural legislation, religious law.

Military:

- `FOCUS_FILTER_MILITARY_LAWS`: doctrine, organisation, high command, general military
  policy.
- `FOCUS_FILTER_ARMY`, `FOCUS_FILTER_AIRCRAFT`, `FOCUS_FILTER_NAVY`: the service branch.
- `FOCUS_FILTER_EQUIPMENT`: weapons systems, missile defence, military exports.
- `FOCUS_FILTER_MANPOWER`: conscription, reserves, mobilisation.
- `FOCUS_FILTER_WAR_SUPPORT`: raising war support.
- `FOCUS_FILTER_ARMY_XP`, `FOCUS_FILTER_AIR_XP`, `FOCUS_FILTER_NAVY_XP`: the primary
  effect is experience.
- `FOCUS_FILTER_SPACE`: space programs and satellites.
- `FOCUS_FILTER_INSURGENCY`: counter-insurgency, occupation, non-state actors.

Economy:

- `FOCUS_FILTER_INDUSTRY`: factories, industrial capacity, general development.
- `FOCUS_FILTER_ECONOMY`: fiscal and monetary policy, restructuring.
- `FOCUS_FILTER_EXPENDITURE`: the reward spends treasury. Needs the bankruptcy guard.
- `FOCUS_FILTER_RESEARCH`: research bonuses, universities, R&D.
- `FOCUS_FILTER_RESOURCE`: resource extraction and energy deals.
- `FOCUS_FILTER_TRADE`: trade agreements, export policy.
- `FOCUS_FILTER_FOREIGN_INVESTMENTS`: foreign capital, investment zones, privatisation.
- `FOCUS_FILTER_ENVIRONMENT`: green energy, conservation.
- `FOCUS_FILTER_RENEWABLE_ENERGY_INFRASTRUCTURE`: renewable energy infrastructure.
- `FOCUS_FILTER_POWER_INFRASTRUCTURE`: grid and power stations.
- `FOCUS_FILTER_ADD_BUILDING`: the primary effect builds a specific building.
- `FOCUS_FILTER_INFRASTRUCTURE`: road, rail, and port projects.

Diplomacy:

- `FOCUS_FILTER_FOREIGN_POLICY`: general relations and treaties.
- `FOCUS_FILTER_DIPLOMACY`: direct actions such as guarantees, pacts, military access.
- `FOCUS_FILTER_INFLUENCE`: soft power, sphere of influence, puppets.
- `FOCUS_FILTER_ANNEXATION`: territorial expansion and annexation.
- `FOCUS_FILTER_SECTARIANISM`: religious or ethnic conflict.
- `FOCUS_FILTER_MIGRANT_CRISIS`: refugee flows, border management.

Blocs and system:

- `FOCUS_FILTER_NATO`, `FOCUS_FILTER_EUROPEAN_UNION`, `FOCUS_FILTER_CMW` (Commonwealth).
- `FOCUS_FILTER_TFV_AUTONOMY`: autonomy within a faction or under an overlord.
- `FOCUS_FILTER_COUNTER_DEBUFF`: removes a starting negative national spirit.

## Bankruptcy guard

A focus whose `completion_reward` spends real treasury (about 5bn or more through
`modify_treasury_effect`, or a money-costing scripted or building effect) takes
`FOCUS_FILTER_EXPENDITURE` and this modifier in `ai_will_do`:

```
modifier = {
 factor = 0
 has_active_mission = bankruptcy_incoming_collapse
}
```

The gate is the reward's money cost, not the focus `cost` field, which is completion
time. Keep it in `ai_will_do`, never `available`.

## Israel

Every Israel focus takes its custom filter plus the generic pair:

| Custom                       | Generic pair                  |
| ---------------------------- | ----------------------------- |
| `FOCUS_FILTER_ISRPOLIT`      | `FOCUS_FILTER_POLITICAL`      |
| `FOCUS_FILTER_ISRFOREIGNPOL` | `FOCUS_FILTER_FOREIGN_POLICY` |
| `FOCUS_FILTER_ISRPALSTUFF`   | `FOCUS_FILTER_INSURGENCY`     |
| `FOCUS_FILTER_ISRPOLICE`     | `FOCUS_FILTER_STABILITY`      |
| `FOCUS_FILTER_ISRMILITARY`   | By content, below             |
| `FOCUS_FILTER_ISRECON`       | By content, below             |

- `ISRMILITARY`: air force content takes `FOCUS_FILTER_AIRCRAFT`, naval takes
  `FOCUS_FILTER_NAVY`, space takes `FOCUS_FILTER_SPACE` and `FOCUS_FILTER_EQUIPMENT`,
  weapons systems and missile defence take `FOCUS_FILTER_EQUIPMENT`, and ground
  doctrine and training take `FOCUS_FILTER_MILITARY_LAWS`.
- `ISRECON`: R&D takes `FOCUS_FILTER_RESEARCH` and `FOCUS_FILTER_INDUSTRY`, resources
  and gas deals take `FOCUS_FILTER_RESOURCE` and `FOCUS_FILTER_INDUSTRY`, and general
  development takes `FOCUS_FILTER_INDUSTRY`.

## Other custom filters

Custom filters are country-specific. Never use another country's.

| Country       | Custom filters                                                          |
| ------------- | ----------------------------------------------------------------------- |
| Russia        | `FOCUS_FILTER_RUSSIA_ECONOMY`, `FOCUS_FILTER_RUSSIA_ARMY`, party ones   |
| Ukraine       | `FOCUS_FILTER_UKRAINE_VSU`, `FOCUS_FILTER_UKRAINE_SECURITY`, party ones |
| Armenia       | `FOCUS_FILTER_ARMENIA_*` (5 filters)                                    |
| Brazil        | `FOCUS_FILTER_BRAZILIAN_MERCOSUR`, `FOCUS_FILTER_UNASUL`, 2 more        |
| Iran          | `FOCUS_FILTER_IRANIAN_NUCLEAR_DEV`, `FOCUS_FILTER_THOUSAND`, 1 more     |
| Korea         | `FOCUS_FILTER_KOREAN_PENINSULA`, `FOCUS_FILTER_KOREAN_NUCLEAR_ISSUE`    |
| Italy         | `FOCUS_FILTER_ITA_MAFIA`                                                |
| UK            | `FOCUS_FILTER_INNER_CIRCLE`                                             |
| Czech Rep.    | `FOCUS_FILTER_SKODA`                                                    |
| Spain         | `FOCUS_FILTER_SPR_CULTURE`                                              |
| Transnistria  | `FOCUS_FILTER_TRANSNISTRIA_*` (9 filters)                               |
| South Ossetia | `FOCUS_FILTER_OSSETIA_*` (7 filters)                                    |
| Ural          | `FOCUS_FILTER_URAL_*` (3 filters)                                       |

## Common mistakes

- A custom filter with no generic.
- `FOCUS_FILTER_MILITARY`. It is an unused legacy name. Use
  `FOCUS_FILTER_MILITARY_LAWS`.
- `FOCUS_FILTER_DIPLOMACY` for all foreign policy. General relations are
  `FOCUS_FILTER_FOREIGN_POLICY`.
- A treasury-spending focus without `FOCUS_FILTER_EXPENDITURE` and the guard.
- More than two generic filters. Do not over-tag.
