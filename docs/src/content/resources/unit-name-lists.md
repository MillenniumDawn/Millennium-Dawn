---
title: Unit Name Lists Guidelines
description: Guidelines for creating unit name lists for Millennium Dawn
---

Name lists define what new trained units, ships, and air wings will be called during the game. They are required for all new content and add significant flavour while being relatively low-effort to complete.

**Core rule:** List names (the group label the player sees) must be in English. The individual unit names within a list should be in the native language of the country.

---

## Division Name Lists

**File path:** `common/units/names_divisions/TAG_names_divisions.txt`

Each country gets its own file. Name lists shared across countries can go in a common file.

### Required groups

Every country must cover all front-line unit types. The seven standard groups are:

| Group token            | `division_types` values                                      | Notes                             |
| ---------------------- | ------------------------------------------------------------ | --------------------------------- |
| `TAG_INF_DIV`          | `L_Inf_Bat Mot_Inf_Bat Mech_Inf_Bat Arm_Inf_Bat`             | Link with `TAG_INF_BDE`           |
| `TAG_INF_BDE`          | same as above                                                | Brigades; link with `TAG_INF_DIV` |
| `TAG_ARM_BDE`          | `armor_Bat`                                                  | Armoured formations               |
| `TAG_SOF`              | `Special_Forces`                                             | Special forces / commando         |
| `TAG_AIR_CAV_BRIGADES` | `L_Air_assault_Bat L_Air_Inf_Bat Mot_Air_Inf_Bat`            | Air assault / airborne            |
| `TAG_MAR`              | `L_Marine_Bat Mot_Marine_Bat Mech_Marine_Bat Arm_Marine_Bat` | Marine / naval infantry           |
| `TAG_MIL`              | `Militia_Bat Mot_Militia_Bat`                                | Militia / paramilitary            |

### Mandatory fields

```
TAG_INF_DIV = {
    name = "Infantry Divisions"           # English label shown in the template designer
    for_countries = { TAG }
    division_types = { "L_Inf_Bat" "Mot_Inf_Bat" "Mech_Inf_Bat" "Arm_Inf_Bat" }
    link_numbering_with = { "TAG_INF_BDE" }
    fallback_name = "%d Infantry Division"

    ordered = {
        1 = { "1st Infantry Division" }
        2 = { "2nd Infantry Division" }
    }
}
```

- **`name`** — English string describing the theme (e.g. `"Infantry Divisions"`, `"Armoured Brigades"`).
- **`for_countries`** — one or more country tags.
- **`division_types`** — controls which template type the AI assigns this list to. Only front-line types belong here (infantry, armour, air cavalry, marines, militia, special forces). Do not include support battalions.
- **`link_numbering_with`** — prevents two groups from issuing the same ordinal simultaneously. Link `INF_DIV` ↔ `INF_BDE` so you never have both a "3rd Infantry Division" and a "3rd Infantry Brigade" at the same time.
- **`fallback_name`** — used once all `ordered` names are exhausted. `%d` inserts an Arabic numeral; `%s` inserts a Roman numeral.
- **`ordered`** — named entries (optional but encouraged). Keys are integers assigned in order of unit creation. Gaps are allowed.

**Do not add an empty `can_use = { }` block.** An empty `can_use` has a real performance cost; omit the field entirely if you do not need a visibility condition.

### Language and naming conventions

- Use the country's official language for unit names (French for Francophone Africa, Spanish for Latin America, Portuguese for Lusophone nations, English for Anglophone nations, native Latin-script spelling for Slavic/Balkan countries).
- HOI4's font supports UTF-8 with standard Latin diacritics (é, à, ü, š, č, ž). **Do not use Arabic, Greek, Cyrillic, or CJK characters** — they will not render correctly.
- Name units after real-life formations where possible. For countries with less documented naming traditions, use the local linguistic pattern (e.g. French: "1ère Brigade d'Infanterie", Spanish: "1a Brigada de Infantería").
- Whether to use "division" or "brigade" depends on the size of the country's starting templates. Most small nations use brigade-sized formations.

### Landlocked nations — MAR substitution

Landlocked countries cannot build marine divisions in most playthroughs, but the `TAG_MAR` group must still be present (for AI assignment and modding flexibility). Use contextually appropriate riverine or lake forces instead of sea-based names:

| Context                    | Example name                                               |
| -------------------------- | ---------------------------------------------------------- |
| Major river                | `"1er Bataillon d'Infanterie Fluviale"`                    |
| Lake bordering the country | `"Lake Tanganyika Battalion"` / `"Bataillon du Lac Tchad"` |
| Generic substitute         | `"Riverine Defence Battalion"`                             |

### Assigning name lists to OOB units

After creating the file, assign lists to starting templates in `history/units/TAG_*.oob`:

```
division_template = {
    name = "1st Infantry Brigade"
    division_names_group = TAG_INF_BDE
    ...
}

units = {
    division = {
        name = "1st Infantry Brigade"
        division_name = { is_name_ordered = yes name_order = 1 }
        ...
    }
}
```

`name_order` does not need to correspond to an entry in the `ordered` block — if the key is missing the game uses `fallback_name` with that number.

---

## Ship Hull Name Lists

**File path:** `common/units/names_ships/TAG_ship_names.txt`

These names are drawn when individual ship hulls are constructed in the naval production queue. Each built ship gets one name from the pool.

### Structure

```
TAG_FRIGATE_HISTORICAL = {
    name = NAME_THEME_HISTORICAL_FRIGATE    # localisation key for the theme label

    for_countries = { TAG }

    type = ship
    ship_types = { stealth_frigate frigate }

    prefix = "HMS "                         # prepended to every name in the list
    fallback_name = "Frigate (F-%d)"        # used when unique names run out

    unique = {
        "Name One" "Name Two" "Name Three"
    }
}
```

### Ship type tokens

| Token                     | Description                       |
| ------------------------- | --------------------------------- |
| `carrier`                 | Aircraft carriers                 |
| `helicopter_operator`     | Helicopter carriers / LHDs        |
| `destroyer`               | Destroyers                        |
| `stealth_destroyer`       | Stealth destroyers                |
| `frigate`                 | Frigates                          |
| `stealth_frigate`         | Stealth frigates                  |
| `corvette`                | Corvettes                         |
| `stealth_corvette`        | Stealth corvettes                 |
| `cruiser`                 | Cruisers                          |
| `battle_cruiser`          | Battle cruisers                   |
| `battleship`              | Battleships                       |
| `submarine`               | Conventional submarines           |
| `attack_submarine`        | Nuclear attack submarines         |
| `diesel_attack_submarine` | Diesel-electric attack submarines |
| `missile_submarine`       | Ballistic missile submarines      |

Pair related types in one group (e.g. `stealth_frigate frigate`) so AI-built ships of either variant draw from the same name pool.

### Common `name` theme keys

| Key                                | Intended use                    |
| ---------------------------------- | ------------------------------- |
| `NAME_THEME_HISTORICAL_CARRIERS`   | Carrier hull names              |
| `NAME_THEME_HISTORICAL_FRIGATE`    | Frigate hull names              |
| `NAME_THEME_HISTORICAL_CORVETTE`   | Corvette hull names             |
| `NAME_THEME_HISTORICAL_SUBMARINES` | Submarine hull names            |
| `NAME_THEME_BATTLES`               | Historical battles/places theme |
| `NAME_THEME_CITIES`                | Cities theme                    |
| `NAME_THEME_LEADERS`               | Historical leaders theme        |

### Naval prefix conventions

Use each navy's documented ship prefix. Verified prefixes:

| Country     | Prefix    | Source                                                       |
| ----------- | --------- | ------------------------------------------------------------ |
| USA         | `"USS "`  | United States Ship                                           |
| GBR         | `"HMS "`  | His/Her Majesty's Ship                                       |
| FRA         | `"FS "`   | French Ship (NATO designation)                               |
| RUS         | no prefix | Hull numbers only                                            |
| CHI         | no prefix | Hull numbers                                                 |
| JAP         | `"JS "`   | Japan Ship                                                   |
| RAJ (India) | `"INS "`  | Indian Naval Ship                                            |
| KOR         | `"ROKS "` | Republic of Korea Ship                                       |
| CAN         | `"HMCS "` | His/Her Majesty's Canadian Ship                              |
| AUS         | `"HMAS "` | His/Her Majesty's Australian Ship                            |
| SIN         | `"RSS "`  | Republic of Singapore Ship                                   |
| TUN         | `"MNT "`  | Marine Nationale Tunisienne                                  |
| AZE         | `"ARG "`  | Azerbaijani Navy (Azerbaycan Respublikasinin Harbiye Gemisi) |
| GHA         | `"GNS "`  | Ghana Naval Ship                                             |
| TAN         | `"TNS "`  | Tanzania Naval Ship                                          |
| GEO         | `""`      | No standard prefix; hull numbers                             |
| SEN         | `""`      | No standard prefix                                           |
| ERI         | `""`      | No standard prefix                                           |

If a country has no documented official prefix, use an empty string `prefix = ""`.

### Content guidelines

- Real ships of the class (actual vessels in service) go in `unique`. Fictional or projected names go after real ones.
- For smaller navies with limited real names, add thematic names: geographic features, historical battles, national heroes.
- Avoid Arabic, Greek, Cyrillic, or CJK script in ship names.

---

## Ship Class / Design Names

**File path:** `common/units/names/00_TAG_names.txt`

These names appear in the naval designer when a player creates a new ship class design. Each entry represents the default class name for a design of that hull type.

### Structure

```
TAG = {
    destroyer = {
        prefix = "TAG "          # optional; shown before the class name
        generic = { "Destroyer" }
        unique = {
            "Class Name One" "Class Name Two"
        }
    }
    frigate = {
        prefix = ""
        generic = { "Frigate" }
        unique = {
            "Lekiu" "Kasturi"
        }
    }
    L_Inf_Bat = {
        prefix = ""
        generic = { "Infantry Division" }
        generic_pattern = "UNIT_GENERIC_NAME_GENERIC_INFANTRY"
        unique = { }
    }
}
```

Keys inside `TAG = { }` must match real sub_unit names from `common/units/MD_naval_units.txt` (for ships) or `common/units/MD_land_units.txt` (for land). A key that does not correspond to a real MD sub_unit compiles silently and never fires.

**Never use `infantry`.** That is vanilla's sub_unit name; MD restructured land units and the canonical land sub_units are `L_Inf_Bat`, `Mot_Inf_Bat`, `Mech_Inf_Bat`, `Arm_Inf_Bat`, `Militia_Bat`, `armor_Bat`, and so on (see `MD_land_units.txt`). Every `00_TAG_names.txt` should include at minimum an `L_Inf_Bat = { ... }` block as the light-infantry fallback — localize the `generic` label to the country's language where appropriate (e.g. `"Infanterie-Division"`, `"Strelkovaya Diviziya"`).

### Naming conventions

- Class names should reflect real-world naming traditions for that navy:
  - **China:** Dynasty names (Song, Yuan, Han, Ming) for subs; province/city names for carriers and surface combatants
  - **Turkey:** Historical Ottoman battles for carriers; Turkish islands for corvettes; historical figures for frigates/destroyers
  - **India:** Sanskrit/Hindi themed; weapon names (Khukri, Khanjar) for corvettes; river/mountain names for frigates
  - **Korea:** Yi Sun-sin class pattern for destroyers; Korean islands for LHDs; Korean commanders for frigates
  - **Greece:** Ancient Greek heroes and sea battles for subs; island names for frigates; mythological for corvettes
- `unique` names are exhausted in order and then `generic` is used with incrementing numbers.
- The prefix in `00_TAG_names.txt` is purely cosmetic and appears in the naval designer; it is separate from the hull prefix in `names_ships/`.

---

## Checklist for a Complete Namelist Package

For a new country tag, the following files are required:

- [ ] `common/units/names_divisions/TAG_names_divisions.txt` — all 7 division groups covered
- [ ] `common/units/names_ships/TAG_ship_names.txt` — frigate, corvette, and at least one additional type (submarine or destroyer where relevant)
- [ ] `common/units/names/00_TAG_names.txt` — ship class names for all relevant hull types (keys must match `MD_naval_units.txt`) + an `L_Inf_Bat` block as the minimum land fallback. Never use vanilla's `infantry` key — it does not match any MD sub_unit.
- [ ] OOB units in `history/units/TAG_*.oob` updated with `division_names_group` assignments

For questions, contact Kalkalash.
