# Namelist Reference

Full authoring guide: `docs/src/content/resources/unit-name-lists.md`. All files are
UTF-8 without BOM. Latin diacritics work. Arabic, Greek, Cyrillic, and CJK do not.

## Division names (`common/units/names_divisions/TAG_names_divisions.txt`)

Seven mandatory groups. `division_types` must match `common/units/MD_land_units.txt`.

| Token                  | division_types                                               |
| ---------------------- | ------------------------------------------------------------ |
| `TAG_INF_DIV`          | `L_Inf_Bat Mot_Inf_Bat Mech_Inf_Bat Arm_Inf_Bat`             |
| `TAG_INF_BDE`          | same                                                         |
| `TAG_ARM_BDE`          | `armor_Bat`                                                  |
| `TAG_SOF`              | `Special_Forces`                                             |
| `TAG_AIR_CAV_BRIGADES` | `L_Air_assault_Bat L_Air_Inf_Bat Mot_Air_Inf_Bat`            |
| `TAG_MAR`              | `L_Marine_Bat Mot_Marine_Bat Mech_Marine_Bat Arm_Marine_Bat` |
| `TAG_MIL`              | `Militia_Bat Mot_Militia_Bat`                                |

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

- `TAG_INF_DIV` and `TAG_INF_BDE` link numbering with each other. No other group links.
- In `fallback_name`, `%d` is an Arabic numeral and `%s` a Roman one.
- Never add an empty `can_use = { }`. It costs performance.
- Landlocked nations use river or lake names for `TAG_MAR`.

## Ship names (`common/units/names_ships/TAG_ship_names.txt`)

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

- Valid `ship_types`, from `common/units/MD_naval_units.txt`: `carrier`,
  `helicopter_operator`, `destroyer`, `stealth_destroyer`, `screen_destroyer`,
  `frigate`, `stealth_frigate`, `heavy_frigate`, `corvette`, `stealth_corvette`,
  `patrol_boat`, `cruiser`, `battle_cruiser`, `battleship`, `attack_submarine`,
  `missile_submarine`.
- Dead vanilla tokens that never match: `submarine`, `light_cruiser`, `heavy_cruiser`,
  `ship_hull_carrier`, `ship_hull_cruiser`, `ship_hull_heavy`, `ship_hull_light`,
  `ship_hull_submarine`, `battleship_hull_0`, `LHA`. When you touch a tag's namelists,
  migrate their strings: `submarine` to `attack_submarine` or `missile_submarine`, the
  cruisers to `cruiser`, `LHA` to `helicopter_operator`.
- Use the navy's official prefix (`USS `, `HMS `, `INS `). With none documented, use
  `prefix = ""`.

## Design names (`common/units/names/00_TAG_names.txt`)

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

- Keys must be real MD sub-unit names from `MD_naval_units.txt` and `MD_land_units.txt`.
  Any other key compiles silently and never fires. `LHA` is a sprite name, and
  `infantry` is vanilla's sub-unit. Use `helicopter_operator` and `L_Inf_Bat`.
- Always include an `L_Inf_Bat` block, even with an empty `unique`, so the country gets
  a flavored generic label. Write the `generic` label in the country's language.
- Class names follow national naming traditions.

## Air wing names (same file)

Two layers, both backed by loc keys in
`localisation/english/replace/replaced_from_unit_names_l_english.yml`:

1. `air_wing_names_template = AIR_WING_NAME_TAG_FALLBACK`, set once at the top of the
   `TAG = { }` block.
2. One `*_airframe` block per aircraft sub-unit, each with a `generic_pattern`.

```yaml
AIR_WING_NAME_TAG_FALLBACK: "$NUMBER$ Squadron"
AIR_WING_NAME_TAG_GENERIC: "$NR$ $NAME$"
AIR_WING_NAME_TAG_CARRIER: "$NR$ Carrier Wing $NAME$" # only for cv_ archetypes
```

```
small_plane_airframe = {
	prefix = ""
	generic = { "Fighter Squadron" }
	generic_pattern = AIR_WING_NAME_TAG_GENERIC
	unique = { }
}
```

- A template with no matching loc key renders the literal token in game.
- Archetype names must match `common/units/MD_air_units.txt`. Copy them from there, not
  from another country's namelist. There are 27: the 17 land airframes plus the `cv_`
  small and medium carrier forms.
- An empty `unique = { }` is fine on every archetype. The block must still exist.

## Checklist for a new tag

- [ ] `names_divisions/TAG_names_divisions.txt`: all 7 groups.
- [ ] `names_ships/TAG_ship_names.txt`: frigate and corvette at minimum. Skip if
      landlocked.
- [ ] `names/00_TAG_names.txt`: relevant hulls, `L_Inf_Bat`, `air_wing_names_template`,
      and every airframe block.
- [ ] `AIR_WING_NAME_TAG_FALLBACK` and `_GENERIC` loc keys.
- [ ] `division_names_group` set on every template in `history/units/TAG_YEAR*.txt`.
