# OOB and Equipment Variants Reference

For OOB files in `history/units/` and equipment variants in `history/countries/`.

## Files

| Pattern                  | DLC gate       | Content      | Type system                    |
| ------------------------ | -------------- | ------------ | ------------------------------ |
| `TAG_YEAR_nsb.txt`       | No Step Back   | Ground units | Chassis type + `variant_name`  |
| `TAG_YEAR_nonnsb.txt`    | Fallback       | Ground units | Legacy id, no `variant_name`   |
| `TAG_YEAR_bba.txt`       | By Blood Alone | Air units    | Airframe type + `variant_name` |
| `TAG_YEAR_nonbba.txt`    | Fallback       | Air units    | Legacy id, no `variant_name`   |
| `TAG_YEAR_naval_mtg.txt` | Man the Guns   | Fleets       | Hull type + `version_name`     |

Never mix the two systems in one file. `variant_name` has no effect in a fallback file.

The country history file picks the OOBs with `set_oob`, `set_naval_oob`, and
`set_air_oob`. Variants are defined there too, inside the `2000.1.1` block, under
`has_dlc = "No Step Back"` or `has_dlc = "By Blood Alone"` with fallback content in `else`.

## Land equipment

Source: `common/units/equipment/MD_x_tank_chassis.txt`. MD repurposes the vanilla
chassis names for modern roles.

| Role                 | NSB chassis                           | Legacy id                    |
| -------------------- | ------------------------------------- | ---------------------------- |
| MBT                  | `medium_tank_chassis_N`               | `MBT_{N+1}`                  |
| APC                  | `medium_tank_amphibious_chassis_N`    | `APC_{N+1}`                  |
| IFV                  | `medium_tank_flame_chassis_N`         | `IFV_{N+1}`                  |
| Recon or light tank  | `medium_tank_destroyer_chassis_N`     | `Rec_tank_N`                 |
| SP artillery         | `medium_tank_artillery_chassis_N`     | `SP_arty_N`                  |
| Rocket artillery     | `medium_tank_rocket_chassis_N`        | `SP_R_arty_N`                |
| SP anti-air          | `medium_tank_aa_chassis_N`            | `SP_Anti_Air_N`              |
| Towed artillery      | `artillery_N`                         | `artillery_N`                |
| Attack helicopter    | `heavy_tank_chassis_{N+1}`            | `attack_helicopter_{N+1}`    |
| Transport helicopter | `heavy_tank_amphibious_chassis_{N+1}` | `transport_helicopter_{N+1}` |

- Helicopters are land equipment on the heavy tank chassis.
- `_0` is 1965, and each step is about ten years. The MBT line skips an id at the top:
  `medium_tank_chassis_4` is `MBT_5` (2015), `_5` is `MBT_7` (2025), `_6` is `MBT_8` (2035).
- Tiers: MBT, APC, and IFV have 8. Recon has 6. SP artillery, rockets, and anti-air have 5.

```
create_equipment_variant = {
    name = "T-64B"
    type = medium_tank_chassis_1
    parent_version = 0
    modules = {
        main_armament_slot = tank_medium_cannon_2
        ammunition_load_slot = mixed_main_ammo_2
        turret_type_slot = tank_soviet_turret
        suspension_type_slot = tank_torsion_bar_suspension_medium
        armor_type_slot = tank_composite_armor_gen2
        engine_type_slot = tank_diesel_engine_gen2
        reload_type_slot = automatic_loading
        special_type_slot_1 = smoke_launchers
    }
    upgrades = { tank_nsb_armor_upgrade = 2 }
    obsolete = yes
    icon = "GFX_TAG_LAND_image"
    model = "entity_name"
}
```

`icon` takes a `GFX_` sprite, never a raw `.dds` path. Raw-path plane icons crash the air
battle window on macOS. Register the sprite in the matching `interface/*_profiles.gfx`
file: `tank`, `afv`, `spart`, `helicopter`, `ship`, `infantry`, `utility_vehicle`, or
`plane`. Name it after the texture path under `gfx/interface/technologies/`: drop the
extension, write `+` as `plus`, and turn every other symbol into an underscore, as in
`GFX_SOV_AIR_MiG_21Bis`. The designer pools in
`gfx/interface/equipmentdesigner/graphic_db/` use the same sprite names.

## Aircraft

Source: `common/units/equipment/MD_x_plane_airframes.txt`. Base archetypes are
`small_plane_airframe`, `medium_plane_airframe`, `large_plane_airframe`, and the `cv_`
small and medium carrier versions. A sub-type derives from the archetype in its prefix.

| Airframe                                | Role                     | HOI4 type         |
| --------------------------------------- | ------------------------ | ----------------- |
| `small_plane_cas_airframe`              | Small CAS                | `cas`             |
| `small_plane_strike_airframe`           | Light multirole, trainer | `tactical_bomber` |
| `small_plane_naval_bomber_airframe`     | Small naval bomber       | `naval_bomber`    |
| `small_plane_suicide_airframe`          | UAV                      | `suicide`         |
| `medium_plane_fighter_airframe`         | Air superiority fighter  | `fighter`         |
| `medium_plane_cas_airframe`             | Medium CAS               | `cas`             |
| `medium_plane_suicide_airframe`         | Loitering munition       | `suicide`         |
| `medium_plane_maritime_patrol_airframe` | Medium maritime patrol   | `naval_bomber`    |
| `medium_plane_air_transport_airframe`   | Medium transport         | `suicide`         |
| `large_plane_maritime_patrol_airframe`  | Large maritime patrol    | `naval_bomber`    |
| `large_plane_awacs_airframe`            | AWACS                    | `scout_plane`     |
| `large_plane_cas_airframe`              | Gunship                  | `cas`             |
| `large_plane_air_transport_airframe`    | Large transport          | `suicide`         |

- Transports use HOI4 type `suicide` on purpose. Do not change it.
- Multirole and strike fighters use the base `medium_plane_airframe` directly.
- Carrier sub-types mirror these with a `cv_` prefix, plus
  `cv_medium_plane_scout_airframe` for carrier AWACS.
- Legacy ids: `L_Strike_fighter1-5`, `Air_UAV1-4`, `AS_Fighter1-7`, `MR_Fighter1-7`,
  `Strike_fighter1-7`, `cas1-5`, `kamikaze_drone_1-4`, `naval_plane1-6`,
  `awacs_equipment_1-2`, `transport_plane1-6`, and the `CV_` and `cv_` carrier forms.

| Suffix     | Tech      | Year |
| ---------- | --------- | ---- |
| `_0`, `_1` | `gen_3_*` | 1960 |
| `_2`       | `gen_4_*` | 1980 |
| `_3`       | `gen_5_*` | 2015 |
| `_4`       | `gen_6_*` | 2025 |
| `_5`       | `gen_7_*` | 2035 |

The suffix must match a technology the country holds. A variant of an unlocked type
exists but cannot be produced or stockpiled.

```
create_equipment_variant = {
    name = "An-26"
    type = large_plane_air_transport_airframe_1
    parent_version = 1
    modules = {
        fixed_main_weapon_slot = weap_buff_transport
        engine_type_slot = engine_prop_double_1
        avionics_type_slot = avionics_manned_1
        wingform_type_slot = wing_straight
    }
    obsolete = yes
    icon = "GFX_TAG_AIR_image"
}
```

Air wings in the BBA OOB. The state id is the deployment location:

```
696 = {
    small_plane_airframe_2 = { owner = "UKR" creator = "SOV" amount = 50 version_name = "MiG-29 Fulcrum" }
    name = "8-yi Vynyshchuvalnyi Aviatsiynyi Polk"
    start_experience_factor = 0.4
}
```

## Ships

Source: `common/units/equipment/MD_mtg_ships.txt`.

| Hull                         | Type           | Tiers |
| ---------------------------- | -------------- | ----- |
| `corvette_hull_N`            | `screen_ship`  | 1-6   |
| `stealth_corvette_hull_N`    | `screen_ship`  | 1-3   |
| `frigate_hull_N`             | `screen_ship`  | 1-6   |
| `stealth_frigate_hull_N`     | `screen_ship`  | 1-3   |
| `destroyer_hull_N`           | `screen_ship`  | 1-5   |
| `stealth_destroyer_hull_N`   | `capital_ship` | 1-3   |
| `cruiser_hull_N`             | `capital_ship` | 1-5   |
| `battle_cruiser_hull_N`      | `capital_ship` | 1-4   |
| `battleship_hull_N`          | `capital_ship` | 0-4   |
| `helicopter_operator_hull_N` | `carrier`      | 1-4   |
| `carrier_hull_N`             | `carrier`      | 1-5   |
| `attack_submarine_hull_N`    | `submarine`    | 1-6   |
| `missile_submarine_hull_N`   | `submarine`    | 1-6   |

- OOB `definition` values: `corvette`, `frigate`, `destroyer`, `cruiser`,
  `battle_cruiser`, `battleship`, `helicopter_operator`, `carrier`, `submarine`.
- Hulls have no combat stats of their own. Everything comes from modules. Armor is
  zeroed, and CIWS modules provide missile defense.
- `heavy_frigate` is an archetype only. `battleship_hull_0` is the battleship archetype.

```
ship = { name = "Hetman Sahaydachnyi" definition = frigate start_experience_factor = 0.50 equipment = { frigate_hull_1 = { amount = 1 owner = UKR creator = UKR version_name = "Krivak III Class" } } }
```

In-progress builds:

```
instant_effect = {
    add_equipment_production = {
        equipment = { type = corvette_hull_2 creator = "UKR" version_name = "Grisha V Class" }
        requested_factories = 1
        progress = 0.80
        efficiency = 30
        amount = 1
    }
}
```

## Stockpiles

```
add_equipment_to_stockpile = {
    type = medium_tank_chassis_1
    variant_name = "T-64B"
    amount = 500
    producer = UKR
}
```

In a fallback file the same entry is `type = MBT_2` with no `variant_name`.

## Rules that fail silently

- `variant_name` and `version_name` must match the variant's `name` exactly, and `type`
  must match the variant's `type`. A hull mismatch logs
  `does not have any equipment variant for type X version 0`. Other mismatches drop the
  equipment with no error.
- The variant must be defined in the history file of its `creator` or `producer`.
  Countries with inherited Soviet equipment use `SOV`.
- The country needs the technology for the chassis, airframe, and every module. An event
  or focus that introduces an advanced variant must also grant the tech.
- The first variant of a type has `parent_version = 0`. Later ones chain from an
  existing parent.
- Air wings need matching `add_equipment_to_stockpile` entries, uncommented.
- Events that add aircraft need both a BBA branch with `variant_name` and an `else`
  with the legacy type.
- Set `obsolete = yes` on older variants so the AI does not build them.
- An `equipment_bonus` in an idea targets one chassis archetype. An MBT bonus does not
  cover APCs or IFVs. List each archetype.

## Module technology

`validate_history.py` maps each module to its enabling tech and reports a
`create_equipment_variant` using a module the country's `set_technology` does not grant.
It also checks each tech's prerequisites and is DLC-aware.

- Naval and base-game techs go in the plain `set_technology` block.
- No Step Back and By Blood Alone techs go in a `set_technology` under the matching
  `has_dlc` check.
- Grant the prerequisites too.

Alaska (ASK), the Confederate States (CSA), the Great Lakes Confederation (GLC), and New
England (NEN) inherit technology from the United States at spawn. Their history files
still carry a `set_technology` block matching their variants. Keep it in sync, since
inheritance does not satisfy the static check.

## Slot rules

A design can only use slots its hull defines, and each slot only accepts modules from
its `allowed_module_categories`. Break either rule and the engine drops the module at
load with no error. A dropped `fixed_ship_engine_slot` leaves the ship with no engine.

Slots live per archetype in `common/units/equipment/`. A hull either inherits them
(`module_slots = inherit`) or replaces the block, so check the hull the variant names.

- An absent `allowed_module_categories` is unconstrained. An empty one permits nothing
  on its own, and the slot is filled by what the equipped modules unlock. Most tank and
  helicopter slots work this way.
- Modules widen each other's slots. `tank_small_medium_cannon_2` lets `main_gun_ammo`
  into `ammunition_load_slot`. Drop the module and everything it unlocked stops fitting.
- `duplicate_archetypes` clones whole families. `medium_tank_destroyer_chassis_2` exists
  in game with the slots of `medium_tank_chassis_2` but appears in no equipment file.
- Tank and plane slot names (`turret_type_slot`, `engine_type_slot`) are ignored on a
  ship hull.
- Corvettes have one aux slot, `fixed_ship_auxillary_slot`. Frigates have `_1` to `_3`.
  Helicopter operators have `_2` and `_3` but no `_1`.

`validate_oob_units.py` checks every `create_equipment_variant` against its hull, and
`validate_ai_equipment.py` does the same for AI `target_variant` designs.
