---
name: new-namelist
description: 'Scaffold division name lists, ship hull names, ship class design names, and air wing name blocks for a country. Use when asked to create namelists or unit/ship/squadron names for a TAG, e.g. "/new-namelist GHA".'
---

**Syntax:** `/new-namelist <TAG>`

Read `docs/src/content/resources/unit-name-lists.md` first. Templates, valid tokens, and
the new-tag checklist are in `.claude/docs/namelist-reference.md`. They are not repeated
here.

## 1. Gather country data

- `history/units/TAG_*.txt`: starting templates and ships.
- `history/countries/TAG*.txt`: name, region, language.
- `history/states/*.txt`: whether the country owns a coastal state.

Decide the language for unit names (French, Spanish, Portuguese, English, or native
Latin-script spelling), whether the country is landlocked, and how large its navy is.

If any of the three target files exist, warn before overwriting and offer to append.

## 2. Division names

Write `common/units/names_divisions/TAG_names_divisions.txt` with all seven groups. Aim
for 6 to 10 `ordered` entries per group for a major country and 3 to 6 for a small one.
Use real formation names where they exist.

## 3. Ship names

Write `common/units/names_ships/TAG_ship_names.txt`. Frigate and corvette are the
minimum. Add the other types the OOB fields. Aim for 8 to 15 names per group, mixing
real ship names with geographic features, battles, national heroes, rivers, and
islands. Landlocked nations get no ship file.

## 4. Design and air wing names

Write or append `common/units/names/00_TAG_names.txt`:

- Ship class names for the hull types the country uses. Follow the national tradition:
  dynasty names for Chinese submarines, islands for Turkish corvettes, Sanskrit weapon
  names for Indian corvettes, commanders for Korean destroyers, Aegean islands for Greek
  frigates.
- The `L_Inf_Bat` block.
- `air_wing_names_template` and a block for every air archetype, even with an empty
  `unique`. A missing block does not error. It silently falls back to a numbered
  generic. Add 8 to 15 real squadron names on the main fighter, strike, and CAS
  archetypes for a major nation.
- Each `generic_pattern` must point at an existing loc key. Without a `_CARRIER` key,
  point the `cv_` archetypes at `AIR_WING_NAME_TAG_GENERIC`.

Landlocked nations take only the `L_Inf_Bat` and air wing blocks.

## 5. OOB templates

If the OOB defines templates, add `division_names_group = TAG_<GROUP>` to each
`division_template`, and to each starting division:

```
division_name = { is_name_ordered = yes name_order = 1 }
```

Increment `name_order` per unit in the same group. It need not match an `ordered` key.
If the OOB is minimal or generic, leave it and say so.

## 6. Report

Files created or changed, the seven division groups, ship groups and class types
covered, air archetypes covered and any missing, whether the OOB was updated, and any
name that still needs verifying.
