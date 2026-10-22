# 3D Models

Every `.mesh` names its own textures, and a `pdxmesh` block in `gfx/entities/` can replace them. If a rendered material ends up with an empty texture name, the game has no texture to load for that map. `validate_mesh_textures.py` catches this on commit.

For how meshes, entities and animations link together, see [Entity & 3D Model System](../../.claude/docs/entity-system.md).

## How a model finds its textures

Each material in a `.mesh` stores a diffuse, normal and specular texture by file name only. The game looks that name up anywhere under `gfx/`, in the mod or in vanilla. A shared texture such as `gfx/models/units/basic_normal.dds` works for meshes in any folder, so don't copy it next to every mesh.

Two kinds of empty slot are normal:

- `Collision` materials never render, so their slots are empty by design.
- A slot missing from the material entirely. Vanilla ships helper shapes like the bombers' `dummyShape` this way.

A texture name that is an empty string on a rendered material is a bug. Vanilla never ships one.

## Filling a slot with meshsettings

You don't have to re-export the mesh. Add a `meshsettings` block to the `pdxmesh`:

```
pdxmesh = {
	name = "PER_truck_mesh"
	file = "gfx/models/units/vehicles/PER/PER_truck.mesh"

	meshsettings = {
		name = "MeshShape.001"
		index = 0
		texture_diffuse = "PER_motorized_diffuse_desert.dds"
		texture_normal = "PER_motorized_normal.dds"
		texture_specular = "PER_motorized_specular.dds"
		shader = "PdxMeshAdvanced"
	}
}
```

- `name` is the shape inside the mesh, and `index` is the mesh within that shape, counting from 0. The validator prints both for every finding.
- Without `name`, `index` counts the rendered materials across the whole mesh. That is fine for a single-shape mesh, but give a `name` whenever there are several shapes.
- Set all three textures and the shader, even if only one slot was empty. Vanilla's blocks always set all three.
- A sand, winter or other camo variant is its own `pdxmesh` with its own `meshsettings`, so each variant needs the fix.

For a missing normal or specular map, reuse a shared one: `basic_normal.dds` and `basic_specular.dds` for units, and `MD_building_normaltex.dds` and `MD_building_speculartex.dds` for buildings.

## Checking your work

The `md-validate-mesh-textures` pre-commit hook runs when you stage anything under `gfx/models/` or `gfx/entities/`. To run it by hand:

```bash
python3 tools/validation/validate_mesh_textures.py --no-color
```

It reports two things, both as errors:

- `mesh-texture-empty`: a rendered material still has an empty texture name after `meshsettings`.
- `mesh-texture-missing`: a texture name matches no file in mod or vanilla `gfx/`. This check needs a local HoI4 install (set `HOI4_PATH` if it isn't found) and is skipped without one.

CI doesn't check out model files, so the pre-commit hook is the only check. Don't skip it on model commits.
