# resources

Reference-only material that ships with the repo but never loads in game.
Pre-commit and the validators skip this whole directory.

Most of what used to live here has moved to
[millennium-dawn-resources](https://github.com/MillenniumDawn/millennium-dawn-resources):
archived branches, cut country content and systems, OOB source PDFs, GFX
templates, spreadsheets, and the legacy generator scripts. Look there first if
you are hunting for something that used to be in this folder.

## What stayed, and why

| Path                | Why it is still here                                                                                              |
| ------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `documentation/`    | CI dependency. `tools/validation/validate_modifiers.py` reads `modifiers_documentation.md`, `refresh_vanilla_data.py` writes these files, and three workflows sparse-check-out the directory. |
| `AA_graphics_dump/` | Art source pool. Sprites pulled out of the mod that artists still draw from.                                        |
| `portrait_dump/`    | Same, for leader portraits.                                                                                         |
| `misc-graphics/`    | Same, for loose textures and 3D meshes.                                                                             |
| `hoi_mapfont4.*`    | Vanilla map font, kept as the editing template for map font work.                                                   |

The three art dumps are unreviewed. They are the next thing to sort through.

## Retiring content

When you pull something out of the mod and it is worth keeping, it goes in the
millennium-dawn-resources repo, not here. The art dumps are the one exception:
sprites and portraits that came out of `gfx/` still land in the dumps above.
