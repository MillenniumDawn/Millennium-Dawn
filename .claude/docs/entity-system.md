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
define (`donbas_gfx` does this for tanks, planes, and ships). The division designer's
model selector is engine-native and enumerates every unit entity, so entity count
drives how slow it is to open.

## Tierless and tiered motorized entities

A tag's tierless entity can supply missing tiers without overriding that tag's distinct
tiered art. Remove a tier entity only when its resolved mesh, animations, scale, and
attachments match the tierless entity with the same prefix, sub-unit, and terrain.
Keep terrain variants that have no matching tierless terrain entity. Repoint surviving
clones to the equivalent tierless source before deleting their tier source.

The France pilot in [#5417](https://github.com/MillenniumDawn/Millennium-Dawn/pull/5417),
commit `70d372bb`, removed 23 repeated entries (68 to 45 motorized entities) while
keeping the different vehicles at tiers 6 and 7. The maintainer reported that the
in-game check passed. This supports the same-tag rule, not culture, generic, or
cosmetic-prefix lookup. Cosmetic prefixes need their own in-game check.

Keep numbered culture and generic sprite entities for #1106. Since HOI4 1.18,
tierless fallbacks match every tier at high priority and can override country-tiered
models. A culture's sprite set needs `_1` to `_7` entries, either distinct entities or
clones. Equal resolved appearance alone does not make these fallback tiers redundant.

## Motorized sprite consolidation

The #5374 conversion builds on #5418 and moves regular motorized models to
`<prefix>_MD_motorized_*` across country, cosmetic, and shared cultural sets. Matching
militia, airborne, and marine entities use that sprite set instead. Keep sub-unit
entities whose mesh, animations, scale, or attachments differ. An omitted scale is 1.
Keep the shared base before surviving clones that reference it.

The conversion removes 1,243 definitions across 56 files and 65 prefixes (2,126 to
883 motorized entities). France drops from 45 to 33 and `jihadist_gfx` from 44 to 9.
Distinct English and Korean regular-infantry bases remain as sub-unit overrides.
All 91 existing numbered cultural motorized sprite entries remain; 67 former default
copies now hold the regular infantry's distinct tiered art. Their former appearance
remains in the shared base. Do not recreate identical country tiers removed by #5418.

Sprite/sub-unit lookup remains unverified in game. The shared sprite also serves heavy
motorized infantry, reconnaissance, and headquarters, whose tier selection may change.
Check all motorized sub-units at each tier in the designer and on the map, including
desert and snow, and check `error.log` for new missing entity lines. Static comparisons
cannot prove sprite fallback, terrain selection, cosmetic priority, or priority against
culture-level sub-unit entities. Do not treat this conversion as a confirmed lookup rule
until those checks pass.

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
