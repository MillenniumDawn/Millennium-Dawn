Reference guide for editing OOB (Order of Battle) files and equipment variants in Millennium Dawn.

This skill is not invocable — it documents patterns and conventions for OOB and variant work.

---

## File Structure

### OOB Files (`history/units/`)

Each country has multiple OOB files gated by DLC:

| Pattern | DLC Gate | Content |
|---------|----------|---------|
| `TAG_YEAR_nsb.txt` | No Step Back | Ground units (divisions, templates) |
| `TAG_YEAR_nonnsb.txt` | Fallback | Legacy ground units |
| `TAG_YEAR_bba.txt` | By Blood Alone | Air units (airframes, wings) |
| `TAG_YEAR_nonbba.txt` | Fallback | Legacy air units |
| `TAG_YEAR_naval_mtg.txt` | Man the Guns | Naval fleets (ships, task forces) |

The country history file (`history/countries/TAG - Name.txt`) sets which OOB to use:
```
set_oob = "TAG_2000_nsb"         # Ground
set_naval_oob = "TAG_2000_naval_mtg"  # Naval
set_air_oob = "TAG_2000_bba"    # Air
```

### Equipment Variants (`history/countries/TAG - Name.txt`)

Variants are defined inside the `2000.1.1` date block, typically gated by DLC:
```
if = {
    limit = { has_dlc = "No Step Back" }
    # NSB tank/vehicle variants here
}
if = {
    limit = { has_dlc = "By Blood Alone" }
    # BBA aircraft variants here
}
```

---

## Equipment Variant Patterns

### Tank / Vehicle Variant
```
create_equipment_variant = {
    name = "T-64B"
    type = medium_tank_chassis_1          # chassis type + generation
    parent_version = 0                     # base version to derive from
    modules = {
        main_armament_slot = tank_medium_cannon_2
        ammunition_load_slot = mixed_main_ammo_2
        turret_type_slot = tank_soviet_turret
        suspension_type_slot = tank_torsion_bar_suspension_medium
        armor_type_slot = tank_composite_armor_gen2
        engine_type_slot = tank_diesel_engine_gen2
        reload_type_slot = automatic_loading
        special_type_slot_1 = smoke_launchers
        special_type_slot_2 = empty
        special_type_slot_3 = smoothbore_atgm_gen1
        special_type_slot_4 = tank_battlestation_2
        special_type_slot_6 = reactive_armor_gen1   # optional ERA
    }
    upgrades = {
        tank_nsb_armor_upgrade = 2
    }
    obsolete = yes                         # mark if not in active production
    icon = "gfx/interface/technologies/TAG/LAND/image.dds"
    model = "entity_name"
}
```

### Chassis Types

Source: `common/units/equipment/MD_x_tank_chassis.txt`

| Chassis | In-Game Role | Equipment IDs | Example Vehicles |
|---------|-------------|---------------|------------------|
| `medium_tank_chassis_N` | MBT (Main Battle Tank) | MBT_1 – MBT_8 | T-64, T-84, Leopard 2, M1 Abrams |
| `medium_tank_amphibious_chassis_N` | APC (Wheeled/Tracked APC) | APC_1 – APC_8 | BTR-3, BTR-60, MT-LB, M113 |
| `medium_tank_flame_chassis_N` | IFV (Infantry Fighting Vehicle) | IFV_1 – IFV_8 | BMP-2, BMP-3, Bradley, Marder |
| `medium_tank_artillery_chassis_N` | SP Artillery | SP_arty_0 – SP_arty_4 | 2S1 Gvozdika, 2S19 Msta, PzH 2000 |
| `medium_tank_rocket_chassis_N` | MLRS / Rocket Artillery | SP_R_arty_0 – SP_R_arty_4 | BM-27 Uragan, M270 MLRS |
| `medium_tank_aa_chassis_N` | SPAA (Self-Propelled Anti-Air) | SP_Anti_Air_0 – SP_Anti_Air_4 | ZSU-23-4, Tunguska, Gepard |
| `medium_tank_destroyer_chassis_N` | Recon Tank / Light Tank | Rec_tank_0 – Rec_tank_5 | BRDM, AMX-10RC, Stryker |
| `heavy_tank_chassis_N` | Attack Helicopter | attack_helicopter1 – attack_helicopter5 | Mi-24, AH-64 Apache, Ka-52 |
| `heavy_tank_amphibious_chassis_N` | Transport Helicopter | transport_helicopter1 – transport_helicopter5 | Mi-8, UH-60 Black Hawk, CH-47 |

**Generation mapping (medium_tank_chassis MBT):**

| Equipment ID | Year | Gen (`_N` suffix) |
|-------------|------|--------------------|
| MBT_1 | 1965 | `medium_tank_chassis_0` |
| MBT_2 | 1975 | `medium_tank_chassis_1` |
| MBT_3 | 1985 | `medium_tank_chassis_2` |
| MBT_4 | 1995 | `medium_tank_chassis_3` |
| MBT_5 | 2015 | `medium_tank_chassis_4` |
| MBT_7 | 2025 | `medium_tank_chassis_5` |
| MBT_8 | 2035 | `medium_tank_chassis_6` |

**Generation mapping (APC/IFV — same pattern):** APC_1/IFV_1 = `_0` (1965), APC_2/IFV_2 = `_1` (1975), etc. through `_7` (2035).

**Notes:**
- Despite the HOI4 naming (`flame`, `amphibious`, `destroyer`), MD repurposes these chassis types for modern vehicle roles as shown above.
- Attack and transport helicopters use `heavy_tank_chassis` / `heavy_tank_amphibious_chassis` — they are land equipment, not air.
- SP Arty, MLRS, and SPAA have fewer generations (5 tiers: 0–4) compared to MBT/APC/IFV (8 tiers: 1–8).
- Recon tanks have 6 tiers (0–5).
- Helicopters have 5 tiers (1–5).

### Key Tank Modules

**Main guns** (generation matters for historical accuracy):
- `tank_medium_cannon` — Gen 1 (e.g., 2A26M2 on T-64A/B)
- `tank_medium_cannon_2` — Gen 2 (e.g., 2A46M on T-72B, T-80U, T-84)

**Ammo:**
- `mixed_main_ammo_1` — Gen 1 (T-64A/B era rounds)
- `mixed_main_ammo_2` — Gen 2 (improved rounds)

**ATGMs:**
- `smoothbore_atgm_gen1` — Gen 1 (9M112 Kobra)
- `smoothbore_atgm_gen2` — Gen 2 (9M119 Svir basic)
- `smoothbore_atgm_gen3` — Gen 3 (9K120 Svir/Refleks, Kombat)

**Armor:**
- `tank_composite_armor_gen1` / `gen2` — Composite armor generations
- `reactive_armor_gen1` — ERA (e.g., Kontakt-1 on T-64BV)
- `reactive_armor_gen2` — Improved ERA (e.g., Nozh on T-64BM Bulat)

**Engines:**
- `tank_diesel_engine_gen1` through `gen4` — Diesel engine generations
- `tank_turbine_engine_gen1` through `gen2` — Gas turbine engines

---

## Aircraft

### Aircraft Airframe Types

Source: `common/units/equipment/MD_x_plane_airframes.txt`

Base archetypes (defined in `MD_plane_airframes.txt`):
- `small_plane_airframe` — Small fighters
- `cv_small_plane_airframe` — Small carrier fighters
- `medium_plane_airframe` — Medium multirole / strike fighters
- `cv_medium_plane_airframe` — Medium carrier planes
- `large_plane_airframe` — Large strategic bombers

Duplicate archetypes (sub-types derived from base archetypes):

| Airframe | Base Archetype | In-Game Role | HOI4 Type | Equipment IDs |
|----------|---------------|-------------|-----------|---------------|
| `small_plane_cas_airframe` | `small_plane_airframe` | Small CAS | `cas` | — |
| `small_plane_strike_airframe` | `small_plane_airframe` | Light Multirole / Trainer | `tactical_bomber` | L_Strike_fighter1–5 |
| `small_plane_naval_bomber_airframe` | `small_plane_airframe` | Small Naval Bomber | `naval_bomber` | — |
| `small_plane_suicide_airframe` | `small_plane_airframe` | UAV / Drone | `suicide` | Air_UAV1–4 |
| `medium_plane_fighter_airframe` | `medium_plane_airframe` | Air Superiority Fighter | `fighter` | AS_Fighter1–7 |
| `medium_plane_cas_airframe` | `medium_plane_airframe` | Medium CAS / Attack | `cas` | cas1–5 |
| `medium_plane_suicide_airframe` | `medium_plane_airframe` | Kamikaze Drone / Loitering Munition | `suicide` | kamikaze_drone_1–4 |
| `medium_plane_maritime_patrol_airframe` | `medium_plane_airframe` | Medium Maritime Patrol | `naval_bomber` | — |
| `medium_plane_air_transport_airframe` | `medium_plane_airframe` | Medium Transport | `suicide` | — |
| `large_plane_maritime_patrol_airframe` | `large_plane_airframe` | Large Maritime Patrol (MPA) | `naval_bomber` | naval_plane1–6 |
| `large_plane_awacs_airframe` | `large_plane_airframe` | AWACS / Scout Plane | `scout_plane` | awacs_equipment_1–2 |
| `large_plane_cas_airframe` | `large_plane_airframe` | Gunship (AC-130 type) | `cas` | — |
| `large_plane_air_transport_airframe` | `large_plane_airframe` | Large Transport | `suicide` | transport_plane1–6 |

Carrier variants (CV prefix):

| Airframe | Base Archetype | Role | Equipment IDs |
|----------|---------------|------|---------------|
| `cv_small_plane_cas_airframe` | `cv_small_plane_airframe` | Carrier CAS | — |
| `cv_small_plane_naval_bomber_airframe` | `cv_small_plane_airframe` | Carrier Naval Bomber | — |
| `cv_small_plane_suicide_airframe` | `cv_small_plane_airframe` | Carrier Drone | — |
| `cv_small_plane_strike_airframe` | `cv_small_plane_airframe` | Carrier Light Multirole | CV_L_Strike_fighter1–5 |
| `cv_medium_plane_fighter_airframe` | `cv_medium_plane_airframe` | Carrier AS Fighter | — |
| `cv_medium_plane_cas_airframe` | `cv_medium_plane_airframe` | Carrier CAS | — |
| `cv_medium_plane_scout_airframe` | `cv_medium_plane_airframe` | Carrier AWACS | cv_awacs_equipment_1–2 |
| `cv_medium_plane_maritime_patrol_airframe` | `cv_medium_plane_airframe` | Carrier MPA | — |
| `cv_medium_plane_air_transport_airframe` | `cv_medium_plane_airframe` | Carrier Transport | — |

**Medium multirole equipment (uses base `medium_plane_airframe` directly):**
- Multirole fighters: MR_Fighter1–7 (carrier: CV_MR_Fighter1–7)
- Strike fighters: Strike_fighter1–7

### Aircraft Variant (BBA)
```
create_equipment_variant = { #Large Transport
    name = "An-26"
    type = large_plane_air_transport_airframe_1
    parent_version = 1
    modules = {
        fixed_main_weapon_slot = weap_buff_transport
        fixed_gun_slot = empty
        engine_type_slot = engine_prop_double_1
        avionics_type_slot = avionics_manned_1
        wingform_type_slot = wing_straight
        special_slot_type_1 = empty
        special_slot_type_2 = empty
        special_slot_type_3 = empty
        fixed_auxiliary_weapon_slot_1 = empty
        fixed_auxiliary_weapon_slot_2 = empty
    }
    obsolete = yes
    icon = "gfx/interface/technologies/TAG/AIR/image.dds"
}
```

---

## Stockpile & Deployment

### Adding to Stockpile (reserve equipment)
```
add_equipment_to_stockpile = {
    type = medium_tank_chassis_1
    variant_name = "T-64B"
    amount = 500
    producer = UKR              # who manufactured it
}
```

### Air Wings (deployed in BBA OOB file)
```
696 = { #Kharkiv
    small_plane_airframe_2 = { owner = "UKR" creator = "SOV" amount = 50 version_name = "MiG-29 Fulcrum" }
    name = "8-yi Vynyshchuvalnyi Aviatsiynyi Polk"
    start_experience_factor = 0.4
}
```

The state ID is the deployment location. `owner` is current owner, `creator` is who built it (affects variant lookup).

---

## Naval OOB

### Ship Entry
```
ship = { name = "Hetman Sahaydachnyi" definition = frigate start_experience_factor = 0.50 equipment = { frigate_hull_1 = { amount = 1 owner = UKR creator = UKR version_name = "Krivak III Class" } } }
```

- `definition` = ship class (frigate, corvette, cruiser, submarine, etc.)
- `creator` = who defined the variant (often SOV for Soviet-era ships inherited by successor states)
- `version_name` must match a `create_equipment_variant` with that `name` in the creator country's history file

### Ship Hulls

Source: `common/units/equipment/MD_mtg_ships.txt`

**Screen Ships:**

| Hull | Type | Tiers | Year Range | Role |
|------|------|-------|------------|------|
| `corvette_hull_N` | `screen_ship` | 1–6 | 1965–2040 | Corvettes, patrol boats (Grisha, Tarantul, Pauk) |
| `stealth_corvette_hull_N` | `screen_ship` | 1–3 | 2010–2040 | Stealth corvettes (higher cost, lower visibility) |
| `frigate_hull_N` | `screen_ship` | 1–6 | 1965–2040 | Frigates (Krivak, Oliver Hazard Perry) |
| `stealth_frigate_hull_N` | `screen_ship` | 1–3 | 2010–2040 | Stealth frigates |
| `heavy_frigate` | `screen_ship` | archetype only | 2010 | Heavy frigate upgrade (higher cost) |
| `destroyer_hull_N` | `screen_ship` | 1–5 | 1965–2045 | Destroyers (Arleigh Burke, Sovremenny) |
| `stealth_destroyer_hull_N` | `capital_ship` | 1–3 | 2015–2040 | Stealth destroyers (Zumwalt-type) |

**Capital Ships:**

| Hull | Type | Tiers | Year Range | Role |
|------|------|-------|------------|------|
| `cruiser_hull_N` | `capital_ship` | 1–5 | 1965–2040 | Cruisers (Slava, Ticonderoga) |
| `battle_cruiser_hull_N` | `capital_ship` | 1–4 | 1965–2025 | Battlecruisers (Kirov class) |
| `battleship_hull_N` | `capital_ship` | 0–4 | 1965–2025 | Battleships (Iowa class, Yamato) |
| `helicopter_operator_hull_N` | `carrier` | 1–4 | 1970–2025 | Helicopter carriers / LHDs (Mistral, Wasp) |
| `carrier_hull_N` | `carrier` | 1–5 | 1965–2040 | Aircraft carriers (Nimitz, Kuznetsov) |

**Submarines:**

| Hull | Type | Tiers | Year Range | Role |
|------|------|-------|------------|------|
| `attack_submarine_hull_N` | `submarine` | 1–6 | 1965–2040 | Attack submarines (Los Angeles, Akula, Kilo) |
| `missile_submarine_hull_N` | `submarine` | 1–6 | 1965–2040 | Missile submarines / SSBNs (Ohio, Typhoon) |

**OOB `definition` field values:** The `definition` field in ship entries maps to these roles: `corvette`, `frigate`, `destroyer`, `cruiser`, `battle_cruiser`, `battleship`, `helicopter_operator`, `carrier`, `submarine` (for both attack and missile subs).

**Notes:**
- Stealth variants have significantly lower `surface_visibility` but higher build cost and use `composites` instead of `aluminium`
- Battleship uses `battleship_hull_0` as its archetype (not a separate named archetype) — it's an `is_archetype = yes` hull
- Ship hulls have zero intrinsic combat stats — all offense/defense comes from modules
- Armor is zeroed out across all hulls; CIWS modules provide missile defense instead

### Production Queue (in-progress builds)
```
instant_effect = {
    add_equipment_production = {
        equipment = {
            type = corvette_hull_2
            creator = "UKR"
            version_name = "Grisha V Class"
        }
        requested_factories = 0      # 0 = paused
        progress = 0.80              # 80% complete
        efficiency = 30
        amount = 1
    }
}
```

---

## Equipment Bonuses in Ideas

When adding production bonuses in `common/ideas/`, target the **chassis archetype**, not individual equipment IDs. Each chassis type is independent for bonus purposes:

```
equipment_bonus = {
    medium_tank_chassis = { build_cost_ic = -0.03 }              # MBTs only
    medium_tank_amphibious_chassis = { build_cost_ic = -0.03 }   # APCs only
    medium_tank_flame_chassis = { build_cost_ic = -0.03 }        # IFVs only
}
```

A country with MBT bonuses does NOT automatically get APC or IFV bonuses — each must be listed separately.

---

## Common Pitfalls

1. **Creator mismatch**: If a ship/plane uses `creator = SOV`, the variant must be defined in `SOV - Russia.txt`, not the country's own file. Countries that inherited Soviet equipment typically use `creator = SOV`.

2. **Tech requirements**: A country must have the tech for a chassis/airframe type before it can use variants of that type. Check the country's `set_technology` block.

3. **Module availability**: Modules like `smoothbore_atgm_gen3` require the corresponding tech (e.g., `nsb_special_ammo_1`). Verify the country has it before assigning the module.

4. **Obsolete flag**: Set `obsolete = yes` on older variants so AI doesn't try to produce them. Only the newest/best variant should lack this flag.

5. **Production bonuses**: Equipment bonuses in ideas target chassis types, not individual variants. If a country has `medium_tank_chassis` bonuses but not `medium_tank_amphibious_chassis` or `medium_tank_flame_chassis`, IFVs/APCs won't benefit.

6. **Hull/role mismatch**: Don't use corvette hulls for minesweepers or other roles the hull wasn't designed for — it causes AI equipment/role mismatch issues.

7. **DLC gating**: Always place NSB variants inside `has_dlc = "No Step Back"` blocks and BBA variants inside `has_dlc = "By Blood Alone"` blocks. Provide fallback content in `else` blocks.

8. **Helicopter chassis confusion**: Attack and transport helicopters use `heavy_tank_chassis` and `heavy_tank_amphibious_chassis` respectively — they are land equipment despite being aircraft. Don't confuse these with actual heavy tank or amphibious tank variants.

9. **Transport airframe type**: Both `medium_plane_air_transport_airframe` and `large_plane_air_transport_airframe` use HOI4 type `suicide` internally (a quirk of the engine). This is normal — don't change it.
