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

### Ship type tokens

`carrier` `helicopter_operator` `destroyer` `stealth_destroyer` `frigate` `stealth_frigate` `corvette` `stealth_corvette` `cruiser` `battle_cruiser` `battleship` `submarine` `attack_submarine` `diesel_attack_submarine` `missile_submarine`

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

## Ship Class Design Names (`common/units/names/00_TAG_names.txt`)

Names shown in the naval designer for new class designs.

```
TAG = {
	destroyer = {
		prefix = ""
		generic = { "Destroyer" }
		unique = { "Class One" "Class Two" }
	}
	infantry = {
		prefix = ""
		generic = { "Infantry Division" }
		generic_pattern = "UNIT_GENERIC_NAME_GENERIC_INFANTRY"
		unique = { }
	}
}
```

- **`infantry` block is required** even for pure naval nations — engine always expects it
- Class names follow national naming traditions (dynasty names for China subs, island names for Turkey corvettes, weapon names for India corvettes, etc.)
- Encoding: UTF-8 no BOM; same script constraints as division files

---

## Checklist for a New Tag

- [ ] `common/units/names_divisions/TAG_names_divisions.txt` — all 7 groups
- [ ] `common/units/names_ships/TAG_ship_names.txt` — frigate + corvette minimum
- [ ] `common/units/names/00_TAG_names.txt` — relevant hull types + infantry block
- [ ] `history/units/TAG_*.oob` — `division_names_group` set on every template
