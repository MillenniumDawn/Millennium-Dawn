---
name: new-namelist
description: 'Scaffold division name lists, ship hull names, ship class design names, and air wing name blocks for a country. Use when asked to create namelists or unit/ship/squadron names for a TAG, e.g. "/new-namelist GHA".'
---

Scaffold division name lists, ship hull name lists, and ship class design names for a country in Millennium Dawn.

**Syntax:** `/new-namelist <TAG>`

The authoritative guide is `docs/src/content/resources/unit-name-lists.md`. Read it before starting. For exact syntax, follow the templates and canonical tables in `.claude/docs/namelist-reference.md` (division groups, ship type tokens, naval prefixes, air wing archetypes) — it is the single source of truth, not restated here.

## Execution

### 1. Gather country data

Read for TAG:

- OOB file(s): `history/units/TAG_*.txt` — starting division templates and ship entries
- History file: `history/countries/TAG*.txt` — name, region, official language
- State files: `history/states/*.txt` — does the country own coastal states (landlocked check)

Determine:

- **Language** for unit names: French (Francophone), Spanish (Latin America), Portuguese (Lusophone), English (Anglophone), or native Latin-script spelling (Slavic/Balkan/other)
- **Coastal or landlocked** — affects `TAG_MAR` group and whether a ship hull file is warranted
- **Naval strength** — count starting ships in the OOB. Minimal/zero ships still needs a minimal ship file (frigate + corvette minimum)

Check whether these already exist (avoid overwriting):

- `common/units/names_divisions/TAG_names_divisions.txt`
- `common/units/names_ships/TAG_ship_names.txt`
- `common/units/names/00_TAG_names.txt`

If any exist, warn before overwriting and offer to append instead.

### 2. Create the division name list

Write `common/units/names_divisions/TAG_names_divisions.txt`. All seven groups are mandatory. Aim for 6–10 `ordered` entries per group for major countries; 3–6 acceptable for small nations. Research real formation names where available.

### 3. Create the ship hull name list

Write `common/units/names_ships/TAG_ship_names.txt`. Minimum groups: frigate and corvette; add destroyer, submarine, carrier, or others the country fields in the OOB. For unlisted naval prefixes, research the official one (Wikipedia "Naval ensign of X", "List of X Navy ships") or use `""` if none is documented.

Add thematic names beyond real ship names: geographic features, historical battles, national heroes, rivers, islands. Aim for 8–15 unique names per group.

For **landlocked nations**, omit the ship hull file — they cannot operate ships.

### 4. Create the ship class design names and airwing fallback structure

Write or append `common/units/names/00_TAG_names.txt`. This file holds three things:

1. **Ship class design names** — shown in the naval designer when creating a new ship class. Keys must match real naval sub_units from `common/units/MD_naval_units.txt`.
2. **Land unit design names** — minimum is an `L_Inf_Bat` block (light infantry battalion). Keys must match real land sub_units from `common/units/MD_land_units.txt`. Never use `infantry = { }` — vanilla's sub_unit was renamed.
3. **Air wing fallback names** — used when generating squadron labels for the country's aircraft. Without these blocks the country falls through to the engine's generic numbered name and looks unfinished.

Class naming traditions by region/country:

- **China:** Dynasty names (Song, Yuan, Han, Ming) for subs; province/city names for surface combatants
- **Turkey:** Ottoman battle names for carriers; Turkish islands for corvettes; historical figures for destroyers/frigates
- **India:** Sanskrit weapon names (Khukri, Khanjar) for corvettes; rivers/mountains for frigates and destroyers
- **Korea:** Commander names (Yi Sun-sin pattern) for destroyers; Korean islands for carriers/LHDs
- **Greece:** Ancient heroes for subs; Aegean island names for frigates; mythological names for corvettes
- **General:** National heroes, geographic features, rivers, battles, historical ships of the same class

For **landlocked nations**, omit all ship class blocks and include only the `L_Inf_Bat` block + the airwing blocks below.

### 4a. Air wing archetype blocks (do not skip)

In `00_TAG_names.txt`, after the ship class blocks, add one block per aircraft archetype the country can field. **Even when the country has no curated squadron names, the blocks must exist with empty `unique = { }` lists** — otherwise air wings get an unbranded generic label and players see the country as half-finished.

Where to source real squadron names: official air force / navy aviation orders of battle on Wikipedia ("List of {Country} Air Force squadrons"); national defence ministry publications. Aim for 8–15 `unique` entries on the principal fighter / strike / CAS archetypes for major nations; empty `unique = { }` is acceptable on every other archetype.

Common pitfalls to avoid:

- **Missing archetypes** — leaving out an archetype block does not error in-game; it silently falls back to a numbered generic. Reviewers won't catch it. Always include all 27.
- **`generic_pattern` mismatches** — each archetype's `generic_pattern` must point at an existing loc key. Convention: `AIR_WING_NAME_TAG_GENERIC` for land archetypes, `AIR_WING_NAME_TAG_CARRIER` for `cv_*` ones (if defined). If you don't have a `_CARRIER` loc key, point carrier archetypes at `AIR_WING_NAME_TAG_GENERIC` too — never invent a key without backing loc.

### 5. Update OOB templates (if OOB exists)

In `history/units/TAG_*.txt`, add `division_names_group = TAG_INF_BDE` (or the relevant group token) inside each `division_template` block.

For each starting `division = { }` unit, add:

```
division_name = { is_name_ordered = yes name_order = 1 }
```

Increment `name_order` for each unit that should draw from the same name group. `name_order` does not need to match an `ordered` key — the game falls back to `fallback_name` if the key is absent.

Only update the OOB if it already has templates defined. If the OOB is minimal or templates are set up generically, note it for the user to do manually.

### 6. Report output

Summarise:

- Files created or modified
- Division groups written (list all 7 tokens)
- Ship hull groups written (list name keys used)
- Ship class types covered
- Air wing archetypes covered (should be all 27 — flag missing ones)
- `air_wing_names_template` line added
- Whether the OOB was updated
- Any names that need research (flag as "placeholder — verify")
- Whether portraits or other assets are still needed
