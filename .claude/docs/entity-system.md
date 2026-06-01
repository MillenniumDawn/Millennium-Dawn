# Entity & 3D Model System

How Hearts of Iron IV links unit/equipment script objects to 3D models, and how
Millennium Dawn organises that data.

## The mesh → entity → animation chain

Three layers, all under `gfx/`:

| Layer     | File                    | Block       | Defines                                                                                                                    |
| --------- | ----------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------- |
| Mesh      | `gfx/entities/*.gfx`    | `pdxmesh`   | `name`, `file` (path to a `.mesh`), `animation` id→type bindings, `scale`                                                  |
| Entity    | `gfx/entities/*.asset`  | `entity`    | `name`, `pdxmesh`, `state` (animation states), `attach` (sub-entities), `locator`, `scale`, `cull_radius`, `default_state` |
| Animation | `gfx/models/**/*.asset` | `animation` | `name`, `file` (path to a `.anim`)                                                                                         |

An `entity` references a `pdxmesh` by name; a `pdxmesh` references a `.mesh` file and binds
animation ids; an `animation` id resolves to a `.anim` file. An entity may `attach` other
entities (a soldier attaches weapon entities, a vehicle attaches its crew, etc.).

## How a unit gets its 3D model — the three-level lookup

The engine builds an entity name from a **prefix** plus a **suffix** and resolves it through
three levels, first hit wins:

1. `<TAG>_<suffix>_entity` — country-specific override
2. `<graphical_culture>_<suffix>_entity` — culture-shared
3. `<suffix>_entity` — generic fallback

`graphical_culture` is set per country in `common/countries/<Country>.txt`; valid values are
listed in `common/graphicalculturetype.txt`. **The `graphical_culture` value doubles as an
entity-name prefix** — vanilla ships `asian_gfx_infantry_entity`,
`southamerican_gfx_infantry_entity`, `commonwealth_gfx_infantry_entity`, etc.

Consequence: a group of country tags can share **one** bespoke entity set by sharing a
`graphical_culture` and defining a single `<graphical_culture>_*` set — no per-tag copies needed.
In MD, 332 of 391 tags have no bespoke entity file at all and resolve straight to the generic
`<suffix>_entity` set.

## Naming convention

```
[<prefix>_]<suffix>_entity[_<terrain>]
```

- `prefix` — a country `TAG`, a `graphical_culture`, or omitted (generic).
- `suffix` — identifies the unit/equipment (sub-unit + equipment model level).
- `terrain` — optional `desert` / `snow` variant.

## File organisation in `gfx/entities/`

Entity files (`.asset`) define `entity` blocks; pdxmesh files (`.gfx`) define `pdxmesh` blocks
in `objectTypes = { }`.

### Shared pdxmesh files

| File                           | Contains                                                                     |
| ------------------------------ | ---------------------------------------------------------------------------- |
| `infantry.gfx`                 | Shared infantry pdxmesh definitions (fallback variants for generic infantry) |
| `MD_vehicles.gfx`              | Shared vehicle pdxmesh definitions                                           |
| `MD_smallarms.gfx`             | Shared small-arms pdxmesh definitions                                        |
| `MD_ships.gfx`                 | Shared ship pdxmesh definitions                                              |
| `MD_buildings.gfx`             | Shared building pdxmesh definitions                                          |
| `MD_units_planes.asset`        | Generic plane entity sets                                                    |
| `MD_units_ships.asset`         | Generic ship entity sets                                                     |
| `___MD_planes.gfx`             | Additional shared plane pdxmesh definitions                                  |
| `___MD_tanks_and_vehicles.gfx` | Additional shared tank/vehicle pdxmesh definitions                           |

Pdxmesh naming follows the `MD_` prefix convention (e.g., `MD_mechanized`, `MD_infantry_2`).
Historical files may still reference the older `MD4_` prefix — both patterns are valid but new
definitions should use `MD_`.

### Per-country files

- `<TAG>_MD_infantryandvehicle.asset` / `.gfx` — per-country infantry/vehicle entity sets and
  associated pdxmesh definitions (~59 tags have one).
- `<TAG>_MD_planes.asset` — per-country plane entity sets (SOV, USA, JAP, GER, etc.).
- `<TAG>_MD_tanks.asset` / `*_tanks.asset` — per-country tank entity sets.
- `<TAG>_MD_ships.asset` — per-country ship entity sets.
- `northamerican_gfx_infantryandvehicle.asset` — a culture-shared set serving all the
  US-balkanization breakaway nations at once.

Shared weapon/accessory entities (`*_weapon_*_entity`, `cigarette_entity`, vehicle entities) are
`attach`ed by soldier entities and are referenced across many files.

## The division designer model selector (performance note)

The 3D model selector in the division designer (`interface/divisiondesignerview.gui`, window
`div_template_select_model`, gridbox `buttons_grid`) is **engine-native** — there is no scripted
GUI, no `dynamic_lists`, and no `dirty` variable. The engine enumerates unit entities to build
the list, so total entity count drives how heavy it is to open. MD ships ~25,000 entities versus
vanilla's ~575.

**Do not copy a unit entity set once per country tag.** If several tags should share a bespoke
look, give them the same `graphical_culture` and define one `<graphical_culture>_*` set; the
engine's culture-level lookup serves all of them. (The US breakaways were once 17 byte-identical
per-tag copies — 4,760 entities — later consolidated into a single 280-entity
`northamerican_gfx_*` set.)

## Landmark buildings (state-placed 3D models)

Landmarks (Big Ben, Statue of Liberty, Mt. Fuji, etc.) use the same mesh/entity chain but add
two more layers: a **state-file placement** and a **map spawn point**. Both must agree on which
province the landmark sits in, or the icon shows in the state UI while the 3D model never
renders. Most rendering bugs are at this layer, not in the asset chain.

### Five files per landmark

| File                                         | Block / line                                                                 | Purpose                                                                              |
| -------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `common/buildings/01_landmark_buildings.txt` | `landmark_<name> = { spawn_point = landmark_spawn ... }`                     | Building definition (DLC gate, modifiers, icon, scale cap, `enable_for_controllers`) |
| `gfx/entities/landmarks.asset`               | `entity = { name = "building_landmark_<name>" pdxmesh = "..." }`             | Entity definition + scale + destruction animation states                             |
| `gfx/entities/landmarks.gfx`                 | `pdxmesh = { name = "landmark_<name>_mesh" file = "..." }`                   | Mesh-name → `.mesh` file mapping                                                     |
| `history/states/<id>-<Name>.txt`             | Inside `buildings = { <PROVINCE_ID> = { landmark_<name> = { level = 1 } } }` | Per-state placement of the landmark in a specific province                           |
| `map/buildings.txt`                          | `<state_id>;landmark_spawn;<x>;<y>;<z>;<rot>;<province_id>`                  | World-space spawn coordinates used to render the model                               |

If any of those is missing or inconsistent, the building either silently fails to render or
errors out in `error.log` (`mapbuildings.cpp:679: ... not over the land - ignoring instance`).

### Validating a spawn point against the province bitmap

The engine determines which province a spawn sits in from `(x, z)` against `map/provinces.bmp`.
The trailing province-id field on a `landmark_spawn` line is the explicit binding hint — it must
match the same province that `provinces.bmp` reports at those coordinates and the same province
the state file places the landmark in. **All three must agree**, otherwise rendering silently
fails.

Pixel-to-world coordinates: `world_x == pixel_x`, `world_z == (height - 1) - pixel_y`. Map is
5632×2048. Province colors come from `map/definition.csv`.

Audit script template (used to fix the entire landmark roster during the 2026-05 restoration):

```python
from PIL import Image
import numpy as np, csv

arr = np.array(Image.open('map/provinces.bmp')); H, W, _ = arr.shape
hmap = np.array(Image.open('map/heightmap.bmp').convert('L'))
color_to_pid = {}
with open('map/definition.csv', encoding='latin-1') as f:
    for r in csv.reader(f, delimiter=';'):
        if r and r[0].isdigit():
            color_to_pid[(int(r[1]), int(r[2]), int(r[3]))] = int(r[0])

def prov_at(x, z):
    px, py = int(round(x)), (H-1) - int(round(z))
    return color_to_pid.get(tuple(arr[py, px].tolist()))

def heightmap_at(x, z):
    return int(hmap[(H-1) - int(z), int(x)])
```

To find a known-good spawn for a given province ID, take the centroid of an _eroded_ mask
(only interior pixels) so the spawn isn't on a province border.

### Y-coordinate calibration from the heightmap

`map/heightmap.bmp` is a single-channel image where sea level ≈ 95. The `y` value on a
`landmark_spawn` line must sit just above the terrain at that XZ. Empirical fit across 15
working landmarks: `y ≈ 0.1017 × heightmap + 0.06 + 0.3 clearance`.

Examples that anchored the formula:

- Big Ben at (2802, 1551): heightmap 98 → y = 10.30 (terrain ~10.03, clearance 0.27)
- Mt. Fuji at (4968, 1243): heightmap 124 → y = 12.40
- Bojnice Castle at (3098, 1502): heightmap 141 → y = 14.70

If `y` is well below terrain, the engine still accepts the line but the model renders
underground — invisible from above. If `y` is too far above, the model floats. **Aim for
heightmap-derived y + ~0.3 clearance.**

### Common gotchas

1. **"not over the land" in error.log** = the spawn's `(x, z)` falls in a sea-province pixel.
   The trailing `province_id` doesn't help; XZ must be a land tile. Float harbours sit in sea
   provinces — their coordinates are _not_ valid landmark spawns.

2. **Co-occupancy with `naval_base` in the same province block** breaks landmark rendering.
   The Statue of Liberty pattern (one landmark in its own dedicated province block, nothing else)
   reliably works; combining a landmark with `naval_base = N` in the same block does not.
   Workaround: move the other building to a different province in the state, or split blocks.

3. **Map reworks silently drop `landmark_spawn` lines.** Commits 89ccbf62cc (#725) and 4da960e3c8
   (#810) regenerated `map/buildings.txt` without preserving the existing landmark spawn entries.
   When auditing landmark issues, `git log -S "<state_id>;landmark_spawn" -- map/buildings.txt`
   tells you whether a spawn existed historically.

4. **Same filename = vanilla file is replaced.** MD's `landmarks.gfx` / `landmarks.asset` /
   `01_landmark_buildings.txt` override vanilla's at the file level (none of those paths are in
   `descriptor.mod`'s `replace_path` list, but file-level shadowing applies regardless). When
   adding a vanilla landmark to MD, the entity, mesh, and building definitions must be **copied
   into MD's files** — they will not be merged from vanilla's. Mesh **binaries** (`.mesh`, `.dds`,
   `.anim`) under `gfx/models/buildings/landmarks/` use path-based fallback, so MD doesn't need
   to ship copies when vanilla's bytes are correct.

5. **`enable_for_controllers` gating.** Removing it follows the Mecca pattern: any controller of
   the state gets the modifier (good for tourism / heritage). Keeping it gates the modifier to
   the home country only (good for strategic/military buildings like ICBM silos where a foreign
   occupier shouldn't benefit).

6. **`show_on_map = 0`** means no 3D model is drawn even if a spawn exists. The Binnenhof
   landmark uses this — it's intentionally state-UI-only.

### Quick troubleshooting flow

When a landmark shows the icon in the state UI but no 3D model appears:

1. Grep `map/buildings.txt` for the state's `landmark_spawn` line. If missing, that's the bug.
2. Run `prov_at(x, z)` against the spawn's XZ. Confirm it equals the province in the state file.
   If not, recompute the centroid of the placement province and update the spawn.
3. Check `error.log` for `mapbuildings.cpp:679` — "not over the land" means XZ is sea, move it.
4. Confirm the building's `dlc_allowed` matches the DLC the player has installed
   (`~/.local/share/Steam/steamapps/common/Hearts of Iron IV/dlc/`).
5. Verify the building's province block in the state file doesn't share with `naval_base` (the
   Big Ben gotcha).
6. Confirm the entity + mesh definitions exist in MD's `landmarks.asset` / `landmarks.gfx`
   (file-level override means vanilla's are not loaded).
