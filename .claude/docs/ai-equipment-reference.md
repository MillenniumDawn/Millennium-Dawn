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

| Role                        | Equipment Type         | Used By                                                  |
| --------------------------- | ---------------------- | -------------------------------------------------------- |
| `land_modern_tank`          | MBT chassis            | `armor_Bat`                                              |
| `land_modern_apc`           | APC chassis            | `Mech_Inf_Bat`, `Mech_Air_Inf_Bat`                       |
| `land_modern_ifv`           | IFV chassis            | `Arm_Inf_Bat`                                            |
| `land_modern_artillery`     | SP artillery chassis   | `SP_Arty_Bat`, `SP_Arty_Battery`                         |
| `land_medium_tank_anti_air` | SP AA chassis          | `SP_AA_Bat`, `SP_AA_Battery`                             |
| `land_attack_helicopter`    | Attack helo chassis    | `attack_helo_bat`                                        |
| `land_assault_helicopter`   | Transport/assault helo | `L_Air_assault_Bat`, `helicopter_combat_service_support` |
| `land_modern_mlrs`          | MLRS chassis           | MLRS variants                                            |
| `land_modern_light_tank`    | Light tank chassis     | Light tank variants                                      |

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

## CV Plane ai_type System

Carrier-variant (CV) plane airframes must have `ai_type` set to one of 5 engine-recognized CV types. Any other `ai_type` (including land types like `heavy_fighter`) silently excludes the plane from carrier production — the engine treats it as a land plane.

Valid CV `ai_type` values:

| ai_type           | unit_ratio ID     | What it covers                                           |
| ----------------- | ----------------- | -------------------------------------------------------- |
| `cv_fighter`      | `cv_fighter`      | MR fighters, AWACS/scouts (no dedicated cv_scout exists) |
| `cv_interceptor`  | `cv_interceptor`  | AS fighters                                              |
| `cv_cas`          | `cv_cas`          | CAS variants                                             |
| `cv_naval_bomber` | `cv_naval_bomber` | Naval bombers, maritime patrol                           |
| `cv_suicide`      | `cv_suicide`      | Drones, transports (no dedicated cv_transport exists)    |

When creating CV plane sub-archetypes, always set `ai_type` explicitly — do not rely on inheriting from the parent archetype, as the parent may use a generic type.

## Equipment Role Chain

Three systems must align for AI equipment production to work:

```
Equipment design role (ai_equipment/) → Airframe ai_type (units/equipment/) → AI strategy unit_ratio (ai_strategy/)
```

1. **Equipment design `roles = { X }`** — tells AI which design template to use
2. **Airframe `ai_type = Y`** — tells engine which production bucket the airframe belongs to
3. **AI strategy `unit_ratio id = Y`** — tells AI what proportion of production to allocate

If any link is missing, the AI either can't build the equipment or doesn't know it should.

## Naval Goals Structure

Naval goal files (`common/ai_navy/goals/`) must define a **complete set of all objective types** per nation. Vanilla blocks custom nations from generic goals and gives each a full replacement set. Partial overrides cause duplicate goals (both generic and custom apply simultaneously).

**Required objective types per nation** (11 total):
`naval_invasion_support`, `naval_invasion_defense`, `coast_defense`, `convoy_protection`, `convoy_raiding`, `naval_dominance`, `naval_blockade`, `mines_sweeping`, `mines_planting`, `training`, `strike_force_objective`

When adding a new nation's goals file:

1. Define all 11 objective types with `available_for = { TAG }`
2. Add the TAG to `blocked_for` on every generic goal entry in `goals_generic.txt`
3. Customize min/max_priority to match the nation's naval doctrine

## Screen Destroyer Role

MD splits destroyers into two sub_units: `destroyer` (capital_ship) and `screen_destroyer` (screen_ship). Both use the same equipment (`need_equipment = { destroyer = 1 }`), following vanilla's light_cruiser/heavy_cruiser pattern.

For nations that need distinct ASW-focused screen destroyers (e.g., USA), add a `naval_screen_destroyer` role with ASW-optimized designs (sonar, torpedoes, ASW missiles). Add corresponding `role_ratio` in the AI strategy file.

## Taskforce Composition Limits

NAI defines in `common/defines/MD_defines.lua` cap how many ships the AI puts per category in a single taskforce. The `optimal_composition` in fleet templates is silently capped by these:

| Define                                | Value | Category     | Ship Types                                                                          |
| ------------------------------------- | ----- | ------------ | ----------------------------------------------------------------------------------- |
| `CARRIER_TASKFORCE_MAX_CARRIER_COUNT` | 2     | carrier      | carrier, helicopter_operator                                                        |
| `CAPITAL_TASKFORCE_MAX_CAPITAL_COUNT` | 6     | capital_ship | battleship, battle_cruiser, cruiser, stealth_destroyer, destroyer, heavy_frigate    |
| `SCREEN_TASKFORCE_MAX_SHIP_COUNT`     | 8     | screen_ship  | screen_destroyer, stealth_frigate, frigate, corvette, stealth_corvette, patrol_boat |
| `SUB_TASKFORCE_MAX_SHIP_COUNT`        | 8     | submarine    | missile_submarine, attack_submarine                                                 |

**If an optimal_composition exceeds these caps, the excess ships are silently ignored.** The `validate_ai_navy` pre-commit hook catches violations.

Other relevant ratios:

- `CAPITALS_TO_CARRIER_RATIO = 2` — AI wants 2 capitals per carrier
- `SCREENS_TO_CAPITAL_RATIO = 3` — AI wants 3 screens per capital
- `MIN_CAPITALS_FOR_CARRIER_TASKFORCE = 2` — need 2 capitals to form carrier TF

### Fleet Sizing for Large Navies

Nations with many ships (100+) need sufficient fleet/taskforce slots to absorb them:

- Increase `optional_taskforces` counts in fleet templates
- Add more fleet template varieties (patrol, escort, submarine, corvette fleets)
- The AI creates **multiple instances** of each fleet template if ships are available
- Keep taskforce sizes within define caps; create more taskforces rather than larger ones

### NOT Block AND Trap in Priority Blocks

`NOT = { tag = A tag = B }` means NOT(A AND B) — always true since a country can only be one tag. This is a common copy-paste error in priority blocks:

```pdx
# WRONG — always evaluates true, modifier never applies
modifier = {
    factor = 0
    NOT = {
        tag = USA
        tag = ENG
    }
}

# CORRECT — zeroes priority for any nation not in the list
modifier = {
    factor = 0
    NOT = {
        OR = {
            tag = USA
            tag = ENG
        }
    }
}
```

## Common Mistakes

| Mistake                                                  | Impact                                                    | Fix                                                |
| -------------------------------------------------------- | --------------------------------------------------------- | -------------------------------------------------- |
| Wrong module in slot (e.g., armor in `reload_type_slot`) | AI fails to build valid variant                           | Check module matches slot type                     |
| Duplicate role template names across files               | Second silently overwrites first                          | Use unique names per template                      |
| `roles = { medium_as_fighter }` on CAS designs           | AI deploys CAS as air superiority                         | Use `medium_cas_fighter` for CAS                   |
| Factory threshold `< 15` on small nations                | Nation can never produce                                  | Use date checks or lower thresholds                |
| Missing top-level `priority` on role template            | Undefined AI priority behavior                            | Always include `priority = { factor = N }`         |
| `available_for` overlap between templates for same role  | AI gets competing designs                                 | Verify intent; remove overlap if not wanted        |
| Missing `allowed_modules`                                | AI won't pick any modules beyond `target_variant.modules` | Add if AI should use extra modules                 |
| CV plane `ai_type = heavy_fighter` (land type)           | Plane excluded from carrier production entirely           | Use one of 5 valid CV ai_types (see above)         |
| `equipment_variant_production_factor = -95` on base type | Subtypes inherit penalty even with positive overrides     | Keep base type penalty mild (-25 max)              |
| Nation excluded from generic but no custom role coverage | AI cannot produce that equipment type at all              | Run `validate_ai_equipment.py`                     |
| Partial naval goals (only overriding a few types)        | Duplicate goals — both generic and custom apply           | Define complete set of all 11 objective types      |
| Nation blocked from generic air with no custom strategy  | Zero interceptor/bomber/drone production                  | Verify every excluded nation has full air doctrine |
| `NOT = { tag=A tag=B }` in priority block                | Modifier never fires (AND trap)                           | Use `NOT = { OR = { tag=A tag=B } }`               |
| `factor = 0` for nation + nation not in `blocked_for`    | Nation uses template but with zero priority               | Either block the nation or remove factor=0         |
| Duplicate design names within a role template            | Second silently overwrites first — design is lost         | Use unique names (e.g., `_improved`, `_next`)      |
| Optimal composition exceeds NAI define caps              | Engine silently caps ships; excess wasted                 | Run `validate_ai_navy.py`, respect define limits   |
| `AP_` prefix on design names (copy-paste from JAP)       | No functional impact but confuses debugging               | Use correct tag prefix                             |
