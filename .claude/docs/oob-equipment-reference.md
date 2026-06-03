# OOB Equipment Quick Reference

Quick reference for equipment types in Order of Battle (OOB) files. For complete documentation, see `.claude/skills/oob-variants/SKILL.md`.

## File Type Quick Reference

| File Pattern   | DLC Required   | Equipment System     | Syntax                                                               |
| -------------- | -------------- | -------------------- | -------------------------------------------------------------------- |
| `*_nsb.txt`    | No Step Back   | Chassis types        | `type = medium_tank_chassis_1` + `variant_name = "T-72B"`            |
| `*_nonnsb.txt` | None           | Legacy equipment IDs | `type = MBT_2` (no variant_name)                                     |
| `*_bba.txt`    | By Blood Alone | Airframe types       | `type = medium_plane_fighter_airframe_2` + `variant_name = "MiG-29"` |
| `*_nonbba.txt` | None           | Legacy aircraft IDs  | `type = AS_Fighter2`                                                 |

**Critical Rule**: Never mix the two systems. NSB files use chassis types with `variant_name`; non-NSB files use legacy IDs without `variant_name`.

## Equipment Type Mapping

| Vehicle         | NSB Chassis                           | Non-NSB Legacy               |
| --------------- | ------------------------------------- | ---------------------------- |
| MBT             | `medium_tank_chassis_N`               | `MBT_{N+1}`                  |
| APC             | `medium_tank_amphibious_chassis_N`    | `APC_{N+1}`                  |
| IFV             | `medium_tank_flame_chassis_N`         | `IFV_{N+1}`                  |
| Recon           | `medium_tank_destroyer_chassis_N`     | `Rec_tank_N`                 |
| SP Artillery    | `medium_tank_artillery_chassis_N`     | `SP_arty_N`                  |
| SP Rocket Arty  | `medium_tank_rocket_chassis_N`        | `SP_R_arty_N`                |
| SP Anti-Air     | `medium_tank_aa_chassis_N`            | `SP_Anti_Air_N`              |
| Towed Artillery | `artillery_N`                         | `artillery_N`                |
| Attack Helo     | `heavy_tank_chassis_{N+1}`            | `attack_helicopter_{N+1}`    |
| Transport Helo  | `heavy_tank_amphibious_chassis_{N+1}` | `transport_helicopter_{N+1}` |

**Generation Mapping**: `_N` = generation starting at 0 for 1965, incrementing by ~10 years.

- `_0` / `_1` suffix = 1965 (Gen 1)
- `_1` / `_2` suffix = 1975 (Gen 2)
- `_2` / `_3` suffix = 1985 (Gen 3)
- etc.

## Common Errors

### Type System Mix-Up

| File Type | Wrong                          | Correct                                   |
| --------- | ------------------------------ | ----------------------------------------- |
| NSB       | `type = APC_2`                 | `type = medium_tank_amphibious_chassis_1` |
| NSB       | Missing `variant_name`         | Add `variant_name = "Exact Variant Name"` |
| Non-NSB   | `type = medium_tank_chassis_1` | `type = MBT_2`                            |
| Non-NSB   | Has `variant_name = "..."`     | Remove variant_name line entirely         |

### Chassis/Variant Mismatch

The `type` must match the chassis used in `create_equipment_variant`:

```
# In country history file:
create_equipment_variant = {
    name = "AVGP Grizzly"
    type = medium_tank_amphibious_chassis_1  # APC chassis
    ...
}

# In OOB file - WRONG:
type = medium_tank_flame_chassis_0  # IFV chassis doesn't match!
variant_name = "Grizzly AVGP"  # Name doesn't match either!

# In OOB file - CORRECT:
type = medium_tank_amphibious_chassis_1  # Same chassis as variant
variant_name = "AVGP Grizzly"  # Exact match to variant name
```

### Generation Mismatch

| Vehicle   | Era       | NSB Type                           | Non-NSB Type |
| --------- | --------- | ---------------------------------- | ------------ |
| Leopard 1 | 1970s     | `medium_tank_chassis_1`            | `MBT_2`      |
| Leopard 2 | 1980s     | `medium_tank_chassis_2`            | `MBT_3`      |
| T-55      | 1950s/60s | `medium_tank_chassis_0`            | `MBT_1`      |
| T-72A     | 1970s     | `medium_tank_chassis_1`            | `MBT_2`      |
| T-72B     | 1980s     | `medium_tank_chassis_2`            | `MBT_3`      |
| M113      | 1960s     | `medium_tank_amphibious_chassis_1` | `APC_2`      |
| BMP-1     | 1960s     | `medium_tank_flame_chassis_0`      | `IFV_1`      |
| BMP-2     | 1980s     | `medium_tank_flame_chassis_1`      | `IFV_2`      |

## Quick Diagnosis

```bash
# Find NSB files using legacy types (wrong)
grep -l "type = APC_\|type = MBT_\|type = IFV_\|type = Rec_tank_" history/units/*_nsb.txt

# Find non-NSB files using chassis types (wrong)
grep -l "medium_tank_chassis\|medium_tank_amphibious\|medium_tank_flame" history/units/*_nonnsb.txt

# Check variant exists for an NSB file
grep "variant_name" history/units/TAG_2000_nsb.txt
grep 'name = "VARIANT_NAME"' history/countries/TAG\ -\ Name.txt
```

## Complete Reference

For chassis types and roles, module configuration, aircraft airframes, naval hulls, complete equipment type mapping tables, and variant verification workflows, see `.claude/skills/oob-variants/SKILL.md`.
