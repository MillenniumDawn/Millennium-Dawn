# AI Focuses

These files tell the AI which technology categories to research for each AI focus.
Weights run from 1 to 10. Leave out any category that would be 0 or 1.

`descriptor.mod` replaces this directory, so vanilla `ai_focuses` files never load.

## How the engine uses them

Every AI country holds a value for each focus, usually 0 to 100. When the AI scores
techs, it multiplies that value by the weights below and adds the result to the
"need" for each matching category. `NDefines.NAI.RESEARCH_NEEDS_FACTOR` in
`common/defines/MD_defines.lua` then scales need into the tech score.

- A missing category adds nothing. Do not write `= 0`.
- Weights add up. A tech in two weighted categories gets both.
- A negative weight pushes the AI away from a category. Only `CAT_air_drones = -4`
  in the generic and RAJ aviation blocks does this today.
- To make AI focuses matter more or less overall, change `RESEARCH_NEEDS_FACTOR`,
  not every weight.

## Scale

| Weight | Meaning                           |
| ------ | --------------------------------- |
| 10     | Top priority for this focus       |
| 6-8    | Strong pull                       |
| 3-5    | Steady interest                   |
| 2      | Light nudge                       |
| 1      | Too small to matter. Leave it out |

Use whole numbers. Compare weights across blocks too, since a 4 in `ai_focus_peaceful`
competes with a 4 in `ai_focus_war_production` whenever both focuses are active.

## Files

- `MD_generic.txt`: every country without its own file.
- `MD_SOV.txt`, `MD_USA.txt`, `MD_RAJ.txt`: country overrides.

A block named `ai_focus_<focus>_<TAG>` replaces the generic block for that country.
Copy every line you still want. `ai_focus_naval_air_USA` is empty on purpose so the
USA does not pick up the generic medium aircraft weight.

## Focus values

The engine sets these before the weights apply. `ai_focus_<x>_factor` modifiers
(for example `ai_focus_naval_factor = 0.5`) scale the result afterward.

| Focus                   | Default value                                                     | Modifier                                |
| ----------------------- | ----------------------------------------------------------------- | --------------------------------------- |
| `defense`               | 50 at peace, 100 in a defensive war, 0 in an offensive war        | `ai_focus_defense_factor`               |
| `aggressive`            | 50 at peace (75 fascist), 0 in a defensive war, 100 in offensive  | `ai_focus_aggressive_factor`            |
| `war_production`        | 10 at peace (30 fascist), 100 at war                              | `ai_focus_war_production_factor`        |
| `military_advancements` | 25 per research slot (max 100)                                    | `ai_focus_military_advancements_factor` |
| `peaceful`              | 100 at peace, 0 at war                                            | `ai_focus_peaceful_factor`              |
| `naval`                 | Dockyards plus convoy and import use, max 100. -999 with no docks | `ai_focus_naval_factor`                 |
| `naval_air`             | 20 per carrier (max 100). -999 with no carriers                   | `ai_focus_naval_air_factor`             |
| `aviation`              | 10 per airport (max 100). -999 with no airports                   | `ai_focus_aviation_factor`              |
| `military_equipment`    | 75 at peace, 100 at war                                           | `ai_focus_military_equipment_factor`    |

`naval`, `naval_air`, `aviation` and `military_advancements` drop by 25% at peace.
