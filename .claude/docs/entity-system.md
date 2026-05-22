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

- `GENERIC_infantryandvehicles.asset`, `GENERIC_tanks.asset`, `MD4_units_planes.asset`,
  `MD4_units_ships.asset` — generic `<suffix>_entity` sets used by most countries.
- `<TAG>_MD_infantryandvehicle.asset` — per-country override sets (~59 tags have one).
- `northamerican_gfx_infantryandvehicle.asset` — a culture-shared set serving all the
  US-balkanization breakaway nations at once.
- Shared weapon/accessory entities (`*_weapon_*_entity`, `cigarette_entity`, vehicle entities)
  are `attach`ed by soldier entities and are referenced across many files.

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
