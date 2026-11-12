---
title: Art Standards
description: Document detailing Millennium Dawn's GFX/Art Standards
---

## 3D Models

Follow the [3D Model Performance Guidelines](/dev-resources/3d-model-performance-guidelines/) for mesh and texture budgets, triangle targets, CM consultation, and permissions for public redistribution through GitHub.

## File Management

All graphics need to be placed in the right location to ensure they aren’t lost and implemented into the game. Here are the resources you need and the places you need to be looking when you finish your icons.

## Saving Textures

First, download the Nvidia Texture Tools Exporter as a standalone app or a plugin for Photoshop to save icons as DDS files. You can find it here.

https://developer.nvidia.com/nvidia-texture-tools-exporter

The app will be brought up when saving a copy of a file when using it as a plugin for Photoshop. Select the correct format (usually RGB or RGBA, depending on the transparency) when exporting with the highest compression quality before you save.

### File Formats

- Leader Portraits - DXT1 (BC1) - No Mipmaps
- Leader Portraits Small - B8R8A8G8 (Linear A8R8G8B8) - No Mipmaps
- Event Pictures - DXT5 (BC3) - No Mipmaps

- Tech Icons/Variant Icons - B8R8A8G8 (Linear A8R8G8B8) - No Mipmaps
- Ideas - B8R8A8G8 (Linear A8R8G8B8) - No Mipmaps
- Goals/Focus - B8R8A8G8 (Linear A8R8G8B8) - No Mipmaps
- GUI icons - B8R8A8G8 (Linear A8R8G8B8) - No Mipmaps

- Loading Screens/Main Menu - DXT1 (BC1) - No Mipmaps - 1920x1440 - see [Add Loading Screens](/dev-resources/add-loading-screens/)

- 3D Model Textures - DXT1 (BC1), or DXT5 (BC3) when alpha carries data - With Mipmaps - see [3D Model Performance Guidelines](/dev-resources/3d-model-performance-guidelines/)

Some textures, such as flags, require the TGA format instead. Be mindful of what you’re working on.

### Rules for every DDS file

- **Use the legacy DDS header.** The DX10 header is not supported. BC7 and BC6H always write one, and so does any format your exporter labels sRGB, so do not pick those.
- **Uncompressed means 32-bit A8R8G8B8.** Do not save 24-bit RGB or 16-bit files, even when the art has no transparency.
- **A `.dds` file must hold DDS data.** Do not rename a PNG, JPEG, or TGA.
- **No mipmaps on GUI art.** Portraits, event pictures, icons, and backgrounds are drawn at full size, so the smaller levels are never shown. They only add a third to the file size and to video memory.
- **Mipmaps on anything drawn on the 3D map.** Model and particle textures are drawn far below full size when zoomed out, and shimmer without the smaller levels.

A leader portrait counts as small when its shorter side is under 100 pixels.

### Large GUI backgrounds

Icons stay uncompressed because DXT damages fine detail, text, and flat color. Large smooth art, such as a panel background, can compress with no visible change.

You do not have to decide this by hand. Save GUI art uncompressed. `dds_standardize.py` test-compresses each uncompressed GUI texture and keeps the result only when it scores at least 40 dB PSNR against the original, with 99.9% of texels within 20 of 255.

### When block compression hurts

DXT1 and DXT5 are lossy. On photographs the damage is usually invisible, but on flat colour and hard edges (a logo, a map, a heraldic device) it blocks up badly. Measured on real event art, DXT5 lands around 26 dB PSNR on a two-colour logo against 30 dB on an oil painting.

Save those as uncompressed B8R8A8G8 instead. It is four times the file size and bit-exact, and the game loads it fine: several hundred event pictures and leader portraits already ship that way. Use your judgement, and prefer uncompressed whenever the art has large flat areas.

`dds_standardize.py` cannot tell flat art from a photograph. It lists every uncompressed event picture and large portrait as one it would compress, so leave the flat ones out when you run it with `--fix --write`.

### Flags

Flags are uncompressed TGA at three sizes, and the game finds each one by the same filename in a different directory:

- `gfx/flags/NAME.tga` at 82x52
- `gfx/flags/medium/NAME.tga` at 41x26
- `gfx/flags/small/NAME.tga` at 10x7

Never put the size in the filename. `PER_federation_m.tga` in `medium/` will never load, because the game is looking for `medium/PER_federation.tga`.

For a cosmetic tag, `NAME` is the tag exactly as `set_cosmetic_tag` spells it, case included.

Most tools write TGA with a top-left origin descriptor. Nearly every flag in the repo uses bottom-left, so match it: in ImageMagick that means `-flip -orient bottom-left -compress None`.

## Placing Files

There is no shared graphics branch. Put your graphics on a small branch of their own and open a pull request from it quickly, or put them on a content branch that is about to merge into `main`. Do not leave art on a long-lived branch. Large binary files cannot be merged, and a stale branch will conflict with everyone else's art.

You can usually find the location where your graphics need to go relatively easily just by looking at the names of the folders. Compare them to what you’re working on. Folder layouts might vary; some are deeper in the files than others. Here are just some examples.

- Event Pictures: gfx → event_pictures
- Flags: gfx → flags, medium, small
- Leaders: gfx → leaders → TAG
- National Focuses: gfx → interface → goals
- Loading Screens: gfx → loadingscreens, then [Add Loading Screens](/dev-resources/add-loading-screens/)

Remember that some of these folders have subfolders for each country or region. Place your graphics for Germany in the German folder if you see one.

## Naming Files

Try to follow what everything else in the folder is named, and don’t put “gfx” in front of everything. Try to follow the example below.

DO: GER_Icon_Name
DO NOT: GFX_Germany_Icon_Name

## Converting

`tools/assets/md_art_convert.py` writes the formats above so you don’t have to remember the flags. It needs ImageMagick on PATH.

```bash
# Event pictures, 217x163 for a country event or 397x153 for a news event
python3 tools/assets/md_art_convert.py event art/*.png --out-dir "gfx/event_pictures/europe/france - FRA"

# Leader portraits, 156x210
python3 tools/assets/md_art_convert.py portrait art/leader.png --out-dir gfx/leaders/FRA

# A flag, written to all three sizes at once
python3 tools/assets/md_art_convert.py flag art/flag.png --name FRA_commune
```

It refuses art that is the wrong size rather than silently rescaling it, and checks each same-size result against its source so a bad conversion can’t reach the branch. Pass `--resize` if you really do want it scaled.

`normalise` rewrites any TGA that was saved with a top-left origin. It moves rows and clears one header bit, so the image itself is untouched:

```bash
python3 tools/assets/md_art_convert.py normalise gfx/flags --check
```

## Checking Textures

`tools/assets/dds_standardize.py` checks existing DDS files against the formats and rules above. Without `--fix --write` it only reports.

```bash
# Report what is off-standard in the folder you worked in
python3 tools/assets/dds_standardize.py gfx/interface/technologies/FRA

# Rewrite those files
python3 tools/assets/dds_standardize.py --fix --write gfx/interface/technologies/FRA
```

- A DX10 header, 16-bit or 24-bit texels, and PNG or JPEG data under a `.dds` name are rewritten in the folder's format. When that format is uncompressed, no pixel changes.
- Uncompressed art in a folder listed as DXT1 or DXT5 is compressed. This is lossy, so read [When block compression hurts](#when-block-compression-hurts) first.
- Mipmaps are dropped from GUI art and added to model textures. The full-size image is not re-encoded.

`tools/assets/dds_mipmaps.py` runs the mipmap check alone and takes the same arguments. It also covers particle textures.

Run the fix on the files or folder you added or changed, never on all of `gfx/`. Every converted file needs a look in game, and a bulk pass makes that impossible.

Both tools need numpy and Pillow. `tools/README.md` lists the install command.

## Implementation

We have a Python script that can do that automatically now. Either Bird or I will run it every time we’ve got lots of new stuff on the branch.

The script works as long as everything should be in the files. Please contact whoever requested the graphics you’re working on if the auto implementation isn’t working.
