---
title: Art Standards
description: Document detailing Millennium Dawn's GFX/Art Standards
---

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

- Loading Screens/Main Menu - PNG

Some textures, such as flags, require the TGA format instead. Be mindful of what you’re working on.

### When block compression hurts

DXT1 and DXT5 are lossy. On photographs the damage is usually invisible, but on flat colour and hard edges (a logo, a map, a heraldic device) it blocks up badly. Measured on real event art, DXT5 lands around 26 dB PSNR on a two-colour logo against 30 dB on an oil painting.

Save those as uncompressed B8R8A8G8 instead. It is four times the file size and bit-exact, and the game loads it fine: several hundred event pictures and leader portraits already ship that way. Use your judgement, and prefer uncompressed whenever the art has large flat areas.

### Flags

Flags are uncompressed TGA at three sizes, and the game finds each one by the same filename in a different directory:

- `gfx/flags/NAME.tga` at 82x52
- `gfx/flags/medium/NAME.tga` at 41x26
- `gfx/flags/small/NAME.tga` at 10x7

Never put the size in the filename. `PER_federation_m.tga` in `medium/` will never load, because the game is looking for `medium/PER_federation.tga`.

For a cosmetic tag, `NAME` is the tag exactly as `set_cosmetic_tag` spells it, case included.

Most tools write TGA with a top-left origin descriptor. Nearly every flag in the repo uses bottom-left, so match it: in ImageMagick that means `-flip -orient bottom-left -compress None`.

## Placing Files

Ensure that you are in the gfx-input branch on the GitHub repository before dropping anything into the mod. This is where all graphics go regardless of what they are being made for.

You can usually find the location where your graphics need to go relatively easily just by looking at the names of the folders. Compare them to what you’re working on. Folder layouts might vary; some are deeper in the files than others. Here are just some examples.

- Event Pictures: gfx → event_pictures
- Flags: gfx → flags, medium, small
- Leaders: gfx → leaders → TAG
- National Focuses: gfx → interface → goals

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

## Implementation

We have a Python script that can do that automatically now. Either Bird or I will run it every time we’ve got lots of new stuff on the branch.

The script works as long as everything should be in the files. Please contact whoever requested the graphics you’re working on if the auto implementation isn’t working.
