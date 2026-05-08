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

### 4. Create the ship class design names

Write or append `common/units/names/00_TAG_names.txt`.

These names appear in the naval designer when the player creates a new ship design class. Include all hull types the country can plausibly build.

**The `infantry` block is always required**, even for pure naval nations:

```
TAG = {
	destroyer = {
		prefix = ""
		generic = { "Destroyer" }
		unique = {
			"Class Name One" "Class Name Two"
		}
	}
	infantry = {
		prefix = ""
		generic = { "Infantry Division" }
		generic_pattern = "UNIT_GENERIC_NAME_GENERIC_INFANTRY"
		unique = { }
	}
}
```

Class naming traditions by region/country:

- **China:** Dynasty names (Song, Yuan, Han, Ming) for subs; province/city names for surface combatants
- **Turkey:** Ottoman battle names for carriers; Turkish islands for corvettes; historical figures for destroyers/frigates
- **India:** Sanskrit weapon names (Khukri, Khanjar) for corvettes; rivers/mountains for frigates and destroyers
- **Korea:** Commander names (Yi Sun-sin pattern) for destroyers; Korean islands for carriers/LHDs
- **Greece:** Ancient heroes for subs; Aegean island names for frigates; mythological names for corvettes
- **General:** National heroes, geographic features, rivers, battles, historical ships of the same class

For **landlocked nations**, include only the `infantry` block.

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
- Whether the OOB was updated
- Any names that need research (flag as "placeholder — verify")
- Whether portraits or other assets are still needed
