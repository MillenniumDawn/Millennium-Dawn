---
title: GFX Entity & Asset Errors
description: How to diagnose and fix common GFX entity, particle, and asset errors in Millennium Dawn.
---

This guide covers the most common `pdx_entity.cpp` and `assetfactory.cpp` errors that appear in the HOI4 error log and how to fix them.

The error log is located at:

- **Linux**: `~/.local/share/Paradox Interactive/Hearts of Iron IV/logs/error.log`
- **Windows**: `Documents/Paradox Interactive/Hearts of Iron IV/logs/error.log`

---

## GFX File Structure

Understanding the relationship between file types is essential for diagnosing entity errors.

### File Types

| Extension            | Purpose                                                                                               |
| -------------------- | ----------------------------------------------------------------------------------------------------- |
| `.gfx`               | Declares `pdxmesh` (mesh + animation bindings) and `pdxparticle` references                           |
| `.asset`             | Defines `entity` blocks that reference `pdxmesh` names and wire up states, attachments, and particles |
| `.mesh`              | The raw 3D model file, referenced by `pdxmesh` blocks in `.gfx` files                                 |
| `.asset` (particles) | Defines particle systems referenced by `pdxparticle` in `.gfx` files                                  |

A typical country unit requires two paired files:

```
gfx/entities/
  TAG_MD_infantryandvehicle.gfx    ← declares pdxmesh + animations
  TAG_MD_infantryandvehicle.asset  ← defines entity blocks using those meshes
```

The `.gfx` file links a mesh name to a `.mesh` file and maps animation IDs:

```
pdxmesh = {
    name = "JAP_MDinfantry1_mesh"
    file = "gfx/models/units/infantry/JAP KOR TAI/JAP_MDinfantry_1.mesh"
    animation = { id = "idle"   type = "GER_infantry_mg_idle_animation" }
    animation = { id = "attack" type = "GER_infantry_mg_attack_animation" }
    ...
}
```

The `.asset` file then defines entities that reference that mesh and add states and attach points:

```
entity = {
    name = "JAP_MD4_infantry_2_entity"
    pdxmesh = "JAP_MDinfantry1_mesh"

    state = { name = "idle"   animation = "idle"   ... }
    state = { name = "attack" animation = "attack" ... }

    attach = { name = "rifle1" Right_Hand_node = "JAP_weapon_Type89rifle_right_entity" }
}
```

### File Naming Conventions

| Pattern                                     | Usage                                                         |
| ------------------------------------------- | ------------------------------------------------------------- |
| `TAG_MD_infantryandvehicle.asset/.gfx`      | Country infantry and vehicle entities                         |
| `TAG_MD_planes.gfx` + `TAG_planes.asset`    | Country air unit entities                                     |
| `TAG_MD_tanks.gfx` + `TAG_tanks.asset`      | Country armor entities                                        |
| `___MD_infantry_units.asset`                | Shared infantry definitions (triple underscore = loads first) |
| `___MD_tanks_and_vechicles.gfx`             | Shared vehicle mesh declarations                              |
| `units_ships.asset`, `units_infantry.asset` | Vanilla-parallel base files                                   |
| `_BfB_vehicles.asset`, `_LaR_units_*.asset` | Submod/DLC compatibility files                                |
| `MD4_units_ships.asset`                     | MD ship entity overrides/additions                            |

### Clone Entities

Clone blocks create environment-specific variants (snow, desert, default) from a single base entity without duplicating all state definitions:

```
entity = {
    clone = "JAP_MD4_infantry_2_entity"
    name = "JAP_infantry_entity_snow"
    pdxmesh = "JAP_MDinfantry1_mesh"
}
```

The clone inherits all states and attach points from the parent. Only fields explicitly set in the clone block are overridden. **The parent entity must be defined before the clone in load order.**

### Particle Wiring

Particles are declared in `gfx/particles/` as `.asset` files, then registered in a `.gfx` file as a named `pdxparticle`, and finally referenced by that name inside entity `state` event blocks:

```
# gfx/particles/vehicles/sparks.asset
particle = { name="MD_sparks_file" ... }

# gfx/entities/MD_particles.gfx
pdxparticle = { name = "sparks_particle"  type = "MD_sparks_file"  scale = 1 }

# gfx/entities/TAG_MD_infantryandvehicle.asset
state = { name = "attack"  ...
    event = { node="barrel" particle = "sparks_particle" ... }
}
```

### Vanilla File Locations

The vanilla game and each DLC ship their own entity files that are merged with mod files at load time. Always check both locations when diagnosing duplicates:

```
Hearts of Iron IV/gfx/entities/              ← base game
Hearts of Iron IV/dlc/DLC_NAME/gfx/entities/ ← DLC additions
```

Notable DLC entity packs that overlap with MD assets:

| DLC folder                                 | Contents                                 |
| ------------------------------------------ | ---------------------------------------- |
| `dlc025_axis_armor_pack`                   | Italian, German, Japanese armor entities |
| `dlc036_by_blood_alone`                    | Italian air/vehicle entities             |
| `dlc048_expansion_pass_2_seaplane_tenders` | Commonwealth ship entities               |

---

## Duplicate Entity

```plaintext
[pdx_entity.cpp:2172]: Duplicate of ITA_mechanized_vehicle_1_entity added to entity system
```

**Cause:** An entity name is defined in both the mod and a vanilla file (base game or DLC). HOI4 merges all `.asset` files at load time — it does not let mod files override vanilla ones.

**How to diagnose:**

1. Search the mod for the entity name:
   ```bash
   grep -rn 'name = "ITA_mechanized_vehicle_1_entity"' gfx/entities/
   ```
2. Search the vanilla install for the same name:
   ```bash
   grep -rn '"ITA_mechanized_vehicle_1_entity"' \
     ~/.local/share/Steam/steamapps/common/Hearts\ of\ Iron\ IV/
   ```
3. If both return results, you have a duplicate.

**Fix options:**

- **Remove the mod definition** if the vanilla entity already provides the correct mesh and animations. Check that nothing else in the mod references the entity before deleting.
- **Rename the mod's entity** to a unique name (e.g., prefix with `TAG_MD_`) and update all references if the mod needs a different visual.

---

## Missing Clone Parent

```plaintext
[assetfactory.cpp:876]: Couldn't find parent clone entity JAP_MD4_infantry_1_entity,
  in file "gfx/entities/JAP_MD_infantryandvehicle.asset", near line 1808
```

This is usually followed by a second error:

```plaintext
[pdx_entity.cpp:324]: Failed to find entity "JAP_infantry_entity_desert" for attachment in infantry
```

**Cause:** A `clone = "..."` block references a parent entity that does not exist. The child entity fails to be created entirely, causing any downstream `attach` references to it to also fail.

**How to diagnose:**

Search for the parent entity name in all mod `.asset` files:

```bash
grep -rn 'name = "JAP_MD4_infantry_1_entity"' gfx/entities/
```

If no results, the parent was renamed, never defined, or is a typo.

**Fix:** Correct the `clone` value to point to an entity that actually exists. Check nearby entity blocks in the same file for the correct name:

```bash
grep -n 'name = "JAP_MD4_infantry' gfx/entities/JAP_MD_infantryandvehicle.asset
```

Example fix — change the nonexistent parent to the correct one:

```diff
 entity = {
-	clone = "JAP_MD4_infantry_1_entity"
+	clone = "JAP_MD4_infantry_2_entity"
 	name = "JAP_infantry_entity_desert"
 	pdxmesh = "JAP_MDinfantry1_mesh"
 }
```

---

## Duplicate Particle Name

```plaintext
[pdx_particle.cpp:1608]: Particle name is not unique: sparks_file
```

**Cause:** The mod defines a particle with the same `name` as a vanilla particle. Like entities, particle files are merged — not overridden.

**How to diagnose:**

1. Search mod particle files:
   ```bash
   grep -rn 'name="sparks_file"' gfx/particles/
   ```
2. Search vanilla:
   ```bash
   grep -rn 'name="sparks_file"' \
     ~/.local/share/Steam/steamapps/common/Hearts\ of\ Iron\ IV/gfx/particles/
   ```

**Fix:** Rename the mod's particle to a unique name and update the corresponding `pdxparticle` reference in the `.gfx` file that references it.

`gfx/particles/vehicles/sparks.asset`:

```diff
 particle={
-	name="sparks_file"
+	name="MD_sparks_file"
```

`gfx/entities/MD_particles.gfx`:

```diff
 pdxparticle = {
 	name = "sparks_particle"
-	type = "sparks_file"
+	type = "MD_sparks_file"
 	scale = 1
 }
```

---

## Parent Window Not Found (GUI)

```plaintext
[p:447]: Parent window for MD_UN_SC_gui is not found.
```

**Cause:** A GUI element declares a `parent` container that hasn't been defined yet, or the parent name is misspelled.

**How to diagnose:**

```bash
grep -rn 'MD_UN_SC_gui\|name = "MD_UN_SC_gui"' interface/
```

Check that the parent `containerWindowType` or `windowType` exists and that its `name` matches exactly what is referenced.

---

## General Debugging Tips

- Always check the **vanilla DLC folders** as well as the base game — many entities and particles are added by DLC packs (e.g., `dlc025_axis_armor_pack`, `dlc048_expansion_pass_2_seaplane_tenders`).
- Entity names defined in mod files **cannot override** vanilla entities. You must use a unique name.
- After fixing an entity error, the downstream "Failed to find entity for attachment" errors for the same entity will automatically resolve.
- Filter the error log to just entity/asset lines for faster triage:
  ```bash
  grep -E 'pdx_entity|assetfactory|pdx_particle' error.log
  ```
