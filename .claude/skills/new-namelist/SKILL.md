Scaffold division name lists, ship hull name lists, and ship class design names for a country in Millennium Dawn.

**Syntax:** `/new-namelist <TAG>`

The authoritative guide is `docs/src/content/resources/unit-name-lists.md`. Read it before starting. The quick reference is `.claude/docs/namelist-reference.md`.

---

## Execution

### 1. Gather country data

Read the following for TAG:

- OOB file(s): `history/units/TAG_*.oob` — identify starting division templates and ship entries
- History file: `history/countries/TAG*.txt` — identify the country's name, region, and official language
- State files: `history/states/*.txt` — check if the country owns any coastal states (to determine if it is landlocked)

Determine:

- **Language** for unit names: French (Francophone), Spanish (Latin America), Portuguese (Lusophone), English (Anglophone), or native Latin-script spelling (Slavic/Balkan/other)
- **Coastal or landlocked** — affects the `TAG_MAR` division group and whether a ship hull file is warranted
- **Naval strength** — number of starting ships in the OOB. Minimal or zero ships means a minimal ship file is still required (with frigate + corvette at minimum)

Check whether these files already exist to avoid overwriting:

- `common/units/names_divisions/TAG_names_divisions.txt`
- `common/units/names_ships/TAG_ship_names.txt`
- `common/units/names/00_TAG_names.txt`

If any exist, warn before overwriting and offer to append instead.

---

### 2. Create the division name list

Write `common/units/names_divisions/TAG_names_divisions.txt`.

All seven groups are mandatory:

| Token                  | division_types                                               | Link            |
| ---------------------- | ------------------------------------------------------------ | --------------- |
| `TAG_INF_DIV`          | `L_Inf_Bat Mot_Inf_Bat Mech_Inf_Bat Arm_Inf_Bat`             | ↔ `TAG_INF_BDE` |
| `TAG_INF_BDE`          | same as above                                                | ↔ `TAG_INF_DIV` |
| `TAG_ARM_BDE`          | `armor_Bat`                                                  | —               |
| `TAG_SOF`              | `Special_Forces`                                             | —               |
| `TAG_AIR_CAV_BRIGADES` | `L_Air_assault_Bat L_Air_Inf_Bat Mot_Air_Inf_Bat`            | —               |
| `TAG_MAR`              | `L_Marine_Bat Mot_Marine_Bat Mech_Marine_Bat Arm_Marine_Bat` | —               |
| `TAG_MIL`              | `Militia_Bat Mot_Militia_Bat`                                | —               |

Rules:

- Group `name` fields must be in English (the label the player sees in the template designer)
- Individual unit names in `ordered` must be in the country's official language
- `link_numbering_with` must link `TAG_INF_DIV` ↔ `TAG_INF_BDE` so their ordinals do not collide
- `%d` = Arabic numeral in `fallback_name`; `%s` = Roman numeral
- **Never add empty `can_use = { }` blocks** — omit the field entirely if not needed (performance cost)
- Encoding: UTF-8 without BOM; Latin diacritics (é à ü š č ž) are supported; no Arabic, Greek, Cyrillic, or CJK characters
- For **landlocked nations**, use riverine or lake forces for `TAG_MAR` instead of sea marines:
  - Major river nearby → `"1er Bataillon d'Infanterie Fluviale"` / `"River Force Battalion"`
  - Bordering lake → `"Lake [Name] Battalion"` / `"Bataillon du Lac [Name]"`

Aim for at least 6–10 `ordered` entries per group for major countries; 3–6 is acceptable for small nations. Research real formation names where available.

---

### 3. Create the ship hull name list

Write `common/units/names_ships/TAG_ship_names.txt`.

Minimum required groups: frigate (`stealth_frigate frigate`) and corvette (`stealth_corvette corvette`). Add destroyer, submarine, carrier, or others if the country fields them in the OOB.

Template:

```
TAG_FRIGATE_HISTORICAL = {
	name = NAME_THEME_HISTORICAL_FRIGATE
	for_countries = { TAG }
	type = ship
	ship_types = { stealth_frigate frigate }
	prefix = ""
	fallback_name = "Frigate (F-%d)"
	unique = {
		"Name One" "Name Two" "Name Three"
	}
}
```

Common `name` theme keys: `NAME_THEME_HISTORICAL_CARRIERS`, `NAME_THEME_HISTORICAL_FRIGATE`, `NAME_THEME_HISTORICAL_CORVETTE`, `NAME_THEME_HISTORICAL_SUBMARINES`, `NAME_THEME_BATTLES`, `NAME_THEME_CITIES`, `NAME_THEME_LEADERS`.

**Naval prefix lookup — use the documented prefix, or `""` if none is established:**

| Tag | Prefix |     | Tag | Prefix  |
| --- | ------ | --- | --- | ------- |
| USA | `USS ` |     | KOR | `ROKS ` |
| GBR | `HMS ` |     | CAN | `HMCS ` |
| FRA | `FS `  |     | AUS | `HMAS ` |
| JAP | `JS `  |     | SIN | `RSS `  |
| RAJ | `INS ` |     | GHA | `GNS `  |
| TUN | `MNT ` |     | TAN | `TNS `  |
| AZE | `ARG ` |     | GEO | `""`    |
| SEN | `""`   |     | ERI | `""`    |

For unlisted countries, research the official prefix (Wikipedia "Naval ensign of X", "List of X Navy ships"). If no standard prefix is documented, use `""`.

Add thematic names beyond real ship names: geographic features, historical battles, national heroes, rivers, islands. Aim for 8–15 unique names per group.

For **landlocked nations**, omit the ship hull file — they cannot operate ships.

---

### 4. Create the ship class design names and airwing fallback structure

Write or append `common/units/names/00_TAG_names.txt`. This file holds three things:

1. **Ship class design names** — what the player sees in the naval designer when creating a new ship class. Keys must match real naval sub_units from `common/units/MD_naval_units.txt`.
2. **Land unit design names** — minimum is an `L_Inf_Bat` block (light infantry battalion). Keys must match real land sub_units from `common/units/MD_land_units.txt`.
3. **Air wing fallback names** — what the game uses when generating squadron labels for the country's aircraft. Without these blocks the country falls through to the engine's generic numbered name and looks unfinished.

**Never use `infantry = { }`.** Vanilla's `infantry` sub_unit was renamed when MD restructured land units; the canonical MD land sub_units live in `common/units/MD_land_units.txt` as `L_Inf_Bat`, `Mot_Inf_Bat`, `Mech_Inf_Bat`, `Arm_Inf_Bat`, `Militia_Bat`, `armor_Bat`, and so on. A bare `infantry = { }` block compiles silently and never fires. Use `L_Inf_Bat` as the minimum land block — it is the MD light infantry battalion and the natural fallback.

Top-of-file scaffold:

```
TAG = {
	# Optional: fleet_names_template = FLEET_NAME_TAG   (only if you ALSO add a FLEET_NAME_TAG loc key)
	# Only set the line below if you ALSO add AIR_WING_NAME_TAG_FALLBACK + _GENERIC keys to
	# localisation/english/replace/replaced_from_unit_names_l_english.yml.
	air_wing_names_template = AIR_WING_NAME_TAG_FALLBACK

	destroyer = {
		prefix = ""
		generic = { "Destroyer" }
		unique = {
			"Class Name One" "Class Name Two"
		}
	}
	# ...other ship class blocks (keys must match common/units/MD_naval_units.txt)...

	L_Inf_Bat = {
		prefix = ""
		generic = { "Infantry Division" }       # localize to country language where appropriate
		generic_pattern = "UNIT_GENERIC_NAME_GENERIC_INFANTRY"
		unique = { }
	}

	# Air wing archetype blocks — see below
}
```

Class naming traditions by region/country:

- **China:** Dynasty names (Song, Yuan, Han, Ming) for subs; province/city names for surface combatants
- **Turkey:** Ottoman battle names for carriers; Turkish islands for corvettes; historical figures for destroyers/frigates
- **India:** Sanskrit weapon names (Khukri, Khanjar) for corvettes; rivers/mountains for frigates and destroyers
- **Korea:** Commander names (Yi Sun-sin pattern) for destroyers; Korean islands for carriers/LHDs
- **Greece:** Ancient heroes for subs; Aegean island names for frigates; mythological names for corvettes
- **General:** National heroes, geographic features, rivers, battles, historical ships of the same class

For **landlocked nations**, omit all ship class blocks and include only the `L_Inf_Bat` block + the airwing blocks below.

---

### 4a. Air wing archetype blocks (do not skip)

In `00_TAG_names.txt`, after the ship class blocks, add one block per aircraft archetype the country can field. **Even when the country has no curated squadron names, the blocks must exist with empty `unique = { }` lists** — otherwise air wings get an unbranded generic label and players see the country as half-finished.

The canonical list of 27 archetypes (mirrors `common/units/MD_air_units.txt`):

| Tier         | Land archetypes                                                                                                                                                                                        | Carrier archetypes (`cv_` prefix)                                                                                                                                                                                      |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Small plane  | `small_plane_airframe` (fighter), `small_plane_strike_airframe`, `small_plane_naval_bomber_airframe`, `small_plane_cas_airframe`, `small_plane_suicide_airframe`                                       | `cv_small_plane_airframe`, `cv_small_plane_strike_airframe`, `cv_small_plane_naval_bomber_airframe`, `cv_small_plane_cas_airframe`, `cv_small_plane_suicide_airframe`                                                  |
| Medium plane | `medium_plane_airframe`, `medium_plane_fighter_airframe`, `medium_plane_cas_airframe`, `medium_plane_maritime_patrol_airframe`, `medium_plane_air_transport_airframe`, `medium_plane_suicide_airframe` | `cv_medium_plane_airframe`, `cv_medium_plane_fighter_airframe`, `cv_medium_plane_cas_airframe`, `cv_medium_plane_maritime_patrol_airframe`, `cv_medium_plane_air_transport_airframe`, `cv_medium_plane_scout_airframe` |
| Large plane  | `large_plane_airframe`, `large_plane_air_transport_airframe`, `large_plane_awacs_airframe`, `large_plane_cas_airframe`, `large_plane_maritime_patrol_airframe`                                         | — (no carrier large planes)                                                                                                                                                                                            |

Minimum (fallback-only) block — everyone gets this even with no real squadron names. Use the country's language for the `generic` label:

```
small_plane_airframe = {
	prefix = ""
	generic = { "Fighter Squadron" }        # in country's language
	generic_pattern = AIR_WING_NAME_TAG_GENERIC
	unique = { }
}
```

Carrier blocks should use a `_CARRIER` pattern suffix:

```
cv_small_plane_airframe = {
	prefix = ""
	generic = { "Carrier Air Wing" }
	generic_pattern = AIR_WING_NAME_TAG_CARRIER
	unique = { }
}
```

Where to source real squadron names: official air force / navy aviation orders of battle on Wikipedia ("List of {Country} Air Force squadrons"); national defence ministry publications. Aim for 8–15 `unique` entries on the principal fighter / strike / CAS archetypes for major nations; empty `unique = { }` is acceptable on every other archetype.

Common pitfalls to avoid:

- **Typo `sucide` vs `suicide`** — vanilla USA's namelist contains the malformed token `small_plane_sucide_airframe`. The correct token everywhere is `small_plane_suicide_airframe` (matches the equipment archetype in `common/units/MD_air_units.txt`). Always copy from `MD_air_units.txt`, never from USA's namelist.
- **Missing archetypes** — leaving out an archetype block does not error in-game; it silently falls back to a numbered generic. Reviewers won't catch it. Always include all 27.
- **Dead template references** — `air_wing_names_template = AIR_WING_NAME_TAG_FALLBACK` only resolves if a matching loc key exists in `localisation/english/replace/replaced_from_unit_names_l_english.yml`. If the key is missing, HOI4 renders the literal token (e.g. `AIR_WING_NAME_TAG_FALLBACK`) as the wing name in-game. **You must add both keys** (`AIR_WING_NAME_TAG_FALLBACK` and `AIR_WING_NAME_TAG_GENERIC`) when you set the template. Known dead refs: AST, FIN, JAP, USA, GER — these will render the raw token until fixed.
- **`generic_pattern` mismatches** — each archetype's `generic_pattern` must point at a loc key that exists. The convention is `AIR_WING_NAME_TAG_GENERIC` for land archetypes and `AIR_WING_NAME_TAG_CARRIER` for `cv_*` ones (if you defined the latter). If you don't have a `_CARRIER` loc key, point carrier archetypes at `AIR_WING_NAME_TAG_GENERIC` too — never invent a key without backing loc.

---

### 5. Update OOB templates (if OOB exists)

In `history/units/TAG_*.oob`, add `division_names_group = TAG_INF_BDE` (or the relevant group token) inside each `division_template` block.

For each starting `division = { }` unit, add:

```
division_name = { is_name_ordered = yes name_order = 1 }
```

Increment `name_order` for each unit that should draw from the same name group. `name_order` does not need to match an `ordered` key — the game falls back to `fallback_name` if the key is absent.

Only update the OOB if it already has templates defined. If the OOB is minimal or the division templates are set up generically, note it for the user to do manually.

---

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
