---
title: Terrain Photo System
description: How to add terrain photos to provinces in Millennium Dawn
---

# Terrain Photo System

The terrain photo system displays location-specific photographs in the province info panel when a player views a province. Each terrain photo requires entries in **3 files**, plus the image asset.

## Architecture

The system uses HOI4's province modifier auto-show mechanism:

1. A province receives a `terrain_X` static modifier via `add_province_modifier` in its **history/states** file
2. The engine looks up `GFX_terrain_X` in the sprite registry (**MD_terrain_cities.gfx**)
3. The engine auto-shows the `terrain_X_icon` widget in the state view GUI (**countrystateview.gui**)

All terrain modifiers have empty bodies (`terrain_X = { }`). They exist solely as visibility tokens.

## Files

| File                                         | Purpose                                     |
| -------------------------------------------- | ------------------------------------------- |
| `common/modifiers/01_province_modifiers.txt` | Modifier definitions (empty stubs)          |
| `interface/MD_terrain_cities.gfx`            | GFX sprite → DDS texture mappings           |
| `interface/countrystateview.gui`             | GUI icon declarations                       |
| `history/states/{id}-{name}.txt`             | Where the modifier is applied to a province |
| `gfx/interface/terrain/{filename}.dds`       | The actual image file                       |

## Adding a New Terrain Photo

### Step 1: Prepare the DDS image

- Place the image in `gfx/interface/terrain/`
- Name it `{TAG}_{city_name}.dds` (e.g., `CUB_havana.dds`). A small number of legacy entries use `{city_name}.dds` without a TAG prefix; do not rename them.
- Target size is approximately 30,080 bytes (the standard resolution/compression for most entries)

### Step 2: Add the modifier stub

In `common/modifiers/01_province_modifiers.txt`, add under the correct region/country section:

```
terrain_{city_name} = { }
```

### Step 3: Add the GFX sprite

In `interface/MD_terrain_cities.gfx`, add under the correct region/country section:

```
spriteType = {
    name = "GFX_terrain_{city_name}"
    textureFile = "gfx/interface/terrain/{TAG}_{city_name}.dds"
}
```

Note: The GFX `name` uses the modifier name (no TAG prefix). The `textureFile` uses the DDS filename (which has the TAG prefix).

### Step 4: Add the GUI icon

In `interface/countrystateview.gui`, add inside the `custom_icon_container` under the correct region/country section:

```
iconType = {
    name = "terrain_{city_name}_icon"
    spriteType = "GFX_terrain_{city_name}"
    alwaystransparent = yes
}
```

### Step 5: Apply to the province

In `history/states/{state_id}-{state_name}.txt`, add inside the `history = { }` block:

```
add_province_modifier = {
    static_modifiers = { terrain_{city_name} }
    province = { id = {province_id} }
}
```

Place it alongside any existing `add_province_modifier` blocks.

## Naming Convention

- **Modifier name**: `terrain_{city_name}` — lowercase, underscores for spaces, no country TAG prefix
- **GFX sprite name**: `GFX_terrain_{city_name}` — matches modifier name with `GFX_` prefix
- **GUI icon name**: `terrain_{city_name}_icon` — modifier name with `_icon` suffix
- **DDS filename**: `{TAG}_{city_name}.dds` — country TAG prefix (uppercase), lowercase city name

### When to use TAG prefixes

Only add a TAG prefix to the **modifier/GFX/GUI names** when the city name collides with another entry. Known collisions:

| City          | Entries                                                                                          |
| ------------- | ------------------------------------------------------------------------------------------------ |
| london        | `terrain_london` (UK), `terrain_CAN_london` (Canada)                                             |
| santiago      | `terrain_santiago` (Chile), `terrain_DOM_santiago` (Dominican Republic)                          |
| victoria      | `terrain_victoria` (Canada), `terrain_SPR_victoria` (Spain), `terrain_SEY_victoria` (Seychelles) |
| hamilton      | `terrain_hamilton` (Canada), `terrain_NZL_hamilton` (New Zealand)                                |
| san_francisco | `terrain_san_francisco` (USA), `terrain_DOM_san_francisco` (Dominican Republic)                  |

For the full list, check the modifiers file for entries with TAG prefixes.

## Common Pitfalls

- **Case sensitivity**: GFX lookups are case-sensitive on Linux. `GFX_terrain_Paris` will not match modifier `terrain_paris`.
- **Name mismatches**: The modifier name, GFX name (minus `GFX_` prefix), and GUI icon name (minus `_icon` suffix) must all match exactly.
- **Wrong state file**: Verify the province ID belongs to the state you're editing. The state ID is in the filename.
- **Missing entries**: All 3 files plus the history/states file must have matching entries for a terrain photo to display.
