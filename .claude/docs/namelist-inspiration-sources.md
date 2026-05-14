# Namelist Inspiration Sources

External resources used as **inspiration** when authoring division, ship, and class designer namelists in `common/units/`. Direct copy-paste is not done; these references inform native-language unit naming, plausible unit types per country, and historical formation flavor.

## Steam Workshop: "Better Mechanics : Namelists"

- **Workshop ID**: `3413087807`
- **Local path** (when subscribed via Steam): `~/.local/share/Steam/steamapps/workshop/content/394360/3413087807/`
- **Format**: Vanilla HOI4 — uses tokens like `infantry`, `mechanized`, `paratrooper`, `marine`, `mountaineers`, `militia`. **Not directly compatible with MD**, which uses `L_Inf_Bat`, `Mot_Inf_Bat`, `Mech_Inf_Bat`, `Arm_Inf_Bat`, `armor_Bat`, `Special_Forces`, `Militia_Bat`, etc.
- **What we draw from it**:
  - Native-language unit-type vocabulary per country (e.g., Swiss "Festungsdivision", Belarusian "Krepasnaja Dyvizija", Croatian "Pješačka Brigada", Maltese AFM regiment naming).
  - Categorical unit type variety beyond the MD 7-group standard — Fortress, Coastal Defense, Border Guard, Mountain, Volunteer, Reserve, Grenadier, Assault. These map to optional **schema-extension groups** in MD files (see below).
- **What we DO NOT do**: copy the `ordered` blocks (mostly single-entry fallback duplications anyway), copy file headers, or use vanilla division-type tokens.

Countries covered by the workshop mod that have been integrated into MD namelists in this repo (non-exhaustive): BLR, CAT, CRO, ICE, IRE, LUX, MLT, SWI, plus broader European/major coverage that informed the major-powers batch.

## MD's mandatory 7-group standard (recap)

Files in `common/units/names_divisions/` must use these tokens for the core 7 groups. Schema-extension groups (below) are **optional additions**, not replacements.

| Mandatory group            | division_types                                                                  |
| -------------------------- | ------------------------------------------------------------------------------- |
| `TAG_ARMY_DIVISIONS`       | `L_Inf_Bat Mot_Inf_Bat Mech_Inf_Bat Arm_Inf_Bat` (link with ARMOURED_DIVISIONS) |
| `TAG_ARMY_BRIGADES`        | same as ARMY_DIVISIONS                                                          |
| `TAG_ARMOURED_DIVISIONS`   | `armor_Bat` (link with ARMY_DIVISIONS)                                          |
| `TAG_AIR_CAV_BRIGADES`     | `L_Air_assault_Bat L_Air_Inf_Bat Mot_Air_Inf_Bat`                               |
| `TAG_MAR_BRIGADES`         | `L_Marine_Bat Mot_Marine_Bat Mech_Marine_Bat Arm_Marine_Bat`                    |
| `TAG_SPEC_FORCES_BRIGADES` | `Special_Forces`                                                                |
| `TAG_MIL_BRIGADES`         | `Militia_Bat Mot_Militia_Bat`                                                   |

## Schema-extension groups (optional, drawn from workshop categorical variety)

These add flavor where a country plausibly fields a distinctive sub-type beyond the 7 standard. They reuse the same MD `division_types` tokens — the differentiation is **naming flavor only**, not new gameplay categories.

| Optional group                 | division_types                          | Fits                                                                                     |
| ------------------------------ | --------------------------------------- | ---------------------------------------------------------------------------------------- |
| `TAG_MOUNTAIN_BRIGADES`        | `Special_Forces L_Inf_Bat Mot_Inf_Bat`  | Alpine/highland nations (SWI, CAT Pyrenees, SCL Alps, CRE White Mountains, CRO Dinarics) |
| `TAG_FORTRESS_DIVISIONS`       | `L_Inf_Bat Mech_Inf_Bat`                | Static-defense traditions (SWI Réduit, MLT Knights legacy)                               |
| `TAG_BORDER_GUARD_BRIGADES`    | `L_Inf_Bat Mot_Inf_Bat`                 | Landlocked or contested-border (SWI Grenzschutz, CRO border)                             |
| `TAG_GARRISON_BRIGADES`        | `L_Inf_Bat Militia_Bat Mot_Militia_Bat` | Islands and static defense (MLT, NCY, CRE)                                               |
| `TAG_COASTAL_DEFENSE_BRIGADES` | `L_Inf_Bat Mot_Inf_Bat`                 | Coastal/island states with coast-guard role (ICE)                                        |

Add these only when they make sense for the country. Never replace one of the 7 mandatory groups with an extension group.

## Crediting in files

Single-line comment at the top of files that drew from the workshop mod:

```
# Inspired by workshop mod "Better Mechanics : Namelists" (3413087807); MD format / no copy-paste.
```

Apply only to files where the workshop genuinely informed the content. Files where we authored entirely from independent research (CRE, NCY, SCL, and all of batch 1 from before the mod was downloaded) do **not** get this header.
