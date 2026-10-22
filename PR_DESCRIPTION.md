### Changes

Naval rework on top of `Ex-USSR-navy-rework-` (base commit `207323f`). Every surface ship from patrol boats to battlecruisers now uses one standard 21-slot layout: basic equipment no longer takes weapon slots, the patrol boat becomes a real single-role coastal craft, and several systems are split by ship size. 256 files changed, mostly history variants, focus and event designs, OOBs and AI templates converted to the new layout.

All MD validators (`equipment_variants`, `technologies`, `tech_categories`, `history`, `oob_units`, `gfx_references`, `modifiers`, `localisation`, `ai_equipment`, `ai_roles`, `ai_navy`, `style --staged`) report no new issues compared to the base branch. A separate check of all 2,764 ship designs (slot exists, category allowed, unlocks, count limits) is clean apart from 23 carrier designs that already lacked a flight deck on the base branch. Nothing has been tested in game yet, so balance, AI designs and the designer layout still need an in-game check.

---

## 1. The 21-slot layout

Restructured hulls: patrol boat, corvette, stealth corvette, frigate, stealth frigate, heavy frigate, destroyer, stealth destroyer, cruiser and battlecruiser. Fixed slots are placed by index, custom slots fill the middle row:

| Row | Slots (index) |
|---|---|
| Bottom: auxiliary equipment (0-6) | Hull Shape, Engine, Fire Control, Radar / Sonar, CIWS, Auxiliary Equipment, Helicopter Deck |
| Middle: generic weapons | Missile Magazine (fixed index 7), then up to six custom slots (any weapon of the class) |
| Top: named weapons (fixed 8-14) | Artillery, Main Armament, Secondary Armament, Tertiary Armament, ASW Armament I, ASW Armament II, Medium-Range SAM |

- Generic weapon slots per class: patrol boat 0, corvette and stealth corvette 2 (a trimaran opens a 3rd), frigate and stealth frigate 3, heavy frigate 4, destroyer and stealth destroyer 4, cruiser 5, battlecruiser 6. They are custom slots, and the designer always draws all custom positions, so the ones a class does not have show a padlock.
- Patrol boats only have Artillery, Main Armament, Secondary Armament (opened by a trimaran hull) and Medium-Range SAM in the top row, and their middle row is locked apart from the missile magazine.
- `interface/equipmentdesignerview.gui`: fixed positions 8-14 form the top row, custom positions 0-5 fill the middle row after the missile magazine and custom position 6 sits at the end of the top row (only battleships, carriers and landing ships use it). Fixed positions 0-7 are unchanged, so submarines keep their layout apart from the missile submarine's single custom slot, which moves to the middle row. The dynamic version checkbox moved below the middle row.
- Battleships, carriers and landing ships keep their current slots and get extra fixed weapon slots (copies of their custom slot categories) up to 21. Landing ships also get four more custom slots. Submarines are unchanged.
- The designer overlays (`interface/equipmentdesigner/MD_ship_hull_*.gui`) are regenerated from the new slot lists, keeping the existing category art.

### Conditional slots
HoI4 has no conditional `module_count_limit`, but a module can open categories in another slot (`allowed_module_categories = { <slot> = { ... } }`, the mechanism missile mounts already use for the missile magazine). The hull shape modules use it:

| Hull shape (patrol boat, corvette) | Helicopter deck | Sonar and ASW weapons | Extra |
|---|---|---|---|
| Conventional | yes | yes | |
| Hydrofoil | no | yes | faster, shorter range |
| Hovercraft (air cushion) | no | no | mine sweeping and landing support |
| Trimaran (from 2010) | yes | yes | one more weapon slot (patrol boats: Secondary Armament) |

Fixed per-hull limits are still used where the rule depends on the hull level (for example no hangar on the first two corvette hulls).

## 2. Patrol boats
- Six hulls: 1965, 1985, 2010, 2030, 2050, 2070 (`patrol_boat_hull_1_tech` to `_6_tech`), unlocked like corvette hulls of the same era for every country. References to the old eight techs in history, focuses and events were remapped.
- One combat role in Main Armament: patrol and boarding equipment, anti-ship missile tubes (2 or 4), light ASW torpedoes or a light ASW mortar, or mine countermeasures (mechanical, magnetic or drone sweeps). Pure patrol designs get the patrol equipment.
- Radar or sonar (one slot), artillery up to 76 mm or a gun CIWS (one or two mounts), AA slot with MANPADS, a CIWS (one or two mounts) or autocannons (a two-mount CIWS only once per ship, in the Artillery or the CIWS slot), auxiliary slot for a patrol launch, sea drones, a recon drone or mines, tube SAM launchers (2 or 4).
- Hit profile: missile tubes add +50% (Jeune Ecole light tubes +25%), the helipad another +50% and costs 2500-3000 IC (more than the whole 1750 IC hull). No helipad on the first hull.
- Short range (hull shapes -40% to -65% range) and combat bonuses in fjords, littoral and shallow seas (+15% to +20% attack, +5% to +10% movement) with -20% attack on the deep ocean.
- Cost and steel: hull 1750 IC (corvette 2100); 3 steel on hulls 1-4 and 5 on hulls 5-6. Jeune Ecole: -37.5% production cost, -50% design cost, light series hull forms with less steel and light missile tubes.
- Classification: up to 400-500 t full load and coastal only. OPVs and anything able to operate on the open ocean stay corvettes. 51 variants and 379 starting ships use the patrol hull (missile boats such as Tarantul, Sa'ar 4/4.5, Hamina, Stockholm; ASW boats such as Pauk, Svetlyak, Mukha; minesweepers such as Sonya, Landsort; patrol boats such as Cyclone, Fearless).
- AI: missile, ASW and minesweeper patrol boats for all six hulls in `common/ai_equipment/generic_patrol_boats.txt`, with role ratios in `common/ai_strategy/naval.txt`.

## 3. Auxiliary row by class
| Slot | Patrol boat | Corvettes | Frigates | Destroyers | Cruisers, battlecruisers |
|---|---|---|---|---|---|
| Hull Shape | conventional, hydrofoil, hovercraft, trimaran | same | conventional, inverted bow | same | same |
| Engine | patrol diesel or gas turbine; diesel-electric for minesweepers only | light diesel, gas turbine or combined | medium diesel, gas turbine or combined | gas turbine, combined or small nuclear | combined or nuclear |
| Fire Control | small | small | large | large | large |
| Radar / Sonar | small radar or sonar | small radar or sonar; combined suite from the third hull | radar, sonar or combined | radar, sonar or combined | radar only (battlecruisers also sonar or combined) |
| CIWS mounts | 1 or 2 (2 in one slot only) | up to 2 | up to 4 | up to 4 | up to 6 |
| Helicopter Deck | patrol landing pad | landing pad, hangar (not on hulls 1-2) | landing pad, hangar, extended hangar | same | same |

- Engines are split into families by ship size, each family its own category:
  - Patrol boats get their own engines: oil and diesel I-V, gas turbine I-IV, and a diesel-electric drive I-V (-3 speed, -15% surface visibility, some mine sweeping) that only a mine countermeasure module unlocks. Other hulls forbid it with a count limit.
  - New combined propulsion (CODOG / CODAG / COGAG) I-VI in light, medium and large sizes: gas turbine speed, 10% more range than either plant, 15% higher cost. Unlocked by the gas turbine techs.
  - Small nuclear reactors (the former light reactors) are for destroyers only; full reactors and fusion engines go on cruisers, battlecruisers and capital ships.
  - The oil-fired plant stays in the diesel category of patrol boats, corvettes and frigates. Frigates keep the medium engines; medium reactors and fusion engines were removed.
  - Battleships, carriers and landing ships take every large-ship family.
  - Designs: destroyers on diesel or oil and cruisers on diesel, oil or gas turbines now use combined propulsion of the same level; nuclear destroyer AI templates use small reactors.
- Combined radar and sonar suites I to IX (small and large) carry both sensors at 90% of their cost.
- CIWS: four families (gun CIWS, missile CIWS / RAM, gun-missile, laser) with 1, 2, 3, 4 or 6 mounts. Mounts are averaged for armor, so one slot with a mount count replaces stacking modules. A second CIWS family on a ship goes to a generic weapon slot.
- Helicopter deck: landing pad (new, cheap, no hangar), hangar (light helipad, one helicopter), extended hangar (two helicopters).
- Small, large and capital fire control as before; capital fire control for carriers, landing ships and battleships.

## 4. Weapons
- Artillery: gun artillery (57 mm and 76 mm light guns, 100 mm and 127 mm medium guns, 155 mm guns from 2000 on destroyers and larger), single or twin barrels; gun batteries (76/100/127/152 mm) with two single, two twin or three twin turrets; autocannons and machine guns (patrol boats, corvettes and frigates only).
- Main, Secondary, Tertiary: missile mounts, multipurpose VLS (16, 24, 32, 48 cells; 64 cells on destroyers and larger), railguns, guns; mine countermeasures and minelaying as a ship role.
- ASW I and II: torpedoes (light 324 mm on every hull, universal 533 mm, drone and nuclear torpedoes on corvettes and larger), rocket launchers (light and heavy ASW mortars) and depth charges (new, three levels).
- Medium-Range SAM: arm launchers (1 or 2, not on patrol boats), tube launchers (2, 4, 6 or 8 tubes; patrol boats 2 or 4; from the first SAM tech in 1975), VLS SAM (8 cells on corvettes, 8 or 16 on frigates, 16 or 32 on destroyers and larger). The old 4-cell VLS SAM became the 4-tube launcher.
- Torpedoes: light (324 mm) and universal (533 mm), each in ASW and anti-ship versions. Soviet names: light SET-40, SET-72, MPT-1UME, MTT (Paket-NK); universal ASW SET-53, SET-65, TEST-71, TE-2.
- VLS limits: corvettes one bank up to 32 cells, frigates one 48-cell bank, destroyers two 48 and two 64, cruisers no 16-cell banks, three 48 and two 64, battlecruisers up to six 64.

## 5. Landing ships
- A required Ship Class slot replaces the old flight deck slot and carries the ship's aviation, so helicopter and deck limits per class are enforced:

| Class | Aviation | Price and stats |
|---|---|---|
| LST | none | cost -45%, strength -35%, speed -10%, visibility -35%, shore attack -30% |
| LST with helipad I-III | 1 helicopter | as LST |
| LSD I-III | 2 helicopters | cost -20%, strength -15% |
| LPD I-III | 3 helicopters | cost +5% |
| LPH | flight deck (air wing 1) | cost +5% |
| LHD / LHA | full flight deck (air wing 2) | cost +20%, strength +15%, detection +10% |

- New naval rocket launchers I-III (Soviet level I: A-215 Grad-M) for LSTs and LSDs. Weapon rules per class (no guns or rocket launchers on LPD/LPH, VLS for LHD/LHA) are written in the module descriptions and followed by history and AI designs, but not enforced.
- Carriers can also mount heavy ASW mortars, so ships like Admiral Kuznetsov can be modelled. The carrier hull keeps `offensive_weapons = no`.

## 6. Design conversion
- All 1,833 surface-ship designs (365 history, focus, event and decision variants and 1,468 AI templates) were moved to the new slots by module type. Engines were resized to the class, radar and sonar merged into a combined suite where the class allows it, CIWS mounts of one family were summed into one module, two arm SAM launchers became a twin launcher, VLS SAM sizes follow the class, and helicopter modules follow the class rules.
- 26 designs lost a minor extra module that has no slot left: a second autocannon on 11 patrol boats (the AA slot keeps the MANPADS or CIWS), an extra ESM on 7 battlecruiser AI templates, a fuel tank on 5 ships, and an unused heavy frigate upgrade package on 3 frigates.
- AI `allowed_modules` lists were extended with every category their converted templates use.

---

## Interface and localisation
- New slot titles, category titles, and names and descriptions for 204 new modules (English only; other languages follow the usual translation pass).
- Slot and module icons reuse existing textures.
- One Changelog line under v2.1.0 Balance.

## Known limitations
- Slot positions assume the engine places fixed slots in definition order. If it does not, the rows need reordering in the hull files.
- Category unlocks from hull shapes rely on the same mechanism as the missile magazine; this needs an in-game check for the helicopter deck, radar and ASW slots.
- Terrain bonuses on the patrol boat sub-unit use the same keys as the naval doctrines and need an in-game check.
- Landing ship weapon rules per class are not enforced by the engine.
- The old light flight deck modules are no longer used by any hull but are still defined and unlocked.
