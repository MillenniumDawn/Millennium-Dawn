---
title: Add Landmarks
description: How to add a new landmark building (3D model + spawn point + state placement) to Millennium Dawn
---

Landmarks are special buildings that render a 3D model on the world map (Big Ben, Mt. Fuji, Statue of Liberty, etc.). Adding a new landmark requires **five files** to agree on which state, which province, and which world-space coordinates the model uses. If any one is wrong, you typically see the landmark icon appear in the state UI while the 3D model fails to render silently.

## Architecture

The chain runs in five layers:

1. The **building definition** in `common/buildings/01_landmark_buildings.txt` declares the landmark's name, DLC gate, modifiers, and `spawn_point = landmark_spawn`.
2. The **entity definition** in `gfx/entities/landmarks.asset` wires `building_landmark_<name>` to a mesh and to its scale + destruction states.
3. The **mesh definition** in `gfx/entities/landmarks.gfx` maps the mesh name to the `.mesh` file path.
4. The **state file placement** in `history/states/<id>-<Name>.txt` places the landmark in a specific province inside a `buildings = { }` block.
5. The **map spawn** in `map/buildings.txt` provides the world-space `(x, y, z)` coordinates used to actually render the model.

## Files

| File                                                                         | Purpose                                                                    |
| ---------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `common/buildings/01_landmark_buildings.txt`                                 | Building definition (DLC gate, modifiers, icon, controller gating)         |
| `gfx/entities/landmarks.asset`                                               | Entity blocks (`building_landmark_<name>` + `_destroyed`)                  |
| `gfx/entities/landmarks.gfx`                                                 | Mesh blocks (`landmark_<name>_mesh` + `_destroyed_mesh`)                   |
| `gfx/models/buildings/landmarks/<name>.mesh`                                 | The 3D model itself, plus its `.dds` textures and `.anim` files            |
| `interface/buildings/MD_landmarks.gfx`                                       | Icon sprites (`GFX_<name>_icon_small`) shown in the state UI               |
| `history/states/<id>-<Name>.txt`                                             | Per-state placement: `<PROVINCE_ID> = { landmark_<name> = { level = 1 } }` |
| `map/buildings.txt`                                                          | Spawn line: `<state_id>;landmark_spawn;<x>;<y>;<z>;<rot>;<province_id>`    |
| `localisation/english/replace/replaced_from_vanilla_buildings_l_english.yml` | `landmark_<name>` (display name) + `landmark_<name>_desc` (tooltip)        |

## Adding a New Landmark

### Step 1: Add the building definition

In `common/buildings/01_landmark_buildings.txt`, inside the outer `buildings = { }` block, add an entry. Follow the existing pattern:

```
landmark_my_landmark = {
    dlc_allowed = { has_dlc = "Götterdämmerung" }  # only required if DLC-gated
    show_on_map = 1
    base_cost = 20000
    damage_factor = 0
    icon_frame = 22
    value = 5

    is_buildable = no
    disable_grow_animation = yes
    spawn_point = landmark_spawn
    repair_speed_factor = @landmark_repair_speed_factor
    only_display_if_exists = yes
    special_icon = GFX_my_landmark_icon_small
    level_cap = {
        province_max = 1
    }
    always_shown = yes
    show_modifier = yes
    country_modifiers = {
        modifiers = {
            stability_factor = 0.02
            population_tax_income_multiplier_modifier = 0.01
        }
    }
}
```

**Naming convention:** the building key is `landmark_<name>`. The entity name will be `building_landmark_<name>`. The mesh name will be `landmark_<name>_mesh`. Pick `<name>` to be `[a-z_]` only.

**Tourism income:** add `population_tax_income_multiplier_modifier` (typically 0.01–0.02) for landmarks the player would realistically draw tourist revenue from. Skip it for strategic/military landmarks (ICBM silos, military bases).

**Controller gating:** omit `enable_for_controllers` so any owner of the state gets the modifier (the Mecca pattern). Add `enable_for_controllers = { TAG }` only when the modifier is meant to benefit a specific country (military assets, ideologically-coded monuments).

### Step 2: Add the entity definition

In `gfx/entities/landmarks.asset`, add the regular and destroyed entity blocks:

```
entity = {
    name = "building_landmark_my_landmark"
    pdxmesh = "landmark_my_landmark_mesh"

    default_state = "idle"
    state = { name = "idle"  animation = "idle"  animation_blend_time = 0.3 animation_speed = 1.0 looping = no }

    scale = 0.2
}

entity = {
    name = "building_landmark_my_landmark_destroyed"
    pdxmesh = "landmark_my_landmark_destroyed_mesh"

    default_state = "destroy"
    state = { name = "destroy"  animation = "destroy"  animation_blend_time = 0.0 animation_speed = 0.8 looping = no
        event = { time = 0 node="explosion" particle = "ship_explosion_particle" keep_particle = yes }
        event = { time = 0.2 sound = { soundeffect = "explosion_c4" } }
    }

    scale = 0.2
}
```

**Scale guidance:** larger meshes need smaller scales. Existing landmark scales range from `0.06` (Mt. Fuji, very large mesh) to `0.3` (Big Ben, normal building). Start with the same scale as a visually similar existing landmark.

### Step 3: Add the mesh definition

In `gfx/entities/landmarks.gfx`, inside the outer `objectTypes = { }` block, add the mesh blocks:

```
pdxmesh = {
    name = "landmark_my_landmark_mesh"
    file = "gfx/models/buildings/landmarks/landmark_my_landmark.mesh"

    animation = { id = "idle"  type = "landmark_my_landmark_idle_animation" }
}

pdxmesh = {
    name = "landmark_my_landmark_destroyed_mesh"
    file = "gfx/models/buildings/landmarks/landmark_my_landmark_destroyed.mesh"

    animation = { id = "destroy"  type = "landmark_my_landmark_destroyed_destroy_animation" }
}
```

### Step 4: Place the .mesh, .dds, and .anim files

Drop the model assets into `gfx/models/buildings/landmarks/`:

- `landmark_my_landmark.mesh` (and the destroyed variant)
- `landmark_my_landmark_diffuse.dds`
- `landmark_my_landmark_normal.dds`
- `landmark_my_landmark_specular.dds`
- `landmark_my_landmark_idle_animation.anim`
- `landmark_my_landmark_destroyed_destroy_animation.anim`

If you're reusing a vanilla mesh, skip this step — the engine resolves the path against vanilla as a fallback when MD doesn't ship its own copy.

### Step 5: Add the icon sprite

In `interface/buildings/MD_landmarks.gfx`, add:

```
spriteType = {
    name = "GFX_my_landmark_icon"
    texturefile = "gfx/interface/buildings/historical_buildings/large/my_landmark_icon.dds"
    noOfFrames = 2
}
spriteType = {
    name = "GFX_my_landmark_icon_small"
    texturefile = "gfx/interface/buildings/historical_buildings/small/my_landmark_icon_small.dds"
    noOfFrames = 2
}
```

Drop the corresponding DDS files into `gfx/interface/buildings/historical_buildings/large/` and `small/`.

### Step 6: Place the landmark in a state file

Inside the state's `history.buildings = { }` block, add a dedicated province block:

```
<PROVINCE_ID> = {
    landmark_my_landmark = {
        allowed = { has_dlc = "Götterdämmerung" }   # match the dlc_allowed value, or omit
        level = 1
    }
}
```

**Use a dedicated province block** containing only the landmark. Combining a landmark with `naval_base = N` in the same province block breaks rendering — the Big Ben gotcha. If the province already has other buildings, either move the landmark to a different province in the same state, or move the other building into its own block elsewhere in the file.

### Step 7: Add the world-space spawn line

In `map/buildings.txt`, append at the end:

```
<state_id>;landmark_spawn;<x>;<y>;<z>;<rotation>;<province_id>
```

You need four numbers that must agree:

- **state_id** matches the state file's `id = ...`.
- **province_id** (trailing field) matches the province the state file places the landmark in.
- **(x, z)** must fall inside that same province on `map/provinces.bmp` (see Step 8).
- **y** sits just above terrain at that XZ (see Step 9).
- **rotation** is in radians (0 to ~6.28); use whatever orientation looks right.

### Step 8: Verify the (x, z) coordinates land in the right province

Use this Python snippet to confirm your spawn lands inside the target province:

```python
from PIL import Image
import numpy as np, csv

arr = np.array(Image.open('map/provinces.bmp')); H, W, _ = arr.shape
color_to_pid = {}
with open('map/definition.csv', encoding='latin-1') as f:
    for r in csv.reader(f, delimiter=';'):
        if r and r[0].isdigit():
            color_to_pid[(int(r[1]), int(r[2]), int(r[3]))] = int(r[0])

def prov_at(x, z):
    px, py = int(round(x)), (H-1) - int(round(z))
    return color_to_pid.get(tuple(arr[py, px].tolist()))

# Replace with your spawn coords:
print(prov_at(2802, 1551))  # should print the province ID from your state file
```

If the function returns a different province ID than the one you placed the landmark in, the landmark will not render. Either move the spawn or move the placement.

**Pixel-to-world:** `world_x == pixel_x`, `world_z == (height − 1) − pixel_y`. The map is 5632×2048.

To find a safe interior pixel of a known province, take the centroid of the eroded mask (interior pixels only, no borders) of all pixels matching the province's RGB color in `definition.csv`.

### Step 9: Set y from the heightmap

`map/heightmap.bmp` is a single-channel image where sea level ≈ 95. The empirical formula across 15 working landmarks:

```
y ≈ 0.1017 × heightmap_value + 0.06 + 0.3 clearance
```

Examples:

- Heightmap 98 (London) → y ≈ 10.30
- Heightmap 124 (Mt. Fuji area) → y ≈ 12.40
- Heightmap 141 (Slovak mountains) → y ≈ 14.70

If `y` is well below terrain, the model renders underground and is invisible. If `y` is well above, it floats. The clearance of 0.3 sits the base just above the ground.

### Step 10: Add localisation

In `localisation/english/replace/replaced_from_vanilla_buildings_l_english.yml`:

```
 landmark_my_landmark: "My Landmark"
 landmark_my_landmark_plural: "$landmark_my_landmark$"
 landmark_my_landmark_desc: "A short description, written for the 2000s setting. Focus on the building's role today, not its founding myth or 1936-era framing. One paragraph, plain factual sentences."
```

The file must be UTF-8 with BOM. All landmark loc lives here for centralised maintenance.

## Common Pitfalls

### "not over the land" in error.log

```
mapbuildings.cpp:679: map/buildings.txt error at line N: map building location is not over the land - ignoring instance.
```

The XZ falls on a sea-province pixel. Floating harbor coordinates are not valid landmark spawns — they sit in water. Move the XZ to a land pixel.

### Icon shows in state UI but 3D model never renders

The most common silent failure. Walk through this checklist:

1. Does `map/buildings.txt` have a `landmark_spawn` line for the right state ID? If not, that's the bug.
2. Run `prov_at(x, z)` — does it return the province ID where the state file places the landmark? If not, the spawn is in the wrong province.
3. Does the province block in the state file contain only the landmark? If it also has `naval_base = N`, the naval base will block landmark rendering.
4. Does the player have the DLC named in `dlc_allowed`? Check `~/.local/share/Steam/steamapps/common/Hearts of Iron IV/dlc/`.
5. Do the entity and mesh definitions exist in MD's `landmarks.asset` / `landmarks.gfx`? MD's files file-override vanilla — vanilla entity/mesh definitions for new landmarks must be copied into MD.

### Map reworks silently drop spawn lines

When `map/buildings.txt` is regenerated as part of a map rework, the existing `landmark_spawn` lines can be dropped. To check whether a spawn used to exist:

```bash
git log -S "<state_id>;landmark_spawn" -- map/buildings.txt
```

If history shows the line existed and was removed, restore it (the old XZ may still be valid; re-verify with Step 8).

### Sharing the building file with vanilla

`common/buildings/01_landmark_buildings.txt`, `gfx/entities/landmarks.asset`, and `gfx/entities/landmarks.gfx` are file-level overridden by MD's copies. Vanilla's versions of these files are NOT loaded when MD is active. When adopting a vanilla landmark into MD:

1. Copy the building definition from vanilla's `01_landmark_buildings.txt` into MD's.
2. Copy the entity (regular + destroyed) from vanilla's `landmarks.asset` into MD's.
3. Copy the mesh (regular + destroyed) from vanilla's `landmarks.gfx` into MD's.
4. The `.mesh` / `.dds` / `.anim` binary files in `gfx/models/buildings/landmarks/` can stay vanilla-only — those resolve through the engine's path-based fallback.

## See Also

- [GFX Entity & Asset Errors](/dev-resources/gfx-entity-errors/) — for the general `pdx_entity.cpp` and `assetfactory.cpp` error patterns
- [Art Standards](/dev-resources/art-standards/) — DDS format specifications for the mesh textures
- [Terrain Photo System](/dev-resources/terrain-photo-guide/) — a similar multi-file system pattern for state-level art
