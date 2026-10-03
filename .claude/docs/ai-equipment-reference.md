# AI Equipment Reference

`common/ai_equipment/*.txt` defines the variants the AI aims for when it designs tanks,
ships, and planes. Without coverage for a role, the AI does not produce that equipment.

## Role template

A top-level block in any file. The block name is its id, and a duplicate name silently
overwrites the first. The AI keeps one variant per role, from the highest-priority
template with that role.

```pdx
my_role_template = {
    category = land              # Required: land, naval, or air
    roles = { land_modern_tank } # Required: names used by role_ratio strategies
    available_for = { USA GER }  # Or blocked_for = { ... }
    priority = {                 # Required
        factor = 200
        modifier = {
            has_war = yes
            factor = 2
        }
    }

    # design blocks
}
```

## Design block

```pdx
my_design_name = {
    priority = {              # Required: importance within this template
        factor = 100
        modifier = {
            has_tech = mbt_tech_3
            factor = 0        # Stop when the next tech is available
        }
    }

    name = "My Tank"          # Optional preset name
    history = yes             # Optional: show in the designer's presets, per group
    role_icon_index = 2       # Optional, naval only
    enable = { ... }          # Optional

    target_variant = {        # Required
        match_value = 1000    # Required
        type = medium_tank_chassis_2  # Required
        modules = {
            main_armament_slot = tank_medium_cannon_2
            turret_type_slot = {
                any_of = {
                    tank_medium_three_man_turret
                    tank_medium_two_man_turret
                }
            }
            engine_type_slot = {
                module = tank_gasoline_engine
                upgrade = current        # Keep the same module when upgrading
            }
            armor_type_slot = > tank_welded_armor  # Newest at or above this
        }
        upgrades = {
            tank_nsb_engine_upgrade = 3
            tank_nsb_armor_upgrade = {
                base = 1
                modifier = { has_war = yes add = 2 }
            }
        }
    }

    requirements = { ... }    # Required modules not tied to a slot
    allowed_modules = {       # Extra modules the AI may pick, first is highest priority
        tank_smoke_launchers
        tank_radio
    }
    allowed_types = { ... }   # Sub-units the AI may add
}
```

- `slot = empty` leaves a slot empty. `slot = > empty` requires it filled.
- Without `allowed_modules` the AI picks nothing beyond `target_variant.modules`.
- Priority blocks use the weight syntax in `ai-strategy-reference.md`.

## Coverage

`generic_tank.txt`, `generic_plane.txt`, and `generic_naval.txt` are the fallback for any
nation without a custom file. They exclude covered nations with `blocked_for`.

- When you add a custom file for a tag, add the tag to `blocked_for` in the matching
  generic file.
- Every nation blocked from generic must have a custom or shared design for every role
  it needs. `validate_ai_equipment.py` checks this.
- Shared files: `NATO_tank.txt`, `SOV_tank.txt` (SOV and BLR), `CHI_tank.txt`,
  `USA_tank.txt`. Most nation files cover the MBT only.

| Role                        | Equipment                 | Used by                            |
| --------------------------- | ------------------------- | ---------------------------------- |
| `land_modern_tank`          | MBT chassis               | `armor_Bat`                        |
| `land_modern_apc`           | APC chassis               | `Mech_Inf_Bat`, `Mech_Air_Inf_Bat` |
| `land_modern_ifv`           | IFV chassis               | `Arm_Inf_Bat`                      |
| `land_modern_artillery`     | SP artillery chassis      | `SP_Arty_Bat`, `SP_Arty_Battery`   |
| `land_medium_tank_anti_air` | SP AA chassis             | `SP_AA_Bat`, `SP_AA_Battery`       |
| `land_attack_helicopter`    | Attack helicopter chassis | `attack_helo_bat`                  |
| `land_assault_helicopter`   | Transport helicopter      | `L_Air_assault_Bat`, helo support  |
| `land_modern_mlrs`          | MLRS chassis              | MLRS variants                      |
| `land_modern_light_tank`    | Light tank chassis        | Light tank variants                |

## Role chain

Three things must line up, or the AI cannot build the equipment or does not know it
should:

1. The design's `roles = { X }` in `common/ai_equipment/`.
2. The equipment's `ai_type = Y` in `common/units/equipment/`.
3. A `unit_ratio id = Y` or `role_ratio id = X` in `common/ai_strategy/`.

A carrier airframe must set `ai_type` to one of five carrier types. Any other value,
including a land type such as `heavy_fighter`, excludes it from carrier production. Set
it explicitly on every carrier sub-archetype.

| `ai_type`         | Covers                         |
| ----------------- | ------------------------------ |
| `cv_fighter`      | Multirole fighters, AWACS      |
| `cv_interceptor`  | Air superiority fighters       |
| `cv_cas`          | CAS                            |
| `cv_naval_bomber` | Naval bombers, maritime patrol |
| `cv_suicide`      | Drones, transports             |

## Naval

- Goal files in `common/ai_navy/goals/` must define all 11 objective types per nation:
  `naval_invasion_support`, `naval_invasion_defense`, `coast_defense`,
  `convoy_protection`, `convoy_raiding`, `naval_dominance`, `naval_blockade`,
  `mines_sweeping`, `mines_planting`, `training`, `strike_force_objective`. Add the tag
  to `blocked_for` on every entry in `goals_generic.txt`. A partial override leaves
  both the generic and the custom goal active.
- Destroyers are two sub-units on the same equipment: `destroyer` (capital ship) and
  `screen_destroyer` (screen ship). A nation that needs ASW screen destroyers adds a
  `naval_screen_destroyer` role and a matching `role_ratio`.
- The NAI defines in `common/defines/MD_defines.lua` cap ships per taskforce:
  `CARRIER_TASKFORCE_MAX_CARRIER_COUNT`, `CAPITAL_TASKFORCE_MAX_CAPITAL_COUNT`,
  `SCREEN_TASKFORCE_MAX_SHIP_COUNT`, and `SUB_TASKFORCE_MAX_SHIP_COUNT`. Ships in an
  `optimal_composition` beyond a cap are silently ignored. `validate_ai_navy.py` checks
  this. For a large navy, add more taskforces and fleet templates, not bigger ones.
- Categories: carrier (`carrier`, `helicopter_operator`), capital ship (`battleship`,
  `battle_cruiser`, `cruiser`, `stealth_destroyer`, `destroyer`, `heavy_frigate`),
  screen ship (`screen_destroyer`, `stealth_frigate`, `frigate`, `corvette`,
  `stealth_corvette`, `patrol_boat`), submarine (`missile_submarine`,
  `attack_submarine`).

## Common mistakes

- A module in the wrong slot. The AI cannot build a valid variant.
- Duplicate template names across files, or duplicate design names in one template.
- `roles = { medium_as_fighter }` on a CAS design. Use `medium_cas_fighter`.
- A factory threshold a small nation can never reach. Use date checks.
- Overlapping `available_for` between templates for the same role.
- `equipment_variant_production_factor = -95` on a base type. Subtypes inherit it even
  with positive overrides. Keep it at -25 or milder.
- A nation blocked from generic air with no custom air strategy.
- `NOT = { tag = A tag = B }` in a priority block. It is always true. Use
  `NOT = { OR = { ... } }`.
- `factor = 0` for a nation that is not in `blocked_for`. It uses the template at zero
  priority.
