# Namelist Reference

Quick reference for creating division, ship hull, and ship class design name files.

Full authoring guide: `docs/src/content/resources/unit-name-lists.md`

---

## Division Names (`common/units/names_divisions/TAG_names_divisions.txt`)

### Seven mandatory groups

| Token                  | division_types                                               | Link            |
| ---------------------- | ------------------------------------------------------------ | --------------- |
| `TAG_INF_DIV`          | `L_Inf_Bat Mot_Inf_Bat Mech_Inf_Bat Arm_Inf_Bat`             | ↔ `TAG_INF_BDE` |
| `TAG_INF_BDE`          | same as above                                                | ↔ `TAG_INF_DIV` |
| `TAG_ARM_BDE`          | `armor_Bat`                                                  | —               |
| `TAG_SOF`              | `Special_Forces`                                             | —               |
| `TAG_AIR_CAV_BRIGADES` | `L_Air_assault_Bat L_Air_Inf_Bat Mot_Air_Inf_Bat`            | —               |
| `TAG_MAR`              | `L_Marine_Bat Mot_Marine_Bat Mech_Marine_Bat Arm_Marine_Bat` | —               |
| `TAG_MIL`              | `Militia_Bat Mot_Militia_Bat`                                | —               |

### Minimal template

```
TAG_INF_DIV = {
	name = "Infantry Divisions"
	for_countries = { TAG }
	division_types = { "L_Inf_Bat" "Mot_Inf_Bat" "Mech_Inf_Bat" "Arm_Inf_Bat" }
	link_numbering_with = { "TAG_INF_BDE" }
	fallback_name = "%d Infantry Division"
	ordered = {
		1 = { "1st Infantry Division" }
	}
}
```

- `%d` = Arabic numeral, `%s` = Roman numeral in fallback_name
- **Never add empty `can_use = { }`** — performance cost; omit it entirely if unused
- Landlocked nations: use riverine/lake names for `TAG_MAR` (e.g. `"Bataillon du Lac Tanganyika"`, `"River Force Battalion"`)
- Encoding: UTF-8 no BOM. Latin diacritics (é à š č ž) work. No Arabic/Greek/Cyrillic/CJK.

---

## Ship Hull Names (`common/units/names_ships/TAG_ship_names.txt`)

Individual ship names drawn when hulls are built.

```
TAG_FRIGATE_HISTORICAL = {
	name = NAME_THEME_HISTORICAL_FRIGATE
	for_countries = { TAG }
	type = ship
	ship_types = { stealth_frigate frigate }
	prefix = "HMS "
	fallback_name = "Frigate (F-%d)"
	unique = {
		"Name One" "Name Two"
	}
}
```

### Ship type tokens (canonical — match `common/units/MD_naval_units.txt`)

Valid: `carrier` `helicopter_operator` `destroyer` `stealth_destroyer` `frigate` `stealth_frigate` `corvette` `stealth_corvette` `cruiser` `battle_cruiser` `battleship` `attack_submarine` `diesel_attack_submarine` `missile_submarine`

**Dead vanilla tokens that silently never match** (these were removed when MD restructured naval units — never use them):

`submarine` `light_cruiser` `heavy_cruiser` `ship_hull_carrier` `ship_hull_cruiser` `ship_hull_heavy` `ship_hull_light` `ship_hull_submarine` `battleship_hull_0` `LHA`

**`LHA` is the sprite of `helicopter_operator`, not a sub_unit.** Class-designer blocks (`names/00_TAG_names.txt`) and `ship_types` lists (`names_ships/`) must use `helicopter_operator` — an `LHA = { ... }` block compiles silently and never fires.

There are still 17 legacy `names_ships/TAG_ship_names.txt` files and 129 legacy `names/00_TAG_names.txt` files in the repo that reference these dead tokens — their `unique` lists never get used. When you touch a tag's namelists, check for these and migrate the strings into the modern equivalents (`submarine` → `attack_submarine`/`missile_submarine`/`diesel_attack_submarine`; `light_cruiser`/`heavy_cruiser` → `cruiser`; `LHA` → `helicopter_operator`).

### Verified naval prefixes

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

If no documented official prefix exists, use `prefix = ""`.

---

## Ship Class & Land Unit Design Names (`common/units/names/00_TAG_names.txt`)

Names shown in the designer for new class designs (naval and land).

```
TAG = {
	destroyer = {
		prefix = ""
		generic = { "Destroyer" }
		unique = { "Class One" "Class Two" }
	}
	L_Inf_Bat = {
		prefix = ""
		generic = { "Infantry Division" }
		generic_pattern = "UNIT_GENERIC_NAME_GENERIC_INFANTRY"
		unique = { }
	}
}
```

- Keys inside `TAG = { }` must be **real sub_unit names** — for ships, from `common/units/MD_naval_units.txt`; for land, from `common/units/MD_land_units.txt`. A key that does not correspond to a real MD sub_unit compiles silently and never fires. Use `helicopter_operator`, not `LHA` (LHA is the sprite name only).
- **Do not use `infantry`.** That was vanilla's sub_unit name; MD renamed it. The canonical MD land sub_units are `L_Inf_Bat`, `Mot_Inf_Bat`, `Mech_Inf_Bat`, `Arm_Inf_Bat`, `Militia_Bat`, `armor_Bat`, etc. (see `MD_land_units.txt`).
- **Minimum land fallback is `L_Inf_Bat = { ... }`** — the light infantry battalion. Include it (even with empty `unique = { }`) so the country gets a flavoured generic label instead of the unbranded numbered fallback. Localize the `generic` label to the country's language (e.g. `"Infanterie-Division"` for GER, `"Strelkovaya Diviziya"` for SOV).
- Class names follow national naming traditions (dynasty names for China subs, island names for Turkey corvettes, weapon names for India corvettes, etc.)
- Encoding: UTF-8 no BOM; same script constraints as division files

---

## Air Wing Names (inside `common/units/names/00_TAG_names.txt`)

Air wing labels come from two layers:

1. **`air_wing_names_template = AIR_WING_NAME_TAG_FALLBACK`** — set once at the top of the `TAG = { }` block. This is the master fallback that the engine uses when generating numbered wing names ("3rd Squadron", "Geschwader 14", etc.).
2. **Per-archetype `*_airframe` blocks** — one per aircraft sub-unit type, each pointing at a `generic_pattern` loc key for that country.

**Both layers depend on matching loc keys.** Define them in `localisation/english/replace/replaced_from_unit_names_l_english.yml`:

```yaml
AIR_WING_NAME_TAG_FALLBACK: "$NUMBER$ Squadron"
AIR_WING_NAME_TAG_GENERIC: "$NR$ $NAME$"
AIR_WING_NAME_TAG_CARRIER: "$NR$ Carrier Wing $NAME$" # only if you use _CARRIER on cv_* archetypes
```

If you set `air_wing_names_template = AIR_WING_NAME_FOO_FALLBACK` but no matching loc key exists, HOI4 renders the literal token in-game. **Known dead refs** (currently bugged): `AST`, `FIN`, `JAP`, `USA`, `GER`.

**Coverage:** 36 of 86 country files declare `air_wing_names_template`; the rest fall through to the vanilla `AIR_WING_NAME_GENERIC` family.

### 27 archetypes (must match `common/units/MD_air_units.txt`)

| Land                                                                                                                                                                                                   | Carrier (`cv_`)                                                                                                                                                                                                        |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `small_plane_airframe`, `small_plane_strike_airframe`, `small_plane_naval_bomber_airframe`, `small_plane_cas_airframe`, `small_plane_suicide_airframe`                                                 | `cv_small_plane_airframe`, `cv_small_plane_strike_airframe`, `cv_small_plane_naval_bomber_airframe`, `cv_small_plane_cas_airframe`, `cv_small_plane_suicide_airframe`                                                  |
| `medium_plane_airframe`, `medium_plane_fighter_airframe`, `medium_plane_cas_airframe`, `medium_plane_maritime_patrol_airframe`, `medium_plane_air_transport_airframe`, `medium_plane_suicide_airframe` | `cv_medium_plane_airframe`, `cv_medium_plane_fighter_airframe`, `cv_medium_plane_cas_airframe`, `cv_medium_plane_maritime_patrol_airframe`, `cv_medium_plane_air_transport_airframe`, `cv_medium_plane_scout_airframe` |
| `large_plane_airframe`, `large_plane_air_transport_airframe`, `large_plane_awacs_airframe`, `large_plane_cas_airframe`, `large_plane_maritime_patrol_airframe`                                         | —                                                                                                                                                                                                                      |

**USA's namelist contains a typo**: `small_plane_sucide_airframe` (missing the `i`). The correct token is `small_plane_suicide_airframe` — copy from `common/units/MD_air_units.txt`, never from `00_USA_names.txt`.

### Minimum scaffold per archetype

```
small_plane_airframe = {
	prefix = ""
	generic = { "Fighter Squadron" }       # in country language
	generic_pattern = AIR_WING_NAME_TAG_GENERIC
	unique = { }
}
```

Leaving `unique = { }` empty is acceptable on every archetype. The block must still exist so the country gets the flavoured generic pattern instead of the vanilla numbered fallback.

---

## Checklist for a New Tag

- [ ] `common/units/names_divisions/TAG_names_divisions.txt` — all 7 groups
- [ ] `common/units/names_ships/TAG_ship_names.txt` — frigate + corvette minimum (skip for landlocked)
- [ ] `common/units/names/00_TAG_names.txt` — relevant hull types (naval sub_units from `MD_naval_units.txt`) + `L_Inf_Bat` block (minimum land fallback; use the MD sub_unit, **never** vanilla's `infantry`) + `air_wing_names_template` + all 27 airframe blocks.
- [ ] `localisation/english/replace/replaced_from_unit_names_l_english.yml` — `AIR_WING_NAME_TAG_FALLBACK` + `_GENERIC` keys (+ `_CARRIER` if used)
- [ ] `history/units/TAG_*.oob` — `division_names_group` set on every template
