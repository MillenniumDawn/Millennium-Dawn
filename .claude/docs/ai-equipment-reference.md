# AI Equipment Reference

## Overview

AI equipment files (`common/ai_equipment/*.txt`) define equipment variants that the AI should aim for when assigning modules to tank, ship, or plane variants. These control what the AI designs and produces — without proper coverage, AI nations will not produce equipment they need for their division templates.

## Role Template Structure

A role template is a top-level block in any file in the folder. The block name is the role template's unique ID — **duplicates silently overwrite**.

```pdx
my_role_template = {
    category = land              # REQUIRED: land, naval, or air
    roles = { land_modern_tank } # REQUIRED: role names for role_ratio AI strategy
    available_for = { USA GER }  # Restricts to listed tags (omit for all)
    blocked_for = { ... }        # Excludes listed tags (only if no available_for)

    priority = {                 # REQUIRED: MTTH block for template importance
        factor = 200             # vs other role templates for spending XP
        modifier = {
            has_war = yes
            factor = 2
        }
    }

    # Design blocks go here...
}
```

### Role Template Arguments

| Argument                        | Required     | Description                                                                                                         |
| ------------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------- |
| `category = <land\|naval\|air>` | Yes          | Whether template is for tanks, ships, or planes                                                                     |
| `roles = { ... }`               | Yes          | List of roles used by `role_ratio` AI strategy. AI tries to have one variant per role.                              |
| `available_for = { ... }`       | One of these | Restricts to listed country tags                                                                                    |
| `blocked_for = { ... }`         | One of these | Excludes listed country tags (only if no `available_for`)                                                           |
| `priority = { ... }`            | Yes          | MTTH block deciding importance vs other role templates. Highest priority among templates with same roles gets used. |

## Design Block Structure

Within role templates, each design is a block with a unique name.

```pdx
my_design_name = {
    priority = {              # REQUIRED: importance vs other designs in this template
        factor = 100
        modifier = {
            has_tech = mbt_tech_3
            factor = 0        # Stop building when next tech available
        }
    }

    name = "My Tank"          # Optional: preset name. Without it, uses TAG_type_N_short loc.
    history = yes             # Optional: marks as historical design
    role_icon_index = 2       # Optional: ship role icon (naval only)

    enable = { ... }          # Optional: trigger for when AI should aim for this design

    target_variant = {        # REQUIRED
        match_value = 1000    # REQUIRED: value to AI if matched
        type = medium_tank_chassis_2  # REQUIRED: specific equipment type

        modules = {           # Module slot assignments
            # Direct module assignment:
            main_armament_slot = tank_medium_cannon_2

            # any_of block (pick best available):
            turret_type_slot = {
                any_of = {
                    tank_medium_three_man_turret
                    tank_medium_two_man_turret
                }
            }

            # Module with upgrade requirement:
            engine_type_slot = {
                module = tank_gasoline_engine
                upgrade = current    # Keep same when upgrading (> = must upgrade)
            }

            # Using > or < for newer/older modules:
            armor_type_slot = > tank_welded_armor  # Aim for newest >= this
        }

        upgrades = {          # Optional: upgrade priorities
            tank_nsb_engine_upgrade = 3           # Fixed priority
            tank_nsb_armor_upgrade = {            # Dynamic MTTH priority
                base = 1
                modifier = { has_war = yes add = 2 }
            }
        }
    }

    requirements = { ... }    # Optional: required modules not tied to specific slots
                              # Same format as module slot assignments

    allowed_modules = {       # Optional: modules AI can pick after requirements met
        tank_smoke_launchers  # First listed = highest priority
        tank_radio
    }

    allowed_types = { ... }   # Optional: sub-units AI can add to design
                              # Omitted = AI never adds it
}
```

### Design Arguments

| Argument                            | Required | Description                                                           |
| ----------------------------------- | -------- | --------------------------------------------------------------------- |
| `priority = { ... }`                | Yes      | MTTH block for design importance within the role template             |
| `target_variant = { ... }`          | Yes      | The variant AI should aim for                                         |
| `target_variant.match_value`        | Yes      | How much the template is worth to AI if matched                       |
| `target_variant.type`               | Yes      | Specific equipment type (chassis) to use                              |
| `target_variant.modules = { ... }`  | Yes      | Module slot assignments                                               |
| `target_variant.upgrades = { ... }` | No       | Upgrade priorities                                                    |
| `name = "..."`                      | No       | Preset name for the equipment                                         |
| `history = yes`                     | No       | Marks as historical design                                            |
| `role_icon_index = N`               | No       | Ship role icon (naval only)                                           |
| `enable = { ... }`                  | No       | Trigger for when AI should use this design                            |
| `requirements = { ... }`            | No       | Required modules not tied to specific slots                           |
| `allowed_modules = { ... }`         | No       | Modules AI can pick beyond target_variant. Not listed = never picked. |
| `allowed_types = { ... }`           | No       | Sub-units AI can add. Omitted = never added.                          |

### Module Slot Assignment Formats

```pdx
# Direct module:
slot_name = module_name

# Direct with version comparison (> = newest, < = oldest):
slot_name = > module_name

# Empty slot:
slot_name = empty

# Ensure not empty:
slot_name = > empty

# any_of block:
slot_name = {
    any_of = {
        module_a
        module_b
    }
}

# With upgrade requirement:
slot_name = {
    module = module_name
    upgrade = current      # Keep same when upgrading
}
```

## Coverage Model

The generic files (`generic_tank.txt`, `generic_plane.txt`, `generic_naval.txt`) provide fallback designs for all nations. They use `blocked_for` to exclude ~27 named nations that have custom files.

**Every nation blocked from generic MUST have coverage in a custom or shared file for each role it needs.** Missing coverage = AI cannot produce that equipment type.

### Land Equipment Roles

| Role                                    | Equipment Type         | Used By                                                  |
| --------------------------------------- | ---------------------- | -------------------------------------------------------- |
| `land_modern_tank` / `land_medium_tank` | MBT chassis            | `armor_Bat`                                              |
| `land_modern_apc`                       | APC chassis            | `Mech_Inf_Bat`, `Mech_Air_Inf_Bat`                       |
| `land_modern_ifv`                       | IFV chassis            | `Arm_Inf_Bat`                                            |
| `land_modern_artillery`                 | SP artillery chassis   | `SP_Arty_Bat`, `SP_Arty_Battery`                         |
| `land_medium_tank_anti_air`             | SP AA chassis          | `SP_AA_Bat`, `SP_AA_Battery`                             |
| `land_attack_helicopter`                | Attack helo chassis    | `attack_helo_bat`                                        |
| `land_assault_helicopter`               | Transport/assault helo | `L_Air_assault_Bat`, `helicopter_combat_service_support` |
| `land_modern_mlrs`                      | MLRS chassis           | MLRS variants                                            |
| `land_modern_light_tank`                | Light tank chassis     | Light tank variants                                      |

### Coverage Files

| File                         | Covers                                                     | Nations                       |
| ---------------------------- | ---------------------------------------------------------- | ----------------------------- |
| `generic_tank.txt`           | All land roles                                             | All except 27 blocked nations |
| `NATO_tank.txt`              | MBT, APC, IFV, artillery, SP AA, attack helo, assault helo | NATO-aligned nations          |
| `SOV_tank.txt`               | MBT, APC, IFV, artillery, SP AA, attack helo, assault helo | SOV, BLR                      |
| `CHI_tank.txt`               | MBT, APC, IFV, artillery, SP AA, attack helo, assault helo | CHI                           |
| `USA_tank.txt`               | All land roles                                             | USA                           |
| Nation-specific `*_tank.txt` | Usually MBT only                                           | Individual nations            |

## MTTH Blocks (Priority Syntax)

Priority blocks use Mean Time To Happen (MTTH) syntax:

- Starts at assumed value of 1
- `base = N` sets value to N (like multiply by 0 then add N)
- `factor = N` multiplies current value by N
- `add = N` adds N to current value
- `modifier = { ... }` applies operations conditionally (trigger + value operations)

```pdx
priority = {
    factor = 200          # Start: 1 * 200 = 200
    modifier = {
        has_war = yes
        factor = 2        # If at war: 200 * 2 = 400
    }
    modifier = {
        num_of_factories < 15
        factor = 0        # If < 15 factories: kill priority entirely
    }
}
```

## Common Mistakes

| Mistake                                                  | Impact                                                    | Fix                                         |
| -------------------------------------------------------- | --------------------------------------------------------- | ------------------------------------------- |
| Wrong module in slot (e.g., armor in `reload_type_slot`) | AI fails to build valid variant                           | Check module matches slot type              |
| Duplicate role template names across files               | Second silently overwrites first                          | Use unique names per template               |
| `roles = { medium_as_fighter }` on CAS designs           | AI deploys CAS as air superiority                         | Use `medium_cas_fighter` for CAS            |
| Factory threshold `< 15` on small nations                | Nation can never produce                                  | Use date checks or lower thresholds         |
| Missing top-level `priority` on role template            | Undefined AI priority behavior                            | Always include `priority = { factor = N }`  |
| `available_for` overlap between templates for same role  | AI gets competing designs                                 | Verify intent; remove overlap if not wanted |
| Missing `allowed_modules`                                | AI won't pick any modules beyond `target_variant.modules` | Add if AI should use extra modules          |
