---
title: 3D Model Performance Guidelines
description: Mesh, texture, triangle, and redistribution requirements for Millennium Dawn 3D models
---

Build for a mid-range laptop, not a NASA supercomputer. These budgets are targets, not laws. If an asset genuinely needs to exceed a budget, ask a CM (DROID, Bird, or Doolittle) before you start, not after it is finished. For on-map models, consult with a CM.

## Permissions and Redistribution

Use only models for which you have express permission from the rights holder or a license that allows use in Millennium Dawn and redistribution, including through our public GitHub repository. This also applies to the model's textures and any modified versions you distribute. Being able to download or purchase an asset does not by itself grant redistribution rights.

Provide the source, creator, and license or written permission when submitting an asset. If redistribution rights are unclear, ask a CM before using it. Do not submit an asset whose terms prohibit public redistribution.

## Why This Matters

- Every model is multiplied. Unit models are drawn repeatedly for visible divisions, ships, and aircraft. A model that costs three times more can be felt hundreds of times over in a late-game world war.
- MD is already heavy. The mod adds many unit, ship, and aircraft models beyond vanilla, so every new asset has to justify its cost.
- Players' hardware varies. Budget for a mid-range laptop.
- The cost is more than polygons. Texture size, material count, bones, attachments, and particles all add up. Any one of them can sink an otherwise lean model.

## Mesh

- Never export the high-poly mesh. Bake its detail into a normal map and ship only the retopologized low-poly mesh.
- Apply or remove Subdivision modifiers. A forgotten Subdivision modifier can quadruple the triangle count at export.
- Delete faces nobody sees. Undersides of vehicles, hull interiors, and faces hidden inside other parts cost the same as visible ones.
- Merge duplicate vertices. Run Merge by Distance before export to remove doubled vertices from mirroring and booleans.
- Use triangles or quads, not n-gons. N-gons triangulate unpredictably on export and can produce shading errors.
- Keep geometry manifold where needed for baking. Fix unintended holes and remove stray internal faces that cause baking errors or waste triangles.
- Use one object and one material where possible. Separate meshes or materials add draw calls, so join parts unless they need to animate independently.
- Apply transforms before export. Use Ctrl+A on location, rotation, and scale, with -Y forward and +Z up, so the model does not need a giant scale value in the `.gfx` file.

## Textures

- Default to 1024×1024. This covers infantry, vehicles, and aircraft. Small attachments and props should use 512×512 or smaller.
- Use power-of-two sizes only: 256, 512, 1024, or 2048. This lets the engine compress and mipmap them correctly.
- Save as compressed DDS with mipmaps. Use DXT1/BC1 for maps without meaningful alpha and DXT5/BC3 where alpha carries data. Never ship uncompressed DDS for 3D model textures.
- Pack channels correctly. Follow the Clausewitz layout: normal X/Y in R and A of the normal map; specular in G, metalness in B, and gloss in A of the specular map. This avoids extra textures.
- Reuse textures across variants. Country camouflage variants should share the mesh, normal map, and specular map, swapping only the diffuse texture.
- Share atlases for families of models. Related vehicles or ships can share one texture set instead of each loading its own.
- Do not waste UV space. Large empty areas in the UV layout are paid-for pixels. Pack islands efficiently, leaving padding for mipmaps, before raising the resolution.

## Triangle Limits

Count triangles in the exported low-poly mesh, not faces in the source model.

| Model Type       | Triangle Target |
| ---------------- | --------------- |
| Weapons          | 1,000           |
| Armor & Vehicles | 5,000           |
| Ships            | 8,000           |
| Aircraft         | 6,000           |

See [Art Standards](/dev-resources/art-standards/) for file placement and naming.
