# Entity and 3D Model System

## Mesh, entity, animation

| Layer     | File                    | Block       |
| --------- | ----------------------- | ----------- |
| Mesh      | `gfx/entities/*.gfx`    | `pdxmesh`   |
| Entity    | `gfx/entities/*.asset`  | `entity`    |
| Animation | `gfx/models/**/*.asset` | `animation` |

An `entity` references a `pdxmesh` by name. A `pdxmesh` references a `.mesh` file and
binds animation ids. An `animation` id resolves to a `.anim` file. An entity may
`attach` other entities, such as a soldier's weapon.

## How a unit gets its model

The engine builds an entity name and resolves it through three levels. First hit wins:

1. `<TAG>_<suffix>_entity`
2. `<graphical_culture>_<suffix>_entity`
3. `<suffix>_entity`

The full form is `[<prefix>_]<suffix>_entity[_<terrain>]`, where `terrain` is an optional
`desert` or `snow` variant. `graphical_culture` is set per country in
`common/countries/<Country>.txt`.

Do not copy an entity set once per tag. To give several tags a shared look, give them
the same `graphical_culture` and define one `<graphical_culture>_*` set
(`northamerican_gfx_infantryandvehicle.asset` serves every US breakaway). A new culture
needs a line in `common/graphicalculturetype.txt`. Tags moved to it lose the old culture's
fallbacks, so clone the old culture's entities for any unit type the shared set does not
define (`donbas_gfx` does this for tanks, planes, and ships). Give each tierless sprite
entity in a culture set `_1` to `_7` clones, or it matches every tier. The division
designer's model selector is engine-native and enumerates every unit entity, so entity
count drives how slow it is to open.

## Files in `gfx/entities/`

- Shared pdxmeshes: `infantry.gfx`, `MD_vehicles.gfx`, `MD_smallarms.gfx`, `MD_ships.gfx`,
  `MD_buildings.gfx`, `___MD_planes.gfx`, `___MD_tanks_and_vehicles.gfx`.
- Generic entity sets: `MD_units_planes.asset`, `MD_units_ships.asset`.
- Per country: `<TAG>_MD_infantryandvehicle.asset` and `.gfx`, `<TAG>_MD_planes.asset`,
  `<TAG>_MD_tanks.asset`, `<TAG>_MD_ships.asset`.
- New pdxmesh names use the `MD_` prefix. Older ones use `MD4_`.

## Mesh texture lookups

Run `tools/validation/validate_mesh_textures.py` instead of a hand-rolled scan. Before
reporting a missing or empty texture in a `.mesh`, or copying textures between folders:

- The engine finds mesh textures by filename anywhere under `gfx/`, not only in the
  mesh's own folder. Vanilla relies on this.
- Empty diffuse, normal, or spec names on `Collision` shader materials are by design.
  A slot absent from a material is also fine.
- Skip `#`-commented `pdxmesh` blocks, and apply `meshsettings` (`name` is the shape,
  `index` the mesh within it) before flagging.

## Landmark buildings

A landmark uses the same chain plus a state-file placement and a map spawn point. Five
files must agree:

- `common/buildings/01_landmark_buildings.txt`: the building definition.
- `gfx/entities/landmarks.asset`: `entity` named `building_landmark_<name>`.
- `gfx/entities/landmarks.gfx`: `pdxmesh` named `landmark_<name>_mesh`.
- `history/states/<id>-<Name>.txt`:
  `buildings = { <PROVINCE_ID> = { landmark_<name> = { level = 1 } } }`.
- `map/buildings.txt`: `<state_id>;landmark_spawn;<x>;<y>;<z>;<rot>;<province_id>`.

Rules:

- The province in the state file, the trailing province id on the spawn line, and the
  province `map/provinces.bmp` reports at `(x, z)` must all match, or the icon shows in
  the state UI while the model never renders.
- Pixel to world: `world_x = pixel_x`, `world_z = (height - 1) - pixel_y`. The map is
  5632 by 2048. Province colors are in `map/definition.csv`. Pick an interior pixel,
  not one on a province border.
- `y` sits just above the terrain: about `0.1017 * heightmap + 0.36`, where
  `map/heightmap.bmp` has sea level near 95. Too low renders underground. Too high
  floats.
- `not over the land` in `error.log` (`mapbuildings.cpp:679`) means the spawn's `(x, z)`
  is a sea pixel. Floating harbor coordinates are not valid landmark spawns.
- A landmark sharing its province block with `naval_base` does not render. Give it its
  own block.
- Map reworks have dropped `landmark_spawn` lines. Check with
  `git log -S "<state_id>;landmark_spawn" -- map/buildings.txt`.
- MD's `landmarks.gfx`, `landmarks.asset`, and `01_landmark_buildings.txt` replace
  vanilla's by filename. A vanilla landmark must be copied into MD's files. Mesh
  binaries under `gfx/models/buildings/landmarks/` fall back to vanilla by path.
- `enable_for_controllers` gates the modifier to the listed countries. Without it, any
  controller of the state gets the modifier.
- `show_on_map = 0` draws no model on purpose.

When the icon shows but the model does not: check the spawn line exists, check its
province, check `error.log`, check `dlc_allowed`, check for a shared `naval_base` block,
then check the entity and mesh definitions exist in MD's files.
