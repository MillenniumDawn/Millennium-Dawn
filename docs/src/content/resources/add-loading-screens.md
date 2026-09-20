---
title: Add Loading Screens
description: The steps to add a loading screen or replace the main-menu image so both the loading rotation and the main-menu background picker show it
---

Loading screens double as main-menu backgrounds. The rotation shows every `.dds` in `gfx/loadingscreens/`; the _Change background_ picker only lists entries declared in `common/frontend/backgrounds/base_backgrounds.txt`, and previews each with a generated 192x144 thumbnail. Skip the declaration or the thumbnail and the picker shows vanilla art.

## Add a loading screen

1. On the `gfx-input` branch, save the image as `gfx/loadingscreens/load_<N>.dds` - 1920x1440, DXT1 (BC1), no mipmaps, `<N>` one above the highest existing number. Never renumber existing files; players' saved selections are stored by path.
2. Add `load_<N> = { }` to `common/frontend/backgrounds/base_backgrounds.txt`.
3. Run `python3 tools/assets/generate_background_thumbnails.py`. It writes `load_<N>_small.dds` and regenerates `interface/small_background.gfx` - never edit either by hand.
4. Optional quote: add the next `LOADING_TIP_<n>` key to `localisation/english/loading_tips_l_english.yml`.
5. Commit the `.dds`, the `_small.dds`, the `base_backgrounds.txt` line and the `.gfx` together. `python3 tools/assets/generate_background_thumbnails.py --check` fails if any is missing or stale.

To remove one, delete the `.dds`, its `_small.dds` and its `base_backgrounds.txt` line, then run the generator.

## Replace the main-menu image

1. Overwrite `gfx/main_menu/main_menu.dds` (1920x1440, DXT1, no mipmaps). It is wired by `GFX_frontend_bg` in `interface/frontendmainviewbg.gfx`.
2. Run `python3 tools/assets/generate_background_thumbnails.py` and commit the regenerated `main_menu_small.dds` and `.gfx` with it - the picker lists the menu image as a tile too.
