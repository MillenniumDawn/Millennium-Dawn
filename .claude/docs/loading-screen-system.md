# Loading Screen System

Contributor steps: `docs/src/content/resources/add-loading-screens.md`. This page is the contract behind them.

## Contract

- Rotation: every `gfx/loadingscreens/*.dds` except `*_small.dds` (`replace_path` hides vanilla's folder).
- Picker: entries in `common/frontend/backgrounds/base_backgrounds.txt`; `load_7 = { }` reads `gfx/loadingscreens/load_7.dds` and previews sprite `GFX_load_7_small` (engine builds `"GFX_" + name + "_small"`). On a miss it falls back to vanilla's `GFX_frontend_bg_basic_small` with nothing in `error.log` - `replace_path` does not block vanilla texture lookups. That was the v2.0 picker bug.
- `GFX_frontend_bg` (`interface/frontendmainviewbg.gfx` -> `gfx/main_menu/main_menu.dds`) is listed as an extra picker tile, previewed by `GFX_main_menu_small`.
- Selection persists by texture path in `settings.txt`; renaming a file resets it.

## Generator

`tools/assets/generate_background_thumbnails.py` is the only writer of `*_small.dds` (192x144 DXT1) and `interface/small_background.gfx`. It reads every backgrounds entry plus the `GFX_frontend_bg` texture, re-encodes with `batchdds-2.py`, writes only changed bytes, and `--check` exits 1 on anything stale, missing, undecodable or orphaned. Not wired into pre-commit or CI - run by hand. `interface/small_background.gfx` keeps the vanilla filename so vanilla's `GFX_load_1_small..9_small` cannot coexist with MD's, and carries vanilla's border sprite for the same reason.

## Review checks

- A new `load_<N>.dds` must arrive with its `base_backgrounds.txt` line, its `_small.dds` and the regenerated `.gfx`.
- Hand-edited `small_background.gfx` or hand-made thumbnails are wrong; the next generator run reverts them.
- Art should be 1920x1440 DXT1 without mipmaps; uncompressed (8-11 MB) only for flat colour.
